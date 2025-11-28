"""
Property-based tests for QueryResults Lambda function.

Feature: aws-cartoon-rekognition, Property 7: Query Results Return Complete Data
Validates: Requirements 4.4
"""

import json
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, settings, strategies as st

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.query_results.handler import lambda_handler


# Strategy for valid UUIDs (UUID v4 format)
valid_uuids = st.uuids().map(str)

# Strategy for character names
character_names = st.text(min_size=1, max_size=50, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'),
    whitelist_characters=' -'
))

# Strategy for confidence values (0-100)
confidence_values = st.floats(min_value=0.0, max_value=100.0)

# Strategy for ISO 8601 timestamps
timestamps = st.datetimes().map(lambda dt: dt.isoformat() + 'Z')

# Strategy for metadata
metadata_strategy = st.fixed_dictionaries({
    's3Bucket': st.text(min_size=3, max_size=63, alphabet=st.characters(
        whitelist_categories=('Ll', 'Nd'),
        whitelist_characters='-'
    )),
    's3Key': st.text(min_size=1, max_size=100),
    'imageSize': st.integers(min_value=0, max_value=15000000),
    'labels': st.lists(
        st.fixed_dictionaries({
            'name': st.text(min_size=1, max_size=50),
            'confidence': st.floats(min_value=0.0, max_value=100.0)
        }),
        min_size=0,
        max_size=10
    ),
    'processingTime': st.integers(min_value=0, max_value=300000)
})


@given(
    image_id=valid_uuids,
    character_name=character_names,
    confidence=confidence_values,
    timestamp=timestamps,
    metadata=metadata_strategy
)
@settings(max_examples=100)
def test_property_query_results_return_complete_data(
    image_id, character_name, confidence, timestamp, metadata
):
    """
    Property: For any valid imageId that exists in DynamoDB, calling the
    /prod/result endpoint should return the complete analysis data including
    all stored attributes (imageId, characterName, confidence, timestamp, metadata).
    
    Feature: aws-cartoon-rekognition, Property 7: Query Results Return Complete Data
    Validates: Requirements 4.4
    """
    # Create mock DynamoDB item with Decimal types (as DynamoDB returns)
    mock_item = {
        'ImageId': image_id,
        'CharacterName': character_name,
        'Confidence': Decimal(str(confidence)),
        'Timestamp': timestamp,
        'Metadata': {
            's3Bucket': metadata['s3Bucket'],
            's3Key': metadata['s3Key'],
            'imageSize': metadata['imageSize'],
            'labels': [
                {
                    'name': label['name'],
                    'confidence': Decimal(str(label['confidence']))
                }
                for label in metadata['labels']
            ],
            'processingTime': metadata['processingTime']
        }
    }
    
    # Mock DynamoDB resource
    with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {'Item': mock_item}
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_get_db.return_value = mock_resource
        
        # Create API Gateway event
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'imageId': image_id
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Verify response structure
        assert response is not None, "Response should not be None"
        assert 'statusCode' in response, "Response should have statusCode"
        assert 'body' in response, "Response should have body"
        
        # Should return 200 OK for existing item
        assert response['statusCode'] == 200, f"Expected 200 status, got {response['statusCode']}"
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify all required fields are present
        assert 'imageId' in body, "Response should contain imageId"
        assert 'characterName' in body, "Response should contain characterName"
        assert 'confidence' in body, "Response should contain confidence"
        assert 'timestamp' in body, "Response should contain timestamp"
        assert 'metadata' in body, "Response should contain metadata"
        
        # Verify field values match the stored data
        assert body['imageId'] == image_id, "imageId should match"
        assert body['characterName'] == character_name, "characterName should match"
        
        # Confidence should be numeric (float or int)
        assert isinstance(body['confidence'], (int, float)), "confidence should be numeric"
        assert abs(body['confidence'] - confidence) < 0.01, "confidence value should match"
        
        assert body['timestamp'] == timestamp, "timestamp should match"
        
        # Verify metadata structure
        assert isinstance(body['metadata'], dict), "metadata should be a dictionary"
        assert 's3Bucket' in body['metadata'], "metadata should contain s3Bucket"
        assert 's3Key' in body['metadata'], "metadata should contain s3Key"
        assert 'imageSize' in body['metadata'], "metadata should contain imageSize"
        assert 'labels' in body['metadata'], "metadata should contain labels"
        assert 'processingTime' in body['metadata'], "metadata should contain processingTime"
        
        # Verify metadata values
        assert body['metadata']['s3Bucket'] == metadata['s3Bucket']
        assert body['metadata']['s3Key'] == metadata['s3Key']
        assert body['metadata']['imageSize'] == metadata['imageSize']
        assert body['metadata']['processingTime'] == metadata['processingTime']
        
        # Verify labels structure
        assert isinstance(body['metadata']['labels'], list), "labels should be a list"
        assert len(body['metadata']['labels']) == len(metadata['labels'])
        
        # Verify DynamoDB was queried correctly
        mock_table.get_item.assert_called_once()
        call_args = mock_table.get_item.call_args
        assert call_args[1]['Key'] == {'ImageId': image_id}


