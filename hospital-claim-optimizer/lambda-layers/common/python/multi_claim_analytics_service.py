"""
Multi-Claim Analytics Service

Provides analytics across all patient claims to identify patterns
and optimize billing strategies.

Requirements: 5.4.1, 5.4.2, 5.4.3, 5.4.4, 5.4.5
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
import statistics


class ClaimAnalytics:
    """Analytics results for patient claims"""
    
    def __init__(
        self,
        patient_id: str,
        total_claim_amount: float,
        average_settlement_ratio: float,
        common_rejection_reasons: List[Dict[str, Any]],
        policy_utilization: Dict[str, Any],
        historical_performance: List[Dict[str, Any]]
    ):
        self.patient_id = patient_id
        self.total_claim_amount = total_claim_amount
        self.average_settlement_ratio = average_settlement_ratio
        self.common_rejection_reasons = common_rejection_reasons
        self.policy_utilization = policy_utilization
        self.historical_performance = historical_performance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'patient_id': self.patient_id,
            'total_claim_amount': self.total_claim_amount,
            'average_settlement_ratio': self.average_settlement_ratio,
            'common_rejection_reasons': self.common_rejection_reasons,
            'policy_utilization': self.policy_utilization,
            'historical_performance': self.historical_performance
        }


class MultiClaimAnalyticsService:
    """Service for multi-claim analytics"""
    
    def __init__(self):
        pass
    
    def analyze_patient_claims(
        self,
        patient_id: str,
        claims: List[Dict[str, Any]]
    ) -> ClaimAnalytics:
        """
        Analyze all claims for a patient
        
        Requirements: 5.4.1, 5.4.2, 5.4.3, 5.4.4, 5.4.5
        """
        if not claims:
            return ClaimAnalytics(
                patient_id=patient_id,
                total_claim_amount=0.0,
                average_settlement_ratio=0.0,
                common_rejection_reasons=[],
                policy_utilization={},
                historical_performance=[]
            )
        
        # Calculate total claim amount
        total_amount = self._calculate_total_claim_amount(claims)
        
        # Calculate average settlement ratio
        avg_settlement = self._calculate_average_settlement_ratio(claims)
        
        # Identify common rejection reasons
        rejection_reasons = self._identify_common_rejection_reasons(claims)
        
        # Analyze policy utilization patterns
        policy_utilization = self._analyze_policy_utilization(claims)
        
        # Calculate historical performance trends
        historical_performance = self._calculate_historical_performance(claims)
        
        return ClaimAnalytics(
            patient_id=patient_id,
            total_claim_amount=total_amount,
            average_settlement_ratio=avg_settlement,
            common_rejection_reasons=rejection_reasons,
            policy_utilization=policy_utilization,
            historical_performance=historical_performance
        )
    
    def _calculate_total_claim_amount(self, claims: List[Dict[str, Any]]) -> float:
        """
        Calculate total claim amount across all claims
        
        Requirements: 5.4.1
        """
        total = sum(claim.get('amount', 0) for claim in claims)
        return round(total, 2)
    
    def _calculate_average_settlement_ratio(self, claims: List[Dict[str, Any]]) -> float:
        """
        Calculate average settlement ratio
        
        Requirements: 5.4.2
        """
        # Only include claims with settlement data
        settled_claims = [
            claim for claim in claims 
            if claim.get('settlement_ratio') is not None and claim.get('settlement_ratio') > 0
        ]
        
        if not settled_claims:
            return 0.0
        
        total_ratio = sum(claim.get('settlement_ratio', 0) for claim in settled_claims)
        avg_ratio = total_ratio / len(settled_claims)
        
        return round(avg_ratio, 4)
    
    def _identify_common_rejection_reasons(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify common rejection reasons
        
        Requirements: 5.4.3
        """
        # Get all rejection reasons
        rejection_reasons = []
        for claim in claims:
            if claim.get('status') == 'rejected' and claim.get('rejection_reason'):
                rejection_reasons.append(claim.get('rejection_reason'))
        
        if not rejection_reasons:
            return []
        
        # Count occurrences
        reason_counts = Counter(rejection_reasons)
        
        # Calculate percentages
        total_rejections = len(rejection_reasons)
        common_reasons = []
        
        for reason, count in reason_counts.most_common(10):  # Top 10 reasons
            common_reasons.append({
                'reason': reason,
                'count': count,
                'percentage': round((count / total_rejections) * 100, 2)
            })
        
        return common_reasons
    
    def _analyze_policy_utilization(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze policy utilization patterns
        
        Requirements: 5.4.4
        """
        # Analyze procedure codes
        procedure_counts = Counter()
        diagnosis_counts = Counter()
        
        for claim in claims:
            for proc in claim.get('procedure_codes', []):
                procedure_counts[proc] += 1
            for diag in claim.get('diagnosis_codes', []):
                diagnosis_counts[diag] += 1
        
        # Calculate utilization by category
        category_utilization = self._categorize_procedures(procedure_counts)
        
        # Calculate coverage statistics
        covered_claims = sum(1 for c in claims if c.get('status') == 'approved')
        total_claims = len(claims)
        coverage_rate = (covered_claims / total_claims * 100) if total_claims > 0 else 0
        
        # Identify most utilized benefits
        top_procedures = [
            {
                'code': code,
                'count': count,
                'percentage': round((count / total_claims) * 100, 2)
            }
            for code, count in procedure_counts.most_common(10)
        ]
        
        top_diagnoses = [
            {
                'code': code,
                'count': count,
                'percentage': round((count / total_claims) * 100, 2)
            }
            for code, count in diagnosis_counts.most_common(10)
        ]
        
        return {
            'coverage_rate': round(coverage_rate, 2),
            'total_procedures': len(procedure_counts),
            'total_diagnoses': len(diagnosis_counts),
            'category_utilization': category_utilization,
            'top_procedures': top_procedures,
            'top_diagnoses': top_diagnoses,
            'utilization_diversity': self._calculate_utilization_diversity(procedure_counts)
        }
    
    def _categorize_procedures(self, procedure_counts: Counter) -> Dict[str, Any]:
        """Categorize procedures by type"""
        # Simple categorization based on procedure code patterns
        # In a real implementation, this would use a comprehensive procedure code database
        categories = {
            'diagnostic': 0,
            'surgical': 0,
            'therapeutic': 0,
            'preventive': 0,
            'emergency': 0,
            'other': 0
        }
        
        for code, count in procedure_counts.items():
            # Simple heuristic categorization
            if code.startswith('7') or code.startswith('8'):
                categories['diagnostic'] += count
            elif code.startswith('0') or code.startswith('1'):
                categories['surgical'] += count
            elif code.startswith('9'):
                categories['therapeutic'] += count
            elif code.startswith('Z'):
                categories['preventive'] += count
            elif code.startswith('E'):
                categories['emergency'] += count
            else:
                categories['other'] += count
        
        total = sum(categories.values())
        if total > 0:
            for category in categories:
                categories[category] = {
                    'count': categories[category],
                    'percentage': round((categories[category] / total) * 100, 2)
                }
        
        return categories
    
    def _calculate_utilization_diversity(self, procedure_counts: Counter) -> float:
        """Calculate diversity of procedure utilization (Shannon entropy)"""
        if not procedure_counts:
            return 0.0
        
        total = sum(procedure_counts.values())
        probabilities = [count / total for count in procedure_counts.values()]
        
        # Calculate Shannon entropy
        import math
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        
        # Normalize to 0-100 scale
        max_entropy = math.log2(len(procedure_counts)) if len(procedure_counts) > 1 else 1
        normalized = (entropy / max_entropy * 100) if max_entropy > 0 else 0
        
        return round(normalized, 2)
    
    def _calculate_historical_performance(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate historical performance trends
        
        Requirements: 5.4.5
        """
        if not claims:
            return []
        
        # Sort claims by date
        sorted_claims = sorted(
            [c for c in claims if c.get('date')],
            key=lambda x: x.get('date', '')
        )
        
        if not sorted_claims:
            return []
        
        # Group by month
        monthly_data = {}
        
        for claim in sorted_claims:
            date_str = claim.get('date', '')
            if not date_str:
                continue
            
            # Extract year-month
            month_key = date_str[:7]  # YYYY-MM
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'claims': [],
                    'total_amount': 0,
                    'approved_count': 0,
                    'rejected_count': 0,
                    'pending_count': 0
                }
            
            monthly_data[month_key]['claims'].append(claim)
            monthly_data[month_key]['total_amount'] += claim.get('amount', 0)
            
            status = claim.get('status', 'pending')
            if status == 'approved':
                monthly_data[month_key]['approved_count'] += 1
            elif status == 'rejected':
                monthly_data[month_key]['rejected_count'] += 1
            else:
                monthly_data[month_key]['pending_count'] += 1
        
        # Calculate metrics for each month
        performance = []
        
        for month, data in sorted(monthly_data.items()):
            total_claims = len(data['claims'])
            
            # Calculate average settlement ratio for the month
            settlement_ratios = [
                c.get('settlement_ratio', 0) 
                for c in data['claims'] 
                if c.get('settlement_ratio') is not None and c.get('settlement_ratio') > 0
            ]
            avg_settlement = (
                sum(settlement_ratios) / len(settlement_ratios) 
                if settlement_ratios else 0
            )
            
            # Calculate approval rate
            approval_rate = (
                (data['approved_count'] / total_claims * 100) 
                if total_claims > 0 else 0
            )
            
            # Calculate average claim amount
            avg_amount = data['total_amount'] / total_claims if total_claims > 0 else 0
            
            performance.append({
                'month': month,
                'total_claims': total_claims,
                'total_amount': round(data['total_amount'], 2),
                'average_amount': round(avg_amount, 2),
                'average_settlement_ratio': round(avg_settlement, 4),
                'approval_rate': round(approval_rate, 2),
                'approved_count': data['approved_count'],
                'rejected_count': data['rejected_count'],
                'pending_count': data['pending_count']
            })
        
        # Add trend indicators
        if len(performance) >= 2:
            for i in range(1, len(performance)):
                prev = performance[i - 1]
                curr = performance[i]
                
                # Calculate month-over-month changes
                curr['mom_amount_change'] = round(
                    ((curr['total_amount'] - prev['total_amount']) / prev['total_amount'] * 100)
                    if prev['total_amount'] > 0 else 0,
                    2
                )
                
                curr['mom_settlement_change'] = round(
                    ((curr['average_settlement_ratio'] - prev['average_settlement_ratio']) / prev['average_settlement_ratio'] * 100)
                    if prev['average_settlement_ratio'] > 0 else 0,
                    2
                )
                
                curr['mom_approval_change'] = round(
                    curr['approval_rate'] - prev['approval_rate'],
                    2
                )
        
        return performance
    
    def compare_to_benchmarks(
        self,
        analytics: ClaimAnalytics,
        hospital_benchmarks: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare patient analytics to hospital benchmarks
        
        Args:
            analytics: Patient claim analytics
            hospital_benchmarks: Hospital-wide benchmark data
        
        Returns:
            Comparison results with percentile rankings
        """
        if not hospital_benchmarks:
            # Use default benchmarks if not provided
            hospital_benchmarks = {
                'average_claim_amount': 150000,
                'average_settlement_ratio': 0.85,
                'average_approval_rate': 75.0
            }
        
        comparison = {
            'claim_amount': {
                'patient': analytics.total_claim_amount,
                'hospital_average': hospital_benchmarks.get('average_claim_amount', 0),
                'percentile': self._calculate_percentile(
                    analytics.total_claim_amount,
                    hospital_benchmarks.get('average_claim_amount', 0)
                )
            },
            'settlement_ratio': {
                'patient': analytics.average_settlement_ratio,
                'hospital_average': hospital_benchmarks.get('average_settlement_ratio', 0),
                'percentile': self._calculate_percentile(
                    analytics.average_settlement_ratio,
                    hospital_benchmarks.get('average_settlement_ratio', 0)
                )
            }
        }
        
        return comparison
    
    def _calculate_percentile(self, value: float, average: float) -> str:
        """Calculate approximate percentile based on value vs average"""
        if average == 0:
            return 'N/A'
        
        ratio = value / average
        
        if ratio >= 1.5:
            return '90th+'
        elif ratio >= 1.2:
            return '75th-90th'
        elif ratio >= 0.8:
            return '25th-75th'
        elif ratio >= 0.5:
            return '10th-25th'
        else:
            return '<10th'
