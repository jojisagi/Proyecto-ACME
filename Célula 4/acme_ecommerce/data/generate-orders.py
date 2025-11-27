#!/usr/bin/env python3
"""
Script para generar 50 órdenes de muestra para DynamoDB
"""
import json
import random
from datetime import datetime, timedelta
import uuid

# Datos de muestra
CUSTOMERS = [
    {"id": "cust-001", "name": "María García", "email": "maria.garcia@email.com"},
    {"id": "cust-002", "name": "Juan Pérez", "email": "juan.perez@email.com"},
    {"id": "cust-003", "name": "Ana Martínez", "email": "ana.martinez@email.com"},
    {"id": "cust-004", "name": "Carlos Rodríguez", "email": "carlos.rodriguez@email.com"},
    {"id": "cust-005", "name": "Laura Sánchez", "email": "laura.sanchez@email.com"},
    {"id": "cust-006", "name": "Pedro López", "email": "pedro.lopez@email.com"},
    {"id": "cust-007", "name": "Isabel Fernández", "email": "isabel.fernandez@email.com"},
    {"id": "cust-008", "name": "Miguel Torres", "email": "miguel.torres@email.com"},
    {"id": "cust-009", "name": "Carmen Ruiz", "email": "carmen.ruiz@email.com"},
    {"id": "cust-010", "name": "David Moreno", "email": "david.moreno@email.com"},
]

PRODUCTS = [
    {"id": "prod-101", "name": "Laptop HP 15", "price": 299.99},
    {"id": "prod-102", "name": "Laptop Dell Inspiron", "price": 449.99},
    {"id": "prod-103", "name": "MacBook Air M2", "price": 999.99},
    {"id": "prod-104", "name": "MacBook Pro 14", "price": 1299.99},
    {"id": "prod-201", "name": "Mouse Inalámbrico", "price": 24.99},
    {"id": "prod-202", "name": "Teclado Mecánico", "price": 79.99},
    {"id": "prod-203", "name": "Webcam HD", "price": 89.99},
    {"id": "prod-301", "name": "Monitor 24 pulgadas", "price": 199.99},
    {"id": "prod-302", "name": "Monitor 27 pulgadas", "price": 349.00},
    {"id": "prod-303", "name": "Monitor 32 pulgadas 4K", "price": 599.99},
    {"id": "prod-401", "name": "Auriculares Bluetooth", "price": 79.99},
    {"id": "prod-402", "name": "Auriculares Gaming", "price": 129.99},
    {"id": "prod-501", "name": "Disco Duro Externo 1TB", "price": 129.99},
    {"id": "prod-502", "name": "SSD Externo 500GB", "price": 89.99},
    {"id": "prod-503", "name": "Memoria USB 64GB", "price": 19.99},
    {"id": "prod-601", "name": "Cable USB-C", "price": 15.99},
    {"id": "prod-602", "name": "Hub USB 4 puertos", "price": 29.99},
    {"id": "prod-701", "name": "Tablet Samsung", "price": 399.99},
    {"id": "prod-702", "name": "iPad Air", "price": 599.99},
    {"id": "prod-801", "name": "Impresora WiFi", "price": 189.99},
    {"id": "prod-802", "name": "Escáner Portátil", "price": 149.99},
    {"id": "prod-901", "name": "Silla Gaming", "price": 299.99},
    {"id": "prod-902", "name": "Escritorio Ajustable", "price": 449.99},
    {"id": "prod-1001", "name": "Router WiFi 6", "price": 129.99},
    {"id": "prod-1002", "name": "Cámara Web 4K", "price": 199.99},
]

CITIES = [
    {"city": "Madrid", "state": "Madrid", "zipCode": "28001"},
    {"city": "Barcelona", "state": "Cataluña", "zipCode": "08001"},
    {"city": "Valencia", "state": "Valencia", "zipCode": "46001"},
    {"city": "Sevilla", "state": "Andalucía", "zipCode": "41001"},
    {"city": "Bilbao", "state": "País Vasco", "zipCode": "48001"},
    {"city": "Zaragoza", "state": "Aragón", "zipCode": "50001"},
    {"city": "Málaga", "state": "Andalucía", "zipCode": "29001"},
    {"city": "Murcia", "state": "Murcia", "zipCode": "30001"},
]

STATUSES = ["PENDING", "PAYMENT_PROCESSED", "SHIPPED", "DELIVERED"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal"]

def generate_order(order_num):
    """Generar una orden de muestra"""
    customer = random.choice(CUSTOMERS)
    
    # Generar items (1-4 productos)
    num_items = random.randint(1, 4)
    items = []
    total_amount = 0
    
    for _ in range(num_items):
        product = random.choice(PRODUCTS)
        quantity = random.randint(1, 3)
        items.append({
            "productId": product["id"],
            "name": product["name"],
            "quantity": quantity,
            "price": product["price"]
        })
        total_amount += product["price"] * quantity
    
    # Fecha aleatoria en los últimos 30 días
    days_ago = random.randint(0, 30)
    order_date = datetime.utcnow() - timedelta(days=days_ago)
    
    # Dirección de envío
    location = random.choice(CITIES)
    shipping_address = {
        "street": f"Calle {random.choice(['Principal', 'Mayor', 'Sol', 'Luna', 'Norte'])} {random.randint(1, 999)}",
        "city": location["city"],
        "state": location["state"],
        "zipCode": location["zipCode"],
        "country": "España"
    }
    
    order = {
        "orderId": f"order-{str(order_num).zfill(3)}",
        "customerId": customer["id"],
        "customerName": customer["name"],
        "customerEmail": customer["email"],
        "orderDate": order_date.isoformat() + "Z",
        "status": random.choice(STATUSES),
        "totalAmount": round(total_amount, 2),
        "paymentMethod": random.choice(PAYMENT_METHODS),
        "items": items,
        "shippingAddress": shipping_address
    }
    
    # Agregar campos adicionales según el estado
    if order["status"] in ["PAYMENT_PROCESSED", "SHIPPED", "DELIVERED"]:
        order["paymentDate"] = (order_date + timedelta(hours=1)).isoformat() + "Z"
        order["transactionId"] = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    
    if order["status"] in ["SHIPPED", "DELIVERED"]:
        order["shipmentDate"] = (order_date + timedelta(days=1)).isoformat() + "Z"
        order["trackingNumber"] = f"TRACK-{uuid.uuid4().hex[:12].upper()}"
        order["estimatedDeliveryDays"] = random.randint(3, 5)
    
    if order["status"] == "DELIVERED":
        order["deliveryDate"] = (order_date + timedelta(days=random.randint(3, 7))).isoformat() + "Z"
    
    return order

def main():
    """Generar 50 órdenes"""
    orders = []
    for i in range(1, 51):
        order = generate_order(i)
        orders.append(order)
    
    # Guardar en archivo JSON
    with open('data/orders-50.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Generadas {len(orders)} órdenes en data/orders-50.json")

if __name__ == "__main__":
    main()
