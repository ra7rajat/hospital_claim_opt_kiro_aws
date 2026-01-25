"""
Property-Based Tests for Risk Assessment
Tests Properties 12-14 for risk scoring validation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-functions', 'risk-scorer'))

import unittest
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List

from risk_scorer import RiskScoringEngine
from data_models import Claim, ClaimItem, RiskLevel, ClaimStatus, AuditStatus
from database_access import DynamoDBAccessLayer

# Test data generators
@st.composite
def claim_data_strategy(draw):
    """Generate valid claim data"""
    claim_id = f"clm_{draw(st.integers(min_value=1000, max_value=9999))}"
    patient_id = f"pat_{draw(st.integers(min_value=100, max_value=999))}"
    hospital_id = f"hosp_{draw(st.integers(min_value=10, max_value=99))}"
    
    total_items = draw(st.integers(min_value=1, max_value=100))
    approved_items = draw(st.integers(min_value=0, max_value=total_items))
    rejected_items = draw(st.integers(min_value=0, max_value=total_items - approved_items))
    review_items = total_items - approved_items - rejected_items
    
    total_amount = draw(st.floats(min_value=1000.0, max_value=1000000.0))
    approved_amount = draw(st.floats(min_value=0.0, max_value=total_amount))
    rejected_amount = total_amount - approved_amount
    
    return {
        'claim_id': claim_id,
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'status': draw(st.sampled_from([
            ClaimStatus.AUDITED.value,
            ClaimStatus.SUBMITTED.value,
            ClaimStatus.APPROVED.value
        ])),
        'total_amount': total_amount,
        'risk_score': 0,
        'risk_level': RiskLevel.MEDIUM.value,
        'audit_results': {
            'total_items': total_items,
            'approved_items': approved_items,
            'rejected_items': rejected_items,
            'review_items': review_items,
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'rejected_amount': rejected_amount
        }
    }

@st.composite
def claim_items_strategy(draw, claim_id: str, num_items: int):
    """Generate claim items for a claim"""
    items = []
    for i in range(num_items):
        item = {
            'item_id': f"item_{i}",
            'claim_id': claim_id,
            'description': draw(st.text(min_size=10, max_size=50)),
            'cost': draw(st.floats(min_value=100.0, max_value=100000.0)),
            'category': draw(st.sampled_from(['accommodation', 'surgery', 'diagnostics', 'pharmacy'])),
            'audit_status': draw(st.sampled_from([
                AuditStatus.APPROVED.value,
                AuditStatus.REJECTED.value,
                AuditStatus.REQUIRES_REVIEW.value
            ]))
        }
        items.append(item)
    return items

class TestRiskAssessmentProperties(unittest.TestCase):
    """Property-based tests for risk assessment"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_client = Mock(spec=DynamoDBAccessLayer)
        self.risk_engine = RiskScoringEngine(self.mock_db_client)
    
    @given(claim_data=claim_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_12_risk_score_assignment(self, claim_data):
        """
        Property 12: Risk Score Assignment
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        
        Every claim must be assigned:
        1. A risk score between 0-100
        2. A risk level (High/Medium/Low)
        3. Clear explanations for the risk assessment
        """
        # Setup mocks
        self.mock_db_client.get_item.return_value = claim_data
        self.mock_db_client.query_items.return_value = []
        self.mock_db_client.put_item.return_value = True
        
        # Calculate risk score
        result = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=claim_data
        )
        
        # Verify success
        self.assertTrue(result['success'], "Risk calculation should succeed")
        
        # Property: Risk score must be in valid range
        risk_score = result['risk_score']
        self.assertGreaterEqual(
            risk_score,
            0,
            "Risk score must be >= 0"
        )
        self.assertLessEqual(
            risk_score,
            100,
            "Risk score must be <= 100"
        )
        
        # Property: Risk level must be valid
        risk_level = result['risk_level']
        self.assertIn(
            risk_level,
            [RiskLevel.HIGH.value, RiskLevel.MEDIUM.value, RiskLevel.LOW.value],
            "Risk level must be valid"
        )
        
        # Property: Risk level must be consistent with score
        if risk_score >= 70:
            self.assertEqual(
                risk_level,
                RiskLevel.HIGH.value,
                "High score should result in HIGH risk level"
            )
        elif risk_score >= 40:
            self.assertEqual(
                risk_level,
                RiskLevel.MEDIUM.value,
                "Medium score should result in MEDIUM risk level"
            )
        else:
            self.assertEqual(
                risk_level,
                RiskLevel.LOW.value,
                "Low score should result in LOW risk level"
            )
        
        # Property: Must have risk factors
        self.assertIn('risk_factors', result)
        risk_factors = result['risk_factors']
        self.assertIsInstance(risk_factors, dict)
        self.assertGreater(len(risk_factors), 0, "Must have risk factors")
        
        # Property: Must have explanation
        self.assertIn('explanation', result)
        self.assertIsInstance(result['explanation'], str)
        self.assertGreater(
            len(result['explanation']),
            0,
            "Explanation must not be empty"
        )
        
        # Property: Must have recommendations
        self.assertIn('recommendations', result)
        self.assertIsInstance(result['recommendations'], list)
    
    @given(claim_data=claim_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_13_risk_score_updates(self, claim_data):
        """
        Property 13: Risk Score Updates
        **Validates: Requirements 4.4**
        
        When claim data changes, risk scores must be recalculated and updated.
        """
        # Ensure we start with a low amount to test the update
        assume(claim_data['total_amount'] < 100000.0)
        
        # Setup initial state
        self.mock_db_client.get_item.return_value = claim_data
        self.mock_db_client.query_items.return_value = []
        self.mock_db_client.put_item.return_value = True
        
        # Calculate initial risk
        result1 = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=claim_data
        )
        
        initial_score = result1['risk_score']
        
        # Modify claim data significantly (change to very high amount)
        modified_claim = claim_data.copy()
        modified_claim['total_amount'] = 600000.0  # Very high amount
        modified_claim['audit_results'] = claim_data['audit_results'].copy()
        modified_claim['audit_results']['total_amount'] = 600000.0
        
        self.mock_db_client.get_item.return_value = modified_claim
        
        # Recalculate risk
        result2 = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=modified_claim
        )
        
        updated_score = result2['risk_score']
        
        # Property: Risk score should change when claim amount changes significantly
        self.assertNotEqual(
            initial_score,
            updated_score,
            "Risk score should update when claim data changes significantly"
        )
        
        # Property: Higher amount should result in higher score
        self.assertGreater(
            updated_score,
            initial_score,
            "Higher claim amount should increase risk score"
        )
        
        # Property: Database update should be called
        self.assertTrue(
            self.mock_db_client.put_item.called,
            "Risk update should persist to database"
        )
    
    @given(
        num_claims=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_14_multi_claim_risk_aggregation(self, num_claims):
        """
        Property 14: Multi-claim Risk Aggregation
        **Validates: Requirements 4.5**
        
        Aggregated risk across multiple claims must:
        1. Calculate average risk score
        2. Identify high-risk claims
        3. Provide risk distribution
        4. Be consistent with individual scores
        """
        # Generate multiple claims
        patient_id = "pat_test"
        hospital_id = "hosp_test"
        
        claims = []
        individual_scores = []
        
        for i in range(num_claims):
            claim_data = {
                'claim_id': f"clm_{i}",
                'patient_id': patient_id,
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value,
                'total_amount': 50000.0 * (i + 1),
                'risk_score': 0,
                'risk_level': RiskLevel.MEDIUM.value,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 8,
                    'rejected_items': 2,
                    'review_items': 0,
                    'total_amount': 50000.0 * (i + 1),
                    'approved_amount': 40000.0 * (i + 1),
                    'rejected_amount': 10000.0 * (i + 1)
                }
            }
            claims.append(claim_data)
        
        # Setup mocks
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            claims if pk == f"PATIENT#{patient_id}" else []
        )
        self.mock_db_client.get_item.side_effect = lambda pk, sk: (
            next((c for c in claims if c['claim_id'] in sk), None)
        )
        self.mock_db_client.put_item.return_value = True
        
        # Calculate aggregated risk
        result = self.risk_engine.calculate_aggregated_risk(
            patient_id=patient_id,
            hospital_id=hospital_id
        )
        
        # Verify success
        self.assertTrue(result['success'], "Aggregated risk calculation should succeed")
        
        # Property: Total claims should match
        self.assertEqual(
            result['total_claims'],
            num_claims,
            "Total claims should match input"
        )
        
        # Property: Average risk score should be in valid range
        avg_risk = result['average_risk_score']
        self.assertGreaterEqual(avg_risk, 0, "Average risk must be >= 0")
        self.assertLessEqual(avg_risk, 100, "Average risk must be <= 100")
        
        # Property: Max risk should be >= average
        self.assertGreaterEqual(
            result['max_risk_score'],
            avg_risk,
            "Max risk should be >= average"
        )
        
        # Property: Min risk should be <= average
        self.assertLessEqual(
            result['min_risk_score'],
            avg_risk,
            "Min risk should be <= average"
        )
        
        # Property: Risk distribution should sum to total claims
        distribution = result['risk_distribution']
        total_distributed = (
            distribution['high'] +
            distribution['medium'] +
            distribution['low']
        )
        self.assertEqual(
            total_distributed,
            num_claims,
            "Risk distribution should sum to total claims"
        )
        
        # Property: Overall risk level should be consistent with average
        overall_level = result['overall_risk_level']
        if avg_risk >= 70:
            self.assertEqual(overall_level, RiskLevel.HIGH.value)
        elif avg_risk >= 40:
            self.assertEqual(overall_level, RiskLevel.MEDIUM.value)
        else:
            self.assertEqual(overall_level, RiskLevel.LOW.value)
    
    @given(claim_data=claim_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_risk_factors_completeness(self, claim_data):
        """
        Additional Property: Risk Factors Completeness
        
        All expected risk factors should be calculated and included.
        """
        # Setup
        self.mock_db_client.get_item.return_value = claim_data
        self.mock_db_client.query_items.return_value = []
        self.mock_db_client.put_item.return_value = True
        
        # Calculate risk
        result = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=claim_data
        )
        
        # Property: All expected risk factors should be present
        expected_factors = [
            'claim_amount',
            'policy_complexity',
            'procedure_count',
            'rejection_history',
            'documentation_completeness',
            'procedure_combinations'
        ]
        
        risk_factors = result['risk_factors']
        
        for factor in expected_factors:
            self.assertIn(
                factor,
                risk_factors,
                f"Risk factor '{factor}' should be present"
            )
            
            # Property: Each factor should be in valid range
            factor_score = risk_factors[factor]
            self.assertGreaterEqual(
                factor_score,
                0.0,
                f"Factor '{factor}' should be >= 0"
            )
            self.assertLessEqual(
                factor_score,
                100.0,
                f"Factor '{factor}' should be <= 100"
            )
    
    @given(claim_data=claim_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_risk_determinism(self, claim_data):
        """
        Additional Property: Risk Determinism
        
        Calculating risk for the same claim data should produce consistent results.
        """
        # Setup
        self.mock_db_client.get_item.return_value = claim_data
        self.mock_db_client.query_items.return_value = []
        self.mock_db_client.put_item.return_value = True
        
        # Calculate risk twice
        result1 = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=claim_data
        )
        
        result2 = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=claim_data
        )
        
        # Property: Results should be identical
        self.assertEqual(
            result1['risk_score'],
            result2['risk_score'],
            "Risk score should be deterministic"
        )
        self.assertEqual(
            result1['risk_level'],
            result2['risk_level'],
            "Risk level should be deterministic"
        )
        self.assertEqual(
            result1['risk_factors'],
            result2['risk_factors'],
            "Risk factors should be deterministic"
        )
    
    @given(claim_data=claim_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_property_high_amount_high_risk(self, claim_data):
        """
        Additional Property: High Amount Correlation
        
        Very high claim amounts should result in higher risk scores.
        """
        # Setup
        self.mock_db_client.query_items.return_value = []
        self.mock_db_client.put_item.return_value = True
        
        # Test with low amount
        low_amount_claim = claim_data.copy()
        low_amount_claim['total_amount'] = 10000.0
        low_amount_claim['audit_results'] = claim_data['audit_results'].copy()
        low_amount_claim['audit_results']['total_amount'] = 10000.0
        
        self.mock_db_client.get_item.return_value = low_amount_claim
        
        result_low = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=low_amount_claim
        )
        
        # Test with high amount
        high_amount_claim = claim_data.copy()
        high_amount_claim['total_amount'] = 500000.0
        high_amount_claim['audit_results'] = claim_data['audit_results'].copy()
        high_amount_claim['audit_results']['total_amount'] = 500000.0
        
        self.mock_db_client.get_item.return_value = high_amount_claim
        
        result_high = self.risk_engine.calculate_risk_score(
            claim_id=claim_data['claim_id'],
            patient_id=claim_data['patient_id'],
            hospital_id=claim_data['hospital_id'],
            claim_data=high_amount_claim
        )
        
        # Property: High amount should result in higher risk
        self.assertGreater(
            result_high['risk_score'],
            result_low['risk_score'],
            "Higher claim amount should result in higher risk score"
        )

