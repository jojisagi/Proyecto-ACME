#!/bin/bash

###############################################################################
# Script de Configuración de Cuentas AWS
# Célula 3 - Acme Image Handler
###############################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Verificar que AWS CLI esté instalado
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI no está instalado"
    echo "Instala con: brew install awscli"
    exit 1
fi

print_header "Configuración de Cuentas AWS - Acme Image Handler"

# Solicitar información de las cuentas
echo ""
echo "Por favor ingresa la información de las cuentas AWS:"
echo ""

read -p "Build Account ID: " BUILD_ACCOUNT_ID
read -p "Sandbox Account ID: " SANDBOX_ACCOUNT_ID
read -p "Production Account ID: " PROD_ACCOUNT_ID

echo ""
print_info "Cuentas configuradas:"
echo "  Build: $BUILD_ACCOUNT_ID"
echo "  Sandbox: $SANDBOX_ACCOUNT_ID"
echo "  Production: $PROD_ACCOUNT_ID"
echo ""

read -p "¿Es correcta esta información? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    print_error "Configuración cancelada"
    exit 1
fi

# Verificar perfiles AWS CLI
print_header "Verificando Perfiles AWS CLI"

for profile in build sandbox prod; do
    if aws sts get-caller-identity --profile $profile &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --profile $profile --query 'Account' --output text)
        print_success "Perfil '$profile' configurado (Account: $ACCOUNT_ID)"
    else
        print_error "Perfil '$profile' no configurado"
        echo "Configura con: aws configure --profile $profile"
        exit 1
    fi
done

# Configurar Sandbox
print_header "Configurando Cuenta Sandbox"

print_info "Creando VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=acme-sandbox-vpc},{Key=Environment,Value=sandbox}]' \
    --profile sandbox \
    --query 'Vpc.VpcId' \
    --output text 2>/dev/null || echo "")

if [ -n "$VPC_ID" ]; then
    print_success "VPC creada: $VPC_ID"
    
    # Habilitar DNS
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --profile sandbox
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --profile sandbox
    
    # Crear subnets
    print_info "Creando subnets privadas..."
    
    SUBNET1=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --availability-zone us-east-1a \
        --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-sandbox-private-1a}]' \
        --profile sandbox \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Subnet 1 creada: $SUBNET1"
    
    SUBNET2=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.2.0/24 \
        --availability-zone us-east-1b \
        --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-sandbox-private-1b}]' \
        --profile sandbox \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Subnet 2 creada: $SUBNET2"
    
    # Actualizar archivo de parámetros
    print_info "Actualizando parámetros de sandbox..."
    cat > pipeline/parameters-sandbox.json <<EOF
[
  {
    "ParameterKey": "EnvironmentName",
    "ParameterValue": "sandbox"
  },
  {
    "ParameterKey": "VPCId",
    "ParameterValue": "$VPC_ID"
  },
  {
    "ParameterKey": "PrivateSubnet1",
    "ParameterValue": "$SUBNET1"
  },
  {
    "ParameterKey": "PrivateSubnet2",
    "ParameterValue": "$SUBNET2"
  },
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "acme-image-handler"
  }
]
EOF
    print_success "Parámetros actualizados"
else
    print_error "Error creando VPC (puede que ya exista)"
fi

# Configurar Producción
print_header "Configurando Cuenta Producción"

print_info "Creando VPC..."
VPC_ID_PROD=$(aws ec2 create-vpc \
    --cidr-block 10.1.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=acme-prod-vpc},{Key=Environment,Value=prod}]' \
    --profile prod \
    --query 'Vpc.VpcId' \
    --output text 2>/dev/null || echo "")

if [ -n "$VPC_ID_PROD" ]; then
    print_success "VPC creada: $VPC_ID_PROD"
    
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID_PROD --enable-dns-hostnames --profile prod
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID_PROD --enable-dns-support --profile prod
    
    print_info "Creando subnets privadas..."
    
    SUBNET1_PROD=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID_PROD \
        --cidr-block 10.1.1.0/24 \
        --availability-zone us-east-1a \
        --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-prod-private-1a}]' \
        --profile prod \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Subnet 1 creada: $SUBNET1_PROD"
    
    SUBNET2_PROD=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID_PROD \
        --cidr-block 10.1.2.0/24 \
        --availability-zone us-east-1b \
        --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-prod-private-1b}]' \
        --profile prod \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Subnet 2 creada: $SUBNET2_PROD"
    
    # Actualizar archivo de parámetros
    print_info "Actualizando parámetros de producción..."
    cat > pipeline/parameters-prod.json <<EOF
[
  {
    "ParameterKey": "EnvironmentName",
    "ParameterValue": "prod"
  },
  {
    "ParameterKey": "VPCId",
    "ParameterValue": "$VPC_ID_PROD"
  },
  {
    "ParameterKey": "PrivateSubnet1",
    "ParameterValue": "$SUBNET1_PROD"
  },
  {
    "ParameterKey": "PrivateSubnet2",
    "ParameterValue": "$SUBNET2_PROD"
  },
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "acme-image-handler"
  }
]
EOF
    print_success "Parámetros actualizados"
else
    print_error "Error creando VPC (puede que ya exista)"
fi

# Resumen
print_header "Resumen de Configuración"

echo ""
echo "Sandbox:"
echo "  VPC: $VPC_ID"
echo "  Subnet 1: $SUBNET1"
echo "  Subnet 2: $SUBNET2"
echo ""
echo "Producción:"
echo "  VPC: $VPC_ID_PROD"
echo "  Subnet 1: $SUBNET1_PROD"
echo "  Subnet 2: $SUBNET2_PROD"
echo ""

print_success "Configuración completada"
echo ""
print_info "Próximos pasos:"
echo "  1. Revisar archivos de parámetros en pipeline/"
echo "  2. Configurar NAT Gateways (opcional, costo adicional)"
echo "  3. Configurar VPC Endpoints para S3 y DynamoDB"
echo "  4. Ejecutar despliegue: ./pipeline/deploy.sh sandbox"
echo ""
