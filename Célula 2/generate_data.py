import json
import uuid
from datetime import datetime, timedelta
import random

gadget_types = ['Rocket Shoes', 'Jetpack', 'Laser Pointer', 'Invisible Cloak', 'Time Turner', 'Teleporter', 'Hoverboard', 'Smart Glasses', 'Drone', 'Robot Assistant']
base_prices = {'Rocket Shoes': 299.99, 'Jetpack': 4999.99, 'Laser Pointer': 49.99, 'Invisible Cloak': 1999.99, 'Time Turner': 9999.99, 'Teleporter': 15999.99, 'Hoverboard': 899.99, 'Smart Glasses': 399.99, 'Drone': 599.99, 'Robot Assistant': 2499.99}
suppliers = {'Rocket Shoes': 'AcmeTech Footwear Inc.', 'Jetpack': 'SkyHigh Industries', 'Laser Pointer': 'PhotonWorks Ltd.', 'Invisible Cloak': 'Stealth Solutions', 'Time Turner': 'Temporal Dynamics Corp.', 'Teleporter': 'Quantum Transport Systems', 'Hoverboard': 'AntiGrav Technologies', 'Smart Glasses': 'VisionTech Solutions', 'Drone': 'AeroBot Industries', 'Robot Assistant': 'AI Companions Inc.'}
statuses = ['pending', 'processing', 'completed', 'shipped', 'delivered']
orders = []

for i in range(50):
    gadget_type = random.choice(gadget_types)
    quantity = random.randint(1, 200)
    unit_price = base_prices[gadget_type]
    discount_rate = 0.15 if quantity >= 100 else 0.10 if quantity >= 50 else 0.05 if quantity >= 20 else 0
    subtotal = unit_price * quantity
    discount_amount = subtotal * discount_rate
    total = subtotal - discount_amount
    priority = 'high' if quantity >= 100 else 'medium' if quantity >= 50 else 'normal'
    days_ago = random.randint(0, 30)
    created_at = (datetime.now() - timedelta(days=days_ago)).isoformat() + 'Z'
    status = random.choice(statuses)
    
    orders.append({
        'orderId': str(uuid.uuid4()),
        'createdAt': created_at,
        'scheduleId': f'sched-{i+1:03d}',
        'gadgetType': gadget_type,
        'quantity': quantity,
        'unitPrice': unit_price,
        'subtotal': round(subtotal, 2),
        'discountRate': discount_rate,
        'discountAmount': round(discount_amount, 2),
        'total': round(total, 2),
        'priority': priority,
        'supplier': suppliers[gadget_type],
        'status': status,
        'estimatedDeliveryDays': 7 if priority == 'high' else 14 if priority == 'medium' else 21,
        'metadata': {
            'generatedBy': 'Data Generator Script',
            'scheduleName': f'schedule-{gadget_type.lower().replace(" ", "-")}-{i}',
            'frequency': random.choice(['rate(1 hour)', 'rate(6 hours)', 'rate(1 day)', 'cron(0 9 * * ? *)'])
        }
    })

with open('scheduling-system/data/sample_orders.json', 'w') as f:
    json.dump(orders, f, indent=2)

print(f'Generated {len(orders)} orders successfully!')
