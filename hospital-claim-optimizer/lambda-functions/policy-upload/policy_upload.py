"""
Policy Upload Handler Lambda Function
Handles policy PDF uploads, OCR processing, and policy rule extraction
"""
import json
import os
from typing import Dict, Any
import sys
sys.path.append('/opt/python')

from common_utils import (
    DynamoDBClient, S3Client, TextractClient, BedrockClient,
    create_response, generate_id, get_timestamp, extract_text_from_textract
)
from auth_middleware import require_auth, require_hospital_access, audit_action, Permission
from security_config import create_secure_response, validate_input_data, check_rate_limit

# Environment variables
TABLE_NAME = os.environ['TABLE_NAME']
POLICY_BUCKET = os.environ['POLICY_BUCKET']

@require_auth([Permission.UPLOAD_POLICY])
@require_hospital_access
@audit_action("upload_policy", "policy")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for policy upload and processing
    """
    try:
        # Rate limiting check
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'anonymous')
        
        if not check_rate_limit(user_id, limit=10):  # 10 uploads per minute
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Validate input data
        required_fields = ['hospital_id', 'policy_name']
        validation_result = validate_input_data(body, required_fields)
        
        if not validation_result['is_valid']:
            return create_secure_response(400, {
                'error': 'Invalid input data',
                'details': validation_result['errors']
            })
        
        # Use sanitized data
        body = validation_result['sanitized_data']
        
        hospital_id = body.get('hospital_id')
        policy_name = body.get('policy_name')
        file_size = body.get('file_size', 0)
        content_type = body.get('content_type', 'application/pdf')
        
        # Validate file size (50MB limit)
        if file_size > 50 * 1024 * 1024:
            return create_secure_response(400, {
                'error': 'File size exceeds 50MB limit'
            })
        
        # Validate content type
        if content_type != 'application/pdf':
            return create_secure_response(400, {
                'error': 'Only PDF files are supported'
            })
        
        # Generate policy ID and S3 key
        policy_id = generate_id('pol')
        s3_key = f"policies/{hospital_id}/{policy_id}.pdf"
        
        # Initialize clients
        s3_client = S3Client()
        dynamodb_client = DynamoDBClient(TABLE_NAME)
        
        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(POLICY_BUCKET, s3_key)
        if not presigned_url:
            return create_secure_response(500, {
                'error': 'Failed to generate upload URL'
            })
        
        # Store initial policy record in DynamoDB
        timestamp = get_timestamp()
        policy_item = {
            'PK': f'HOSPITAL#{hospital_id}',
            'SK': f'POLICY#{policy_id}',
            'policy_id': policy_id,
            'policy_name': policy_name,
            'hospital_id': hospital_id,
            'file_size': file_size,
            'content_type': content_type,
            's3_key': s3_key,
            'extraction_status': 'PENDING_UPLOAD',
            'created_at': timestamp,
            'updated_at': timestamp,
            'created_by': user_id,
            'version': 1,
            'GSI1PK': f'POLICY#{policy_id}',
            'GSI1SK': timestamp
        }
        
        success = dynamodb_client.put_item(policy_item)
        if not success:
            return create_secure_response(500, {
                'error': 'Failed to store policy record'
            })
        
        return create_secure_response(200, {
            'policy_id': policy_id,
            'upload_url': presigned_url,
            'message': 'Upload URL generated successfully. Upload your PDF to begin processing.',
            'expires_in': 3600  # 1 hour
        })
        
    except Exception as e:
        return create_secure_response(500, {
            'error': f'Internal server error: {str(e)}'
        })

def process_uploaded_policy(policy_id: str, hospital_id: str, s3_key: str) -> Dict[str, Any]:
    """
    Process uploaded policy PDF - extract text and rules
    This would typically be triggered by S3 event
    """
    try:
        # Initialize clients
        dynamodb_client = DynamoDBClient(TABLE_NAME)
        textract_client = TextractClient()
        bedrock_client = BedrockClient()
        
        # Update status to processing
        policy_item = dynamodb_client.get_item(f'HOSPITAL#{hospital_id}', f'POLICY#{policy_id}')
        if not policy_item:
            return {'error': 'Policy not found'}
        
        policy_item['extraction_status'] = 'PROCESSING'
        policy_item['updated_at'] = get_timestamp()
        dynamodb_client.put_item(policy_item)
        
        # Extract text using Textract
        textract_response = textract_client.analyze_document(POLICY_BUCKET, s3_key)
        if not textract_response:
            policy_item['extraction_status'] = 'FAILED'
            policy_item['error_message'] = 'Textract analysis failed'
            dynamodb_client.put_item(policy_item)
            return {'error': 'OCR processing failed'}
        
        # Extract plain text
        extracted_text = extract_text_from_textract(textract_response)
        
        # Use Bedrock to extract policy rules
        policy_extraction_prompt = f"""
