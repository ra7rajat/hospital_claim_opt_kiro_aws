"""
Risk Recommendation Engine

Generates actionable recommendations to reduce patient risk
and improve settlement ratios.

Requirements: 5.3.1, 5.3.2, 5.3.3, 5.3.4, 5.3.5
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key


class Recommendation:
    """Risk mitigation recommendation"""
    
    def __init__(
        self,
        recommendation_id: str,
        priority: str,
        title: str,
        description: str,
        action_steps: List[str],
        expected_impact: float,
        effort: str,
        category: str
    ):
        self.recommendation_id = recommendation_id
        self.priority = priority
        self.title = title
        self.description = description
        self.action_steps = action_steps
        self.expected_impact = expected_impact
        self.effort = effort
        self.category = category
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'recommendation_id': self.recommendation_id,
            'priority': self.priority,
            'title': self.title,
            'description': self.description,
            'action_steps': self.action_steps,
            'expected_impact': self.expected_impact,
            'effort': self.effort,
            'category': self.category
        }


class RiskRecommendationService:
    """Service for generating risk mitigation recommendations"""
    
    def __init__(self, dynamodb_client=None, table_name: str = 'HospitalClaimOptimizer'):
        self.dynamodb = dynamodb_client or boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def generate_recommendations(
        self,
        patient_id: str,
        risk_factors: Dict[str, Any],
        claims: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations to reduce risk
        
        Requirements: 5.3.1, 5.3.2, 5.3.3, 5.3.4
        
        Args:
            patient_id: Patient ID
            risk_factors: Risk factors from aggregated risk calculation
            claims: List of patient claims
        
        Returns:
            List of recommendations prioritized by impact
        """
        recommendations = []
        
        # Analyze risk factors and generate recommendations
        for factor in risk_factors.get('factors', []):
            factor_name = factor.get('name')
            factor_value = factor.get('value', 0)
            
            if factor_name == 'Total Claim Amount' and factor_value > 60:
                recommendations.append(self._recommend_claim_consolidation(patient_id, claims))
            
            if factor_name == 'Settlement Ratio' and factor_value > 50:
                recommendations.append(self._recommend_documentation_improvement(patient_id, claims))
            
            if factor_name == 'High-Risk Claims' and factor_value > 40:
                recommendations.append(self._recommend_pre_authorization(patient_id, claims))
            
            if factor_name == 'Rejection Rate' and factor_value > 30:
                recommendations.append(self._recommend_policy_review(patient_id, claims))
            
            if factor_name == 'Policy Complexity' and factor_value > 50:
                recommendations.append(self._recommend_policy_simplification(patient_id, claims))
        
        # Add general recommendations based on claim patterns
        recommendations.extend(self._analyze_claim_patterns(patient_id, claims))
        
        # Remove None values and duplicates
        recommendations = [r for r in recommendations if r is not None]
        recommendations = self._deduplicate_recommendations(recommendations)
        
        # Sort by priority and expected impact
        recommendations.sort(
            key=lambda r: (
                {'high': 0, 'medium': 1, 'low': 2}[r.priority],
                -r.expected_impact
            )
        )
        
        return recommendations
    
    def _recommend_claim_consolidation(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> Optional[Recommendation]:
        """Recommend consolidating multiple small claims"""
        small_claims = [c for c in claims if c.get('amount', 0) < 50000]
        
        if len(small_claims) >= 3:
            return Recommendation(
                recommendation_id=f'REC-{patient_id}-CONSOLIDATE',
                priority='high',
                title='Consolidate Multiple Small Claims',
                description=f'Patient has {len(small_claims)} small claims that could be consolidated to reduce processing overhead and improve settlement ratios.',
                action_steps=[
                    'Review all pending small claims for this patient',
                    'Identify claims that can be combined under a single treatment episode',
                    'Submit consolidated claim with comprehensive documentation',
                    'Follow up with TPA to ensure faster processing'
                ],
                expected_impact=15.0,
                effort='medium',
                category='claim_optimization'
            )
        return None
    
    def _recommend_documentation_improvement(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> Optional[Recommendation]:
        """Recommend improving claim documentation"""
        low_settlement = [c for c in claims if c.get('settlement_ratio', 1.0) < 0.7]
        
        if len(low_settlement) >= 2:
            return Recommendation(
                recommendation_id=f'REC-{patient_id}-DOCUMENTATION',
                priority='high',
                title='Improve Claim Documentation',
                description=f'{len(low_settlement)} claims have low settlement ratios, likely due to insufficient documentation.',
                action_steps=[
                    'Review rejected or partially settled claims',
                    'Identify missing medical records or supporting documents',
                    'Obtain additional documentation from treating physicians',
                    'Resubmit claims with complete documentation package',
                    'Implement documentation checklist for future claims'
                ],
                expected_impact=20.0,
                effort='medium',
                category='documentation'
            )
        return None
    
    def _recommend_pre_authorization(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> Optional[Recommendation]:
        """Recommend obtaining pre-authorization for high-risk procedures"""
        high_risk = [c for c in claims if c.get('risk_score', 0) > 70]
        
        if len(high_risk) >= 1:
            return Recommendation(
                recommendation_id=f'REC-{patient_id}-PREAUTH',
                priority='high',
                title='Obtain Pre-Authorization for High-Risk Procedures',
                description=f'{len(high_risk)} high-risk claims detected. Pre-authorization can significantly improve approval rates.',
                action_steps=[
                    'Identify upcoming procedures requiring pre-authorization',
                    'Submit pre-authorization requests 7-10 days before procedure',
                    'Include detailed medical necessity documentation',
                    'Follow up with TPA to ensure approval before procedure date',
                    'Keep patient informed of authorization status'
                ],
                expected_impact=25.0,
                effort='low',
                category='pre_authorization'
            )
        return None
    
    def _recommend_policy_review(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> Optional[Recommendation]:
        """Recommend reviewing policy coverage"""
        rejected = [c for c in claims if c.get('status') == 'rejected']
        
        if len(rejected) >= 2:
            # Analyze rejection reasons
            rejection_reasons = {}
            for claim in rejected:
                reason = claim.get('rejection_reason', 'Unknown')
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
            
            most_common_reason = max(rejection_reasons.items(), key=lambda x: x[1])[0] if rejection_reasons else 'Unknown'
            
            return Recommendation(
                recommendation_id=f'REC-{patient_id}-POLICY',
                priority='medium',
                title='Review Policy Coverage and Exclusions',
                description=f'{len(rejected)} claims rejected. Most common reason: {most_common_reason}. Policy review may prevent future rejections.',
                action_steps=[
                    'Schedule meeting with patient to review policy coverage',
                    'Identify procedures not covered by current policy',
                    'Discuss alternative treatment options covered by policy',
                    'Consider policy upgrade if frequent rejections occur',
                    'Educate patient on policy limitations and exclusions'
                ],
                expected_impact=18.0,
                effort='high',
                category='policy_review'
            )
        return None
    
    def _recommend_policy_simplification(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> Optional[Recommendation]:
        """Recommend simplifying policy structure"""
        unique_procedures = len(set(
            proc for claim in claims 
            for proc in claim.get('procedure_codes', [])
        ))
        
        if unique_procedures > 15:
            return Recommendation(
                recommendation_id=f'REC-{patient_id}-SIMPLIFY',
                priority='low',
                title='Simplify Treatment Plan',
                description=f'Patient has {unique_procedures} different procedure types, indicating complex treatment. Simplification may reduce administrative burden.',
                action_steps=[
                    'Review all procedures with treating physician',
                    'Identify procedures that can be combined or eliminated',
                    'Create streamlined treatment plan',
                    'Coordinate with multiple specialists to reduce redundancy',
                    'Focus on essential treatments covered by policy'
                ],
                expected_impact=10.0,
                effort='high',
                category='treatment_optimization'
            )
        return None
    
    def _analyze_claim_patterns(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> List[Recommendation]:
        """Analyze claim patterns for additional recommendations"""
        recommendations = []
        
        # Check for frequent claims (potential chronic condition)
        if len(claims) > 10:
            recommendations.append(Recommendation(
                recommendation_id=f'REC-{patient_id}-CHRONIC',
                priority='medium',
                title='Consider Chronic Disease Management Program',
                description=f'Patient has {len(claims)} claims, suggesting chronic condition. Disease management program may improve outcomes and reduce costs.',
                action_steps=[
                    'Evaluate patient for chronic disease management program',
                    'Coordinate with primary care physician for ongoing care plan',
                    'Set up regular monitoring and preventive care schedule',
                    'Educate patient on self-management techniques',
                    'Leverage policy benefits for preventive care'
                ],
                expected_impact=22.0,
                effort='medium',
                category='disease_management'
            ))
        
        # Check for recent high-value claims
        recent_high_value = [
            c for c in claims 
            if c.get('amount', 0) > 200000 and 
            self._is_recent(c.get('date', ''))
        ]
        
        if recent_high_value:
            recommendations.append(Recommendation(
                recommendation_id=f'REC-{patient_id}-FOLLOWUP',
                priority='high',
                title='Follow Up on High-Value Claims',
                description=f'{len(recent_high_value)} recent high-value claims require close monitoring to ensure proper settlement.',
                action_steps=[
                    'Track settlement status of high-value claims',
                    'Proactively communicate with TPA on claim progress',
                    'Ensure all supporting documentation is complete',
                    'Escalate any delays or issues immediately',
                    'Keep patient informed of settlement timeline'
                ],
                expected_impact=30.0,
                effort='low',
                category='claim_monitoring'
            ))
        
        return recommendations
    
    def _is_recent(self, date_str: str, days: int = 90) -> bool:
        """Check if date is within recent period"""
        try:
            claim_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now(claim_date.tzinfo)
            return (now - claim_date).days <= days
        except:
            return False
    
    def _deduplicate_recommendations(
        self,
        recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Remove duplicate recommendations"""
        seen = set()
        unique = []
        
        for rec in recommendations:
            if rec.recommendation_id not in seen:
                seen.add(rec.recommendation_id)
                unique.append(rec)
        
        return unique
    
    def mark_recommendation_completed(
        self,
        patient_id: str,
        recommendation_id: str,
        completed_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a recommendation as completed
        
        Requirements: 5.3.4
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Store completion record
            self.table.put_item(
                Item={
                    'PK': f'PATIENT#{patient_id}',
                    'SK': f'REC_COMPLETED#{recommendation_id}',
                    'recommendation_id': recommendation_id,
                    'completed_at': timestamp,
                    'completed_by': completed_by,
                    'notes': notes or ''
                }
            )
            
            return {
                'success': True,
                'recommendation_id': recommendation_id,
                'completed_at': timestamp
            }
        
        except Exception as e:
            print(f"Error marking recommendation completed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def track_recommendation_effectiveness(
        self,
        patient_id: str,
        recommendation_id: str,
        before_risk_score: float,
        after_risk_score: float
    ) -> Dict[str, Any]:
        """
        Track effectiveness of implemented recommendations
        
        Requirements: 5.3.5
        """
        try:
            effectiveness = ((before_risk_score - after_risk_score) / before_risk_score) * 100
            
            # Store effectiveness record
            self.table.put_item(
                Item={
                    'PK': f'REC_EFFECTIVENESS#{recommendation_id}',
                    'SK': f'PATIENT#{patient_id}',
                    'recommendation_id': recommendation_id,
                    'patient_id': patient_id,
                    'before_risk_score': float(before_risk_score),
                    'after_risk_score': float(after_risk_score),
                    'effectiveness_percentage': float(effectiveness),
                    'tracked_at': datetime.utcnow().isoformat()
                }
            )
            
            return {
                'success': True,
                'effectiveness': round(effectiveness, 2),
                'risk_reduction': round(before_risk_score - after_risk_score, 2)
            }
        
        except Exception as e:
            print(f"Error tracking recommendation effectiveness: {e}")
            return {
                'success': False,
                'error': str(e)
            }
