import json
import boto3
import os
from datetime import datetime
import uuid
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
table = dynamodb.Table('Orders')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Lambda handler para el servidor de aplicaciones
    Maneja las solicitudes HTTP del API Gateway
    """
    print(f"Event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    # Routing
    if http_method == 'POST' and path == '/orders':
        return create_order(event)
    elif http_method == 'GET' and path == '/orders':
        return get_orders(event)
    elif http_method == 'GET' and '/orders/' in path:
        return get_order(event)
    elif http_method == 'GET' and path == '/health':
        return health_check()
    else:
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Not found'})
        }

def create_order(event):
    """Crear una nueva orden"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validar datos requeridos
        required_fields = ['customerId', 'customerName', 'customerEmail', 'items', 'totalAmount']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }
        
        order_id = str(uuid.uuid4())
        order = {
            'orderId': order_id,
            'customerId': body.get('customerId'),
            'customerName': body.get('customerName'),
            'customerEmail': body.get('customerEmail'),
            'items': body.get('items', []),
            'totalAmount': Decimal(str(body.get('totalAmount'))),
            'status': 'PENDING',
            'orderDate': datetime.utcnow().isoformat(),
            'shippingAddress': body.get('shippingAddress', {}),
            'paymentMethod': body.get('paymentMethod', 'credit_card')
        }
        
        # Guardar en DynamoDB
        table.put_item(Item=order)
        
        # Enviar a SQS para procesamiento asíncrono
        queue_url = os.environ.get('QUEUE_URL')
        if queue_url:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps({'orderId': order_id})
            )
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(order, cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def get_orders(event):
    """Obtener todas las órdenes"""
    try:
        # Obtener parámetros de query
        query_params = event.get('queryStringParameters') or {}
        customer_id = query_params.get('customerId')
        
        if customer_id:
            # Buscar por cliente usando GSI
            response = table.query(
                IndexName='CustomerIndex',
                KeyConditionExpression='customerId = :cid',
                ExpressionAttributeValues={':cid': customer_id}
            )
        else:
            # Scan completo (limitado)
            response = table.scan(Limit=50)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response.get('Items', []), cls=DecimalEncoder)
        }
    except Exception as e:
        print(f"Error getting orders: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def get_order(event):
    """Obtener una orden específica"""
    try:
        order_id = event['path'].split('/')[-1]
        response = table.get_item(Key={'orderId': order_id})
        
        if 'Item' in response:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response['Item'], cls=DecimalEncoder)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Order not found'})
            }
    except Exception as e:
        print(f"Error getting order: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

def health_check():
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'app-server',
            'timestamp': datetime.utcnow().isoformat()
        })
    }
