# Serverless Purchase Order Aggregation System

A production-ready serverless system for processing and aggregating purchase orders using AWS services.

## Architecture

- **Event Processing**: EventBridge/DynamoDB Streams
- **Compute**: AWS Lambda
- **Storage**: DynamoDB
- **API**: API Gateway with Cognito authentication
- **Security**: KMS encryption, VPC, IAM least privilege
- **CI/CD**: CodePipeline + CodeBuild + GitHub

## Project Structure

```
|          # CloudFormation templates
├── src/        # Lambda function handlers
│   ├── order_aggregator.py
│   ├── order_api.py
|   └── order_processor.py    
├── iac/        # Lambda function handlers
│   ├── iamroles.yaml
│   ├── main.yaml
|   └── pipeline.yaml    
├── data/                  # Test files
└── buildspec.yml           # CodeBuild configuration
```

## Deployment

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS account with necessary permissions
- GitHub repository for source code
- GitHub personal access token

## Deployment Steps

### 1. Deploy Main Infrastructure

```bash
aws cloudformation create-stack \
  --stack-name purchase-orders-dev \
  --template-body file://main.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=GitHubRepo,ParameterValue=your-repo \
    ParameterKey=GitHubBranch,ParameterValue=main \
  --capabilities CAPABILITY_IAM
```

### 2. Deploy CI/CD Pipeline

```bash
aws cloudformation create-stack \
  --stack-name purchase-orders-pipeline \
  --template-body file://pipeline.yaml \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue=your-username \
    ParameterKey=GitHubRepo,ParameterValue=your-repo \
    ParameterKey=GitHubBranch,ParameterValue=main \
    ParameterKey=GitHubToken,ParameterValue=your-token \
  --capabilities CAPABILITY_IAM
```

### 3. Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name purchase-orders-dev \
  --query 'Stacks[0].Outputs'
```

## Architecture Components

### DynamoDB Tables

1. **purchase-orders-{env}**: Stores raw order data
   - Primary Key: orderId (HASH), timestamp (RANGE)
   - GSI: CustomerIndex (customerId, timestamp)
   - Encryption: KMS
   - Streams: Enabled

2. **order-aggregations-{env}**: Stores aggregated data
   - Primary Key: aggregationKey (HASH), period (RANGE)
   - Encryption: KMS

### Lambda Functions

1. **order-processor**: Receives orders from EventBridge
2. **order-aggregator**: Processes DynamoDB streams
3. **order-api**: Handles API Gateway requests

### Security

- All Lambda functions run in private VPC
- KMS encryption for data at rest
- Cognito authentication for API
- IAM roles with least privilege
- VPC endpoints for AWS services

## Testing

### Generate Test Data

```bash
python scripts/test_data_generator.py
```

### Test API Endpoints

```bash
# Get API endpoint and create Cognito user first
./scripts/test_api.sh <API_ENDPOINT> <AUTH_TOKEN>
```

## Monitoring

CloudWatch Logs are automatically created for:
- Lambda function executions
- API Gateway requests
- DynamoDB operations

## Cleanup

```bash
aws cloudformation delete-stack --stack-name purchase-orders-dev
aws cloudformation delete-stack --stack-name purchase-orders-pipeline
```
