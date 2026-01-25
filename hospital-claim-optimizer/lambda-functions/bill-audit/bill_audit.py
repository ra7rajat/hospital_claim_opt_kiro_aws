"""
Bill Audit Engine Lambda Function
Processes medical bills and validates against policy rules
"""
import json
import os
import time
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Add common layer to path
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission, audit_action, require_hospital_access
from security_config import create_secure_response, validate_input_data, check_rate_limit
from database_access import DynamoDBAccessLayer
from data_models import Claim, ClaimItem, AuditStatus, ClaimStatus, RiskLevel
from common_utils import generate_id, get_timestamp
from policy_service import PolicyService
from audit_service import AuditResultsService
from alert_service import AlertService

# Initialize Bedrock client
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'RevenueZ_Main')
BILLS_BUCKET = os.environ.get('BILLS_BUCKET', '')

# Initialize DynamoDB client
db_client = DynamoDBAccessLayer(TABLE_NAME)
policy_service = PolicyService(db_client)
audit_results_service = AuditResultsService(db_client)
alert_service = AlertService(db_client)

class AIAuditAnalyzer:
    """AI-powered audit analysis using Amazon Bedrock"""
    
    def __init__(self):
        self.bedrock_client = bedrock_runtime
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def analyze_rejected_items(
        self,
        rejected_items: List[Dict[str, Any]],
        policy_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to analyze rejected items and provide optimization suggestions
        """
        if not rejected_items:
            return {
                'suggestions': [],
                'predicted_improvement': 0.0
            }
        
        # Prepare prompt for Claude
        prompt = self._create_optimization_prompt(rejected_items, policy_rules)
        
        try:
            # Call Bedrock
            response = self._invoke_bedrock(prompt)
            
            # Parse AI response
            analysis = self._parse_ai_response(response)
            
            return analysis
            
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {
                'suggestions': [],
                'predicted_improvement': 0.0,
                'error': str(e)
            }
    
    def validate_procedure_bundling(
        self,
        line_items: List[Dict[str, Any]],
        policy_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for procedure bundling violations using AI
        """
        # Prepare prompt for bundling analysis
        prompt = self._create_bundling_prompt(line_items, policy_rules)
        
        try:
            response = self._invoke_bedrock(prompt)
            bundling_analysis = self._parse_bundling_response(response)
            
            return bundling_analysis
            
        except Exception as e:
            print(f"Error in bundling analysis: {str(e)}")
            return {
                'bundling_violations': [],
                'bundling_opportunities': []
            }
    
    def predict_settlement_ratio(
        self,
        audit_results: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Predict settlement ratio using AI analysis
        """
        # Simple calculation based on approved vs total
        total_amount = audit_results.get('total_amount', 0.0)
        approved_amount = audit_results.get('approved_amount', 0.0)
        
        if total_amount == 0:
            return 0.0
        
        base_ratio = approved_amount / total_amount
        
        # AI enhancement: adjust based on review items and historical patterns
        review_items = audit_results.get('review_items', 0)
        
        if review_items > 0:
            # Assume 70% of review items will be approved
            review_amount = total_amount - approved_amount - audit_results.get('rejected_amount', 0.0)
            estimated_additional = review_amount * 0.7
            predicted_ratio = (approved_amount + estimated_additional) / total_amount
        else:
            predicted_ratio = base_ratio
        
        return min(predicted_ratio, 1.0)
    
    def _create_optimization_prompt(
        self,
        rejected_items: List[Dict[str, Any]],
        policy_rules: Dict[str, Any]
    ) -> str:
        """Create prompt for optimization suggestions"""
        items_text = "\n".join([
            f"- {item['description']}: ${item['cost']:.2f} (Reason: {item['rejection_reason']})"
            for item in rejected_items
        ])
        
        prompt = f"""You are a medical billing optimization expert. Analyze the following rejected claim items and provide specific, actionable suggestions to improve claim approval rates.

Rejected Items:
{items_text}

Policy Rules Summary:
{json.dumps(policy_rules, indent=2)}

Please provide:
1. Specific optimization suggestions for each rejected item
2. Alternative procedures or coding that might be covered
3. Documentation requirements that could support approval
4. Estimated improvement in settlement ratio if suggestions are implemented

Format your response as JSON with this structure:
{{
    "suggestions": [
        {{
            "item_description": "...",
            "suggestion": "...",
            "alternative_approach": "...",
            "documentation_needed": "...",
            "estimated_approval_chance": 0.0-1.0
        }}
    ],
    "predicted_improvement": 0.0-1.0,
    "overall_strategy": "..."
}}"""
        
        return prompt
    
    def _create_bundling_prompt(
        self,
        line_items: List[Dict[str, Any]],
        policy_rules: Dict[str, Any]
    ) -> str:
        """Create prompt for bundling analysis"""
        items_text = "\n".join([
            f"- {item['description']}: ${item['cost']:.2f} (Code: {item.get('procedure_code', 'N/A')})"
            for item in line_items
        ])
        
        prompt = f"""You are a medical billing expert. Analyze the following claim items for procedure bundling violations and opportunities.

Claim Items:
{items_text}

Identify:
1. Procedures that should be bundled together (violations if billed separately)
2. Procedures that are correctly bundled
3. Opportunities to bundle procedures for better reimbursement

Format your response as JSON:
{{
    "bundling_violations": [
        {{
            "procedures": ["...", "..."],
            "issue": "...",
            "correct_approach": "..."
        }}
    ],
    "bundling_opportunities": [
        {{
            "procedures": ["...", "..."],
            "benefit": "...",
            "estimated_savings": 0.0
        }}
    ]
}}"""
        
        return prompt
    
    def _invoke_bedrock(self, prompt: str) -> str:
        """Invoke Bedrock Claude model"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for optimization suggestions"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: return structured response
                return {
                    'suggestions': [],
                    'predicted_improvement': 0.0,
                    'overall_strategy': response
                }
        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            return {
                'suggestions': [],
                'predicted_improvement': 0.0,
                'error': str(e)
            }
    
    def _parse_bundling_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for bundling analysis"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    'bundling_violations': [],
                    'bundling_opportunities': []
                }
        except Exception as e:
            print(f"Error parsing bundling response: {str(e)}")
            return {
                'bundling_violations': [],
                'bundling_opportunities': []
            }

class BillAuditEngine:
    """Engine for auditing medical bills against policy rules"""
    
    def __init__(self, db_client: DynamoDBAccessLayer, policy_service: PolicyService):
        self.db_client = db_client
        self.policy_service = policy_service
        self.ai_analyzer = AIAuditAnalyzer()
    
    def audit_bill(
        self,
        hospital_id: str,
        patient_id: str,
        policy_id: str,
        line_items: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Audit a medical bill against policy rules
        
        Args:
            hospital_id: Hospital identifier
            patient_id: Patient identifier
            policy_id: Policy to audit against
            line_items: List of bill line items
            user_id: User performing the audit
        
        Returns:
            Audit results with approved/rejected items
        """
        start_time = time.time()
        
        # Get policy
        policy = self.policy_service.get_policy(hospital_id, policy_id)
        if not policy:
            return {
                'success': False,
                'error': f'Policy {policy_id} not found'
            }
        
        # Create claim
        claim_id = generate_id('clm')
        claim = Claim(
            claim_id=claim_id,
            patient_id=patient_id,
            hospital_id=hospital_id,
            status=ClaimStatus.DRAFT.value
        )
        
        # Audit each line item
        audit_results = []
        approved_items = []
        rejected_items = []
        review_items = []
        
        total_amount = 0.0
        approved_amount = 0.0
        rejected_amount = 0.0
        
        for idx, item_data in enumerate(line_items):
            item_id = generate_id('item')
            
            # Extract item details
            description = item_data.get('description', '')
            cost = float(item_data.get('cost', 0.0))
            category = item_data.get('category', 'other')
            procedure_code = item_data.get('procedure_code', '')
            
            total_amount += cost
            
            # Validate against policy
            validation_result = self._validate_line_item(
                item_data=item_data,
                policy=policy,
                claim_id=claim_id
            )
            
            # Create claim item
            claim_item = ClaimItem(
                item_id=item_id,
                claim_id=claim_id,
                description=description,
                cost=cost,
                category=category,
                procedure_code=procedure_code,
                audit_status=validation_result['status'],
                rejection_reason=validation_result.get('rejection_reason', ''),
                policy_clause_reference=validation_result.get('policy_clause', ''),
                optimization_suggestion=validation_result.get('optimization_suggestion', '')
            )
            
            # Store claim item
            self.db_client.put_item(claim_item.to_dynamodb_item())
            
            # Categorize results
            item_result = {
                'item_id': item_id,
                'description': description,
                'cost': cost,
                'category': category,
                'procedure_code': procedure_code,
                'status': validation_result['status'],
                'rejection_reason': validation_result.get('rejection_reason', ''),
                'policy_clause': validation_result.get('policy_clause', ''),
                'optimization_suggestion': validation_result.get('optimization_suggestion', '')
            }
            
            audit_results.append(item_result)
            
            if validation_result['status'] == AuditStatus.APPROVED.value:
                approved_items.append(item_result)
                approved_amount += cost
            elif validation_result['status'] == AuditStatus.REJECTED.value:
                rejected_items.append(item_result)
                rejected_amount += cost
            else:
                review_items.append(item_result)
        
        # Update claim with audit results
        claim.total_amount = total_amount
        claim.status = ClaimStatus.AUDITED.value
        claim.audit_results = {
            'total_items': len(line_items),
            'approved_items': len(approved_items),
            'rejected_items': len(rejected_items),
            'review_items': len(review_items),
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'rejected_amount': rejected_amount,
            'audit_date': get_timestamp(),
            'audited_by': user_id
        }
        
        # Calculate predicted settlement ratio
        if total_amount > 0:
            claim.predicted_settlement_ratio = approved_amount / total_amount
        else:
            claim.predicted_settlement_ratio = 0.0
        
        # AI-powered analysis for rejected items
        ai_analysis = {}
        bundling_analysis = {}
        
        if rejected_items:
            ai_analysis = self.ai_analyzer.analyze_rejected_items(
                rejected_items=rejected_items,
                policy_rules=policy.extracted_rules
            )
            
            # Update predicted settlement ratio with AI insights
            if 'predicted_improvement' in ai_analysis:
                improvement = ai_analysis['predicted_improvement']
                claim.predicted_settlement_ratio = min(
                    claim.predicted_settlement_ratio + improvement,
                    1.0
                )
        
        # Check for procedure bundling
        bundling_analysis = self.ai_analyzer.validate_procedure_bundling(
            line_items=line_items,
            policy_rules=policy.extracted_rules
        )
        
        # Add AI insights to audit results
        claim.audit_results['ai_optimization_suggestions'] = ai_analysis.get('suggestions', [])
        claim.audit_results['bundling_analysis'] = bundling_analysis
        claim.audit_results['overall_strategy'] = ai_analysis.get('overall_strategy', '')
        
        # Store claim
        self.db_client.put_item(claim.to_dynamodb_item())
        
        # Generate alerts based on audit results (if alert_service is available)
        try:
            alerts = alert_service.check_and_generate_alerts(
                hospital_id=hospital_id,
                claim_data=claim.to_dynamodb_item()
            )
        except Exception as e:
            print(f"Warning: Could not generate alerts: {str(e)}")
            alerts = []
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'claim_id': claim_id,
            'audit_results': {
                'total_items': len(line_items),
                'approved_items': len(approved_items),
                'rejected_items': len(rejected_items),
                'review_items': len(review_items),
                'total_amount': total_amount,
                'approved_amount': approved_amount,
                'rejected_amount': rejected_amount,
                'predicted_settlement_ratio': claim.predicted_settlement_ratio,
                'processing_time_seconds': processing_time,
                'ai_optimization_suggestions': ai_analysis.get('suggestions', []),
                'bundling_analysis': bundling_analysis,
                'overall_strategy': ai_analysis.get('overall_strategy', '')
            },
            'line_items': audit_results,
            'approved_items': approved_items,
            'rejected_items': rejected_items,
            'review_items': review_items
        }
    
    def _validate_line_item(
        self,
        item_data: Dict[str, Any],
        policy: Any,
        claim_id: str
    ) -> Dict[str, Any]:
        """
        Validate a single line item against policy rules
        
        Returns:
            Validation result with status and reasons
        """
        procedure_code = item_data.get('procedure_code', '')
        category = item_data.get('category', 'other')
        cost = float(item_data.get('cost', 0.0))
        description = item_data.get('description', '')
        
        # Get extracted rules from policy
        extracted_rules = policy.extracted_rules
        
        # Check for explicit exclusions
        exclusions = extracted_rules.get('procedure_exclusions', [])
        for exclusion in exclusions:
            exclusion_code = exclusion.get('procedure_code', '')
            exclusion_name = exclusion.get('procedure_name', '')
            
            if (procedure_code and procedure_code == exclusion_code) or \
               (exclusion_name.lower() in description.lower()):
                return {
                    'status': AuditStatus.REJECTED.value,
                    'rejection_reason': exclusion.get('exclusion_reason', 'Procedure not covered'),
                    'policy_clause': exclusion.get('clause_reference', 'Exclusions'),
                    'optimization_suggestion': f'Consider alternative procedure or patient payment'
                }
        
        # Check room rent cap
        if category == 'accommodation' or 'room' in description.lower():
            room_rent_cap = extracted_rules.get('room_rent_cap', {})
            if room_rent_cap:
                cap_type = room_rent_cap.get('type', 'percentage')
                cap_value = room_rent_cap.get('value', 1.0)
                
                # For simplicity, assume a base sum insured of 500000
                sum_insured = 500000
                max_room_rent = sum_insured * (cap_value / 100)
                
                if cost > max_room_rent:
                    return {
                        'status': AuditStatus.REJECTED.value,
                        'rejection_reason': f'Room rent exceeds cap of {cap_value}% of sum insured',
                        'policy_clause': 'Room Rent Limits',
                        'optimization_suggestion': f'Reduce room charges to {max_room_rent} or upgrade policy'
                    }
        
        # Check copay conditions
        copay_conditions = extracted_rules.get('copay_conditions', [])
        for copay in copay_conditions:
            copay_procedure = copay.get('procedure_type', '')
            copay_percentage = copay.get('copay_percentage', 0.0)
            
            if copay_procedure.lower() in category.lower() or \
               copay_procedure.lower() in description.lower():
                # Apply copay
                patient_responsibility = cost * (copay_percentage / 100)
                approved_amount = cost - patient_responsibility
                
                return {
                    'status': AuditStatus.APPROVED.value,
                    'rejection_reason': '',
                    'policy_clause': f'Copay: {copay_percentage}%',
                    'optimization_suggestion': f'Patient copay: {patient_responsibility:.2f}, Approved: {approved_amount:.2f}'
                }
        
        # Check for non-medical consumables
        non_medical_keywords = ['mask', 'gloves', 'sanitizer', 'tissue', 'soap']
        if any(keyword in description.lower() for keyword in non_medical_keywords):
            if category == 'consumables':
                return {
                    'status': AuditStatus.REJECTED.value,
                    'rejection_reason': 'Non-medical consumables not covered',
                    'policy_clause': 'Consumables Coverage',
                    'optimization_suggestion': 'Remove non-medical items from claim'
                }
        
        # Check for high-cost items requiring review
        if cost > 50000:
            return {
                'status': AuditStatus.REQUIRES_REVIEW.value,
                'rejection_reason': 'High-cost item requires manual review',
                'policy_clause': 'High-Value Claims',
                'optimization_suggestion': 'Provide detailed justification and supporting documents'
            }
        
        # Default: Approve
        return {
            'status': AuditStatus.APPROVED.value,
            'rejection_reason': '',
            'policy_clause': 'General Coverage',
            'optimization_suggestion': ''
        }
    
    def get_audit_results(self, claim_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get audit results for a claim"""
        # Get claim
        claim_item = self.db_client.get_item(f"PATIENT#{patient_id}", f"CLAIM#{claim_id}")
        if not claim_item:
            return None
        
        # Get claim items
        claim_items = self.db_client.query_items(f"CLAIM#{claim_id}", "ITEM#")
        
        return {
            'claim': claim_item,
            'line_items': claim_items
        }

# Initialize audit engine
audit_engine = BillAuditEngine(db_client, policy_service)

@require_auth([Permission.AUDIT_CLAIM])
@require_hospital_access
@audit_action("audit_bill", "claim")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for bill audit requests
    """
    try:
        # Rate limiting
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'unknown')
        
        if not check_rate_limit(user_id, limit=50):
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validate input
        required_fields = ['hospital_id', 'patient_id', 'policy_id', 'line_items']
        validation = validate_input_data(body, required_fields)
        
        if not validation['is_valid']:
            return create_secure_response(400, {
                'error': 'Invalid input',
                'details': validation['errors']
            })
        
        sanitized_data = validation['sanitized_data']
        
        # Extract parameters
        hospital_id = sanitized_data['hospital_id']
        patient_id = sanitized_data['patient_id']
        policy_id = sanitized_data['policy_id']
        line_items = sanitized_data['line_items']
        
        # Validate line items
        if not isinstance(line_items, list) or len(line_items) == 0:
            return create_secure_response(400, {
                'error': 'line_items must be a non-empty list'
            })
        
        # Perform audit
        result = audit_engine.audit_bill(
            hospital_id=hospital_id,
            patient_id=patient_id,
            policy_id=policy_id,
            line_items=line_items,
            user_id=user_id
        )
        
        if not result['success']:
            return create_secure_response(400, {
                'error': result.get('error', 'Audit failed')
            })
        
        return create_secure_response(200, {
            'message': 'Bill audit completed successfully',
            'data': result
        })
        
    except json.JSONDecodeError:
        return create_secure_response(400, {
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        print(f"Error in bill audit handler: {str(e)}")
        return create_secure_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })
