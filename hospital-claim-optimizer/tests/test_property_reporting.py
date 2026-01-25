"""
Property-Based Tests for Reporting System
Tests Properties 28-30 for report generation and metrics tracking
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

import unittest
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List
from datetime import datetime, timedelta

from reporting_service import ReportingService, MetricsTrackingService
from data_models import ClaimStatus, RiskLevel
from database_access import DynamoDBAccessLayer

# Test data generators
@st.composite
def claim_with_audit_strategy(draw):
    """Generate claim with audit results"""
    claim_id = f"clm_{draw(st.integers(min_value=1000, max_value=9999))}"
    patient_id = f"pat_{draw(st.integers(min_value=100, max_value=999))}"
    
    total_amount = draw(st.floats(min_value=1000.0, max_value=500000.0))
    approved_amount = draw(st.floats(min_value=0.0, max_value=total_amount))
    
    # Generate date within last year
    days_ago = draw(st.integers(min_value=0, max_value=365))
    created_at = (datetime.utcnow() - timedelta(days=days_ago)).isoformat()
    
    return {
        'claim_id': claim_id,
        'patient_id': patient_id,
        'hospital_id': 'hosp_test',
        'status': ClaimStatus.AUDITED.value,
        'total_amount': total_amount,
        'risk_level': draw(st.sampled_from([
            RiskLevel.HIGH.value,
            RiskLevel.MEDIUM.value,
            RiskLevel.LOW.value
        ])),
        'audit_results': {
            'total_items': draw(st.integers(min_value=1, max_value=50)),
            'approved_items': draw(st.integers(min_value=0, max_value=50)),
            'rejected_items': draw(st.integers(min_value=0, max_value=50)),
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'rejected_amount': total_amount - approved_amount,
            'processing_time_seconds': draw(st.floats(min_value=1.0, max_value=30.0)),
            'ai_optimization_suggestions': [
                {'suggestion': 'Test suggestion'}
            ] if draw(st.booleans()) else []
        },
        'created_at': created_at,
        'PK': f"PATIENT#{patient_id}",
        'SK': f"CLAIM#{claim_id}"
    }

class TestReportingProperties(unittest.TestCase):
    """Property-based tests for reporting system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_client = Mock(spec=DynamoDBAccessLayer)
        self.reporting_service = ReportingService(self.mock_db_client)
        self.metrics_service = MetricsTrackingService(self.mock_db_client)
    
    @given(
        num_claims=st.integers(min_value=5, max_value=30)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_28_report_generation_completeness(self, num_claims):
        """
        Property 28: Report Generation Completeness
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4**
        
        Generated reports must include:
        1. All required data fields
        2. Accurate calculations
        3. Proper date range filtering
        4. Complete metadata
        """
        hospital_id = "hosp_test"
        
        # Generate test claims
        claims = []
        for i in range(num_claims):
            total_amount = 10000.0 * (i + 1)
            approved_amount = total_amount * 0.8
            
            claim = {
                'claim_id': f"clm_{i}",
                'patient_id': f"pat_{i % 5}",  # 5 patients
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': total_amount,
                'risk_level': RiskLevel.MEDIUM.value if i % 2 == 0 else RiskLevel.HIGH.value,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 8,
                    'rejected_items': 2,
                    'total_amount': total_amount,
                    'approved_amount': approved_amount,
                    'rejected_amount': total_amount - approved_amount
                },
                'created_at': f"2024-01-{(i % 28) + 1:02d}T00:00:00Z"
            }
            claims.append(claim)
        
        # Setup mocks
        patients = [{'patient_id': f"pat_{i}", 'hospital_id': hospital_id} for i in range(5)]
        
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            patients if "HOSPITAL#" in pk else
            [c for c in claims if c['patient_id'] in pk]
        )
        
        # Generate CSR trend report
        result = self.reporting_service.generate_csr_trend_report(
            hospital_id=hospital_id,
            start_date='2024-01-01T00:00:00Z',
            end_date='2024-01-31T23:59:59Z'
        )
        
        # Property: Report must be successful
        self.assertTrue(result['success'], "Report generation should succeed")
        
        # Property: Report must have required fields
        required_fields = [
            'report_type',
            'period',
            'overall_csr',
            'total_claims',
            'total_amount',
            'approved_amount',
            'monthly_csr',
            'csr_by_risk_level',
            'trend',
            'generated_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Report must include {field}")
        
        # Property: CSR must be in valid range
        overall_csr = result['overall_csr']
        self.assertGreaterEqual(overall_csr, 0.0, "CSR must be >= 0")
        self.assertLessEqual(overall_csr, 1.0, "CSR must be <= 1.0")
        
        # Property: Total claims must match
        self.assertEqual(
            result['total_claims'],
            num_claims,
            "Total claims must match input"
        )
        
        # Property: Total amount must be sum of all claims
        expected_total = sum(c['total_amount'] for c in claims)
        self.assertAlmostEqual(
            result['total_amount'],
            expected_total,
            places=2,
            msg="Total amount must match sum of claims"
        )
        
        # Property: Approved amount must be consistent with CSR
        expected_approved = sum(c['audit_results']['approved_amount'] for c in claims)
        self.assertAlmostEqual(
            result['approved_amount'],
            expected_approved,
            places=2,
            msg="Approved amount must be accurate"
        )
        
        # Property: CSR calculation must be correct
        expected_csr = expected_approved / expected_total if expected_total > 0 else 0.0
        self.assertAlmostEqual(
            overall_csr,
            expected_csr,
            places=4,
            msg="CSR calculation must be accurate"
        )
        
        # Property: Monthly CSR must be present
        self.assertIsInstance(result['monthly_csr'], list)
        
        # Property: Trend must be valid
        self.assertIn(
            result['trend'],
            ['improving', 'declining', 'stable', 'insufficient_data'],
            "Trend must be valid"
        )
    
    @given(
        num_claims=st.integers(min_value=10, max_value=30)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_29_metrics_tracking(self, num_claims):
        """
        Property 29: Metrics Tracking
        **Validates: Requirements 9.5**
        
        Metrics tracking must:
        1. Accurately track processing times
        2. Calculate cost savings correctly
        3. Provide meaningful statistics
        """
        hospital_id = "hosp_test"
        
        # Generate claims with processing times
        claims = []
        for i in range(num_claims):
            processing_time = 5.0 + (i * 0.5)  # Varying processing times
            
            claim = {
                'claim_id': f"clm_{i}",
                'patient_id': f"pat_{i % 5}",
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': 50000.0,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 7,
                    'rejected_items': 3,
                    'total_amount': 50000.0,
                    'approved_amount': 35000.0,
                    'rejected_amount': 15000.0,
                    'processing_time_seconds': processing_time,
                    'ai_optimization_suggestions': [
                        {'suggestion': 'Test'}
                    ] if i % 2 == 0 else []
                },
                'created_at': '2024-01-15T00:00:00Z'
            }
            claims.append(claim)
        
        # Setup mocks
        patients = [{'patient_id': f"pat_{i}", 'hospital_id': hospital_id} for i in range(5)]
        
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            patients if "HOSPITAL#" in pk else
            [c for c in claims if c['patient_id'] in pk]
        )
        
        # Track processing time
        result = self.metrics_service.track_processing_time_improvement(
            hospital_id=hospital_id,
            start_date='2024-01-01T00:00:00Z',
            end_date='2024-01-31T23:59:59Z'
        )
        
        # Property: Metrics must be successful
        self.assertTrue(result['success'], "Metrics tracking should succeed")
        
        # Property: Must include required fields
        self.assertIn('average_processing_time', result)
        self.assertIn('min_processing_time', result)
        self.assertIn('max_processing_time', result)
        self.assertIn('total_claims_processed', result)
        
        # Property: Claim count must match
        self.assertEqual(
            result['total_claims_processed'],
            num_claims,
            "Claim count must match"
        )
        
        # Property: Average must be within min/max range
        avg_time = result['average_processing_time']
        min_time = result['min_processing_time']
        max_time = result['max_processing_time']
        
        self.assertGreaterEqual(avg_time, min_time, "Average must be >= min")
        self.assertLessEqual(avg_time, max_time, "Average must be <= max")
        
        # Property: Processing times must be positive
        self.assertGreater(min_time, 0, "Min processing time must be positive")
        self.assertGreater(avg_time, 0, "Avg processing time must be positive")
        self.assertGreater(max_time, 0, "Max processing time must be positive")
    
    @given(
        num_claims=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_30_report_navigation(self, num_claims):
        """
        Property 30: Report Navigation
        **Validates: Requirements 9.6**
        
        Reports must support:
        1. Drill-down from summaries to details
        2. Filtering and sorting
        3. Data consistency across levels
        """
        hospital_id = "hosp_test"
        
        # Generate claims with rejection data
        claims = []
        claim_items_map = {}
        
        for i in range(num_claims):
            claim_id = f"clm_{i}"
            
            claim = {
                'claim_id': claim_id,
                'patient_id': f"pat_{i % 3}",
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': 50000.0,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 7,
                    'rejected_items': 3,
                    'total_amount': 50000.0,
                    'approved_amount': 35000.0,
                    'rejected_amount': 15000.0
                },
                'created_at': '2024-01-15T00:00:00Z'
            }
            claims.append(claim)
            
            # Generate claim items
            claim_items = []
            for j in range(3):  # 3 rejected items per claim
                item = {
                    'item_id': f"item_{i}_{j}",
                    'claim_id': claim_id,
                    'description': f"Item {j}",
                    'cost': 5000.0,
                    'audit_status': 'REJECTED',
                    'rejection_reason': f"Reason {j % 2}",  # 2 different reasons
                    'policy_clause_reference': f"Clause {j % 2}"
                }
                claim_items.append(item)
            
            claim_items_map[claim_id] = claim_items
        
        # Setup mocks
        patients = [{'patient_id': f"pat_{i}", 'hospital_id': hospital_id} for i in range(3)]
        
        def mock_query(pk, sk=None):
            if "HOSPITAL#" in pk:
                return patients
            elif "PATIENT#" in pk:
                return [c for c in claims if c['patient_id'] in pk]
            elif "CLAIM#" in pk:
                claim_id = pk.split('#')[1]
                return claim_items_map.get(claim_id, [])
            return []
        
        self.mock_db_client.query_items.side_effect = mock_query
        
        # Generate rejection analysis report
        result = self.reporting_service.generate_rejection_analysis_report(
            hospital_id=hospital_id,
            start_date='2024-01-01T00:00:00Z',
            end_date='2024-01-31T23:59:59Z'
        )
        
        # Property: Report must be successful
        self.assertTrue(result['success'], "Report generation should succeed")
        
        # Property: Must include drill-down data
        self.assertIn('top_rejection_reasons', result)
        self.assertIn('top_policy_clauses', result)
        
        # Property: Rejection reasons must be detailed
        rejection_reasons = result['top_rejection_reasons']
        self.assertIsInstance(rejection_reasons, list)
        
        for reason in rejection_reasons:
            # Property: Each reason must have required fields
            self.assertIn('reason', reason)
            self.assertIn('count', reason)
            self.assertIn('total_amount', reason)
            self.assertIn('percentage', reason)
            
            # Property: Percentage must be valid
            self.assertGreaterEqual(reason['percentage'], 0.0)
            self.assertLessEqual(reason['percentage'], 100.0)
        
        # Property: Total rejected items must match sum of reasons
        total_rejected = result['total_rejected_items']
        sum_of_reasons = sum(r['count'] for r in rejection_reasons)
        
        self.assertEqual(
            total_rejected,
            sum_of_reasons,
            "Total rejected items must match sum of reasons"
        )
        
        # Property: Policy clauses must be detailed
        policy_clauses = result['top_policy_clauses']
        self.assertIsInstance(policy_clauses, list)
        
        for clause in policy_clauses:
            self.assertIn('clause', clause)
            self.assertIn('count', clause)
            self.assertIn('total_amount', clause)
    
    @given(
        comparison_days=st.integers(min_value=7, max_value=90)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_benchmark_comparison_consistency(self, comparison_days):
        """
        Additional Property: Benchmark Comparison Consistency
        
        Benchmark reports must provide consistent comparisons between periods.
        """
        hospital_id = "hosp_test"
        
        # Generate claims for two periods
        end_date = datetime.utcnow()
        current_start = end_date - timedelta(days=comparison_days)
        previous_start = current_start - timedelta(days=comparison_days)
        
        # Current period claims
        current_claims = []
        for i in range(10):
            claim = {
                'claim_id': f"clm_current_{i}",
                'patient_id': f"pat_{i % 3}",
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': 50000.0,
                'risk_level': RiskLevel.MEDIUM.value,
                'audit_results': {
                    'approved_amount': 40000.0
                },
                'created_at': (current_start + timedelta(days=i)).isoformat()
            }
            current_claims.append(claim)
        
        # Previous period claims
        previous_claims = []
        for i in range(8):
            claim = {
                'claim_id': f"clm_previous_{i}",
                'patient_id': f"pat_{i % 3}",
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': 45000.0,
                'risk_level': RiskLevel.LOW.value,
                'audit_results': {
                    'approved_amount': 36000.0
                },
                'created_at': (previous_start + timedelta(days=i)).isoformat()
            }
            previous_claims.append(claim)
        
        all_claims = current_claims + previous_claims
        
        # Setup mocks
        patients = [{'patient_id': f"pat_{i}", 'hospital_id': hospital_id} for i in range(3)]
        
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            patients if "HOSPITAL#" in pk else
            [c for c in all_claims if c['patient_id'] in pk]
        )
        
        # Generate benchmark report
        result = self.reporting_service.generate_benchmark_report(
            hospital_id=hospital_id,
            comparison_period_days=comparison_days
        )
        
        # Property: Report must be successful
        self.assertTrue(result['success'], "Benchmark report should succeed")
        
        # Property: Must have both periods
        self.assertIn('current_period', result)
        self.assertIn('previous_period', result)
        self.assertIn('changes', result)
        
        # Property: Changes must be calculated correctly
        current_metrics = result['current_period']['metrics']
        previous_metrics = result['previous_period']['metrics']
        changes = result['changes']
        
        # Verify CSR change
        expected_csr_change = current_metrics['csr'] - previous_metrics['csr']
        self.assertAlmostEqual(
            changes['csr_change'],
            expected_csr_change,
            places=4,
            msg="CSR change must be accurate"
        )
        
        # Verify claim volume change
        expected_volume_change = current_metrics['claim_count'] - previous_metrics['claim_count']
        self.assertEqual(
            changes['claim_volume_change'],
            expected_volume_change,
            "Claim volume change must be accurate"
        )

