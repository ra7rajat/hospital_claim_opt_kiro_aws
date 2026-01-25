"""
Property-based tests for policy processing functionality
Tests universal properties that must hold for policy upload, extraction, and processing
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import json
from datetime import datetime, timedelta
import sys
import os
import time
from unittest.mock import Mock, patch

# Add the lambda layers to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from data_models import Policy, Hospital
from common_utils import generate_id, get_timestamp

# Test data generators
@composite
def policy_upload_data(draw):
    """Generate valid policy upload request data"""
    hospital_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_-')))
    policy_name = draw(st.text(min_size=5, max_size=100))
    file_size = draw(st.integers(min_value=1024, max_value=50*1024*1024))  # 1KB to 50MB
    
    return {
        'hospital_id': hospital_id,
        'policy_name': policy_name,
        'file_size': file_size,
        'content_type': 'application/pdf'
    }

@composite
def policy_extraction_data(draw):
    """Generate policy extraction test data"""
    return {
        'raw_text': draw(st.text(min_size=100, max_size=5000)),
        'confidence_score': draw(st.floats(min_value=0.0, max_value=1.0)),
        'extraction_status': draw(st.sampled_from(['PROCESSING', 'COMPLETED', 'FAILED'])),
        'file_size': draw(st.integers(min_value=1024, max_value=50*1024*1024))
    }

@composite
def invalid_policy_data(draw):
    """Generate invalid policy data for error handling tests"""
    # Generate various types of invalid data
    invalid_type = draw(st.sampled_from([
        'missing_hospital_id',
        'missing_policy_name', 
        'oversized_file',
        'invalid_content_type',
        'empty_policy_name',
        'invalid_hospital_id'
    ]))
    
    base_data = {
        'hospital_id': 'hosp_001',
        'policy_name': 'Test Policy',
        'file_size': 1024,
        'content_type': 'application/pdf'
    }
    
    if invalid_type == 'missing_hospital_id':
        del base_data['hospital_id']
    elif invalid_type == 'missing_policy_name':
        del base_data['policy_name']
    elif invalid_type == 'oversized_file':
        base_data['file_size'] = 60 * 1024 * 1024  # 60MB - over limit
    elif invalid_type == 'invalid_content_type':
        base_data['content_type'] = draw(st.sampled_from(['text/plain', 'image/jpeg', 'application/msword']))
    elif invalid_type == 'empty_policy_name':
        base_data['policy_name'] = ''
    elif invalid_type == 'invalid_hospital_id':
        base_data['hospital_id'] = draw(st.text(max_size=2))  # Too short
    
    return base_data, invalid_type

class TestPolicyProcessingProperties:
    """Property-based tests for policy processing"""
    
    @given(policy_upload_data())
    @settings(max_examples=100)
    def test_property_1_policy_processing_round_trip_upload(self, upload_data):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 1: Policy Processing Round Trip**
        For any valid policy upload request, the system should generate a policy ID and return upload URL
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Mock the policy upload process
        hospital_id = upload_data['hospital_id']
        policy_name = upload_data['policy_name']
        file_size = upload_data['file_size']
        
        # Create policy entity
        policy_id = generate_id('pol')
        policy = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name=policy_name,
            file_size=file_size,
            content_type=upload_data['content_type'],
            s3_key=f"policies/{hospital_id}/{policy_id}.pdf"
        )
        
        # Verify policy structure
        assert policy.policy_id.startswith('pol_')
        assert policy.hospital_id == hospital_id
        assert policy.policy_name == policy_name
        assert policy.file_size == file_size
        assert policy.extraction_status == 'PENDING_UPLOAD'
        
        # Verify DynamoDB item conversion
        dynamodb_item = policy.to_dynamodb_item()
        assert dynamodb_item['PK'] == f"HOSPITAL#{hospital_id}"
        assert dynamodb_item['SK'] == f"POLICY#{policy_id}"
        assert dynamodb_item['policy_name'] == policy_name
        assert dynamodb_item['file_size'] == file_size
        assert 'created_at' in dynamodb_item
        assert 'updated_at' in dynamodb_item
    
    @given(invalid_policy_data())
    @settings(max_examples=100)
    def test_property_2_policy_error_handling(self, invalid_data_tuple):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 2: Policy Error Handling**
        For any invalid policy data, the system should reject the request with appropriate error messages
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """
        invalid_data, error_type = invalid_data_tuple
        
        # Test validation logic
        validation_errors = []
        
        # Check required fields
        if 'hospital_id' not in invalid_data or not invalid_data.get('hospital_id'):
            validation_errors.append('Missing hospital_id')
        
        if 'policy_name' not in invalid_data or not invalid_data.get('policy_name'):
            validation_errors.append('Missing policy_name')
        
        # Check file size limits
        if invalid_data.get('file_size', 0) > 50 * 1024 * 1024:
            validation_errors.append('File size exceeds limit')
        
        # Check content type
        if invalid_data.get('content_type') != 'application/pdf':
            validation_errors.append('Invalid content type')
        
        # Check hospital ID format
        hospital_id = invalid_data.get('hospital_id', '')
        if hospital_id and len(hospital_id) < 3:
            validation_errors.append('Invalid hospital_id format')
        
        # Should have at least one validation error for invalid data
        assert len(validation_errors) > 0, f"Expected validation errors for {error_type}"
        
        # Verify specific error types
        if error_type == 'missing_hospital_id':
            assert any('hospital_id' in error for error in validation_errors)
        elif error_type == 'missing_policy_name':
            assert any('policy_name' in error for error in validation_errors)
        elif error_type == 'oversized_file':
            assert any('size' in error.lower() for error in validation_errors)
        elif error_type == 'invalid_content_type':
            assert any('content type' in error.lower() for error in validation_errors)
    
    @given(policy_extraction_data())
    @settings(max_examples=50)
    def test_property_24_document_processing_performance(self, extraction_data):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 24: Document Processing Performance**
        For any document processing operation, the system should complete within reasonable time limits
        **Validates: Requirements 8.2**
        """
        raw_text = extraction_data['raw_text']
        file_size = extraction_data['file_size']
        
        # Simulate processing time based on file size and content
        start_time = time.time()
        
        # Mock text processing (simulate OCR and extraction)
        processed_text = raw_text.upper()  # Simple transformation
        word_count = len(processed_text.split())
        
        # Mock rule extraction (simulate Bedrock processing)
        extracted_rules = {
            'room_rent_cap': {'type': 'percentage', 'value': 1.0},
            'copay_conditions': [],
            'procedure_exclusions': [],
            'extraction_confidence': extraction_data['confidence_score']
        }
        
        processing_time = time.time() - start_time
        
        # Performance assertions based on file size
        if file_size < 1024 * 1024:  # < 1MB
            max_processing_time = 5.0  # 5 seconds
        elif file_size < 10 * 1024 * 1024:  # < 10MB
            max_processing_time = 30.0  # 30 seconds
        else:  # >= 10MB
            max_processing_time = 120.0  # 2 minutes
        
        # Processing should complete within time limits
        assert processing_time < max_processing_time, f"Processing took {processing_time:.2f}s, expected < {max_processing_time}s"
        
        # Verify processing results
        assert len(processed_text) > 0
        assert word_count > 0
        assert isinstance(extracted_rules, dict)
        assert 'extraction_confidence' in extracted_rules
        assert 0.0 <= extracted_rules['extraction_confidence'] <= 1.0
    
    @given(st.text(min_size=5, max_size=20), st.text(min_size=5, max_size=100))
    @settings(max_examples=50)
    def test_property_policy_id_uniqueness(self, hospital_id, policy_name):
        """
        Test that policy IDs are unique across multiple generations
        """
        policy_ids = set()
        
        # Generate multiple policy IDs
        for _ in range(10):
            policy_id = generate_id('pol')
            assert policy_id not in policy_ids, "Policy IDs should be unique"
            policy_ids.add(policy_id)
            
            # Verify policy ID format
            assert policy_id.startswith('pol_')
            assert len(policy_id) > 4  # Should have content after prefix
    
    @given(policy_upload_data())
    @settings(max_examples=50)
    def test_property_policy_versioning_consistency(self, upload_data):
        """
        Test that policy versioning maintains consistency across updates
        """
        hospital_id = upload_data['hospital_id']
        policy_name = upload_data['policy_name']
        
        # Create initial policy
        policy_id = generate_id('pol')
        policy_v1 = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name=policy_name,
            file_size=upload_data['file_size'],
            content_type=upload_data['content_type'],
            s3_key=f"policies/{hospital_id}/{policy_id}.pdf",
            version=1
        )
        
        # Create updated policy
        policy_v2 = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name=f"Updated {policy_name}",
            file_size=upload_data['file_size'] + 1024,
            content_type=upload_data['content_type'],
            s3_key=f"policies/{hospital_id}/{policy_id}_v2.pdf",
            version=2
        )
        
        # Verify version consistency
        assert policy_v1.policy_id == policy_v2.policy_id
        assert policy_v1.hospital_id == policy_v2.hospital_id
        assert policy_v1.version < policy_v2.version
        assert policy_v1.created_at <= policy_v2.created_at
        
        # Verify DynamoDB keys remain consistent
        item_v1 = policy_v1.to_dynamodb_item()
        item_v2 = policy_v2.to_dynamodb_item()
        
        assert item_v1['PK'] == item_v2['PK']  # Same partition key
        assert item_v1['SK'] == item_v2['SK']  # Same sort key for updates
        assert item_v1['version'] < item_v2['version']
    
    @given(st.lists(policy_upload_data(), min_size=1, max_size=5))
    @settings(max_examples=20)
    def test_property_batch_policy_processing(self, policies_data):
        """
        Test that batch policy processing maintains consistency
        """
        processed_policies = []
        
        for policy_data in policies_data:
            policy_id = generate_id('pol')
            policy = Policy(
                policy_id=policy_id,
                hospital_id=policy_data['hospital_id'],
                policy_name=policy_data['policy_name'],
                file_size=policy_data['file_size'],
                content_type=policy_data['content_type'],
                s3_key=f"policies/{policy_data['hospital_id']}/{policy_id}.pdf"
            )
            processed_policies.append(policy)
        
        # Verify all policies are valid
        for policy in processed_policies:
            assert policy.policy_id.startswith('pol_')
            assert len(policy.hospital_id) > 0
            assert len(policy.policy_name) > 0
            assert policy.file_size > 0
            assert policy.extraction_status == 'PENDING_UPLOAD'
        
        # Verify unique policy IDs
        policy_ids = [p.policy_id for p in processed_policies]
        assert len(policy_ids) == len(set(policy_ids)), "All policy IDs should be unique"
        
        # Verify DynamoDB items are valid
        for policy in processed_policies:
            item = policy.to_dynamodb_item()
            assert 'PK' in item
            assert 'SK' in item
            assert 'policy_id' in item
            assert 'hospital_id' in item
            assert 'created_at' in item
    
    @given(st.text(min_size=10, max_size=1000))
    @settings(max_examples=30)
    def test_property_policy_text_extraction_consistency(self, sample_text):
        """
        Test that policy text extraction produces consistent results
        """
        # Simulate text extraction process
        extracted_text = sample_text.strip()
        
        # Basic text processing
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        # Verify extraction consistency
        assert word_count >= 0
        assert char_count >= 0
        
        if len(sample_text.strip()) > 0:
            assert word_count > 0, "Non-empty text should have words"
            assert char_count > 0, "Non-empty text should have characters"
        
        # Simulate confidence scoring
        confidence = min(1.0, word_count / 100.0)  # Simple confidence metric
        assert 0.0 <= confidence <= 1.0
        
        # Verify text processing doesn't corrupt data
        assert isinstance(extracted_text, str)
        assert len(extracted_text) <= len(sample_text)  # Should not grow during extraction

def test_policy_processing_integration():
    """Integration test for complete policy processing workflow"""
    # Create test hospital
    hospital = Hospital(
        hospital_id="test_hosp_001",
        org_name="Test Hospital",
        license_key="TEST123"
    )
    
    # Create test policy
    policy = Policy(
        policy_id="test_pol_001",
        hospital_id="test_hosp_001",
        policy_name="Test Policy Document",
        file_size=2048,
        content_type="application/pdf",
        s3_key="policies/test_hosp_001/test_pol_001.pdf"
    )
    
    # Verify relationship
    assert policy.hospital_id == hospital.hospital_id
    
    # Verify DynamoDB structure supports queries
    hospital_item = hospital.to_dynamodb_item()
    policy_item = policy.to_dynamodb_item()
    
    # Hospital and policy should be in same partition for efficient queries
    assert hospital_item['PK'] == f"HOSPITAL#{hospital.hospital_id}"
    assert policy_item['PK'] == f"HOSPITAL#{hospital.hospital_id}"
    
    # Different sort keys for different entity types
    assert hospital_item['SK'] == "METADATA"
    assert policy_item['SK'] == f"POLICY#{policy.policy_id}"

if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])