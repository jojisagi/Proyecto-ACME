import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
votes_table = dynamodb.Table('Votes')
results_table = dynamodb.Table('VoteResults')
gadgets_table = dynamodb.Table('GadgetPrueba')  # tabla de gadgets

def lambda_handler(event, context):

    body = json.loads(event["body"])

    user_id = body.get("userID")
    vote_id = body.get("voteId")
    gadget_id = body.get("gadgetId")

    print("userID:", user_id)
    print("voteId:", vote_id)
    print("gadgetId:", gadget_id)

    # Verificar si el gadget existe
    try:
        response = gadgets_table.get_item(Key={'gadgetId': gadget_id})
        if 'Item' not in response:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Gadget not found"})
            }
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error checking gadget", "error": str(e)})
        }

    # Guardar voto solo si no existe un voto previo del mismo usuario
    try:
        votes_table.put_item(
            Item={
                'userID': user_id,       
                'voteId': vote_id,       
                'gadgetId': gadget_id,
                'timestamp': datetime.utcnow().isoformat()
            },
            ConditionExpression="attribute_not_exists(userID)"
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "User has already voted"})
            }
        else:
            raise

    # Actualizar conteo en VoteResults
    results_table.update_item(
        Key={'gadgetId': gadget_id},
        UpdateExpression="SET totalVotes = if_not_exists(totalVotes, :zero) + :inc",
        ExpressionAttributeValues={
            ":inc": 1,
            ":zero": 0
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Vote recorded", "gadgetId": gadget_id})
    }