You are a Healthcare Policy Analyst. Extract the following constraints from this insurance document:

1. Room Rent Capping (Numerical amount or Percentage of Sum Insured)
2. Co-pay conditions and percentages
3. Specific Procedure Exclusions (e.g., Robotic Surgery, Cosmetic procedures)
4. Coverage limits and deductibles
5. Pre-authorization requirements
6. General exclusions and waiting periods

Document Text:
{extracted_text[:8000]}  # Limit text to avoid token limits

Output strictly in JSON format with the following structure:
{{
    "room_rent_cap": {{
        "type": "percentage|fixed_amount",
        "value": number,
        "description": "string"
    }},
    "copay_conditions": [
        {{
            "procedure_type": "string",
            "copay_percentage": number,
            "description": "string"
        }}
    ],
    "procedure_exclusions": [
        {{
            "procedure_name": "string",
            "exclusion_reason": "string",
            "clause_reference": "string"
        }}
    ],
    "coverage_limits": {{
        "annual_limit": number,
        "lifetime_limit": number,
        "per_incident_limit": number
    }},
    "pre_authorization_required": [
        {{
            "procedure_type": "string",
            "threshold_amount": number,
            "documentation_required": ["string"]
        }}
    ],
    "general_exclusions": ["string"],
    "waiting_periods": {{
        "general": number,
        "pre_existing_conditions": number,
        "specific_procedures": [
            {{
                "procedure": "string",
                "waiting_period_days": number
            }}
        ]
    }},
    "extraction_confidence": number
}}
"""
        
        extracted_rules = bedrock_client.invoke_claude(policy_extraction_prompt)
        if not extracted_rules:
            policy_item['extraction_status'] = 'FAILED'
            policy_item['error_message'] = 'Policy rule extraction failed'
            dynamodb_client.put_item(policy_item)
            return {'error': 'Policy rule extraction failed'}
        
        try:
            # Parse extracted rules JSON
            rules_data = json.loads(extracted_rules)
            
            # Update policy item with extracted rules
            policy_item['extraction_status'] = 'COMPLETED'
            policy_item['extracted_rules'] = rules_data
            policy_item['raw_text'] = extracted_text[:5000]  # Store truncated text
            policy_item['extraction_confidence'] = rules_data.get('extraction_confidence', 0.8)
            policy_item['updated_at'] = get_timestamp()
            
            success = dynamodb_client.put_item(policy_item)
            if success:
                return {
                    'policy_id': policy_id,
                    'extraction_status': 'COMPLETED',
                    'extracted_rules': rules_data
                }
            else:
                return {'error': 'Failed to store extracted rules'}
                
        except json.JSONDecodeError:
            policy_item['extraction_status'] = 'FAILED'
            policy_item['error_message'] = 'Invalid JSON in extracted rules'
            policy_item['raw_extraction'] = extracted_rules
            dynamodb_client.put_item(policy_item)
            return {'error': 'Invalid policy rules format'}
        
    except Exception as e:
        return {'error': f'Processing error: {str(e)}'}