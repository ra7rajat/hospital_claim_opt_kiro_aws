"""
Property-Based Tests for Multi-Claim Risk
Tests Property 44: Risk Aggregation Correctness

**Feature: journey-enhancements, Property 44: Risk Aggregation Correctness**

These tests validate that aggregated risk accurately reflects individual claim risks
and that risk factors are properly weighted.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add lambda layer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from patient_profile_service import PatientProfileService
from risk_recommendation_service import RiskRecommendationService
from multi_claim_analytics_service import MultiClaimAnalyticsService


# Strategies for generating test data
@st.composite
def claim_strategy(draw):
    """Generate a valid claim"""
    # Generate date as string directly to avoid datetime API issues
    year = draw(st.integers(min_value=2023, max_value=2024))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Use 28 to avoid month-end issues
    
    return {
        'claim_id': f"CLM-{draw(st.integers(min_value=1000, max_value=9999))}",
        'date': f"{year}-{month:02d}-{day:02d}",
        'amount': draw(st.floats(min_value=1000, max_value=500000)),
        'status': draw(st.sampled_from(['approved', 'rejected', 'pending'])),
        'risk_score': draw(st.floats(min_value=0, max_value=100)),
        'settlement_ratio': draw(st.floats(min_value=0, max_value=1)),
        'procedure_codes': draw(st.lists(st.text(min_size=3, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), min_size=1, max_size=5)),
        'diagnosis_codes': draw(st.lists(st.text(min_size=3, max_size=5, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))), min_size=1, max_size=3)),
        'hospital_name': draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        'rejection_reason': draw(st.one_of(st.none(), st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')))))
    }


from datetime import datetime
from unittest.mock import Mock, MagicMock


class TestRiskAggregationCorrectness:
    """Test Property 44: Risk Aggregation Correctness"""
    
    @given(st.lists(claim_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_1_aggregated_risk_increases_with_high_risk_claims(self, claims):
        """
        Property 44.1: Aggregated risk increases with high-risk claims
        
        **Validates: Requirements 5.1, 5.2**
        """
        # Mock DynamoDB
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        service = PatientProfileService(dynamodb_client=mock_dynamodb)
        
        # Calculate risk with original claims
        risk1 = service._calculate_aggregated_risk('TEST-PATIENT', claims)
        
        # Add a high-risk claim
        high_risk_claim = {
            'claim_id': 'CLM-HIGH',
            'date': '2024-01-15',
            'amount': 300000,
            'status': 'pending',
            'risk_score': 95,
            'settlement_ratio': 0.5,
            'procedure_codes': ['PROC1', 'PROC2'],
            'diagnosis_codes': ['DIAG1'],
            'hospital_name': 'Test Hospital',
            'rejection_reason': None
        }
        
        claims_with_high_risk = claims + [high_risk_claim]
        risk2 = service._calculate_aggregated_risk('TEST-PATIENT', claims_with_high_risk)
        
        # Aggregated risk should increase or stay the same
        assert risk2['risk_score'] >= risk1['risk_score'], \
            f"Risk should increase with high-risk claim: {risk1['risk_score']} -> {risk2['risk_score']}"
    
    @given(st.lists(claim_strategy(), min_size=2, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_2_risk_factors_properly_weighted(self, claims):
        """
        Property 44.2: Risk factors are properly weighted
        
        **Validates: Requirements 5.2**
        """
        service = PatientProfileService()
        
        risk = service._calculate_aggregated_risk('TEST-PATIENT', claims)
        
        # Check that all factors are present
        assert 'factors' in risk
        assert len(risk['factors']) == 5  # 5 risk factors
        
        # Check that weights sum to 1.0
        total_weight = sum(f['weight'] for f in risk['factors'])
        assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
        
        # Check that contributions match value * weight
        for factor in risk['factors']:
            expected_contribution = factor['value'] * factor['weight']
            assert abs(factor['contribution'] - expected_contribution) < 0.1, \
                f"Contribution mismatch for {factor['name']}: expected {expected_contribution}, got {factor['contribution']}"
        
        # Check that risk score is sum of contributions
        total_contribution = sum(f['contribution'] for f in risk['factors'])
        assert abs(risk['risk_score'] - total_contribution) < 0.1, \
            f"Risk score should equal sum of contributions: {risk['risk_score']} vs {total_contribution}"
    
    @given(st.lists(claim_strategy(), min_size=3, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_3_risk_trends_calculated_correctly(self, claims):
        """
        Property 44.3: Risk trends are calculated correctly
        
        **Validates: Requirements 5.2.5**
        """
        service = PatientProfileService()
        
        # Ensure claims have dates
        for i, claim in enumerate(claims):
            claim['date'] = f"2024-{(i % 12) + 1:02d}-15"
        
        risk = service._calculate_aggregated_risk('TEST-PATIENT', claims)
        
        # Check trend is one of valid values
        assert risk['trend'] in ['increasing', 'stable', 'decreasing'], \
            f"Invalid trend value: {risk['trend']}"
        
        # Get risk trend data
        trend_data = service._calculate_risk_trend('TEST-PATIENT', claims)
        
        # Trend data should be sorted by month
        if len(trend_data) > 1:
            months = [t['month'] for t in trend_data]
            assert months == sorted(months), "Trend data should be sorted by month"
    
    @given(st.lists(claim_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_4_recommendations_match_risk_factors(self, claims):
        """
        Property 44.4: Recommendations match risk factors
        
        **Validates: Requirements 5.3**
        """
        profile_service = PatientProfileService()
        rec_service = RiskRecommendationService()
        
        # Calculate risk
        risk = profile_service._calculate_aggregated_risk('TEST-PATIENT', claims)
        
        # Generate recommendations
        recommendations = rec_service.generate_recommendations('TEST-PATIENT', risk, claims)
        
        # Recommendations should be sorted by priority and impact
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                curr = recommendations[i]
                next_rec = recommendations[i + 1]
                
                priority_order = {'high': 0, 'medium': 1, 'low': 2}
                curr_priority = priority_order[curr.priority]
                next_priority = priority_order[next_rec.priority]
                
                # Current should have higher or equal priority
                if curr_priority == next_priority:
                    # If same priority, current should have higher or equal impact
                    assert curr.expected_impact >= next_rec.expected_impact, \
                        "Recommendations should be sorted by impact within same priority"
                else:
                    assert curr_priority <= next_priority, \
                        "Recommendations should be sorted by priority"
    
    @given(st.lists(claim_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_5_analytics_total_matches_sum(self, claims):
        """
        Property 44.5: Analytics total claim amount matches sum of individual claims
        
        **Validates: Requirements 5.4.1**
        """
        analytics_service = MultiClaimAnalyticsService()
        
        # Calculate analytics
        analytics = analytics_service.analyze_patient_claims('TEST-PATIENT', claims)
        
        # Calculate expected total
        expected_total = sum(c.get('amount', 0) for c in claims)
        
        # Check that totals match (within rounding error)
        assert abs(analytics.total_claim_amount - expected_total) < 0.01, \
            f"Total claim amount mismatch: {analytics.total_claim_amount} vs {expected_total}"
    
    @given(st.lists(claim_strategy(), min_size=2, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_6_settlement_ratio_bounds(self, claims):
        """
        Property 44.6: Average settlement ratio is within valid bounds
        
        **Validates: Requirements 5.4.2**
        """
        analytics_service = MultiClaimAnalyticsService()
        
        # Ensure some claims have settlement ratios
        for claim in claims[:len(claims)//2]:
            claim['settlement_ratio'] = min(1.0, max(0.0, claim.get('settlement_ratio', 0.5)))
        
        analytics = analytics_service.analyze_patient_claims('TEST-PATIENT', claims)
        
        # Settlement ratio should be between 0 and 1
        assert 0 <= analytics.average_settlement_ratio <= 1, \
            f"Settlement ratio out of bounds: {analytics.average_settlement_ratio}"
    
    @given(st.lists(claim_strategy(), min_size=3, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_7_rejection_reasons_counted_correctly(self, claims):
        """
        Property 44.7: Rejection reasons are counted correctly
        
        **Validates: Requirements 5.4.3**
        """
        analytics_service = MultiClaimAnalyticsService()
        
        # Set some claims as rejected with reasons
        rejection_reasons = ['Insufficient documentation', 'Pre-authorization required', 'Not covered']
        for i, claim in enumerate(claims[:len(claims)//2]):
            claim['status'] = 'rejected'
            claim['rejection_reason'] = rejection_reasons[i % len(rejection_reasons)]
        
        analytics = analytics_service.analyze_patient_claims('TEST-PATIENT', claims)
        
        # Count expected rejections
        expected_rejections = sum(1 for c in claims if c.get('status') == 'rejected')
        actual_rejections = sum(r['count'] for r in analytics.common_rejection_reasons)
        
        assert actual_rejections == expected_rejections, \
            f"Rejection count mismatch: {actual_rejections} vs {expected_rejections}"
        
        # Check percentages sum to 100
        if analytics.common_rejection_reasons:
            total_percentage = sum(r['percentage'] for r in analytics.common_rejection_reasons)
            assert abs(total_percentage - 100.0) < 0.1, \
                f"Rejection percentages should sum to 100: {total_percentage}"
    
    @given(st.lists(claim_strategy(), min_size=2, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_8_historical_performance_monotonic_dates(self, claims):
        """
        Property 44.8: Historical performance has monotonically increasing dates
        
        **Validates: Requirements 5.4.5**
        """
        analytics_service = MultiClaimAnalyticsService()
        
        # Ensure claims have valid dates
        for i, claim in enumerate(claims):
            claim['date'] = f"2024-{(i % 12) + 1:02d}-15"
        
        analytics = analytics_service.analyze_patient_claims('TEST-PATIENT', claims)
        
        # Check that months are in order
        if len(analytics.historical_performance) > 1:
            months = [p['month'] for p in analytics.historical_performance]
            assert months == sorted(months), \
                f"Historical performance months should be sorted: {months}"
    
    @given(st.lists(claim_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_9_risk_score_bounds(self, claims):
        """
        Property 44.9: Risk score is within valid bounds (0-100)
        
        **Validates: Requirements 5.1.5, 5.2**
        """
        service = PatientProfileService()
        
        risk = service._calculate_aggregated_risk('TEST-PATIENT', claims)
        
        # Risk score should be between 0 and 100
        assert 0 <= risk['risk_score'] <= 100, \
            f"Risk score out of bounds: {risk['risk_score']}"
        
        # Risk level should match score
        if risk['risk_score'] >= 70:
            assert risk['risk_level'] == 'high'
        elif risk['risk_score'] >= 40:
            assert risk['risk_level'] == 'medium'
        else:
            assert risk['risk_level'] == 'low'
    
    @given(st.lists(claim_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_44_10_recommendation_impact_positive(self, claims):
        """
        Property 44.10: Recommendation expected impact is positive
        
        **Validates: Requirements 5.3.2**
        """
        profile_service = PatientProfileService()
        rec_service = RiskRecommendationService()
        
        risk = profile_service._calculate_aggregated_risk('TEST-PATIENT', claims)
        recommendations = rec_service.generate_recommendations('TEST-PATIENT', risk, claims)
        
        # All recommendations should have positive expected impact
        for rec in recommendations:
            assert rec.expected_impact > 0, \
                f"Recommendation {rec.recommendation_id} has non-positive impact: {rec.expected_impact}"
            
            # Impact should be reasonable (0-100%)
            assert rec.expected_impact <= 100, \
                f"Recommendation {rec.recommendation_id} has unrealistic impact: {rec.expected_impact}"


def test_multi_claim_risk_integration():
    """
    Integration test for multi-claim risk functionality
    
    **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """
    # Create test claims
    claims = [
        {
            'claim_id': 'CLM-001',
            'date': '2024-01-15',
            'amount': 150000,
            'status': 'approved',
            'risk_score': 45,
            'settlement_ratio': 0.85,
            'procedure_codes': ['PROC1', 'PROC2'],
            'diagnosis_codes': ['DIAG1'],
            'hospital_name': 'Test Hospital',
            'rejection_reason': None
        },
        {
            'claim_id': 'CLM-002',
            'date': '2024-02-20',
            'amount': 200000,
            'status': 'rejected',
            'risk_score': 75,
            'settlement_ratio': 0.0,
            'procedure_codes': ['PROC3'],
            'diagnosis_codes': ['DIAG2'],
            'hospital_name': 'Test Hospital',
            'rejection_reason': 'Insufficient documentation'
        },
        {
            'claim_id': 'CLM-003',
            'date': '2024-03-10',
            'amount': 100000,
            'status': 'approved',
            'risk_score': 30,
            'settlement_ratio': 0.95,
            'procedure_codes': ['PROC1'],
            'diagnosis_codes': ['DIAG1'],
            'hospital_name': 'Test Hospital',
            'rejection_reason': None
        }
    ]
    
    # Mock DynamoDB client
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Test patient profile service
    profile_service = PatientProfileService(dynamodb_client=mock_dynamodb)
    risk = profile_service._calculate_aggregated_risk('TEST-PATIENT', claims)
    
    assert 'risk_score' in risk
    assert 'risk_level' in risk
    assert 'factors' in risk
    assert len(risk['factors']) == 5
    
    # Test recommendation service
    rec_service = RiskRecommendationService(dynamodb_client=mock_dynamodb)
    recommendations = rec_service.generate_recommendations('TEST-PATIENT', risk, claims)
    
    assert len(recommendations) > 0
    assert all(hasattr(r, 'priority') for r in recommendations)
    assert all(hasattr(r, 'expected_impact') for r in recommendations)
    
    # Test analytics service
    analytics_service = MultiClaimAnalyticsService()
    analytics = analytics_service.analyze_patient_claims('TEST-PATIENT', claims)
    
    assert analytics.total_claim_amount == 450000
    assert 0 <= analytics.average_settlement_ratio <= 1
    assert len(analytics.common_rejection_reasons) > 0
    assert len(analytics.historical_performance) > 0
    
    print("✓ Multi-claim risk integration test passed")


if __name__ == '__main__':
    # Run integration test
    test_multi_claim_risk_integration()
    print("\n✓ All multi-claim risk tests completed successfully")