@given(image_id=valid_uuids)
@settings(max_examples=100)
def test_property_query_nonexistent_returns_404(image_id):
    """
    Property: For any valid UUID that does not exist in DynamoDB,
    the system should return 404 Not Found.
    
    Feature: aws-cartoon-rekognition, Property 7: Query Results Return Complete Data
    Validates: Requirements 4.4
    """
    # Mock DynamoDB resource to return no item
    with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # No 'Item' key means not found
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_get_db.return_value = mock_resource
        
        # Create API Gateway event
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'imageId': image_id
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Should return 404 Not Found
        assert response['statusCode'] == 404, f"Expected 404 status, got {response['statusCode']}"
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify error structure
        assert 'error' in body, "Error response should contain error field"
        assert 'message' in body, "Error response should contain message field"
        assert body['error'] == 'NotFound', "Error code should be NotFound"
        assert image_id in body['message'], "Error message should mention the imageId"


@given(
    invalid_id=st.one_of(
        st.text(min_size=1, max_size=50).filter(
            lambda x: not x.count('-') == 4 or len(x) != 36
        ),
        st.just('not-a-uuid'),
        st.just('12345'),
        st.just(''),
    )
)
@settings(max_examples=100)
def test_property_invalid_uuid_format_rejected(invalid_id):
    """
    Property: For any imageId that is not a valid UUID v4 format,
    the system should reject the request with 400 Bad Request.
    
    Feature: aws-cartoon-rekognition, Property 7: Query Results Return Complete Data
    Validates: Requirements 4.4
    """
    # Skip empty string as it's handled by missing parameter check
    if invalid_id == '':
        return
    
    with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
        # Create API Gateway event with invalid imageId
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'imageId': invalid_id
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400, f"Expected 400 status for invalid UUID, got {response['statusCode']}"
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify error structure
        assert 'error' in body, "Error response should contain error field"
        assert 'message' in body, "Error response should contain message field"
        assert body['error'] == 'BadRequest', "Error code should be BadRequest"
        
        # DynamoDB should not be queried for invalid input
        mock_get_db.assert_not_called()


@given(image_id=valid_uuids)
@settings(max_examples=50)
def test_property_response_includes_cors_headers(image_id):
    """
    Property: For any query, the response should include proper CORS headers
    to allow cross-origin requests.
    
    Feature: aws-cartoon-rekognition, Property 7: Query Results Return Complete Data
    Validates: Requirements 4.4
    """
    # Mock DynamoDB resource
    with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # Not found is fine for this test
        
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_get_db.return_value = mock_resource
        
        # Create API Gateway event
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'imageId': image_id
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Verify CORS headers are present
        assert 'headers' in response, "Response should have headers"
        headers = response['headers']
        
        assert 'Access-Control-Allow-Origin' in headers, "Should have CORS origin header"
        assert headers['Access-Control-Allow-Origin'] == '*', "Should allow all origins"
        
        assert 'Access-Control-Allow-Headers' in headers, "Should have CORS headers header"
        assert 'Access-Control-Allow-Methods' in headers, "Should have CORS methods header"
        
        assert 'Content-Type' in headers, "Should have Content-Type header"
        assert headers['Content-Type'] == 'application/json', "Content-Type should be JSON"
