"""
Authentication and Authorization Middleware
Provides role-based access control for Lambda functions
"""
import json
import os
import time
from typing import Dict, Any, Optional, List
from functools import wraps
from enum import Enum

class UserRole(Enum):
    HOSPITAL_ADMIN = "hospital_admin"
    DOCTOR = "doctor"
    TPA_USER = "tpa_user"

class Permission(Enum):
    # Policy management
    UPLOAD_POLICY = "upload_policy"
    VIEW_POLICY = "view_policy"
    DELETE_POLICY = "delete_policy"
    
    # Eligibility checking
    CHECK_ELIGIBILITY = "check_eligibility"
    
    # Claim auditing
    AUDIT_CLAIM = "audit_claim"
    VIEW_AUDIT_RESULTS = "view_audit_results"
    
    # Dashboard and reporting
    VIEW_DASHBOARD = "view_dashboard"
    GENERATE_REPORTS = "generate_reports"
    
    # Patient management
    VIEW_PATIENT_DATA = "view_patient_data"
    EDIT_PATIENT_DATA = "edit_patient_data"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.HOSPITAL_ADMIN: [
        Permission.UPLOAD_POLICY,
        Permission.VIEW_POLICY,
        Permission.DELETE_POLICY,
        Permission.CHECK_ELIGIBILITY,
        Permission.AUDIT_CLAIM,
        Permission.VIEW_AUDIT_RESULTS,
        Permission.VIEW_DASHBOARD,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_PATIENT_DATA,
        Permission.EDIT_PATIENT_DATA,
    ],
    UserRole.DOCTOR: [
        Permission.CHECK_ELIGIBILITY,
        Permission.VIEW_PATIENT_DATA,
    ],
    UserRole.TPA_USER: [
        Permission.AUDIT_CLAIM,
        Permission.VIEW_AUDIT_RESULTS,
        Permission.VIEW_DASHBOARD,
        Permission.GENERATE_REPORTS,
        Permission.VIEW_PATIENT_DATA,
    ],
}

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class AuthorizationError(Exception):
    """Raised when user lacks required permissions"""
    pass

def extract_user_info(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from Cognito JWT token in API Gateway event
    """
    try:
        # Get the authorization context from API Gateway
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        
        # Extract claims from Cognito authorizer
        claims = authorizer.get('claims', {})
        
        if not claims:
            raise AuthenticationError("No authentication claims found")
        
        user_info = {
            'user_id': claims.get('sub'),
            'email': claims.get('email'),
            'username': claims.get('cognito:username'),
            'role': claims.get('custom:role', 'doctor'),  # Default to doctor role
            'hospital_id': claims.get('custom:hospital_id'),
            'groups': claims.get('cognito:groups', '').split(',') if claims.get('cognito:groups') else [],
        }
        
        # Validate required fields
        if not user_info['user_id']:
            raise AuthenticationError("User ID not found in token")
        
        return user_info
        
    except Exception as e:
        raise AuthenticationError(f"Failed to extract user info: {str(e)}")

def check_permission(user_role: str, required_permission: Permission) -> bool:
    """
    Check if user role has the required permission
    """
    try:
        role_enum = UserRole(user_role)
        allowed_permissions = ROLE_PERMISSIONS.get(role_enum, [])
        return required_permission in allowed_permissions
    except ValueError:
        # Invalid role
        return False

def require_auth(required_permissions: List[Permission] = None):
    """
    Decorator to require authentication and optionally check permissions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            try:
                # Extract user information
                user_info = extract_user_info(event)
                
                # Check permissions if specified
                if required_permissions:
                    user_role = user_info.get('role')
                    
                    for permission in required_permissions:
                        if not check_permission(user_role, permission):
                            return create_error_response(
                                403, 
                                f"Insufficient permissions. Required: {permission.value}"
                            )
                
                # Add user info to event for use in the function
                event['user_info'] = user_info
                
                # Call the original function
                return func(event, context)
                
            except AuthenticationError as e:
                return create_error_response(401, f"Authentication failed: {str(e)}")
            except AuthorizationError as e:
                return create_error_response(403, f"Authorization failed: {str(e)}")
            except Exception as e:
                return create_error_response(500, f"Internal error: {str(e)}")
        
        return wrapper
    return decorator

def require_hospital_access(func):
    """
    Decorator to ensure user can only access data from their hospital
    """
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        user_info = event.get('user_info', {})
        user_hospital_id = user_info.get('hospital_id')
        
        # Extract hospital_id from request
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        requested_hospital_id = body.get('hospital_id')
        
        # Check if user is trying to access data from their hospital
        if requested_hospital_id and requested_hospital_id != user_hospital_id:
            return create_error_response(
                403, 
                "Access denied: You can only access data from your hospital"
            )
        
        return func(event, context)
    
    return wrapper

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create standardized error response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        },
        'body': json.dumps({
            'error': message,
            'timestamp': str(int(time.time())),
        })
    }

