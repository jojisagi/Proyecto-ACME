"""
Lambda function to process S3 events and analyze images with Rekognition.

This function is triggered by S3 events when images are uploaded. It invokes
Amazon Rekognition to detect labels, identifies cartoon characters, and stores
the analysis results in DynamoDB.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients (will be initialized on first use)
s3_client = None
rekognition_client = None
dynamodb = None

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'CartoonAnalysisResults')


def _get_s3_client():
    """Get or create S3 client."""
    global s3_client
    if s3_client is None:
        s3_client = boto3.client('s3')
    return s3_client


def _get_rekognition_client():
    """Get or create Rekognition client."""
    global rekognition_client
    if rekognition_client is None:
        rekognition_client = boto3.client('rekognition')
    return rekognition_client


def _get_dynamodb_resource():
    """Get or create DynamoDB resource."""
    global dynamodb
    if dynamodb is None:
        dynamodb = boto3.resource('dynamodb')
    return dynamodb

# Known cartoon characters for identification
KNOWN_CHARACTERS = [
    'Mickey Mouse', 'Minnie Mouse', 'Donald Duck', 'Goofy', 'Pluto',
    'Bugs Bunny', 'Daffy Duck', 'Tweety', 'Sylvester', 'Porky Pig',
    'SpongeBob', 'Patrick', 'Squidward', 'Sandy', 'Mr. Krabs',
    'Homer Simpson', 'Bart Simpson', 'Lisa Simpson', 'Marge Simpson',
    'Scooby-Doo', 'Shaggy', 'Fred', 'Daphne', 'Velma',
    'Tom', 'Jerry', 'Pikachu', 'Sonic', 'Mario', 'Luigi'
]


def lambda_handler(event: Dict[str, Any], context: Any) -> None:
    """
    Lambda handler to process S3 events and analyze images.
    
    Args:
        event: S3 event containing bucket and object information
        context: Lambda context object
    """
    logger.info(f"Received S3 event: {json.dumps(event)}")
    
    try:
        # Process each record in the event
        for record in event.get('Records', []):
            process_record(record)
            
    except Exception as e:
        logger.error(f"Unexpected error processing event: {str(e)}", exc_info=True)
        # Re-raise to trigger retry via DLQ
        raise


def process_record(record: Dict[str, Any]) -> None:
    """
    Process a single S3 event record.
    
    Args:
        record: S3 event record
    """
    try:
        # Extract bucket and key from S3 event
        s3_info = record.get('s3', {})
        bucket_name = s3_info.get('bucket', {}).get('name')
        object_key = s3_info.get('object', {}).get('key')
        
        if not bucket_name or not object_key:
            logger.error(f"Invalid S3 event record: missing bucket or key")
            return
        
        logger.info(f"Processing image: s3://{bucket_name}/{object_key}")
        
        # Extract imageId from object key (format: {uuid}.{extension})
        image_id = extract_image_id(object_key)
        
        # Get image metadata from S3
        image_metadata = get_image_metadata(bucket_name, object_key)
        
        # Call Rekognition to analyze the image
        rekognition_response = analyze_image_with_rekognition(bucket_name, object_key)
        
        # Extract character information from Rekognition results
        character_name, confidence = extract_character_from_labels(
            rekognition_response.get('Labels', [])
        )
        
        # Generate timestamp in ISO 8601 format
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Construct DynamoDB record
        record_data = {
            'ImageId': image_id,
            'CharacterName': character_name,
            'Confidence': confidence,
            'Timestamp': timestamp,
            'Metadata': {
                's3Bucket': bucket_name,
                's3Key': object_key,
                'imageSize': image_metadata.get('size', 0),
                'labels': [
                    {
                        'name': label.get('Name', ''),
                        'confidence': label.get('Confidence', 0.0)
                    }
                    for label in rekognition_response.get('Labels', [])
                ],
                'processingTime': 0  # Placeholder for processing time
            }
        }
        
        # Save to DynamoDB
        save_to_dynamodb(record_data)
        
        logger.info(f"Successfully processed image {image_id}: {character_name} ({confidence}%)")
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"AWS ClientError ({error_code}): {str(e)}", exc_info=True)
        
        # Handle specific error cases
        if error_code in ['InvalidImageFormatException', 'ImageTooLargeException']:
            # Permanent error - log and continue
            logger.warning(f"Permanent error processing image: {error_code}")
        else:
            # Transient error - re-raise for retry
            raise
            
    except Exception as e:
        logger.error(f"Error processing record: {str(e)}", exc_info=True)
        raise


def extract_image_id(object_key: str) -> str:
    """
    Extract image ID from S3 object key.
    
    Args:
        object_key: S3 object key (e.g., "uuid.jpg" or "path/uuid.png")
        
    Returns:
        Image ID (UUID without extension)
    """
    # Get filename from path
    filename = object_key.split('/')[-1]
    
    # Remove extension
    image_id = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    return image_id


def get_image_metadata(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """
    Get image metadata from S3.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        
    Returns:
        Dictionary with image metadata
    """
    try:
        client = _get_s3_client()
        response = client.head_object(Bucket=bucket_name, Key=object_key)
        
        return {
            'size': response.get('ContentLength', 0),
            'contentType': response.get('ContentType', ''),
            'lastModified': response.get('LastModified', '').isoformat() if response.get('LastModified') else ''
        }
    except ClientError as e:
        logger.warning(f"Failed to get image metadata: {str(e)}")
        return {'size': 0}


def analyze_image_with_rekognition(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """
    Analyze image using Amazon Rekognition DetectLabels API.
    
    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        
    Returns:
        Rekognition response dictionary
    """
    logger.info(f"Calling Rekognition DetectLabels for s3://{bucket_name}/{object_key}")
    
    try:
        client = _get_rekognition_client()
        response = client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_key
                }
            },
            MaxLabels=10,
            MinConfidence=70.0
        )
        
        logger.info(f"Rekognition returned {len(response.get('Labels', []))} labels")
        return response
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"Rekognition error ({error_code}): {str(e)}")
        
        # Return empty response for graceful degradation
        if error_code in ['InvalidImageFormatException', 'ImageTooLargeException']:
            return {'Labels': []}
        
        # Re-raise for transient errors
        raise


def extract_character_from_labels(labels: List[Dict[str, Any]]) -> tuple[str, float]:
    """
    Extract cartoon character name and confidence from Rekognition labels.
    
    Args:
        labels: List of Rekognition label dictionaries
        
    Returns:
        Tuple of (character_name, confidence)
    """
    if not labels:
        logger.warning("No labels detected by Rekognition")
        return ("Unknown", 0.0)
    
    # Strategy 1: Look for known cartoon characters in labels
    for label in labels:
        label_name = label.get('Name', '')
        confidence = label.get('Confidence', 0.0)
        
        # Check if label matches any known character
        for character in KNOWN_CHARACTERS:
            if character.lower() in label_name.lower() or label_name.lower() in character.lower():
                logger.info(f"Identified character: {character} (confidence: {confidence})")
                return (character, confidence)
    
    # Strategy 2: Use label with highest confidence as fallback
    highest_confidence_label = max(labels, key=lambda x: x.get('Confidence', 0.0))
    character_name = highest_confidence_label.get('Name', 'Unknown')
    confidence = highest_confidence_label.get('Confidence', 0.0)
    
    logger.info(f"Using highest confidence label: {character_name} (confidence: {confidence})")
    return (character_name, confidence)


def save_to_dynamodb(record_data: Dict[str, Any]) -> None:
    """
    Save analysis record to DynamoDB.
    
    Args:
        record_data: Dictionary containing record data
    """
    try:
        resource = _get_dynamodb_resource()
        table = resource.Table(TABLE_NAME)
        
        logger.info(f"Saving record to DynamoDB table {TABLE_NAME}")
        
        # Convert float to Decimal for DynamoDB
        from decimal import Decimal
        
        def convert_floats(obj):
            """Recursively convert floats to Decimal for DynamoDB."""
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(item) for item in obj]
            return obj
        
        record_data = convert_floats(record_data)
        
        table.put_item(Item=record_data)
        
        logger.info(f"Successfully saved record for ImageId: {record_data['ImageId']}")
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}", exc_info=True)
        raise
