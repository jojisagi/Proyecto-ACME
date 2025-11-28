# Deployment Scripts

This directory contains scripts for deploying the AWS Cartoon Rekognition infrastructure.

## deploy.sh

Main deployment script that deploys all CloudFormation stacks in the correct order.

### Prerequisites

1. AWS CLI installed and configured
2. Valid AWS credentials with permissions to create CloudFormation stacks
3. Appropriate IAM permissions for all services (S3, DynamoDB, Lambda, API Gateway, etc.)

### Usage

#### Deploy all stacks to an environment:

```bash
./scripts/deploy.sh <environment>
```

Where `<environment>` is one of:
- `sandbox` - Development environment
- `preprod` - Pre-production environment
- `prod` - Production environment

Example:
```bash
./scripts/deploy.sh sandbox
```

#### Deploy a single stack:

```bash
./scripts/deploy.sh <environment> <stack-name>
```

Where `<stack-name>` is one of:
- `network` - VPC, subnets, VPC endpoints
- `kms` - KMS encryption keys
- `s3` - S3 bucket for images
- `dynamodb` - DynamoDB table for results
- `cognito` - Cognito User Pool
- `lambda` - Lambda functions
- `api_gateway` - API Gateway REST API
- `pipeline` - CI/CD pipeline

Example:
```bash
./scripts/deploy.sh sandbox lambda
```

### Deployment Order

The script deploys stacks in the following order to respect dependencies:

1. **network** - VPC infrastructure (required by all other stacks)
2. **kms** - Encryption keys (required by S3, DynamoDB, Lambda)
3. **s3** - Image storage bucket
4. **dynamodb** - Results table
5. **cognito** - User authentication
6. **lambda** - Processing functions (depends on network, kms, s3, dynamodb)
7. **api_gateway** - REST API (depends on lambda, cognito)
8. **pipeline** - CI/CD pipeline (optional, sandbox only)

### Features

- **Automatic validation**: Validates CloudFormation templates before deployment
- **Progress tracking**: Shows detailed progress for each stack
- **Error handling**: Automatically rolls back failed stacks
- **Output capture**: Captures and displays important stack outputs
- **Lambda packaging**: Automatically packages Lambda functions before deployment
- **Update detection**: Detects if stack needs update or creation
- **Colored output**: Easy-to-read colored console output

### Error Handling

If a stack deployment fails:
1. The script will display the error details
2. The failed stack will be automatically rolled back
3. The script will exit with error code 1
4. Previously deployed stacks will remain in place

To manually rollback all stacks:
```bash
# Delete stacks in reverse order
aws cloudformation delete-stack --stack-name cartoon-rekognition-pipeline-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-api-gateway-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-lambda-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-cognito-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-dynamodb-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-s3-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-kms-sandbox
aws cloudformation delete-stack --stack-name cartoon-rekognition-network-sandbox
```

### Parameter Files

The script uses environment-specific parameter files located in `iac/`:
- `iac/params-sandbox.json`
- `iac/params-preprod.json`
- `iac/params-prod.json`

Make sure to update these files with your specific configuration before deployment.

### Troubleshooting

#### AWS CLI not configured
```
Error: AWS CLI is not configured
```
Solution: Run `aws configure` and provide your AWS credentials.

#### Template validation failed
```
Error: Template validation failed
```
Solution: Check the CloudFormation template for syntax errors. Run:
```bash
aws cloudformation validate-template --template-body file://iac/<template>.yml
```

#### Stack already exists
If a stack already exists, the script will automatically update it instead of creating a new one.

#### Permission denied
On Unix/Linux/Mac, make the script executable:
```bash
chmod +x scripts/deploy.sh
```

### Examples

Deploy everything to sandbox:
```bash
./scripts/deploy.sh sandbox
```

Update only the Lambda stack in production:
```bash
./scripts/deploy.sh prod lambda
```

Deploy to preprod:
```bash
./scripts/deploy.sh preprod
```

### Notes

- The pipeline stack is only deployed to sandbox by default
- Lambda functions are automatically packaged before deployment
- Stack outputs are displayed at the end of deployment
- All stacks are tagged with Environment and Project tags
