"""
Webhook Testing Service
Tests webhook endpoints before activation
"""
import json
import time
import ssl
import socket
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import urllib3
from urllib3.exceptions import SSLError, TimeoutError, MaxRetryError

# Import from Lambda layer
import sys
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission


class WebhookTestService:
    """Service for testing webhook endpoints"""
    
    def __init__(self):
        # Initialize HTTP client with SSL verification
        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=10.0, read=30.0),
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=None  # Use system CA bundle
        )
    
    def generate_sample_payload(self, event_type: str) -> Dict[str, Any]:
        """
        Generate sample payload for testing
        
        Requirements: 3.3.1
        """
        timestamp = datetime.utcnow().isoformat()
        event_id = f"test_{int(time.time() * 1000)}"
        
        # Base payload structure
        base_payload = {
            'event_id': event_id,
            'event_type': event_type,
            'timestamp': timestamp,
            'test_mode': True
        }
        
        # Event-specific data
        if event_type == 'claim_submitted':
            base_payload['data'] = {
                'claim_id': 'test_claim_001',
                'patient_id': 'test_patient_001',
                'amount': 1500.00,
                'status': 'submitted',
                'submitted_at': timestamp
            }
        
        elif event_type == 'claim_approved':
            base_payload['data'] = {
                'claim_id': 'test_claim_001',
                'approved_amount': 1350.00,
                'settlement_ratio': 0.90,
                'approved_at': timestamp
            }
        
        elif event_type == 'claim_rejected':
            base_payload['data'] = {
                'claim_id': 'test_claim_001',
                'rejection_reason': 'Test rejection',
                'rejected_at': timestamp
            }
        
        elif event_type == 'audit_completed':
            base_payload['data'] = {
                'audit_id': 'test_audit_001',
                'claim_id': 'test_claim_001',
                'risk_score': 45,
                'findings': ['Test finding 1', 'Test finding 2'],
                'completed_at': timestamp
            }
        
        elif event_type == 'high_risk_detected':
            base_payload['data'] = {
                'claim_id': 'test_claim_001',
                'risk_score': 85,
                'risk_factors': ['high_amount', 'complex_procedure'],
                'detected_at': timestamp
            }
        
        elif event_type == 'policy_updated':
            base_payload['data'] = {
                'policy_id': 'test_policy_001',
                'version': 2,
                'changes': ['coverage_updated', 'limits_modified'],
                'updated_at': timestamp
            }
        
        elif event_type == 'policy_expired':
            base_payload['data'] = {
                'policy_id': 'test_policy_001',
                'expiry_date': timestamp,
                'affected_claims': 5
            }
        
        elif event_type == 'settlement_completed':
            base_payload['data'] = {
                'settlement_id': 'test_settlement_001',
                'total_amount': 50000.00,
                'claims_count': 10,
                'completed_at': timestamp
            }
        
        else:
            # Generic test data
            base_payload['data'] = {
                'test_field': 'test_value',
                'message': f'Test event for {event_type}'
            }
        
        return base_payload
    
    def validate_ssl_certificate(self, url: str) -> Dict[str, Any]:
        """
        Validate SSL certificate for HTTPS URLs
        
        Requirements: 3.3.3
        """
        parsed_url = urlparse(url)
        
        if parsed_url.scheme != 'https':
            return {
                'valid': True,
                'message': 'Not HTTPS, SSL validation skipped'
            }
        
        try:
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'valid': True,
                        'message': 'SSL certificate is valid',
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'expires': cert.get('notAfter')
                    }
        
        except ssl.SSLError as e:
            return {
                'valid': False,
                'message': f'SSL certificate validation failed: {str(e)}'
            }
        
        except Exception as e:
            return {
                'valid': False,
                'message': f'SSL validation error: {str(e)}'
            }
    
    def test_webhook(
        self,
        url: str,
        event_type: str = 'test_event',
        auth_type: str = 'api_key',
        auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Test webhook endpoint with sample payload
        
        Requirements: 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.5
        """
        start_time = time.time()
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                'success': False,
                'error': 'Invalid URL format',
                'status_code': None,
                'response_time_ms': 0
            }
        
        # Validate SSL certificate
        ssl_validation = self.validate_ssl_certificate(url)
        
        # Generate sample payload
        payload = self.generate_sample_payload(event_type)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Hospital-Claim-Optimizer-Webhook/1.0',
            'X-Webhook-Test': 'true'
        }
        
        # Add authentication
        if auth_type == 'api_key' and auth_config and 'api_key' in auth_config:
            headers['Authorization'] = f"Bearer {auth_config['api_key']}"
        elif auth_type == 'oauth2' and auth_config:
            # For OAuth2, we would need to get token first
            # For testing, we'll just add a placeholder
            headers['Authorization'] = 'Bearer test_oauth_token'
        
        try:
            # Send test request
            response = self.http.request(
                'POST',
                url,
                body=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Parse response
            try:
                response_body = response.data.decode('utf-8')
            except:
                response_body = str(response.data)
            
            # Determine success
            success = 200 <= response.status < 300
            
            return {
                'success': success,
                'status_code': response.status,
                'response_time_ms': response_time_ms,
                'response_body': response_body[:1000],  # Limit to 1000 chars
                'ssl_validation': ssl_validation,
                'payload_sent': payload,
                'headers_sent': {k: v for k, v in headers.items() if k != 'Authorization'},
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except SSLError as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return {
                'success': False,
                'error': f'SSL Error: {str(e)}',
                'status_code': None,
                'response_time_ms': response_time_ms,
                'ssl_validation': ssl_validation,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except TimeoutError as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return {
                'success': False,
                'error': 'Request timeout (30 seconds)',
                'status_code': None,
                'response_time_ms': response_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except MaxRetryError as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return {
                'success': False,
                'error': f'Connection failed: {str(e.reason)}',
                'status_code': None,
                'response_time_ms': response_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'status_code': None,
                'response_time_ms': response_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            }


# Lambda handler
@require_auth()
def lambda_handler(event, context):
    """
    Lambda handler for webhook testing
    
    POST /webhooks/test
    Body: {
        "url": "https://example.com/webhook",
        "event_type": "claim_submitted",
        "auth_type": "api_key",
        "auth_config": {"api_key": "secret"}
    }
    """
    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        url = body.get('url')
        if not url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'URL is required'})
            }
        
        event_type = body.get('event_type', 'test_event')
        auth_type = body.get('auth_type', 'api_key')
        auth_config = body.get('auth_config')
        
        # Test webhook
        service = WebhookTestService()
        result = service.test_webhook(
            url=url,
            event_type=event_type,
            auth_type=auth_type,
            auth_config=auth_config
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
    
    except Exception as e:
        print(f"Error in webhook test handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
