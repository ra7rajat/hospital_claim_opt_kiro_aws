"""
API Middleware for consistent error handling, rate limiting, and response formatting.
"""
import json
import time
import traceback
from typing import Dict, Any, Optional, Callable
from functools import wraps
from decimal import Decimal
from datetime import datetime, date
from dataclasses import is_dataclass, asdict


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal, datetime, and dataclass objects."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response with security headers.
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Additional headers to include
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Access-Control-Allow-Origin': '*',  # Configure based on environment
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def create_error_response(
    status_code: int,
    error_code: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_code: Application-specific error code
        error_message: Human-readable error message
        error_details: Additional error details
        retry_after: Seconds to wait before retrying (for rate limiting)
        
    Returns:
        API Gateway error response
    """
    body = {
        'error': {
            'code': error_code,
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat(),
        }
    }
    
    if error_details:
        body['error']['details'] = error_details
    
    if retry_after:
        body['error']['retry_after'] = retry_after
    
    headers = {}
    if retry_after:
        headers['Retry-After'] = str(retry_after)
    
    return create_response(status_code, body, headers)


def api_handler(func: Callable) -> Callable:
    """
    Decorator for Lambda handlers that provides:
    - Consistent error handling
    - Request/response logging
    - Performance tracking
    - Automatic response formatting
    
    Usage:
        @api_handler
        def handler(event, context):
            return {'data': 'response'}
    """
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        start_time = time.time()
        request_id = context.request_id if context else 'unknown'
        
        try:
            # Log incoming request (sanitized)
            print(f"[{request_id}] Incoming request: {event.get('httpMethod', 'UNKNOWN')} {event.get('path', 'UNKNOWN')}")
            
            # Parse body if present
            if 'body' in event and event['body']:
                try:
                    event['parsed_body'] = json.loads(event['body'])
                except json.JSONDecodeError as e:
                    return create_error_response(
                        400,
                        'INVALID_JSON',
                        'Request body contains invalid JSON',
                        {'parse_error': str(e)}
                    )
            
            # Call the actual handler
            result = func(event, context)
            
            # If result is already a properly formatted response, return it
            if isinstance(result, dict) and 'statusCode' in result:
                response = result
            else:
                # Wrap result in standard response format
                response = create_response(200, result)
            
            # Log response time
            elapsed_time = time.time() - start_time
            print(f"[{request_id}] Request completed in {elapsed_time:.3f}s with status {response['statusCode']}")
            
            return response
            
        except ValueError as e:
            # Validation errors
            return create_error_response(
                400,
                'VALIDATION_ERROR',
                str(e),
                {'type': 'ValueError'}
            )
            
        except PermissionError as e:
            # Authorization errors
            return create_error_response(
                403,
                'FORBIDDEN',
                str(e),
                {'type': 'PermissionError'}
            )
            
        except KeyError as e:
            # Missing required fields
            return create_error_response(
                400,
                'MISSING_FIELD',
                f'Required field missing: {str(e)}',
                {'type': 'KeyError'}
            )
            
        except Exception as e:
            # Unexpected errors
            error_trace = traceback.format_exc()
            print(f"[{request_id}] Unexpected error: {error_trace}")
            
            return create_error_response(
                500,
                'INTERNAL_ERROR',
                'An unexpected error occurred',
                {
                    'type': type(e).__name__,
                    'message': str(e),
                    'request_id': request_id
                }
            )
    
    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present in the data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def extract_path_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract path parameters from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary of path parameters
    """
    return event.get('pathParameters', {}) or {}


def extract_query_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract query string parameters from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary of query parameters
    """
    return event.get('queryStringParameters', {}) or {}


def extract_user_context(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user context from Cognito authorizer claims.
    
    Args:
        event: API Gateway event
        
    Returns:
        Dictionary with user information
    """
    authorizer = event.get('requestContext', {}).get('authorizer', {})
    claims = authorizer.get('claims', {})
    
    return {
        'user_id': claims.get('sub', 'unknown'),
        'email': claims.get('email', 'unknown'),
        'role': claims.get('custom:role', 'unknown'),
        'hospital_id': claims.get('custom:hospital_id', 'unknown'),
    }


def paginate_results(
    items: list,
    page: int = 1,
    page_size: int = 50,
    max_page_size: int = 100
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Dictionary with paginated results and metadata
    """
    # Validate and constrain page size
    page_size = min(max(1, page_size), max_page_size)
    page = max(1, page)
    
    # Calculate pagination
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        'items': items[start_idx:end_idx],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
        }
    }
