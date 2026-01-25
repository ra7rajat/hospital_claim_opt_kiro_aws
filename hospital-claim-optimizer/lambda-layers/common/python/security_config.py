"""
Security Configuration and Utilities
Provides security-related configurations and utilities for HIPAA compliance
"""
import os
import hashlib
import secrets
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import time

class SecurityConfig:
    """Security configuration constants and utilities"""
    
    # Encryption settings
    ENCRYPTION_ALGORITHM = "AES-256"
    TLS_VERSION = "1.3"
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = 60
    REFRESH_TOKEN_DAYS = 30
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SYMBOLS = True
    
    # Audit settings
    AUDIT_RETENTION_DAYS = 2555  # 7 years for HIPAA compliance
    
    # Rate limiting
    API_RATE_LIMIT_PER_MINUTE = 100
    LOGIN_ATTEMPT_LIMIT = 5
    LOGIN_LOCKOUT_MINUTES = 15

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data: str, salt: Optional[str] = None) -> Dict[str, str]:
    """
    Hash sensitive data using SHA-256 with salt
    Returns both hash and salt for storage
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine data and salt
    salted_data = f"{data}{salt}"
    
    # Create hash
    hash_object = hashlib.sha256(salted_data.encode())
    hash_hex = hash_object.hexdigest()
    
    return {
        'hash': hash_hex,
        'salt': salt
    }

def verify_hash(data: str, stored_hash: str, salt: str) -> bool:
    """Verify data against stored hash"""
    computed_hash = hash_sensitive_data(data, salt)['hash']
    return computed_hash == stored_hash

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data for logging by removing or masking sensitive information
    """
    sensitive_fields = [
        'password', 'ssn', 'social_security_number', 'credit_card',
        'bank_account', 'medical_record_number', 'patient_id',
        'authorization', 'token', 'api_key'
    ]
    
    sanitized = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field contains sensitive information
        is_sensitive = any(sensitive_field in key_lower for sensitive_field in sensitive_fields)
        
        if is_sensitive:
            if isinstance(value, str) and len(value) > 8:
                # Mask all but last 4 characters for longer strings
                sanitized[key] = '*' * (len(value) - 4) + value[-4:]
            else:
                # Completely mask shorter strings
                sanitized[key] = '***MASKED***'
        else:
            sanitized[key] = value
    
    return sanitized

def create_audit_entry(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized audit log entry
    """
    timestamp = datetime.utcnow().isoformat()
    
    audit_entry = {
        'timestamp': timestamp,
        'user_id': user_id,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'details': sanitize_log_data(details or {}),
        'audit_id': generate_secure_token(16),
    }
    
    return audit_entry

def validate_hipaa_compliance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that data handling meets HIPAA compliance requirements
    """
    compliance_check = {
        'is_compliant': True,
        'violations': [],
        'recommendations': []
    }
    
    # Check for PHI in logs
    phi_indicators = [
        'ssn', 'social_security', 'medical_record_number',
        'patient_name', 'date_of_birth', 'phone_number',
        'email', 'address', 'diagnosis'
    ]
    
    for key, value in data.items():
        key_lower = key.lower()
        
        for phi_indicator in phi_indicators:
            if phi_indicator in key_lower:
                if isinstance(value, str) and len(value) > 0 and not value.startswith('*'):
                    compliance_check['is_compliant'] = False
                    compliance_check['violations'].append(
                        f"Potential PHI exposure in field: {key}"
                    )
    
    # Check encryption requirements
    if 'encryption_status' in data:
        if data['encryption_status'] != 'encrypted':
            compliance_check['is_compliant'] = False
            compliance_check['violations'].append(
                "Data not properly encrypted"
            )
    
    # Add recommendations
    if not compliance_check['is_compliant']:
        compliance_check['recommendations'].extend([
            "Ensure all PHI is properly masked or encrypted",
            "Implement data encryption at rest and in transit",
            "Review data handling procedures",
            "Consider additional access controls"
        ])
    
    return compliance_check

def get_security_headers() -> Dict[str, str]:
    """
    Get standard security headers for HTTP responses
    """
    return {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Access-Control-Allow-Origin': '*',  # Configure appropriately for production
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    }

def create_secure_response(
    status_code: int,
    body: Dict[str, Any],
    additional_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a secure HTTP response with proper headers
    """
    headers = get_security_headers()
    
    if additional_headers:
        headers.update(additional_headers)
    
    # Ensure Content-Type is set
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json'
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, default=str)  # Handle datetime serialization
    }

def validate_input_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate input data for required fields and basic security
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'sanitized_data': {}
    }
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Missing required field: {field}")
    
    # Basic input sanitization
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potential script tags and other dangerous content
            sanitized_value = value.replace('<script>', '').replace('</script>', '')
            sanitized_value = sanitized_value.replace('javascript:', '')
            validation_result['sanitized_data'][key] = sanitized_value
        else:
            validation_result['sanitized_data'][key] = value
    
    return validation_result

class RateLimiter:
    """Simple in-memory rate limiter for Lambda functions"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier: str, limit: int, window_minutes: int = 1) -> bool:
        """
        Check if request is allowed based on rate limit
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []
        
        # Check if under limit
        if len(self.requests[identifier]) < limit:
            self.requests[identifier].append(now)
            return True
        
        return False

# Global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(identifier: str, limit: int = SecurityConfig.API_RATE_LIMIT_PER_MINUTE) -> bool:
    """Check if request is within rate limit"""
    return rate_limiter.is_allowed(identifier, limit)

# Environment-specific security configurations
def get_environment_config() -> Dict[str, Any]:
    """Get security configuration based on environment"""
    env = os.environ.get('ENVIRONMENT', 'development')
    
    base_config = {
        'tls_version': SecurityConfig.TLS_VERSION,
        'encryption_algorithm': SecurityConfig.ENCRYPTION_ALGORITHM,
        'session_timeout': SecurityConfig.SESSION_TIMEOUT_MINUTES,
        'audit_retention_days': SecurityConfig.AUDIT_RETENTION_DAYS,
    }
    
    if env == 'production':
        base_config.update({
            'debug_mode': False,
            'log_level': 'WARNING',
            'cors_origins': ['https://yourdomain.com'],
            'require_mfa': True,
        })
    elif env == 'staging':
        base_config.update({
            'debug_mode': False,
            'log_level': 'INFO',
            'cors_origins': ['https://staging.yourdomain.com'],
            'require_mfa': True,
        })
    else:  # development
        base_config.update({
            'debug_mode': True,
            'log_level': 'DEBUG',
            'cors_origins': ['*'],
            'require_mfa': False,
        })
    
    return base_config