"""
Eligibility Checker Lambda Function
Provides real-time treatment eligibility validation against policy rules
"""
import json
import os
from typing import Dict, Any, List, Optional
import sys
sys.path.append('/opt/python')

from common_utils import (
    DynamoDBClient, BedrockClient,
    create_response, get_timestamp
)
from auth_middleware import require_auth, audit_action, Permission
from security_config import create_secure_response, validate_input_data, check_rate_limit

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']

@require_auth([Permission.CHECK_ELIGIBILITY])
@audit_action("check_eligibility", "eligibility")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for eligibility checking
    """
    try:
        # Rate limiting check
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'anonymous')
        
        if not check_rate_limit(user_id, limit=60):  # 60 checks per minute
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Validate input data
        required_fields = ['patient_id']
        validation_result = validate_input_data(body, required_fields)
        
        if not validation_result['is_valid']:
            return create_secure_response(400, {
                'error': 'Invalid input data',
                'details': validation_result['errors']
            })
        
        # Use sanitized data
        body = validation_result['sanitized_data']
        
        patient_id = body.get('patient_id')
        procedure_codes = body.get('procedure_codes', [])
        procedure_name = body.get('procedure_name', '')
        diagnosis_codes = body.get('diagnosis_codes', [])
        treatment_date = body.get('treatment_date')
        provider_id = body.get('provider_id')
        room_category = body.get('room_category', 'general')
        
        if not procedure_codes and not procedure_name:
            return create_secure_response(400, {
                'error': 'Either procedure_codes or procedure_name is required'
            })
        
        # Initialize clients
        dynamodb_client = DynamoDBClient(TABLE_NAME)
        bedrock_client = BedrockClient()
        
        # Get patient information and associated policies
        patient_info = get_patient_policies(dynamodb_client, patient_id)
        if not patient_info:
            return create_secure_response(404, {
                'error': 'Patient not found or no active policies'
            })
        
        # Verify user can access this patient's data
        patient_hospital_id = patient_info['patient_info'].get('hospital_id')
        user_hospital_id = user_info.get('hospital_id')
        
        if patient_hospital_id != user_hospital_id:
            return create_secure_response(403, {
                'error': 'Access denied: You can only check eligibility for patients in your hospital'
            })
        
        # Check eligibility against all active policies
        eligibility_results = []
        
        for policy in patient_info['policies']:
            result = check_procedure_eligibility(
                policy, procedure_name, procedure_codes, room_category, bedrock_client
            )
            eligibility_results.append(result)
        
        # Determine overall eligibility status
        overall_status = determine_overall_status(eligibility_results)
        
        # Generate response
        response_data = {
            'patient_id': patient_id,
            'procedure_name': procedure_name,
            'procedure_codes': procedure_codes,
            'room_category': room_category,
            'overall_status': overall_status['status'],
            'message': overall_status['message'],
            'policy_results': eligibility_results,
            'timestamp': get_timestamp(),
            'checked_by': user_id
        }
        
        # Add pre-authorization template if needed
        if overall_status.get('pre_auth_required'):
            template = generate_preauth_template(
                procedure_name, overall_status.get('requirements', []), bedrock_client
            )
            response_data['pre_authorization_template'] = template
        
        return create_secure_response(200, response_data)
        
    except Exception as e:
        return create_secure_response(500, {
            'error': f'Internal server error: {str(e)}'
        })

def get_patient_policies(dynamodb_client: DynamoDBClient, patient_id: str) -> Optional[Dict[str, Any]]:
    """Get patient information and associated active policies"""
    try:
        # First, find the patient record to get hospital_id
        # In a real implementation, you'd have a GSI for patient lookups
        # For now, we'll simulate finding the patient
        
        # This is a simplified approach - in production you'd have proper indexing
        patient_item = dynamodb_client.get_item(f'PATIENT#{patient_id}', 'METADATA')
        if not patient_item:
            return None
        
        hospital_id = patient_item.get('hospital_id')
        active_policy_ids = patient_item.get('active_policies', [])
        
        # Get all active policies for this patient
        policies = []
        for policy_id in active_policy_ids:
            policy = dynamodb_client.get_item(f'HOSPITAL#{hospital_id}', f'POLICY#{policy_id}')
            if policy and policy.get('extraction_status') == 'COMPLETED':
                policies.append(policy)
        
        return {
            'patient_info': patient_item,
            'policies': policies
        }
        
    except Exception as e:
        print(f"Error getting patient policies: {str(e)}")
        return None

def check_procedure_eligibility(
    policy: Dict[str, Any], 
    procedure_name: str, 
    procedure_codes: List[str],
    room_category: str,
    bedrock_client: BedrockClient
) -> Dict[str, Any]:
    """Check procedure eligibility against a specific policy"""
    
    extracted_rules = policy.get('extracted_rules', {})
    policy_id = policy.get('policy_id')
    
    # Use Bedrock to analyze eligibility
    eligibility_prompt = f"""
