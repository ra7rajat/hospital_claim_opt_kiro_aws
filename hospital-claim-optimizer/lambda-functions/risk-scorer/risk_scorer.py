"""
Risk Scoring Lambda Function
Calculates risk scores for claims based on multiple factors
"""
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add common layer to path
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission, audit_action
from security_config import create_secure_response, validate_input_data, check_rate_limit
from database_access import DynamoDBAccessLayer
from data_models import Claim, RiskLevel, ClaimStatus
from common_utils import get_timestamp

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'RevenueZ_Main')

# Initialize DynamoDB client
db_client = DynamoDBAccessLayer(TABLE_NAME)

class RiskScoringEngine:
    """Engine for calculating claim risk scores"""
    
    # Risk scoring weights
    WEIGHTS = {
        'claim_amount': 0.25,
        'policy_complexity': 0.20,
        'procedure_count': 0.15,
        'rejection_history': 0.20,
        'documentation_completeness': 0.10,
        'procedure_combinations': 0.10
    }
    
    # Risk thresholds
    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
    
    def calculate_risk_score(
        self,
        claim_id: str,
        patient_id: str,
        hospital_id: str,
        claim_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a claim
        
        Args:
            claim_id: Claim identifier
            patient_id: Patient identifier
            hospital_id: Hospital identifier
            claim_data: Optional claim data (if not provided, will fetch from DB)
        
        Returns:
            Risk assessment with score, level, and explanations
        """
        # Get claim data if not provided
        if not claim_data:
            claim_data = self.db_client.get_item(
                f"PATIENT#{patient_id}",
                f"CLAIM#{claim_id}"
            )
            
            if not claim_data:
                return {
                    'success': False,
                    'error': f'Claim {claim_id} not found'
                }
        
        # Calculate individual risk factors
        risk_factors = {}
        
        # 1. Claim Amount Risk
        risk_factors['claim_amount'] = self._calculate_amount_risk(claim_data)
        
        # 2. Policy Complexity Risk
        risk_factors['policy_complexity'] = self._calculate_policy_complexity_risk(
            hospital_id,
            claim_data
        )
        
        # 3. Procedure Count Risk
        risk_factors['procedure_count'] = self._calculate_procedure_count_risk(claim_id)
        
        # 4. Rejection History Risk
        risk_factors['rejection_history'] = self._calculate_rejection_history_risk(
            patient_id,
            hospital_id
        )
        
        # 5. Documentation Completeness Risk
        risk_factors['documentation_completeness'] = self._calculate_documentation_risk(
            claim_data
        )
        
        # 6. Procedure Combinations Risk
        risk_factors['procedure_combinations'] = self._calculate_procedure_combination_risk(
            claim_id
        )
        
        # Calculate weighted risk score
        total_score = 0.0
        for factor, score in risk_factors.items():
            weight = self.WEIGHTS.get(factor, 0.0)
            total_score += score * weight
        
        # Normalize to 0-100 scale
        risk_score = int(total_score)
        
        # Determine risk level
        if risk_score >= self.HIGH_RISK_THRESHOLD:
            risk_level = RiskLevel.HIGH.value
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            risk_level = RiskLevel.MEDIUM.value
        else:
            risk_level = RiskLevel.LOW.value
        
        # Generate risk explanation
        explanation = self._generate_risk_explanation(risk_factors, risk_score, risk_level)
        
        # Update claim with risk information
        self._update_claim_risk(claim_id, patient_id, risk_score, risk_level)
        
        return {
            'success': True,
            'claim_id': claim_id,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'explanation': explanation,
            'recommendations': self._generate_recommendations(risk_level, risk_factors)
        }
    
    def _calculate_amount_risk(self, claim_data: Dict[str, Any]) -> float:
        """Calculate risk based on claim amount"""
        total_amount = claim_data.get('total_amount', 0.0)
        
        # Risk increases with claim amount
        if total_amount >= 500000:
            return 90.0
        elif total_amount >= 200000:
            return 70.0
        elif total_amount >= 100000:
            return 50.0
        elif total_amount >= 50000:
            return 30.0
        else:
            return 10.0
    
    def _calculate_policy_complexity_risk(
        self,
        hospital_id: str,
        claim_data: Dict[str, Any]
    ) -> float:
        """Calculate risk based on policy complexity"""
        # Get policy information
        # For now, use audit results as proxy for complexity
        audit_results = claim_data.get('audit_results', {})
        
        rejected_items = audit_results.get('rejected_items', 0)
        review_items = audit_results.get('review_items', 0)
        total_items = audit_results.get('total_items', 1)
        
        # Higher rejection/review rate indicates complex policy
        complexity_ratio = (rejected_items + review_items) / total_items
        
        return complexity_ratio * 100.0
    
    def _calculate_procedure_count_risk(self, claim_id: str) -> float:
        """Calculate risk based on number of procedures"""
        # Get claim items
        claim_items = self.db_client.query_items(f"CLAIM#{claim_id}", "ITEM#")
        
        item_count = len(claim_items)
        
        # Risk increases with procedure count
        if item_count >= 50:
            return 80.0
        elif item_count >= 30:
            return 60.0
        elif item_count >= 20:
            return 40.0
        elif item_count >= 10:
            return 20.0
        else:
            return 10.0
    
    def _calculate_rejection_history_risk(
        self,
        patient_id: str,
        hospital_id: str
    ) -> float:
        """Calculate risk based on patient's rejection history"""
        # Get patient's previous claims
        previous_claims = self.db_client.query_items(
            f"PATIENT#{patient_id}",
            "CLAIM#"
        )
        
        if len(previous_claims) <= 1:
            # No history, medium risk
            return 50.0
        
        # Calculate rejection rate
        rejected_count = 0
        total_count = 0
        
        for claim in previous_claims:
            status = claim.get('status', '')
            if status in ['REJECTED', 'PARTIALLY_APPROVED']:
                rejected_count += 1
            if status in ['APPROVED', 'REJECTED', 'PARTIALLY_APPROVED']:
                total_count += 1
        
        if total_count == 0:
            return 50.0
        
        rejection_rate = rejected_count / total_count
        
        return rejection_rate * 100.0
    
    def _calculate_documentation_risk(self, claim_data: Dict[str, Any]) -> float:
        """Calculate risk based on documentation completeness"""
        audit_results = claim_data.get('audit_results', {})
        
        # Check for review items (often indicate missing documentation)
        review_items = audit_results.get('review_items', 0)
        total_items = audit_results.get('total_items', 1)
        
        review_ratio = review_items / total_items
        
        return review_ratio * 100.0
    
    def _calculate_procedure_combination_risk(self, claim_id: str) -> float:
        """Calculate risk based on procedure combinations"""
        # Get claim items
        claim_items = self.db_client.query_items(f"CLAIM#{claim_id}", "ITEM#")
        
        # Check for high-risk combinations
        categories = set()
        high_cost_items = 0
        
        for item in claim_items:
            category = item.get('category', '')
            categories.add(category)
            
            cost = item.get('cost', 0.0)
            if cost > 50000:
                high_cost_items += 1
        
        # Multiple categories + high-cost items = higher risk
        category_risk = min(len(categories) * 10, 50)
        cost_risk = min(high_cost_items * 20, 50)
        
        return (category_risk + cost_risk) / 2
    
    def _generate_risk_explanation(
        self,
        risk_factors: Dict[str, float],
        risk_score: int,
        risk_level: str
    ) -> str:
        """Generate human-readable risk explanation"""
        # Find top risk factors
        sorted_factors = sorted(
            risk_factors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_factors = sorted_factors[:3]
        
        explanation = f"Risk Level: {risk_level} (Score: {risk_score}/100)\n\n"
        explanation += "Top Risk Factors:\n"
        
        factor_names = {
            'claim_amount': 'Claim Amount',
            'policy_complexity': 'Policy Complexity',
            'procedure_count': 'Number of Procedures',
            'rejection_history': 'Historical Rejection Rate',
            'documentation_completeness': 'Documentation Completeness',
            'procedure_combinations': 'Procedure Combinations'
        }
        
        for factor, score in top_factors:
            factor_name = factor_names.get(factor, factor)
            explanation += f"- {factor_name}: {score:.1f}/100\n"
        
        return explanation
    
    def _generate_recommendations(
        self,
        risk_level: str,
        risk_factors: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []
        
        if risk_level == RiskLevel.HIGH.value:
            recommendations.append("Conduct thorough pre-submission review")
            recommendations.append("Ensure all supporting documentation is complete")
            recommendations.append("Consider pre-authorization for high-value items")
        
        # Specific recommendations based on risk factors
        if risk_factors.get('claim_amount', 0) > 60:
            recommendations.append("Break down claim into smaller submissions if possible")
        
        if risk_factors.get('policy_complexity', 0) > 60:
            recommendations.append("Review policy exclusions and limitations carefully")
        
        if risk_factors.get('rejection_history', 0) > 60:
            recommendations.append("Address previous rejection reasons before resubmission")
        
        if risk_factors.get('documentation_completeness', 0) > 60:
            recommendations.append("Gather additional supporting documentation")
        
        if risk_factors.get('procedure_combinations', 0) > 60:
            recommendations.append("Verify procedure bundling rules")
        
        return recommendations
    
    def _update_claim_risk(
        self,
        claim_id: str,
        patient_id: str,
        risk_score: int,
        risk_level: str
    ) -> bool:
        """Update claim with risk information"""
        try:
            # Get current claim
            claim_data = self.db_client.get_item(
                f"PATIENT#{patient_id}",
                f"CLAIM#{claim_id}"
            )
            
            if not claim_data:
                return False
            
            # Update risk fields
            claim_data['risk_score'] = risk_score
            claim_data['risk_level'] = risk_level
            claim_data['risk_updated_at'] = get_timestamp()
            
            # Save updated claim
            return self.db_client.put_item(claim_data)
            
        except Exception as e:
            print(f"Error updating claim risk: {str(e)}")
            return False
    
    def calculate_aggregated_risk(
        self,
        patient_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Calculate aggregated risk across all patient claims
        
        Args:
            patient_id: Patient identifier
            hospital_id: Hospital identifier
        
        Returns:
            Aggregated risk assessment
        """
        # Get all claims for patient
        claims = self.db_client.query_items(
            f"PATIENT#{patient_id}",
            "CLAIM#"
        )
        
        if not claims:
            return {
                'success': False,
                'error': 'No claims found for patient'
            }
        
        # Calculate risk for each claim
        risk_scores = []
        high_risk_claims = []
        medium_risk_claims = []
        low_risk_claims = []
        
        for claim in claims:
            claim_id = claim.get('claim_id', '')
            if not claim_id:
                continue
            
            risk_result = self.calculate_risk_score(
                claim_id=claim_id,
                patient_id=patient_id,
                hospital_id=hospital_id,
                claim_data=claim
            )
            
            if risk_result['success']:
                risk_score = risk_result['risk_score']
                risk_level = risk_result['risk_level']
                
                risk_scores.append(risk_score)
                
                if risk_level == RiskLevel.HIGH.value:
                    high_risk_claims.append(claim_id)
                elif risk_level == RiskLevel.MEDIUM.value:
                    medium_risk_claims.append(claim_id)
                else:
                    low_risk_claims.append(claim_id)
        
        # Calculate aggregate statistics
        if risk_scores:
            avg_risk_score = sum(risk_scores) / len(risk_scores)
            max_risk_score = max(risk_scores)
            min_risk_score = min(risk_scores)
        else:
            avg_risk_score = 0
            max_risk_score = 0
            min_risk_score = 0
        
        # Determine overall risk level
        if avg_risk_score >= RiskScoringEngine.HIGH_RISK_THRESHOLD:
            overall_risk_level = RiskLevel.HIGH.value
        elif avg_risk_score >= RiskScoringEngine.MEDIUM_RISK_THRESHOLD:
            overall_risk_level = RiskLevel.MEDIUM.value
        else:
            overall_risk_level = RiskLevel.LOW.value
        
        return {
            'success': True,
            'patient_id': patient_id,
            'total_claims': len(claims),
            'average_risk_score': int(avg_risk_score),
            'max_risk_score': max_risk_score,
            'min_risk_score': min_risk_score,
            'overall_risk_level': overall_risk_level,
            'high_risk_claims': high_risk_claims,
            'medium_risk_claims': medium_risk_claims,
            'low_risk_claims': low_risk_claims,
            'risk_distribution': {
                'high': len(high_risk_claims),
                'medium': len(medium_risk_claims),
                'low': len(low_risk_claims)
            }
        }

# Initialize risk scoring engine
risk_engine = RiskScoringEngine(db_client)

@require_auth([Permission.AUDIT_CLAIM, Permission.VIEW_AUDIT_RESULTS])
@audit_action("calculate_risk", "claim")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for risk scoring requests
    """
    try:
        # Rate limiting
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'unknown')
        
        if not check_rate_limit(user_id, limit=100):
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Determine operation type
        operation = body.get('operation', 'calculate_risk')
        
        if operation == 'calculate_risk':
            # Single claim risk calculation
            required_fields = ['claim_id', 'patient_id', 'hospital_id']
            validation = validate_input_data(body, required_fields)
            
            if not validation['is_valid']:
                return create_secure_response(400, {
                    'error': 'Invalid input',
                    'details': validation['errors']
                })
            
            sanitized_data = validation['sanitized_data']
            
            result = risk_engine.calculate_risk_score(
                claim_id=sanitized_data['claim_id'],
                patient_id=sanitized_data['patient_id'],
                hospital_id=sanitized_data['hospital_id']
            )
            
        elif operation == 'aggregate_risk':
            # Aggregated risk calculation
            required_fields = ['patient_id', 'hospital_id']
            validation = validate_input_data(body, required_fields)
            
            if not validation['is_valid']:
                return create_secure_response(400, {
                    'error': 'Invalid input',
                    'details': validation['errors']
                })
            
            sanitized_data = validation['sanitized_data']
            
            result = risk_engine.calculate_aggregated_risk(
                patient_id=sanitized_data['patient_id'],
                hospital_id=sanitized_data['hospital_id']
            )
            
        else:
            return create_secure_response(400, {
                'error': f'Unknown operation: {operation}'
            })
        
        if not result['success']:
            return create_secure_response(400, {
                'error': result.get('error', 'Risk calculation failed')
            })
        
        return create_secure_response(200, {
            'message': 'Risk calculation completed successfully',
            'data': result
        })
        
    except json.JSONDecodeError:
        return create_secure_response(400, {
            'error': 'Invalid JSON in request body'
        })
    except Exception as e:
        print(f"Error in risk scoring handler: {str(e)}")
        return create_secure_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })
