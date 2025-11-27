# Configuración de Cuentas AWS - Célula 3

## Resumen de Cuentas

Este proyecto utiliza **3 cuentas AWS separadas** siguiendo las mejores prácticas de AWS Organizations:

| Cuenta | Propósito | Account ID | Ambiente |
|--------|-----------|------------|----------|
| **Build** | Pipeline CI/CD | `111111111111` | N/A |
| **Sandbox** | Desarrollo y pruebas | `222222222222` | sandbox |
| **Producción** | Ambiente productivo | `333333333333` | prod |

## Arquitectura Multi-Cuenta

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Organizations                         │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐│
│  │  Build Account │  │ Sandbox Account│  │  Prod Account  ││
│  │                │  │                │  │                ││
│  │  CodePipeline  │  │  Lambda        │  │  Lambda        ││
│  │  CodeBuild     │──▶  API Gateway   │  │  API Gateway   ││
│  │  S3 Artifacts  │  │  S3            │  │  S3            ││
│  │                │  │  DynamoDB      │  │  DynamoDB      ││
│  │                │  │  Cognito       │  │  Cognito       ││
│  └────────────────┘  └────────────────┘  └────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Cuenta 1: Build (CI/CD)

### Propósito
Cuenta dedicada para ejecutar el pipeline de CI/CD. Centraliza la construcción y despliegue a otros ambientes.

### Servicios Utilizados
- **CodePipeline**: Orquestación del pipeline
- **CodeBuild**: Compilación y empaquetado
- **S3**: Almacenamiento de artefactos
- **IAM**: Roles para cross-account deployment

### Configuración

```bash
# Configurar perfil AWS CLI
aws configure --profile build
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: us-east-1
# Default output format: json

# Verificar cuenta
aws sts get-caller-identity --profile build
```

### Recursos a Crear

1. **S3 Bucket para Artefactos**
```bash
aws s3 mb s3://acme-pipeline-artifacts-111111111111 --profile build
aws s3api put-bucket-versioning \
  --bucket acme-pipeline-artifacts-111111111111 \
  --versioning-configuration Status=Enabled \
  --profile build
```

2. **IAM Role para CodePipeline**
```bash
aws iam create-role \
  --role-name AcmeCodePipelineRole \
  --assume-role-policy-document file://policies/codepipeline-trust.json \
  --profile build

aws iam attach-role-policy \
  --role-name AcmeCodePipelineRole \
  --policy-arn arn:aws:iam::aws:policy/AWSCodePipelineFullAccess \
  --profile build
```

3. **IAM Role para CodeBuild**
```bash
aws iam create-role \
  --role-name AcmeCodeBuildRole \
  --assume-role-policy-document file://policies/codebuild-trust.json \
  --profile build

aws iam attach-role-policy \
  --role-name AcmeCodeBuildRole \
  --policy-arn arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess \
  --profile build
```

### Costos Estimados
- CodePipeline: $1/mes por pipeline activo
- CodeBuild: $0.005/min (aprox $5/mes con 1000 builds)
- S3: $0.023/GB (aprox $1/mes)
- **Total**: ~$7/mes

## Cuenta 2: Sandbox (Desarrollo)

### Propósito
Ambiente de desarrollo y pruebas. Permite experimentación sin afectar producción.

### Servicios Utilizados
- **Lambda**: Funciones serverless
- **API Gateway**: APIs REST
- **S3**: Almacenamiento de imágenes
- **DynamoDB**: Base de datos NoSQL
- **Cognito**: Autenticación
- **KMS**: Cifrado
- **VPC**: Red privada

### Configuración

```bash
# Configurar perfil
aws configure --profile sandbox

# Verificar cuenta
aws sts get-caller-identity --profile sandbox
```

### Recursos a Crear

1. **VPC y Networking**
```bash
# Crear VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=acme-sandbox-vpc}]' \
  --profile sandbox \
  --query 'Vpc.VpcId' \
  --output text)

# Crear subnets privadas
SUBNET1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-sandbox-private-1a}]' \
  --profile sandbox \
  --query 'Subnet.SubnetId' \
  --output text)

SUBNET2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=acme-sandbox-private-1b}]' \
  --profile sandbox \
  --query 'Subnet.SubnetId' \
  --output text)

# Crear Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=acme-sandbox-igw}]' \
  --profile sandbox \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID \
  --profile sandbox

# Crear NAT Gateway (requiere Elastic IP)
EIP_ALLOC=$(aws ec2 allocate-address \
  --domain vpc \
  --profile sandbox \
  --query 'AllocationId' \
  --output text)

NAT_GW=$(aws ec2 create-nat-gateway \
  --subnet-id $SUBNET1 \
  --allocation-id $EIP_ALLOC \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=acme-sandbox-nat}]' \
  --profile sandbox \
  --query 'NatGateway.NatGatewayId' \
  --output text)

# Crear VPC Endpoints
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids $ROUTE_TABLE_ID \
  --profile sandbox

aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids $ROUTE_TABLE_ID \
  --profile sandbox
```

