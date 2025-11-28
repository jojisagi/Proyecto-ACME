import json
import boto3
import os
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        gadget_id = str(uuid.uuid4())
        item = {
            'GadgetId': gadget_id,
            'Name': body['Name'],
            'Category': body['Category'],
            'MaxSpeed': body['MaxSpeed'],
            'PropulsionType': body['PropulsionType'],
            'Seats': body['Seats'],
            'Status': body.get('Status', 'Active'),
            'CreatedAt': datetime.utcnow().isoformat()
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(item)
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
