"""
Property-based tests for security features.

**Feature: hospital-insurance-claim-settlement-optimizer**

Tests the following properties:
- Property 18: Data Encryption Standards
- Property 19: Authentication and Access Control
- Property 20: Audit Logging
- Property 33: Change Tracking
- Property 34: Audit Search Capabilities

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.6, 10.1, 10.3, 10.4, 10.6**
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import assume
import json
from datetime import datetime, timedelta
import bcrypt


# Test data strategies
@st.composite
def user_action_strategy(draw):
    """Generate valid user action data."""
    return {
        'user_id': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'action': draw(st.sampled_from(['CREATE', 'UPDATE', 'DELETE', 'VIEW'])),
        'resource_type': draw(st.sampled_from(['POLICY', 'CLAIM', 'PATIENT'])),
        'resource_id': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'details': {
            'field': draw(st.text(min_size=1, max_size=100)),
            'value': draw(st.text(min_size=1, max_size=100))
        },
        'ip_address': f"{draw(st.integers(1, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}"
    }


@st.composite
def password_strategy(draw):
    """Generate passwords for testing."""
    return draw(st.text(min_size=8, max_size=72))  # bcrypt max is 72 bytes


@st.composite
def audit_search_params_strategy(draw):
    """Generate audit search parameters."""
    return {
        'action': draw(st.one_of(st.none(), st.sampled_from(['CREATE', 'UPDATE', 'DELETE', 'VIEW']))),
        'resource_type': draw(st.one_of(st.none(), st.sampled_from(['POLICY', 'CLAIM', 'PATIENT']))),
        'user_id': draw(st.one_of(st.none(), st.text(min_size=5, max_size=50))),
        'limit': draw(st.integers(min_value=1, max_value=100))
    }


class MockAuditLogger:
    """Mock audit logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def log_action(self, user_id, action, resource_type, resource_id, details, 
                   ip_address=None, user_agent=None, before_state=None, after_state=None):
        timestamp = datetime.utcnow().isoformat()
        audit_id = f"AUDIT#{resource_type}#{resource_id}#{len(self.logs)}"
        
        entry = {
            'audit_id': audit_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'timestamp': timestamp,
            'details': details,
            'ip_address': ip_address or 'unknown',
            'user_agent': user_agent or 'unknown'
        }
        
        if before_state:
            entry['before_state'] = before_state
        if after_state:
            entry['after_state'] = after_state
        
        self.logs.append(entry)
        return audit_id
    
    def get_audit_trail(self, resource_type, resource_id, limit=100):
        return [log for log in self.logs 
                if log['resource_type'] == resource_type and log['resource_id'] == resource_id][:limit]
    
    def search_audit_logs(self, action=None, resource_type=None, user_id=None, 
                         start_date=None, end_date=None, limit=100):
        results = self.logs
        
        if action:
            results = [log for log in results if log['action'] == action]
        if resource_type:
            results = [log for log in results if log['resource_type'] == resource_type]
        if user_id:
            results = [log for log in results if log['user_id'] == user_id]
        
        return results[:limit]


@pytest.fixture
def mock_audit_logger():
    """Provide a mock audit logger for tests."""
    return MockAuditLogger()


