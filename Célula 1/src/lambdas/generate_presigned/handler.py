"""
Lambda function to generate presigned URLs for S3 image uploads.

This function handles API Gateway requests to generate temporary presigned URLs
that allow users to upload images directly to S3.
"""

import json
import logging
import os
import uuid
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')

# Environment variables
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'cartoon-rekognition-images-sandbox')
EXPIRATION_SECONDS = int(os.environ.get('EXPIRATION_SECONDS', '300'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to generate presigned URL for S3 upload.
    
    Args:
        event: API Gateway event containing queryStringParameters
        context: Lambda context object
        
    Returns:
        API Gateway response with presigned URL or error
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
        
        filename = query_params.get('filename')
        content_type = query_params.get('contentType')
        
        # Validate required parameters
        if not filename:
            return create_error_response(
                400,
                "BadRequest",
                "Missing required parameter: filename"
            )
        
        if not content_type:
            return create_error_response(
                400,
                "BadRequest",
                "Missing required parameter: contentType"
            )
        
        # Validate content type
        valid_content_types = ['image/jpeg', 'image/jpg', 'image/png']
        if content_type not in valid_content_types:
            return create_error_response(
                400,
                "BadRequest",
                f"Invalid contentType. Must be one of: {', '.join(valid_content_types)}"
            )
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Extract file extension from filename or content type
        file_extension = get_file_extension(filename, content_type)
        s3_key = f"{image_id}.{file_extension}"
        
        logger.info(f"Generating presigned URL for key: {s3_key}")
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key,
                'ContentType': content_type
            },
            ExpiresIn=EXPIRATION_SECONDS,
            HttpMethod='PUT'
        )
        
        logger.info(f"Successfully generated presigned URL for imageId: {image_id}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'uploadUrl': presigned_url,
                'imageId': image_id,
                'expiresIn': EXPIRATION_SECONDS
            })
        }
        
    except ClientError as e:
        logger.error(f"AWS ClientError: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            "S3Error",
            f"Failed to generate presigned URL: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            "InternalServerError",
            "An unexpected error occurred"
        )


def get_file_extension(filename: str, content_type: str) -> str:
    """
    Extract file extension from filename or derive from content type.
    
    Args:
        filename: Original filename
        content_type: MIME type
        
    Returns:
        File extension (without dot)
    """
    # Try to get extension from filename
    if '.' in filename:
        extension = filename.rsplit('.', 1)[-1].lower()
        if extension in ['jpg', 'jpeg', 'png']:
            return extension
    
    # Derive from content type
    content_type_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png'
    }
    
    return content_type_map.get(content_type, 'jpg')


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
