"""
Patient Profile Aggregation Service

This service aggregates patient data, claims, and risk information
for the multi-claim risk patient view.

Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr


class PatientProfile:
    """Patient profile with aggregated data"""
    
    def __init__(
        self,
        patient_id: str,
        demographics: Dict[str, Any],
        insurance_info: Dict[str, Any],
        claims: List[Dict[str, Any]],
        aggregated_risk: Dict[str, Any],
        risk_trend: List[Dict[str, Any]]
    ):
        self.patient_id = patient_id
        self.demographics = demographics
        self.insurance_info = insurance_info
        self.claims = claims
        self.aggregated_risk = aggregated_risk
        self.risk_trend = risk_trend
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'patient_id': self.patient_id,
            'demographics': self.demographics,
            'insurance_info': self.insurance_info,
            'claims': self.claims,
            'aggregated_risk': self.aggregated_risk,
            'risk_trend': self.risk_trend
        }


class PatientProfileService:
    """Service for patient profile aggregation"""
    
    def __init__(self, dynamodb_client=None, table_name: str = 'HospitalClaimOptimizer'):
        self.dynamodb = dynamodb_client or boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def get_patient_profile(self, patient_id: str) -> PatientProfile:
        """
        Get complete patient profile with all claims and risk data
        
        Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5
        """
        # Get patient demographics
        demographics = self._get_patient_demographics(patient_id)
        
        # Get insurance information
        insurance_info = self._get_insurance_info(patient_id)
        
        # Get all claims for patient
        claims = self._get_patient_claims(patient_id)
        
        # Calculate aggregated risk
        aggregated_risk = self._calculate_aggregated_risk(patient_id, claims)
        
        # Get risk trend over time
        risk_trend = self._calculate_risk_trend(patient_id, claims)
        
        return PatientProfile(
            patient_id=patient_id,
            demographics=demographics,
            insurance_info=insurance_info,
            claims=claims,
            aggregated_risk=aggregated_risk,
            risk_trend=risk_trend
        )
    
    def _get_patient_demographics(self, patient_id: str) -> Dict[str, Any]:
        """Get patient demographic information"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'PATIENT#{patient_id}',
                    'SK': 'DEMOGRAPHICS'
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                return {
                    'name': item.get('name', 'Unknown'),
                    'date_of_birth': item.get('date_of_birth'),
                    'gender': item.get('gender'),
                    'contact_email': item.get('contact_email'),
                    'contact_phone': item.get('contact_phone'),
                    'address': item.get('address', {})
                }
            else:
                # Return minimal demographics if not found
                return {
                    'name': f'Patient {patient_id}',
                    'date_of_birth': None,
                    'gender': None,
                    'contact_email': None,
                    'contact_phone': None,
                    'address': {}
                }
        except Exception as e:
            print(f"Error getting patient demographics: {e}")
            return {
                'name': f'Patient {patient_id}',
                'date_of_birth': None,
                'gender': None,
                'contact_email': None,
                'contact_phone': None,
                'address': {}
            }
    
    def _get_insurance_info(self, patient_id: str) -> Dict[str, Any]:
        """Get patient insurance information"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'PATIENT#{patient_id}',
                    'SK': 'INSURANCE'
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                return {
                    'policy_number': item.get('policy_number'),
                    'policy_name': item.get('policy_name'),
                    'policy_id': item.get('policy_id'),
                    'coverage_start': item.get('coverage_start'),
                    'coverage_end': item.get('coverage_end'),
                    'tpa_name': item.get('tpa_name'),
                    'sum_insured': float(item.get('sum_insured', 0))
                }
            else:
                return {
                    'policy_number': None,
                    'policy_name': None,
                    'policy_id': None,
                    'coverage_start': None,
                    'coverage_end': None,
                    'tpa_name': None,
                    'sum_insured': 0
                }
        except Exception as e:
            print(f"Error getting insurance info: {e}")
            return {
                'policy_number': None,
                'policy_name': None,
                'policy_id': None,
                'coverage_start': None,
                'coverage_end': None,
                'tpa_name': None,
                'sum_insured': 0
            }
    
    def _get_patient_claims(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all claims for a patient, sorted by date
        
        Requirements: 5.1.3, 5.1.4
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq(f'PATIENT#{patient_id}') & Key('SK').begins_with('CLAIM#')
            )
            
            claims = []
            for item in response.get('Items', []):
                claim = {
                    'claim_id': item.get('claim_id'),
                    'date': item.get('date'),
                    'amount': float(item.get('amount', 0)),
                    'status': item.get('status', 'pending'),
                    'risk_score': float(item.get('risk_score', 0)),
                    'settlement_ratio': float(item.get('settlement_ratio', 0)),
                    'procedure_codes': item.get('procedure_codes', []),
                    'diagnosis_codes': item.get('diagnosis_codes', []),
                    'hospital_name': item.get('hospital_name'),
                    'rejection_reason': item.get('rejection_reason')
                }
                claims.append(claim)
            
            # Sort by date (newest first)
            claims.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            return claims
        except Exception as e:
            print(f"Error getting patient claims: {e}")
            return []
    
    def _calculate_aggregated_risk(self, patient_id: str, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregated risk score across all patient claims
        
        Requirements: 5.1.5
        
        Risk factors:
        - Total claim amount (weight: 0.3)
        - Average settlement ratio (weight: 0.25)
        - Number of high-risk claims (weight: 0.2)
        - Rejection patterns (weight: 0.15)
        - Policy complexity (weight: 0.1)
        """
        if not claims:
            return {
                'risk_score': 0,
                'risk_level': 'low',
                'factors': [],
                'trend': 'stable'
            }
        
        # Calculate total claim amount
        total_amount = sum(claim.get('amount', 0) for claim in claims)
        
        # Calculate average settlement ratio
        settlement_ratios = [claim.get('settlement_ratio', 0) for claim in claims if claim.get('settlement_ratio', 0) > 0]
        avg_settlement_ratio = sum(settlement_ratios) / len(settlement_ratios) if settlement_ratios else 0
        
        # Count high-risk claims (risk_score > 70)
        high_risk_claims = sum(1 for claim in claims if claim.get('risk_score', 0) > 70)
        
        # Count rejections
        rejections = sum(1 for claim in claims if claim.get('status') == 'rejected')
        
        # Calculate unique procedure codes (proxy for policy complexity)
        unique_procedures = len(set(
            proc for claim in claims 
            for proc in claim.get('procedure_codes', [])
        ))
        
        # Normalize factors to 0-100 scale
        amount_factor = min(100, (total_amount / 1000000) * 100)  # Normalize to 1M
        settlement_factor = (1 - avg_settlement_ratio) * 100  # Lower settlement = higher risk
        high_risk_factor = (high_risk_claims / len(claims)) * 100
        rejection_factor = (rejections / len(claims)) * 100
        complexity_factor = min(100, (unique_procedures / 20) * 100)  # Normalize to 20 procedures
        
        # Calculate weighted risk score
        risk_score = (
            amount_factor * 0.3 +
            settlement_factor * 0.25 +
            high_risk_factor * 0.2 +
            rejection_factor * 0.15 +
            complexity_factor * 0.1
        )
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'high'
        elif risk_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Calculate trend (compare recent vs older claims)
        trend = self._calculate_risk_trend_direction(claims)
        
        # Get hospital average for comparison
        hospital_average = self._get_hospital_average_risk()
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'factors': [
                {
                    'name': 'Total Claim Amount',
                    'value': round(amount_factor, 2),
                    'weight': 0.3,
                    'contribution': round(amount_factor * 0.3, 2)
                },
                {
                    'name': 'Settlement Ratio',
                    'value': round(settlement_factor, 2),
                    'weight': 0.25,
                    'contribution': round(settlement_factor * 0.25, 2)
                },
                {
                    'name': 'High-Risk Claims',
                    'value': round(high_risk_factor, 2),
                    'weight': 0.2,
                    'contribution': round(high_risk_factor * 0.2, 2)
                },
                {
                    'name': 'Rejection Rate',
                    'value': round(rejection_factor, 2),
                    'weight': 0.15,
                    'contribution': round(rejection_factor * 0.15, 2)
                },
                {
                    'name': 'Policy Complexity',
                    'value': round(complexity_factor, 2),
                    'weight': 0.1,
                    'contribution': round(complexity_factor * 0.1, 2)
                }
            ],
            'trend': trend,
            'hospital_average': hospital_average,
            'comparison': 'above' if risk_score > hospital_average else 'below'
        }
    
    def _calculate_risk_trend_direction(self, claims: List[Dict[str, Any]]) -> str:
        """Calculate if risk is increasing, stable, or decreasing"""
        if len(claims) < 2:
            return 'stable'
        
        # Sort by date
        sorted_claims = sorted(claims, key=lambda x: x.get('date', ''))
        
        # Split into two halves
        mid = len(sorted_claims) // 2
        older_claims = sorted_claims[:mid]
        recent_claims = sorted_claims[mid:]
        
        # Calculate average risk for each half
        older_avg = sum(c.get('risk_score', 0) for c in older_claims) / len(older_claims)
        recent_avg = sum(c.get('risk_score', 0) for c in recent_claims) / len(recent_claims)
        
        # Determine trend
        diff = recent_avg - older_avg
        if diff > 10:
            return 'increasing'
        elif diff < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_risk_trend(self, patient_id: str, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate risk trend over time
        
        Requirements: 5.1.5
        """
        if not claims:
            return []
        
        # Sort by date
        sorted_claims = sorted(claims, key=lambda x: x.get('date', ''))
        
        # Group by month
        monthly_risk = {}
        for claim in sorted_claims:
            date_str = claim.get('date', '')
            if date_str:
                # Extract year-month
                month_key = date_str[:7]  # YYYY-MM
                if month_key not in monthly_risk:
                    monthly_risk[month_key] = []
                monthly_risk[month_key].append(claim.get('risk_score', 0))
        
        # Calculate average risk per month
        trend = []
        for month, risks in sorted(monthly_risk.items()):
            avg_risk = sum(risks) / len(risks)
            trend.append({
                'month': month,
                'risk_score': round(avg_risk, 2),
                'claim_count': len(risks)
            })
        
        return trend
    
    def _get_hospital_average_risk(self) -> float:
        """Get hospital-wide average risk score for comparison"""
        # In a real implementation, this would query aggregated statistics
        # For now, return a reasonable default
        return 45.0
    
    def get_patient_claims_sorted(
        self,
        patient_id: str,
        sort_by: str = 'date',
        sort_order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get patient claims with sorting
        
        Requirements: 5.1.4
        
        Args:
            patient_id: Patient ID
            sort_by: Field to sort by (date, amount, status, risk_score)
            sort_order: Sort order (asc, desc)
        """
        claims = self._get_patient_claims(patient_id)
        
        # Sort claims
        reverse = (sort_order == 'desc')
        
        if sort_by == 'date':
            claims.sort(key=lambda x: x.get('date', ''), reverse=reverse)
        elif sort_by == 'amount':
            claims.sort(key=lambda x: x.get('amount', 0), reverse=reverse)
        elif sort_by == 'status':
            claims.sort(key=lambda x: x.get('status', ''), reverse=reverse)
        elif sort_by == 'risk_score':
            claims.sort(key=lambda x: x.get('risk_score', 0), reverse=reverse)
        
        return claims
