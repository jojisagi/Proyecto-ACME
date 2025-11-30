#!/usr/bin/env python3
"""
Script to generate synthetic cartoon character recognition data.
This creates test data for the AWS Cartoon Rekognition system.
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path


# List of cartoon characters for variety
CARTOON_CHARACTERS = [
    "Mickey Mouse",
    "Bugs Bunny",
    "SpongeBob SquarePants",
    "Homer Simpson",
    "Scooby-Doo",
    "Tom Cat",
    "Jerry Mouse",
    "Donald Duck",
    "Pikachu",
    "Bart Simpson",
    "Patrick Star",
    "Squidward Tentacles",
    "Tweety Bird",
    "Sylvester Cat",
    "Daffy Duck",
    "Porky Pig",
    "Road Runner",
    "Wile E. Coyote",
    "Fred Flintstone",
    "Yogi Bear",
]


def generate_timestamp(days_back_range=(0, 30)):
    """
    Generate a random timestamp within the specified range of days back.
    
    Args:
        days_back_range: Tuple of (min_days, max_days) to go back from now
        
    Returns:
        ISO 8601 formatted timestamp string
    """
    days_back = random.randint(days_back_range[0], days_back_range[1])
    hours_back = random.randint(0, 23)
    minutes_back = random.randint(0, 59)
    seconds_back = random.randint(0, 59)
    
    timestamp = datetime.now() - timedelta(
        days=days_back,
        hours=hours_back,
        minutes=minutes_back,
        seconds=seconds_back
    )
    
    return timestamp.isoformat() + "Z"


def generate_image_dimensions():
    """
    Generate random but realistic image dimensions.
    
    Returns:
        Dict with width and height
    """
    # Common image sizes for cartoon images
    common_sizes = [
        (800, 600),
        (1024, 768),
        (1280, 720),
        (1920, 1080),
        (640, 480),
        (1600, 900),
    ]
    
    width, height = random.choice(common_sizes)
    return {"width": width, "height": height}


def generate_image_size(dimensions):
    """
    Generate realistic file size based on dimensions.
    
    Args:
        dimensions: Dict with width and height
        
    Returns:
        File size in bytes
    """
    # Rough estimate: ~3 bytes per pixel for JPEG
    pixels = dimensions["width"] * dimensions["height"]
    base_size = pixels * 3
    
    # Add some randomness (compression varies)
    variation = random.uniform(0.3, 0.7)
    return int(base_size * variation)


def generate_synthetic_record():
    """
    Generate a single synthetic cartoon analysis record.
    
    Returns:
        Dict containing all required fields for a cartoon analysis result
    """
    image_id = str(uuid.uuid4())
    character_name = random.choice(CARTOON_CHARACTERS)
    confidence = round(random.uniform(70.0, 100.0), 2)
    timestamp = generate_timestamp()
    dimensions = generate_image_dimensions()
    image_size = generate_image_size(dimensions)
    
    # Generate S3 key based on image_id
    file_extension = random.choice(["jpg", "jpeg", "png"])
    s3_key = f"{image_id}.{file_extension}"
    
    record = {
        "ImageId": image_id,
        "CharacterName": character_name,
        "Confidence": confidence,
        "Timestamp": timestamp,
        "Metadata": {
            "s3Bucket": "cartoon-rekognition-images-sandbox",
            "s3Key": s3_key,
            "imageSize": image_size,
            "dimensions": dimensions,
            "labels": [
                {
                    "name": character_name,
                    "confidence": confidence
                },
                {
                    "name": "Cartoon",
                    "confidence": round(random.uniform(90.0, 99.9), 2)
                },
                {
                    "name": "Animation",
                    "confidence": round(random.uniform(85.0, 98.0), 2)
                }
            ],
            "processingTime": random.randint(100, 2000)
        }
    }
    
    return record


def generate_dataset(num_records=50):
    """
    Generate a complete synthetic dataset.
    
    Args:
        num_records: Number of records to generate (default: 50)
        
    Returns:
        List of synthetic records
    """
    dataset = []
    
    for _ in range(num_records):
        record = generate_synthetic_record()
        dataset.append(record)
    
    return dataset


def save_dataset(dataset, output_path="data/dataset_metadata.json"):
    """
    Save the dataset to a JSON file.
    
    Args:
        dataset: List of records to save
        output_path: Path where to save the JSON file
    """
    # Ensure the directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the dataset with pretty formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(dataset)} synthetic records")
    print(f"Saved to: {output_path}")


def main():
    """Main function to generate and save synthetic data."""
    # Generate 50+ records as required
    num_records = random.randint(50, 75)
    dataset = generate_dataset(num_records)
    
    # Save to the specified location
    save_dataset(dataset)
    
    # Print some statistics
    characters = [record["CharacterName"] for record in dataset]
    unique_characters = set(characters)
    
    print(f"\nDataset Statistics:")
    print(f"  Total records: {len(dataset)}")
    print(f"  Unique characters: {len(unique_characters)}")
    print(f"  Characters: {', '.join(sorted(unique_characters))}")
    
    confidences = [record["Confidence"] for record in dataset]
    print(f"  Confidence range: {min(confidences):.2f} - {max(confidences):.2f}")
    
    timestamps = [record["Timestamp"] for record in dataset]
    print(f"  Timestamp range: {min(timestamps)} to {max(timestamps)}")


if __name__ == "__main__":
    main()
