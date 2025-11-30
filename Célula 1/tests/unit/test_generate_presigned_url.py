"""
Unit tests for GeneratePresignedUrl Lambda function.

Tests specific examples and edge cases for presigned URL generation.
"""

import json
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

import pytest

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.generate_presigned.handler import (
    lambda_handler,
    get_file_extension,
    create_error_response
)


class TestLambdaHandlerValidInputs:
    """Test cases for valid inputs."""
    
    def test_valid_jpeg_request(self):
        """Test successful presigned URL generation for JPEG image."""
        mock_url = "https://test-bucket.s3.amazonaws.com/test.jpg?signature=abc123"
        
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = mock_url
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'cartoon.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['uploadUrl'] == mock_url
            assert 'imageId' in body
            assert body['expiresIn'] == 300
    
    def test_valid_png_request(self):
        """Test successful presigned URL generation for PNG image."""
        mock_url = "https://test-bucket.s3.amazonaws.com/test.png?signature=xyz789"
        
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = mock_url
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'cartoon.png',
                    'contentType': 'image/png'
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['uploadUrl'] == mock_url
            assert 'imageId' in body
    
    def test_response_includes_cors_headers(self):
        """Test that response includes proper CORS headers."""
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://test.com/url"
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            response = lambda_handler(event, None)
            
            assert 'headers' in response
            headers = response['headers']
            assert headers['Access-Control-Allow-Origin'] == '*'
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers


class TestLambdaHandlerInvalidInputs:
    """Test cases for invalid inputs."""
    
    def test_missing_query_parameters(self):
        """Test error when query parameters are missing entirely."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'query parameters' in body['message'].lower()
    
    def test_missing_filename(self):
        """Test error when filename parameter is missing."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'contentType': 'image/jpeg'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'filename' in body['message'].lower()
    
    def test_missing_content_type(self):
        """Test error when contentType parameter is missing."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'filename': 'test.jpg'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'contenttype' in body['message'].lower()
    
    def test_invalid_content_type(self):
        """Test error when contentType is not supported."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'filename': 'test.gif',
                'contentType': 'image/gif'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'invalid' in body['message'].lower()
    
    def test_empty_filename(self):
        """Test error when filename is empty string."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'filename': '',
                'contentType': 'image/jpeg'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'


class TestS3ErrorHandling:
    """Test cases for S3 error handling."""
    
    def test_s3_client_error(self):
        """Test handling of S3 ClientError."""
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            # Simulate S3 ClientError
            mock_s3.generate_presigned_url.side_effect = ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket does not exist'}},
                'generate_presigned_url'
            )
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error'] == 'S3Error'
            assert 'presigned URL' in body['message']
    
    def test_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            # Simulate unexpected exception
            mock_s3.generate_presigned_url.side_effect = Exception("Unexpected error")
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error'] == 'InternalServerError'


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_get_file_extension_from_filename(self):
        """Test extracting extension from filename."""
        assert get_file_extension('image.jpg', 'image/jpeg') == 'jpg'
        assert get_file_extension('photo.jpeg', 'image/jpeg') == 'jpeg'
        assert get_file_extension('picture.png', 'image/png') == 'png'
    
    def test_get_file_extension_from_content_type(self):
        """Test deriving extension from content type when filename has no extension."""
        assert get_file_extension('image', 'image/jpeg') == 'jpg'
        assert get_file_extension('photo', 'image/jpg') == 'jpg'
        assert get_file_extension('picture', 'image/png') == 'png'
    
    def test_get_file_extension_invalid_extension_in_filename(self):
        """Test fallback when filename has invalid extension."""
        assert get_file_extension('image.gif', 'image/jpeg') == 'jpg'
        assert get_file_extension('image.bmp', 'image/png') == 'png'
    
    def test_create_error_response(self):
        """Test error response creation."""
        response = create_error_response(400, 'TestError', 'Test message')
        
        assert response['statusCode'] == 400
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['error'] == 'TestError'
        assert body['message'] == 'Test message'


class TestImageIdGeneration:
    """Test cases for image ID generation."""
    
    def test_unique_image_ids(self):
        """Test that multiple calls generate unique image IDs."""
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://test.com/url"
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            # Generate multiple image IDs
            image_ids = []
            for _ in range(10):
                response = lambda_handler(event, None)
                body = json.loads(response['body'])
                image_ids.append(body['imageId'])
            
            # All IDs should be unique
            assert len(image_ids) == len(set(image_ids))
    
    def test_image_id_uuid_format(self):
        """Test that image ID follows UUID v4 format."""
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://test.com/url"
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                }
            }
            
            response = lambda_handler(event, None)
            body = json.loads(response['body'])
            image_id = body['imageId']
            
            # UUID v4 format: 8-4-4-4-12 characters
            parts = image_id.split('-')
            assert len(parts) == 5
            assert len(parts[0]) == 8
            assert len(parts[1]) == 4
            assert len(parts[2]) == 4
            assert len(parts[3]) == 4
            assert len(parts[4]) == 12
