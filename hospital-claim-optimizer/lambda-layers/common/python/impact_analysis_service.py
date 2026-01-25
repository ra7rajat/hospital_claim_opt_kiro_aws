"""
Impact Analysis Service Module
Analyzes the impact of policy changes on active claims and settlement ratios
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from data_models import Policy
from database_access import DynamoDBAccessLayer
from common_utils import get_timestamp


@dataclass
class ImpactAnalysis:
    """Represents impact analysis results"""
    policy_id: str
    version1: int
    version2: int
    affected_claims_count: int
    affected_claim_ids: List[str]
    estimated_settlement_change: float  # Percentage change
    patients_to_notify: List[str]
    confidence_level: str  # 'high', 'medium', 'low'
    risk_level: str  # 'high', 'medium', 'low'
    detailed_impacts: List[Dict[str, Any]]
    analysis_timestamp: str


class ImpactAnalysisService:
    """Service for analyzing policy change impacts"""
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
    
    def analyze_policy_change_impact(
        self,
        hospital_id: str,
        policy_id: str,
        version1: int,
        version2: int,
        policy1_rules: Dict[str, Any],
        policy2_rules: Dict[str, Any]
    ) -> ImpactAnalysis:
        """
        Analyze the impact of policy changes on active claims
        
        Args:
            hospital_id: Hospital identifier
            policy_id: Policy identifier
            version1: Original version number
            version2: New version number
            policy1_rules: Extracted rules from version 1
            policy2_rules: Extracted rules from version 2
            
        Returns:
            ImpactAnalysis object with detailed impact assessment
        """
        # Get active claims using this policy
        active_claims = self._get_active_claims_for_policy(hospital_id, policy_id)
        
        # Analyze impact on each claim
        affected_claims = []
        detailed_impacts = []
        patients_to_notify = set()
        settlement_changes = []
        
        for claim in active_claims:
            impact = self._analyze_claim_impact(
                claim,
                policy1_rules,
                policy2_rules
            )
            
            if impact['is_affected']:
                affected_claims.append(claim['claim_id'])
                detailed_impacts.append(impact)
                patients_to_notify.add(claim['patient_id'])
                settlement_changes.append(impact['settlement_change'])
        
        # Calculate average settlement change
        avg_settlement_change = (
            sum(settlement_changes) / len(settlement_changes)
            if settlement_changes else 0.0
        )
        
        # Assess confidence and risk
        confidence = self._assess_confidence(len(active_claims), len(affected_claims))
        risk = self._assess_risk(len(affected_claims), avg_settlement_change)
        
        return ImpactAnalysis(
            policy_id=policy_id,
            version1=version1,
            version2=version2,
            affected_claims_count=len(affected_claims),
            affected_claim_ids=affected_claims,
            estimated_settlement_change=avg_settlement_change,
            patients_to_notify=list(patients_to_notify),
            confidence_level=confidence,
            risk_level=risk,
            detailed_impacts=detailed_impacts,
            analysis_timestamp=get_timestamp()
        )
    
    def _get_active_claims_for_policy(
        self,
        hospital_id: str,
        policy_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all active claims that use this policy
        """
        # Query claims for this hospital
        items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "CLAIM#")
        
        active_claims = []
        for item in items:
            # Check if claim uses this policy and is active
            if (item.get('policy_id') == policy_id and
                item.get('status') in ['PENDING', 'IN_REVIEW', 'SUBMITTED']):
                active_claims.append({
                    'claim_id': item.get('claim_id'),
                    'patient_id': item.get('patient_id'),
                    'procedure_code': item.get('procedure_code'),
                    'claim_amount': item.get('claim_amount', 0),
                    'status': item.get('status'),
                    'audit_results': item.get('audit_results', {})
                })
        
        return active_claims
    
    def _analyze_claim_impact(
        self,
        claim: Dict[str, Any],
        old_rules: Dict[str, Any],
        new_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze impact of policy change on a specific claim
        """
        # Simulate audit with both rule sets
        old_result = self._simulate_audit(claim, old_rules)
        new_result = self._simulate_audit(claim, new_rules)
        
        # Calculate differences
        coverage_change = new_result['coverage_percentage'] - old_result['coverage_percentage']
        settlement_change = new_result['settlement_ratio'] - old_result['settlement_ratio']
        
        # Determine if claim is affected
        is_affected = (
            abs(coverage_change) > 1.0 or  # More than 1% coverage change
            abs(settlement_change) > 0.01 or  # More than 1% settlement change
            old_result['is_covered'] != new_result['is_covered']  # Coverage status changed
        )
        
        return {
            'claim_id': claim['claim_id'],
            'patient_id': claim['patient_id'],
            'is_affected': is_affected,
            'coverage_change': coverage_change,
            'settlement_change': settlement_change,
            'old_coverage': old_result['coverage_percentage'],
            'new_coverage': new_result['coverage_percentage'],
            'old_settlement': old_result['settlement_ratio'],
            'new_settlement': new_result['settlement_ratio'],
            'coverage_status_changed': old_result['is_covered'] != new_result['is_covered'],
            'impact_severity': self._calculate_impact_severity(coverage_change, settlement_change)
        }
    
    def _simulate_audit(
        self,
        claim: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate bill audit with given policy rules
        
        This is a simplified simulation. In production, would use
        the actual audit logic from bill_audit.py
        """
        procedure_code = claim.get('procedure_code', '')
        claim_amount = claim.get('claim_amount', 0)
        
        # Check if procedure is covered
        covered_procedures = rules.get('covered_procedures', [])
        excluded_procedures = rules.get('procedure_exclusions', [])
        
        is_covered = True
        coverage_percentage = 100.0
        
        # Check exclusions
        if procedure_code in excluded_procedures:
            is_covered = False
            coverage_percentage = 0.0
        
        # Check if in covered list (if list exists)
        elif covered_procedures and procedure_code not in covered_procedures:
            is_covered = False
            coverage_percentage = 0.0
        
        # Apply copay if covered
        if is_covered:
            copay_conditions = rules.get('copay_conditions', [])
            for copay in copay_conditions:
                if copay.get('procedure_code') == procedure_code:
                    copay_percentage = copay.get('percentage', 0)
                    coverage_percentage -= copay_percentage
                    break
        
        # Apply room rent cap
        room_rent_cap = rules.get('room_rent_cap', {})
        if room_rent_cap and 'room' in procedure_code.lower():
            cap_type = room_rent_cap.get('type')
            cap_value = room_rent_cap.get('value', 0)
            
            if cap_type == 'fixed' and claim_amount > cap_value:
                # Reduce coverage based on cap
                coverage_percentage *= (cap_value / claim_amount)
        
        # Calculate settlement ratio
        settlement_ratio = coverage_percentage / 100.0 if is_covered else 0.0
        
        return {
            'is_covered': is_covered,
            'coverage_percentage': coverage_percentage,
            'settlement_ratio': settlement_ratio,
            'approved_amount': claim_amount * settlement_ratio
        }
    
    def _calculate_impact_severity(
        self,
        coverage_change: float,
        settlement_change: float
    ) -> str:
        """
        Calculate severity of impact on a claim
        """
        # High severity: >10% change in coverage or >5% in settlement
        if abs(coverage_change) > 10.0 or abs(settlement_change) > 0.05:
            return 'high'
        
        # Medium severity: >5% change in coverage or >2% in settlement
        elif abs(coverage_change) > 5.0 or abs(settlement_change) > 0.02:
            return 'medium'
        
        # Low severity: any other change
        else:
            return 'low'
    
    def _assess_confidence(
        self,
        total_claims: int,
        affected_claims: int
    ) -> str:
        """
        Assess confidence level of impact analysis
        """
        if total_claims == 0:
            return 'low'
        
        # High confidence if we have enough data
        if total_claims >= 50:
            return 'high'
        elif total_claims >= 20:
            return 'medium'
        else:
            return 'low'
    
    def _assess_risk(
        self,
        affected_claims: int,
        avg_settlement_change: float
    ) -> str:
        """
        Assess overall risk level of policy change
        """
        # High risk: many claims affected or large settlement change
        if affected_claims > 20 or abs(avg_settlement_change) > 0.05:
            return 'high'
        
        # Medium risk: moderate number of claims or moderate change
        elif affected_claims > 5 or abs(avg_settlement_change) > 0.02:
            return 'medium'
        
        # Low risk: few claims affected and small change
        else:
            return 'low'
    
    def generate_impact_report(
        self,
        analysis: ImpactAnalysis
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive impact report
        """
        report = {
            'policy_id': analysis.policy_id,
            'versions_compared': f"v{analysis.version1} → v{analysis.version2}",
            'analysis_date': analysis.analysis_timestamp,
            'summary': {
                'affected_claims': analysis.affected_claims_count,
                'patients_to_notify': len(analysis.patients_to_notify),
                'estimated_settlement_change': f"{analysis.estimated_settlement_change:+.2%}",
                'confidence_level': analysis.confidence_level,
                'risk_level': analysis.risk_level
            },
            'impact_by_severity': self._group_by_severity(analysis.detailed_impacts),
            'top_affected_claims': self._get_top_affected_claims(analysis.detailed_impacts, 10),
            'recommendations': self._generate_recommendations(analysis)
        }
        
        return report
    
    def _group_by_severity(
        self,
        impacts: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Group impacts by severity level
        """
        severity_counts = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for impact in impacts:
            severity = impact.get('impact_severity', 'low')
            severity_counts[severity] += 1
        
        return severity_counts
    
    def _get_top_affected_claims(
        self,
        impacts: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the most affected claims
        """
        # Sort by absolute settlement change
        sorted_impacts = sorted(
            impacts,
            key=lambda x: abs(x.get('settlement_change', 0)),
            reverse=True
        )
        
        return sorted_impacts[:limit]
    
    def _generate_recommendations(
        self,
        analysis: ImpactAnalysis
    ) -> List[str]:
        """
        Generate recommendations based on impact analysis
        """
        recommendations = []
        
        if analysis.risk_level == 'high':
            recommendations.append(
                "HIGH RISK: Consider phased rollout or additional review before activation"
            )
        
        if analysis.affected_claims_count > 0:
            recommendations.append(
                f"Notify {len(analysis.patients_to_notify)} patients about policy changes"
            )
        
        if abs(analysis.estimated_settlement_change) > 0.05:
            direction = "increase" if analysis.estimated_settlement_change > 0 else "decrease"
            recommendations.append(
                f"Significant settlement ratio {direction} expected - review financial impact"
            )
        
        if analysis.confidence_level == 'low':
            recommendations.append(
                "Low confidence due to limited data - monitor closely after activation"
            )
        
        # Add specific recommendations based on detailed impacts
        high_severity_count = sum(
            1 for impact in analysis.detailed_impacts
            if impact.get('impact_severity') == 'high'
        )
        
        if high_severity_count > 0:
            recommendations.append(
                f"Review {high_severity_count} high-severity claim impacts individually"
            )
        
        return recommendations
    
    def compare_settlement_ratios(
        self,
        hospital_id: str,
        policy_id: str,
        old_rules: Dict[str, Any],
        new_rules: Dict[str, Any],
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        Compare settlement ratios across a sample of historical claims
        """
        # Get historical claims for this policy
        historical_claims = self._get_historical_claims(
            hospital_id,
            policy_id,
            sample_size
        )
        
        old_settlements = []
        new_settlements = []
        
        for claim in historical_claims:
            old_result = self._simulate_audit(claim, old_rules)
            new_result = self._simulate_audit(claim, new_rules)
            
            old_settlements.append(old_result['settlement_ratio'])
            new_settlements.append(new_result['settlement_ratio'])
        
        # Calculate statistics
        old_avg = sum(old_settlements) / len(old_settlements) if old_settlements else 0
        new_avg = sum(new_settlements) / len(new_settlements) if new_settlements else 0
        
        return {
            'sample_size': len(historical_claims),
            'old_average_settlement': old_avg,
            'new_average_settlement': new_avg,
            'change': new_avg - old_avg,
            'change_percentage': ((new_avg - old_avg) / old_avg * 100) if old_avg > 0 else 0
        }
    
    def _get_historical_claims(
        self,
        hospital_id: str,
        policy_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get historical claims for settlement ratio comparison
        """
        # Query completed claims for this policy
        items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "CLAIM#")
        
        historical_claims = []
        for item in items:
            if (item.get('policy_id') == policy_id and
                item.get('status') in ['APPROVED', 'COMPLETED', 'SETTLED']):
                historical_claims.append({
                    'claim_id': item.get('claim_id'),
                    'patient_id': item.get('patient_id'),
                    'procedure_code': item.get('procedure_code'),
                    'claim_amount': item.get('claim_amount', 0),
                    'status': item.get('status')
                })
                
                if len(historical_claims) >= limit:
                    break
        
        return historical_claims
