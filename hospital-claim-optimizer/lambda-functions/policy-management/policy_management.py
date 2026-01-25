"""
Policy Management Lambda Function
Handles policy CRUD operations, versioning, and search functionality
"""
import json
import os
from typing import Dict, Any
import sys
sys.path.append('/opt/python')

from common_utils import DynamoDBClient, create_response, get_timestamp
from auth_middleware import require_auth, require_hospital_access, audit_action, Permission
from security_config import create_secure_response, validate_input_data, check_rate_limit
from policy_service import PolicyService, PolicySearchService, PolicyVersioningError
from database_access import DynamoDBAccessLayer

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']

@require_auth([Permission.VIEW_POLICY])
@audit_action("manage_policy", "policy")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for policy management operations
    """
    try:
        # Rate limiting check
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'anonymous')
        
        if not check_rate_limit(user_id, limit=30):  # 30 operations per minute
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        if 'body' in event and event['body']:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = {}
        
        # Initialize services
        dynamodb_client = DynamoDBClient(TABLE_NAME)
        db_access = DynamoDBAccessLayer(dynamodb_client)
        policy_service = PolicyService(db_access)
        search_service = PolicySearchService(policy_service)
        
        # Route to appropriate handler
        if http_method == 'GET':
            return handle_get_request(policy_service, search_service, path_parameters, query_parameters, user_info)
        elif http_method == 'POST':
            return handle_post_request(policy_service, body, user_info)
        elif http_method == 'PUT':
            return handle_put_request(policy_service, path_parameters, body, user_info)
        elif http_method == 'DELETE':
            return handle_delete_request(policy_service, path_parameters, user_info)
        else:
            return create_secure_response(405, {
                'error': f'Method {http_method} not allowed'
            })
        
    except Exception as e:
        return create_secure_response(500, {
            'error': f'Internal server error: {str(e)}'
        })

def handle_get_request(
    policy_service: PolicyService,
    search_service: PolicySearchService,
    path_params: Dict[str, Any],
    query_params: Dict[str, Any],
    user_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle GET requests for policy retrieval and search"""
    
    hospital_id = user_info.get('hospital_id')
    if not hospital_id:
        return create_secure_response(400, {
            'error': 'Hospital ID not found in user context'
        })
    
    policy_id = path_params.get('policy_id')
    
    # Single policy retrieval
    if policy_id:
        if path_params.get('action') == 'versions':
            # Get policy version history
            versions = policy_service.get_policy_versions(hospital_id, policy_id)
            return create_secure_response(200, {
                'policy_id': policy_id,
                'versions': versions
            })
        elif path_params.get('action') == 'audit':
            # Get policy audit trail
            audit_trail = policy_service.get_policy_audit_trail(policy_id)
            return create_secure_response(200, {
                'policy_id': policy_id,
                'audit_trail': audit_trail
            })
        else:
            # Get single policy
            policy = policy_service.get_policy(hospital_id, policy_id)
            if not policy:
                return create_secure_response(404, {
                    'error': 'Policy not found'
                })
            
            return create_secure_response(200, {
                'policy': policy.to_dynamodb_item()
            })
    
    # Policy search and listing
    search_type = query_params.get('search_type', 'basic')
    
    if search_type == 'advanced':
        # Advanced search
        search_criteria = {
            'policy_name': query_params.get('name'),
            'extraction_status': query_params.get('status'),
            'min_confidence': float(query_params.get('min_confidence', 0)),
            'version': int(query_params.get('version', 0)) if query_params.get('version') else None,
            'sort_by': query_params.get('sort_by', 'created_at'),
            'sort_order': query_params.get('sort_order', 'desc'),
            'limit': int(query_params.get('limit', 50)),
            'offset': int(query_params.get('offset', 0))
        }
        
        # Remove None values
        search_criteria = {k: v for k, v in search_criteria.items() if v is not None}
        
        policies = search_service.advanced_search(hospital_id, search_criteria)
        
    elif search_type == 'by_name':
        # Search by name pattern
        name_pattern = query_params.get('name', '')
        policies = policy_service.search_policies_by_name(hospital_id, name_pattern)
        
    elif search_type == 'by_status':
        # Search by status
        status = query_params.get('status', 'COMPLETED')
        policies = policy_service.get_policies_by_status(hospital_id, status)
        
    elif search_type == 'statistics':
        # Get policy statistics
        stats = policy_service.get_policy_statistics(hospital_id)
        return create_secure_response(200, {
            'statistics': stats
        })
        
    else:
        # Basic search (all policies)
        policies = policy_service.search_policies(hospital_id)
    
    # Convert policies to response format
    policy_data = []
    for policy in policies:
        policy_item = policy.to_dynamodb_item()
        # Remove sensitive fields for list view
        policy_item.pop('raw_text', None)
        policy_data.append(policy_item)
    
    return create_secure_response(200, {
        'policies': policy_data,
        'count': len(policy_data),
        'search_type': search_type
    })

