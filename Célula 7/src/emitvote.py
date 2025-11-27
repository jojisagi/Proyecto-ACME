import json
import os
import time
import uuid
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['VOTES_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        gadgetId = body.get("gadgetId")

        if not gadgetId:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing gadgetId"})
            }

        # Claims vienen desde API Gateway (Cognito)
        claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
        userId = claims["sub"]  # ID del usuario autenticado

        voteId = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)

        # Inserción atómica para evitar doble voto
        table.put_item(
            Item={
                "userId": userId,
                "voteId": voteId,
                "gadgetId": gadgetId,
                "timestamp": timestamp
            },
            ConditionExpression="attribute_not_exists(userId)"
        )

        return {
            "statusCode": 201,
            "body": json.dumps({"message": "Vote registered", "voteId": voteId})
        }

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return {
            "statusCode": 409,
            "body": json.dumps({"error": "User already voted"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
