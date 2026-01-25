"""
Enhanced Webhook Delivery Service
Handles webhook delivery with retry, logging, and circuit breaker
"""
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import urllib3
from urllib3.exceptions import TimeoutError, MaxRetryError

from database_access import DynamoDBAccessLayer
from audit_logger import AuditLogger


class CircuitBreaker:
    """Circuit breaker to prevent infinite retries to failing webhooks"""
    
    def __init__(self, failure_threshold: int = 10, timeout_seconds: int = 300):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout_seconds: Time to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failures = {}  # webhook_id -> failure_count
        self.opened_at = {}  # webhook_id -> timestamp
    
    def record_success(self, webhook_id: str):
        """Record successful delivery"""
        if webhook_id in self.failures:
            del self.failures[webhook_id]
        if webhook_id in self.opened_at:
            del self.opened_at[webhook_id]
    
    def record_failure(self, webhook_id: str):
        """Record failed delivery"""
        self.failures[webhook_id] = self.failures.get(webhook_id, 0) + 1
        
        if self.failures[webhook_id] >= self.failure_threshold:
            self.opened_at[webhook_id] = datetime.utcnow()
    
    def is_open(self, webhook_id: str) -> bool:
        """Check if circuit is open (webhook disabled)"""
        if webhook_id not in self.opened_at:
            return False
        
        # Check if timeout has passed
        opened_time = self.opened_at[webhook_id]
        if datetime.utcnow() - opened_time > timedelta(seconds=self.timeout_seconds):
            # Try to close circuit (half-open state)
            del self.opened_at[webhook_id]
            self.failures[webhook_id] = self.failure_threshold - 1
            return False
        
        return True
    
    def get_failure_count(self, webhook_id: str) -> int:
        """Get current failure count"""
        return self.failures.get(webhook_id, 0)


