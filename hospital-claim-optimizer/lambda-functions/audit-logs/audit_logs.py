"""
Lambda function for audit log management and retrieval.
Provides endpoints for searching, filtering, and generating compliance reports.
"""

import json
import sys
import os

# Add lambda layer to path
sys.path.insert(0, '/opt/python')

from audit_logger import audit_logger
from auth_middleware import require_auth, require_role
from api_middleware import create_response, handle_errors


@handle_errors
@require_auth
@require_role(['admin', 'tpa_manager'])
def get_audit_trail(event, context):
    """Get audit trail for a specific resource."""
    resource_type = event['pathParameters']['resourceType']
    resource_id = event['pathParameters']['resourceId']
    
    query_params = event.get('queryStringParameters') or {}
    limit = int(query_params.get('limit', 100))
    
    entries = audit_logger.get_audit_trail(
        resource_type=resource_type.upper(),
        resource_id=resource_id,
        limit=limit
    )
    
    return create_response(200, {
        'resource_type': resource_type,
        'resource_id': resource_id,
        'entries': entries,
        'count': len(entries)
    })


@handle_errors
@require_auth
@require_role(['admin', 'tpa_manager'])
def get_user_actions(event, context):
    """Get all actions performed by a user."""
    user_id = event['pathParameters']['userId']
    
    query_params = event.get('queryStringParameters') or {}
    start_date = query_params.get('startDate')
    end_date = query_params.get('endDate')
    limit = int(query_params.get('limit', 100))
    
    entries = audit_logger.get_user_actions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return create_response(200, {
        'user_id': user_id,
        'entries': entries,
        'count': len(entries)
    })


@handle_errors
@require_auth
@require_role(['admin', 'tpa_manager'])
def search_audit_logs(event, context):
    """Search audit logs with filters."""
    query_params = event.get('queryStringParameters') or {}
    
    action = query_params.get('action')
    resource_type = query_params.get('resourceType')
    user_id = query_params.get('userId')
    start_date = query_params.get('startDate')
    end_date = query_params.get('endDate')
    limit = int(query_params.get('limit', 100))
    
    entries = audit_logger.search_audit_logs(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return create_response(200, {
        'filters': {
            'action': action,
            'resource_type': resource_type,
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        },
        'entries': entries,
        'count': len(entries)
    })


@handle_errors
@require_auth
@require_role(['admin'])
def generate_compliance_report(event, context):
    """Generate compliance report for audit logs."""
    body = json.loads(event['body'])
    
    start_date = body['startDate']
    end_date = body['endDate']
    resource_type = body.get('resourceType')
    
    report = audit_logger.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        resource_type=resource_type
    )
    
    return create_response(200, report)


@handle_errors
@require_auth
def get_my_actions(event, context):
    """Get audit trail for the current user's actions."""
    user_id = event['requestContext']['authorizer']['userId']
    
    query_params = event.get('queryStringParameters') or {}
    start_date = query_params.get('startDate')
    end_date = query_params.get('endDate')
    limit = int(query_params.get('limit', 50))
    
    entries = audit_logger.get_user_actions(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return create_response(200, {
        'entries': entries,
        'count': len(entries)
    })


def handler(event, context):
    """Main Lambda handler for audit log operations."""
    http_method = event['httpMethod']
    path = event['path']
    
    # Route to appropriate handler
    if path.endswith('/audit/trail/{resourceType}/{resourceId}'):
        return get_audit_trail(event, context)
    elif path.endswith('/audit/user/{userId}'):
        return get_user_actions(event, context)
    elif path.endswith('/audit/search'):
        return search_audit_logs(event, context)
    elif path.endswith('/audit/compliance-report'):
        return generate_compliance_report(event, context)
    elif path.endswith('/audit/my-actions'):
        return get_my_actions(event, context)
    else:
        return create_response(404, {'error': 'Endpoint not found'})
