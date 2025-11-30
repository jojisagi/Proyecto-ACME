"""
Script para generar datos sintéticos de órdenes de compra
Genera 50+ registros de prueba para poblar DynamoDB
"""

import json
import uuid
from datetime import datetime, timedelta
import random
from decimal import Decimal


def generate_sample_orders(count=50):
    """
    Genera órdenes de compra sintéticas
    """
    gadget_types = [
        'Rocket Shoes',
        'Jetpack',
        'Laser Pointer',
        'Invisible Cloak',
        'Time Turner',
        'Teleporter',
        'Hoverboard',
        'Smart Glasses',
        'Drone',
        'Robot Assistant',
        'Hologram Projector',
        'Energy Shield',
        'Gravity Boots',
        'Mind Reader Helmet',
        'Shrink Ray'
    ]
    
    base_prices = {
        'Rocket Shoes': 299.99,
        'Jetpack': 4999.99,
        'Laser Pointer': 49.99,
        'Invisible Cloak': 1999.99,
        'Time Turner': 9999.99,
        'Teleporter': 15999.99,
        'Hoverboard': 899.99,
        'Smart Glasses': 399.99,
        'Drone': 599.99,
        'Robot Assistant': 2499.99,
        'Hologram Projector': 1299.99,
        'Energy Shield': 3499.99,
        'Gravity Boots': 799.99,
        'Mind Reader Helmet': 5999.99,
        'Shrink Ray': 8999.99
    }
    
    suppliers = {
        'Rocket Shoes': 'AcmeTech Footwear Inc.',
        'Jetpack': 'SkyHigh Industries',
        'Laser Pointer': 'PhotonWorks Ltd.',
        'Invisible Cloak': 'Stealth Solutions',
        'Time Turner': 'Temporal Dynamics Corp.',
        'Teleporter': 'Quantum Transport Systems',
        'Hoverboard': 'AntiGrav Technologies',
        'Smart Glasses': 'VisionTech Solutions',
        'Drone': 'AeroBot Industries',
        'Robot Assistant': 'AI Companions Inc.',
        'Hologram Projector': 'Virtual Reality Corp.',
        'Energy Shield': 'DefenseTech Systems',
        'Gravity Boots': 'AntiGrav Technologies',
        'Mind Reader Helmet': 'NeuroTech Industries',
        'Shrink Ray': 'Quantum Miniaturization Labs'
    }
    
    statuses = ['pending', 'processing', 'completed', 'shipped', 'delivered', 'cancelled']
    priorities = ['normal', 'medium', 'high']
    
    orders = []
    
    for i in range(count):
        gadget_type = random.choice(gadget_types)
        quantity = random.randint(1, 200)
        unit_price = base_prices.get(gadget_type, 99.99)
        
        # Calcular descuento
        discount_rate = 0
        if quantity >= 100:
            discount_rate = 0.15
        elif quantity >= 50:
            discount_rate = 0.10
        elif quantity >= 20:
            discount_rate = 0.05
        
        subtotal = unit_price * quantity
        discount_amount = subtotal * discount_rate
        total = subtotal - discount_amount
        
        # Determinar prioridad
        if quantity >= 100:
            priority = 'high'
        elif quantity >= 50:
            priority = 'medium'
        else:
            priority = random.choice(priorities)
        
        # Fecha aleatoria en los últimos 30 días
        days_ago = random.randint(0, 30)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # Estado basado en antigüedad
        if days_ago > 20:
            status = random.choice(['completed', 'delivered'])
        elif days_ago > 10:
            status = random.choice(['processing', 'shipped', 'completed'])
        elif days_ago > 5:
            status = random.choice(['pending', 'processing'])
        else:
            status = 'pending'
        
        order = {
            'orderId': str(uuid.uuid4()),
            'createdAt': created_at.isoformat(),
            'scheduleId': str(uuid.uuid4()),
            'gadgetType': gadget_type,
            'quantity': quantity,
            'unitPrice': unit_price,
            'subtotal': subtotal,
            'discountRate': discount_rate,
            'discountAmount': discount_amount,
            'total': round(total, 2),
            'priority': priority,
            'supplier': suppliers.get(gadget_type, 'General Supplier Co.'),
            'status': status,
            'estimatedDeliveryDays': 7 if priority == 'high' else 14 if priority == 'medium' else 21,
            'metadata': {
                'generatedBy': 'Data Generator Script',
                'scheduleName': f'schedule-{gadget_type.lower().replace(" ", "-")}-{i}',
                'frequency': random.choice(['rate(1 hour)', 'rate(6 hours)', 'rate(1 day)', 'cron(0 9 * * ? *)'])
            }
        }
        
        orders.append(order)
    
    return orders


def main():
    """
    Función principal para generar y guardar datos
    """
    print("Generando 50+ órdenes sintéticas...")
    
    # Generar 60 órdenes
    orders = generate_sample_orders(60)
    
    # Guardar en archivo JSON
    output_file = '../../data/sample_orders.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)
    
    print(f"✓ {len(orders)} órdenes generadas exitosamente")
    print(f"✓ Archivo guardado en: {output_file}")
    
    # Estadísticas
    print("\n=== Estadísticas ===")
    print(f"Total de órdenes: {len(orders)}")
    
    statuses = {}
    for order in orders:
        status = order['status']
        statuses[status] = statuses.get(status, 0) + 1
    
    print("\nPor estado:")
    for status, count in statuses.items():
        print(f"  {status}: {count}")
    
    priorities = {}
    for order in orders:
        priority = order['priority']
        priorities[priority] = priorities.get(priority, 0) + 1
    
    print("\nPor prioridad:")
    for priority, count in priorities.items():
        print(f"  {priority}: {count}")
    
    total_value = sum(order['total'] for order in orders)
    print(f"\nValor total de órdenes: ${total_value:,.2f}")


if __name__ == '__main__':
    main()
