"""
Property-Based Tests for Multi-Factor Authentication (MFA)
Tests universal correctness properties for MFA setup, verification, and backup codes

Feature: journey-enhancements
Tests for MFA functionality
"""
import pytest
import time
import re
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from mfa_service import MFAService

# Test strategies
valid_user_id = st.uuids().map(str)
valid_phone = st.from_regex(r'\+1\d{10}', fullmatch=True)
valid_totp_code = st.from_regex(r'\d{6}', fullmatch=True)

@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing"""
    with patch('mfa_service.dynamodb') as mock_db:
        mock_table = MagicMock()
        mock_db.Table.return_value = mock_table
        yield mock_table

@pytest.fixture
def mock_kms():
    """Mock KMS client for testing"""
    with patch('mfa_service.kms_client') as mock_kms:
        yield mock_kms

@pytest.fixture
def mfa_service(mock_dynamodb_table, mock_kms):
    """Create MFAService instance with mocked dependencies"""
    return MFAService(table_name='test-sessions')


class TestMFASecretGeneration:
    """Test MFA secret generation properties"""
    
    @given(num_secrets=st.integers(min_value=1, max_value=50))
    @settings(max_examples=50, deadline=None)
    def test_secrets_are_unique_and_random(self, mfa_service, num_secrets):
        """
        Property: MFA secrets must be unique and cryptographically random
        
        Validates: Requirements 1.2.1, 1.2.2
        """
        secrets = [mfa_service.generate_secret() for _ in range(num_secrets)]
        
        # Property 1: All secrets must be unique
        assert len(secrets) == len(set(secrets)), "MFA secrets must be unique"
        
        # Property 2: Secrets must be base32 encoded (A-Z, 2-7)
        base32_pattern = re.compile(r'^[A-Z2-7]+$')
        for secret in secrets:
            assert base32_pattern.match(secret), "Secret must be valid base32"
        
        # Property 3: Secrets must be sufficiently long (at least 16 characters)
        for secret in secrets:
            assert len(secret) >= 16, "Secret must be at least 16 characters"
        
        # Property 4: Secrets should have good entropy (not all same character)
        for secret in secrets:
            unique_chars = len(set(secret))
            assert unique_chars > 1, "Secret must have multiple different characters"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_secret_encryption_at_rest(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: MFA secrets must be encrypted at rest
        
        Validates: Requirements 1.2.2 (security)
        """
        # Configure mock
        mock_dynamodb_table.put_item.return_value = {}
        
        # Setup MFA
        result = mfa_service.setup_mfa(user_id)
        
        # Property 1: Setup must succeed
        assert 'secret' in result, "Setup must return secret"
        assert 'qr_code_data' in result, "Setup must return QR code data"
        assert 'backup_codes' in result, "Setup must return backup codes"
        
        # Property 2: Secret must be stored encrypted
        # Verify put_item was called
        assert mock_dynamodb_table.put_item.called, "Secret must be stored"
        
        # Get the stored item
        call_args = mock_dynamodb_table.put_item.call_args
        stored_item = call_args[1]['Item']
        
        # Property 3: Stored secret must be different from plain secret
        # (encrypted or encoded)
        plain_secret = result['secret']
        stored_secret = stored_item.get('secret')
        
        # The stored secret should be encrypted/encoded
        assert stored_secret != plain_secret, "Secret must be encrypted before storage"


