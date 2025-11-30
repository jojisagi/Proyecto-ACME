"""
Order Processor Lambda Function
Receives orders from EventBridge and stores them in DynamoDB
"""
import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ORDERS_TABLE'])

def handler(event, context):
    """
    Process incoming purchase orders
    
    Args:
        event: EventBridge event or direct invocation
        context: Lambda context
    
    Returns:
        Response with status code and message
    """
    print(f"Processing event: {json.dumps(event, default=str)}")
    
    processed_count = 0
    errors = []
    
    try:
        # Handle EventBridge events
        if 'detail' in event:
            orders = [event['detail']]
        # Handle batch events
        elif 'Records' in event:
            orders = [json.loads(r.get('body', r)) for r in event['Records']]
        # Handle direct invocation
        else:
            orders = [event]
        
        for order in orders:
            try:
                process_order(order)
                processed_count += 1
            except Exception as e:
                error_msg = f"Failed to process order {order.get('orderId')}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
        
        return {
            'statusCode': 200 if not errors else 207,
            'body': json.dumps({
                'processed': processed_count,
                'errors': errors
            })
        }
    
    except Exception as e:
        print(f"Critical error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_order(order):
    """Store order in DynamoDB"""
    order_id = order['orderId']
    timestamp = int(datetime.now().timestamp() * 1000)
    
    item = {
        'orderId': order_id,
        'timestamp': timestamp,
        'customerId': order['customerId'],
        'gadgetId': order['gadgetId'],
        'gadgetName': order.get('gadgetName', ''),
        'category': order['category'],
        'quantity': Decimal(str(order['quantity'])),
        'price': Decimal(str(order['price'])),
        'totalAmount': Decimal(str(order['quantity'])) * Decimal(str(order['price'])),
        'status': 'processed'
    }
    
    table.put_item(Item=item)
    print(f"Successfully stored order: {order_id}")
