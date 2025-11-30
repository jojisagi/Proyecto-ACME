#!/usr/bin/env python3
"""
Generador de Datos de Prueba para Acme Image Handler
Genera 50 imágenes sintéticas de gadgets con metadatos
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont
import random
from datetime import datetime

# Configuración
OUTPUT_DIR = "data/test-images"
METADATA_FILE = "data/test-metadata.json"
NUM_IMAGES = 50

# Categorías de gadgets
CATEGORIES = [
    "Smartphones",
    "Tablets",
    "Laptops",
    "Smartwatches",
    "Headphones",
    "Cameras",
    "Drones",
    "Gaming Consoles",
    "Smart Home",
    "Wearables"
]

# Nombres de productos
PRODUCT_NAMES = [
    "Pro Max", "Ultra", "Elite", "Premium", "Standard",
    "Mini", "Plus", "Air", "Lite", "Advanced",
    "Classic", "Modern", "Sport", "Business", "Gaming"
]

# Colores para las imágenes
COLORS = [
    (52, 152, 219),   # Azul
    (46, 204, 113),   # Verde
    (155, 89, 182),   # Púrpura
    (241, 196, 15),   # Amarillo
    (230, 126, 34),   # Naranja
    (231, 76, 60),    # Rojo
    (149, 165, 166),  # Gris
    (52, 73, 94),     # Azul oscuro
]


def generate_gadget_image(gadget_id, name, category, size=(800, 600)):
    """
    Genera una imagen sintética de un gadget
    """
    # Crear imagen con color de fondo aleatorio
    bg_color = random.choice(COLORS)
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Dibujar un rectángulo para simular el producto
    product_width = size[0] // 2
    product_height = size[1] // 2
    product_x = (size[0] - product_width) // 2
    product_y = (size[1] - product_height) // 2
    
    # Color del producto (más claro que el fondo)
    product_color = tuple(min(c + 50, 255) for c in bg_color)
    draw.rectangle(
        [product_x, product_y, product_x + product_width, product_y + product_height],
        fill=product_color,
        outline=(255, 255, 255),
        width=3
    )
    
    # Agregar texto con información del producto
    try:
        # Intentar usar una fuente del sistema
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except:
        # Fallback a fuente por defecto
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Texto del nombre del producto
    text_bbox = draw.textbbox((0, 0), name, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (size[0] - text_width) // 2
    text_y = size[1] // 2 - 40
    
    draw.text((text_x, text_y), name, fill=(255, 255, 255), font=font_large)
    
    # Texto del ID
    id_text = f"ID: {gadget_id}"
    id_bbox = draw.textbbox((0, 0), id_text, font=font_small)
    id_width = id_bbox[2] - id_bbox[0]
    id_x = (size[0] - id_width) // 2
    id_y = text_y + 50
    
    draw.text((id_x, id_y), id_text, fill=(255, 255, 255), font=font_small)
    
    # Texto de la categoría
    cat_text = category
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_small)
    cat_width = cat_bbox[2] - cat_bbox[0]
    cat_x = (size[0] - cat_width) // 2
    cat_y = id_y + 35
    
    draw.text((cat_x, cat_y), cat_text, fill=(255, 255, 255), font=font_small)
    
    # Agregar algunos detalles decorativos
    for _ in range(5):
        x = random.randint(20, size[0] - 20)
        y = random.randint(20, size[1] - 20)
        radius = random.randint(5, 15)
        draw.ellipse([x, y, x + radius, y + radius], fill=(255, 255, 255, 128))
    
    return img


def generate_test_data():
    """
    Genera todas las imágenes de prueba y sus metadatos
    """
    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    metadata_list = []
    
    print(f"Generando {NUM_IMAGES} imágenes de prueba...")
    print(f"Directorio de salida: {OUTPUT_DIR}")
    print("-" * 50)
    
    for i in range(1, NUM_IMAGES + 1):
        # Generar datos del gadget
        gadget_id = f"GADGET-{i:04d}"
        category = random.choice(CATEGORIES)
        product_name = f"{category} {random.choice(PRODUCT_NAMES)}"
        
        # Dimensiones aleatorias
        width = random.choice([800, 1024, 1200, 1600])
        height = random.choice([600, 768, 900, 1200])
        
        # Generar imagen
        img = generate_gadget_image(gadget_id, product_name, category, (width, height))
        
        # Guardar imagen
        filename = f"{gadget_id}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, 'JPEG', quality=95)
        
        # Crear metadatos
        metadata = {
            'gadgetId': gadget_id,
            'name': product_name,
            'category': category,
            'filename': filename,
            'resolution': {
                'width': width,
                'height': height
            },
            'format': 'JPEG',
            'fileSize': os.path.getsize(filepath),
            'generatedAt': datetime.utcnow().isoformat(),
            'description': f"Imagen sintética de {product_name} para pruebas",
            'tags': [category.lower(), 'test', 'synthetic', 'acme']
        }
        
        metadata_list.append(metadata)
        
        print(f"✓ Generada: {filename} ({width}x{height}) - {product_name}")
    
    # Guardar metadatos en JSON
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    print("-" * 50)
    print(f"✓ {NUM_IMAGES} imágenes generadas exitosamente")
    print(f"✓ Metadatos guardados en: {METADATA_FILE}")
    print(f"✓ Tamaño total: {sum(m['fileSize'] for m in metadata_list) / 1024 / 1024:.2f} MB")


if __name__ == '__main__':
    generate_test_data()
