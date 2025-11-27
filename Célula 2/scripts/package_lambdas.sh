#!/bin/bash

# Script para empaquetar funciones Lambda en archivos ZIP
# Compatible con Windows (Git Bash) y Linux

echo "=== Empaquetando Funciones Lambda ==="

# Crear directorio para los paquetes
mkdir -p ../dist

# Empaquetar Scheduler Manager
echo "Empaquetando scheduler_manager..."
cd ../src/scheduler_manager
zip -r ../../dist/scheduler_manager.zip app.py
echo "✓ scheduler_manager.zip creado"

# Empaquetar Order Executor
echo "Empaquetando order_executor..."
cd ../order_executor
zip -r ../../dist/order_executor.zip app.py
echo "✓ order_executor.zip creado"

cd ../../scripts

echo ""
echo "=== Paquetes Lambda Creados ==="
ls -lh ../dist/*.zip

echo ""
echo "✓ Empaquetado completado exitosamente"
echo ""
echo "Siguiente paso: Subir los ZIPs a S3 o desplegar directamente con CloudFormation"
