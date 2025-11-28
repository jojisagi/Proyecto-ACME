"""
Unit tests for QueryResults Lambda function.

Tests specific examples and edge cases for querying analysis results.
"""

import json
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

import pytest

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.query_results.handler import (
    lambda_handler,
    is_valid_uuid,
    query_dynamodb,
    convert_decimals_to_float,
    create_error_response
)


class TestLambdaHandlerValidImageId:
    """Test cases for valid imageId queries."""
    
    def test_existing_image_id_returns_complete_data(self):
        """Test successful query with existing imageId."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_item = {
            'ImageId': image_id,
            'CharacterName': 'Mickey Mouse',
            'Confidence': Decimal('98.5'),
            'Timestamp': '2025-11-27T10:30:00Z',
            'Metadata': {
                's3Bucket': 'test-bucket',
                's3Key': f'{image_id}.jpg',
                'imageSize': 1024000,
                'labels': [
                    {'name': 'Mouse', 'confidence': Decimal('98.5')},
                    {'name': 'Cartoon', 'confidence': Decimal('95.0')}
                ],
                'processingTime': 1500
            }
        }
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {'Item': mock_item}
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            
            assert body['imageId'] == image_id
            assert body['characterName'] == 'Mickey Mouse'
            assert body['confidence'] == 98.5
            assert body['timestamp'] == '2025-11-27T10:30:00Z'
            assert 'metadata' in body
            assert body['metadata']['s3Bucket'] == 'test-bucket'
    
    def test_response_includes_cors_headers(self):
        """Test that response includes proper CORS headers."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {}
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            assert 'headers' in response
            headers = response['headers']
            assert headers['Access-Control-Allow-Origin'] == '*'
            assert 'Access-Control-Allow-Headers' in headers
            assert 'Access-Control-Allow-Methods' in headers


class TestLambdaHandlerNonExistentImageId:
    """Test cases for non-existent imageId (404)."""
    
    def test_nonexistent_image_id_returns_404(self):
        """Test 404 response when imageId doesn't exist."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {}  # No 'Item' key
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 404
            body = json.loads(response['body'])
            assert body['error'] == 'NotFound'
            assert image_id in body['message']
    
    def test_nonexistent_image_id_logs_appropriately(self):
        """Test that non-existent imageId is logged."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {}
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            # Verify DynamoDB was queried
            mock_table.get_item.assert_called_once()


class TestLambdaHandlerInvalidImageId:
    """Test cases for invalid imageId format."""
    
    def test_invalid_uuid_format_returns_400(self):
        """Test 400 response for invalid UUID format."""
        invalid_ids = [
            'not-a-uuid',
            '12345',
            'abc-def-ghi',
            '550e8400-e29b-41d4-a716',  # Too short
            '550e8400-e29b-41d4-a716-446655440000-extra',  # Too long
        ]
        
        for invalid_id in invalid_ids:
            with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
                event = {
                    'httpMethod': 'GET',
                    'queryStringParameters': {
                        'imageId': invalid_id
                    }
                }
                
                response = lambda_handler(event, None)
                
                assert response['statusCode'] == 400, f"Failed for: {invalid_id}"
                body = json.loads(response['body'])
                assert body['error'] == 'BadRequest'
                assert 'UUID' in body['message'] or 'uuid' in body['message'].lower()
                
                # DynamoDB should not be called
                mock_get_db.assert_not_called()
    
    def test_missing_image_id_returns_400(self):
        """Test 400 response when imageId parameter is missing."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'otherParam': 'value'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'imageId' in body['message']
    
    def test_empty_image_id_returns_400(self):
        """Test 400 response when imageId is empty string."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'imageId': ''
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
    
    def test_missing_query_parameters_returns_400(self):
        """Test 400 response when query parameters are missing entirely."""
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'BadRequest'
        assert 'query parameters' in body['message'].lower()


class TestDynamoDBErrorHandling:
    """Test cases for DynamoDB error handling."""
    
    def test_dynamodb_client_error(self):
        """Test handling of DynamoDB ClientError."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.side_effect = ClientError(
                {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
                'GetItem'
            )
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error'] == 'DynamoDBError'
            assert 'DynamoDB' in body['message']
    
    def test_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_get_db.side_effect = Exception("Unexpected error")
            
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 500
            body = json.loads(response['body'])
            assert body['error'] == 'InternalServerError'


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_is_valid_uuid_with_valid_uuids(self):
        """Test UUID validation with valid UUIDs."""
        valid_uuids = [
            '550e8400-e29b-41d4-a716-446655440000',
            '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
            'f47ac10b-58cc-4372-a567-0e02b2c3d479',
        ]
        
        for uuid in valid_uuids:
            assert is_valid_uuid(uuid) is True, f"Should be valid: {uuid}"
            # Test case insensitivity
            assert is_valid_uuid(uuid.upper()) is True
            assert is_valid_uuid(uuid.lower()) is True
    
    def test_is_valid_uuid_with_invalid_uuids(self):
        """Test UUID validation with invalid UUIDs."""
        invalid_uuids = [
            'not-a-uuid',
            '12345',
            '',
            None,
            '550e8400-e29b-41d4-a716',  # Too short
            '550e8400-e29b-41d4-a716-446655440000-extra',  # Too long
        ]
        
        for uuid in invalid_uuids:
            assert is_valid_uuid(uuid) is False, f"Should be invalid: {uuid}"
    
    def test_convert_decimals_to_float(self):
        """Test Decimal to float conversion."""
        # Test simple Decimal
        assert convert_decimals_to_float(Decimal('98.5')) == 98.5
        assert convert_decimals_to_float(Decimal('100')) == 100
        
        # Test nested structure
        obj = {
            'confidence': Decimal('98.5'),
            'count': Decimal('10'),
            'nested': {
                'value': Decimal('50.25')
            },
            'list': [Decimal('1.1'), Decimal('2.2')]
        }
        
        result = convert_decimals_to_float(obj)
        
        assert result['confidence'] == 98.5
        assert result['count'] == 10
        assert result['nested']['value'] == 50.25
        assert result['list'] == [1.1, 2.2]
    
    def test_create_error_response(self):
        """Test error response creation."""
        response = create_error_response(404, 'NotFound', 'Resource not found')
        
        assert response['statusCode'] == 404
        assert 'headers' in response
        assert response['headers']['Content-Type'] == 'application/json'
        
        body = json.loads(response['body'])
        assert body['error'] == 'NotFound'
        assert body['message'] == 'Resource not found'


class TestQueryDynamoDB:
    """Test cases for query_dynamodb function."""
    
    def test_query_dynamodb_existing_item(self):
        """Test querying existing item from DynamoDB."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        mock_item = {
            'ImageId': image_id,
            'CharacterName': 'SpongeBob',
            'Confidence': Decimal('95.0'),
            'Timestamp': '2025-11-27T12:00:00Z',
            'Metadata': {}
        }
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {'Item': mock_item}
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            result = query_dynamodb(image_id)
            
            assert result is not None
            assert result['imageId'] == image_id
            assert result['characterName'] == 'SpongeBob'
            assert result['confidence'] == Decimal('95.0')
    
    def test_query_dynamodb_nonexistent_item(self):
        """Test querying non-existent item returns None."""
        image_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with patch('lambdas.query_results.handler._get_dynamodb_resource') as mock_get_db:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {}  # No 'Item' key
            
            mock_resource = MagicMock()
            mock_resource.Table.return_value = mock_table
            mock_get_db.return_value = mock_resource
            
            result = query_dynamodb(image_id)
            
            assert result is None
