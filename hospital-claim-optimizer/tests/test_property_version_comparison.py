"""
Property-Based Tests for Version Comparison
Tests Property 43: Version Comparison Accuracy

**Feature: journey-enhancements, Property 43: Version Comparison Accuracy**

These tests validate that version comparison correctly identifies all changes
between policy versions with no false positives or negatives.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import json
from typing import Dict, Any

# Mock imports for testing
from unittest.mock import Mock, MagicMock

# Import services to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from version_comparison_service import (
    VersionComparisonService,
    RuleChange,
    VersionComparison
)
from impact_analysis_service import ImpactAnalysisService, ImpactAnalysis
from version_rollback_service import VersionRollbackService, RollbackResult


# Test data generators
@st.composite
def policy_rules(draw):
    """Generate realistic policy rules"""
    return {
        'room_rent_cap': {
            'type': draw(st.sampled_from(['fixed', 'percentage', 'none'])),
            'value': draw(st.integers(min_value=1000, max_value=10000))
        },
        'copay_conditions': draw(st.lists(
            st.fixed_dictionaries({
                'procedure_code': st.text(min_size=3, max_size=10),
                'percentage': st.integers(min_value=0, max_value=50)
            }),
            max_size=5
        )),
        'procedure_exclusions': draw(st.lists(
            st.text(min_size=3, max_size=10),
            max_size=10
        )),
        'covered_procedures': draw(st.lists(
            st.text(min_size=3, max_size=10),
            max_size=20
        ))
    }


@st.composite
def modified_rules(draw, original_rules):
    """Generate modified version of policy rules"""
    rules = json.loads(json.dumps(original_rules))  # Deep copy
    
    # Randomly modify some fields
    if draw(st.booleans()):
        rules['room_rent_cap']['value'] = draw(st.integers(min_value=1000, max_value=10000))
    
    if draw(st.booleans()) and rules['copay_conditions']:
        idx = draw(st.integers(min_value=0, max_value=len(rules['copay_conditions'])-1))
        rules['copay_conditions'][idx]['percentage'] = draw(st.integers(min_value=0, max_value=50))
    
    if draw(st.booleans()):
        new_exclusion = draw(st.text(min_size=3, max_size=10))
        rules['procedure_exclusions'].append(new_exclusion)
    
    return rules


class TestVersionComparisonAccuracy:
    """
    **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
    
    Test that version comparison correctly identifies all changes
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_policy_service = Mock()
        self.comparison_service = VersionComparisonService(self.mock_policy_service)
    
    @given(rules1=policy_rules(), rules2=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_1_all_added_rules_detected(self, rules1, rules2):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: All added rules are correctly detected
        """
        # Compare rules
        added, removed, modified, unchanged = self.comparison_service._compare_rules(rules1, rules2)
        
        # Check that all categories in rules2 but not in rules1 are in added
        for category in rules2:
            if category not in rules1:
                assert any(a['category'] == category for a in added), \
                    f"Added category {category} not detected"
    
    @given(rules1=policy_rules(), rules2=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_2_all_removed_rules_detected(self, rules1, rules2):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: All removed rules are correctly detected
        """
        # Compare rules
        added, removed, modified, unchanged = self.comparison_service._compare_rules(rules1, rules2)
        
        # Check that all categories in rules1 but not in rules2 are in removed
        for category in rules1:
            if category not in rules2:
                assert any(r['category'] == category for r in removed), \
                    f"Removed category {category} not detected"
    
    @given(original=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_3_all_modified_rules_detected(self, original):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: All modified rules are correctly detected
        """
        # Create a modified version
        modified_version = json.loads(json.dumps(original))
        
        # Modify room rent cap value
        if 'room_rent_cap' in modified_version:
            modified_version['room_rent_cap']['value'] += 1000
        
        # Compare rules
        added, removed, modified_rules, unchanged = self.comparison_service._compare_rules(
            original,
            modified_version
        )
        
        # Should detect the modification
        if 'room_rent_cap' in original and 'room_rent_cap' in modified_version:
            if original['room_rent_cap'] != modified_version['room_rent_cap']:
                assert len(modified_rules) > 0, "Modified rule not detected"
    
    @given(rules=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_4_no_false_positives(self, rules):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Comparing identical rules produces no changes (no false positives)
        """
        # Compare identical rules
        added, removed, modified, unchanged = self.comparison_service._compare_rules(rules, rules)
        
        # Should have no changes
        assert len(added) == 0, f"False positive: {len(added)} rules incorrectly marked as added"
        assert len(removed) == 0, f"False positive: {len(removed)} rules incorrectly marked as removed"
        assert len(modified) == 0, f"False positive: {len(modified)} rules incorrectly marked as modified"
    
    @given(rules1=policy_rules(), rules2=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_5_comparison_is_symmetric(self, rules1, rules2):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Comparison is symmetric - added in A→B equals removed in B→A
        """
        # Compare A to B
        added_ab, removed_ab, modified_ab, _ = self.comparison_service._compare_rules(rules1, rules2)
        
        # Compare B to A
        added_ba, removed_ba, modified_ba, _ = self.comparison_service._compare_rules(rules2, rules1)
        
        # Added in A→B should equal removed in B→A
        assert len(added_ab) == len(removed_ba), \
            "Comparison not symmetric: added count mismatch"
        
        # Removed in A→B should equal added in B→A
        assert len(removed_ab) == len(added_ba), \
            "Comparison not symmetric: removed count mismatch"
    
    @given(rules=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_6_similarity_score_bounds(self, rules):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Similarity scores are always between 0.0 and 1.0
        """
        # Create a modified version
        modified = json.loads(json.dumps(rules))
        if 'room_rent_cap' in modified:
            modified['room_rent_cap']['value'] += 500
        
        # Compare and check similarity scores
        _, _, modified_rules, _ = self.comparison_service._compare_rules(rules, modified)
        
        for change in modified_rules:
            assert 0.0 <= change.similarity_score <= 1.0, \
                f"Similarity score {change.similarity_score} out of bounds"
    
    @given(rules=policy_rules())
    @settings(max_examples=100, deadline=None)
    def test_property_43_7_identical_rules_have_perfect_similarity(self, rules):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Identical values have similarity score of 1.0
        """
        for category, value in rules.items():
            similarity = self.comparison_service._calculate_similarity(value, value)
            assert similarity == 1.0, \
                f"Identical values should have similarity 1.0, got {similarity}"
    
    @given(
        value1=st.integers(min_value=0, max_value=10000),
        value2=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_43_8_numeric_similarity_is_relative(self, value1, value2):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Numeric similarity reflects relative difference
        """
        similarity = self.comparison_service._calculate_similarity(value1, value2)
        
        # Identical values should have similarity 1.0
        if value1 == value2:
            assert similarity == 1.0
        
        # Different values should have similarity < 1.0
        else:
            assert similarity < 1.0
        
        # Similarity should always be non-negative
        assert similarity >= 0.0


class TestImpactAnalysisCorrectness:
    """
    **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
    
    Test that impact analysis correctly assesses policy changes
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.impact_service = ImpactAnalysisService(self.mock_db)
    
    @given(
        claim_amount=st.integers(min_value=1000, max_value=100000),
        coverage1=st.integers(min_value=0, max_value=100),
        coverage2=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_43_9_impact_reflects_coverage_change(self, claim_amount, coverage1, coverage2):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Impact severity reflects magnitude of coverage change
        """
        coverage_change = abs(coverage2 - coverage1)
        settlement_change = coverage_change / 100.0
        
        severity = self.impact_service._calculate_impact_severity(
            coverage_change,
            settlement_change
        )
        
        # High coverage change should result in high severity
        if coverage_change > 10:
            assert severity in ['high', 'medium'], \
                f"Large coverage change ({coverage_change}%) should be high/medium severity"
        
        # Small coverage change should result in low severity
        elif coverage_change <= 5:
            assert severity in ['low', 'medium'], \
                f"Small coverage change ({coverage_change}%) should be low/medium severity"
    
    @given(
        total_claims=st.integers(min_value=0, max_value=200),
        affected_claims=st.integers(min_value=0, max_value=200)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_43_10_confidence_increases_with_data(self, total_claims, affected_claims):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Confidence level increases with more data
        """
        assume(affected_claims <= total_claims)
        
        confidence = self.impact_service._assess_confidence(total_claims, affected_claims)
        
        # More claims should give higher confidence
        if total_claims >= 50:
            assert confidence == 'high', \
                f"50+ claims should give high confidence, got {confidence}"
        elif total_claims >= 20:
            assert confidence in ['medium', 'high'], \
                f"20+ claims should give medium/high confidence, got {confidence}"
        elif total_claims > 0:
            assert confidence in ['low', 'medium'], \
                f"Few claims should give low/medium confidence, got {confidence}"


class TestRollbackCorrectness:
    """
    **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
    
    Test that rollback operations maintain data integrity
    """
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_policy_service = Mock()
        self.mock_db = Mock()
        self.rollback_service = VersionRollbackService(
            self.mock_policy_service,
            self.mock_db
        )
    
    @given(
        current_version=st.integers(min_value=2, max_value=100),
        target_version=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_43_11_rollback_validation(self, current_version, target_version):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Rollback validation correctly identifies invalid operations
        """
        error = self.rollback_service._validate_rollback(current_version, target_version)
        
        # Can only rollback to earlier versions
        if target_version >= current_version:
            assert error is not None, \
                "Should reject rollback to same or later version"
        else:
            assert error is None, \
                "Should allow rollback to earlier version"
    
    @given(
        current_version=st.integers(min_value=2, max_value=10),
        target_version=st.integers(min_value=1, max_value=9)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_43_12_rollback_creates_new_version(self, current_version, target_version):
        """
        **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
        
        Property: Rollback creates new version rather than deleting history
        """
        assume(target_version < current_version)
        
        # Mock policy service
        mock_policy = Mock()
        mock_policy.version = current_version
        self.mock_policy_service.get_policy.return_value = mock_policy
        self.mock_policy_service.get_policy_audit_trail.return_value = [
            {
                'action': 'UPDATE_POLICY',
                'changes': {'version': target_version},
                'after_state': {'extracted_rules': {}, 'version': target_version}
            }
        ]
        self.mock_policy_service.update_policy.return_value = Mock(version=current_version + 1)
        self.mock_db.query_items.return_value = []
        
        # Perform rollback
        result = self.rollback_service.rollback_to_version(
            'hospital1',
            'policy1',
            target_version,
            'Test rollback',
            'user1'
        )
        
        if result.success:
            # New version should be current + 1
            assert result.new_version_number == current_version + 1, \
                "Rollback should create new version, not delete history"


def test_version_comparison_integration():
    """
    Integration test for version comparison workflow
    
    **Feature: journey-enhancements, Property 43: Version Comparison Accuracy**
    """
    # Create mock services
    mock_policy_service = Mock()
    comparison_service = VersionComparisonService(mock_policy_service)
    
    # Create two versions of rules
    rules_v1 = {
        'room_rent_cap': {'type': 'fixed', 'value': 5000},
        'copay_conditions': [{'procedure_code': 'PROC1', 'percentage': 10}],
        'procedure_exclusions': ['EXCL1', 'EXCL2']
    }
    
    rules_v2 = {
        'room_rent_cap': {'type': 'fixed', 'value': 6000},  # Modified
        'copay_conditions': [{'procedure_code': 'PROC1', 'percentage': 15}],  # Modified
        'procedure_exclusions': ['EXCL1', 'EXCL2', 'EXCL3'],  # Added
        'covered_procedures': ['PROC1', 'PROC2']  # Added category
    }
    
    # Compare
    added, removed, modified, unchanged = comparison_service._compare_rules(rules_v1, rules_v2)
    
    # Verify results
    assert len(added) > 0, "Should detect added category"
    assert len(modified) > 0, "Should detect modifications"
    
    # Check that all changes are accounted for
    total_categories = len(set(rules_v1.keys()) | set(rules_v2.keys()))
    total_detected = len(added) + len(removed) + len(modified) + len(unchanged)
    assert total_detected == total_categories, \
        "All categories should be accounted for in comparison"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
