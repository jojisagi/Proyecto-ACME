"""
Unit tests for S3EventProcessor Lambda function.

Tests specific examples and edge cases for S3 event processing.
"""

import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from decimal import Decimal

import pytest
from botocore.exceptions import ClientError

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.s3_event_processor.handler import (
    lambda_handler,
    extract_image_id,
    extract_character_from_labels
)


def create_mock_clients():
    """Helper to create mock AWS clients."""
    mock_rekognition = MagicMock()
    mock_s3 = MagicMock()
    mock_dynamodb = MagicMock()
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    return mock_rekognition, mock_s3, mock_dynamodb, mock_table


class TestLambdaHandlerValidEvent:
    """Test cases for valid S3 events."""
    
    def test_valid_s3_event(self):
        """Test successful processing of valid S3 event."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
             patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
            
            mock_rek, mock_s3, mock_ddb, mock_table = create_mock_clients()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            mock_get_ddb.return_value = mock_ddb
            
            mock_rek.detect_labels.return_value = {
                'Labels': [
                    {'Name': 'Mickey Mouse', 'Confidence': 98.5},
                    {'Name': 'Cartoon', 'Confidence': 95.0}
                ]
            }
            
            mock_s3.head_object.return_value = {
                'ContentLength': 1024000,
                'ContentType': 'image/jpeg'
            }
            
            event = {
                'Records': [{
                    's3': {
                        'bucket': {'name': 'test-bucket'},
                        'object': {'key': 'abc-123-def.jpg'}
                    }
                }]
            }
            
            lambda_handler(event, None)
            
            mock_rek.detect_labels.assert_called_once()
            mock_table.put_item.assert_called_once()
    
    def test_multiple_records_in_event(self):
        """Test processing multiple S3 records in one event."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
             patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
            
            mock_rek, mock_s3, mock_ddb, mock_table = create_mock_clients()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            mock_get_ddb.return_value = mock_ddb
            
            mock_rek.detect_labels.return_value = {
                'Labels': [{'Name': 'Cartoon', 'Confidence': 90.0}]
            }
            
            mock_s3.head_object.return_value = {
                'ContentLength': 1024000,
                'ContentType': 'image/jpeg'
            }
            
            event = {
                'Records': [
                    {'s3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'image1.jpg'}}},
                    {'s3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'image2.png'}}}
                ]
            }
            
            lambda_handler(event, None)
            
            assert mock_rek.detect_labels.call_count == 2
            assert mock_table.put_item.call_count == 2


class TestRekognitionIntegration:
    """Test cases for Rekognition integration."""
    
    def test_rekognition_no_labels(self):
        """Test handling when Rekognition returns no labels (edge case)."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
             patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
            
            mock_rek, mock_s3, mock_ddb, mock_table = create_mock_clients()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            mock_get_ddb.return_value = mock_ddb
            
            mock_rek.detect_labels.return_value = {'Labels': []}
            mock_s3.head_object.return_value = {'ContentLength': 1024000, 'ContentType': 'image/jpeg'}
            
            event = {
                'Records': [{
                    's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'test.jpg'}}
                }]
            }
            
            lambda_handler(event, None)
            
            mock_table.put_item.assert_called_once()
            saved_record = mock_table.put_item.call_args[1]['Item']
            assert saved_record['CharacterName'] == 'Unknown'
            assert float(saved_record['Confidence']) == 0.0
    
    def test_rekognition_failure(self):
        """Test handling of Rekognition API failure."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3:
            
            mock_rek = MagicMock()
            mock_s3 = MagicMock()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            
            mock_rek.detect_labels.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'detect_labels'
            )
            mock_s3.head_object.return_value = {'ContentLength': 1024000}
            
            event = {
                'Records': [{
                    's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'test.jpg'}}
                }]
            }
            
            with pytest.raises(ClientError):
                lambda_handler(event, None)


class TestCharacterExtraction:
    """Test cases for character extraction logic."""
    
    def test_extract_known_character(self):
        """Test extraction of known cartoon character."""
        labels = [
            {'Name': 'Mickey Mouse', 'Confidence': 98.5},
            {'Name': 'Cartoon', 'Confidence': 95.0}
        ]
        
        character, confidence = extract_character_from_labels(labels)
        
        assert character == 'Mickey Mouse'
        assert confidence == 98.5
    
    def test_extract_fallback_to_highest_confidence(self):
        """Test fallback to highest confidence label when no known character found."""
        labels = [
            {'Name': 'Animated', 'Confidence': 95.0},
            {'Name': 'Drawing', 'Confidence': 92.0}
        ]
        
        character, confidence = extract_character_from_labels(labels)
        
        assert character == 'Animated'
        assert confidence == 95.0
    
    def test_extract_empty_labels(self):
        """Test extraction with empty labels list."""
        character, confidence = extract_character_from_labels([])
        
        assert character == 'Unknown'
        assert confidence == 0.0


class TestHelperFunctions:
    """Test cases for helper functions."""
    
    def test_extract_image_id_simple(self):
        """Test extracting image ID from simple filename."""
        assert extract_image_id('abc-123-def.jpg') == 'abc-123-def'
        assert extract_image_id('uuid-456.png') == 'uuid-456'
    
    def test_extract_image_id_with_path(self):
        """Test extracting image ID from key with path."""
        assert extract_image_id('images/abc-123.jpg') == 'abc-123'
        assert extract_image_id('folder/subfolder/uuid.png') == 'uuid'
    
    def test_extract_image_id_no_extension(self):
        """Test extracting image ID when no extension present."""
        assert extract_image_id('abc-123-def') == 'abc-123-def'


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_invalid_s3_event_record(self):
        """Test handling of invalid S3 event record."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek:
            mock_rek = MagicMock()
            mock_get_rek.return_value = mock_rek
            
            event = {
                'Records': [{
                    's3': {
                        'bucket': {},
                        'object': {'key': 'test.jpg'}
                    }
                }]
            }
            
            lambda_handler(event, None)
            
            mock_rek.detect_labels.assert_not_called()
    
    def test_transient_error_raises_for_retry(self):
        """Test that transient errors are raised for retry."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3:
            
            mock_rek = MagicMock()
            mock_s3 = MagicMock()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            
            mock_rek.detect_labels.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'detect_labels'
            )
            mock_s3.head_object.return_value = {'ContentLength': 1024000}
            
            event = {
                'Records': [{
                    's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'test.jpg'}}
                }]
            }
            
            with pytest.raises(ClientError):
                lambda_handler(event, None)


class TestDynamoDBRecordStructure:
    """Test cases for DynamoDB record structure."""
    
    def test_timestamp_iso8601_format(self):
        """Test that generated timestamps are in ISO 8601 format."""
        with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
             patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
             patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
            
            mock_rek, mock_s3, mock_ddb, mock_table = create_mock_clients()
            mock_get_rek.return_value = mock_rek
            mock_get_s3.return_value = mock_s3
            mock_get_ddb.return_value = mock_ddb
            
            mock_rek.detect_labels.return_value = {
                'Labels': [{'Name': 'Test', 'Confidence': 90.0}]
            }
            mock_s3.head_object.return_value = {'ContentLength': 1024000, 'ContentType': 'image/jpeg'}
            
            event = {
                'Records': [{
                    's3': {'bucket': {'name': 'test-bucket'}, 'object': {'key': 'test.jpg'}}
                }]
            }
            
            lambda_handler(event, None)
            
            saved_record = mock_table.put_item.call_args[1]['Item']
            timestamp = saved_record['Timestamp']
            
            assert isinstance(timestamp, str)
            assert 'T' in timestamp
            assert timestamp.endswith('Z')
            
            # Verify it can be parsed as datetime
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
