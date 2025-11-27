import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
results_table = dynamodb.Table(os.environ['RESULTS_TABLE'])

def lambda_handler(event, context):
    try:
        for record in event.get("Records", []):
            if record["eventName"] != "INSERT":
                continue

            new_image = record["dynamodb"].get("NewImage", {})
            gadgetId = new_image["gadgetId"]["S"]

            # Actualizar tabla de resultados
            results_table.update_item(
                Key={"gadgetId": gadgetId},
                UpdateExpression="SET totalVotes = if_not_exists(totalVotes, :zero) + :inc, lastUpdated = :ts",
                ExpressionAttributeValues={
                    ":inc": 1,
                    ":zero": 0,
                    ":ts": datetime.utcnow().isoformat()
                }
            )

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print("Error:", str(e))
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
