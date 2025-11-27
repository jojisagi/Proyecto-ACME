import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
results_table = dynamodb.Table(os.environ['RESULTS_TABLE'])

def lambda_handler(event, context):
    """
    Lambda para procesar DynamoDB Streams.
    Se dispara automáticamente al recibir nuevos votos.
    Actualiza contadores atómicamente en VoteResults.
    """
    try:
        processed_records = 0
        
        for record in event['Records']:
            # Solo procesar inserciones nuevas
            if record['eventName'] == 'INSERT':
                # Extraer datos del nuevo voto
                new_image = record['dynamodb']['NewImage']
                gadget_id = new_image['gadgetId']['S']
                
                print(f"Procesando voto para gadget: {gadget_id}")
                
                # Incrementar contador atómicamente
                try:
                    results_table.update_item(
                        Key={'gadgetId': gadget_id},
                        UpdateExpression='ADD totalVotes :inc',
                        ExpressionAttributeValues={':inc': 1}
                    )
                    processed_records += 1
                    print(f"Voto agregado exitosamente para {gadget_id}")
                    
                except Exception as e:
                    print(f"Error actualizando contador para {gadget_id}: {str(e)}")
                    raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Procesados {processed_records} votos',
                'processedRecords': processed_records
            })
        }
        
    except Exception as e:
        print(f"Error procesando stream: {str(e)}")
        # Re-lanzar excepción para que Lambda reintente
        raise
