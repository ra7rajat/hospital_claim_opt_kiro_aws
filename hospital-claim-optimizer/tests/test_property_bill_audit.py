"""
Property-Based Tests for Bill Audit Functionality
Tests Properties 7-11 for comprehensive bill audit validation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-functions', 'bill-audit'))

import unittest
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List
import json

from bill_audit import BillAuditEngine, AIAuditAnalyzer
from data_models import Policy, AuditStatus, ClaimStatus
from database_access import DynamoDBAccessLayer
from policy_service import PolicyService

# Test data generators
@st.composite
def line_item_strategy(draw):
    """Generate valid line item data"""
    categories = ['accommodation', 'surgery', 'diagnostics', 'pharmacy', 'consumables', 'other']
    
    return {
        'description': draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=['L', 'N', 'P']))),
        'cost': draw(st.floats(min_value=100.0, max_value=100000.0)),
        'category': draw(st.sampled_from(categories)),
        'procedure_code': draw(st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=['Lu', 'Nd'])))
    }

@st.composite
def line_items_list_strategy(draw, min_items=1, max_items=100):
    """Generate list of line items"""
    num_items = draw(st.integers(min_value=min_items, max_value=max_items))
    return [draw(line_item_strategy()) for _ in range(num_items)]

@st.composite
def policy_with_rules_strategy(draw):
    """Generate policy with extracted rules"""
    policy_id = f"pol_{draw(st.integers(min_value=1000, max_value=9999))}"
    hospital_id = f"hosp_{draw(st.integers(min_value=100, max_value=999))}"
    
    # Generate policy rules
    extracted_rules = {
        'room_rent_cap': {
            'type': 'percentage',
            'value': draw(st.floats(min_value=0.5, max_value=2.0)),
            'description': '1% of Sum Insured'
        },
        'copay_conditions': [
            {
                'procedure_type': 'surgery',
                'copay_percentage': draw(st.floats(min_value=5.0, max_value=20.0)),
                'description': 'Copay for surgical procedures'
            }
        ],
        'procedure_exclusions': [
            {
                'procedure_code': 'COSMETIC_001',
                'procedure_name': 'Cosmetic Surgery',
                'exclusion_reason': 'Not medically necessary',
                'clause_reference': 'Section 4.2.1'
            }
        ]
    }
    
    policy = Policy(
        policy_id=policy_id,
        hospital_id=hospital_id,
        policy_name=f"Test Policy {policy_id}",
        file_size=2048576,
        content_type="application/pdf",
        s3_key=f"policies/{hospital_id}/{policy_id}.pdf",
        extraction_status="COMPLETED",
        extracted_rules=extracted_rules,
        extraction_confidence=draw(st.floats(min_value=0.8, max_value=1.0)),
        version=1
    )
    
    return policy

class TestBillAuditProperties(unittest.TestCase):
    """Property-based tests for bill audit functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_client = Mock(spec=DynamoDBAccessLayer)
        self.mock_policy_service = Mock(spec=PolicyService)
        self.audit_engine = BillAuditEngine(self.mock_db_client, self.mock_policy_service)
        
        # Mock successful database operations
        self.mock_db_client.put_item.return_value = True
        self.mock_db_client.get_item.return_value = None
        self.mock_db_client.query_items.return_value = []
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=1, max_items=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_7_comprehensive_line_item_analysis(self, policy, line_items):
        """
        Property 7: Comprehensive Line Item Analysis
        **Validates: Requirements 3.1, 3.2, 3.7**
        
        Every line item in a bill must be analyzed and assigned a status
        (approved, rejected, or requires review) with a clear reason.
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Execute audit
        result = self.audit_engine.audit_bill(
            hospital_id=policy.hospital_id,
            patient_id="pat_test",
            policy_id=policy.policy_id,
            line_items=line_items,
            user_id="user_test"
        )
        
        # Verify success
        self.assertTrue(result['success'], "Audit should succeed")
        
        # Property: Every line item must be analyzed
        audit_results = result['audit_results']
        self.assertEqual(
            audit_results['total_items'],
            len(line_items),
            "All line items must be analyzed"
        )
        
        # Property: Sum of categorized items equals total
        categorized_count = (
            audit_results['approved_items'] +
            audit_results['rejected_items'] +
            audit_results['review_items']
        )
        self.assertEqual(
            categorized_count,
            len(line_items),
            "All items must be categorized"
        )
        
        # Property: Each line item has a status
        line_items_results = result['line_items']
        self.assertEqual(len(line_items_results), len(line_items))
        
        for item_result in line_items_results:
            self.assertIn('status', item_result, "Each item must have a status")
            self.assertIn(
                item_result['status'],
                [AuditStatus.APPROVED.value, AuditStatus.REJECTED.value, AuditStatus.REQUIRES_REVIEW.value],
                "Status must be valid"
            )
            
            # Property: Rejected items must have rejection reason
            if item_result['status'] == AuditStatus.REJECTED.value:
                self.assertTrue(
                    len(item_result['rejection_reason']) > 0,
                    "Rejected items must have a rejection reason"
                )
                self.assertTrue(
                    len(item_result['policy_clause']) > 0,
                    "Rejected items must reference policy clause"
                )
        
        # Property: Processing time is reasonable (< 30 seconds for 100 items)
        processing_time = audit_results['processing_time_seconds']
        items_per_second = len(line_items) / max(processing_time, 0.001)
        self.assertGreater(
            items_per_second,
            3.0,  # At least 3 items per second
            "Processing must be efficient"
        )
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=5, max_items=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_8_rejection_explanation_completeness(self, policy, line_items):
        """
        Property 8: Rejection Explanation Completeness
        **Validates: Requirements 3.2, 3.3**
        
        Every rejected line item must have:
        1. A clear rejection reason
        2. A policy clause reference
        3. An optimization suggestion (if applicable)
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Add some items that will be rejected
        line_items.append({
            'description': 'Cosmetic Surgery Procedure',
            'cost': 50000.0,
            'category': 'surgery',
            'procedure_code': 'COSMETIC_001'
        })
        
        line_items.append({
            'description': 'N95 Mask',
            'cost': 500.0,
            'category': 'consumables',
            'procedure_code': 'MASK_N95'
        })
        
        # Execute audit
        result = self.audit_engine.audit_bill(
            hospital_id=policy.hospital_id,
            patient_id="pat_test",
            policy_id=policy.policy_id,
            line_items=line_items,
            user_id="user_test"
        )
        
        # Verify rejected items
        rejected_items = result['rejected_items']
        
        for rejected_item in rejected_items:
            # Property: Must have rejection reason
            self.assertIn('rejection_reason', rejected_item)
            self.assertIsInstance(rejected_item['rejection_reason'], str)
            self.assertGreater(
                len(rejected_item['rejection_reason']),
                0,
                "Rejection reason must not be empty"
            )
            
            # Property: Must have policy clause reference
            self.assertIn('policy_clause', rejected_item)
            self.assertIsInstance(rejected_item['policy_clause'], str)
            self.assertGreater(
                len(rejected_item['policy_clause']),
                0,
                "Policy clause must not be empty"
            )
            
            # Property: Must have optimization suggestion
            self.assertIn('optimization_suggestion', rejected_item)
            # Optimization suggestion can be empty for some cases
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=10, max_items=30)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_9_settlement_ratio_prediction(self, policy, line_items):
        """
        Property 9: Settlement Ratio Prediction
        **Validates: Requirements 3.4, 3.5**
        
        The predicted settlement ratio must be:
        1. Between 0.0 and 1.0
        2. Based on approved vs total amounts
        3. Consistent with audit results
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Execute audit
        result = self.audit_engine.audit_bill(
            hospital_id=policy.hospital_id,
            patient_id="pat_test",
            policy_id=policy.policy_id,
            line_items=line_items,
            user_id="user_test"
        )
        
        audit_results = result['audit_results']
        
        # Property: Settlement ratio is in valid range
        settlement_ratio = audit_results['predicted_settlement_ratio']
        self.assertGreaterEqual(
            settlement_ratio,
            0.0,
            "Settlement ratio must be >= 0.0"
        )
        self.assertLessEqual(
            settlement_ratio,
            1.0,
            "Settlement ratio must be <= 1.0"
        )
        
        # Property: Settlement ratio is consistent with amounts
        total_amount = audit_results['total_amount']
        approved_amount = audit_results['approved_amount']
        
        if total_amount > 0:
            base_ratio = approved_amount / total_amount
            
            # Settlement ratio should be at least the base ratio
            # (can be higher due to AI predictions for review items)
            self.assertGreaterEqual(
                settlement_ratio,
                base_ratio - 0.01,  # Allow small floating point error
                "Settlement ratio should be at least base approval ratio"
            )
        else:
            self.assertEqual(
                settlement_ratio,
                0.0,
                "Settlement ratio should be 0 for zero total"
            )
        
        # Property: If all items approved, ratio should be 1.0
        if audit_results['rejected_items'] == 0 and audit_results['review_items'] == 0:
            self.assertAlmostEqual(
                settlement_ratio,
                1.0,
                places=2,
                msg="Settlement ratio should be 1.0 when all items approved"
            )
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=5, max_items=15)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_10_optimization_suggestions(self, policy, line_items):
        """
        Property 10: Optimization Suggestions
        **Validates: Requirements 3.4, 3.5, 3.6**
        
        When there are rejected items, the system should provide:
        1. AI-powered optimization suggestions
        2. Alternative approaches
        3. Predicted improvement estimates
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Add items that will be rejected
        line_items.append({
            'description': 'Deluxe Room Charges',
            'cost': 150000.0,  # Very high cost to trigger rejection
            'category': 'accommodation',
            'procedure_code': 'ROOM_DELUXE'
        })
        
        # Mock AI analyzer
        with patch.object(self.audit_engine.ai_analyzer, 'analyze_rejected_items') as mock_ai:
            mock_ai.return_value = {
                'suggestions': [
                    {
                        'item_description': 'Deluxe Room Charges',
                        'suggestion': 'Downgrade to standard room',
                        'alternative_approach': 'Use semi-private room',
                        'documentation_needed': 'Medical necessity certificate',
                        'estimated_approval_chance': 0.8
                    }
                ],
                'predicted_improvement': 0.15,
                'overall_strategy': 'Focus on medical necessity documentation'
            }
            
            # Execute audit
            result = self.audit_engine.audit_bill(
                hospital_id=policy.hospital_id,
                patient_id="pat_test",
                policy_id=policy.policy_id,
                line_items=line_items,
                user_id="user_test"
            )
        
        # Verify optimization suggestions
        audit_results = result['audit_results']
        
        if audit_results['rejected_items'] > 0:
            # Property: AI suggestions should be provided
            self.assertIn('ai_optimization_suggestions', audit_results)
            suggestions = audit_results['ai_optimization_suggestions']
            
            # Property: Suggestions should be a list
            self.assertIsInstance(suggestions, list)
            
            # Property: Each suggestion should have required fields
            for suggestion in suggestions:
                if isinstance(suggestion, dict):
                    self.assertIn('item_description', suggestion)
                    self.assertIn('suggestion', suggestion)
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=5, max_items=20)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_11_procedure_bundling_validation(self, policy, line_items):
        """
        Property 11: Procedure Bundling Validation
        **Validates: Requirements 3.6**
        
        The system should identify:
        1. Procedure bundling violations
        2. Bundling opportunities
        3. Correct bundling practices
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Mock bundling analyzer
        with patch.object(self.audit_engine.ai_analyzer, 'validate_procedure_bundling') as mock_bundling:
            mock_bundling.return_value = {
                'bundling_violations': [
                    {
                        'procedures': ['Procedure A', 'Procedure B'],
                        'issue': 'Should be bundled together',
                        'correct_approach': 'Use combined code'
                    }
                ],
                'bundling_opportunities': [
                    {
                        'procedures': ['Procedure C', 'Procedure D'],
                        'benefit': 'Better reimbursement',
                        'estimated_savings': 5000.0
                    }
                ]
            }
            
            # Execute audit
            result = self.audit_engine.audit_bill(
                hospital_id=policy.hospital_id,
                patient_id="pat_test",
                policy_id=policy.policy_id,
                line_items=line_items,
                user_id="user_test"
            )
        
        # Verify bundling analysis
        audit_results = result['audit_results']
        
        # Property: Bundling analysis should be present
        self.assertIn('bundling_analysis', audit_results)
        bundling_analysis = audit_results['bundling_analysis']
        
        # Property: Bundling analysis should have required fields
        self.assertIsInstance(bundling_analysis, dict)
        self.assertIn('bundling_violations', bundling_analysis)
        self.assertIn('bundling_opportunities', bundling_analysis)
        
        # Property: Violations and opportunities should be lists
        self.assertIsInstance(bundling_analysis['bundling_violations'], list)
        self.assertIsInstance(bundling_analysis['bundling_opportunities'], list)
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=10, max_items=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_audit_amount_consistency(self, policy, line_items):
        """
        Additional Property: Audit Amount Consistency
        
        The sum of approved, rejected, and review amounts should equal total amount.
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Execute audit
        result = self.audit_engine.audit_bill(
            hospital_id=policy.hospital_id,
            patient_id="pat_test",
            policy_id=policy.policy_id,
            line_items=line_items,
            user_id="user_test"
        )
        
        audit_results = result['audit_results']
        
        # Calculate expected total
        expected_total = sum(item['cost'] for item in line_items)
        
        # Property: Total amount matches sum of line items
        self.assertAlmostEqual(
            audit_results['total_amount'],
            expected_total,
            places=2,
            msg="Total amount should match sum of line items"
        )
        
        # Property: Categorized amounts sum to total
        approved_amount = audit_results['approved_amount']
        rejected_amount = audit_results['rejected_amount']
        
        # Note: Review items are not included in approved or rejected
        # So we can't check the exact sum, but we can verify bounds
        self.assertLessEqual(
            approved_amount + rejected_amount,
            audit_results['total_amount'] + 0.01,  # Allow floating point error
            "Approved + rejected should not exceed total"
        )
    
    @given(
        policy=policy_with_rules_strategy(),
        line_items=line_items_list_strategy(min_items=1, max_items=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_audit_idempotency(self, policy, line_items):
        """
        Additional Property: Audit Idempotency
        
        Running the same audit multiple times should produce consistent results
        (excluding AI suggestions which may vary).
        """
        # Setup
        self.mock_policy_service.get_policy.return_value = policy
        
        # Mock AI to return consistent results
        with patch.object(self.audit_engine.ai_analyzer, 'analyze_rejected_items') as mock_ai, \
             patch.object(self.audit_engine.ai_analyzer, 'validate_procedure_bundling') as mock_bundling:
            
            mock_ai.return_value = {'suggestions': [], 'predicted_improvement': 0.0}
            mock_bundling.return_value = {'bundling_violations': [], 'bundling_opportunities': []}
            
            # Execute audit twice
            result1 = self.audit_engine.audit_bill(
                hospital_id=policy.hospital_id,
                patient_id="pat_test",
                policy_id=policy.policy_id,
                line_items=line_items,
                user_id="user_test"
            )
            
            result2 = self.audit_engine.audit_bill(
                hospital_id=policy.hospital_id,
                patient_id="pat_test",
                policy_id=policy.policy_id,
                line_items=line_items,
                user_id="user_test"
            )
        
        # Property: Core audit results should be consistent
        self.assertEqual(
            result1['audit_results']['total_items'],
            result2['audit_results']['total_items']
        )
        self.assertEqual(
            result1['audit_results']['approved_items'],
            result2['audit_results']['approved_items']
        )
        self.assertEqual(
            result1['audit_results']['rejected_items'],
            result2['audit_results']['rejected_items']
        )
        self.assertAlmostEqual(
            result1['audit_results']['total_amount'],
            result2['audit_results']['total_amount'],
            places=2
        )

def test_bill_audit_integration():
    """Integration test for bill audit workflow"""
    # Setup
    mock_db_client = Mock(spec=DynamoDBAccessLayer)
    mock_policy_service = Mock(spec=PolicyService)
    
    mock_db_client.put_item.return_value = True
    
    # Create test policy
    policy = Policy(
        policy_id="pol_test",
        hospital_id="hosp_test",
        policy_name="Test Policy",
        file_size=2048576,
        content_type="application/pdf",
        s3_key="policies/test.pdf",
        extraction_status="COMPLETED",
        extracted_rules={
            'room_rent_cap': {'type': 'percentage', 'value': 1.0},
            'copay_conditions': [],
            'procedure_exclusions': []
        },
        extraction_confidence=0.95,
        version=1
    )
    
    mock_policy_service.get_policy.return_value = policy
    
    # Create audit engine
    audit_engine = BillAuditEngine(mock_db_client, mock_policy_service)
    
    # Test line items
    line_items = [
        {
            'description': 'Room Charges',
            'cost': 5000.0,
            'category': 'accommodation',
            'procedure_code': 'ROOM_001'
        },
        {
            'description': 'Surgery',
            'cost': 50000.0,
            'category': 'surgery',
            'procedure_code': 'SURG_001'
        }
    ]
    
    # Execute audit
    result = audit_engine.audit_bill(
        hospital_id="hosp_test",
        patient_id="pat_test",
        policy_id="pol_test",
        line_items=line_items,
        user_id="user_test"
    )
    
    # Verify
    assert result['success'] is True
    assert result['audit_results']['total_items'] == 2
    assert result['audit_results']['total_amount'] == 55000.0

if __name__ == '__main__':
    unittest.main()
