"""
Property-based tests for S3EventProcessor Lambda function.

Feature: aws-cartoon-rekognition
"""

import json
import os
from unittest.mock import patch, MagicMock
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

# Import the handler
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.s3_event_processor.handler import (
    lambda_handler,
    process_record,
    extract_image_id,
    extract_character_from_labels,
    analyze_image_with_rekognition,
    save_to_dynamodb
)


# Strategies for generating test data
valid_bucket_names = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'),
    min_size=3,
    max_size=63
).filter(lambda x: not x.startswith('-') and not x.endswith('-'))

valid_image_keys = st.builds(
    lambda uuid, ext: f"{uuid}.{ext}",
    uuid=st.uuids().map(str),
    ext=st.sampled_from(['jpg', 'jpeg', 'png'])
)

valid_labels = st.lists(
    st.builds(
        lambda name, conf: {'Name': name, 'Confidence': conf},
        name=st.text(min_size=1, max_size=50),
        conf=st.floats(min_value=70.0, max_value=100.0)
    ),
    min_size=1,
    max_size=10
)


@given(bucket=valid_bucket_names, key=valid_image_keys)
@settings(max_examples=100)
def test_property_rekognition_invocation_on_image_processing(bucket, key):
    """
    Property 3: Rekognition Invocation on Image Processing
    
    For any image uploaded to the S3 bucket, the S3EventProcessor Lambda should
    call Amazon Rekognition's DetectLabels API with the correct image reference.
    
    Feature: aws-cartoon-rekognition, Property 3: Rekognition Invocation on Image Processing
    Validates: Requirements 2.2
    """
    # Mock AWS clients
    with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
         patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
         patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
        
        mock_rekognition = MagicMock()
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        
        mock_get_rek.return_value = mock_rekognition
        mock_get_s3.return_value = mock_s3
        mock_get_ddb.return_value = mock_dynamodb
        
        # Setup mocks
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Cartoon', 'Confidence': 95.5},
                {'Name': 'Character', 'Confidence': 90.0}
            ]
        }
        
        mock_s3.head_object.return_value = {
            'ContentLength': 1024000,
            'ContentType': 'image/jpeg'
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
        
        # Call the handler
        lambda_handler(event, None)
        
        # Verify Rekognition was called
        mock_rekognition.detect_labels.assert_called_once()
        
        # Verify the call parameters
        call_args = mock_rekognition.detect_labels.call_args
        assert 'Image' in call_args[1], "Should include Image parameter"
        assert 'S3Object' in call_args[1]['Image'], "Should use S3Object"
        
        s3_object = call_args[1]['Image']['S3Object']
        assert s3_object['Bucket'] == bucket, f"Should call Rekognition with correct bucket: {bucket}"
        assert s3_object['Name'] == key, f"Should call Rekognition with correct key: {key}"
        
        # Verify MaxLabels and MinConfidence are set
        assert call_args[1]['MaxLabels'] == 10, "Should request max 10 labels"
        assert call_args[1]['MinConfidence'] == 70.0, "Should set min confidence to 70.0"


@given(labels=valid_labels)
@settings(max_examples=100)
def test_property_character_extraction_from_rekognition_results(labels):
    """
    Property 4: Character Extraction from Rekognition Results
    
    For any valid Rekognition response containing labels, the Lambda should extract
    at least one character name and confidence score from the results.
    
    Feature: aws-cartoon-rekognition, Property 4: Character Extraction from Rekognition Results
    Validates: Requirements 2.3
    """
    # Call the extraction function
    character_name, confidence = extract_character_from_labels(labels)
    
    # Verify that a character name was extracted
    assert character_name is not None, "Should extract a character name"
    assert isinstance(character_name, str), "Character name should be a string"
    assert len(character_name) > 0, "Character name should not be empty"
    
    # Verify that confidence was extracted
    assert confidence is not None, "Should extract confidence"
    assert isinstance(confidence, (int, float)), "Confidence should be numeric"
    assert 0.0 <= confidence <= 100.0, f"Confidence should be between 0 and 100, got {confidence}"
    
    # Verify the confidence matches one of the labels
    label_confidences = [label['Confidence'] for label in labels]
    assert confidence in label_confidences, "Extracted confidence should match one of the input labels"


def test_property_character_extraction_empty_labels():
    """
    Property 4: Character Extraction from Rekognition Results (Edge Case)
    
    When Rekognition returns no labels, the system should handle it gracefully
    by returning "Unknown" with 0.0 confidence.
    
    Feature: aws-cartoon-rekognition, Property 4: Character Extraction from Rekognition Results
    Validates: Requirements 2.3
    """
    # Call with empty labels
    character_name, confidence = extract_character_from_labels([])
    
    # Verify graceful handling
    assert character_name == "Unknown", "Should return 'Unknown' for empty labels"
    assert confidence == 0.0, "Should return 0.0 confidence for empty labels"


@given(
    bucket=valid_bucket_names,
    key=valid_image_keys,
    labels=valid_labels
)
@settings(max_examples=100)
def test_property_complete_dynamodb_record_structure(bucket, key, labels):
    """
    Property 5: Complete DynamoDB Record Structure
    
    For any completed analysis, the record saved to DynamoDB should contain all
    required attributes (ImageId, CharacterName, Confidence, Timestamp in ISO 8601
    format, Metadata) with valid data types and values.
    
    Feature: aws-cartoon-rekognition, Property 5: Complete DynamoDB Record Structure
    Validates: Requirements 3.2, 3.5
    """
    # Mock AWS clients
    with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
         patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
         patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
        
        mock_rekognition = MagicMock()
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        
        mock_get_rek.return_value = mock_rekognition
        mock_get_s3.return_value = mock_s3
        mock_get_ddb.return_value = mock_dynamodb
        
        # Setup mocks
        mock_rekognition.detect_labels.return_value = {'Labels': labels}
        
        mock_s3.head_object.return_value = {
            'ContentLength': 1024000,
            'ContentType': 'image/jpeg'
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
        
        # Call the handler
        lambda_handler(event, None)
        
        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        
        # Extract the saved record
        call_args = mock_table.put_item.call_args
        saved_record = call_args[1]['Item']
        
        # Verify all required attributes are present
        assert 'ImageId' in saved_record, "Record should contain ImageId"
        assert 'CharacterName' in saved_record, "Record should contain CharacterName"
        assert 'Confidence' in saved_record, "Record should contain Confidence"
        assert 'Timestamp' in saved_record, "Record should contain Timestamp"
        assert 'Metadata' in saved_record, "Record should contain Metadata"
        
        # Verify ImageId format (should be UUID from key)
        image_id = saved_record['ImageId']
        assert isinstance(image_id, str), "ImageId should be a string"
        assert len(image_id) > 0, "ImageId should not be empty"
        
        # Verify CharacterName
        character_name = saved_record['CharacterName']
        assert isinstance(character_name, str), "CharacterName should be a string"
        assert len(character_name) > 0, "CharacterName should not be empty"
        
        # Verify Confidence
        confidence = saved_record['Confidence']
        assert isinstance(confidence, (int, float, Decimal)), "Confidence should be numeric"
        assert 0.0 <= float(confidence) <= 100.0, "Confidence should be between 0 and 100"
        
        # Verify Timestamp is in ISO 8601 format
        timestamp = saved_record['Timestamp']
        assert isinstance(timestamp, str), "Timestamp should be a string"
        assert 'T' in timestamp, "Timestamp should be in ISO 8601 format (contains 'T')"
        assert timestamp.endswith('Z'), "Timestamp should end with 'Z' (UTC)"
        
        # Verify Metadata structure
        metadata = saved_record['Metadata']
        assert isinstance(metadata, dict), "Metadata should be a dictionary"
        assert 's3Bucket' in metadata, "Metadata should contain s3Bucket"
        assert 's3Key' in metadata, "Metadata should contain s3Key"
        assert 'imageSize' in metadata, "Metadata should contain imageSize"
        assert 'labels' in metadata, "Metadata should contain labels"
        
        # Verify Metadata values
        assert metadata['s3Bucket'] == bucket, "Metadata s3Bucket should match input bucket"
        assert metadata['s3Key'] == key, "Metadata s3Key should match input key"
        assert isinstance(metadata['imageSize'], (int, Decimal)), "imageSize should be numeric"
        assert isinstance(metadata['labels'], list), "labels should be a list"
        
        # Verify labels in metadata
        for label in metadata['labels']:
            assert 'name' in label, "Each label should have a name"
            assert 'confidence' in label, "Each label should have a confidence"
            assert isinstance(label['name'], str), "Label name should be a string"
            assert isinstance(label['confidence'], (int, float, Decimal)), "Label confidence should be numeric"


@given(key=valid_image_keys)
@settings(max_examples=100)
def test_property_image_id_extraction(key):
    """
    Property: Image ID extraction should correctly extract UUID from S3 key.
    
    For any valid S3 object key, the extract_image_id function should return
    the UUID portion without the file extension.
    """
    # Extract image ID
    image_id = extract_image_id(key)
    
    # Verify it's a valid UUID format (without extension)
    assert isinstance(image_id, str), "Image ID should be a string"
    assert '.' not in image_id, "Image ID should not contain file extension"
    assert len(image_id) == 36, "Image ID should be UUID format (36 chars)"
    assert image_id.count('-') == 4, "UUID should have 4 hyphens"


@given(bucket=valid_bucket_names, key=valid_image_keys)
@settings(max_examples=100)
def test_property_s3_event_triggers_lambda_invocation(bucket, key):
    """
    Property 2: S3 Event Triggers Lambda Invocation
    
    For any image uploaded to the S3 bucket, the S3EventProcessor Lambda should be
    automatically invoked with the correct bucket and key information.
    
    Feature: aws-cartoon-rekognition, Property 2: S3 Event Triggers Lambda Invocation
    Validates: Requirements 2.1
    """
    # Mock AWS clients
    with patch('lambdas.s3_event_processor.handler._get_rekognition_client') as mock_get_rek, \
         patch('lambdas.s3_event_processor.handler._get_s3_client') as mock_get_s3, \
         patch('lambdas.s3_event_processor.handler._get_dynamodb_resource') as mock_get_ddb:
        
        mock_rekognition = MagicMock()
        mock_s3 = MagicMock()
        mock_dynamodb = MagicMock()
        
        mock_get_rek.return_value = mock_rekognition
        mock_get_s3.return_value = mock_s3
        mock_get_ddb.return_value = mock_dynamodb
        
        # Setup mocks
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Cartoon', 'Confidence': 95.5}
            ]
        }
        
        mock_s3.head_object.return_value = {
            'ContentLength': 1024000,
            'ContentType': 'image/jpeg'
        }
        
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        
        # Create S3 event that simulates what S3 sends to Lambda
        # This is the event structure that S3 Event Notifications generate
        event = {
            'Records': [{
                'eventVersion': '2.1',
                'eventSource': 'aws:s3',
                'eventName': 's3:ObjectCreated:Put',
                's3': {
                    'bucket': {
                        'name': bucket,
                        'arn': f'arn:aws:s3:::{bucket}'
                    },
                    'object': {
                        'key': key,
                        'size': 1024000
                    }
                }
            }]
        }
        
        # Invoke the Lambda handler (simulating S3 triggering the Lambda)
        lambda_handler(event, None)
        
        # Verify that the Lambda was invoked and processed the event correctly
        # by checking that it called the expected AWS services with correct parameters
        
        # 1. Verify S3 head_object was called to get metadata
        mock_s3.head_object.assert_called_once_with(
            Bucket=bucket,
            Key=key
        )
        
        # 2. Verify Rekognition was called with correct bucket and key
        mock_rekognition.detect_labels.assert_called_once()
        call_args = mock_rekognition.detect_labels.call_args
        assert call_args[1]['Image']['S3Object']['Bucket'] == bucket, \
            f"Lambda should process event with correct bucket: {bucket}"
        assert call_args[1]['Image']['S3Object']['Name'] == key, \
            f"Lambda should process event with correct key: {key}"
        
        # 3. Verify DynamoDB was called to save results
        mock_table.put_item.assert_called_once()
        
        # 4. Verify the saved record contains the correct S3 information
        saved_record = mock_table.put_item.call_args[1]['Item']
        assert saved_record['Metadata']['s3Bucket'] == bucket, \
            "Saved record should contain correct bucket name"
        assert saved_record['Metadata']['s3Key'] == key, \
            "Saved record should contain correct object key"
        
        # This test validates that when S3 sends an event notification to Lambda,
        # the Lambda correctly extracts the bucket and key information and processes
        # the image, which is the core requirement of automatic invocation on upload