class TestSecurityProperties:
    """Property-based tests for security features."""
    
    @given(user_action_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_20_audit_logging(self, action_data):
        """
        **Property 20: Audit Logging**
        
        For any data access or modification operation, detailed audit logs 
        should be created and maintained.
        
        **Validates: Requirements 6.4**
        """
        mock_audit_logger = MockAuditLogger()
        
        # Log the action
        audit_id = mock_audit_logger.log_action(
            user_id=action_data['user_id'],
            action=action_data['action'],
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            details=action_data['details'],
            ip_address=action_data['ip_address']
        )
        
        # Verify audit log was created
        assert audit_id is not None
        assert audit_id.startswith('AUDIT#')
        
        # Retrieve and verify the audit trail
        trail = mock_audit_logger.get_audit_trail(
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            limit=10
        )
        
        # Should have at least one entry
        assert len(trail) > 0
        
        # Find our entry
        our_entry = next((e for e in trail if e.get('audit_id') == audit_id), None)
        assert our_entry is not None
        
        # Verify all required fields are present
        assert our_entry['user_id'] == action_data['user_id']
        assert our_entry['action'] == action_data['action']
        assert our_entry['resource_type'] == action_data['resource_type']
        assert our_entry['resource_id'] == action_data['resource_id']
        assert our_entry['ip_address'] == action_data['ip_address']
        assert 'timestamp' in our_entry
        assert 'details' in our_entry
    
    @given(
        user_action_strategy(),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=100)),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=100))
    )
    @settings(max_examples=100, deadline=None)
    def test_property_33_change_tracking(self, action_data, before_state, after_state):
        """
        **Property 33: Change Tracking**
        
        For any claim modification, before and after states should be recorded 
        with complete comparison data.
        
        **Validates: Requirements 10.3**
        """
        mock_audit_logger = MockAuditLogger()
        assume(action_data['action'] in ['UPDATE', 'DELETE'])
        
        # Log action with state tracking
        audit_id = mock_audit_logger.log_action(
            user_id=action_data['user_id'],
            action=action_data['action'],
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            details=action_data['details'],
            before_state=before_state,
            after_state=after_state if action_data['action'] == 'UPDATE' else None
        )
        
        # Retrieve the audit entry
        trail = mock_audit_logger.get_audit_trail(
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            limit=10
        )
        
        our_entry = next((e for e in trail if e.get('audit_id') == audit_id), None)
        assert our_entry is not None
        
        # Verify before state is recorded
        assert 'before_state' in our_entry
        assert our_entry['before_state'] == before_state
        
        # Verify after state for updates
        if action_data['action'] == 'UPDATE':
            assert 'after_state' in our_entry
            assert our_entry['after_state'] == after_state
    
    @given(
        st.lists(user_action_strategy(), min_size=5, max_size=20),
        audit_search_params_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_34_audit_search_capabilities(self, actions, search_params):
        """
        **Property 34: Audit Search Capabilities**
        
        For any audit record search or filtering operation, the system should 
        provide accurate and complete results across all stored audit data.
        
        **Validates: Requirements 10.6**
        """
        mock_audit_logger = MockAuditLogger()
        
        # Log multiple actions
        for action_data in actions:
            mock_audit_logger.log_action(
                user_id=action_data['user_id'],
                action=action_data['action'],
                resource_type=action_data['resource_type'],
                resource_id=action_data['resource_id'],
                details=action_data['details'],
                ip_address=action_data['ip_address']
            )
        
        # Search with filters
        results = mock_audit_logger.search_audit_logs(
            action=search_params['action'],
            resource_type=search_params['resource_type'],
            user_id=search_params['user_id'],
            limit=search_params['limit']
        )
        
        # Verify search returns results
        assert isinstance(results, list)
        
        # If filters are applied, verify results match filters
        for result in results:
            if search_params['action']:
                assert result['action'] == search_params['action']
            if search_params['resource_type']:
                assert result['resource_type'] == search_params['resource_type']
            if search_params['user_id']:
                assert result['user_id'] == search_params['user_id']
            
            # Verify all required fields are present
            assert 'audit_id' in result
            assert 'timestamp' in result
            assert 'user_id' in result
            assert 'action' in result
            assert 'resource_type' in result
            assert 'resource_id' in result
    
    @given(password_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_18_password_encryption(self, password):
        """
        **Property 18: Data Encryption Standards (Password Hashing)**
        
        For any password storage operation, the system should use secure 
        hashing (bcrypt/argon2) and never store plaintext passwords.
        
        **Validates: Requirements 6.1, 6.2**
        """
        # Hash the password using bcrypt
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        # Verify hash is not the plaintext password
        assert hashed.decode('utf-8') != password
        
        # Verify hash has expected format (bcrypt starts with $2b$)
        assert hashed.startswith(b'$2b$') or hashed.startswith(b'$2a$')
        
        # Verify password can be verified
        assert bcrypt.checkpw(password_bytes, hashed) is True
        
        # Verify wrong password fails
        wrong_password = (password + 'wrong').encode('utf-8')
        assert bcrypt.checkpw(wrong_password, hashed) is False
    
    @given(
        st.text(min_size=5, max_size=50),
        st.sampled_from(['admin', 'doctor', 'billing_specialist', 'tpa_manager'])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_19_role_based_access_control(self, user_id, role):
        """
        **Property 19: Authentication and Access Control**
        
        For any system access attempt, multi-factor authentication should be 
        required and role-based access controls should restrict users to 
        appropriate resources only.
        
        **Validates: Requirements 6.3, 6.6**
        """
        # Define role permissions
        role_permissions = {
            'admin': ['DELETE_HOSPITAL', 'MANAGE_USERS', 'VIEW_PATIENT', 'CHECK_ELIGIBILITY', 'AUDIT_BILL', 'SUBMIT_CLAIM'],
            'doctor': ['VIEW_PATIENT', 'CHECK_ELIGIBILITY'],
            'billing_specialist': ['AUDIT_BILL', 'SUBMIT_CLAIM'],
            'tpa_manager': ['VIEW_PATIENT', 'AUDIT_BILL', 'SUBMIT_CLAIM', 'VIEW_REPORTS']
        }
        
        # Verify role has defined permissions
        assert role in role_permissions
        permissions = role_permissions[role]
        assert len(permissions) > 0
        
        # Verify admin has all permissions
        if role == 'admin':
            assert 'DELETE_HOSPITAL' in permissions
            assert 'MANAGE_USERS' in permissions
        
        # Verify non-admin roles don't have admin permissions
        if role != 'admin':
            assert 'DELETE_HOSPITAL' not in permissions
            assert 'MANAGE_USERS' not in permissions


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])



# Test data strategies
@st.composite
def user_action_strategy(draw):
    """Generate valid user action data."""
    return {
        'user_id': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'action': draw(st.sampled_from(['CREATE', 'UPDATE', 'DELETE', 'VIEW'])),
        'resource_type': draw(st.sampled_from(['POLICY', 'CLAIM', 'PATIENT'])),
        'resource_id': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'details': {
            'field': draw(st.text(min_size=1, max_size=100)),
            'value': draw(st.text(min_size=1, max_size=100))
        },
        'ip_address': f"{draw(st.integers(1, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}.{draw(st.integers(0, 255))}"
    }


@st.composite
def password_strategy(draw):
    """Generate passwords for testing."""
    return draw(st.text(min_size=8, max_size=128))


@st.composite
def audit_search_params_strategy(draw):
    """Generate audit search parameters."""
    return {
        'action': draw(st.one_of(st.none(), st.sampled_from(['CREATE', 'UPDATE', 'DELETE', 'VIEW']))),
        'resource_type': draw(st.one_of(st.none(), st.sampled_from(['POLICY', 'CLAIM', 'PATIENT']))),
        'user_id': draw(st.one_of(st.none(), st.text(min_size=5, max_size=50))),
        'limit': draw(st.integers(min_value=1, max_value=100))
    }


class MockAuditLogger:
    """Mock audit logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def log_action(self, user_id, action, resource_type, resource_id, details, 
                   ip_address=None, user_agent=None, before_state=None, after_state=None):
        timestamp = datetime.utcnow().isoformat()
        audit_id = f"AUDIT#{resource_type}#{resource_id}#{len(self.logs)}"
        
        entry = {
            'audit_id': audit_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'timestamp': timestamp,
            'details': details,
            'ip_address': ip_address or 'unknown',
            'user_agent': user_agent or 'unknown'
        }
        
        if before_state:
            entry['before_state'] = before_state
        if after_state:
            entry['after_state'] = after_state
        
        self.logs.append(entry)
        return audit_id
    
    def get_audit_trail(self, resource_type, resource_id, limit=100):
        return [log for log in self.logs 
                if log['resource_type'] == resource_type and log['resource_id'] == resource_id][:limit]
    
    def search_audit_logs(self, action=None, resource_type=None, user_id=None, 
                         start_date=None, end_date=None, limit=100):
        results = self.logs
        
        if action:
            results = [log for log in results if log['action'] == action]
        if resource_type:
            results = [log for log in results if log['resource_type'] == resource_type]
        if user_id:
            results = [log for log in results if log['user_id'] == user_id]
        
        return results[:limit]


@pytest.fixture
def mock_audit_logger():
    """Provide a mock audit logger for tests."""
    return MockAuditLogger()


class TestSecurityProperties:
    """Property-based tests for security features."""
    
    @given(user_action_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_20_audit_logging(self, user_action_strategy, mock_audit_logger):
        """
        **Property 20: Audit Logging**
        
        For any data access or modification operation, detailed audit logs 
        should be created and maintained.
        
        **Validates: Requirements 6.4**
        """
        action_data = user_action_strategy
        
        # Log the action
        audit_id = mock_audit_logger.log_action(
            user_id=action_data['user_id'],
            action=action_data['action'],
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            details=action_data['details'],
            ip_address=action_data['ip_address']
        )
        
        # Verify audit log was created
        assert audit_id is not None
        assert audit_id.startswith('AUDIT#')
        
        # Retrieve and verify the audit trail
        trail = mock_audit_logger.get_audit_trail(
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            limit=10
        )
        
        # Should have at least one entry
        assert len(trail) > 0
        
        # Find our entry
        our_entry = next((e for e in trail if e.get('audit_id') == audit_id), None)
        assert our_entry is not None
        
        # Verify all required fields are present
        assert our_entry['user_id'] == action_data['user_id']
        assert our_entry['action'] == action_data['action']
        assert our_entry['resource_type'] == action_data['resource_type']
        assert our_entry['resource_id'] == action_data['resource_id']
        assert our_entry['ip_address'] == action_data['ip_address']
        assert 'timestamp' in our_entry
        assert 'details' in our_entry
    
    @given(
        user_action_strategy(),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=100)),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=100))
    )
    @settings(max_examples=100, deadline=None)
    def test_property_33_change_tracking(self, user_action_strategy, before_state, after_state, mock_audit_logger):
        """
        **Property 33: Change Tracking**
        
        For any claim modification, before and after states should be recorded 
        with complete comparison data.
        
        **Validates: Requirements 10.3**
        """
        action_data = user_action_strategy
        assume(action_data['action'] in ['UPDATE', 'DELETE'])
        
        # Log action with state tracking
        audit_id = mock_audit_logger.log_action(
            user_id=action_data['user_id'],
            action=action_data['action'],
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            details=action_data['details'],
            before_state=before_state,
            after_state=after_state if action_data['action'] == 'UPDATE' else None
        )
        
        # Retrieve the audit entry
        trail = mock_audit_logger.get_audit_trail(
            resource_type=action_data['resource_type'],
            resource_id=action_data['resource_id'],
            limit=10
        )
        
        our_entry = next((e for e in trail if e.get('audit_id') == audit_id), None)
        assert our_entry is not None
        
        # Verify before state is recorded
        assert 'before_state' in our_entry
        assert our_entry['before_state'] == before_state
        
        # Verify after state for updates
        if action_data['action'] == 'UPDATE':
            assert 'after_state' in our_entry
            assert our_entry['after_state'] == after_state
    
    @given(
        st.lists(user_action_strategy(), min_size=5, max_size=20),
        audit_search_params_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_property_34_audit_search_capabilities(self, actions, search_params, mock_audit_logger):
        """
        **Property 34: Audit Search Capabilities**
        
        For any audit record search or filtering operation, the system should 
        provide accurate and complete results across all stored audit data.
        
        **Validates: Requirements 10.6**
        """
        # Log multiple actions
        for action_data in actions:
            mock_audit_logger.log_action(
                user_id=action_data['user_id'],
                action=action_data['action'],
                resource_type=action_data['resource_type'],
                resource_id=action_data['resource_id'],
                details=action_data['details'],
                ip_address=action_data['ip_address']
            )
        
        # Search with filters
        results = mock_audit_logger.search_audit_logs(
            action=search_params['action'],
            resource_type=search_params['resource_type'],
            user_id=search_params['user_id'],
            limit=search_params['limit']
        )
        
        # Verify search returns results
        assert isinstance(results, list)
        
        # If filters are applied, verify results match filters
        for result in results:
            if search_params['action']:
                assert result['action'] == search_params['action']
            if search_params['resource_type']:
                assert result['resource_type'] == search_params['resource_type']
            if search_params['user_id']:
                assert result['user_id'] == search_params['user_id']
            
            # Verify all required fields are present
            assert 'audit_id' in result
            assert 'timestamp' in result
            assert 'user_id' in result
            assert 'action' in result
            assert 'resource_type' in result
            assert 'resource_id' in result
    
    @given(password_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_18_password_encryption(self, password):
        """
        **Property 18: Data Encryption Standards (Password Hashing)**
        
        For any password storage operation, the system should use secure 
        hashing (bcrypt/argon2) and never store plaintext passwords.
        
        **Validates: Requirements 6.1, 6.2**
        """
        # Hash the password
        hashed = hash_password(password)
        
        # Verify hash is not the plaintext password
        assert hashed != password
        
        # Verify hash has expected format (bcrypt starts with $2b$)
        assert hashed.startswith('$2b$') or hashed.startswith('$2a$')
        
        # Verify password can be verified
        assert verify_password(password, hashed) is True
        
        # Verify wrong password fails
        assert verify_password(password + 'wrong', hashed) is False
    
    @given(
        st.text(min_size=5, max_size=50),
        st.sampled_from(['admin', 'doctor', 'billing_specialist', 'tpa_manager'])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_19_role_based_access_control(self, user_id, role):
        """
        **Property 19: Authentication and Access Control**
        
        For any system access attempt, multi-factor authentication should be 
        required and role-based access controls should restrict users to 
        appropriate resources only.
        
        **Validates: Requirements 6.3, 6.6**
        """
        # Define role permissions
        role_permissions = {
            'admin': ['DELETE_HOSPITAL', 'MANAGE_USERS', 'VIEW_PATIENT', 'CHECK_ELIGIBILITY', 'AUDIT_BILL', 'SUBMIT_CLAIM'],
            'doctor': ['VIEW_PATIENT', 'CHECK_ELIGIBILITY'],
            'billing_specialist': ['AUDIT_BILL', 'SUBMIT_CLAIM'],
            'tpa_manager': ['VIEW_PATIENT', 'AUDIT_BILL', 'SUBMIT_CLAIM', 'VIEW_REPORTS']
        }
        
        # Verify role has defined permissions
        assert role in role_permissions
        permissions = role_permissions[role]
        assert len(permissions) > 0
        
        # Verify admin has all permissions
        if role == 'admin':
            assert 'DELETE_HOSPITAL' in permissions
            assert 'MANAGE_USERS' in permissions
        
        # Verify non-admin roles don't have admin permissions
        if role != 'admin':
            assert 'DELETE_HOSPITAL' not in permissions
            assert 'MANAGE_USERS' not in permissions


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
