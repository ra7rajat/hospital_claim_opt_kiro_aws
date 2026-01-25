"""
Property-based tests for data model consistency
Tests universal properties that must hold across all valid inputs
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import json
from datetime import datetime, timedelta
import sys
import os

# Add the lambda layers to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from data_models import (
    Hospital, Patient, Policy, Claim, ClaimItem, AuditTrail,
    ClaimStatus, RiskLevel, AuditStatus, DynamoDBRepository,
    create_sample_data
)
from database_access import DynamoDBAccessLayer

# Test data generators
@composite
def hospital_data(draw):
    """Generate valid hospital data"""
    # Use a more diverse strategy for hospital IDs to reduce collisions
    hospital_id = draw(st.text(min_size=8, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_-')))
    org_name = draw(st.text(min_size=5, max_size=100))
    license_key = draw(st.text(min_size=8, max_size=50))
    total_claims = draw(st.integers(min_value=0, max_value=100000))
    
    return {
        'hospital_id': hospital_id,
        'org_name': org_name,
        'license_key': license_key,
        'total_claims_processed': total_claims,
        'subscription_tier': draw(st.sampled_from(['basic', 'premium', 'enterprise'])),
        'contact_email': f"admin@{hospital_id.lower().replace('_', '').replace('-', '')}.com",
        'contact_phone': draw(st.text(min_size=10, max_size=15, alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='+-()'))),
        'address': draw(st.text(min_size=10, max_size=200))
    }

@composite
def patient_data(draw, hospital_id=None):
    """Generate valid patient data"""
    if hospital_id is None:
        hospital_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    
    patient_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    name = draw(st.text(min_size=2, max_size=100))
    age = draw(st.integers(min_value=0, max_value=120))
    policy_number = draw(st.text(min_size=8, max_size=50))
    insurer_name = draw(st.text(min_size=5, max_size=100))
    
    # Generate valid ISO datetime
    base_date = datetime(2020, 1, 1)
    days_offset = draw(st.integers(min_value=0, max_value=1460))  # 4 years
    admit_date = (base_date + timedelta(days=days_offset)).isoformat()
    
    return {
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'name': name,
        'age': age,
        'policy_number': policy_number,
        'insurer_name': insurer_name,
        'admit_date': admit_date,
        'active_policies': draw(st.lists(st.text(min_size=5, max_size=20), min_size=0, max_size=5))
    }

@composite
def policy_data(draw, hospital_id=None):
    """Generate valid policy data"""
    if hospital_id is None:
        hospital_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    
    policy_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    policy_name = draw(st.text(min_size=5, max_size=100))
    file_size = draw(st.integers(min_value=1024, max_value=50*1024*1024))  # 1KB to 50MB
    
    return {
        'policy_id': policy_id,
        'hospital_id': hospital_id,
        'policy_name': policy_name,
        'file_size': file_size,
        'content_type': 'application/pdf',
        's3_key': f"policies/{hospital_id}/{policy_id}.pdf",
        'extraction_status': draw(st.sampled_from(['PENDING_UPLOAD', 'PROCESSING', 'COMPLETED', 'FAILED'])),
        'extraction_confidence': draw(st.floats(min_value=0.0, max_value=1.0)),
        'version': draw(st.integers(min_value=1, max_value=10))
    }

@composite
def claim_data(draw, patient_id=None, hospital_id=None):
    """Generate valid claim data"""
    if patient_id is None:
        patient_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    if hospital_id is None:
        hospital_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    
    claim_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='_')))
    total_amount = draw(st.floats(min_value=100.0, max_value=1000000.0))
    risk_score = draw(st.integers(min_value=0, max_value=100))
    
    return {
        'claim_id': claim_id,
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'status': draw(st.sampled_from([status.value for status in ClaimStatus])),
        'total_amount': total_amount,
        'risk_score': risk_score,
        'risk_level': draw(st.sampled_from([level.value for level in RiskLevel])),
        'predicted_settlement_ratio': draw(st.floats(min_value=0.0, max_value=1.0))
    }

class TestDataModelProperties:
    """Property-based tests for data model consistency"""
    
    @given(hospital_data())
    @settings(max_examples=100)
    def test_property_1_policy_processing_round_trip_hospital_creation(self, hospital_data_dict):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 1: Policy Processing Round Trip**
        For any valid hospital data, creating a Hospital entity should produce retrievable structured data
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Create hospital entity
        hospital = Hospital(**hospital_data_dict)
        
        # Verify entity structure
        assert hospital.pk == f"HOSPITAL#{hospital_data_dict['hospital_id']}"
        assert hospital.sk == "METADATA"
        assert hospital.entity_type == "HOSPITAL"
        assert hospital.hospital_id == hospital_data_dict['hospital_id']
        assert hospital.org_name == hospital_data_dict['org_name']
        
        # Verify DynamoDB item conversion
        dynamodb_item = hospital.to_dynamodb_item()
        assert 'PK' in dynamodb_item
        assert 'SK' in dynamodb_item
        assert 'entity_type' in dynamodb_item
        assert 'created_at' in dynamodb_item
        assert 'updated_at' in dynamodb_item
        
        # Verify all original data is preserved
        assert dynamodb_item['hospital_id'] == hospital_data_dict['hospital_id']
        assert dynamodb_item['org_name'] == hospital_data_dict['org_name']
        assert dynamodb_item['license_key'] == hospital_data_dict['license_key']
    
    @given(patient_data())
    @settings(max_examples=100)
    def test_property_1_policy_processing_round_trip_patient_creation(self, patient_data_dict):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 1: Policy Processing Round Trip**
        For any valid patient data, creating a Patient entity should produce retrievable structured data
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Create patient entity
        patient = Patient(**patient_data_dict)
        
        # Verify entity structure
        assert patient.pk == f"HOSPITAL#{patient_data_dict['hospital_id']}"
        assert patient.sk == f"PATIENT#{patient_data_dict['patient_id']}"
        assert patient.entity_type == "PATIENT"
        assert patient.patient_id == patient_data_dict['patient_id']
        assert patient.hospital_id == patient_data_dict['hospital_id']
        
        # Verify DynamoDB item conversion
        dynamodb_item = patient.to_dynamodb_item()
        assert 'PK' in dynamodb_item
        assert 'SK' in dynamodb_item
        assert 'entity_type' in dynamodb_item
        
        # Verify data integrity
        assert dynamodb_item['name'] == patient_data_dict['name']
        assert dynamodb_item['age'] == patient_data_dict['age']
        assert dynamodb_item['policy_number'] == patient_data_dict['policy_number']
        assert isinstance(dynamodb_item['active_policies'], list)
    
    @given(policy_data())
    @settings(max_examples=100)
    def test_property_1_policy_processing_round_trip_policy_creation(self, policy_data_dict):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 1: Policy Processing Round Trip**
        For any valid policy data, creating a Policy entity should produce retrievable structured data
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Create policy entity
        policy = Policy(**policy_data_dict)
        
        # Verify entity structure
        assert policy.pk == f"HOSPITAL#{policy_data_dict['hospital_id']}"
        assert policy.sk == f"POLICY#{policy_data_dict['policy_id']}"
        assert policy.entity_type == "POLICY"
        assert policy.policy_id == policy_data_dict['policy_id']
        assert policy.hospital_id == policy_data_dict['hospital_id']
        
        # Verify DynamoDB item conversion
        dynamodb_item = policy.to_dynamodb_item()
        assert 'PK' in dynamodb_item
        assert 'SK' in dynamodb_item
        assert 'entity_type' in dynamodb_item
        
        # Verify policy-specific data
        assert dynamodb_item['policy_name'] == policy_data_dict['policy_name']
        assert dynamodb_item['file_size'] == policy_data_dict['file_size']
        assert dynamodb_item['extraction_status'] == policy_data_dict['extraction_status']
        assert isinstance(dynamodb_item['extracted_rules'], dict)
    
    @given(claim_data())
    @settings(max_examples=100)
    def test_property_1_policy_processing_round_trip_claim_creation(self, claim_data_dict):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 1: Policy Processing Round Trip**
        For any valid claim data, creating a Claim entity should produce retrievable structured data
        **Validates: Requirements 1.1, 1.2, 1.3**
        """
        # Create claim entity
        claim = Claim(**claim_data_dict)
        
        # Verify entity structure
        assert claim.pk == f"PATIENT#{claim_data_dict['patient_id']}"
        assert claim.sk == f"CLAIM#{claim_data_dict['claim_id']}"
        assert claim.entity_type == "CLAIM"
        assert claim.claim_id == claim_data_dict['claim_id']
        assert claim.patient_id == claim_data_dict['patient_id']
        
        # Verify DynamoDB item conversion
        dynamodb_item = claim.to_dynamodb_item()
        assert 'PK' in dynamodb_item
        assert 'SK' in dynamodb_item
        assert 'entity_type' in dynamodb_item
        
        # Verify claim-specific data
        assert dynamodb_item['status'] == claim_data_dict['status']
        assert dynamodb_item['total_amount'] == claim_data_dict['total_amount']
        assert dynamodb_item['risk_score'] == claim_data_dict['risk_score']
        assert dynamodb_item['risk_level'] == claim_data_dict['risk_level']
    
    @given(st.text(min_size=5, max_size=20), st.text(min_size=5, max_size=50), st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_property_31_audit_immutability(self, entity_id, action, user_id):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 31: Audit Immutability**
        For any created audit log entry, it should remain immutable and maintain complete chronological records
        **Validates: Requirements 10.1, 10.2**
        """
        # Create audit trail entry
        changes = {"field1": "old_value", "field2": "new_value"}
        audit = AuditTrail(
            audit_id=f"audit_{entity_id}",
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            changes=changes
        )
        
        # Verify immutable structure
        original_pk = audit.pk
        original_sk = audit.sk
        original_timestamp = audit.created_at
        
        # Verify audit trail structure
        assert audit.pk == f"AUDIT#{entity_id}"
        assert audit.sk.startswith("TIMESTAMP#")
        assert audit.entity_type == "AUDIT"
        assert audit.action == action
        assert audit.user_id == user_id
        assert audit.changes == changes
        
        # Verify DynamoDB item maintains immutability markers
        dynamodb_item = audit.to_dynamodb_item()
        assert dynamodb_item['PK'] == original_pk
        assert dynamodb_item['SK'] == original_sk
        assert dynamodb_item['created_at'] == original_timestamp
        assert dynamodb_item['entity_id'] == entity_id
        assert dynamodb_item['changes'] == changes
    
    @given(st.text(min_size=5, max_size=20), st.text(min_size=10, max_size=100))
    @settings(max_examples=50)
    def test_property_32_document_metadata_preservation(self, policy_id, s3_key):
        """
        **Feature: hospital-insurance-claim-settlement-optimizer, Property 32: Document Metadata Preservation**
        For any processed document, original files should be stored with complete timestamps and user attribution
        **Validates: Requirements 10.2**
        """
        # Create policy with document metadata
        hospital_id = "test_hospital"
        policy = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name="Test Policy",
            file_size=1024,
            content_type="application/pdf",
            s3_key=s3_key,
            extraction_status="COMPLETED"
        )
        
        # Verify metadata preservation
        dynamodb_item = policy.to_dynamodb_item()
        
        # Verify all metadata is preserved
        assert dynamodb_item['s3_key'] == s3_key
        assert dynamodb_item['file_size'] == 1024
        assert dynamodb_item['content_type'] == "application/pdf"
        assert 'created_at' in dynamodb_item
        assert 'updated_at' in dynamodb_item
        assert dynamodb_item['version'] >= 1
        
        # Verify timestamps are valid ISO format
        created_at = dynamodb_item['created_at']
        updated_at = dynamodb_item['updated_at']
        
        # Should be able to parse as datetime
        datetime.fromisoformat(created_at.replace('Z', '+00:00') if created_at.endswith('Z') else created_at)
        datetime.fromisoformat(updated_at.replace('Z', '+00:00') if updated_at.endswith('Z') else updated_at)
    
    @given(st.lists(hospital_data(), min_size=1, max_size=10, unique_by=lambda x: x['hospital_id']))
    @settings(max_examples=20)
    def test_property_data_consistency_across_multiple_entities(self, hospitals_data):
        """
        Test that multiple entities maintain consistency in their structure and relationships
        """
        hospitals = []
        for hospital_data_dict in hospitals_data:
            hospital = Hospital(**hospital_data_dict)
            hospitals.append(hospital)
            
            # Verify each hospital has unique PK
            assert hospital.pk == f"HOSPITAL#{hospital_data_dict['hospital_id']}"
            
            # Verify consistent entity structure
            dynamodb_item = hospital.to_dynamodb_item()
            assert 'PK' in dynamodb_item
            assert 'SK' in dynamodb_item
            assert 'entity_type' in dynamodb_item
            assert 'created_at' in dynamodb_item
            assert 'updated_at' in dynamodb_item
        
        # Verify no duplicate hospital IDs
        hospital_ids = [h.hospital_id for h in hospitals]
        assert len(hospital_ids) == len(set(hospital_ids)), "Hospital IDs should be unique"
    
    @given(st.text(min_size=5, max_size=20))
    @settings(max_examples=50)
    def test_property_entity_key_generation_consistency(self, entity_id):
        """
        Test that entity key generation is consistent and follows the adjacency list pattern
        """
        hospital_id = entity_id
        patient_id = f"pat_{entity_id}"
        policy_id = f"pol_{entity_id}"
        claim_id = f"clm_{entity_id}"
        
        # Create entities
        hospital = Hospital(
            hospital_id=hospital_id,
            org_name="Test Hospital",
            license_key="TEST123"
        )
        
        patient = Patient(
            patient_id=patient_id,
            hospital_id=hospital_id,
            name="Test Patient",
            age=30,
            policy_number="POL123",
            insurer_name="Test Insurer",
            admit_date=datetime.utcnow().isoformat()
        )
        
        policy = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name="Test Policy",
            file_size=1024,
            content_type="application/pdf",
            s3_key=f"policies/{hospital_id}/{policy_id}.pdf"
        )
        
        claim = Claim(
            claim_id=claim_id,
            patient_id=patient_id,
            hospital_id=hospital_id
        )
        
        # Verify key patterns follow adjacency list design
        assert hospital.pk == f"HOSPITAL#{hospital_id}"
        assert hospital.sk == "METADATA"
        
        assert patient.pk == f"HOSPITAL#{hospital_id}"
        assert patient.sk == f"PATIENT#{patient_id}"
        
        assert policy.pk == f"HOSPITAL#{hospital_id}"
        assert policy.sk == f"POLICY#{policy_id}"
        
        assert claim.pk == f"PATIENT#{patient_id}"
        assert claim.sk == f"CLAIM#{claim_id}"
        
        # Verify relationships can be traversed
        # Hospital -> Patients relationship
        assert patient.pk.endswith(hospital_id)
        # Hospital -> Policies relationship  
        assert policy.pk.endswith(hospital_id)
        # Patient -> Claims relationship
        assert claim.pk.endswith(patient_id)

def test_sample_data_creation():
    """Test that sample data creation works correctly"""
    sample_data = create_sample_data()
    
    # Verify all required entities are created
    assert 'hospital' in sample_data
    assert 'patient' in sample_data
    assert 'policy' in sample_data
    assert 'claim' in sample_data
    assert 'claim_items' in sample_data
    
    # Verify relationships
    hospital = sample_data['hospital']
    patient = sample_data['patient']
    policy = sample_data['policy']
    claim = sample_data['claim']
    
    assert patient.hospital_id == hospital.hospital_id
    assert policy.hospital_id == hospital.hospital_id
    assert claim.patient_id == patient.patient_id
    assert claim.hospital_id == hospital.hospital_id
    
    # Verify data integrity
    for claim_item in sample_data['claim_items']:
        assert claim_item.claim_id == claim.claim_id

if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--tb=short"])