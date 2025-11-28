"""
Order API Lambda Function
Provides REST API endpoints for querying orders and aggregations
"""
import json
import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
agg_table = dynamodb.Table(os.environ['AGGREGATIONS_TABLE'])

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event, context):
    """
    Handle API Gateway requests
    
    Args:
        event: API Gateway event
        context: Lambda context
    
    Returns:
        API Gateway response
    """
    print(f"API Request: {event.get('httpMethod')} {event.get('path')}")
    
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    try:
        if path == '/orders' and method == 'GET':
            return get_orders(event)
        elif path == '/orders' and method == 'POST':
            return create_order(event)
        elif path == '/aggregations' and method == 'GET':
            return get_aggregations(event)
        else:
            return error_response(404, 'Endpoint not found')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, str(e))

def get_orders(event):
    """Get orders with optional filtering"""
    params = event.get('queryStringParameters') or {}
    customer_id = params.get('customerId')
    limit = int(params.get('limit', 100))
    
    try:
        if customer_id:
            response = orders_table.query(
                IndexName='CustomerIndex',
                KeyConditionExpression=Key('customerId').eq(customer_id),
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            response = orders_table.scan(Limit=limit)
        
        return success_response(response['Items'])
    
    except Exception as e:
        return error_response(500, f"Failed to query orders: {str(e)}")

def create_order(event):
    """Create a new order (for testing)"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required = ['orderId', 'customerId', 'gadgetId', 'category', 'quantity', 'price']
        for field in required:
            if field not in body:
                return error_response(400, f"Missing required field: {field}")
        
        # This would typically trigger EventBridge event
        # For now, return success
        return success_response({'message': 'Order received', 'orderId': body['orderId']})
    
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON')

def get_aggregations(event):
    """Get aggregations with filtering"""
    params = event.get('queryStringParameters') or {}
    agg_type = params.get('type', 'gadget')
    agg_id = params.get('id', '')
    period_type = params.get('period', 'daily')
    limit = int(params.get('limit', 100))
    
    try:
        if not agg_id:
            return error_response(400, 'Missing required parameter: id')
        
        agg_key = f"{agg_type}#{agg_id}"
        
        response = agg_table.query(
            KeyConditionExpression=Key('aggregationKey').eq(agg_key) & Key('period').begins_with(period_type),
            Limit=limit,
            ScanIndexForward=False
        )
        
        return success_response(response['Items'])
    
    except Exception as e:
        return error_response(500, f"Failed to query aggregations: {str(e)}")

def success_response(data):
    """Create success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data, cls=DecimalEncoder)
    }

def error_response(status_code, message):
    """Create error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }
