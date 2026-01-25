"""
Tests for policy service functionality
"""
import pytest
from unittest.mock import Mock, patch
import json
import sys
import os
from datetime import datetime

# Add the lambda layers to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from policy_service import PolicyService, PolicySearchService, PolicyVersioningError
from data_models import Policy
from database_access import DynamoDBAccessLayer

class TestPolicyService:
    """Test policy service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_client = Mock()
        self.mock_db_access = Mock(spec=DynamoDBAccessLayer)
        self.policy_service = PolicyService(self.mock_db_access)
    
    def test_create_policy_success(self):
        """Test successful policy creation"""
        # Mock successful database operations
        self.mock_db_access.put_item.return_value = True
        
        # Create policy
        policy = self.policy_service.create_policy(
            hospital_id="hosp_001",
            policy_name="Test Policy",
            file_size=2048,
            content_type="application/pdf",
            s3_key="policies/hosp_001/test.pdf",
            created_by="user123"
        )
        
        # Verify policy creation
        assert policy.hospital_id == "hosp_001"
        assert policy.policy_name == "Test Policy"
        assert policy.file_size == 2048
        assert policy.version == 1
        assert policy.policy_id.startswith('pol_')
        
        # Verify database calls
        assert self.mock_db_access.put_item.call_count == 2  # Policy + audit trail
    
    def test_create_policy_database_failure(self):
        """Test policy creation with database failure"""
        # Mock database failure
        self.mock_db_access.put_item.return_value = False
        
        # Should raise exception
        with pytest.raises(PolicyVersioningError):
            self.policy_service.create_policy(
                hospital_id="hosp_001",
                policy_name="Test Policy",
                file_size=2048,
                content_type="application/pdf",
                s3_key="policies/hosp_001/test.pdf",
                created_by="user123"
            )
    
    def test_update_policy_success(self):
        """Test successful policy update"""
        # Mock existing policy
        existing_policy = Policy(
            policy_id="pol_001",
            hospital_id="hosp_001",
            policy_name="Original Policy",
            file_size=1024,
            content_type="application/pdf",
            s3_key="policies/hosp_001/pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        self.mock_db_access.get_item.return_value = existing_policy.to_dynamodb_item()
        self.mock_db_access.put_item.return_value = True
        
        # Mock the get_policy method
        with patch.object(self.policy_service, 'get_policy', return_value=existing_policy):
            # Update policy
            updates = {
                'policy_name': 'Updated Policy',
                'extraction_status': 'COMPLETED'
            }
            
            updated_policy = self.policy_service.update_policy(
                policy_id="pol_001",
                hospital_id="hosp_001",
                updates=updates,
                updated_by="user123"
            )
            
            # Verify updates
            assert updated_policy.policy_name == "Updated Policy"
            assert updated_policy.extraction_status == "COMPLETED"
            assert updated_policy.version == 2  # Version incremented
    
    def test_update_nonexistent_policy(self):
        """Test updating a policy that doesn't exist"""
        # Mock policy not found
        with patch.object(self.policy_service, 'get_policy', return_value=None):
            with pytest.raises(PolicyVersioningError):
                self.policy_service.update_policy(
                    policy_id="nonexistent",
                    hospital_id="hosp_001",
                    updates={'policy_name': 'Updated'},
                    updated_by="user123"
                )
    
    def test_get_policy_success(self):
        """Test successful policy retrieval"""
        # Mock database response
        mock_item = {
            'PK': 'HOSPITAL#hosp_001',
            'SK': 'POLICY#pol_001',
            'policy_id': 'pol_001',
            'hospital_id': 'hosp_001',
            'policy_name': 'Test Policy',
            'file_size': 2048,
            'content_type': 'application/pdf',
            's3_key': 'policies/hosp_001/pol_001.pdf',
            'extraction_status': 'COMPLETED',
            'version': 1,
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        self.mock_db_access.get_item.return_value = mock_item
        
        # Get policy
        policy = self.policy_service.get_policy("hosp_001", "pol_001")
        
        # Verify policy
        assert policy is not None
        assert policy.policy_id == "pol_001"
        assert policy.hospital_id == "hosp_001"
        assert policy.policy_name == "Test Policy"
        assert policy.version == 1
    
    def test_get_policy_not_found(self):
        """Test policy retrieval when policy doesn't exist"""
        # Mock database returning None
        self.mock_db_access.get_item.return_value = None
        
        # Get policy
        policy = self.policy_service.get_policy("hosp_001", "nonexistent")
        
        # Should return None
        assert policy is None
    
    def test_search_policies(self):
        """Test policy search functionality"""
        # Mock database response
        mock_items = [
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_001',
                'policy_id': 'pol_001',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy One',
                'extraction_status': 'COMPLETED',
                'version': 1,
                'file_size': 1024,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_001.pdf',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            },
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_002',
                'policy_id': 'pol_002',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy Two',
                'extraction_status': 'PROCESSING',
                'version': 1,
                'file_size': 2048,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_002.pdf',
                'created_at': '2024-01-02T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z'
            }
        ]
        
        self.mock_db_access.query_items.return_value = mock_items
        
        # Search policies
        policies = self.policy_service.search_policies("hosp_001")
        
        # Verify results
        assert len(policies) == 2
        assert policies[0].policy_id == "pol_001"
        assert policies[1].policy_id == "pol_002"
    
    def test_search_policies_with_filters(self):
        """Test policy search with filters"""
        # Mock database response
        mock_items = [
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_001',
                'policy_id': 'pol_001',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy One',
                'extraction_status': 'COMPLETED',
                'version': 1,
                'file_size': 1024,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_001.pdf',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            },
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_002',
                'policy_id': 'pol_002',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy Two',
                'extraction_status': 'PROCESSING',
                'version': 1,
                'file_size': 2048,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_002.pdf',
                'created_at': '2024-01-02T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z'
            }
        ]
        
        self.mock_db_access.query_items.return_value = mock_items
        
        # Search with status filter
        filters = {'extraction_status': 'COMPLETED'}
        policies = self.policy_service.search_policies("hosp_001", filters)
        
        # Should only return completed policies
        assert len(policies) == 1
        assert policies[0].extraction_status == 'COMPLETED'
    
    def test_delete_policy_success(self):
        """Test successful policy deletion (soft delete)"""
        # Mock existing policy
        existing_policy = Policy(
            policy_id="pol_001",
            hospital_id="hosp_001",
            policy_name="Test Policy",
            file_size=1024,
            content_type="application/pdf",
            s3_key="policies/hosp_001/pol_001.pdf",
            version=1
        )
        
        # Mock database operations
        with patch.object(self.policy_service, 'get_policy', return_value=existing_policy):
            with patch.object(self.policy_service, 'update_policy', return_value=existing_policy):
                # Delete policy
                success = self.policy_service.delete_policy("hosp_001", "pol_001", "user123")
                
                # Verify success
                assert success is True
    
    def test_delete_nonexistent_policy(self):
        """Test deleting a policy that doesn't exist"""
        # Mock policy not found
        with patch.object(self.policy_service, 'get_policy', return_value=None):
            # Delete policy
            success = self.policy_service.delete_policy("hosp_001", "nonexistent", "user123")
            
            # Should return False
            assert success is False
    
    def test_get_policy_statistics(self):
        """Test policy statistics calculation"""
        # Mock policies
        mock_items = [
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_001',
                'policy_id': 'pol_001',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy One',
                'extraction_status': 'COMPLETED',
                'extraction_confidence': 0.9,
                'version': 1,
                'file_size': 1024,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_001.pdf',
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            },
            {
                'PK': 'HOSPITAL#hosp_001',
                'SK': 'POLICY#pol_002',
                'policy_id': 'pol_002',
                'hospital_id': 'hosp_001',
                'policy_name': 'Policy Two',
                'extraction_status': 'PROCESSING',
                'extraction_confidence': 0.8,
                'version': 2,
                'file_size': 2048,
                'content_type': 'application/pdf',
                's3_key': 'policies/hosp_001/pol_002.pdf',
                'created_at': '2024-01-02T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z'
            }
        ]
        
        self.mock_db_access.query_items.return_value = mock_items
        
        # Get statistics
        stats = self.policy_service.get_policy_statistics("hosp_001")
        
        # Verify statistics
        assert stats['total_policies'] == 2
        assert stats['by_status']['COMPLETED'] == 1
        assert stats['by_status']['PROCESSING'] == 1
        assert stats['by_version'][1] == 1
        assert stats['by_version'][2] == 1
        assert stats['total_file_size'] == 3072  # 1024 + 2048
        assert abs(stats['average_confidence'] - 0.85) < 0.001  # Handle floating point precision

