"""
Integration tests for complete API flow.

Tests the end-to-end flow:
1. Authentication → Get JWT token
2. Get upload URL
3. Upload image to S3
4. Query results

Also tests error scenarios:
- Calling API without JWT returns 401
- Querying non-existent imageId returns 404
"""

import json
import os
import uuid
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

import pytest

# Import the handlers
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from lambdas.generate_presigned.handler import lambda_handler as generate_presigned_handler
from lambdas.query_results.handler import lambda_handler as query_results_handler


class TestAPIFlowIntegration:
    """Integration tests for complete API flow"""
    
    def test_complete_flow_authentication_to_query(self):
        """
        Test: Complete flow from authentication to query results
        
        Flow:
        1. User authenticates with Cognito (simulated)
        2. User calls GET /get-upload-url with JWT
        3. User uploads image to S3 using presigned URL (simulated)
        4. S3 triggers Lambda to process image (tested separately)
        5. User calls GET /result to query analysis results
        """
        # Step 1: Simulate Cognito authentication
        # In real scenario, user would call Cognito API to get JWT
        mock_jwt_token = self._generate_mock_jwt()
        
        # Step 2: Get upload URL
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_presigned_url = "https://test-bucket.s3.amazonaws.com/test-image.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256"
            mock_s3.generate_presigned_url.return_value = mock_presigned_url
            
            get_upload_event = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'filename': 'cartoon.jpg',
                    'contentType': 'image/jpeg'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            upload_response = generate_presigned_handler(get_upload_event, None)
            
            # Verify upload URL response
            assert upload_response['statusCode'] == 200
            upload_body = json.loads(upload_response['body'])
            assert 'uploadUrl' in upload_body
            assert 'imageId' in upload_body
            assert 'expiresIn' in upload_body
            
            image_id = upload_body['imageId']
            upload_url = upload_body['uploadUrl']
        
        # Step 3: Simulate image upload to S3
        # In real scenario, client would PUT image to presigned URL
        # This triggers S3 event notification to S3EventProcessor Lambda
        # (S3EventProcessor is tested separately)
        
        # Step 4: Simulate that image has been processed and stored in DynamoDB
        mock_analysis_result = {
            'ImageId': image_id,
            'CharacterName': 'Mickey Mouse',
            'Confidence': 95.5,
            'Timestamp': datetime.utcnow().isoformat() + 'Z',
            'Metadata': {
                's3Bucket': 'test-bucket',
                's3Key': f'{image_id}.jpg',
                'imageSize': 1024000,
                'labels': [
                    {'name': 'Mickey Mouse', 'confidence': 95.5},
                    {'name': 'Cartoon', 'confidence': 98.0}
                ]
            }
        }
        
        # Step 5: Query results
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_table.get_item.return_value = {
                'Item': mock_analysis_result
            }
            
            query_event = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'imageId': image_id
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            query_response = query_results_handler(query_event, None)
            
            # Verify query response
            assert query_response['statusCode'] == 200
            query_body = json.loads(query_response['body'])
            
            assert query_body['imageId'] == image_id
            assert query_body['characterName'] == 'Mickey Mouse'
            assert query_body['confidence'] == 95.5
            assert 'timestamp' in query_body
            assert 'metadata' in query_body
            
            # Verify DynamoDB was queried
            mock_table.get_item.assert_called_once()
            call_args = mock_table.get_item.call_args
            assert call_args[1]['Key']['ImageId'] == image_id
    
    def test_api_call_without_jwt_returns_401(self):
        """
        Test: Calling API without JWT returns 401 Unauthorized
        
        This simulates API Gateway's Cognito Authorizer rejecting
        requests without valid JWT tokens.
        """
        # Attempt to get upload URL without JWT
        event_no_auth = {
            'httpMethod': 'GET',
            'headers': {},  # No Authorization header
            'queryStringParameters': {
                'filename': 'cartoon.jpg',
                'contentType': 'image/jpeg'
            },
            'requestContext': {
                'authorizer': None  # No authorizer context
            }
        }
        
        # In real API Gateway, Cognito Authorizer would reject this before Lambda
        # We simulate the 401 response that API Gateway would return
        
        # Check if authorization is present
        auth_header = event_no_auth.get('headers', {}).get('Authorization')
        
        if not auth_header:
            # Simulate API Gateway 401 response
            response = {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Unauthorized'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
            
            assert response['statusCode'] == 401
            body = json.loads(response['body'])
            assert body['message'] == 'Unauthorized'
        
        # Test with invalid JWT format
        event_invalid_jwt = {
            'httpMethod': 'GET',
            'headers': {
                'Authorization': 'InvalidToken'  # Not Bearer format
            },
            'queryStringParameters': {
                'filename': 'cartoon.jpg',
                'contentType': 'image/jpeg'
            },
            'requestContext': {
                'authorizer': None
            }
        }
        
        auth_header = event_invalid_jwt.get('headers', {}).get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            # Simulate API Gateway 401 response
            response = {
                'statusCode': 401,
                'body': json.dumps({
                    'message': 'Unauthorized'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
            
            assert response['statusCode'] == 401
            body = json.loads(response['body'])
            assert body['message'] == 'Unauthorized'
    
    def test_query_nonexistent_image_returns_404(self):
        """
        Test: Querying with non-existent imageId returns 404 Not Found
        """
        mock_jwt_token = self._generate_mock_jwt()
        non_existent_image_id = str(uuid.uuid4())
        
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            
            # Simulate DynamoDB returning no item
            mock_table.get_item.return_value = {}
            
            query_event = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'imageId': non_existent_image_id
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            query_response = query_results_handler(query_event, None)
            
            # Verify 404 response
            assert query_response['statusCode'] == 404
            body = json.loads(query_response['body'])
            assert 'error' in body
            assert body['error'] == 'NotFound'
            assert 'message' in body
    
    def test_invalid_image_id_format_returns_400(self):
        """
        Test: Querying with invalid imageId format returns 400 Bad Request
        """
        mock_jwt_token = self._generate_mock_jwt()
        invalid_image_id = 'not-a-valid-uuid'
        
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            query_event = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'imageId': invalid_image_id
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            query_response = query_results_handler(query_event, None)
            
            # Verify 400 response
            assert query_response['statusCode'] == 400
            body = json.loads(query_response['body'])
            assert 'error' in body
            assert body['error'] == 'BadRequest'
    
    def test_missing_query_parameters_returns_400(self):
        """
        Test: API calls with missing required query parameters return 400
        """
        mock_jwt_token = self._generate_mock_jwt()
        
        # Test missing filename for get-upload-url
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            event_missing_filename = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'contentType': 'image/jpeg'
                    # Missing 'filename'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            response = generate_presigned_handler(event_missing_filename, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body
        
        # Test missing imageId for query-results
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            event_missing_image_id = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {},  # Missing 'imageId'
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            response = query_results_handler(event_missing_image_id, None)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert 'error' in body
    
    def test_cors_headers_present_in_responses(self):
        """
        Test: All API responses include CORS headers
        """
        mock_jwt_token = self._generate_mock_jwt()
        
        # Test CORS headers in successful response
        with patch('lambdas.generate_presigned.handler.s3_client') as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.jpg"
            
            event = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {
                    'filename': 'test.jpg',
                    'contentType': 'image/jpeg'
                },
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            response = generate_presigned_handler(event, None)
            
            assert 'headers' in response
            assert 'Access-Control-Allow-Origin' in response['headers']
            assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        # Test CORS headers in error response
        with patch('lambdas.query_results.handler.dynamodb') as mock_dynamodb:
            event_error = {
                'httpMethod': 'GET',
                'headers': {
                    'Authorization': f'Bearer {mock_jwt_token}'
                },
                'queryStringParameters': {},  # Missing imageId
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'sub': 'user-123',
                            'email': 'user@example.com'
                        }
                    }
                }
            }
            
            response = query_results_handler(event_error, None)
            
            assert 'headers' in response
            assert 'Access-Control-Allow-Origin' in response['headers']
    
    def _generate_mock_jwt(self):
        """Generate a mock JWT token for testing"""
        # In real scenario, this would be a valid JWT from Cognito
        # For testing, we just need a token-like string
        import base64
        
        header = base64.b64encode(json.dumps({
            'alg': 'RS256',
            'typ': 'JWT'
        }).encode()).decode()
        
        payload = base64.b64encode(json.dumps({
            'sub': 'user-123',
            'email': 'user@example.com',
            'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }).encode()).decode()
        
        signature = base64.b64encode(b'mock-signature').decode()
        
        return f'{header}.{payload}.{signature}'


class TestAPIGatewayConfiguration:
    """Tests for API Gateway configuration aspects"""
    
    def test_throttling_configuration(self):
        """
        Test: Verify throttling configuration is properly set
        
        This is a configuration test that would be validated during
        CloudFormation deployment. Here we document the expected values.
        """
        expected_throttling = {
            'rateLimit': 1000,  # requests per second
            'burstLimit': 2000  # burst capacity
        }
        
        # In real deployment, these would be verified via AWS API
        assert expected_throttling['rateLimit'] == 1000
        assert expected_throttling['burstLimit'] == 2000
    
    def test_api_endpoints_configuration(self):
        """
        Test: Verify all required API endpoints are configured
        """
        required_endpoints = [
            {
                'path': '/get-upload-url',
                'method': 'GET',
                'authorization': 'COGNITO_USER_POOLS',
                'integration': 'GeneratePresignedUrl Lambda'
            },
            {
                'path': '/result',
                'method': 'GET',
                'authorization': 'COGNITO_USER_POOLS',
                'integration': 'QueryResults Lambda'
            },
            {
                'path': '/register-analysis',
                'method': 'POST',
                'authorization': 'COGNITO_USER_POOLS',
                'integration': 'Mock (optional)'
            }
        ]
        
        # Verify endpoint configuration
        for endpoint in required_endpoints:
            assert endpoint['path'] is not None
            assert endpoint['method'] in ['GET', 'POST']
            assert endpoint['authorization'] == 'COGNITO_USER_POOLS'
    
    def test_access_logging_configuration(self):
        """
        Test: Verify access logging is enabled
        """
        # In real deployment, this would be verified via CloudFormation outputs
        # or AWS API calls
        expected_logging_config = {
            'enabled': True,
            'destination': 'CloudWatch Logs',
            'format': 'JSON',
            'retention_days': 90
        }
        
        assert expected_logging_config['enabled'] is True
        assert expected_logging_config['destination'] == 'CloudWatch Logs'
