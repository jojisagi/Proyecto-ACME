import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import random

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table('Orders')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Lambda handler para procesamiento de órdenes
    Maneja diferentes acciones del flujo de trabajo
    """
    print(f"Processing order event: {json.dumps(event)}")
    
    order_id = event.get('orderId')
    action = event.get('action', 'process_payment')
    
    if not order_id:
        raise ValueError('orderId is required')
    
    if action == 'process_payment':
        return process_payment(order_id)
    elif action == 'arrange_shipment':
        return arrange_shipment(order_id)
    elif action == 'send_notification':
        return send_notification(order_id)
    else:
        raise ValueError(f'Unknown action: {action}')

def process_payment(order_id):
    """
    Procesar pago de la orden
    Simula integración con sistema de pagos externo
    """
    try:
        # Obtener detalles de la orden
        response = table.get_item(Key={'orderId': order_id})
        order = response.get('Item')
        
        if not order:
            raise ValueError(f'Order {order_id} not found')
        
        # Simular procesamiento de pago (90% éxito)
        payment_success = random.random() > 0.1
        
        if not payment_success:
            # Actualizar estado a PAYMENT_FAILED
            table.update_item(
                Key={'orderId': order_id},
                UpdateExpression='SET #status = :status, paymentFailedDate = :date',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'PAYMENT_FAILED',
                    ':date': datetime.utcnow().isoformat()
                }
            )
            raise Exception('Payment processing failed')
        
        # Actualizar estado a PAYMENT_PROCESSED
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, paymentDate = :date, transactionId = :txn',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PAYMENT_PROCESSED',
                ':date': datetime.utcnow().isoformat(),
                ':txn': f'TXN-{order_id[:8]}'
            }
        )
        
        print(f'Payment processed successfully for order {order_id}')
        return {
            'status': 'payment_processed',
            'orderId': order_id,
            'transactionId': f'TXN-{order_id[:8]}'
        }
    except Exception as e:
        print(f'Error processing payment: {str(e)}')
        raise

def arrange_shipment(order_id):
    """
    Arreglar envío de la orden
    Simula integración con sistema de envíos externo
    """
    try:
        # Obtener detalles de la orden
        response = table.get_item(Key={'orderId': order_id})
        order = response.get('Item')
        
        if not order:
            raise ValueError(f'Order {order_id} not found')
        
        # Generar número de tracking
        tracking_number = f'TRACK-{order_id[:12].upper()}'
        
        # Calcular fecha estimada de entrega (3-5 días)
        estimated_days = random.randint(3, 5)
        
        # Actualizar estado a SHIPPED
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #status = :status, shipmentDate = :date, trackingNumber = :tracking, estimatedDeliveryDays = :days',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'SHIPPED',
                ':date': datetime.utcnow().isoformat(),
                ':tracking': tracking_number,
                ':days': estimated_days
            }
        )
        
        print(f'Shipment arranged for order {order_id}, tracking: {tracking_number}')
        return {
            'status': 'shipped',
            'orderId': order_id,
            'trackingNumber': tracking_number,
            'estimatedDeliveryDays': estimated_days
        }
    except Exception as e:
        print(f'Error arranging shipment: {str(e)}')
        raise

def send_notification(order_id):
    """
    Enviar notificación al cliente
    Publica mensaje a SNS Topic
    """
    try:
        # Obtener detalles de la orden
        response = table.get_item(Key={'orderId': order_id})
        order = response.get('Item')
        
        if not order:
            raise ValueError(f'Order {order_id} not found')
        
        # Preparar mensaje de notificación
        items_summary = '\n'.join([
            f"  - {item.get('name', 'Item')} x{item.get('quantity', 1)} - ${float(item.get('price', 0))}"
            for item in order.get('items', [])
        ])
        
        message = f"""
Order Confirmation - E-commerce Store

Dear {order.get('customerName', 'Customer')},

Thank you for your order!

Order Details:
--------------
Order ID: {order_id}
Order Date: {order.get('orderDate', 'N/A')}
Status: {order.get('status', 'N/A')}

Items:
{items_summary}

Total Amount: ${float(order.get('totalAmount', 0))}

Shipping Address:
{order.get('shippingAddress', {}).get('street', '')}, 
{order.get('shippingAddress', {}).get('city', '')}, 
{order.get('shippingAddress', {}).get('state', '')} {order.get('shippingAddress', {}).get('zipCode', '')}

Tracking Number: {order.get('trackingNumber', 'Will be provided soon')}
Estimated Delivery: {order.get('estimatedDeliveryDays', 'N/A')} business days

Thank you for shopping with us!

Best regards,
E-commerce Team
        """
        
        # Publicar a SNS
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if sns_topic_arn:
            sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f'Order Confirmation - {order_id}',
                Message=message,
                MessageAttributes={
                    'orderId': {'DataType': 'String', 'StringValue': order_id},
                    'customerEmail': {'DataType': 'String', 'StringValue': order.get('customerEmail', '')}
                }
            )
        
        # Actualizar orden con fecha de notificación
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET notificationSentDate = :date',
            ExpressionAttributeValues={
                ':date': datetime.utcnow().isoformat()
            }
        )
        
        print(f'Notification sent for order {order_id}')
        return {
            'status': 'notification_sent',
            'orderId': order_id,
            'customerEmail': order.get('customerEmail')
        }
    except Exception as e:
        print(f'Error sending notification: {str(e)}')
        raise
