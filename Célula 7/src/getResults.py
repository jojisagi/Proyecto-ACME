import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['RESULTS_TABLE'])

def lambda_handler(event, context):
    try:
        # Escaneo completo (tabla pequeña)
        response = table.scan()

        items = response.get("Items", [])

        return {
            "statusCode": 200,
            "body": json.dumps(items)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
