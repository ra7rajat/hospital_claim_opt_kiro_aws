"""
Patient Profile Lambda Function

Handles patient profile aggregation and retrieval.

Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5
"""
import json
import os
from typing import Dict, Any
import sys

# Add lambda layer to path
sys.path.append('/opt/python')

from patient_profile_service import PatientProfileService


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for patient profile operations
    
    Endpoints:
    - GET /patients/{patient_id}/profile - Get complete patient profile
    - GET /patients/{patient_id}/claims - Get patient claims with sorting
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters', {})
        query_parameters = event.get('queryStringParameters', {}) or {}
        
        patient_id = path_parameters.get('patient_id')
        
        if not patient_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Patient ID is required'
                })
            }
        
        # Initialize service
        service = PatientProfileService()
        
        # Route to appropriate handler
        if http_method == 'GET' and '/profile' in path:
            return handle_get_profile(service, patient_id)
        elif http_method == 'GET' and '/claims' in path:
            return handle_get_claims(service, patient_id, query_parameters)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Endpoint not found'
                })
            }
    
    except Exception as e:
        print(f"Error in patient profile handler: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_get_profile(service: PatientProfileService, patient_id: str) -> Dict[str, Any]:
    """
    Get complete patient profile
    
    Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5
    """
    try:
        profile = service.get_patient_profile(patient_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(profile.to_dict())
        }
    
    except Exception as e:
        print(f"Error getting patient profile: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get patient profile',
                'message': str(e)
            })
        }


def handle_get_claims(
    service: PatientProfileService,
    patient_id: str,
    query_parameters: Dict[str, str]
) -> Dict[str, Any]:
    """
    Get patient claims with sorting
    
    Requirements: 5.1.4
    
    Query parameters:
    - sort_by: Field to sort by (date, amount, status, risk_score)
    - sort_order: Sort order (asc, desc)
    """
    try:
        sort_by = query_parameters.get('sort_by', 'date')
        sort_order = query_parameters.get('sort_order', 'desc')
        
        claims = service.get_patient_claims_sorted(patient_id, sort_by, sort_order)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'patient_id': patient_id,
                'claims': claims,
                'total': len(claims)
            })
        }
    
    except Exception as e:
        print(f"Error getting patient claims: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to get patient claims',
                'message': str(e)
            })
        }
