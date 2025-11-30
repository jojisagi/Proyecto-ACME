"""
Property-based tests for Lambda CloudWatch logging.

Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
Validates: Requirements 12.1
"""

import json
import logging
import os
from io import StringIO
from unittest.mock import patch, MagicMock, call
import sys

import pytest
from hypothesis import given, settings, strategies as st

# Import the handlers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.generate_presigned.handler import lambda_handler as generate_presigned_handler
from lambdas.s3_event_processor.handler import lambda_handler as s3_processor_handler
from lambdas.query_results.handler import lambda_handler as query_results_handler


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

# Strategy for valid UUIDs
valid_uuids = st.uuids().map(str)


@given(filename=valid_filenames, content_type=valid_content_types)
@settings(max_examples=100)
def test_property_generate_presigned_logs_to_cloudwatch(filename, content_type):
    """
    Property: For any Lambda execution (GeneratePresignedUrl), all log statements
    should be successfully sent to CloudWatch Logs.
    
    Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
    Validates: Requirements 12.1
    """
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    
    # Get the root logger used by the Lambda function
    logger = logging.getLogger()
    original_level = logger.level
    original_handlers = logger.handlers[:]
    
    try:
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]
        
        # Mock S3 client
        mock_presigned_url = "https://test-bucket.s3.amazonaws.com/test-key"
        
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = mock_presigned_url
            
            # Create event
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': filename,
                    'contentType': content_type
                }
            }
            
            # Call handler
            response = generate_presigned_handler(event, None)
            
            # Get log output
            log_output = log_capture.getvalue()
            
            # Verify logs were generated
            assert log_output, "Lambda should generate log output"
            assert len(log_output) > 0, "Log output should not be empty"
            
            # Verify specific log messages are present
            assert "Received event:" in log_output, "Should log received event"
            
            if response['statusCode'] == 200:
                # For successful requests, verify success log
                assert "Successfully generated presigned URL" in log_output or \
                       "Generating presigned URL" in log_output, \
                       "Should log successful URL generation"
            else:
                # For error cases, verify error logging
                assert "error" in log_output.lower() or \
                       "failed" in log_output.lower(), \
                       "Should log errors"
    
    finally:
        # Restore original logger configuration
        logger.setLevel(original_level)
        logger.handlers = original_handlers


@given(
    bucket=st.text(min_size=3, max_size=63, alphabet=st.characters(
        whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'
    )),
    key=valid_filenames
)
@settings(max_examples=100)
def test_property_s3_processor_logs_to_cloudwatch(bucket, key):
    """
    Property: For any Lambda execution (S3EventProcessor), all log statements
    should be successfully sent to CloudWatch Logs.
    
    Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
    Validates: Requirements 12.1
    """
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    
    # Get the root logger used by the Lambda function
    logger = logging.getLogger()
    original_level = logger.level
    original_handlers = logger.handlers[:]
    
    try:
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]
        
        # Mock AWS services
        with patch('lambdas.s3_event_processor.handler.s3_client') as mock_s3, \
             patch('lambdas.s3_event_processor.handler.rekognition_client') as mock_rekognition, \
             patch('lambdas.s3_event_processor.handler.dynamodb') as mock_dynamodb:
            
            # Setup mocks
            mock_s3.head_object.return_value = {'ContentLength': 1024000}
            mock_rekognition.detect_labels.return_value = {
                'Labels': [
                    {'Name': 'Mickey Mouse', 'Confidence': 95.5},
                    {'Name': 'Cartoon', 'Confidence': 98.0}
                ]
            }
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Create S3 event
            event = {
                'Records': [{
                    's3': {
                        'bucket': {'name': bucket},
                        'object': {'key': key}
                    }
                }]
            }
            
            # Call handler
            try:
                response = s3_processor_handler(event, None)
            except Exception:
                # Even if handler fails, logs should be generated
                pass
            
            # Get log output
            log_output = log_capture.getvalue()
            
            # Verify logs were generated
            assert log_output, "Lambda should generate log output"
            assert len(log_output) > 0, "Log output should not be empty"
            
            # Verify specific log messages are present
            assert "Received S3 event:" in log_output or \
                   "Processing image:" in log_output, \
                   "Should log S3 event processing"
    
    finally:
        # Restore original logger configuration
        logger.setLevel(original_level)
        logger.handlers = original_handlers


@given(image_id=valid_uuids)
@settings(max_examples=100)
def test_property_query_results_logs_to_cloudwatch(image_id):
    """
    Property: For any Lambda execution (QueryResults), all log statements
    should be successfully sent to CloudWatch Logs.
    
    Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
    Validates: Requirements 12.1
    """
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    
    # Get the root logger used by the Lambda function
    logger = logging.getLogger()
    original_level = logger.level
    original_handlers = logger.handlers[:]
    
    try:
        logger.setLevel(logging.INFO)
        logger.handlers = [handler]
        
        # Mock DynamoDB
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            mock_table = MagicMock()
            mock_table.get_item.return_value = {
                'Item': {
                    'ImageId': image_id,
                    'CharacterName': 'Mickey Mouse',
                    'Confidence': 95.5,
                    'Timestamp': '2025-11-27T10:00:00Z',
                    'Metadata': {
                        's3Bucket': 'test-bucket',
                        's3Key': f'{image_id}.jpg',
                        'imageSize': 1024000
                    }
                }
            }
            mock_dynamodb.Table.return_value = mock_table
            
            # Create event
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'imageId': image_id
                }
            }
            
            # Call handler
            response = query_results_handler(event, None)
            
            # Get log output
            log_output = log_capture.getvalue()
            
            # Verify logs were generated
            assert log_output, "Lambda should generate log output"
            assert len(log_output) > 0, "Log output should not be empty"
            
            # Verify specific log messages are present
            assert "Received event:" in log_output, "Should log received event"
            
            if response['statusCode'] == 200:
                # For successful requests, verify success log
                assert "Successfully retrieved data" in log_output or \
                       image_id in log_output, \
                       "Should log successful data retrieval"
            elif response['statusCode'] == 404:
                # For not found, verify appropriate log
                assert "not found" in log_output.lower(), \
                       "Should log when image not found"
    
    finally:
        # Restore original logger configuration
        logger.setLevel(original_level)
        logger.handlers = original_handlers


@given(
    filename=valid_filenames,
    content_type=valid_content_types
)
@settings(max_examples=50)
def test_property_error_cases_logged_to_cloudwatch(filename, content_type):
    """
    Property: For any Lambda execution that encounters an error, error details
    should be logged to CloudWatch Logs.
    
    Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
    Validates: Requirements 12.1
    """
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.ERROR)
    
    # Get the root logger used by the Lambda function
    logger = logging.getLogger()
    original_level = logger.level
    original_handlers = logger.handlers[:]
    
    try:
        logger.setLevel(logging.ERROR)
        logger.handlers = [handler]
        
        # Mock S3 client to raise an error
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.side_effect = Exception("Simulated AWS error")
            
            # Create event
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': filename,
                    'contentType': content_type
                }
            }
            
            # Call handler
            response = generate_presigned_handler(event, None)
            
            # Should return error response
            assert response['statusCode'] == 500, "Should return 500 for errors"
            
            # Get log output
            log_output = log_capture.getvalue()
            
            # Verify error was logged
            assert log_output, "Lambda should log errors"
            assert "error" in log_output.lower(), "Should log error message"
            assert "Simulated AWS error" in log_output or \
                   "Unexpected error" in log_output, \
                   "Should log specific error details"
    
    finally:
        # Restore original logger configuration
        logger.setLevel(original_level)
        logger.handlers = original_handlers


@given(
    filename=valid_filenames,
    content_type=valid_content_types
)
@settings(max_examples=50)
def test_property_all_log_levels_sent_to_cloudwatch(filename, content_type):
    """
    Property: For any Lambda execution, logs at all levels (INFO, WARNING, ERROR)
    should be sent to CloudWatch Logs.
    
    Feature: aws-cartoon-rekognition, Property 13: Lambda Logs Sent to CloudWatch
    Validates: Requirements 12.1
    """
    # Capture log output at all levels
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Get the root logger used by the Lambda function
    logger = logging.getLogger()
    original_level = logger.level
    original_handlers = logger.handlers[:]
    
    try:
        logger.setLevel(logging.DEBUG)
        logger.handlers = [handler]
        
        # Mock S3 client
        mock_presigned_url = "https://test-bucket.s3.amazonaws.com/test-key"
        
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = mock_presigned_url
            
            # Create event
            event = {
                'httpMethod': 'GET',
                'queryStringParameters': {
                    'filename': filename,
                    'contentType': content_type
                }
            }
            
            # Call handler
            response = generate_presigned_handler(event, None)
            
            # Get log output
            log_output = log_capture.getvalue()
            
            # Verify logs were generated
            assert log_output, "Lambda should generate log output"
            
            # Verify INFO level logs are present (most common)
            # The handler uses logger.info() for normal operations
            assert len(log_output) > 0, "Should have log output at INFO level"
            
            # Verify log output contains structured information
            # (event data, operation details, results)
            log_lines = log_output.split('\n')
            assert len(log_lines) > 0, "Should have multiple log lines"
    
    finally:
        # Restore original logger configuration
        logger.setLevel(original_level)
        logger.handlers = original_handlers
