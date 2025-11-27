#!/bin/bash

# Script para poblar datos de ejemplo en DynamoDB

set -e

echo "Poblando datos de ejemplo en DynamoDB..."

# Verificar que AWS CLI esté configurado
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI no está instalado"
    exit 1
fi

# Inicializar tabla VoteResults con gadgets
echo "Inicializando tabla VoteResults con gadgets..."

gadgets=(
    "gadget-001:SmartWatch Pro X"
    "gadget-002:AirPods Ultra"
    "gadget-003:Drone Phantom 5"
    "gadget-004:VR Headset Elite"
    "gadget-005:Robot Aspiradora AI"
    "gadget-006:Tablet Creator Pro"
    "gadget-007:Smart Speaker Max"
    "gadget-008:Gaming Console Next"
    "gadget-009:E-Reader Premium"
    "gadget-010:Smart Thermostat"
)

for gadget in "${gadgets[@]}"; do
    IFS=':' read -r gadget_id gadget_name <<< "$gadget"
    
    aws dynamodb put-item \
        --table-name VoteResults \
        --item "{
            \"gadgetId\": {\"S\": \"${gadget_id}\"},
            \"gadgetName\": {\"S\": \"${gadget_name}\"},
            \"totalVotes\": {\"N\": \"0\"}
        }" \
        --no-cli-pager
    
    echo "✓ ${gadget_name} inicializado"
done

echo ""
echo "Insertando votos de ejemplo..."

# Leer votos del archivo JSON y insertarlos
vote_count=0
while IFS= read -r line; do
    # Extraer userId y gadgetId del JSON
    user_id=$(echo "$line" | grep -o '"userId": "[^"]*"' | cut -d'"' -f4)
    gadget_id=$(echo "$line" | grep -o '"gadgetId": "[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$user_id" ] && [ -n "$gadget_id" ]; then
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        vote_uuid=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "uuid-$RANDOM-$RANDOM")
        
        aws dynamodb put-item \
            --table-name Votes \
            --item "{
                \"userId\": {\"S\": \"${user_id}\"},
                \"voteId\": {\"S\": \"VOTE\"},
                \"gadgetId\": {\"S\": \"${gadget_id}\"},
                \"timestamp\": {\"S\": \"${timestamp}\"},
                \"voteUuid\": {\"S\": \"${vote_uuid}\"}
            }" \
            --no-cli-pager > /dev/null
        
        ((vote_count++))
        echo -ne "\rVotos insertados: ${vote_count}"
    fi
done < ../data/sample-votes.json

echo ""
echo ""
echo "✓ Datos poblados exitosamente"
echo "  - 10 gadgets inicializados en VoteResults"
echo "  - ${vote_count} votos insertados en Votes"
echo ""
echo "Nota: Los votos se agregarán automáticamente a VoteResults"
echo "      mediante el StreamProcessor Lambda en unos segundos."
