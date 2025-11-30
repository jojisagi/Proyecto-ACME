"""
Order Aggregator Lambda Function
Processes DynamoDB Stream events and updates aggregations
"""
import json
import os
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['AGGREGATIONS_TABLE'])

def handler(event, context):
    """
    Aggregate orders from DynamoDB Stream
    
    Args:
        event: DynamoDB Stream event
        context: Lambda context
    
    Returns:
        Response with status code
    """
    print(f"Processing {len(event['Records'])} stream records")
    
    aggregation_updates = {}
    
    for record in event['Records']:
        if record['eventName'] != 'INSERT':
            continue
        
        try:
            new_image = record['dynamodb']['NewImage']
            order_data = parse_dynamodb_item(new_image)
            
            # Generate aggregation keys
            updates = generate_aggregations(order_data)
            
            # Merge updates
            for key, value in updates.items():
                if key not in aggregation_updates:
                    aggregation_updates[key] = value
                else:
                    aggregation_updates[key]['orderCount'] += value['orderCount']
                    aggregation_updates[key]['totalQuantity'] += value['totalQuantity']
                    aggregation_updates[key]['totalRevenue'] += value['totalRevenue']
        
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            continue
    
    # Batch update aggregations
    for agg_key, agg_data in aggregation_updates.items():
        try:
            update_aggregation(agg_key, agg_data)
        except Exception as e:
            print(f"Error updating aggregation {agg_key}: {str(e)}")
    
    return {'statusCode': 200}

def parse_dynamodb_item(item):
    """Parse DynamoDB item from stream"""
    return {
        'customerId': item['customerId']['S'],
        'gadgetId': item['gadgetId']['S'],
        'category': item['category']['S'],
        'quantity': Decimal(item['quantity']['N']),
        'totalAmount': Decimal(item['totalAmount']['N']),
        'timestamp': int(item['timestamp']['N'])
    }

def generate_aggregations(order_data):
    """Generate all aggregation keys and values"""
    dt = datetime.fromtimestamp(order_data['timestamp'] / 1000)
    
    periods = {
        'daily': dt.strftime('%Y-%m-%d'),
        'weekly': dt.strftime('%Y-W%U'),
        'monthly': dt.strftime('%Y-%m')
    }
    
    aggregations = {}
    
    for period_type, period_value in periods.items():
        # By gadget
        key = f"gadget#{order_data['gadgetId']}#{period_type}#{period_value}"
        aggregations[key] = create_agg_value(
            f"gadget#{order_data['gadgetId']}",
            f"{period_type}#{period_value}",
            order_data
        )
        
        # By category
        key = f"category#{order_data['category']}#{period_type}#{period_value}"
        aggregations[key] = create_agg_value(
            f"category#{order_data['category']}",
            f"{period_type}#{period_value}",
            order_data
        )
        
        # By customer
        key = f"customer#{order_data['customerId']}#{period_type}#{period_value}"
        aggregations[key] = create_agg_value(
            f"customer#{order_data['customerId']}",
            f"{period_type}#{period_value}",
            order_data
        )
    
    return aggregations

def create_agg_value(agg_key, period, order_data):
    """Create aggregation value object"""
    return {
        'aggregationKey': agg_key,
        'period': period,
        'orderCount': 1,
        'totalQuantity': order_data['quantity'],
        'totalRevenue': order_data['totalAmount']
    }

def update_aggregation(key, data):
    """Update aggregation in DynamoDB"""
    table.update_item(
        Key={
            'aggregationKey': data['aggregationKey'],
            'period': data['period']
        },
        UpdateExpression='ADD orderCount :count, totalQuantity :qty, totalRevenue :rev',
        ExpressionAttributeValues={
            ':count': data['orderCount'],
            ':qty': data['totalQuantity'],
            ':rev': data['totalRevenue']
        }
    )