def test_reporting_integration():
    """Integration test for reporting workflow"""
    # Setup
    mock_db_client = Mock(spec=DynamoDBAccessLayer)
    reporting_service = ReportingService(mock_db_client)
    
    # Create test data
    hospital_id = "hosp_test"
    patients = [{'patient_id': 'pat_001', 'hospital_id': hospital_id}]
    
    claims = [{
        'claim_id': 'clm_001',
        'patient_id': 'pat_001',
        'hospital_id': hospital_id,
        'status': ClaimStatus.AUDITED.value,
        'total_amount': 100000.0,
        'risk_level': RiskLevel.MEDIUM.value,
        'audit_results': {
            'total_items': 10,
            'approved_items': 8,
            'rejected_items': 2,
            'total_amount': 100000.0,
            'approved_amount': 80000.0,
            'rejected_amount': 20000.0
        },
        'created_at': '2024-01-15T00:00:00Z'
    }]
    
    mock_db_client.query_items.side_effect = lambda pk, sk=None: (
        patients if "HOSPITAL#" in pk else claims
    )
    
    # Generate CSR report
    result = reporting_service.generate_csr_trend_report(
        hospital_id=hospital_id,
        start_date='2024-01-01T00:00:00Z',
        end_date='2024-01-31T23:59:59Z'
    )
    
    # Verify
    assert result['success'] is True
    assert result['overall_csr'] == 0.8
    assert result['total_claims'] == 1
    assert result['total_amount'] == 100000.0

if __name__ == '__main__':
    unittest.main()
