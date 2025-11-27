import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
results_table = dynamodb.Table(os.environ['RESULTS_TABLE'])

class DecimalEncoder(json.JSONEncoder):
    """Helper para serializar Decimal de DynamoDB a JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Lambda para consultar resultados de votación.
    Lee directamente de VoteResults para máxima velocidad.
    """
    try:
        # Escanear toda la tabla de resultados
        response = results_table.scan()
        items = response.get('Items', [])
        
        # Continuar escaneando si hay más páginas
        while 'LastEvaluatedKey' in response:
            response = results_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
        
        # Ordenar por totalVotes descendente
        items.sort(key=lambda x: x.get('totalVotes', 0), reverse=True)
        
        # Calcular total de votos
        total_votes = sum(item.get('totalVotes', 0) for item in items)
        
        # Formatear resultados
        results = []
        for item in items:
            votes = int(item.get('totalVotes', 0))
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            
            results.append({
                'gadgetId': item['gadgetId'],
                'gadgetName': item.get('gadgetName', item['gadgetId']),
                'totalVotes': votes,
                'percentage': round(percentage, 2)
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'results': results,
                'totalVotes': int(total_votes),
                'timestamp': context.request_id
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'Error al obtener resultados'})
        }