def audit_action(action: str, resource_type: str, resource_id: str = None):
    """
    Decorator to audit user actions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            user_info = event.get('user_info', {})
            
            # Log the action (in production, this would go to CloudWatch or audit table)
            audit_log = {
                'timestamp': str(int(time.time())),
                'user_id': user_info.get('user_id'),
                'user_email': user_info.get('email'),
                'user_role': user_info.get('role'),
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
                'user_agent': event.get('requestContext', {}).get('identity', {}).get('userAgent'),
            }
            
            print(f"AUDIT: {json.dumps(audit_log)}")
            
            # Call the original function
            result = func(event, context)
            
            # Log the result status
            status_code = result.get('statusCode', 200)
            audit_log['result_status'] = status_code
            audit_log['success'] = 200 <= status_code < 300
            
            print(f"AUDIT_RESULT: {json.dumps(audit_log)}")
            
            return result
        
        return wrapper
    return decorator

# Utility functions for common authorization patterns
def can_access_patient_data(user_info: Dict[str, Any], patient_hospital_id: str) -> bool:
    """Check if user can access patient data"""
    user_hospital_id = user_info.get('hospital_id')
    user_role = user_info.get('role')
    
    # Hospital admin and TPA users can access any patient in their hospital
    if user_role in ['hospital_admin', 'tpa_user']:
        return user_hospital_id == patient_hospital_id
    
    # Doctors can only access patients in their hospital
    if user_role == 'doctor':
        return user_hospital_id == patient_hospital_id
    
    return False

def can_modify_policy(user_info: Dict[str, Any], policy_hospital_id: str) -> bool:
    """Check if user can modify policy"""
    user_hospital_id = user_info.get('hospital_id')
    user_role = user_info.get('role')
    
    # Only hospital admins can modify policies in their hospital
    return (user_role == 'hospital_admin' and 
            user_hospital_id == policy_hospital_id)

def can_audit_claims(user_info: Dict[str, Any], claim_hospital_id: str) -> bool:
    """Check if user can audit claims"""
    user_hospital_id = user_info.get('hospital_id')
    user_role = user_info.get('role')
    
    # Hospital admins and TPA users can audit claims in their hospital
    return (user_role in ['hospital_admin', 'tpa_user'] and 
            user_hospital_id == claim_hospital_id)

# Example usage patterns:
"""
# Basic authentication
@require_auth()
def my_function(event, context):
    user_info = event['user_info']
    # Function logic here

# Authentication with specific permissions
@require_auth([Permission.UPLOAD_POLICY, Permission.VIEW_POLICY])
def upload_policy(event, context):
    # Function logic here

# Authentication with hospital access control
@require_auth([Permission.VIEW_PATIENT_DATA])
@require_hospital_access
def get_patient_data(event, context):
    # Function logic here

# Authentication with auditing
@require_auth([Permission.AUDIT_CLAIM])
@audit_action("audit_claim", "claim")
def audit_claim(event, context):
    # Function logic here
"""