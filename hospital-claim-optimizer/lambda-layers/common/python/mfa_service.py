"""
Multi-Factor Authentication (MFA) Service
Handles TOTP setup, verification, and backup codes
"""
import os
import time
import secrets
import hashlib
import hmac
import base64
import struct
import boto3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')

# Configuration
MFA_CODE_VALIDITY_SECONDS = 300  # 5 minutes
TOTP_INTERVAL = 30  # 30 seconds
TOTP_DIGITS = 6
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8

# Environment variables
SESSIONS_TABLE = os.environ.get('SESSIONS_TABLE', 'sessions')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

class MFAService:
    """Manages Multi-Factor Authentication"""
    
    def __init__(self, table_name: str = None):
        self.table_name = table_name or SESSIONS_TABLE
        self.table = dynamodb.Table(self.table_name)
    
    def generate_secret(self) -> str:
        """
        Generate a random base32-encoded secret for TOTP
        
        Returns:
            Base32-encoded secret string
        """
        # Generate 20 random bytes (160 bits)
        random_bytes = secrets.token_bytes(20)
        # Encode as base32
        secret = base64.b32encode(random_bytes).decode('utf-8')
        # Remove padding
        return secret.rstrip('=')
    
    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt MFA secret using AWS KMS
        
        Args:
            secret: Plain text secret
        
        Returns:
            Base64-encoded encrypted secret
        """
        try:
            if not KMS_KEY_ID:
                # For testing, use simple base64 encoding
                return base64.b64encode(secret.encode()).decode()
            
            response = kms_client.encrypt(
                KeyId=KMS_KEY_ID,
                Plaintext=secret.encode()
            )
            
            # Return base64-encoded ciphertext
            return base64.b64encode(response['CiphertextBlob']).decode()
            
        except Exception as e:
            print(f"Error encrypting secret: {str(e)}")
            raise
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt MFA secret using AWS KMS
        
        Args:
            encrypted_secret: Base64-encoded encrypted secret
        
        Returns:
            Plain text secret
        """
        try:
            if not KMS_KEY_ID:
                # For testing, use simple base64 decoding
                return base64.b64decode(encrypted_secret).decode()
            
            ciphertext = base64.b64decode(encrypted_secret)
            
            response = kms_client.decrypt(
                CiphertextBlob=ciphertext
            )
            
            return response['Plaintext'].decode()
            
        except Exception as e:
            print(f"Error decrypting secret: {str(e)}")
            raise
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for MFA recovery
        
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(BACKUP_CODE_COUNT):
            # Generate random alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
                          for _ in range(BACKUP_CODE_LENGTH))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage
        
        Args:
            code: Plain text backup code
        
        Returns:
            SHA256 hash of the code
        """
        return hashlib.sha256(code.encode()).hexdigest()
    
    def setup_mfa(self, user_id: str, phone_number: str = None) -> Dict[str, Any]:
        """
        Set up MFA for a user
        
        Args:
            user_id: User ID
            phone_number: Optional phone number for SMS fallback
        
        Returns:
            Dict containing secret, QR code data, and backup codes
        """
        # Generate secret
        secret = self.generate_secret()
        
        # Encrypt secret
        encrypted_secret = self.encrypt_secret(secret)
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        
        # Hash backup codes for storage
        hashed_codes = [self.hash_backup_code(code) for code in backup_codes]
        
        # Store MFA configuration
        mfa_config = {
            'PK': f'USER#{user_id}',
            'SK': 'MFA_CONFIG',
            'enabled': False,  # Not enabled until first successful verification
            'secret': encrypted_secret,
            'backup_codes': hashed_codes,
            'backup_codes_used': [],
            'phone_number': phone_number,
            'created_at': int(time.time()),
            'verified_at': None
        }
        
        self.table.put_item(Item=mfa_config)
        
        # Generate QR code data (otpauth:// URL)
        # Format: otpauth://totp/Issuer:user@example.com?secret=SECRET&issuer=Issuer
        qr_data = f"otpauth://totp/HospitalClaimOptimizer:{user_id}?secret={secret}&issuer=HospitalClaimOptimizer&digits={TOTP_DIGITS}&period={TOTP_INTERVAL}"
        
        return {
            'secret': secret,
            'qr_code_data': qr_data,
            'backup_codes': backup_codes,
            'phone_number': phone_number
        }
    
    def generate_totp(self, secret: str, time_step: int = None) -> str:
        """
        Generate a TOTP code
        
        Args:
            secret: Base32-encoded secret
            time_step: Optional time step (for testing)
        
        Returns:
            6-digit TOTP code
        """
        if time_step is None:
            time_step = int(time.time()) // TOTP_INTERVAL
        
        # Decode base32 secret
        key = base64.b32decode(secret + '=' * ((8 - len(secret) % 8) % 8))
        
        # Convert time step to bytes
        time_bytes = struct.pack('>Q', time_step)
        
        # Generate HMAC-SHA1
        hmac_hash = hmac.new(key, time_bytes, hashlib.sha1).digest()
        
        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF
        
        # Generate 6-digit code
        code = code % (10 ** TOTP_DIGITS)
        
        return str(code).zfill(TOTP_DIGITS)
    
    def verify_totp(self, user_id: str, code: str, window: int = 1) -> bool:
        """
        Verify a TOTP code
        
        Args:
            user_id: User ID
            code: 6-digit TOTP code
            window: Number of time steps to check before/after current (default 1)
        
        Returns:
            True if code is valid, False otherwise
        """
        try:
            # Get MFA configuration
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                }
            )
            
            if 'Item' not in response:
                return False
            
            mfa_config = response['Item']
            
            # Decrypt secret
            encrypted_secret = mfa_config.get('secret')
            if not encrypted_secret:
                return False
            
            secret = self.decrypt_secret(encrypted_secret)
            
            # Get current time step
            current_time_step = int(time.time()) // TOTP_INTERVAL
            
            # Check code against current time step and window
            for i in range(-window, window + 1):
                time_step = current_time_step + i
                expected_code = self.generate_totp(secret, time_step)
                
                if code == expected_code:
                    # Code is valid
                    # Update MFA config if this is first verification
                    if not mfa_config.get('enabled'):
                        self.table.update_item(
                            Key={
                                'PK': f'USER#{user_id}',
                                'SK': 'MFA_CONFIG'
                            },
                            UpdateExpression='SET enabled = :enabled, verified_at = :time',
                            ExpressionAttributeValues={
                                ':enabled': True,
                                ':time': int(time.time())
                            }
                        )
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying TOTP: {str(e)}")
            return False
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify a backup code
        
        Args:
            user_id: User ID
            code: Backup code
        
        Returns:
            True if code is valid and unused, False otherwise
        """
        try:
            # Get MFA configuration
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                }
            )
            
            if 'Item' not in response:
                return False
            
            mfa_config = response['Item']
            
            # Hash the provided code
            code_hash = self.hash_backup_code(code)
            
            # Check if code exists and hasn't been used
            backup_codes = mfa_config.get('backup_codes', [])
            used_codes = mfa_config.get('backup_codes_used', [])
            
            if code_hash in backup_codes and code_hash not in used_codes:
                # Mark code as used
                used_codes.append(code_hash)
                
                self.table.update_item(
                    Key={
                        'PK': f'USER#{user_id}',
                        'SK': 'MFA_CONFIG'
                    },
                    UpdateExpression='SET backup_codes_used = :used',
                    ExpressionAttributeValues={
                        ':used': used_codes
                    }
                )
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying backup code: {str(e)}")
            return False
    
    def disable_mfa(self, user_id: str) -> bool:
        """
        Disable MFA for a user
        
        Args:
            user_id: User ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                },
                UpdateExpression='SET enabled = :enabled',
                ExpressionAttributeValues={
                    ':enabled': False
                }
            )
            return True
            
        except Exception as e:
            print(f"Error disabling MFA: {str(e)}")
            return False
    
    def is_mfa_enabled(self, user_id: str) -> bool:
        """
        Check if MFA is enabled for a user
        
        Args:
            user_id: User ID
        
        Returns:
            True if MFA is enabled, False otherwise
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                }
            )
            
            if 'Item' not in response:
                return False
            
            return response['Item'].get('enabled', False)
            
        except Exception as e:
            print(f"Error checking MFA status: {str(e)}")
            return False
    
    def get_mfa_config(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get MFA configuration for a user (without sensitive data)
        
        Args:
            user_id: User ID
        
        Returns:
            MFA configuration dict or None
        """
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                }
            )
            
            if 'Item' not in response:
                return None
            
            config = response['Item']
            
            # Return safe data (no secret or backup codes)
            return {
                'enabled': config.get('enabled', False),
                'phone_number': config.get('phone_number'),
                'created_at': config.get('created_at'),
                'verified_at': config.get('verified_at'),
                'backup_codes_remaining': len(config.get('backup_codes', [])) - len(config.get('backup_codes_used', []))
            }
            
        except Exception as e:
            print(f"Error getting MFA config: {str(e)}")
            return None
    
    def regenerate_backup_codes(self, user_id: str) -> Optional[List[str]]:
        """
        Regenerate backup codes for a user
        
        Args:
            user_id: User ID
        
        Returns:
            New backup codes or None if failed
        """
        try:
            # Generate new backup codes
            backup_codes = self.generate_backup_codes()
            
            # Hash backup codes for storage
            hashed_codes = [self.hash_backup_code(code) for code in backup_codes]
            
            # Update MFA configuration
            self.table.update_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'MFA_CONFIG'
                },
                UpdateExpression='SET backup_codes = :codes, backup_codes_used = :used',
                ExpressionAttributeValues={
                    ':codes': hashed_codes,
                    ':used': []
                }
            )
            
            return backup_codes
            
        except Exception as e:
            print(f"Error regenerating backup codes: {str(e)}")
            return None


# Singleton instance
_mfa_service = None

def get_mfa_service() -> MFAService:
    """Get or create MFAService singleton"""
    global _mfa_service
    if _mfa_service is None:
        _mfa_service = MFAService()
    return _mfa_service
