"""
Session Management Service
Handles session creation, validation, renewal, and expiration
"""
import os
import time
import hashlib
import secrets
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')

# Configuration
SESSION_DURATION_HOURS = 8
INACTIVITY_TIMEOUT_MINUTES = 30
SESSION_RENEWAL_THRESHOLD_HOURS = 4  # Renew if less than 4 hours remaining

class SessionManager:
    """Manages user sessions"""
    
    def __init__(self, table_name: str = None):
        self.table_name = table_name or os.environ.get('SESSIONS_TABLE', 'sessions')
        self.table = dynamodb.Table(self.table_name)
    
    def create_session(
        self,
        user_id: str,
        email: str,
        role: str,
        ip_address: str = 'unknown',
        user_agent: str = 'unknown',
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new session
        
        Returns:
            Dict containing session_token, session_id, and expires_at
        """
        current_time = int(time.time())
        
        # Generate cryptographically secure session token
        session_token = secrets.token_urlsafe(32)
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = current_time + (SESSION_DURATION_HOURS * 3600)
        
        # Prepare session data
        session_data = {
            'PK': f'SESSION#{session_id}',
            'SK': 'METADATA',
            'user_id': user_id,
            'email': email,
            'role': role,
            'created_at': current_time,
            'expires_at': expires_at,
            'last_activity': current_time,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'active': True,
            'renewed_count': 0
        }
        
        # Add optional metadata
        if metadata:
            session_data['metadata'] = metadata
        
        # Store session
        self.table.put_item(Item=session_data)
        
        # Create GSI entry for user lookup
        self.table.put_item(
            Item={
                'PK': f'USER#{user_id}',
                'SK': f'SESSION#{session_id}',
                'session_id': session_id,
                'created_at': current_time,
                'expires_at': expires_at,
                'active': True
            }
        )
        
        return {
            'session_token': session_token,
            'session_id': session_id,
            'expires_at': expires_at,
            'user_id': user_id,
            'email': email,
            'role': role
        }
    
    def validate_session(self, session_token: str, update_activity: bool = True) -> Optional[Dict[str, Any]]:
        """
        Validate a session token
        
        Args:
            session_token: The session token to validate
            update_activity: Whether to update last_activity timestamp
        
        Returns:
            Session data if valid, None otherwise
        """
        current_time = int(time.time())
        
        # Hash token to get session ID
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        try:
            response = self.table.get_item(
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
                # Mark session as inactive
                self._deactivate_session(session_id)
                return None
            
            # Check inactivity timeout
            last_activity = session.get('last_activity', 0)
            inactivity_limit = current_time - (INACTIVITY_TIMEOUT_MINUTES * 60)
            
            if last_activity < inactivity_limit:
                # Session expired due to inactivity
                self._deactivate_session(session_id)
                return None
            
            # Update last activity if requested
            if update_activity:
                self.table.update_item(
                    Key={
                        'PK': f'SESSION#{session_id}',
                        'SK': 'METADATA'
                    },
                    UpdateExpression='SET last_activity = :time',
                    ExpressionAttributeValues={
                        ':time': current_time
                    }
                )
                session['last_activity'] = current_time
            
            return session
            
        except Exception as e:
            print(f"Error validating session: {str(e)}")
            return None
    
    def renew_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Renew a session if it's close to expiring
        
        Returns:
            Updated session info if renewed, None if session invalid
        """
        current_time = int(time.time())
        
        # Validate current session
        session = self.validate_session(session_token, update_activity=False)
        
        if not session:
            return None
        
        # Check if renewal is needed
        expires_at = session.get('expires_at', 0)
        time_remaining = expires_at - current_time
        renewal_threshold = SESSION_RENEWAL_THRESHOLD_HOURS * 3600
        
        if time_remaining > renewal_threshold:
            # No renewal needed yet
            return {
                'renewed': False,
                'expires_at': expires_at,
                'time_remaining': time_remaining
            }
        
        # Renew session
        new_expires_at = current_time + (SESSION_DURATION_HOURS * 3600)
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        
        try:
            self.table.update_item(
                Key={
                    'PK': f'SESSION#{session_id}',
                    'SK': 'METADATA'
                },
                UpdateExpression='SET expires_at = :expires, last_activity = :time, renewed_count = renewed_count + :inc',
                ExpressionAttributeValues={
                    ':expires': new_expires_at,
                    ':time': current_time,
                    ':inc': 1
                }
            )
            
            # Update GSI entry
            user_id = session.get('user_id')
            self.table.update_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'SESSION#{session_id}'
                },
                UpdateExpression='SET expires_at = :expires',
                ExpressionAttributeValues={
                    ':expires': new_expires_at
                }
            )
            
            return {
                'renewed': True,
                'expires_at': new_expires_at,
                'time_remaining': SESSION_DURATION_HOURS * 3600
            }
            
        except Exception as e:
            print(f"Error renewing session: {str(e)}")
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session (logout)
        
        Returns:
            True if successful, False otherwise
        """
        session_id = hashlib.sha256(session_token.encode()).hexdigest()
        return self._deactivate_session(session_id)
    
    def _deactivate_session(self, session_id: str) -> bool:
        """
        Mark a session as inactive
        """
        try:
            # Get session to find user_id
            response = self.table.get_item(
                Key={
                    'PK': f'SESSION#{session_id}',
                    'SK': 'METADATA'
                }
            )
            
            if 'Item' in response:
                user_id = response['Item'].get('user_id')
                
                # Deactivate main session
                self.table.update_item(
                    Key={
                        'PK': f'SESSION#{session_id}',
                        'SK': 'METADATA'
                    },
                    UpdateExpression='SET active = :active',
                    ExpressionAttributeValues={
                        ':active': False
                    }
                )
                
                # Deactivate GSI entry
                if user_id:
                    self.table.update_item(
                        Key={
                            'PK': f'USER#{user_id}',
                            'SK': f'SESSION#{session_id}'
                        },
                        UpdateExpression='SET active = :active',
                        ExpressionAttributeValues={
                            ':active': False
                        }
                    )
            
            return True
            
        except Exception as e:
            print(f"Error deactivating session: {str(e)}")
            return False
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user
        
        Args:
            user_id: The user ID
            active_only: If True, only return active sessions
        
        Returns:
            List of session data
        """
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'USER#{user_id}',
                    ':sk': 'SESSION#'
                }
            )
            
            sessions = response.get('Items', [])
            
            if active_only:
                current_time = int(time.time())
                sessions = [
                    s for s in sessions
                    if s.get('active', False) and s.get('expires_at', 0) > current_time
                ]
            
            return sessions
            
        except Exception as e:
            print(f"Error getting user sessions: {str(e)}")
            return []
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user
        
        Returns:
            Number of sessions invalidated
        """
        sessions = self.get_user_sessions(user_id, active_only=True)
        count = 0
        
        for session in sessions:
            session_id = session.get('session_id')
            if session_id and self._deactivate_session(session_id):
                count += 1
        
        return count
    
    def cleanup_expired_sessions(self, batch_size: int = 100) -> int:
        """
        Clean up expired sessions (for scheduled maintenance)
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = int(time.time())
        count = 0
        
        try:
            # Scan for expired sessions (in production, use a GSI on expires_at)
            response = self.table.scan(
                FilterExpression='expires_at < :time AND active = :active',
                ExpressionAttributeValues={
                    ':time': current_time,
                    ':active': True
                },
                Limit=batch_size
            )
            
            for item in response.get('Items', []):
                pk = item.get('PK', '')
                if pk.startswith('SESSION#'):
                    session_id = pk.replace('SESSION#', '')
                    if self._deactivate_session(session_id):
                        count += 1
            
            return count
            
        except Exception as e:
            print(f"Error cleaning up sessions: {str(e)}")
            return count
    
    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session information without updating activity
        
        Returns:
            Session info including time remaining, activity status
        """
        session = self.validate_session(session_token, update_activity=False)
        
        if not session:
            return None
        
        current_time = int(time.time())
        expires_at = session.get('expires_at', 0)
        last_activity = session.get('last_activity', 0)
        
        return {
            'user_id': session.get('user_id'),
            'email': session.get('email'),
            'role': session.get('role'),
            'created_at': session.get('created_at'),
            'expires_at': expires_at,
            'last_activity': last_activity,
            'time_remaining': max(0, expires_at - current_time),
            'time_since_activity': current_time - last_activity,
            'active': session.get('active', False),
            'renewed_count': session.get('renewed_count', 0),
            'ip_address': session.get('ip_address'),
            'user_agent': session.get('user_agent')
        }

# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create SessionManager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
