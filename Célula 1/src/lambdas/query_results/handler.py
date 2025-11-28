"""
Lambda function to query analysis results from DynamoDB.

This function handles API Gateway requests to retrieve cartoon character
analysis results by imageId.
"""

import json
import logging
import os
import re
from typing import Dict, Any
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource (will be initialized on first use)
dynamodb = None

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'CartoonAnalysisResults')

# UUID regex pattern (accepts all UUID versions)
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def _get_dynamodb_resource():
    """Get or create DynamoDB resource."""
    global dynamodb
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb')
    return dynamodb


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to query analysis results from DynamoDB.
    
    Args:
        event: API Gateway event containing queryStringParameters
        context: Lambda context object
        
    Returns:
        API Gateway response with analysis data or error
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters', {})
        
        if not query_params:
            return create_error_response(
                400,
                "BadRequest",
                "Missing query parameters"
            )
        
        image_id = query_params.get('imageId')
        
        # Validate required parameter
        if not image_id:
            return create_error_response(
                400,
                "BadRequest",
                "Missing required parameter: imageId"
            )
        
        # Validate UUID format
        if not is_valid_uuid(image_id):
            return create_error_response(
                400,
                "BadRequest",
                f"Invalid imageId format. Must be a valid UUID"
            )
        
        logger.info(f"Querying DynamoDB for imageId: {image_id}")
        
        # Query DynamoDB
        result = query_dynamodb(image_id)
        
        if result is None:
            logger.info(f"ImageId not found: {image_id}")
            return create_error_response(
                404,
                "NotFound",
                f"No analysis found for imageId: {image_id}"
            )
        
        logger.info(f"Successfully retrieved result for imageId: {image_id}")
        
        # Convert Decimal to float for JSON serialization
        result = convert_decimals_to_float(result)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps(result)
        }
        
    except ClientError as e:
        logger.error(f"AWS ClientError: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            "DynamoDBError",
            f"Failed to query DynamoDB: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            "InternalServerError",
            "An unexpected error occurred"
        )


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Validate that a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    if not uuid_string:
        return False
    
    return UUID_PATTERN.match(uuid_string) is not None


def query_dynamodb(image_id: str) -> Dict[str, Any]:
    """
    Query DynamoDB for analysis result by imageId.
    
    Args:
        image_id: Image ID (UUID) to query
        
    Returns:
        Dictionary with analysis data, or None if not found
    """
    try:
        resource = _get_dynamodb_resource()
        table = resource.Table(TABLE_NAME)
        
        logger.info(f"Querying table {TABLE_NAME} for ImageId: {image_id}")
        
        response = table.get_item(
            Key={'ImageId': image_id}
        )
        
        # Check if item was found
        if 'Item' not in response:
            return None
        
        item = response['Item']
        
        # Transform to API response format
        result = {
            'imageId': item.get('ImageId'),
            'characterName': item.get('CharacterName'),
            'confidence': item.get('Confidence'),
            'timestamp': item.get('Timestamp'),
            'metadata': item.get('Metadata', {})
        }
        
        return result
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}", exc_info=True)
        raise


def convert_decimals_to_float(obj: Any) -> Any:
    """
    Recursively convert Decimal objects to float for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        Object with Decimals converted to floats
    """
    if isinstance(obj, Decimal):
        # Convert to float, or int if it's a whole number
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    return obj


def create_error_response(status_code: int, error_code: str, message: str) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Application error code
        message: Error message
        
    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps({
            'error': error_code,
            'message': message
        })
    }
