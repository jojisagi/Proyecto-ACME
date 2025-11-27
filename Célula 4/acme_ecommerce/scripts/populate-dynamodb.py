#!/usr/bin/env python3
"""
Script para poblar DynamoDB con datos de muestra
"""
import json
import boto3
from decimal import Decimal

def convert_floats_to_decimal(obj):
    """Convertir floats a Decimal para DynamoDB"""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def main():
    # Inicializar cliente DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Orders')
    
    # Cargar datos
    with open('data/orders-50.json', 'r', encoding='utf-8') as f:
        orders = json.load(f)
    
    print(f"Cargando {len(orders)} órdenes a DynamoDB...")
    
    # Insertar cada orden
    success_count = 0
    error_count = 0
    
    for order in orders:
        try:
            # Convertir floats a Decimal
            order_converted = convert_floats_to_decimal(order)
            
            # Insertar en DynamoDB
            table.put_item(Item=order_converted)
            success_count += 1
            print(f"✓ Insertada orden {order['orderId']}")
        except Exception as e:
            error_count += 1
            print(f"✗ Error insertando orden {order['orderId']}: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Resumen:")
    print(f"  Exitosas: {success_count}")
    print(f"  Errores: {error_count}")
    print(f"  Total: {len(orders)}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
