"""
Lambda Function: Order Executor
Genera órdenes de compra automáticamente cuando es invocada por EventBridge Scheduler
"""

import json
import os
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

# Clientes AWS
dynamodb = boto3.resource('dynamodb')

# Variables de entorno
ORDERS_TABLE_NAME = os.environ['ORDERS_TABLE_NAME']
SCHEDULE_TABLE_NAME = os.environ['SCHEDULE_TABLE_NAME']

orders_table = dynamodb.Table(ORDERS_TABLE_NAME)
schedule_table = dynamodb.Table(SCHEDULE_TABLE_NAME)


def lambda_handler(event, context):
    """
    Handler principal que genera una orden de compra
    
    Event esperado (desde EventBridge Scheduler):
    {
        "scheduleId": "uuid",
        "gadgetType": "Rocket Shoes",
        "quantity": 100
    }
    """
    print(f"Event received: {json.dumps(event)}")
    
    try:
        # Extraer datos del evento
        schedule_id = event.get('scheduleId')
        gadget_type = event.get('gadgetType')
        quantity = event.get('quantity', 1)
        
        if not schedule_id or not gadget_type:
            raise ValueError("scheduleId y gadgetType son requeridos")
        
        # Obtener información adicional del schedule
        schedule_info = get_schedule_info(schedule_id)
        
        # Generar la orden de compra
        order = generate_purchase_order(
            schedule_id=schedule_id,
            gadget_type=gadget_type,
            quantity=quantity,
            schedule_info=schedule_info
        )
        
        # Guardar en DynamoDB
        orders_table.put_item(Item=order)
        
        print(f"Orden creada exitosamente: {order['orderId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Orden generada exitosamente',
                'orderId': order['orderId']
            })
        }
    
    except Exception as e:
        print(f"Error generando orden: {str(e)}")
        
        # Registrar el error pero no fallar completamente
        error_order = {
            'orderId': str(uuid.uuid4()),
            'createdAt': datetime.utcnow().isoformat(),
            'status': 'failed',
            'error': str(e),
            'event': event
        }
        
        try:
            orders_table.put_item(Item=error_order)
        except Exception as db_error:
            print(f"Error guardando orden fallida: {str(db_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def get_schedule_info(schedule_id):
    """
    Obtiene información del schedule desde DynamoDB
    """
    try:
        response = schedule_table.scan(
            FilterExpression='scheduleId = :sid',
            ExpressionAttributeValues={':sid': schedule_id}
        )
        
        items = response.get('Items', [])
        if items:
            return items[0]
        return None
    
    except Exception as e:
        print(f"Error obteniendo info del schedule: {str(e)}")
        return None


def generate_purchase_order(schedule_id, gadget_type, quantity, schedule_info=None):
    """
    Genera una orden de compra con lógica de negocio
    
    Reglas de negocio simuladas:
    - Calcula precio unitario basado en el tipo de gadget
    - Aplica descuentos por volumen
    - Determina prioridad según cantidad
    - Asigna proveedor según tipo de producto
    """
    order_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Lógica de negocio: Precio base por tipo de gadget
    base_prices = {
        'Rocket Shoes': Decimal('299.99'),
        'Jetpack': Decimal('4999.99'),
        'Laser Pointer': Decimal('49.99'),
        'Invisible Cloak': Decimal('1999.99'),
        'Time Turner': Decimal('9999.99'),
        'Teleporter': Decimal('15999.99'),
        'Hoverboard': Decimal('899.99'),
        'Smart Glasses': Decimal('399.99'),
        'Drone': Decimal('599.99'),
        'Robot Assistant': Decimal('2499.99')
    }
    
    unit_price = base_prices.get(gadget_type, Decimal('99.99'))
    
    # Descuento por volumen
    discount_rate = Decimal('0')
    if quantity >= 100:
        discount_rate = Decimal('0.15')  # 15% descuento
    elif quantity >= 50:
        discount_rate = Decimal('0.10')  # 10% descuento
    elif quantity >= 20:
        discount_rate = Decimal('0.05')  # 5% descuento
    
    subtotal = unit_price * Decimal(quantity)
    discount_amount = subtotal * discount_rate
    total = subtotal - discount_amount
    
    # Determinar prioridad
    if quantity >= 100:
        priority = 'high'
    elif quantity >= 50:
        priority = 'medium'
    else:
        priority = 'normal'
    
    # Asignar proveedor según tipo de producto
    suppliers = {
        'Rocket Shoes': 'AcmeTech Footwear Inc.',
        'Jetpack': 'SkyHigh Industries',
        'Laser Pointer': 'PhotonWorks Ltd.',
        'Invisible Cloak': 'Stealth Solutions',
        'Time Turner': 'Temporal Dynamics Corp.',
        'Teleporter': 'Quantum Transport Systems',
        'Hoverboard': 'AntiGrav Technologies',
        'Smart Glasses': 'VisionTech Solutions',
        'Drone': 'AeroBot Industries',
        'Robot Assistant': 'AI Companions Inc.'
    }
    
    supplier = suppliers.get(gadget_type, 'General Supplier Co.')
    
    # Construir la orden
    order = {
        'orderId': order_id,
        'createdAt': timestamp,
        'scheduleId': schedule_id,
        'gadgetType': gadget_type,
        'quantity': quantity,
        'unitPrice': unit_price,
        'subtotal': subtotal,
        'discountRate': discount_rate,
        'discountAmount': discount_amount,
        'total': total,
        'priority': priority,
        'supplier': supplier,
        'status': 'pending',
        'estimatedDeliveryDays': 7 if priority == 'high' else 14,
        'metadata': {
            'generatedBy': 'EventBridge Scheduler',
            'scheduleName': schedule_info.get('scheduleName') if schedule_info else 'Unknown',
            'frequency': schedule_info.get('frequency') if schedule_info else 'Unknown'
        }
    }
    
    return order


def calculate_estimated_delivery(priority):
    """
    Calcula fecha estimada de entrega según prioridad
    """
    from datetime import timedelta
    
    days_map = {
        'high': 7,
        'medium': 14,
        'normal': 21
    }
    
    days = days_map.get(priority, 21)
    estimated_date = datetime.utcnow() + timedelta(days=days)
    
    return estimated_date.isoformat()