You are a rigid Insurance Adjudicator. Analyze the following procedure against the policy rules:

Procedure: {procedure_name}
Procedure Codes: {procedure_codes}
Room Category: {room_category}

Policy Rules:
{json.dumps(extracted_rules, indent=2)}

Determine:
1. Is this procedure covered?
2. What is the coverage percentage?
3. Are there any exclusions that apply?
4. Is pre-authorization required?
5. What is the patient's financial responsibility?
6. Are there any specific documentation requirements?

Respond in JSON format:
{{
    "coverage_status": "COVERED|PARTIALLY_COVERED|NOT_COVERED|REQUIRES_REVIEW",
    "coverage_percentage": number,
    "patient_responsibility_percentage": number,
    "exclusions_apply": boolean,
    "exclusion_reasons": ["string"],
    "pre_auth_required": boolean,
    "documentation_required": ["string"],
    "policy_clause_references": ["string"],
    "room_rent_applicable": boolean,
    "room_rent_coverage": {{
        "covered_amount": number,
        "patient_pays": number,
        "explanation": "string"
    }},
    "warnings": ["string"],
    "alternatives": ["string"],
    "confidence_score": number
}}
"""
    
    try:
        analysis_result = bedrock_client.invoke_claude(eligibility_prompt)
        if analysis_result:
            eligibility_data = json.loads(analysis_result)
            eligibility_data['policy_id'] = policy_id
            eligibility_data['policy_name'] = policy.get('policy_name')
            return eligibility_data
        else:
            return {
                'policy_id': policy_id,
                'coverage_status': 'REQUIRES_REVIEW',
                'error': 'Analysis failed',
                'confidence_score': 0.0
            }
    except json.JSONDecodeError:
        return {
            'policy_id': policy_id,
            'coverage_status': 'REQUIRES_REVIEW',
            'error': 'Invalid analysis response',
            'confidence_score': 0.0
        }
    except Exception as e:
        return {
            'policy_id': policy_id,
            'coverage_status': 'REQUIRES_REVIEW',
            'error': f'Analysis error: {str(e)}',
            'confidence_score': 0.0
        }

def determine_overall_status(eligibility_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Determine overall eligibility status from multiple policy results"""
    
    if not eligibility_results:
        return {
            'status': 'ERROR',
            'message': 'No policy results available',
            'pre_auth_required': False
        }
    
    # Find the best coverage option
    covered_policies = [r for r in eligibility_results if r.get('coverage_status') == 'COVERED']
    partially_covered = [r for r in eligibility_results if r.get('coverage_status') == 'PARTIALLY_COVERED']
    
    if covered_policies:
        best_policy = max(covered_policies, key=lambda x: x.get('coverage_percentage', 0))
        return {
            'status': 'COVERED',
            'message': f"Procedure is covered under {best_policy.get('policy_name')} with {best_policy.get('coverage_percentage', 0)}% coverage",
            'pre_auth_required': best_policy.get('pre_auth_required', False),
            'requirements': best_policy.get('documentation_required', [])
        }
    
    elif partially_covered:
        best_policy = max(partially_covered, key=lambda x: x.get('coverage_percentage', 0))
        return {
            'status': 'PARTIALLY_COVERED',
            'message': f"Procedure is partially covered under {best_policy.get('policy_name')} with {best_policy.get('coverage_percentage', 0)}% coverage",
            'pre_auth_required': best_policy.get('pre_auth_required', False),
            'requirements': best_policy.get('documentation_required', [])
        }
    
    else:
        # Check for exclusions or warnings
        exclusions = []
        warnings = []
        alternatives = []
        
        for result in eligibility_results:
            exclusions.extend(result.get('exclusion_reasons', []))
            warnings.extend(result.get('warnings', []))
            alternatives.extend(result.get('alternatives', []))
        
        message = "Procedure is not covered."
        if exclusions:
            message += f" Exclusions: {', '.join(set(exclusions))}"
        if alternatives:
            message += f" Consider alternatives: {', '.join(set(alternatives))}"
        
        return {
            'status': 'NOT_COVERED',
            'message': message,
            'pre_auth_required': False,
            'exclusions': list(set(exclusions)),
            'alternatives': list(set(alternatives))
        }

def generate_preauth_template(
    procedure_name: str, 
    requirements: List[str], 
    bedrock_client: BedrockClient
) -> Optional[str]:
    """Generate pre-authorization documentation template"""
    
    template_prompt = f"""
Generate a pre-authorization documentation template for the following procedure:

Procedure: {procedure_name}
Required Documentation: {', '.join(requirements)}

Create a professional medical pre-authorization template that includes:
1. Patient information fields
2. Procedure justification section
3. Medical necessity documentation
4. Required clinical information
5. Provider attestation

Format as a structured document template.
"""
    
    try:
        template = bedrock_client.invoke_claude(template_prompt)
        return template
    except Exception as e:
        print(f"Error generating pre-auth template: {str(e)}")
        return None