"""
Lambda Function: Scheduler Manager
Gestiona la creación, consulta y cancelación de schedules en EventBridge Scheduler
"""

import json
import os
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

# Clientes AWS
scheduler_client = boto3.client('scheduler')
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
SCHEDULE_TABLE_NAME = os.environ['SCHEDULE_TABLE_NAME']
ORDER_EXECUTOR_ARN = os.environ['ORDER_EXECUTOR_ARN']
SCHEDULER_ROLE_ARN = os.environ['SCHEDULER_ROLE_ARN']

schedule_table = dynamodb.Table(SCHEDULE_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimal de DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Handler principal que enruta las peticiones según el método HTTP
    """
    print(f"Event received: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    try:
        if http_method == 'POST' and path == '/schedule':
            return create_schedule(event)
        elif http_method == 'GET' and path == '/schedules':
            return list_schedules(event)
        elif http_method == 'GET' and '/schedule/' in path:
            return get_schedule(event)
        elif http_method == 'DELETE' and '/schedule/' in path:
            return delete_schedule(event)
        elif http_method == 'GET' and path == '/orders':
            return list_orders(event)
        else:
            return response(404, {'error': 'Endpoint no encontrado'})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'error': str(e)})


def create_schedule(event):
    """
    Crea un nuevo schedule en EventBridge Scheduler
    
    Body esperado:
    {
        "scheduleName": "rocket-shoes-hourly",
        "frequency": "rate(1 hour)",
        "gadgetType": "Rocket Shoes",
        "quantity": 100,
        "enabled": true
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validar campos requeridos
        required_fields = ['scheduleName', 'frequency', 'gadgetType', 'quantity']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Campo requerido: {field}'})
        
        schedule_id = str(uuid.uuid4())
        schedule_name = body['scheduleName']
        frequency = body['frequency']
        gadget_type = body['gadgetType']
        quantity = body['quantity']
        enabled = body.get('enabled', True)
        
        # Crear el schedule en EventBridge Scheduler
        schedule_expression = frequency
        
        # Payload que se enviará a la Lambda ejecutora
        target_input = {
            'scheduleId': schedule_id,
            'gadgetType': gadget_type,
            'quantity': quantity
        }
        
        scheduler_client.create_schedule(
            Name=schedule_name,
            ScheduleExpression=schedule_expression,
            State='ENABLED' if enabled else 'DISABLED',
            FlexibleTimeWindow={
                'Mode': 'OFF'
            },
            Target={
                'Arn': ORDER_EXECUTOR_ARN,
                'RoleArn': SCHEDULER_ROLE_ARN,
                'Input': json.dumps(target_input)
            },
            Description=f'Schedule para generar órdenes de {gadget_type}'
        )
        
        # Guardar definición en DynamoDB
        timestamp = datetime.utcnow().isoformat()
        schedule_item = {
            'scheduleId': schedule_id,
            'createdAt': timestamp,
            'scheduleName': schedule_name,
            'frequency': frequency,
            'gadgetType': gadget_type,
            'quantity': quantity,
            'enabled': enabled,
            'status': 'active'
        }
        
        schedule_table.put_item(Item=schedule_item)
        
        return response(201, {
            'message': 'Schedule creado exitosamente',
            'schedule': schedule_item
        })
    
    except scheduler_client.exceptions.ConflictException:
        return response(409, {'error': 'Ya existe un schedule con ese nombre'})
    except Exception as e:
        print(f"Error creando schedule: {str(e)}")
        return response(500, {'error': str(e)})


def list_schedules(event):
    """
    Lista todos los schedules activos
    """
    try:
        # Obtener schedules de DynamoDB
        scan_response = schedule_table.scan()
        schedules = scan_response.get('Items', [])
        
        # También obtener información de EventBridge Scheduler
        eb_schedules = []
        try:
            paginator = scheduler_client.get_paginator('list_schedules')
            for page in paginator.paginate():
                eb_schedules.extend(page.get('Schedules', []))
        except Exception as e:
            print(f"Error listando schedules de EventBridge: {str(e)}")
        
        return response(200, {
            'count': len(schedules),
            'schedules': schedules,
            'eventBridgeSchedules': eb_schedules
        })
    
    except Exception as e:
        print(f"Error listando schedules: {str(e)}")
        return response(500, {'error': str(e)})


def get_schedule(event):
    """
    Obtiene detalles de un schedule específico
    """
    try:
        schedule_id = event['pathParameters']['scheduleId']
        
        # Buscar en DynamoDB
        scan_response = schedule_table.scan(
            FilterExpression='scheduleId = :sid',
            ExpressionAttributeValues={':sid': schedule_id}
        )
        
        items = scan_response.get('Items', [])
        if not items:
            return response(404, {'error': 'Schedule no encontrado'})
        
        schedule = items[0]
        
        # Obtener información adicional de EventBridge
        try:
            eb_schedule = scheduler_client.get_schedule(
                Name=schedule['scheduleName']
            )
            schedule['eventBridgeDetails'] = {
                'state': eb_schedule.get('State'),
                'arn': eb_schedule.get('Arn')
            }
        except Exception as e:
            print(f"Error obteniendo detalles de EventBridge: {str(e)}")
        
        return response(200, {'schedule': schedule})
    
    except Exception as e:
        print(f"Error obteniendo schedule: {str(e)}")
        return response(500, {'error': str(e)})


def delete_schedule(event):
    """
    Cancela un schedule existente
    """
    try:
        schedule_id = event['pathParameters']['scheduleId']
        
        # Buscar el schedule en DynamoDB
        scan_response = schedule_table.scan(
            FilterExpression='scheduleId = :sid',
            ExpressionAttributeValues={':sid': schedule_id}
        )
        
        items = scan_response.get('Items', [])
        if not items:
            return response(404, {'error': 'Schedule no encontrado'})
        
        schedule = items[0]
        schedule_name = schedule['scheduleName']
        
        # Eliminar de EventBridge Scheduler
        try:
            scheduler_client.delete_schedule(Name=schedule_name)
        except scheduler_client.exceptions.ResourceNotFoundException:
            print(f"Schedule {schedule_name} no encontrado en EventBridge")
        
        # Actualizar estado en DynamoDB
        schedule_table.update_item(
            Key={
                'scheduleId': schedule_id,
                'createdAt': schedule['createdAt']
            },
            UpdateExpression='SET #status = :status, deletedAt = :deleted_at',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': 'deleted',
                ':deleted_at': datetime.utcnow().isoformat()
            }
        )
        
        return response(200, {
            'message': 'Schedule cancelado exitosamente',
            'scheduleId': schedule_id
        })
    
    except Exception as e:
        print(f"Error eliminando schedule: {str(e)}")
        return response(500, {'error': str(e)})


def list_orders(event):
    """
    Lista las órdenes generadas (consulta a la tabla de órdenes)
    """
    try:
        orders_table_name = os.environ.get('ORDERS_TABLE_NAME', 'PurchaseOrdersTable')
        orders_table = dynamodb.Table(orders_table_name)
        
        # Parámetros de consulta
        query_params = event.get('queryStringParameters', {}) or {}
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', 50))
        
        # Escanear órdenes
        if status_filter:
            scan_response = orders_table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status_filter},
                Limit=limit
            )
        else:
            scan_response = orders_table.scan(Limit=limit)
        
        orders = scan_response.get('Items', [])
        
        return response(200, {
            'count': len(orders),
            'orders': orders
        })
    
    except Exception as e:
        print(f"Error listando órdenes: {str(e)}")
        return response(500, {'error': str(e)})


def response(status_code, body):
    """
    Genera una respuesta HTTP formateada para API Gateway
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