def handle_post_request(
    policy_service: PolicyService,
    body: Dict[str, Any],
    user_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle POST requests for policy creation"""
    
    # Check permissions
    if not check_permission(user_info.get('role'), Permission.UPLOAD_POLICY):
        return create_secure_response(403, {
            'error': 'Insufficient permissions to create policies'
        })
    
    # Validate input
    required_fields = ['policy_name', 'file_size', 's3_key']
    validation_result = validate_input_data(body, required_fields)
    
    if not validation_result['is_valid']:
        return create_secure_response(400, {
            'error': 'Invalid input data',
            'details': validation_result['errors']
        })
    
    body = validation_result['sanitized_data']
    hospital_id = user_info.get('hospital_id')
    user_id = user_info.get('user_id')
    
    try:
        policy = policy_service.create_policy(
            hospital_id=hospital_id,
            policy_name=body['policy_name'],
            file_size=body['file_size'],
            content_type=body.get('content_type', 'application/pdf'),
            s3_key=body['s3_key'],
            created_by=user_id
        )
        
        return create_secure_response(201, {
            'message': 'Policy created successfully',
            'policy': policy.to_dynamodb_item()
        })
        
    except PolicyVersioningError as e:
        return create_secure_response(500, {
            'error': f'Failed to create policy: {str(e)}'
        })

def handle_put_request(
    policy_service: PolicyService,
    path_params: Dict[str, Any],
    body: Dict[str, Any],
    user_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle PUT requests for policy updates"""
    
    # Check permissions
    if not check_permission(user_info.get('role'), Permission.UPLOAD_POLICY):
        return create_secure_response(403, {
            'error': 'Insufficient permissions to update policies'
        })
    
    policy_id = path_params.get('policy_id')
    if not policy_id:
        return create_secure_response(400, {
            'error': 'Policy ID is required'
        })
    
    hospital_id = user_info.get('hospital_id')
    user_id = user_info.get('user_id')
    
    # Validate updates
    allowed_updates = [
        'policy_name', 'extraction_status', 'extracted_rules', 
        'raw_text', 'extraction_confidence', 'effective_date', 
        'expiration_date', 'error_message'
    ]
    
    updates = {k: v for k, v in body.items() if k in allowed_updates}
    
    if not updates:
        return create_secure_response(400, {
            'error': 'No valid updates provided'
        })
    
    try:
        updated_policy = policy_service.update_policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            updates=updates,
            updated_by=user_id
        )
        
        return create_secure_response(200, {
            'message': 'Policy updated successfully',
            'policy': updated_policy.to_dynamodb_item()
        })
        
    except PolicyVersioningError as e:
        return create_secure_response(500, {
            'error': f'Failed to update policy: {str(e)}'
        })

def handle_delete_request(
    policy_service: PolicyService,
    path_params: Dict[str, Any],
    user_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle DELETE requests for policy deletion"""
    
    # Check permissions
    if not check_permission(user_info.get('role'), Permission.DELETE_POLICY):
        return create_secure_response(403, {
            'error': 'Insufficient permissions to delete policies'
        })
    
    policy_id = path_params.get('policy_id')
    if not policy_id:
        return create_secure_response(400, {
            'error': 'Policy ID is required'
        })
    
    hospital_id = user_info.get('hospital_id')
    user_id = user_info.get('user_id')
    
    success = policy_service.delete_policy(hospital_id, policy_id, user_id)
    
    if success:
        return create_secure_response(200, {
            'message': 'Policy deleted successfully'
        })
    else:
        return create_secure_response(404, {
            'error': 'Policy not found or could not be deleted'
        })

# Helper function for permission checking (imported from auth_middleware)
def check_permission(user_role: str, required_permission: Permission) -> bool:
    """Check if user role has the required permission"""
    from auth_middleware import check_permission as auth_check_permission
    return auth_check_permission(user_role, required_permission)