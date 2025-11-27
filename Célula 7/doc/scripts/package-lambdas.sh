#!/bin/bash

# Script para empaquetar funciones Lambda

set -e

echo "Empaquetando funciones Lambda..."

# Crear directorio para los paquetes
mkdir -p ../dist/lambda

# Función para empaquetar una Lambda
package_lambda() {
    local lambda_name=$1
    local lambda_dir="../lambda/${lambda_name}"
    local output_file="../dist/lambda/${lambda_name}.zip"
    
    echo "Empaquetando ${lambda_name}..."
    
    # Crear directorio temporal
    temp_dir=$(mktemp -d)
    
    # Copiar código de la Lambda
    cp "${lambda_dir}/lambda_function.py" "${temp_dir}/"
    
    # Instalar dependencias si existen
    if [ -f "${lambda_dir}/requirements.txt" ]; then
        pip install -r "${lambda_dir}/requirements.txt" -t "${temp_dir}/" --quiet
    fi
    
    # Crear ZIP
    cd "${temp_dir}"
    zip -r "${output_file}" . > /dev/null
    cd - > /dev/null
    
    # Limpiar
    rm -rf "${temp_dir}"
    
    echo "✓ ${lambda_name}.zip creado"
}

# Empaquetar cada Lambda
package_lambda "emit-vote"
package_lambda "get-results"
package_lambda "stream-processor"

echo ""
echo "Todas las Lambdas empaquetadas en dist/lambda/"
echo ""
echo "Siguiente paso: Subir los archivos ZIP a S3"
echo "aws s3 cp dist/lambda/ s3://YOUR-BUCKET/lambda/ --recursive"
