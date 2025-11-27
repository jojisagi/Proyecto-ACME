import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('GadgetPrueba')

def lambda_handler(event, context):
    try:
        body = event.get('body')
        if body:
            data = json.loads(body)
        else:
            data = event
        gadget_id = data['gadgetId']
        nombre = data['nombre']
        categorias = data['categorias']  # ⚠ cambiar aquí
        descripcion = data['descripcion']  # ⚠ también quitar tilde
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f'Missing parameter: {str(e)}')
        }

    item = {
        'gadgetId': gadget_id,
        'nombre': nombre,
        'categorias': categorias,  # ⚠ mismo cambio
        'descripcion': descripcion  # ⚠ mismo cambio
    }

    try:
        table.put_item(Item=item)
        return {
            'statusCode': 200,
            'body': json.dumps(f'Gadget {gadget_id} insertado correctamente')
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error al insertar el gadget: {e.response["Error"]["Message"]}')
        }