class WebhookDeliveryService:
    """
    Enhanced webhook delivery service with retry, logging, and circuit breaker
    
    Requirements: 3.4.1, 3.4.2, 3.4.3, 3.4.4, 3.4.5
    """
    
    def __init__(self, table_name: str):
        self.db_client = DynamoDBAccessLayer(table_name)
        self.audit_logger = AuditLogger(table_name)
        self.circuit_breaker = CircuitBreaker()
        
        # Initialize HTTP client
        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=5.0, read=30.0),
            maxsize=10
        )
    
    def log_delivery(
        self,
        webhook_id: str,
        event_type: str,
        status: str,
        status_code: Optional[int],
        response_time_ms: int,
        payload: Dict[str, Any],
        response: Optional[str] = None,
        error: Optional[str] = None,
        attempt: int = 1
    ) -> str:
        """
        Log webhook delivery attempt
        
        Requirements: 3.4.1, 3.4.2
        """
        delivery_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        delivery_log = {
            'PK': f'WEBHOOK#{webhook_id}',
            'SK': f'DELIVERY#{timestamp}#{delivery_id}',
            'delivery_id': delivery_id,
            'webhook_id': webhook_id,
            'event_type': event_type,
            'status': status,  # 'success' or 'failed'
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'payload': payload,
            'response': response[:1000] if response else None,  # Limit size
            'error': error,
            'attempt': attempt,
            'timestamp': timestamp
        }
        
        self.db_client.put_item(delivery_log)
        
        return delivery_id
    
    def get_delivery_logs(
        self,
        webhook_id: str,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get delivery logs for a webhook
        
        Requirements: 3.4.1, 3.4.4
        """
        # Query deliveries for webhook
        logs = self.db_client.query_items_by_prefix(
            pk=f'WEBHOOK#{webhook_id}',
            sk_prefix='DELIVERY#'
        )
        
        # Filter by status if specified
        if status_filter:
            logs = [log for log in logs if log.get('status') == status_filter]
        
        # Sort by timestamp (most recent first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit results
        return logs[:limit]
    
    def deliver_webhook(
        self,
        webhook_id: str,
        webhook_url: str,
        event_type: str,
        payload: Dict[str, Any],
        auth_type: str = 'api_key',
        auth_config: Optional[Dict[str, Any]] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Deliver webhook with retry logic
        
        Requirements: 3.4.2, 3.4.3
        """
        # Check circuit breaker
        if self.circuit_breaker.is_open(webhook_id):
            error_msg = f"Circuit breaker open for webhook {webhook_id} after {self.circuit_breaker.get_failure_count(webhook_id)} failures"
            
            self.log_delivery(
                webhook_id=webhook_id,
                event_type=event_type,
                status='failed',
                status_code=None,
                response_time_ms=0,
                payload=payload,
                error=error_msg,
                attempt=attempt
            )
            
            return {
                'success': False,
                'error': error_msg,
                'circuit_breaker_open': True
            }
        
        # Default retry policy
        if not retry_policy:
            retry_policy = {
                'max_attempts': 3,
                'backoff_multiplier': 2,
                'initial_delay_seconds': 1
            }
        
        start_time = time.time()
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Hospital-Claim-Optimizer-Webhook/1.0',
            'X-Event-Type': event_type,
            'X-Delivery-Attempt': str(attempt)
        }
        
        # Add authentication
        if auth_type == 'api_key' and auth_config and 'api_key' in auth_config:
            headers['Authorization'] = f"Bearer {auth_config['api_key']}"
        
        try:
            # Send webhook
            response = self.http.request(
                'POST',
                webhook_url,
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
            
            # Check if successful
            success = 200 <= response.status < 300
            
            # Log delivery
            self.log_delivery(
                webhook_id=webhook_id,
                event_type=event_type,
                status='success' if success else 'failed',
                status_code=response.status,
                response_time_ms=response_time_ms,
                payload=payload,
                response=response_body,
                attempt=attempt
            )
            
            if success:
                # Record success in circuit breaker
                self.circuit_breaker.record_success(webhook_id)
                
                return {
                    'success': True,
                    'status_code': response.status,
                    'response_time_ms': response_time_ms,
                    'response_body': response_body
                }
            else:
                # Record failure
                self.circuit_breaker.record_failure(webhook_id)
                
                # Retry if attempts remaining
                if attempt < retry_policy['max_attempts']:
                    delay = retry_policy['initial_delay_seconds'] * (retry_policy['backoff_multiplier'] ** (attempt - 1))
                    time.sleep(delay)
                    
                    return self.deliver_webhook(
                        webhook_id=webhook_id,
                        webhook_url=webhook_url,
                        event_type=event_type,
                        payload=payload,
                        auth_type=auth_type,
                        auth_config=auth_config,
                        retry_policy=retry_policy,
                        attempt=attempt + 1
                    )
                
                return {
                    'success': False,
                    'error': f'HTTP {response.status}: {response_body}',
                    'status_code': response.status,
                    'attempts': attempt
                }
        
        except (TimeoutError, MaxRetryError) as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            error_msg = f'Connection error: {str(e)}'
            
            # Log delivery
            self.log_delivery(
                webhook_id=webhook_id,
                event_type=event_type,
                status='failed',
                status_code=None,
                response_time_ms=response_time_ms,
                payload=payload,
                error=error_msg,
                attempt=attempt
            )
            
            # Record failure
            self.circuit_breaker.record_failure(webhook_id)
            
            # Retry if attempts remaining
            if attempt < retry_policy['max_attempts']:
                delay = retry_policy['initial_delay_seconds'] * (retry_policy['backoff_multiplier'] ** (attempt - 1))
                time.sleep(delay)
                
                return self.deliver_webhook(
                    webhook_id=webhook_id,
                    webhook_url=webhook_url,
                    event_type=event_type,
                    payload=payload,
                    auth_type=auth_type,
                    auth_config=auth_config,
                    retry_policy=retry_policy,
                    attempt=attempt + 1
                )
            
            return {
                'success': False,
                'error': error_msg,
                'attempts': attempt
            }
        
        except Exception as e:
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            error_msg = f'Unexpected error: {str(e)}'
            
            # Log delivery
            self.log_delivery(
                webhook_id=webhook_id,
                event_type=event_type,
                status='failed',
                status_code=None,
                response_time_ms=response_time_ms,
                payload=payload,
                error=error_msg,
                attempt=attempt
            )
            
            # Record failure
            self.circuit_breaker.record_failure(webhook_id)
            
            return {
                'success': False,
                'error': error_msg,
                'attempts': attempt
            }
    
    def retry_failed_delivery(
        self,
        webhook_id: str,
        delivery_id: str
    ) -> Dict[str, Any]:
        """
        Manually retry a failed delivery
        
        Requirements: 3.4.3
        """
        # Get original delivery log
        logs = self.get_delivery_logs(webhook_id, limit=1000)
        delivery_log = next((log for log in logs if log.get('delivery_id') == delivery_id), None)
        
        if not delivery_log:
            return {
                'success': False,
                'error': 'Delivery log not found'
            }
        
        # Get webhook config
        webhook = self.db_client.get_item(
            pk=f'WEBHOOK#{webhook_id}',
            sk='CONFIG'
        )
        
        if not webhook:
            return {
                'success': False,
                'error': 'Webhook not found'
            }
        
        # Retry delivery
        return self.deliver_webhook(
            webhook_id=webhook_id,
            webhook_url=webhook['url'],
            event_type=delivery_log['event_type'],
            payload=delivery_log['payload'],
            auth_type=webhook.get('auth_type', 'api_key'),
            auth_config=webhook.get('auth_config'),
            retry_policy=webhook.get('retry_policy'),
            attempt=1  # Start fresh attempt count
        )
    
    def get_webhook_statistics(self, webhook_id: str) -> Dict[str, Any]:
        """Get delivery statistics for a webhook"""
        logs = self.get_delivery_logs(webhook_id, limit=1000)
        
        total_deliveries = len(logs)
        successful_deliveries = len([log for log in logs if log.get('status') == 'success'])
        failed_deliveries = total_deliveries - successful_deliveries
        
        # Calculate average response time
        response_times = [log.get('response_time_ms', 0) for log in logs if log.get('status') == 'success']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Get recent deliveries (last 24 hours)
        now = datetime.utcnow()
        recent_logs = [
            log for log in logs
            if (now - datetime.fromisoformat(log.get('timestamp', now.isoformat()))).total_seconds() < 86400
        ]
        
        return {
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'success_rate': successful_deliveries / total_deliveries if total_deliveries > 0 else 0,
            'avg_response_time_ms': int(avg_response_time),
            'recent_deliveries_24h': len(recent_logs),
            'circuit_breaker_open': self.circuit_breaker.is_open(webhook_id),
            'consecutive_failures': self.circuit_breaker.get_failure_count(webhook_id)
        }
