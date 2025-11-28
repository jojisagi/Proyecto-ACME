"""
Property-based tests for synthetic data generation.

These tests validate that the synthetic data generation meets the requirements
for variety, structure, and completeness.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from hypothesis import given, settings, strategies as st
import pytest

# Import the generation functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from generate_synthetic_data import (
    generate_synthetic_record,
    generate_dataset,
    CARTOON_CHARACTERS
)


class TestSyntheticDataProperties:
    """Property-based tests for synthetic data generation."""
    
    @settings(max_examples=100)
    @given(st.integers(min_value=50, max_value=200))
    def test_property_14_synthetic_data_variety(self, num_records):
        """
        **Feature: aws-cartoon-rekognition, Property 14: Synthetic Data Variety**
        
        Property: For any generated synthetic dataset with 50+ records, there should be:
        - At least 10 unique character names
        - Confidence levels distributed across the 70-100 range
        - Timestamps spanning multiple days
        
        **Validates: Requirements 13.2**
        """
        # Generate dataset
        dataset = generate_dataset(num_records)
        
        # Extract data for analysis
        characters = [record["CharacterName"] for record in dataset]
        confidences = [record["Confidence"] for record in dataset]
        timestamps = [record["Timestamp"] for record in dataset]
        
        # Verify variety in character names (at least 10 unique)
        unique_characters = set(characters)
        assert len(unique_characters) >= 10, (
            f"Expected at least 10 unique characters, got {len(unique_characters)}"
        )
        
        # Verify all characters are from the known list
        assert unique_characters.issubset(set(CARTOON_CHARACTERS)), (
            "All characters should be from the predefined list"
        )
        
        # Verify confidence levels are distributed across 70-100 range
        min_confidence = min(confidences)
        max_confidence = max(confidences)
        
        assert 70.0 <= min_confidence <= 100.0, (
            f"Minimum confidence {min_confidence} should be in range [70, 100]"
        )
        assert 70.0 <= max_confidence <= 100.0, (
            f"Maximum confidence {max_confidence} should be in range [70, 100]"
        )
        
        # For sufficient data, verify good distribution (not all clustered)
        if num_records >= 50:
            confidence_range = max_confidence - min_confidence
            assert confidence_range >= 10.0, (
                f"Confidence range {confidence_range} should span at least 10 points"
            )
        
        # Verify timestamps span multiple days
        parsed_timestamps = [
            datetime.fromisoformat(ts.replace('Z', '+00:00'))
            for ts in timestamps
        ]
        
        earliest = min(parsed_timestamps)
        latest = max(parsed_timestamps)
        time_span = (latest - earliest).days
        
        # For datasets with 50+ records, expect at least 2 days span
        if num_records >= 50:
            assert time_span >= 2, (
                f"Timestamps should span at least 2 days, got {time_span} days"
            )
    
    @settings(max_examples=100)
    @given(st.integers(min_value=1, max_value=100))
    def test_property_15_synthetic_data_json_validity(self, num_records):
        """
        **Feature: aws-cartoon-rekognition, Property 15: Synthetic Data JSON Validity**
        
        Property: For any generated synthetic dataset, the data should be:
        - Valid JSON when serialized
        - Parseable back to the same structure
        - All records following the same consistent schema
        
        **Validates: Requirements 13.4**
        """
        # Generate dataset
        dataset = generate_dataset(num_records)
        
        # Verify it can be serialized to JSON
        try:
            json_string = json.dumps(dataset)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Dataset cannot be serialized to JSON: {e}")
        
        # Verify it can be parsed back
        try:
            parsed_dataset = json.loads(json_string)
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON cannot be parsed: {e}")
        
        # Verify the parsed data matches the original
        assert parsed_dataset == dataset, "Parsed data should match original"
        
        # Verify all records have consistent schema
        required_fields = {"ImageId", "CharacterName", "Confidence", "Timestamp", "Metadata"}
        required_metadata_fields = {"s3Bucket", "s3Key", "imageSize", "dimensions", "labels", "processingTime"}
        
        for i, record in enumerate(dataset):
            # Check top-level fields
            record_fields = set(record.keys())
            assert record_fields == required_fields, (
                f"Record {i} has inconsistent schema. "
                f"Expected {required_fields}, got {record_fields}"
            )
            
            # Check metadata fields
            metadata_fields = set(record["Metadata"].keys())
            assert metadata_fields == required_metadata_fields, (
                f"Record {i} metadata has inconsistent schema. "
                f"Expected {required_metadata_fields}, got {metadata_fields}"
            )
            
            # Check data types
            assert isinstance(record["ImageId"], str), f"Record {i}: ImageId should be string"
            assert isinstance(record["CharacterName"], str), f"Record {i}: CharacterName should be string"
            assert isinstance(record["Confidence"], (int, float)), f"Record {i}: Confidence should be numeric"
            assert isinstance(record["Timestamp"], str), f"Record {i}: Timestamp should be string"
            assert isinstance(record["Metadata"], dict), f"Record {i}: Metadata should be dict"
    
    @settings(max_examples=100)
    @given(st.integers(min_value=1, max_value=100))
    def test_property_16_synthetic_data_completeness(self, num_records):
        """
        **Feature: aws-cartoon-rekognition, Property 16: Synthetic Data Completeness**
        
        Property: For any record in the synthetic dataset, it should include all required
        metadata fields: imageSize, s3Key, and dimensions (with width and height).
        
        **Validates: Requirements 13.5**
        """
        # Generate dataset
        dataset = generate_dataset(num_records)
        
        for i, record in enumerate(dataset):
            metadata = record["Metadata"]
            
            # Verify imageSize is present and valid
            assert "imageSize" in metadata, f"Record {i}: Missing imageSize in metadata"
            assert isinstance(metadata["imageSize"], int), (
                f"Record {i}: imageSize should be integer"
            )
            assert metadata["imageSize"] > 0, (
                f"Record {i}: imageSize should be positive"
            )
            
            # Verify s3Key is present and valid
            assert "s3Key" in metadata, f"Record {i}: Missing s3Key in metadata"
            assert isinstance(metadata["s3Key"], str), (
                f"Record {i}: s3Key should be string"
            )
            assert len(metadata["s3Key"]) > 0, (
                f"Record {i}: s3Key should not be empty"
            )
            # Verify s3Key has a valid extension
            assert any(metadata["s3Key"].endswith(ext) for ext in [".jpg", ".jpeg", ".png"]), (
                f"Record {i}: s3Key should have valid image extension"
            )
            
            # Verify dimensions is present and valid
            assert "dimensions" in metadata, f"Record {i}: Missing dimensions in metadata"
            assert isinstance(metadata["dimensions"], dict), (
                f"Record {i}: dimensions should be dict"
            )
            
            # Verify dimensions has width and height
            dimensions = metadata["dimensions"]
            assert "width" in dimensions, f"Record {i}: Missing width in dimensions"
            assert "height" in dimensions, f"Record {i}: Missing height in dimensions"
            
            assert isinstance(dimensions["width"], int), (
                f"Record {i}: width should be integer"
            )
            assert isinstance(dimensions["height"], int), (
                f"Record {i}: height should be integer"
            )
            
            assert dimensions["width"] > 0, (
                f"Record {i}: width should be positive"
            )
            assert dimensions["height"] > 0, (
                f"Record {i}: height should be positive"
            )
            
            # Verify imageSize is reasonable given dimensions
            # Rough check: should be between 0.1 and 5 bytes per pixel
            pixels = dimensions["width"] * dimensions["height"]
            min_size = int(pixels * 0.1)
            max_size = int(pixels * 5)
            
            assert min_size <= metadata["imageSize"] <= max_size, (
                f"Record {i}: imageSize {metadata['imageSize']} seems unrealistic "
                f"for dimensions {dimensions['width']}x{dimensions['height']} "
                f"(expected between {min_size} and {max_size})"
            )


class TestGeneratedDatasetFile:
    """Tests for the actual generated dataset file."""
    
    def test_generated_file_exists(self):
        """Verify the dataset file was generated."""
        dataset_path = Path("data/dataset_metadata.json")
        assert dataset_path.exists(), "Dataset file should exist at data/dataset_metadata.json"
    
    def test_generated_file_meets_requirements(self):
        """Verify the generated file meets all requirements."""
        dataset_path = Path("data/dataset_metadata.json")
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Requirement 13.1: Minimum 50 records
        assert len(dataset) >= 50, f"Expected at least 50 records, got {len(dataset)}"
        
        # Requirement 13.2: Variety of characters
        characters = [record["CharacterName"] for record in dataset]
        unique_characters = set(characters)
        assert len(unique_characters) >= 10, (
            f"Expected at least 10 unique characters, got {len(unique_characters)}"
        )
        
        # Requirement 13.3: Confidence levels between 70-100
        confidences = [record["Confidence"] for record in dataset]
        for conf in confidences:
            assert 70.0 <= conf <= 100.0, (
                f"Confidence {conf} should be between 70 and 100"
            )
        
        # Requirement 13.4: Valid JSON format
        # (Already validated by successful json.load above)
        
        # Requirement 13.5: Complete metadata
        for i, record in enumerate(dataset):
            assert "Metadata" in record, f"Record {i}: Missing Metadata"
            metadata = record["Metadata"]
            assert "imageSize" in metadata, f"Record {i}: Missing imageSize"
            assert "s3Key" in metadata, f"Record {i}: Missing s3Key"
            assert "dimensions" in metadata, f"Record {i}: Missing dimensions"