2. **IAM Role para Cross-Account Deployment**
```bash
aws iam create-role \
  --role-name AcmeCrossAccountDeployRole \
  --assume-role-policy-document file://policies/cross-account-trust.json \
  --profile sandbox

aws iam attach-role-policy \
  --role-name AcmeCrossAccountDeployRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --profile sandbox
```

### Actualizar Parámetros

Editar `pipeline/parameters-sandbox.json`:
```json
[
  {
    "ParameterKey": "VPCId",
    "ParameterValue": "vpc-0123456789abcdef0"
  },
  {
    "ParameterKey": "PrivateSubnet1",
    "ParameterValue": "subnet-0123456789abcdef0"
  },
  {
    "ParameterKey": "PrivateSubnet2",
    "ParameterValue": "subnet-0123456789abcdef1"
  }
]
```

### Costos Estimados
- Lambda: $5/mes (1M invocaciones)
- API Gateway: $3.50/mes (1M requests)
- S3: $2/mes (10GB)
- DynamoDB: $1/mes (on-demand)
- NAT Gateway: $32/mes (siempre activo)
- KMS: $1/mes
- **Total**: ~$45/mes

## Cuenta 3: Producción

### Propósito
Ambiente productivo con alta disponibilidad y seguridad.

### Servicios Utilizados
Mismos que Sandbox, pero con configuraciones de producción:
- Multi-AZ
- Backups automáticos
- Monitoreo avanzado
- Alarmas CloudWatch

### Configuración

```bash
# Configurar perfil
aws configure --profile prod

# Verificar cuenta
aws sts get-caller-identity --profile prod
```

### Recursos a Crear

Seguir los mismos pasos que Sandbox, pero con:
- VPC CIDR: 10.1.0.0/16
- Subnets en múltiples AZs
- NAT Gateways redundantes
- Backups habilitados

### Actualizar Parámetros

Editar `pipeline/parameters-prod.json` con los valores de producción.

### Costos Estimados
Depende del tráfico, pero mínimo:
- Lambda: $20/mes
- API Gateway: $15/mes
- S3: $10/mes
- DynamoDB: $5/mes
- NAT Gateway: $64/mes (2 AZs)
- KMS: $1/mes
- **Total**: ~$115/mes (sin tráfico significativo)

## Configuración de Cross-Account Access

### Archivo: policies/cross-account-trust.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111111111111:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "acme-image-handler-deploy"
        }
      }
    }
  ]
}
```

### Archivo: policies/codepipeline-trust.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codepipeline.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Archivo: policies/codebuild-trust.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Verificación de Configuración

### Script de Verificación

```bash
#!/bin/bash

echo "Verificando configuración de cuentas..."

# Build Account
echo "Build Account:"
aws sts get-caller-identity --profile build

# Sandbox Account
echo "Sandbox Account:"
aws sts get-caller-identity --profile sandbox

# Prod Account
echo "Prod Account:"
aws sts get-caller-identity --profile prod

echo "Verificación completada"
```

## Mejores Prácticas

1. **Separación de Cuentas**: Nunca mezclar ambientes en la misma cuenta
2. **IAM Roles**: Usar roles en lugar de access keys cuando sea posible
3. **MFA**: Habilitar MFA en todas las cuentas
4. **CloudTrail**: Habilitar logging en todas las cuentas
5. **Budgets**: Configurar alertas de costos
6. **Tags**: Etiquetar todos los recursos con Environment, Project, Owner

## Troubleshooting

### Error: Access Denied en Cross-Account

**Solución**: Verificar que el rol en la cuenta destino confía en la cuenta origen

```bash
aws iam get-role --role-name AcmeCrossAccountDeployRole --profile sandbox
```

### Error: VPC Endpoint no funciona

**Solución**: Verificar route tables y security groups

```bash
aws ec2 describe-vpc-endpoints --profile sandbox
```

## Contacto

Para problemas con las cuentas AWS, contactar al administrador de AWS Organizations.