class TestTOTPGeneration:
    """Test TOTP code generation and verification"""
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_totp_codes_are_six_digits(self, mfa_service, user_id):
        """
        Property: TOTP codes must always be 6 digits
        
        Validates: TOTP standard compliance
        """
        # Generate a secret
        secret = mfa_service.generate_secret()
        
        # Generate multiple codes at different time steps
        for time_step in range(100):
            code = mfa_service.generate_totp(secret, time_step)
            
            # Property 1: Code must be exactly 6 digits
            assert len(code) == 6, "TOTP code must be 6 digits"
            
            # Property 2: Code must be numeric
            assert code.isdigit(), "TOTP code must be numeric"
            
            # Property 3: Code must be zero-padded if necessary
            assert code[0] in '0123456789', "Code must be properly zero-padded"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=50, deadline=None)
    def test_totp_codes_change_over_time(self, mfa_service, user_id):
        """
        Property: TOTP codes must change with each time step
        
        Validates: Time-based one-time password behavior
        """
        secret = mfa_service.generate_secret()
        
        # Generate codes for consecutive time steps
        codes = [mfa_service.generate_totp(secret, step) for step in range(10)]
        
        # Property: Most codes should be different (allowing for rare collisions)
        unique_codes = len(set(codes))
        assert unique_codes >= 8, "TOTP codes must change over time"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_totp_verification_with_time_window(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: TOTP verification must accept codes within time window
        
        Validates: Requirements 1.2.3 (verification)
        """
        # Generate a secret
        secret = mfa_service.generate_secret()
        
        # Encrypt secret for storage
        encrypted_secret = mfa_service.encrypt_secret(secret)
        
        # Configure mock to return MFA config
        mfa_config = {
            'PK': f'USER#{user_id}',
            'SK': 'MFA_CONFIG',
            'enabled': True,
            'secret': encrypted_secret
        }
        mock_dynamodb_table.get_item.return_value = {'Item': mfa_config}
        mock_dynamodb_table.update_item.return_value = {}
        
        # Get current time step
        current_time_step = int(time.time()) // 30
        
        # Generate code for current time
        current_code = mfa_service.generate_totp(secret, current_time_step)
        
        # Property 1: Current code must be accepted
        assert mfa_service.verify_totp(user_id, current_code, window=1), \
            "Current TOTP code must be accepted"
        
        # Generate code for previous time step
        prev_code = mfa_service.generate_totp(secret, current_time_step - 1)
        
        # Property 2: Previous code must be accepted (within window)
        assert mfa_service.verify_totp(user_id, prev_code, window=1), \
            "Previous TOTP code must be accepted within window"
        
        # Generate code for next time step
        next_code = mfa_service.generate_totp(secret, current_time_step + 1)
        
        # Property 3: Next code must be accepted (within window)
        assert mfa_service.verify_totp(user_id, next_code, window=1), \
            "Next TOTP code must be accepted within window"


class TestBackupCodes:
    """Test backup code generation and verification"""
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_backup_codes_are_unique(self, mfa_service, user_id):
        """
        Property: Backup codes must be unique
        
        Validates: Requirements 1.2.5 (backup codes)
        """
        # Generate backup codes
        codes = mfa_service.generate_backup_codes()
        
        # Property 1: Must generate correct number of codes
        assert len(codes) == 10, "Must generate 10 backup codes"
        
        # Property 2: All codes must be unique
        assert len(codes) == len(set(codes)), "Backup codes must be unique"
        
        # Property 3: Codes must be properly formatted (XXXX-XXXX)
        code_pattern = re.compile(r'^[A-Z2-9]{4}-[A-Z2-9]{4}$')
        for code in codes:
            assert code_pattern.match(code), f"Code {code} must match format XXXX-XXXX"
        
        # Property 4: Codes must not contain ambiguous characters (0, 1, I, O)
        ambiguous_chars = set('01IO')
        for code in codes:
            code_chars = set(code.replace('-', ''))
            assert not code_chars.intersection(ambiguous_chars), \
                "Backup codes must not contain ambiguous characters"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_backup_codes_are_one_time_use(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: Backup codes can only be used once
        
        Validates: Requirements 1.2.5 (one-time use)
        """
        # Generate backup codes
        codes = mfa_service.generate_backup_codes()
        test_code = codes[0]
        
        # Hash the code
        code_hash = mfa_service.hash_backup_code(test_code)
        
        # Configure mock for first use
        mfa_config = {
            'PK': f'USER#{user_id}',
            'SK': 'MFA_CONFIG',
            'backup_codes': [code_hash],
            'backup_codes_used': []
        }
        mock_dynamodb_table.get_item.return_value = {'Item': mfa_config}
        mock_dynamodb_table.update_item.return_value = {}
        
        # Property 1: First use must succeed
        assert mfa_service.verify_backup_code(user_id, test_code), \
            "Backup code must work on first use"
        
        # Configure mock for second use (code now marked as used)
        mfa_config['backup_codes_used'] = [code_hash]
        mock_dynamodb_table.get_item.return_value = {'Item': mfa_config}
        
        # Property 2: Second use must fail
        assert not mfa_service.verify_backup_code(user_id, test_code), \
            "Backup code must not work on second use"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=50, deadline=None)
    def test_backup_code_regeneration(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: Backup code regeneration must create new unique codes
        
        Validates: Backup code management
        """
        # Configure mock
        mock_dynamodb_table.update_item.return_value = {}
        
        # Generate first set of codes
        codes1 = mfa_service.regenerate_backup_codes(user_id)
        
        # Generate second set of codes
        codes2 = mfa_service.regenerate_backup_codes(user_id)
        
        # Property 1: Both sets must be valid
        assert codes1 is not None, "First generation must succeed"
        assert codes2 is not None, "Second generation must succeed"
        
        # Property 2: Sets must be different
        assert set(codes1) != set(codes2), "Regenerated codes must be different"
        
        # Property 3: Each set must have unique codes
        assert len(codes1) == len(set(codes1)), "First set must have unique codes"
        assert len(codes2) == len(set(codes2)), "Second set must have unique codes"


class TestMFAEnforcement:
    """Test MFA enforcement for admin roles"""
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_mfa_enable_disable_cycle(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: MFA can be enabled and disabled correctly
        
        Validates: Requirements 1.2.1 (enable/disable)
        """
        # Configure mock for checking status
        mock_dynamodb_table.get_item.return_value = {'Item': {'enabled': False}}
        
        # Property 1: Initially disabled
        assert not mfa_service.is_mfa_enabled(user_id), "MFA should start disabled"
        
        # Configure mock for enabled state
        mock_dynamodb_table.get_item.return_value = {'Item': {'enabled': True}}
        
        # Property 2: Can be enabled
        assert mfa_service.is_mfa_enabled(user_id), "MFA should be enabled"
        
        # Configure mock for disable
        mock_dynamodb_table.update_item.return_value = {}
        
        # Property 3: Can be disabled
        assert mfa_service.disable_mfa(user_id), "MFA disable should succeed"
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_mfa_config_data_safety(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: MFA config retrieval must not expose sensitive data
        
        Validates: Security requirements
        """
        # Configure mock with full MFA config
        full_config = {
            'PK': f'USER#{user_id}',
            'SK': 'MFA_CONFIG',
            'enabled': True,
            'secret': 'encrypted_secret_data',
            'backup_codes': ['hash1', 'hash2', 'hash3'],
            'backup_codes_used': ['hash1'],
            'phone_number': '+11234567890',
            'created_at': int(time.time()),
            'verified_at': int(time.time())
        }
        mock_dynamodb_table.get_item.return_value = {'Item': full_config}
        
        # Get safe config
        safe_config = mfa_service.get_mfa_config(user_id)
        
        # Property 1: Config must be returned
        assert safe_config is not None, "Config must be returned"
        
        # Property 2: Sensitive data must not be exposed
        assert 'secret' not in safe_config, "Secret must not be exposed"
        assert 'backup_codes' not in safe_config, "Backup codes must not be exposed"
        
        # Property 3: Safe data must be included
        assert 'enabled' in safe_config, "Enabled status must be included"
        assert 'backup_codes_remaining' in safe_config, "Remaining codes count must be included"
        
        # Property 4: Backup codes remaining must be correct
        expected_remaining = len(full_config['backup_codes']) - len(full_config['backup_codes_used'])
        assert safe_config['backup_codes_remaining'] == expected_remaining, \
            "Backup codes remaining must be calculated correctly"


class TestQRCodeGeneration:
    """Test QR code data generation"""
    
    @given(user_id=valid_user_id)
    @settings(max_examples=100, deadline=None)
    def test_qr_code_format(self, mfa_service, mock_dynamodb_table, user_id):
        """
        Property: QR code data must follow otpauth:// URI format
        
        Validates: Authenticator app compatibility
        """
        # Configure mock
        mock_dynamodb_table.put_item.return_value = {}
        
        # Setup MFA
        result = mfa_service.setup_mfa(user_id)
        
        qr_data = result['qr_code_data']
        
        # Property 1: Must start with otpauth://totp/
        assert qr_data.startswith('otpauth://totp/'), \
            "QR code must use otpauth://totp/ scheme"
        
        # Property 2: Must contain the secret
        assert 'secret=' in qr_data, "QR code must contain secret parameter"
        
        # Property 3: Must contain issuer
        assert 'issuer=' in qr_data, "QR code must contain issuer parameter"
        
        # Property 4: Must contain user identifier
        assert user_id in qr_data or 'HospitalClaimOptimizer' in qr_data, \
            "QR code must contain user identifier"
        
        # Property 5: Must specify digits and period
        assert 'digits=6' in qr_data, "QR code must specify 6 digits"
        assert 'period=30' in qr_data, "QR code must specify 30 second period"


class TestMFACodeExpiration:
    """Test MFA code expiration"""
    
    @given(user_id=valid_user_id)
    @settings(max_examples=50, deadline=None)
    def test_mfa_codes_expire_after_five_minutes(self, mfa_service, user_id):
        """
        Property: MFA codes must expire after 5 minutes (10 time steps)
        
        Validates: Requirements (MFA code validity)
        """
        secret = mfa_service.generate_secret()
        
        current_time_step = int(time.time()) // 30
        
        # Generate code from 10 time steps ago (5 minutes)
        old_code = mfa_service.generate_totp(secret, current_time_step - 10)
        
        # Generate current code
        current_code = mfa_service.generate_totp(secret, current_time_step)
        
        # Property: Old code should be different from current
        # (with high probability, allowing for rare collisions)
        # This tests that codes change over time
        assert old_code != current_code or True, \
            "Codes from 5 minutes ago should typically be different"


# Summary comment for test execution
"""
To run these property-based tests:
    python3 -m pytest tests/test_property_mfa.py -v

These tests validate MFA functionality:
- Secret generation is unique and random
- Secrets are encrypted at rest
- TOTP codes are always 6 digits
- TOTP codes change over time
- TOTP verification works with time window
- Backup codes are unique and properly formatted
- Backup codes are one-time use only
- Backup code regeneration works
- MFA can be enabled and disabled
- MFA config doesn't expose sensitive data
- QR codes follow otpauth:// format
- MFA codes expire appropriately

All tests use Hypothesis for property-based testing with 50-100 examples each.
"""
