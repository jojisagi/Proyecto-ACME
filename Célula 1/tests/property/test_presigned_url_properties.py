"""
Property-based tests for presigned URL generation.

Feature: aws-cartoon-rekognition, Property 1: Presigned URL Generation Validity
Validates: Requirements 1.2
"""

import json
import os
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

import pytest
from hypothesis import given, settings, strategies as st

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.generate_presigned.handler import lambda_handler


# Strategy for valid filenames
valid_filenames = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='.-_'
    ),
    min_size=1,
    max_size=100
).map(lambda s: s if '.' in s else s + '.jpg')

# Strategy for valid content types
valid_content_types = st.sampled_from([
    'image/jpeg',
    'image/jpg',
    'image/png'
])


@given(filename=valid_filenames, content_type=valid_content_types)
@settings(max_examples=100)
def test_property_presigned_url_generation_validity(filename, content_type):
    """
    Property: For any valid filename and content type, the system should generate
    a valid presigned URL that expires after the configured time period.
    
    Feature: aws-cartoon-rekognition, Property 1: Presigned URL Generation Validity
    Validates: Requirements 1.2
    """
    # Mock the S3 client to avoid actual AWS calls
    mock_presigned_url = "https://test-bucket.s3.amazonaws.com/test-key?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=test"
    
    with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
        mock_s3.generate_presigned_url.return_value = mock_presigned_url
        
        # Create API Gateway event
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'filename': filename,
                'contentType': content_type
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Verify response structure
        assert response is not None, "Response should not be None"
        assert 'statusCode' in response, "Response should have statusCode"
        assert 'body' in response, "Response should have body"
        
        # For valid inputs, we expect 200 status
        assert response['statusCode'] == 200, f"Expected 200 status for valid inputs, got {response['statusCode']}"
        
        # Parse response body
        body = json.loads(response['body'])
        
        # Verify required fields are present
        assert 'uploadUrl' in body, "Response body should contain uploadUrl"
        assert 'imageId' in body, "Response body should contain imageId"
        assert 'expiresIn' in body, "Response body should contain expiresIn"
        
        # Verify uploadUrl is a valid URL
        upload_url = body['uploadUrl']
        assert upload_url.startswith('https://'), "Upload URL should use HTTPS"
        
        parsed_url = urlparse(upload_url)
        assert parsed_url.scheme == 'https', "URL scheme should be https"
        assert parsed_url.netloc, "URL should have a valid netloc"
        
        # Verify imageId is a valid UUID format
        image_id = body['imageId']
        assert len(image_id) == 36, "ImageId should be UUID format (36 chars with hyphens)"
        assert image_id.count('-') == 4, "UUID should have 4 hyphens"
        
        # Verify expiresIn matches configured value
        expires_in = body['expiresIn']
        assert isinstance(expires_in, int), "expiresIn should be an integer"
        assert expires_in > 0, "expiresIn should be positive"
        assert expires_in == 300, "expiresIn should match EXPIRATION_SECONDS (300)"
        
        # Verify S3 client was called with correct parameters
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        
        assert call_args[0][0] == 'put_object', "Should call put_object operation"
        assert 'Params' in call_args[1], "Should include Params"
        assert call_args[1]['Params']['ContentType'] == content_type, "Should pass correct ContentType"
        assert call_args[1]['ExpiresIn'] == 300, "Should set correct expiration"
        assert call_args[1]['HttpMethod'] == 'PUT', "Should use PUT method"


@given(
    filename=st.one_of(st.none(), st.just('')),
    content_type=valid_content_types
)
@settings(max_examples=50)
def test_property_invalid_filename_rejected(filename, content_type):
    """
    Property: For any missing or empty filename, the system should reject
    the request with a 400 Bad Request error.
    
    Feature: aws-cartoon-rekognition, Property 1: Presigned URL Generation Validity
    Validates: Requirements 1.2
    """
    with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
        # Create API Gateway event with invalid filename
        query_params = {'contentType': content_type}
        if filename is not None:
            query_params['filename'] = filename
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': query_params
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400, "Should return 400 for invalid filename"
        
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain error field"
        assert 'message' in body, "Error response should contain message field"
        
        # S3 client should not be called for invalid input
        mock_s3.generate_presigned_url.assert_not_called()


@given(
    filename=valid_filenames,
    content_type=st.one_of(st.none(), st.just(''))
)
@settings(max_examples=50)
def test_property_invalid_content_type_rejected(filename, content_type):
    """
    Property: For any missing or empty content type, the system should reject
    the request with a 400 Bad Request error.
    
    Feature: aws-cartoon-rekognition, Property 1: Presigned URL Generation Validity
    Validates: Requirements 1.2
    """
    with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
        # Create API Gateway event with invalid content type
        query_params = {'filename': filename}
        if content_type is not None:
            query_params['contentType'] = content_type
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': query_params
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400, "Should return 400 for invalid content type"
        
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain error field"
        assert 'message' in body, "Error response should contain message field"
        
        # S3 client should not be called for invalid input
        mock_s3.generate_presigned_url.assert_not_called()


@given(
    filename=valid_filenames,
    content_type=st.text(min_size=1, max_size=50).filter(
        lambda x: x not in ['image/jpeg', 'image/jpg', 'image/png']
    )
)
@settings(max_examples=50)
def test_property_unsupported_content_type_rejected(filename, content_type):
    """
    Property: For any unsupported content type (not image/jpeg, image/jpg, or image/png),
    the system should reject the request with a 400 Bad Request error.
    
    Feature: aws-cartoon-rekognition, Property 1: Presigned URL Generation Validity
    Validates: Requirements 1.2
    """
    with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
        # Create API Gateway event with unsupported content type
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'filename': filename,
                'contentType': content_type
            }
        }
        
        # Call the handler
        response = lambda_handler(event, None)
        
        # Should return 400 Bad Request
        assert response['statusCode'] == 400, "Should return 400 for unsupported content type"
        
        body = json.loads(response['body'])
        assert 'error' in body, "Error response should contain error field"
        assert body['error'] == 'BadRequest', "Error code should be BadRequest"
        
        # S3 client should not be called for invalid input
        mock_s3.generate_presigned_url.assert_not_called()
