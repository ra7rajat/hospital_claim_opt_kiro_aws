"""
Reports Lambda Function
Handles report generation and export
"""
import json
import os
import sys
from typing import Dict, Any

# Add common layer to path
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission, audit_action
from security_config import create_secure_response, validate_input_data, check_rate_limit
from database_access import DynamoDBAccessLayer
from reporting_service import ReportingService, MetricsTrackingService

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'RevenueZ_Main')

# Initialize clients
db_client = DynamoDBAccessLayer(TABLE_NAME)
reporting_service = ReportingService(db_client)
metrics_service = MetricsTrackingService(db_client)

@require_auth([Permission.GENERATE_REPORTS])
@audit_action("generate_report", "report")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for report generation requests
    """
    try:
        # Rate limiting
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'unknown')
        
        if not check_rate_limit(user_id, limit=50):
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Get hospital_id from user context
        hospital_id = user_info.get('hospital_id')
        if not hospital_id:
            return create_secure_response(400, {
                'error': 'Hospital ID not found in user context'
            })
        
        # Validate input
        required_fields = ['report_type']
        validation = validate_input_data(body, required_fields)
        
        if not validation['is_valid']:
            return create_secure_response(400, {
                'error': 'Invalid input',
                'details': validation['errors']
            })
        
        sanitized_data = validation['sanitized_data']
        report_type = sanitized_data['report_type']
        
        # Generate report based on type
        if report_type == 'csr_trend':
            start_date = sanitized_data.get('start_date')
            end_date = sanitized_data.get('end_date')
            
            if not start_date or not end_date:
                return create_secure_response(400, {
                    'error': 'start_date and end_date are required for CSR trend report'
                })
            
            result = reporting_service.generate_csr_trend_report(
                hospital_id=hospital_id,
                start_date=start_date,
                end_date=end_date
            )
            
        elif report_type == 'rejection_analysis':
            start_date = sanitized_data.get('start_date')
            end_date = sanitized_data.get('end_date')
            
            if not start_date or not end_date:
                return create_secure_response(400, {
                    'error': 'start_date and end_date are required for rejection analysis'
                })
            
            result = reporting_service.generate_rejection_analysis_report(
                hospital_id=hospital_id,
                start_date=start_date,
                end_date=end_date
            )
            
        elif report_type == 'benchmark':
            comparison_days = int(sanitized_data.get('comparison_period_days', 30))
            
            result = reporting_service.generate_benchmark_report(
                hospital_id=hospital_id,
                comparison_period_days=comparison_days
            )
            
        elif report_type == 'policy_clause_frequency':
            start_date = sanitized_data.get('start_date')
            end_date = sanitized_data.get('end_date')
            
            if not start_date or not end_date:
                return create_secure_response(400, {
                    'error': 'start_date and end_date are required for policy clause frequency'
                })
            
            result = reporting_service.generate_policy_clause_frequency_report(
                hospital_id=hospital_id,
                start_date=start_date,
                end_date=end_date
            )
            
        elif report_type == 'processing_time':
            start_date = sanitized_data.get('start_date')
            end_date = sanitized_data.get('end_date')
            
            if not start_date or not end_date:
                return create_secure_response(400, {
                    'error': 'start_date and end_date are required for processing time metrics'
                })
            
            result = metrics_service.track_processing_time_improvement(
                hospital_id=hospital_id,
                start_date=start_date,
                end_date=end_date
            )
            
        elif report_type == 'cost_savings':
            start_date = sanitized_data.get('start_date')
            end_date = sanitized_data.get('end_date')
            
            if not start_date or not end_date:
                return create_secure_response(400, {
                    'error': 'start_date and end_date are required for cost savings'
                })
            
            result = metrics_service.calculate_cost_savings(
                hospital_id=hospital_id,
                start_date=start_date,
                end_date=end_date
            )
            
        else:
            return create_secure_response(400, {
                'error': f'Unknown report type: {report_type}'
            })
        
        if not result.get('success', True):
            return create_secure_response(400, {
                'error': result.get('error', 'Report generation failed')
            })
        
        return create_secure_response(200, {
            'message': 'Report generated successfully',
            'data': result
        })
        
    except json.JSONDecodeError:
        return create_secure_response(400, {
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        print(f"Error in reports handler: {str(e)}")
        return create_secure_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })
