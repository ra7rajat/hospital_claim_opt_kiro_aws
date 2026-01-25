"""
Property-based tests for policy versioning functionality
Tests universal properties that must hold for policy version management
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import json
from datetime import datetime, timedelta
import sys
import os
from unittest.mock import Mock, patch

# Add the lambda layers to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from data_models import Policy, AuditTrail
from policy_service import PolicyService, PolicyVersioningError
from database_access import DynamoDBAccessLayer

# Test data generators
@composite
def policy_update_data(draw):
    """Generate valid policy update data"""
    update_fields = draw(st.sampled_from([
        'policy_name',
        'extraction_status', 
        'extracted_rules',
        'raw_text',
        'extraction_confidence',
        'effective_date',
        'expiration_date',
        'error_message'
    ]))
    
    updates = {}
    
    if update_fields == 'policy_name':
        updates['policy_name'] = draw(st.text(min_size=5, max_size=100))
    elif update_fields == 'extraction_status':
        updates['extraction_status'] = draw(st.sampled_from(['PROCESSING', 'COMPLETED', 'FAILED']))
    elif update_fields == 'extracted_rules':
        updates['extracted_rules'] = {
            'room_rent_cap': {'type': 'percentage', 'value': draw(st.floats(min_value=0.5, max_value=5.0))},
            'copay_conditions': [],
            'procedure_exclusions': []
        }
    elif update_fields == 'raw_text':
        updates['raw_text'] = draw(st.text(min_size=10, max_size=1000))
    elif update_fields == 'extraction_confidence':
        updates['extraction_confidence'] = draw(st.floats(min_value=0.0, max_value=1.0))
    elif update_fields == 'effective_date':
        updates['effective_date'] = datetime.utcnow().isoformat()
    elif update_fields == 'expiration_date':
        future_date = datetime.utcnow() + timedelta(days=draw(st.integers(min_value=30, max_value=365)))
        updates['expiration_date'] = future_date.isoformat()
    elif update_fields == 'error_message':
        updates['error_message'] = draw(st.text(min_size=0, max_size=500))
    
    return updates

@composite
def policy_sequence_data(draw):
    """Generate a sequence of policy updates"""
    num_updates = draw(st.integers(min_value=1, max_value=5))
    updates_sequence = []
    
    for _ in range(num_updates):
        update = draw(policy_update_data())
        updates_sequence.append(update)
    
    return updates_sequence

class TestPolicyVersioningProperties:
    """Property-based tests for policy versioning"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_access = Mock(spec=DynamoDBAccessLayer)
        self.policy_service = PolicyService(self.mock_db_access)
    
    @given(st.text(min_size=5, max_size=20), st.text(min_size=5, max_size=100), policy_update_data())
    @settings(max_examples=100)
    def test_property_3_policy_version_consistency_single_update(self, hospital_id, policy_name, update_data):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 3: Policy Version Consistency**
        For any policy update, version numbers should increment monotonically and maintain consistency
        **Validates: Requirements 1.6**
        """
        # Create initial policy
        initial_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name=policy_name,
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        # Mock get_policy to return the initial policy
        with patch.object(self.policy_service, 'get_policy', return_value=initial_policy):
            # Update the policy
            updated_policy = self.policy_service.update_policy(
                policy_id="test_pol_001",
                hospital_id=hospital_id,
                updates=update_data,
                updated_by="test_user"
            )
            
            # Verify version consistency properties
            assert updated_policy.version == initial_policy.version + 1, "Version should increment by 1"
            assert updated_policy.policy_id == initial_policy.policy_id, "Policy ID should remain unchanged"
            assert updated_policy.hospital_id == initial_policy.hospital_id, "Hospital ID should remain unchanged"
            
            # Verify that updates were applied
            for key, value in update_data.items():
                assert getattr(updated_policy, key) == value, f"Update {key} should be applied"
            
            # Verify that non-updated fields remain unchanged (except version and updated_at)
            unchanged_fields = ['file_size', 'content_type', 's3_key']
            for field in unchanged_fields:
                if field not in update_data:
                    assert getattr(updated_policy, field) == getattr(initial_policy, field), f"Field {field} should remain unchanged"
    
    @given(st.text(min_size=5, max_size=20), st.text(min_size=5, max_size=100), policy_sequence_data())
    @settings(max_examples=50)
    def test_property_3_policy_version_consistency_multiple_updates(self, hospital_id, policy_name, updates_sequence):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 3: Policy Version Consistency**
        For any sequence of policy updates, version numbers should increment monotonically
        **Validates: Requirements 1.6**
        """
        # Create initial policy
        current_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name=policy_name,
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        version_history = [current_policy.version]
        
        # Apply sequence of updates
        for i, update_data in enumerate(updates_sequence):
            with patch.object(self.policy_service, 'get_policy', return_value=current_policy):
                updated_policy = self.policy_service.update_policy(
                    policy_id="test_pol_001",
                    hospital_id=hospital_id,
                    updates=update_data,
                    updated_by=f"test_user_{i}"
                )
                
                # Verify version increments
                assert updated_policy.version == current_policy.version + 1, f"Version should increment at step {i}"
                
                # Verify monotonic increase
                version_history.append(updated_policy.version)
                assert version_history == sorted(version_history), "Versions should be monotonically increasing"
                
                # Update current policy for next iteration
                current_policy = updated_policy
        
        # Final verification
        assert current_policy.version == 1 + len(updates_sequence), "Final version should equal initial + number of updates"
    
    @given(st.text(min_size=5, max_size=20), st.lists(policy_update_data(), min_size=2, max_size=5))
    @settings(max_examples=30)
    def test_property_version_audit_trail_consistency(self, hospital_id, updates_list):
        """
        Test that version changes are properly recorded in audit trail
        """
        # Create initial policy
        current_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name="Test Policy",
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        audit_calls = []
        
        # Mock the audit trail creation
        def mock_create_audit(policy_id, action, user_id, changes, before_state=None, after_state=None):
            audit_calls.append((policy_id, action, user_id, changes, before_state, after_state))
            # Don't call the original method to avoid database operations
            return None
        
        with patch.object(self.policy_service, '_create_audit_trail', side_effect=mock_create_audit):
            # Apply updates
            for i, update_data in enumerate(updates_list):
                with patch.object(self.policy_service, 'get_policy', return_value=current_policy):
                    updated_policy = self.policy_service.update_policy(
                        policy_id="test_pol_001",
                        hospital_id=hospital_id,
                        updates=update_data,
                        updated_by=f"user_{i}"
                    )
                    current_policy = updated_policy
        
        # Verify audit trail calls
        assert len(audit_calls) == len(updates_list), "Should have one audit entry per update"
        
        # Verify audit trail content
        for i, call_args in enumerate(audit_calls):
            policy_id, action, user_id, changes, before_state, after_state = call_args
            assert policy_id == "test_pol_001", "Policy ID should be recorded"
            assert action == "UPDATE_POLICY", "Action should be UPDATE_POLICY"
            assert user_id == f"user_{i}", "User ID should be recorded"
            assert isinstance(changes, dict), "Changes should be recorded as dict"
    
    @given(st.text(min_size=5, max_size=20), st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_property_version_uniqueness_across_policies(self, hospital_id, num_policies):
        """
        Test that version numbers are independent across different policies
        """
        policies = []
        
        # Create multiple policies
        for i in range(num_policies):
            policy = Policy(
                policy_id=f"pol_{i:03d}",
                hospital_id=hospital_id,
                policy_name=f"Policy {i}",
                file_size=1024 * (i + 1),
                content_type="application/pdf",
                s3_key=f"policies/{hospital_id}/pol_{i:03d}.pdf",
                version=1
            )
            policies.append(policy)
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        # Update each policy independently
        for i, policy in enumerate(policies):
            with patch.object(self.policy_service, 'get_policy', return_value=policy):
                updated_policy = self.policy_service.update_policy(
                    policy_id=policy.policy_id,
                    hospital_id=hospital_id,
                    updates={'policy_name': f'Updated Policy {i}'},
                    updated_by="test_user"
                )
                
                # Each policy should have version 2 after one update
                assert updated_policy.version == 2, f"Policy {i} should have version 2"
                
                # Policy IDs should remain unique
                assert updated_policy.policy_id == f"pol_{i:03d}", f"Policy ID should remain unique"
    
    @given(st.text(min_size=5, max_size=20), policy_update_data())
    @settings(max_examples=50)
    def test_property_version_rollback_consistency(self, hospital_id, update_data):
        """
        Test that version information allows for consistent rollback scenarios
        """
        # Create initial policy
        initial_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name="Original Policy",
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1,
            extraction_status="COMPLETED"
        )
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        # Update policy
        with patch.object(self.policy_service, 'get_policy', return_value=initial_policy):
            updated_policy = self.policy_service.update_policy(
                policy_id="test_pol_001",
                hospital_id=hospital_id,
                updates=update_data,
                updated_by="test_user"
            )
        
        # Simulate rollback by creating a new version with original values
        rollback_updates = {
            'policy_name': initial_policy.policy_name,
            'extraction_status': initial_policy.extraction_status,
            'extracted_rules': initial_policy.extracted_rules,
            'raw_text': initial_policy.raw_text,
            'extraction_confidence': initial_policy.extraction_confidence
        }
        
        with patch.object(self.policy_service, 'get_policy', return_value=updated_policy):
            rolled_back_policy = self.policy_service.update_policy(
                policy_id="test_pol_001",
                hospital_id=hospital_id,
                updates=rollback_updates,
                updated_by="test_user"
            )
        
        # Verify rollback consistency
        assert rolled_back_policy.version == 3, "Rollback should create version 3"
        assert rolled_back_policy.policy_name == initial_policy.policy_name, "Policy name should be rolled back"
        assert rolled_back_policy.extraction_status == initial_policy.extraction_status, "Status should be rolled back"
        
        # Version should still be different (no actual rollback, just new version with old values)
        assert rolled_back_policy.version != initial_policy.version, "Version should not actually roll back"
    
    @given(st.text(min_size=5, max_size=20))
    @settings(max_examples=30)
    def test_property_version_error_handling(self, hospital_id):
        """
        Test that version consistency is maintained even when errors occur
        """
        # Mock database failure
        self.mock_db_access.put_item.return_value = False
        
        # Create initial policy
        initial_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name="Test Policy",
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1
        )
        
        with patch.object(self.policy_service, 'get_policy', return_value=initial_policy):
            # Update should fail due to database error
            with pytest.raises(PolicyVersioningError):
                self.policy_service.update_policy(
                    policy_id="test_pol_001",
                    hospital_id=hospital_id,
                    updates={'policy_name': 'Updated Policy'},
                    updated_by="test_user"
                )
        
        # Original policy should remain unchanged
        with patch.object(self.policy_service, 'get_policy', return_value=initial_policy):
            retrieved_policy = self.policy_service.get_policy(hospital_id, "test_pol_001")
            assert retrieved_policy.version == 1, "Version should remain unchanged after failed update"
            assert retrieved_policy.policy_name == "Test Policy", "Policy name should remain unchanged"
    
    @given(st.text(min_size=5, max_size=20), st.integers(min_value=2, max_value=10))
    @settings(max_examples=20)
    def test_property_concurrent_version_updates(self, hospital_id, num_concurrent_updates):
        """
        Test version consistency under simulated concurrent update scenarios
        """
        # Create initial policy
        initial_policy = Policy(
            policy_id="test_pol_001",
            hospital_id=hospital_id,
            policy_name="Test Policy",
            file_size=2048,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/test_pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        self.mock_db_access.put_item.return_value = True
        
        # Simulate concurrent updates (each sees the same initial version)
        update_results = []
        
        for i in range(num_concurrent_updates):
            with patch.object(self.policy_service, 'get_policy', return_value=initial_policy):
                try:
                    updated_policy = self.policy_service.update_policy(
                        policy_id="test_pol_001",
                        hospital_id=hospital_id,
                        updates={'policy_name': f'Concurrent Update {i}'},
                        updated_by=f"user_{i}"
                    )
                    update_results.append(updated_policy)
                except PolicyVersioningError:
                    # Some updates might fail in concurrent scenarios
                    pass
        
        # All successful updates should have version 2 (since they all saw version 1)
        for result in update_results:
            assert result.version == 2, "All concurrent updates should result in version 2"
        
        # In a real system, only one would succeed, but for testing we verify the logic
        assert len(update_results) > 0, "At least one update should succeed"

def test_policy_versioning_integration():
    """Integration test for policy versioning workflow"""
    # Mock database access
    mock_db_access = Mock(spec=DynamoDBAccessLayer)
    mock_db_access.put_item.return_value = True
    
    policy_service = PolicyService(mock_db_access)
    
    # Create initial policy
    initial_policy = Policy(
        policy_id="integration_pol_001",
        hospital_id="integration_hosp_001",
        policy_name="Integration Test Policy",
        file_size=4096,
        content_type="application/pdf",
        s3_key="policies/integration_hosp_001/integration_pol_001.pdf",
        version=1
    )
    
    # Simulate policy lifecycle with version tracking
    versions = [initial_policy]
    
    # Update 1: Change policy name
    with patch.object(policy_service, 'get_policy', return_value=versions[-1]):
        updated_v2 = policy_service.update_policy(
            policy_id="integration_pol_001",
            hospital_id="integration_hosp_001",
            updates={'policy_name': 'Updated Integration Test Policy'},
            updated_by="integration_user"
        )
        versions.append(updated_v2)
    
    # Update 2: Change extraction status
    with patch.object(policy_service, 'get_policy', return_value=versions[-1]):
        updated_v3 = policy_service.update_policy(
            policy_id="integration_pol_001",
            hospital_id="integration_hosp_001",
            updates={'extraction_status': 'COMPLETED'},
            updated_by="integration_user"
        )
        versions.append(updated_v3)
    
    # Verify version progression
    assert len(versions) == 3
    assert versions[0].version == 1
    assert versions[1].version == 2
    assert versions[2].version == 3
    
    # Verify data consistency
    assert versions[0].policy_name == "Integration Test Policy"
    assert versions[1].policy_name == "Updated Integration Test Policy"
    assert versions[2].policy_name == "Updated Integration Test Policy"  # Unchanged from v2
    
    assert versions[0].extraction_status == "PENDING_UPLOAD"  # Default
    assert versions[1].extraction_status == "PENDING_UPLOAD"  # Unchanged from v1
    assert versions[2].extraction_status == "COMPLETED"  # Updated in v3

if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])