def test_risk_assessment_integration():
    """Integration test for risk assessment workflow"""
    # Setup
    mock_db_client = Mock(spec=DynamoDBAccessLayer)
    risk_engine = RiskScoringEngine(mock_db_client)
    
    # Create test claim
    claim_data = {
        'claim_id': 'clm_test',
        'patient_id': 'pat_test',
        'hospital_id': 'hosp_test',
        'status': ClaimStatus.AUDITED.value,
        'total_amount': 150000.0,
        'risk_score': 0,
        'risk_level': RiskLevel.MEDIUM.value,
        'audit_results': {
            'total_items': 25,
            'approved_items': 20,
            'rejected_items': 3,
            'review_items': 2,
            'total_amount': 150000.0,
            'approved_amount': 120000.0,
            'rejected_amount': 30000.0
        }
    }
    
    mock_db_client.get_item.return_value = claim_data
    mock_db_client.query_items.return_value = []
    mock_db_client.put_item.return_value = True
    
    # Calculate risk
    result = risk_engine.calculate_risk_score(
        claim_id='clm_test',
        patient_id='pat_test',
        hospital_id='hosp_test',
        claim_data=claim_data
    )
    
    # Verify
    assert result['success'] is True
    assert 0 <= result['risk_score'] <= 100
    assert result['risk_level'] in [RiskLevel.HIGH.value, RiskLevel.MEDIUM.value, RiskLevel.LOW.value]
    assert len(result['risk_factors']) > 0
    assert len(result['explanation']) > 0
    assert isinstance(result['recommendations'], list)

if __name__ == '__main__':
    unittest.main()
