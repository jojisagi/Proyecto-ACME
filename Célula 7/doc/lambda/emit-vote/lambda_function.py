import json
import os
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
votes_table = dynamodb.Table(os.environ['VOTES_TABLE'])

def lambda_handler(event, context):
    """
    Lambda para registrar votos.
    Valida token de Cognito, verifica idempotencia y registra el voto.
    """
    try:
        # Extraer userId del contexto de Cognito
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Parsear body
        body = json.loads(event['body'])
        gadget_id = body.get('gadgetId')
        
        if not gadget_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'gadgetId es requerido'})
            }
        
        # Verificar si el usuario ya votó (idempotencia)
        try:
            response = votes_table.get_item(
                Key={
                    'userId': user_id,
                    'voteId': 'VOTE'
                }
            )
            
            if 'Item' in response:
                return {
                    'statusCode': 409,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'error': 'Usuario ya ha votado',
                        'existingVote': response['Item']['gadgetId']
                    })
                }
        except Exception as e:
            print(f"Error verificando voto existente: {str(e)}")
        
        # Registrar el voto
        vote_item = {
            'userId': user_id,
            'voteId': 'VOTE',
            'gadgetId': gadget_id,
            'timestamp': datetime.utcnow().isoformat(),
            'voteUuid': str(uuid.uuid4())
        }
        
        votes_table.put_item(Item=vote_item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Voto registrado exitosamente',
                'gadgetId': gadget_id,
                'timestamp': vote_item['timestamp']
            })
        }
        
    except KeyError as e:
        return {
            'statusCode': 401,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Token de autenticación inválido'})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Error interno del servidor'})
        }
