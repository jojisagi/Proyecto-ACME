mport json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
results_table = dynamodb.Table('VoteResults')

def lambda_handler(event, context):
    response = results_table.scan()
    results = response.get("Items", [])

    if not results:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "No se ha votado aún"})
        }

    # Convertir Decimals a float para que json.dumps funcione
    for item in results:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)

    return {
        "statusCode": 200,
        "body": json.dumps({"votes": results})
    }

