"""
Webhook Configuration Lambda
Handles CRUD operations for webhook configurations
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

# Import from Lambda layer
import sys
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission
from database_access import DynamoDBAccessLayer
from audit_logger import AuditLogger

# Initialize services
dynamodb = boto3.resource('dynamodb')
kms = boto3.client('kms')
table_name = os.environ.get('DYNAMODB_TABLE', 'hospital-claim-optimizer')
db_client = DynamoDBAccessLayer(table_name)
audit_logger = AuditLogger(table_name)


class WebhookConfigService:
    """Service for managing webhook configurations"""
    
    def __init__(self):
        self.db_client = db_client
        self.audit_logger = audit_logger
        self.kms_key_id = os.environ.get('KMS_KEY_ID')
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt sensitive data using KMS"""
        if not self.kms_key_id:
            # For testing, return base64 encoded
            import base64
            return base64.b64encode(secret.encode()).decode()
        
        try:
            response = kms.encrypt(
                KeyId=self.kms_key_id,
                Plaintext=secret.encode()
            )
            import base64
            return base64.b64encode(response['CiphertextBlob']).decode()
        except Exception as e:
            print(f"Error encrypting secret: {str(e)}")
            raise
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt sensitive data using KMS"""
        if not self.kms_key_id:
            # For testing, return base64 decoded
            import base64
            return base64.b64decode(encrypted_secret.encode()).decode()
        
        try:
            import base64
            response = kms.decrypt(
                CiphertextBlob=base64.b64decode(encrypted_secret)
            )
            return response['Plaintext'].decode()
        except Exception as e:
            print(f"Error decrypting secret: {str(e)}")
            raise
    
    def create_webhook(
        self,
        user_id: str,
        name: str,
        url: str,
        events: List[str],
        auth_type: str = 'api_key',
        auth_config: Optional[Dict[str, Any]] = None,
        description: str = '',
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new webhook configuration
        
        Requirements: 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5
        """
        webhook_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Encrypt sensitive auth data
        encrypted_auth_config = {}
        if auth_config:
            if auth_type == 'api_key' and 'api_key' in auth_config:
                encrypted_auth_config['api_key'] = self.encrypt_secret(auth_config['api_key'])
            elif auth_type == 'oauth2':
                if 'client_secret' in auth_config:
                    encrypted_auth_config['client_secret'] = self.encrypt_secret(auth_config['client_secret'])
                encrypted_auth_config['client_id'] = auth_config.get('client_id', '')
                encrypted_auth_config['token_url'] = auth_config.get('token_url', '')
        
        webhook_config = {
            'PK': f'WEBHOOK#{webhook_id}',
            'SK': 'CONFIG',
            'webhook_id': webhook_id,
            'user_id': user_id,
            'name': name,
            'url': url,
            'description': description,
            'enabled': enabled,
            'events': events,
            'auth_type': auth_type,
            'auth_config': encrypted_auth_config,
            'retry_policy': {
                'max_attempts': 3,
                'backoff_multiplier': 2,
                'initial_delay_seconds': 1
            },
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id
        }
        
        # Save to DynamoDB
        self.db_client.put_item(webhook_config)
        
        # Audit log
        self.audit_logger.log_action(
            user_id=user_id,
            action='webhook_created',
            resource_type='webhook',
            resource_id=webhook_id,
            details={'name': name, 'url': url, 'events': events}
        )
        
        # Return without sensitive data
        return self._sanitize_webhook_config(webhook_config)
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook configuration by ID"""
        webhook = self.db_client.get_item(
            pk=f'WEBHOOK#{webhook_id}',
            sk='CONFIG'
        )
        
        if webhook:
            return self._sanitize_webhook_config(webhook)
        return None
    
    def list_webhooks(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all webhook configurations"""
        # Query all webhooks
        webhooks = self.db_client.query_items_by_prefix(
            pk_prefix='WEBHOOK#',
            sk='CONFIG'
        )
        
        # Filter by user if specified
        if user_id:
            webhooks = [w for w in webhooks if w.get('user_id') == user_id]
        
        # Sanitize sensitive data
        return [self._sanitize_webhook_config(w) for w in webhooks]
    
    def update_webhook(
        self,
        webhook_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update webhook configuration
        
        Requirements: 3.2.5
        """
        # Get existing webhook
        webhook = self.db_client.get_item(
            pk=f'WEBHOOK#{webhook_id}',
            sk='CONFIG'
        )
        
        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")
        
        # Update fields
        allowed_updates = ['name', 'url', 'description', 'enabled', 'events', 'auth_type', 'auth_config']
        
        for key, value in updates.items():
            if key in allowed_updates:
                if key == 'auth_config' and value:
                    # Encrypt sensitive auth data
                    auth_type = updates.get('auth_type', webhook.get('auth_type'))
                    encrypted_auth_config = {}
                    
                    if auth_type == 'api_key' and 'api_key' in value:
                        encrypted_auth_config['api_key'] = self.encrypt_secret(value['api_key'])
                    elif auth_type == 'oauth2':
                        if 'client_secret' in value:
                            encrypted_auth_config['client_secret'] = self.encrypt_secret(value['client_secret'])
                        encrypted_auth_config['client_id'] = value.get('client_id', '')
                        encrypted_auth_config['token_url'] = value.get('token_url', '')
                    
                    webhook['auth_config'] = encrypted_auth_config
                else:
                    webhook[key] = value
        
        webhook['updated_at'] = datetime.utcnow().isoformat()
        
        # Save to DynamoDB
        self.db_client.put_item(webhook)
        
        # Audit log
        self.audit_logger.log_action(
            user_id=user_id,
            action='webhook_updated',
            resource_type='webhook',
            resource_id=webhook_id,
            details={'updates': list(updates.keys())}
        )
        
        return self._sanitize_webhook_config(webhook)
    
    def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """Delete webhook configuration"""
        # Get webhook first to verify it exists
        webhook = self.db_client.get_item(
            pk=f'WEBHOOK#{webhook_id}',
            sk='CONFIG'
        )
        
        if not webhook:
            return False
        
        # Delete from DynamoDB
        self.db_client.delete_item(
            pk=f'WEBHOOK#{webhook_id}',
            sk='CONFIG'
        )
        
        # Audit log
        self.audit_logger.log_action(
            user_id=user_id,
            action='webhook_deleted',
            resource_type='webhook',
            resource_id=webhook_id,
            details={'name': webhook.get('name')}
        )
        
        return True
    
    def toggle_webhook(self, webhook_id: str, user_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable webhook without deleting"""
        return self.update_webhook(
            webhook_id=webhook_id,
            user_id=user_id,
            updates={'enabled': enabled}
        )
    
    def _sanitize_webhook_config(self, webhook: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from webhook config"""
        sanitized = webhook.copy()
        
        # Remove encrypted secrets from response
        if 'auth_config' in sanitized:
            auth_config = sanitized['auth_config'].copy()
            if 'api_key' in auth_config:
                auth_config['api_key'] = '***ENCRYPTED***'
            if 'client_secret' in auth_config:
                auth_config['client_secret'] = '***ENCRYPTED***'
            sanitized['auth_config'] = auth_config
        
        return sanitized


# Lambda handler
@require_auth()
def lambda_handler(event, context):
    """
    Main Lambda handler for webhook configuration
    
    Supports:
    - POST /webhooks - Create webhook
    - GET /webhooks - List webhooks
    - GET /webhooks/{id} - Get webhook
    - PUT /webhooks/{id} - Update webhook
    - DELETE /webhooks/{id} - Delete webhook
    - POST /webhooks/{id}/toggle - Enable/disable webhook
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters', {})
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Get user from auth context
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('user_id', 'system')
        
        service = WebhookConfigService()
        
        # Route to appropriate handler
        if http_method == 'POST' and path == '/webhooks':
            # Create webhook
            result = service.create_webhook(
                user_id=user_id,
                name=body.get('name'),
                url=body.get('url'),
                events=body.get('events', []),
                auth_type=body.get('auth_type', 'api_key'),
                auth_config=body.get('auth_config'),
                description=body.get('description', ''),
                enabled=body.get('enabled', True)
            )
            
            return {
                'statusCode': 201,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif http_method == 'GET' and path == '/webhooks':
            # List webhooks
            webhooks = service.list_webhooks(user_id=user_id)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'webhooks': webhooks})
            }
        
        elif http_method == 'GET' and path_parameters.get('id'):
            # Get webhook
            webhook_id = path_parameters['id']
            webhook = service.get_webhook(webhook_id)
            
            if not webhook:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Webhook not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(webhook)
            }
        
        elif http_method == 'PUT' and path_parameters.get('id'):
            # Update webhook
            webhook_id = path_parameters['id']
            result = service.update_webhook(
                webhook_id=webhook_id,
                user_id=user_id,
                updates=body
            )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif http_method == 'DELETE' and path_parameters.get('id'):
            # Delete webhook
            webhook_id = path_parameters['id']
            success = service.delete_webhook(webhook_id, user_id)
            
            if not success:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Webhook not found'})
                }
            
            return {
                'statusCode': 204,
                'headers': {'Content-Type': 'application/json'},
                'body': ''
            }
        
        elif http_method == 'POST' and 'toggle' in path:
            # Toggle webhook
            webhook_id = path_parameters['id']
            enabled = body.get('enabled', True)
            result = service.toggle_webhook(webhook_id, user_id, enabled)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    
    except Exception as e:
        print(f"Error in webhook config handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
