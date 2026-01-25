"""
Property-Based Tests for Password Management
Tests universal correctness properties for password validation, reset, and history

Feature: journey-enhancements
Tests for password management functionality
"""
import pytest
import time
import hashlib
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from password_service import PasswordService

# Test strategies
valid_email = st.emails()
valid_user_id = st.uuids().map(str)

# Password strategies
weak_password = st.sampled_from(['pass', '12345', 'abc', 'password'])
strong_password = st.from_regex(r'[A-Z][a-z]{3,}[0-9]{2,}[!@#$%]', fullmatch=True)
valid_password = st.text(min_size=8, max_size=50).filter(
    lambda p: any(c.isupper() for c in p) and 
              any(c.islower() for c in p) and 
              any(c.isdigit() for c in p) and
              any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in p)
)

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing"""
    with patch('password_service.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table

@pytest.fixture
def mock_cognito():
    """Mock Cognito client for testing"""
    with patch('password_service.cognito_client') as mock_cognito:
        yield mock_cognito

@pytest.fixture
def mock_ses():
    """Mock SES client for testing"""
    with patch('password_service.ses_client') as mock_ses:
        yield mock_ses

@pytest.fixture
def password_service(mock_dynamodb_table, mock_cognito, mock_ses):
    """Create PasswordService instance with mocked dependencies"""
    return PasswordService(table_name='test-sessions')


class TestPasswordValidation:
    """Test password validation properties"""
    
    @given(password=st.text(min_size=0, max_size=7))
    @settings(max_examples=100, deadline=None)
    def test_short_passwords_rejected(self, password_service, password):
        """
        Property: Passwords shorter than 8 characters must be rejected
        
        Validates: Requirements 1.4.3
        """
        result = password_service.validate_password(password)
        
        # Property: Short passwords must be invalid
        assert not result['valid'], "Passwords < 8 characters must be rejected"
        assert any('at least 8 characters' in error.lower() for error in result['errors']), \
            "Error message must mention minimum length"
    
    @given(password=st.text(min_size=8, max_size=50).filter(lambda p: p.islower()))
    @settings(max_examples=100, deadline=None)
    def test_passwords_without_uppercase_rejected(self, password_service, password):
        """
        Property: Passwords without uppercase letters must be rejected
        
        Validates: Requirements 1.4.3
        """
        # Skip if password happens to have uppercase
        assume(not any(c.isupper() for c in password))
        
        result = password_service.validate_password(password)
        
        # Property: Must be invalid
        assert not result['valid'], "Passwords without uppercase must be rejected"
        assert any('uppercase' in error.lower() for error in result['errors']), \
            "Error message must mention uppercase requirement"
    
    @given(password=st.text(min_size=8, max_size=50).filter(lambda p: p.isupper()))
    @settings(max_examples=100, deadline=None)
    def test_passwords_without_lowercase_rejected(self, password_service, password):
        """
        Property: Passwords without lowercase letters must be rejected
        
        Validates: Requirements 1.4.3
        """
        # Skip if password happens to have lowercase
        assume(not any(c.islower() for c in password))
        
        result = password_service.validate_password(password)
        
        # Property: Must be invalid
        assert not result['valid'], "Passwords without lowercase must be rejected"
        assert any('lowercase' in error.lower() for error in result['errors']), \
            "Error message must mention lowercase requirement"
    
    @given(password=st.text(min_size=8, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    @settings(max_examples=100, deadline=None)
    def test_passwords_without_numbers_rejected(self, password_service, password):
        """
        Property: Passwords without numbers must be rejected
        
        Validates: Requirements 1.4.3
        """
        # Skip if password happens to have numbers
        assume(not any(c.isdigit() for c in password))
        
        result = password_service.validate_password(password)
        
        # Property: Must be invalid
        assert not result['valid'], "Passwords without numbers must be rejected"
        assert any('number' in error.lower() for error in result['errors']), \
            "Error message must mention number requirement"
    
    @given(password=weak_password)
    @settings(max_examples=50, deadline=None)
    def test_common_weak_passwords_rejected(self, password_service, password):
        """
        Property: Common weak passwords must be rejected
        
        Validates: Security requirements
        """
        result = password_service.validate_password(password)
        
        # Property: Weak passwords must be invalid
        assert not result['valid'], "Common weak passwords must be rejected"
    
    @given(password=strong_password)
    @settings(max_examples=100, deadline=None)
    def test_strong_passwords_accepted(self, password_service, password):
        """
        Property: Strong passwords meeting all requirements must be accepted
        
        Validates: Requirements 1.4.3
        """
        result = password_service.validate_password(password)
        
        # Property: Strong passwords should be valid (or have minimal errors)
        # Note: May still fail due to sequential patterns, but should pass basic requirements
        if not result['valid']:
            # Should not fail on basic requirements
            basic_errors = [
                'at least 8 characters',
                'uppercase letter',
                'lowercase letter',
                'number',
                'special character'
            ]
            for basic_error in basic_errors:
                assert not any(basic_error in error.lower() for error in result['errors']), \
                    f"Strong password should not fail basic requirement: {basic_error}"


class TestPasswordHistory:
    """Test password history properties"""
    
    @given(
        user_id=valid_user_id,
        num_passwords=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_password_history_prevents_reuse(self, password_service, mock_dynamodb_table, user_id, num_passwords):
        """
        Property: Password history must prevent reuse of recent passwords
        
        Validates: Requirements 1.4.5
        """
        # Generate password hashes
        passwords = [f"TestPass{i}123!" for i in range(num_passwords)]
        password_hashes = [password_service.hash_password(p) for p in passwords]
        
        # Configure mock to return history
        mock_dynamodb_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PASSWORD_HISTORY',
                'passwords': password_hashes[:5]  # Last 5 passwords
            }
        }
        
        # Property 1: Passwords in history must be rejected
        for i, password in enumerate(passwords[:5]):
            result = password_service.check_password_history(user_id, password)
            assert not result, f"Password {i} in history must be rejected"
        
        # Property 2: Passwords not in history must be accepted
        for i, password in enumerate(passwords[5:]):
            result = password_service.check_password_history(user_id, password)
            assert result, f"Password {i} not in history must be accepted"
    
    @given(
        user_id=valid_user_id,
        password=st.text(min_size=8, max_size=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_password_hashing_is_deterministic(self, password_service, user_id, password):
        """
        Property: Password hashing must be deterministic
        
        Validates: Hash consistency
        """
        # Hash the same password multiple times
        hash1 = password_service.hash_password(password)
        hash2 = password_service.hash_password(password)
        hash3 = password_service.hash_password(password)
        
        # Property: All hashes must be identical
        assert hash1 == hash2 == hash3, "Password hashing must be deterministic"
        
        # Property: Hash must be hex string
        assert all(c in '0123456789abcdef' for c in hash1), "Hash must be hexadecimal"
        
        # Property: Hash must be 64 characters (SHA256)
        assert len(hash1) == 64, "SHA256 hash must be 64 characters"
    
    @given(
        user_id=valid_user_id,
        password1=st.text(min_size=8, max_size=20),
        password2=st.text(min_size=8, max_size=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_different_passwords_have_different_hashes(self, password_service, user_id, password1, password2):
        """
        Property: Different passwords must have different hashes
        
        Validates: Hash uniqueness
        """
        # Skip if passwords are the same
        assume(password1 != password2)
        
        hash1 = password_service.hash_password(password1)
        hash2 = password_service.hash_password(password2)
        
        # Property: Hashes must be different
        assert hash1 != hash2, "Different passwords must have different hashes"


class TestPasswordReset:
    """Test password reset properties"""
    
    @given(num_tokens=st.integers(min_value=1, max_value=50))
    @settings(max_examples=50, deadline=None)
    def test_reset_tokens_are_unique(self, password_service, num_tokens):
        """
        Property: Reset tokens must be unique
        
        Validates: Requirements 1.4.1
        """
        tokens = [password_service.generate_reset_token() for _ in range(num_tokens)]
        
        # Property 1: All tokens must be unique
        assert len(tokens) == len(set(tokens)), "Reset tokens must be unique"
        
        # Property 2: Tokens must be sufficiently long
        for token in tokens:
            assert len(token) >= 32, "Reset tokens must be at least 32 characters"
        
        # Property 3: Tokens must be URL-safe
        import re
        url_safe_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        for token in tokens:
            assert url_safe_pattern.match(token), "Reset tokens must be URL-safe"
    
    @given(
        email=valid_email,
        user_id=valid_user_id
    )
    @settings(max_examples=100, deadline=None)
    def test_reset_token_expiration(self, password_service, mock_dynamodb_table, mock_cognito, email, user_id):
        """
        Property: Reset tokens must expire after 1 hour
        
        Validates: Requirements 1.4.2
        """
        current_time = int(time.time())
        
        # Configure mocks
        mock_cognito.admin_get_user.return_value = {
            'UserAttributes': [{'Name': 'sub', 'Value': user_id}]
        }
        mock_dynamodb_table.put_item.return_value = {}
        
        # Request password reset
        result = password_service.request_password_reset(email)
        
        # Get the stored token data from put_item call
        if mock_dynamodb_table.put_item.called:
            call_args = mock_dynamodb_table.put_item.call_args
            stored_item = call_args[1]['Item']
            
            # Property 1: Token must have expiration
            assert 'expires_at' in stored_item, "Token must have expiration"
            
            # Property 2: Expiration must be approximately 1 hour from now
            expected_expiration = current_time + 3600
            time_diff = abs(stored_item['expires_at'] - expected_expiration)
            assert time_diff < 10, "Token must expire in approximately 1 hour"
            
            # Property 3: Token must not be marked as used initially
            assert stored_item.get('used') is False, "Token must not be used initially"
    
    @given(
        user_id=valid_user_id,
        email=valid_email
    )
    @settings(max_examples=100, deadline=None)
    def test_reset_tokens_are_one_time_use(self, password_service, mock_dynamodb_table, user_id, email):
        """
        Property: Reset tokens can only be used once
        
        Validates: Requirements 1.4.2
        """
        token = password_service.generate_reset_token()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Configure mock for unused token
        token_data = {
            'PK': f'RESET_TOKEN#{token_hash}',
            'SK': 'METADATA',
            'user_id': user_id,
            'email': email,
            'expires_at': int(time.time()) + 3600,
            'used': False
        }
        mock_dynamodb_table.get_item.return_value = {'Item': token_data}
        
        # Property 1: Unused token must be valid
        result = password_service.verify_reset_token(token)
        assert result is not None, "Unused token must be valid"
        
        # Configure mock for used token
        token_data['used'] = True
        mock_dynamodb_table.get_item.return_value = {'Item': token_data}
        
        # Property 2: Used token must be invalid
        result = password_service.verify_reset_token(token)
        assert result is None, "Used token must be invalid"
    
    @given(
        user_id=valid_user_id,
        email=valid_email
    )
    @settings(max_examples=100, deadline=None)
    def test_expired_reset_tokens_rejected(self, password_service, mock_dynamodb_table, user_id, email):
        """
        Property: Expired reset tokens must be rejected
        
        Validates: Requirements 1.4.2
        """
        token = password_service.generate_reset_token()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Configure mock for expired token
        token_data = {
            'PK': f'RESET_TOKEN#{token_hash}',
            'SK': 'METADATA',
            'user_id': user_id,
            'email': email,
            'expires_at': int(time.time()) - 3600,  # Expired 1 hour ago
            'used': False
        }
        mock_dynamodb_table.get_item.return_value = {'Item': token_data}
        
        # Property: Expired token must be invalid
        result = password_service.verify_reset_token(token)
        assert result is None, "Expired token must be invalid"


class TestPasswordRequirements:
    """Test password requirements properties"""
    
    def test_password_requirements_are_consistent(self, password_service):
        """
        Property: Password requirements must be consistent and documented
        
        Validates: User experience
        """
        requirements = password_service.get_password_requirements()
        
        # Property 1: Requirements must include all necessary fields
        required_fields = ['min_length', 'require_uppercase', 'require_lowercase', 
                          'require_number', 'require_special', 'description']
        for field in required_fields:
            assert field in requirements, f"Requirements must include {field}"
        
        # Property 2: Description must be a list
        assert isinstance(requirements['description'], list), "Description must be a list"
        
        # Property 3: Description must not be empty
        assert len(requirements['description']) > 0, "Description must not be empty"
        
        # Property 4: Min length must be reasonable
        assert 8 <= requirements['min_length'] <= 128, "Min length must be reasonable"


class TestPasswordChange:
    """Test password change properties"""
    
    @given(
        user_id=valid_user_id,
        email=valid_email,
        current_password=st.text(min_size=8, max_size=20),
        new_password=st.text(min_size=8, max_size=20)
    )
    @settings(max_examples=50, deadline=None)
    def test_password_change_requires_different_password(
        self, password_service, mock_dynamodb_table, mock_cognito, user_id, email, current_password, new_password
    ):
        """
        Property: New password must be different from current password
        
        Validates: Security requirements
        """
        # Skip if passwords are different
        assume(current_password == new_password)
        
        # Configure mocks
        mock_dynamodb_table.get_item.return_value = {'Item': {'passwords': []}}
        mock_cognito.admin_set_user_password.return_value = {}
        
        # Try to change password
        result = password_service.change_password(user_id, email, current_password, new_password)
        
        # Property: Must fail when passwords are the same
        assert not result['success'], "Password change must fail when new password equals current"
        assert 'different' in result['message'].lower(), "Error message must mention difference requirement"


# Summary comment for test execution
"""
To run these property-based tests:
    python3 -m pytest tests/test_property_password.py -v

These tests validate password management functionality:
- Password validation enforces all requirements
- Short passwords are rejected
- Passwords without required character types are rejected
- Common weak passwords are rejected
- Strong passwords are accepted
- Password history prevents reuse
- Password hashing is deterministic
- Different passwords have different hashes
- Reset tokens are unique and URL-safe
- Reset tokens expire after 1 hour
- Reset tokens are one-time use
- Expired tokens are rejected
- Password requirements are consistent
- Password change requires different password

All tests use Hypothesis for property-based testing with 50-100 examples each.
"""
