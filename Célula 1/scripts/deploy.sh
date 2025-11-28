#!/bin/bash

################################################################################
# AWS Cartoon Rekognition - Deployment Script
# 
# This script deploys all CloudFormation stacks in the correct order,
# capturing outputs from each stack to pass to dependent stacks.
#
# Usage: ./scripts/deploy.sh <environment> [stack-name]
#   environment: sandbox, preprod, or prod
#   stack-name: (optional) deploy only a specific stack
#
# Requirements: 10.1, 10.2
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IAC_DIR="$PROJECT_ROOT/iac"
SRC_DIR="$PROJECT_ROOT/src"

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed and configured
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region)
    
    log_success "AWS CLI configured for account: $account_id in region: $region"
}

# Validate environment parameter
validate_environment() {
    local env=$1
    
    if [[ ! "$env" =~ ^(sandbox|preprod|prod)$ ]]; then
        log_error "Invalid environment: $env. Must be sandbox, preprod, or prod."
        exit 1
    fi
    
    if [ ! -f "$IAC_DIR/params-$env.json" ]; then
        log_error "Parameter file not found: $IAC_DIR/params-$env.json"
        exit 1
    fi
    
    log_success "Environment validated: $env"
}

# Package Lambda functions
package_lambdas() {
    log_info "Packaging Lambda functions..."
    
    local lambda_package_dir="$PROJECT_ROOT/.lambda-packages"
    mkdir -p "$lambda_package_dir"
    
    # Package each Lambda function
    for lambda_dir in "$SRC_DIR/lambdas"/*; do
        if [ -d "$lambda_dir" ]; then
            local lambda_name=$(basename "$lambda_dir")
            local zip_file="$lambda_package_dir/${lambda_name}.zip"
            
            log_info "Packaging $lambda_name..."
            
            # Create zip with Lambda code
            cd "$lambda_dir"
            zip -r "$zip_file" . -x "*.pyc" -x "__pycache__/*" -x "*.git*" > /dev/null
            
            log_success "Packaged $lambda_name to $zip_file"
        fi
    done
    
    cd "$PROJECT_ROOT"
}

# Deploy a CloudFormation stack
deploy_stack() {
    local stack_name=$1
    local template_file=$2
    local params_file=$3
    local capabilities=${4:-"CAPABILITY_IAM"}
    
    log_info "Deploying stack: $stack_name"
    log_info "Template: $template_file"
    log_info "Parameters: $params_file"
    
    # Check if template exists
    if [ ! -f "$template_file" ]; then
        log_error "Template file not found: $template_file"
        return 1
    fi
    
    # Validate template
    log_info "Validating template..."
    if ! aws cloudformation validate-template --template-body "file://$template_file" > /dev/null; then
        log_error "Template validation failed for $template_file"
        return 1
    fi
    log_success "Template validated successfully"
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$stack_name" &> /dev/null; then
        log_info "Stack exists. Updating..."
        local operation="update-stack"
    else
        log_info "Stack does not exist. Creating..."
        local operation="create-stack"
    fi
    
    # Deploy stack
    local deploy_cmd="aws cloudformation $operation \
        --stack-name $stack_name \
        --template-body file://$template_file \
        --parameters file://$params_file \
        --capabilities $capabilities \
        --tags Key=Environment,Value=$ENVIRONMENT Key=Project,Value=cartoon-rekognition"
    
    if $deploy_cmd > /dev/null; then
        log_info "Stack operation initiated. Waiting for completion..."
    else
        if [ "$operation" = "update-stack" ]; then
            # Check if no updates are needed
            if aws cloudformation describe-stacks --stack-name "$stack_name" &> /dev/null; then
                log_warning "No updates to be performed on stack $stack_name"
                return 0
            fi
        fi
        log_error "Failed to initiate stack operation"
        return 1
    fi
    
    # Wait for stack operation to complete
    if [ "$operation" = "create-stack" ]; then
        wait_for_stack "$stack_name" "stack-create-complete"
    else
        wait_for_stack "$stack_name" "stack-update-complete"
    fi
}

# Wait for stack operation to complete
wait_for_stack() {
    local stack_name=$1
    local wait_condition=$2
    
    log_info "Waiting for $stack_name to reach $wait_condition..."
    
    if aws cloudformation wait "$wait_condition" --stack-name "$stack_name" 2>&1; then
        log_success "Stack $stack_name completed successfully"
        return 0
    else
        log_error "Stack $stack_name failed or timed out"
        
        # Get stack events to show error
        log_error "Recent stack events:"
        aws cloudformation describe-stack-events \
            --stack-name "$stack_name" \
            --max-items 10 \
            --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[Timestamp,ResourceType,LogicalResourceId,ResourceStatusReason]' \
            --output table
        
        return 1
    fi
}

# Get stack output value
get_stack_output() {
    local stack_name=$1
    local output_key=$2
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query "Stacks[0].Outputs[?OutputKey=='$output_key'].OutputValue" \
        --output text 2>/dev/null || echo ""
}

# Rollback stack on failure
rollback_stack() {
    local stack_name=$1
    
    log_warning "Initiating rollback for stack: $stack_name"
    
    if aws cloudformation describe-stacks --stack-name "$stack_name" &> /dev/null; then
        local stack_status=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].StackStatus' \
            --output text)
        
        if [[ "$stack_status" == *"FAILED"* ]] || [[ "$stack_status" == *"ROLLBACK"* ]]; then
            log_info "Stack is in failed state: $stack_status"
            log_info "Deleting failed stack..."
            
            aws cloudformation delete-stack --stack-name "$stack_name"
            aws cloudformation wait stack-delete-complete --stack-name "$stack_name"
            
            log_success "Failed stack deleted"
        fi
    fi
}

# Deploy all stacks in order
deploy_all_stacks() {
    local env=$1
    local project_name="cartoon-rekognition"
    
    # Stack names
    local network_stack="${project_name}-network-${env}"
    local kms_stack="${project_name}-kms-${env}"
    local s3_stack="${project_name}-s3-${env}"
    local dynamodb_stack="${project_name}-dynamodb-${env}"
    local cognito_stack="${project_name}-cognito-${env}"
    local lambda_stack="${project_name}-lambda-${env}"
    local api_gateway_stack="${project_name}-api-gateway-${env}"
    local pipeline_stack="${project_name}-pipeline-${env}"
    
    local params_file="$IAC_DIR/params-${env}.json"
    
    # Track deployed stacks for rollback
    local deployed_stacks=()
    
    # Deploy stacks in order
    log_info "========================================="
    log_info "Starting deployment for environment: $env"
    log_info "========================================="
    
    # 1. Network Stack
    if deploy_stack "$network_stack" "$IAC_DIR/network.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$network_stack")
        log_success "Network stack deployed"
    else
        log_error "Network stack deployment failed"
        rollback_stack "$network_stack"
        exit 1
    fi
    
    # 2. KMS Stack
    if deploy_stack "$kms_stack" "$IAC_DIR/kms.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$kms_stack")
        log_success "KMS stack deployed"
    else
        log_error "KMS stack deployment failed"
        rollback_stack "$kms_stack"
        exit 1
    fi
    
    # 3. S3 Stack
    if deploy_stack "$s3_stack" "$IAC_DIR/s3.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$s3_stack")
        log_success "S3 stack deployed"
    else
        log_error "S3 stack deployment failed"
        rollback_stack "$s3_stack"
        exit 1
    fi
    
    # 4. DynamoDB Stack
    if deploy_stack "$dynamodb_stack" "$IAC_DIR/dynamodb.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$dynamodb_stack")
        log_success "DynamoDB stack deployed"
    else
        log_error "DynamoDB stack deployment failed"
        rollback_stack "$dynamodb_stack"
        exit 1
    fi
    
    # 5. Cognito Stack
    if deploy_stack "$cognito_stack" "$IAC_DIR/cognito.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$cognito_stack")
        log_success "Cognito stack deployed"
    else
        log_error "Cognito stack deployment failed"
        rollback_stack "$cognito_stack"
        exit 1
    fi
    
    # 6. Lambda Stack
    if deploy_stack "$lambda_stack" "$IAC_DIR/lambda.yml" "$params_file" "CAPABILITY_IAM"; then
        deployed_stacks+=("$lambda_stack")
        log_success "Lambda stack deployed"
    else
        log_error "Lambda stack deployment failed"
        rollback_stack "$lambda_stack"
        exit 1
    fi
    
    # 7. API Gateway Stack (if template exists)
    if [ -f "$IAC_DIR/api_gateway.yml" ]; then
        if deploy_stack "$api_gateway_stack" "$IAC_DIR/api_gateway.yml" "$params_file" "CAPABILITY_IAM"; then
            deployed_stacks+=("$api_gateway_stack")
            log_success "API Gateway stack deployed"
        else
            log_error "API Gateway stack deployment failed"
            rollback_stack "$api_gateway_stack"
            exit 1
        fi
    else
        log_warning "API Gateway template not found, skipping..."
    fi
    
    # 8. Pipeline Stack (only for sandbox initially)
    if [ "$env" = "sandbox" ] && [ -f "$IAC_DIR/pipeline.yml" ]; then
        if deploy_stack "$pipeline_stack" "$IAC_DIR/pipeline.yml" "$params_file" "CAPABILITY_IAM"; then
            deployed_stacks+=("$pipeline_stack")
            log_success "Pipeline stack deployed"
        else
            log_error "Pipeline stack deployment failed"
            rollback_stack "$pipeline_stack"
            exit 1
        fi
    fi
    
    log_success "========================================="
    log_success "All stacks deployed successfully!"
    log_success "========================================="
    
    # Display stack outputs
    display_stack_outputs "$env"
}

# Display important stack outputs
display_stack_outputs() {
    local env=$1
    local project_name="cartoon-rekognition"
    
    log_info "========================================="
    log_info "Stack Outputs"
    log_info "========================================="
    
    # API Gateway endpoint
    local api_stack="${project_name}-api-gateway-${env}"
    if aws cloudformation describe-stacks --stack-name "$api_stack" &> /dev/null; then
        local api_endpoint=$(get_stack_output "$api_stack" "ApiEndpoint")
        if [ -n "$api_endpoint" ]; then
            log_info "API Endpoint: $api_endpoint"
        fi
    fi
    
    # S3 Bucket
    local s3_stack="${project_name}-s3-${env}"
    local bucket_name=$(get_stack_output "$s3_stack" "BucketName")
    if [ -n "$bucket_name" ]; then
        log_info "S3 Bucket: $bucket_name"
    fi
    
    # DynamoDB Table
    local dynamodb_stack="${project_name}-dynamodb-${env}"
    local table_name=$(get_stack_output "$dynamodb_stack" "TableName")
    if [ -n "$table_name" ]; then
        log_info "DynamoDB Table: $table_name"
    fi
    
    # Cognito User Pool
    local cognito_stack="${project_name}-cognito-${env}"
    local user_pool_id=$(get_stack_output "$cognito_stack" "UserPoolId")
    if [ -n "$user_pool_id" ]; then
        log_info "Cognito User Pool ID: $user_pool_id"
    fi
    
    log_info "========================================="
}

# Deploy a single stack
deploy_single_stack() {
    local env=$1
    local stack_type=$2
    local project_name="cartoon-rekognition"
    
    local stack_name="${project_name}-${stack_type}-${env}"
    local template_file="$IAC_DIR/${stack_type}.yml"
    local params_file="$IAC_DIR/params-${env}.json"
    
    if [ ! -f "$template_file" ]; then
        log_error "Template file not found: $template_file"
        exit 1
    fi
    
    log_info "Deploying single stack: $stack_name"
    
    if deploy_stack "$stack_name" "$template_file" "$params_file" "CAPABILITY_IAM"; then
        log_success "Stack $stack_name deployed successfully"
    else
        log_error "Stack $stack_name deployment failed"
        exit 1
    fi
}

################################################################################
# Main Script
################################################################################

main() {
    # Parse arguments
    if [ $# -lt 1 ]; then
        log_error "Usage: $0 <environment> [stack-name]"
        log_error "  environment: sandbox, preprod, or prod"
        log_error "  stack-name: (optional) network, kms, s3, dynamodb, cognito, lambda, api_gateway, or pipeline"
        exit 1
    fi
    
    ENVIRONMENT=$1
    STACK_NAME=${2:-""}
    
    # Run checks
    check_prerequisites
    validate_environment "$ENVIRONMENT"
    
    # Package Lambda functions
    package_lambdas
    
    # Deploy stacks
    if [ -z "$STACK_NAME" ]; then
        # Deploy all stacks
        deploy_all_stacks "$ENVIRONMENT"
    else
        # Deploy single stack
        deploy_single_stack "$ENVIRONMENT" "$STACK_NAME"
    fi
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"
