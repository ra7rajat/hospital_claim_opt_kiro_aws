"""
Authentication Handler Lambda Function
Handles user authentication, login, logout, and session management
"""
import json
import os
import time
import boto3
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# AWS clients
cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')

# Environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sessions')

# Session configuration
SESSION_DURATION_HOURS = 8
INACTIVITY_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

def get_secret_hash(username: str) -> str:
    """
    Calculate SECRET_HASH for Cognito authentication
    """
    message = bytes(username + CLIENT_ID, 'utf-8')
    secret = bytes(CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, msg=message, digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()

def check_rate_limit(email: str) -> bool:
    """
    Check if user has exceeded login attempt rate limit
    Returns True if user is allowed to attempt login, False if locked out
    """
    table = dynamodb.Table(SESSIONS_TABLE)
    
    try:
        # Get login attempts for this email
        response = table.get_item(
            Key={
                'PK': f'LOGIN_ATTEMPTS#{email}',
                'SK': 'METADATA'
            }
        )
        
        if 'Item' not in response:
            return True
        
        item = response['Item']
        attempts = item.get('attempts', 0)
        locked_until = item.get('locked_until', 0)
        
        # Check if user is currently locked out
        current_time = int(time.time())
        if locked_until > current_time:
            return False
        
        # Check if attempts exceed limit
        if attempts >= MAX_LOGIN_ATTEMPTS:
            # Lock the account
            table.put_item(
                Item={
                    'PK': f'LOGIN_ATTEMPTS#{email}',
                    'SK': 'METADATA',
                    'attempts': attempts,
                    'locked_until': current_time + (LOCKOUT_DURATION_MINUTES * 60),
                    'updated_at': current_time
                }
            )
            return False
        
        return True
        
    except Exception as e:
        print(f"Error checking rate limit: {str(e)}")
        return True  # Allow login on error to avoid blocking legitimate users

def record_login_attempt(email: str, success: bool):
    """
    Record a login attempt for rate limiting
    """
    table = dynamodb.Table(SESSIONS_TABLE)
    current_time = int(time.time())
    
    try:
        if success:
            # Clear login attempts on successful login
            table.delete_item(
                Key={
                    'PK': f'LOGIN_ATTEMPTS#{email}',
                    'SK': 'METADATA'
                }
            )
        else:
            # Increment failed attempts
            response = table.get_item(
                Key={
                    'PK': f'LOGIN_ATTEMPTS#{email}',
                    'SK': 'METADATA'
                }
            )
            
            attempts = 1
            if 'Item' in response:
                attempts = response['Item'].get('attempts', 0) + 1
            
            table.put_item(
                Item={
                    'PK': f'LOGIN_ATTEMPTS#{email}',
                    'SK': 'METADATA',
                    'attempts': attempts,
                    'locked_until': 0,
                    'updated_at': current_time
                }
            )
    except Exception as e:
        print(f"Error recording login attempt: {str(e)}")

def create_session(user_id: str, email: str, role: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new session in DynamoDB
    """
    import secrets
    
    table = dynamodb.Table(SESSIONS_TABLE)
    current_time = int(time.time())
    
    # Generate cryptographically secure session token
    session_token = secrets.token_urlsafe(32)
    session_id = hashlib.sha256(session_token.encode()).hexdigest()
    
    # Calculate expiration times
    expires_at = current_time + (SESSION_DURATION_HOURS * 3600)
    
    # Extract request metadata
    request_context = event.get('requestContext', {})
    identity = request_context.get('identity', {})
    
    session_data = {
        'PK': f'SESSION#{session_id}',
        'SK': 'METADATA',
        'user_id': user_id,
        'email': email,
        'role': role,
        'created_at': current_time,
        'expires_at': expires_at,
        'last_activity': current_time,
        'ip_address': identity.get('sourceIp', 'unknown'),
        'user_agent': identity.get('userAgent', 'unknown'),
        'active': True
    }
    
    # Store session
    table.put_item(Item=session_data)
    
    # Also create a GSI entry for user lookup
    table.put_item(
        Item={
            'PK': f'USER#{user_id}',
            'SK': f'SESSION#{session_id}',
            'session_id': session_id,
            'created_at': current_time,
            'expires_at': expires_at
        }
    )
    
    return {
        'session_token': session_token,
        'session_id': session_id,
        'expires_at': expires_at
    }

def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session token and return session data if valid
    """
    table = dynamodb.Table(SESSIONS_TABLE)
    current_time = int(time.time())
    
    # Hash the token to get session ID
    session_id = hashlib.sha256(session_token.encode()).hexdigest()
    
    try:
        response = table.get_item(
            Key={
                'PK': f'SESSION#{session_id}',
                'SK': 'METADATA'
            }
        )
        
        if 'Item' not in response:
            return None
        
        session = response['Item']
        
        # Check if session is active
        if not session.get('active', False):
            return None
        
        # Check if session has expired
        if session.get('expires_at', 0) < current_time:
            return None
        
        # Check inactivity timeout
        last_activity = session.get('last_activity', 0)
        inactivity_limit = current_time - (INACTIVITY_TIMEOUT_MINUTES * 60)
        if last_activity < inactivity_limit:
            return None
        
        # Update last activity
        table.update_item(
            Key={
                'PK': f'SESSION#{session_id}',
                'SK': 'METADATA'
            },
            UpdateExpression='SET last_activity = :time',
            ExpressionAttributeValues={
                ':time': current_time
            }
        )
        
        return session
        
    except Exception as e:
        print(f"Error validating session: {str(e)}")
        return None

def invalidate_session(session_token: str) -> bool:
    """
    Invalidate a session (logout)
    """
    table = dynamodb.Table(SESSIONS_TABLE)
    
    # Hash the token to get session ID
    session_id = hashlib.sha256(session_token.encode()).hexdigest()
    
    try:
        table.update_item(
            Key={
                'PK': f'SESSION#{session_id}',
                'SK': 'METADATA'
            },
            UpdateExpression='SET active = :active',
            ExpressionAttributeValues={
                ':active': False
            }
        )
        return True
    except Exception as e:
        print(f"Error invalidating session: {str(e)}")
        return False

def login_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user login with Cognito
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').lower().strip()
        password = body.get('password', '')
        
        # Validate input
        if not email or not password:
            return create_response(400, {'error': 'Email and password are required'})
        
        # Check rate limiting
        if not check_rate_limit(email):
            return create_response(429, {
                'error': 'Too many failed login attempts. Account locked for 30 minutes.'
            })
        
        try:
            # Authenticate with Cognito
            secret_hash = get_secret_hash(email)
            
            response = cognito_client.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
            
            # Check if MFA is required
            if response.get('ChallengeName') == 'SOFTWARE_TOKEN_MFA':
                # MFA is required
                record_login_attempt(email, False)  # Not fully authenticated yet
                
                return create_response(200, {
                    'requires_mfa': True,
                    'session': response.get('Session'),
                    'message': 'MFA code required'
                })
            
            # Get user attributes
            id_token = response['AuthenticationResult']['IdToken']
            access_token = response['AuthenticationResult']['AccessToken']
            
            # Decode ID token to get user info (in production, verify signature)
            import base64
            token_parts = id_token.split('.')
            payload = json.loads(base64.urlsafe_b64decode(token_parts[1] + '=='))
            
            user_id = payload.get('sub')
            user_email = payload.get('email')
            role = payload.get('custom:role', 'doctor')
            
            # Create session
            session_info = create_session(user_id, user_email, role, event)
            
            # Record successful login
            record_login_attempt(email, True)
            
            return create_response(200, {
                'session_token': session_info['session_token'],
                'expires_at': session_info['expires_at'],
                'requires_mfa': False,
                'user_info': {
                    'user_id': user_id,
                    'email': user_email,
                    'role': role
                }
            })
            
        except cognito_client.exceptions.NotAuthorizedException:
            record_login_attempt(email, False)
            return create_response(401, {'error': 'Invalid email or password'})
        
        except cognito_client.exceptions.UserNotFoundException:
            record_login_attempt(email, False)
            return create_response(401, {'error': 'Invalid email or password'})
        
        except Exception as e:
            print(f"Cognito error: {str(e)}")
            return create_response(500, {'error': 'Authentication service error'})
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def logout_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user logout
    """
    try:
        # Get session token from header or body
        headers = event.get('headers', {})
        session_token = headers.get('Authorization', '').replace('Bearer ', '')
        
        if not session_token:
            body = json.loads(event.get('body', '{}'))
            session_token = body.get('session_token', '')
        
        if not session_token:
            return create_response(400, {'error': 'Session token required'})
        
        # Invalidate session
        success = invalidate_session(session_token)
        
        if success:
            return create_response(200, {'message': 'Logged out successfully'})
        else:
            return create_response(500, {'error': 'Failed to logout'})
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def validate_session_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validate a session token
    """
    try:
        # Get session token from header
        headers = event.get('headers', {})
        session_token = headers.get('Authorization', '').replace('Bearer ', '')
        
        if not session_token:
            return create_response(401, {'error': 'Session token required'})
        
        # Validate session
        session = validate_session(session_token)
        
        if not session:
            return create_response(401, {'error': 'Invalid or expired session'})
        
        return create_response(200, {
            'valid': True,
            'user_info': {
                'user_id': session.get('user_id'),
                'email': session.get('email'),
                'role': session.get('role')
            },
            'expires_at': session.get('expires_at'),
            'last_activity': session.get('last_activity')
        })
        
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create standardized API response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        },
        'body': json.dumps(body)
    }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler - routes to appropriate function based on path
    """
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')
    
    # Handle OPTIONS for CORS
    if http_method == 'OPTIONS':
        return create_response(200, {})
    
    # Route to appropriate handler
    if path.endswith('/login') and http_method == 'POST':
        return login_handler(event, context)
    
    elif path.endswith('/logout') and http_method == 'POST':
        return logout_handler(event, context)
    
    elif path.endswith('/validate') and http_method == 'GET':
        return validate_session_handler(event, context)
    
    else:
        return create_response(404, {'error': 'Not found'})