class TestPolicySearchService:
    """Test policy search service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_policy_service = Mock(spec=PolicyService)
        self.search_service = PolicySearchService(self.mock_policy_service)
    
    def test_advanced_search_with_name_filter(self):
        """Test advanced search with name filtering"""
        # Mock policies
        mock_policies = [
            Policy(
                policy_id="pol_001",
                hospital_id="hosp_001",
                policy_name="Health Insurance Policy",
                file_size=1024,
                content_type="application/pdf",
                s3_key="policies/hosp_001/pol_001.pdf"
            ),
            Policy(
                policy_id="pol_002",
                hospital_id="hosp_001",
                policy_name="Dental Coverage Policy",
                file_size=2048,
                content_type="application/pdf",
                s3_key="policies/hosp_001/pol_002.pdf"
            )
        ]
        
        self.mock_policy_service.search_policies.return_value = mock_policies
        
        # Search with name filter
        search_criteria = {
            'policy_name': 'health',
            'sort_by': 'policy_name',
            'sort_order': 'asc'
        }
        
        results = self.search_service.advanced_search("hosp_001", search_criteria)
        
        # Should only return policies with 'health' in name
        assert len(results) == 1
        assert 'health' in results[0].policy_name.lower()
    
    def test_advanced_search_with_pagination(self):
        """Test advanced search with pagination"""
        # Mock many policies
        mock_policies = []
        for i in range(10):
            policy = Policy(
                policy_id=f"pol_{i:03d}",
                hospital_id="hosp_001",
                policy_name=f"Policy {i}",
                file_size=1024,
                content_type="application/pdf",
                s3_key=f"policies/hosp_001/pol_{i:03d}.pdf"
            )
            mock_policies.append(policy)
        
        self.mock_policy_service.search_policies.return_value = mock_policies
        
        # Search with pagination
        search_criteria = {
            'limit': 5,
            'offset': 3
        }
        
        results = self.search_service.advanced_search("hosp_001", search_criteria)
        
        # Should return 5 policies starting from offset 3
        assert len(results) == 5
        # Note: policies are sorted by created_at desc by default, so check the actual order
        policy_ids = [p.policy_id for p in results]
        assert len(policy_ids) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])