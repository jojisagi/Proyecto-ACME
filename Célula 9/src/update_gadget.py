import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        gadget_id = event['pathParameters']['id']
        body = json.loads(event['body'])
        
        update_expr = 'SET '
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in body.items():
            if key != 'GadgetId':
                update_expr += f'#{key} = :{key}, '
                expr_attr_values[f':{key}'] = value
                expr_attr_names[f'#{key}'] = key
        
        update_expr += '#UpdatedAt = :UpdatedAt'
        expr_attr_values[':UpdatedAt'] = datetime.utcnow().isoformat()
        expr_attr_names['#UpdatedAt'] = 'UpdatedAt'
        
        response = table.update_item(
            Key={'GadgetId': gadget_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response['Attributes'])
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
