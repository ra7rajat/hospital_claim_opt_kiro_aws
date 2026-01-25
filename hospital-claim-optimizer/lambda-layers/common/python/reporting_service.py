"""
Reporting and Analytics Service
Handles report generation, CSR analysis, and metrics tracking
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from database_access import DynamoDBAccessLayer
from data_models import ClaimStatus, RiskLevel
from common_utils import get_timestamp

class ReportingService:
    """Service for generating reports and analytics"""
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
    
    def generate_csr_trend_report(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generate Claim Settlement Ratio (CSR) trend analysis
        
        Args:
            hospital_id: Hospital identifier
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            CSR trend report with time-series data
        """
        # Get all claims in date range
        claims = self._get_claims_in_date_range(hospital_id, start_date, end_date)
        
        if not claims:
            return {
                'success': False,
                'error': 'No claims found in date range'
            }
        
        # Calculate overall CSR
        total_amount = sum(c.get('total_amount', 0.0) for c in claims)
        approved_amount = sum(
            c.get('audit_results', {}).get('approved_amount', 0.0)
            for c in claims
        )
        
        overall_csr = approved_amount / total_amount if total_amount > 0 else 0.0
        
        # Calculate CSR by month
        monthly_csr = self._calculate_monthly_csr(claims)
        
        # Calculate CSR by risk level
        csr_by_risk = self._calculate_csr_by_risk(claims)
        
        # Calculate CSR by claim amount range
        csr_by_amount = self._calculate_csr_by_amount_range(claims)
        
        # Identify trends
        trend = self._identify_trend(monthly_csr)
        
        return {
            'success': True,
            'report_type': 'CSR_TREND',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'overall_csr': overall_csr,
            'total_claims': len(claims),
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'monthly_csr': monthly_csr,
            'csr_by_risk_level': csr_by_risk,
            'csr_by_amount_range': csr_by_amount,
            'trend': trend,
            'generated_at': get_timestamp()
        }
    
    def generate_rejection_analysis_report(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generate rejection reason analysis report
        
        Args:
            hospital_id: Hospital identifier
            start_date: Start date
            end_date: End date
        
        Returns:
            Rejection analysis report
        """
        # Get all claims in date range
        claims = self._get_claims_in_date_range(hospital_id, start_date, end_date)
        
        if not claims:
            return {
                'success': False,
                'error': 'No claims found in date range'
            }
        
        # Collect rejection reasons
        rejection_reasons = defaultdict(lambda: {'count': 0, 'total_amount': 0.0})
        policy_clauses = defaultdict(lambda: {'count': 0, 'total_amount': 0.0})
        
        total_rejected_items = 0
        total_rejected_amount = 0.0
        
        for claim in claims:
            claim_id = claim.get('claim_id', '')
            
            # Get claim items
            claim_items = self.db_client.query_items(f"CLAIM#{claim_id}", "ITEM#")
            
            for item in claim_items:
                if item.get('audit_status') == 'REJECTED':
                    total_rejected_items += 1
                    cost = item.get('cost', 0.0)
                    total_rejected_amount += cost
                    
                    # Track rejection reason
                    reason = item.get('rejection_reason', 'Unknown')
                    rejection_reasons[reason]['count'] += 1
                    rejection_reasons[reason]['total_amount'] += cost
                    
                    # Track policy clause
                    clause = item.get('policy_clause_reference', 'Unknown')
                    policy_clauses[clause]['count'] += 1
                    policy_clauses[clause]['total_amount'] += cost
        
        # Sort by frequency
        top_rejection_reasons = sorted(
            [
                {
                    'reason': reason,
                    'count': data['count'],
                    'total_amount': data['total_amount'],
                    'percentage': (data['count'] / total_rejected_items * 100) if total_rejected_items > 0 else 0
                }
                for reason, data in rejection_reasons.items()
            ],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        top_policy_clauses = sorted(
            [
                {
                    'clause': clause,
                    'count': data['count'],
                    'total_amount': data['total_amount'],
                    'percentage': (data['count'] / total_rejected_items * 100) if total_rejected_items > 0 else 0
                }
                for clause, data in policy_clauses.items()
            ],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        return {
            'success': True,
            'report_type': 'REJECTION_ANALYSIS',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_rejected_items': total_rejected_items,
            'total_rejected_amount': total_rejected_amount,
            'top_rejection_reasons': top_rejection_reasons,
            'top_policy_clauses': top_policy_clauses,
            'generated_at': get_timestamp()
        }
    
    def generate_benchmark_report(
        self,
        hospital_id: str,
        comparison_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate benchmark comparison report
        
        Args:
            hospital_id: Hospital identifier
            comparison_period_days: Number of days for comparison
        
        Returns:
            Benchmark report comparing current vs previous period
        """
        # Calculate date ranges
        end_date = datetime.utcnow()
        current_start = end_date - timedelta(days=comparison_period_days)
        previous_start = current_start - timedelta(days=comparison_period_days)
        
        # Get claims for both periods
        current_claims = self._get_claims_in_date_range(
            hospital_id,
            current_start.isoformat(),
            end_date.isoformat()
        )
        
        previous_claims = self._get_claims_in_date_range(
            hospital_id,
            previous_start.isoformat(),
            current_start.isoformat()
        )
        
        # Calculate metrics for both periods
        current_metrics = self._calculate_period_metrics(current_claims)
        previous_metrics = self._calculate_period_metrics(previous_claims)
        
        # Calculate changes
        changes = {
            'csr_change': current_metrics['csr'] - previous_metrics['csr'],
            'claim_volume_change': current_metrics['claim_count'] - previous_metrics['claim_count'],
            'avg_claim_amount_change': current_metrics['avg_claim_amount'] - previous_metrics['avg_claim_amount'],
            'high_risk_percentage_change': current_metrics['high_risk_percentage'] - previous_metrics['high_risk_percentage']
        }
        
        return {
            'success': True,
            'report_type': 'BENCHMARK_COMPARISON',
            'comparison_period_days': comparison_period_days,
            'current_period': {
                'start_date': current_start.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': current_metrics
            },
            'previous_period': {
                'start_date': previous_start.isoformat(),
                'end_date': current_start.isoformat(),
                'metrics': previous_metrics
            },
            'changes': changes,
            'generated_at': get_timestamp()
        }
    
    def generate_policy_clause_frequency_report(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generate policy clause frequency report
        
        Args:
            hospital_id: Hospital identifier
            start_date: Start date
            end_date: End date
        
        Returns:
            Policy clause frequency report
        """
        # Get all claims in date range
        claims = self._get_claims_in_date_range(hospital_id, start_date, end_date)
        
        clause_usage = defaultdict(lambda: {
            'approved_count': 0,
            'rejected_count': 0,
            'total_approved_amount': 0.0,
            'total_rejected_amount': 0.0
        })
        
        for claim in claims:
            claim_id = claim.get('claim_id', '')
            claim_items = self.db_client.query_items(f"CLAIM#{claim_id}", "ITEM#")
            
            for item in claim_items:
                clause = item.get('policy_clause_reference', 'Unknown')
                cost = item.get('cost', 0.0)
                status = item.get('audit_status', '')
                
                if status == 'APPROVED':
                    clause_usage[clause]['approved_count'] += 1
                    clause_usage[clause]['total_approved_amount'] += cost
                elif status == 'REJECTED':
                    clause_usage[clause]['rejected_count'] += 1
                    clause_usage[clause]['total_rejected_amount'] += cost
        
        # Format results
        clause_frequency = [
            {
                'clause': clause,
                'approved_count': data['approved_count'],
                'rejected_count': data['rejected_count'],
                'total_count': data['approved_count'] + data['rejected_count'],
                'approval_rate': (
                    data['approved_count'] / (data['approved_count'] + data['rejected_count'])
                    if (data['approved_count'] + data['rejected_count']) > 0 else 0.0
                ),
                'total_approved_amount': data['total_approved_amount'],
                'total_rejected_amount': data['total_rejected_amount']
            }
            for clause, data in clause_usage.items()
        ]
        
        # Sort by total count
        clause_frequency.sort(key=lambda x: x['total_count'], reverse=True)
        
        return {
            'success': True,
            'report_type': 'POLICY_CLAUSE_FREQUENCY',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'clause_frequency': clause_frequency[:20],  # Top 20
            'generated_at': get_timestamp()
        }
    
    def _get_claims_in_date_range(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Get all claims for hospital in date range"""
        # Get all patients for hospital
        patients = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "PATIENT#")
        
        # Get all claims
        all_claims = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            if patient_id:
                claims = self.db_client.query_items(f"PATIENT#{patient_id}", "CLAIM#")
                all_claims.extend(claims)
        
        # Filter by date range
        filtered_claims = [
            c for c in all_claims
            if start_date <= c.get('created_at', '') <= end_date
        ]
        
        return filtered_claims
    
    def _calculate_monthly_csr(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate CSR by month"""
        monthly_data = defaultdict(lambda: {'total': 0.0, 'approved': 0.0})
        
        for claim in claims:
            created_at = claim.get('created_at', '')
            if created_at:
                month = created_at[:7]  # YYYY-MM
                monthly_data[month]['total'] += claim.get('total_amount', 0.0)
                monthly_data[month]['approved'] += claim.get('audit_results', {}).get('approved_amount', 0.0)
        
        monthly_csr = [
            {
                'month': month,
                'csr': data['approved'] / data['total'] if data['total'] > 0 else 0.0,
                'total_amount': data['total'],
                'approved_amount': data['approved']
            }
            for month, data in sorted(monthly_data.items())
        ]
        
        return monthly_csr
    
    def _calculate_csr_by_risk(self, claims: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate CSR by risk level"""
        risk_data = defaultdict(lambda: {'total': 0.0, 'approved': 0.0})
        
        for claim in claims:
            risk_level = claim.get('risk_level', 'UNKNOWN')
            risk_data[risk_level]['total'] += claim.get('total_amount', 0.0)
            risk_data[risk_level]['approved'] += claim.get('audit_results', {}).get('approved_amount', 0.0)
        
        return {
            risk: data['approved'] / data['total'] if data['total'] > 0 else 0.0
            for risk, data in risk_data.items()
        }
    
    def _calculate_csr_by_amount_range(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate CSR by claim amount range"""
        ranges = [
            (0, 10000, '0-10K'),
            (10000, 50000, '10K-50K'),
            (50000, 100000, '50K-100K'),
            (100000, 200000, '100K-200K'),
            (200000, float('inf'), '200K+')
        ]
        
        range_data = {label: {'total': 0.0, 'approved': 0.0, 'count': 0} for _, _, label in ranges}
        
        for claim in claims:
            amount = claim.get('total_amount', 0.0)
            
            for min_amt, max_amt, label in ranges:
                if min_amt <= amount < max_amt:
                    range_data[label]['total'] += amount
                    range_data[label]['approved'] += claim.get('audit_results', {}).get('approved_amount', 0.0)
                    range_data[label]['count'] += 1
                    break
        
        return [
            {
                'range': label,
                'csr': data['approved'] / data['total'] if data['total'] > 0 else 0.0,
                'claim_count': data['count'],
                'total_amount': data['total']
            }
            for _, _, label in ranges
            for data in [range_data[label]]
            if data['count'] > 0
        ]
    
    def _identify_trend(self, monthly_csr: List[Dict[str, Any]]) -> str:
        """Identify CSR trend"""
        if len(monthly_csr) < 2:
            return 'insufficient_data'
        
        # Calculate average CSR for first and second half
        mid_point = len(monthly_csr) // 2
        first_half_avg = sum(m['csr'] for m in monthly_csr[:mid_point]) / mid_point
        second_half_avg = sum(m['csr'] for m in monthly_csr[mid_point:]) / (len(monthly_csr) - mid_point)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 0.05:
            return 'improving'
        elif diff < -0.05:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_period_metrics(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for a period"""
        if not claims:
            return {
                'claim_count': 0,
                'total_amount': 0.0,
                'approved_amount': 0.0,
                'csr': 0.0,
                'avg_claim_amount': 0.0,
                'high_risk_percentage': 0.0
            }
        
        total_amount = sum(c.get('total_amount', 0.0) for c in claims)
        approved_amount = sum(c.get('audit_results', {}).get('approved_amount', 0.0) for c in claims)
        high_risk_count = len([c for c in claims if c.get('risk_level') == RiskLevel.HIGH.value])
        
        return {
            'claim_count': len(claims),
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'csr': approved_amount / total_amount if total_amount > 0 else 0.0,
            'avg_claim_amount': total_amount / len(claims),
            'high_risk_percentage': (high_risk_count / len(claims) * 100) if claims else 0.0
        }

class MetricsTrackingService:
    """Service for tracking metrics and improvements"""
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
    
    def track_processing_time_improvement(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Track processing time improvements
        
        Args:
            hospital_id: Hospital identifier
            start_date: Start date
            end_date: End date
        
        Returns:
            Processing time metrics
        """
        # Get all claims in date range
        patients = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "PATIENT#")
        
        all_claims = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            if patient_id:
                claims = self.db_client.query_items(f"PATIENT#{patient_id}", "CLAIM#")
                all_claims.extend(claims)
        
        # Filter by date
        filtered_claims = [
            c for c in all_claims
            if start_date <= c.get('created_at', '') <= end_date
        ]
        
        # Calculate processing times
        processing_times = []
        for claim in filtered_claims:
            audit_results = claim.get('audit_results', {})
            processing_time = audit_results.get('processing_time_seconds', 0.0)
            if processing_time > 0:
                processing_times.append(processing_time)
        
        if not processing_times:
            return {
                'success': False,
                'error': 'No processing time data available'
            }
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        min_processing_time = min(processing_times)
        max_processing_time = max(processing_times)
        
        return {
            'success': True,
            'metric_type': 'PROCESSING_TIME',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_claims_processed': len(processing_times),
            'average_processing_time': avg_processing_time,
            'min_processing_time': min_processing_time,
            'max_processing_time': max_processing_time,
            'generated_at': get_timestamp()
        }
    
    def calculate_cost_savings(
        self,
        hospital_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Calculate cost savings from optimization
        
        Args:
            hospital_id: Hospital identifier
            start_date: Start date
            end_date: End date
        
        Returns:
            Cost savings metrics
        """
        # Get all claims in date range
        patients = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "PATIENT#")
        
        all_claims = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            if patient_id:
                claims = self.db_client.query_items(f"PATIENT#{patient_id}", "CLAIM#")
                all_claims.extend(claims)
        
        # Filter by date
        filtered_claims = [
            c for c in all_claims
            if start_date <= c.get('created_at', '') <= end_date
        ]
        
        # Calculate savings from optimization suggestions
        total_potential_savings = 0.0
        claims_with_suggestions = 0
        
        for claim in filtered_claims:
            audit_results = claim.get('audit_results', {})
            ai_suggestions = audit_results.get('ai_optimization_suggestions', [])
            
            if ai_suggestions:
                claims_with_suggestions += 1
                # Estimate potential savings (simplified)
                rejected_amount = audit_results.get('rejected_amount', 0.0)
                # Assume 30% of rejected amount could be recovered with optimization
                total_potential_savings += rejected_amount * 0.3
        
        return {
            'success': True,
            'metric_type': 'COST_SAVINGS',
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'total_claims': len(filtered_claims),
            'claims_with_optimization_suggestions': claims_with_suggestions,
            'estimated_potential_savings': total_potential_savings,
            'generated_at': get_timestamp()
        }
