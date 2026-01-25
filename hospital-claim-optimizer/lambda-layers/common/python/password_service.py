"""
Password Management Service
Handles password reset, change, and validation
"""
import os
import time
import secrets
import hashlib
import re
import boto3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
cognito_client = boto3.client('cognito-idp')
ses_client = boto3.client('ses')

# Configuration
RESET_TOKEN_VALIDITY_HOURS = 1
PASSWORD_HISTORY_COUNT = 5
MIN_PASSWORD_LENGTH = 8

# Environment variables
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sessions')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@hospitalclaimoptimizer.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

# Password requirements
PASSWORD_REQUIREMENTS = {
    'min_length': MIN_PASSWORD_LENGTH,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_number': True,
    'require_special': True,
    'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?'
}

class PasswordService:
    """Manages password operations"""
    
    def __init__(self, table_name: str = None):
        self.table_name = table_name or SESSIONS_TABLE
        self.table = dynamodb.Table(self.table_name)
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """
        Validate password against requirements
        
        Args:
            password: Password to validate
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Check minimum length
        if len(password) < PASSWORD_REQUIREMENTS['min_length']:
            errors.append(f"Password must be at least {PASSWORD_REQUIREMENTS['min_length']} characters long")
        
        # Check for uppercase letter
        if PASSWORD_REQUIREMENTS['require_uppercase'] and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if PASSWORD_REQUIREMENTS['require_lowercase'] and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check for number
        if PASSWORD_REQUIREMENTS['require_number'] and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check for special character
        if PASSWORD_REQUIREMENTS['require_special']:
            special_chars = PASSWORD_REQUIREMENTS['special_chars']
            if not any(char in password for char in special_chars):
                errors.append(f"Password must contain at least one special character ({special_chars})")
        
        # Check for common patterns
        common_patterns = [
            (r'(.)\1{2,}', "Password should not contain repeated characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password should not contain sequential numbers"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', 
             "Password should not contain sequential letters")
        ]
        
        for pattern, message in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(message)
        
        # Check for common weak passwords
        weak_passwords = [
            'password', 'password123', '12345678', 'qwerty', 'abc123',
            'letmein', 'welcome', 'monkey', '1234567890'
        ]
        
        if password.lower() in weak_passwords:
            errors.append("Password is too common and easily guessable")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password for storage (for password history)
        Note: Actual passwords are stored in Cognito, this is just for history
        
        Args:
            password: Plain text password
        
        Returns:
            SHA256 hash of the password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password_history(self, user_id: str, new_password: str) -> bool:
        """
        Check if password was used recently
        
        Args:
            user_id: User ID
            new_password: New password to check
        
        Returns:
            True if password is acceptable (not in history), False otherwise
        """
        try:
            # Get password history
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'PASSWORD_HISTORY'
                }
            )
            
            if 'Item' not in response:
                # No history, password is acceptable
                return True
            
            history = response['Item'].get('passwords', [])
            new_password_hash = self.hash_password(new_password)
            
            # Check if new password hash is in history
            return new_password_hash not in history
            
        except Exception as e:
            print(f"Error checking password history: {str(e)}")
            # On error, allow the password to avoid blocking users
            return True
    
    def add_to_password_history(self, user_id: str, password: str):
        """
        Add password to history
        
        Args:
            user_id: User ID
            password: Password to add to history
        """
        try:
            password_hash = self.hash_password(password)
            
            # Get current history
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'PASSWORD_HISTORY'
                }
            )
            
            if 'Item' in response:
                history = response['Item'].get('passwords', [])
            else:
                history = []
            
            # Add new password to history
            history.append(password_hash)
            
            # Keep only last N passwords
            if len(history) > PASSWORD_HISTORY_COUNT:
                history = history[-PASSWORD_HISTORY_COUNT:]
            
            # Update history
            self.table.put_item(
                Item={
                    'PK': f'USER#{user_id}',
                    'SK': 'PASSWORD_HISTORY',
                    'passwords': history,
                    'updated_at': int(time.time())
                }
            )
            
        except Exception as e:
            print(f"Error adding to password history: {str(e)}")
    
    def generate_reset_token(self) -> str:
        """
        Generate a secure password reset token
        
        Returns:
            URL-safe reset token
        """
        return secrets.token_urlsafe(32)
    
    def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request a password reset
        
        Args:
            email: User email address
        
        Returns:
            Dict with success status and message
        """
        try:
            # Generate reset token
            reset_token = self.generate_reset_token()
            token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
            
            # Get user from Cognito to verify email exists
            try:
                response = cognito_client.admin_get_user(
                    UserPoolId=USER_POOL_ID,
                    Username=email
                )
                
                # Get user_id from Cognito attributes
                user_id = None
                for attr in response.get('UserAttributes', []):
                    if attr['Name'] == 'sub':
                        user_id = attr['Value']
                        break
                
                if not user_id:
                    # User not found, but don't reveal this for security
                    return {
                        'success': True,
                        'message': 'If the email exists, a reset link has been sent'
                    }
                
            except cognito_client.exceptions.UserNotFoundException:
                # User not found, but don't reveal this for security
                return {
                    'success': True,
                    'message': 'If the email exists, a reset link has been sent'
                }
            
            # Store reset token
            expires_at = int(time.time()) + (RESET_TOKEN_VALIDITY_HOURS * 3600)
            
            self.table.put_item(
                Item={
                    'PK': f'RESET_TOKEN#{token_hash}',
                    'SK': 'METADATA',
                    'user_id': user_id,
                    'email': email,
                    'created_at': int(time.time()),
                    'expires_at': expires_at,
                    'used': False
                }
            )
            
            # Send reset email
            reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
            
            self._send_reset_email(email, reset_url)
            
            return {
                'success': True,
                'message': 'If the email exists, a reset link has been sent',
                'token': reset_token  # Only for testing, remove in production
            }
            
        except Exception as e:
            print(f"Error requesting password reset: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to process password reset request'
            }
    
    def verify_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a password reset token
        
        Args:
            token: Reset token
        
        Returns:
            Token data if valid, None otherwise
        """
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            response = self.table.get_item(
                Key={
                    'PK': f'RESET_TOKEN#{token_hash}',
                    'SK': 'METADATA'
                }
            )
            
            if 'Item' not in response:
                return None
            
            token_data = response['Item']
            
            # Check if token has been used
            if token_data.get('used', False):
                return None
            
            # Check if token has expired
            if token_data.get('expires_at', 0) < int(time.time()):
                return None
            
            return token_data
            
        except Exception as e:
            print(f"Error verifying reset token: {str(e)}")
            return None
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password using a reset token
        
        Args:
            token: Reset token
            new_password: New password
        
        Returns:
            Dict with success status and message
        """
        try:
            # Verify token
            token_data = self.verify_reset_token(token)
            
            if not token_data:
                return {
                    'success': False,
                    'message': 'Invalid or expired reset token'
                }
            
            user_id = token_data['user_id']
            email = token_data['email']
            
            # Validate new password
            validation = self.validate_password(new_password)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': 'Password does not meet requirements',
                    'errors': validation['errors']
                }
            
            # Check password history
            if not self.check_password_history(user_id, new_password):
                return {
                    'success': False,
                    'message': f'Password was used recently. Please choose a different password.'
                }
            
            # Reset password in Cognito
            try:
                cognito_client.admin_set_user_password(
                    UserPoolId=USER_POOL_ID,
                    Username=email,
                    Password=new_password,
                    Permanent=True
                )
            except Exception as e:
                print(f"Cognito error: {str(e)}")
                return {
                    'success': False,
                    'message': 'Failed to reset password'
                }
            
            # Add to password history
            self.add_to_password_history(user_id, new_password)
            
            # Mark token as used
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.table.update_item(
                Key={
                    'PK': f'RESET_TOKEN#{token_hash}',
                    'SK': 'METADATA'
                },
                UpdateExpression='SET used = :used, used_at = :time',
                ExpressionAttributeValues={
                    ':used': True,
                    ':time': int(time.time())
                }
            )
            
            return {
                'success': True,
                'message': 'Password reset successfully'
            }
            
        except Exception as e:
            print(f"Error resetting password: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to reset password'
            }
    
    def change_password(self, user_id: str, email: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change password (user must provide current password)
        
        Args:
            user_id: User ID
            email: User email
            current_password: Current password
            new_password: New password
        
        Returns:
            Dict with success status and message
        """
        try:
            # Validate new password
            validation = self.validate_password(new_password)
            if not validation['valid']:
                return {
                    'success': False,
                    'message': 'Password does not meet requirements',
                    'errors': validation['errors']
                }
            
            # Check if new password is same as current
            if current_password == new_password:
                return {
                    'success': False,
                    'message': 'New password must be different from current password'
                }
            
            # Check password history
            if not self.check_password_history(user_id, new_password):
                return {
                    'success': False,
                    'message': f'Password was used recently. Please choose a different password.'
                }
            
            # Change password in Cognito
            try:
                cognito_client.admin_set_user_password(
                    UserPoolId=USER_POOL_ID,
                    Username=email,
                    Password=new_password,
                    Permanent=True
                )
            except Exception as e:
                print(f"Cognito error: {str(e)}")
                return {
                    'success': False,
                    'message': 'Failed to change password'
                }
            
            # Add to password history
            self.add_to_password_history(user_id, new_password)
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            print(f"Error changing password: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to change password'
            }
    
    def _send_reset_email(self, email: str, reset_url: str):
        """
        Send password reset email
        
        Args:
            email: Recipient email
            reset_url: Password reset URL
        """
        try:
            subject = "Password Reset Request - Hospital Claim Optimizer"
            
            html_body = f"""
            <html>
            <head></head>
            <body>
                <h2>Password Reset Request</h2>
                <p>You have requested to reset your password for Hospital Claim Optimizer.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in {RESET_TOKEN_VALIDITY_HOURS} hour(s).</p>
                <p>If you did not request this reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Hospital Claim Optimizer Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Password Reset Request
            
            You have requested to reset your password for Hospital Claim Optimizer.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in {RESET_TOKEN_VALIDITY_HOURS} hour(s).
            
            If you did not request this reset, please ignore this email.
            
            Best regards,
            Hospital Claim Optimizer Team
            """
            
            ses_client.send_email(
                Source=FROM_EMAIL,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {
                        'Text': {'Data': text_body},
                        'Html': {'Data': html_body}
                    }
                }
            )
            
        except Exception as e:
            print(f"Error sending reset email: {str(e)}")
            # Don't fail the request if email fails
    
    def get_password_requirements(self) -> Dict[str, Any]:
        """
        Get password requirements for display to users
        
        Returns:
            Dict with password requirements
        """
        return {
            'min_length': PASSWORD_REQUIREMENTS['min_length'],
            'require_uppercase': PASSWORD_REQUIREMENTS['require_uppercase'],
            'require_lowercase': PASSWORD_REQUIREMENTS['require_lowercase'],
            'require_number': PASSWORD_REQUIREMENTS['require_number'],
            'require_special': PASSWORD_REQUIREMENTS['require_special'],
            'special_chars': PASSWORD_REQUIREMENTS['special_chars'],
            'history_count': PASSWORD_HISTORY_COUNT,
            'description': [
                f"At least {PASSWORD_REQUIREMENTS['min_length']} characters long",
                "Contains uppercase letter (A-Z)",
                "Contains lowercase letter (a-z)",
                "Contains number (0-9)",
                f"Contains special character ({PASSWORD_REQUIREMENTS['special_chars']})",
                f"Not used in last {PASSWORD_HISTORY_COUNT} passwords"
            ]
        }


# Singleton instance
_password_service = None

def get_password_service() -> PasswordService:
    """Get or create PasswordService singleton"""
    global _password_service
    if _password_service is None:
        _password_service = PasswordService()
    return _password_service
