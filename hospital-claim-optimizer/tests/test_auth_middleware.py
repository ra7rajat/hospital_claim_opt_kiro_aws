"""
Tests for authentication middleware
"""
import pytest
import json
import sys
import os

# Add the lambda layers to the path for testing
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from auth_middleware import (
    extract_user_info, check_permission, UserRole, Permission,
    require_auth, AuthenticationError, AuthorizationError
)
from security_config import (
    generate_secure_token, hash_sensitive_data, verify_hash,
    sanitize_log_data, create_audit_entry, validate_hipaa_compliance,
    create_secure_response, validate_input_data
)

class TestAuthMiddleware:
    """Test authentication middleware functionality"""
    
    def test_extract_user_info_success(self):
        """Test successful user info extraction from Cognito claims"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user123',
                        'email': 'doctor@hospital.com',
                        'cognito:username': 'doctor1',
                        'custom:role': 'doctor',
                        'custom:hospital_id': 'hosp_001',
                        'cognito:groups': 'doctors,staff'
                    }
                }
            }
        }
        
        user_info = extract_user_info(event)
        
        assert user_info['user_id'] == 'user123'
        assert user_info['email'] == 'doctor@hospital.com'
        assert user_info['role'] == 'doctor'
        assert user_info['hospital_id'] == 'hosp_001'
        assert 'doctors' in user_info['groups']
    
    def test_extract_user_info_missing_claims(self):
        """Test user info extraction with missing claims"""
        event = {
            'requestContext': {
                'authorizer': {}
            }
        }
        
        with pytest.raises(AuthenticationError):
            extract_user_info(event)
    
    def test_check_permission_hospital_admin(self):
        """Test permission checking for hospital admin"""
        # Hospital admin should have all permissions
        assert check_permission('hospital_admin', Permission.UPLOAD_POLICY)
        assert check_permission('hospital_admin', Permission.CHECK_ELIGIBILITY)
        assert check_permission('hospital_admin', Permission.AUDIT_CLAIM)
        assert check_permission('hospital_admin', Permission.VIEW_DASHBOARD)
    
    def test_check_permission_doctor(self):
        """Test permission checking for doctor"""
        # Doctor should only have limited permissions
        assert check_permission('doctor', Permission.CHECK_ELIGIBILITY)
        assert check_permission('doctor', Permission.VIEW_PATIENT_DATA)
        assert not check_permission('doctor', Permission.UPLOAD_POLICY)
        assert not check_permission('doctor', Permission.AUDIT_CLAIM)
    
    def test_check_permission_tpa_user(self):
        """Test permission checking for TPA user"""
        # TPA user should have audit and reporting permissions
        assert check_permission('tpa_user', Permission.AUDIT_CLAIM)
        assert check_permission('tpa_user', Permission.VIEW_DASHBOARD)
        assert check_permission('tpa_user', Permission.GENERATE_REPORTS)
        assert not check_permission('tpa_user', Permission.UPLOAD_POLICY)
    
    def test_check_permission_invalid_role(self):
        """Test permission checking with invalid role"""
        assert not check_permission('invalid_role', Permission.UPLOAD_POLICY)

class TestSecurityConfig:
    """Test security configuration utilities"""
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        
        # Tokens should be different
        assert token1 != token2
        # Tokens should be non-empty strings
        assert isinstance(token1, str)
        assert len(token1) > 0
    
    def test_hash_sensitive_data(self):
        """Test sensitive data hashing"""
        data = "sensitive_password"
        result = hash_sensitive_data(data)
        
        assert 'hash' in result
        assert 'salt' in result
        assert result['hash'] != data  # Should be hashed
        assert len(result['salt']) > 0
    
    def test_verify_hash(self):
        """Test hash verification"""
        data = "test_password"
        hash_result = hash_sensitive_data(data)
        
        # Correct password should verify
        assert verify_hash(data, hash_result['hash'], hash_result['salt'])
        
        # Wrong password should not verify
        assert not verify_hash("wrong_password", hash_result['hash'], hash_result['salt'])
    
    def test_sanitize_log_data(self):
        """Test log data sanitization"""
        sensitive_data = {
            'username': 'doctor1',
            'password': 'secret123',  # 9 chars - will be partially masked
            'patient_id': 'PAT123',   # 6 chars - will be completely masked
            'normal_field': 'normal_value',
            'authorization': 'Bearer token123456789'  # Long - will be partially masked
        }
        
        sanitized = sanitize_log_data(sensitive_data)
        
        assert sanitized['username'] == 'doctor1'  # Not sensitive
        assert sanitized['password'] == '*****t123'  # Partially masked (9 chars)
        assert sanitized['patient_id'] == '***MASKED***'  # Completely masked (6 chars)
        assert sanitized['normal_field'] == 'normal_value'  # Not sensitive
        assert sanitized['authorization'].endswith('6789')  # Partially masked, ends with last 4
    
    def test_create_audit_entry(self):
        """Test audit entry creation"""
        audit_entry = create_audit_entry(
            user_id='user123',
            action='upload_policy',
            resource_type='policy',
            resource_id='pol_001',
            details={'policy_name': 'Test Policy'},
            ip_address='192.168.1.1'
        )
        
        assert audit_entry['user_id'] == 'user123'
        assert audit_entry['action'] == 'upload_policy'
        assert audit_entry['resource_type'] == 'policy'
        assert audit_entry['resource_id'] == 'pol_001'
        assert 'timestamp' in audit_entry
        assert 'audit_id' in audit_entry
        assert audit_entry['ip_address'] == '192.168.1.1'
    
    def test_validate_hipaa_compliance_pass(self):
        """Test HIPAA compliance validation - passing case"""
        clean_data = {
            'user_id': 'user123',
            'action': 'view_dashboard',
            'timestamp': '2024-01-01T00:00:00Z',
            'encryption_status': 'encrypted'
        }
        
        result = validate_hipaa_compliance(clean_data)
        
        assert result['is_compliant'] is True
        assert len(result['violations']) == 0
    
    def test_validate_hipaa_compliance_fail(self):
        """Test HIPAA compliance validation - failing case"""
        sensitive_data = {
            'user_id': 'user123',
            'patient_name': 'John Doe',  # PHI exposure
            'ssn': '123-45-6789',  # PHI exposure
            'encryption_status': 'unencrypted'  # Encryption violation
        }
        
        result = validate_hipaa_compliance(sensitive_data)
        
        assert result['is_compliant'] is False
        assert len(result['violations']) > 0
        assert len(result['recommendations']) > 0
    
    def test_create_secure_response(self):
        """Test secure response creation"""
        response = create_secure_response(200, {'message': 'success'})
        
        assert response['statusCode'] == 200
        assert 'headers' in response
        assert 'Strict-Transport-Security' in response['headers']
        assert 'X-Content-Type-Options' in response['headers']
        assert 'X-Frame-Options' in response['headers']
        
        body = json.loads(response['body'])
        assert body['message'] == 'success'
    
    def test_validate_input_data_success(self):
        """Test input data validation - success case"""
        data = {
            'hospital_id': 'hosp_001',
            'policy_name': 'Test Policy',
            'file_size': 1024
        }
        required_fields = ['hospital_id', 'policy_name']
        
        result = validate_input_data(data, required_fields)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert result['sanitized_data']['hospital_id'] == 'hosp_001'
    
    def test_validate_input_data_missing_fields(self):
        """Test input data validation - missing required fields"""
        data = {
            'policy_name': 'Test Policy'
        }
        required_fields = ['hospital_id', 'policy_name']
        
        result = validate_input_data(data, required_fields)
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'Missing required field: hospital_id' in result['errors']
    
    def test_validate_input_data_sanitization(self):
        """Test input data sanitization"""
        data = {
            'policy_name': 'Test<script>alert("xss")</script>Policy',
            'description': 'javascript:alert("xss")'
        }
        required_fields = ['policy_name']
        
        result = validate_input_data(data, required_fields)
        
        assert result['is_valid'] is True
        # Script tags should be removed
        assert '<script>' not in result['sanitized_data']['policy_name']
        assert 'javascript:' not in result['sanitized_data']['description']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])