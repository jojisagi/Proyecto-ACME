# Infrastructure as Code

This directory contains CloudFormation templates for the AWS infrastructure.

## Templates

- `network.yml` - VPC, subnets, VPC endpoints, security groups
- `kms.yml` - KMS Customer Master Keys for encryption
- `s3.yml` - S3 bucket for image storage
- `dynamodb.yml` - DynamoDB table for analysis results
- `cognito.yml` - Cognito User Pool for authentication
- `lambda.yml` - Lambda functions and IAM roles
- `api_gateway.yml` - API Gateway REST API
- `pipeline.yml` - CI/CD pipeline with CodePipeline

## Parameter Files

- `params-sandbox.json` - Parameters for sandbox environment
- `params-preprod.json` - Parameters for preprod environment
- `params-prod.json` - Parameters for production environment
