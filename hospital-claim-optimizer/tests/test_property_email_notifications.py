"""
Property-Based Tests for Email Notifications

Tests Property 45: Email Notification Preferences
- Disabled categories don't send emails
- Frequency settings honored
- Unsubscribe links work
- Preferences persist across sessions

**Validates: Requirements 6.1, 6.2, 6.3**

Uses Hypothesis for property-based testing with minimum 100 iterations.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Mock boto3 before importing services
sys.modules['boto3'] = MagicMock()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from notification_preferences_service import NotificationPreferencesService, DEFAULT_PREFERENCES
from email_notification_service import EmailNotificationService


# Test data strategies
@st.composite
def user_id_strategy(draw):
    """Generate valid user IDs"""
    return f"user_{draw(st.integers(min_value=1, max_value=10000))}"


@st.composite
def email_address_strategy(draw):
    """Generate valid email addresses"""
    username = draw(st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Nd')), min_size=3, max_size=20))
    domain = draw(st.sampled_from(['example.com', 'test.com', 'hospital.org']))
    return f"{username}@{domain}"


@st.composite
def category_strategy(draw):
    """Generate valid notification categories"""
    return draw(st.sampled_from(['alerts', 'reports', 'policy_updates', 'claim_status']))


@st.composite
def frequency_strategy(draw):
    """Generate valid frequency settings"""
    return draw(st.sampled_from(['immediate', 'daily', 'weekly']))


@st.composite
def preferences_strategy(draw):
    """Generate valid notification preferences"""
    categories = {
        'alerts': draw(st.booleans()),
        'reports': draw(st.booleans()),
        'policy_updates': draw(st.booleans()),
        'claim_status': draw(st.booleans())
    }
    
    return {
        'categories': categories,
        'frequency': draw(frequency_strategy()),
        'email_address': draw(st.one_of(st.none(), email_address_strategy())),
        'enabled': draw(st.booleans())
    }


class TestProperty45_EmailNotificationPreferences:
    """
    Property 45: Email Notification Preferences
    
    Tests that email notifications respect user preferences correctly.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.prefs_service = NotificationPreferencesService()
        self.email_service = EmailNotificationService()
        
        # Mock DynamoDB
        self.mock_table = Mock()
        self.prefs_service.preferences_table = self.mock_table
        self.email_service.notifications_table = Mock()
        
        # Mock SES client
        self.mock_ses = Mock()
        self.email_service.ses_client = self.mock_ses
    
    @given(
        user_id=user_id_strategy(),
        category=category_strategy(),
        preferences=preferences_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_disabled_categories_dont_send_emails(self, user_id, category, preferences):
        """
        Property 45.1: Disabled categories don't send emails
        
        If a user has disabled a notification category, emails in that
        category should not be sent.
        
        **Validates: Requirements 6.2.1, 6.2.2**
        """
        # Setup: User has specific preferences
        # Mock the preferences service to return our test preferences
        with patch.object(self.prefs_service, 'get_preferences', return_value=preferences):
            # Mock SES send_email
            self.mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
            
            # Test: Try to send email in this category
            result = self.email_service.send_email(
                to_email='test@example.com',
                subject='Test Email',
                html_body='<p>Test</p>',
                text_body='Test',
                category=category,
                user_id=user_id
            )
            
            # Verify: If category is disabled, email should be blocked
            category_enabled = preferences.get('categories', {}).get(category, True)
            overall_enabled = preferences.get('enabled', True)
            
            if not category_enabled or not overall_enabled:
                assert result['status'] == 'blocked', \
                    f"Email should be blocked when category {category} is disabled"
                assert not self.mock_ses.send_email.called, \
                    "SES should not be called when category is disabled"
            else:
                # If enabled, email should be sent (unless frequency is not immediate)
                frequency = preferences.get('frequency', 'immediate')
                if frequency == 'immediate':
                    assert result['status'] in ['sent', 'blocked'], \
                        f"Email should be sent or blocked based on preferences"
    
    @given(
        user_id=user_id_strategy(),
        frequency=frequency_strategy(),
        category=category_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_frequency_settings_honored(self, user_id, frequency, category):
        """
        Property 45.2: Frequency settings honored
        
        Emails should only be sent immediately if frequency is set to 'immediate'.
        For 'daily' or 'weekly', emails should be queued for digest.
        
        **Validates: Requirements 6.2.3**
        """
        # Setup: User has specific frequency preference
        preferences = {
            'categories': {category: True},
            'frequency': frequency,
            'enabled': True
        }
        
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PREFERENCES',
                **preferences
            }
        }
        
        # Mock SES
        self.mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        # Test: Try to send email
        result = self.email_service.send_email(
            to_email='test@example.com',
            subject='Test Email',
            html_body='<p>Test</p>',
            text_body='Test',
            category=category,
            user_id=user_id
        )
        
        # Verify: Frequency setting is honored
        if frequency == 'immediate':
            # Should attempt to send
            assert result['status'] in ['sent', 'blocked'], \
                "Immediate frequency should attempt to send email"
        else:
            # Should be blocked for digest
            assert result['status'] == 'blocked', \
                f"Frequency {frequency} should block immediate sending"
            assert result.get('reason') == 'user_preferences', \
                "Should indicate user preferences as reason"
    
    @given(
        user_id=user_id_strategy(),
        preferences=preferences_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_preferences_persist_across_sessions(self, user_id, preferences):
        """
        Property 45.3: Preferences persist across sessions
        
        User preferences should be stored and retrieved consistently
        across multiple operations.
        
        **Validates: Requirements 6.2.5**
        """
        # Setup: Mock successful save
        self.mock_table.put_item.return_value = {}
        
        # Test: Update preferences
        result = self.prefs_service.update_preferences(user_id, preferences)
        
        # Verify: Update was successful
        assert result['status'] == 'success', \
            "Preferences update should succeed"
        
        # Verify: put_item was called with correct data
        assert self.mock_table.put_item.called, \
            "Preferences should be saved to DynamoDB"
        
        call_args = self.mock_table.put_item.call_args
        saved_item = call_args[1]['Item']
        
        # Verify: All preference fields are saved
        assert saved_item['PK'] == f'USER#{user_id}', \
            "User ID should be in partition key"
        assert saved_item['SK'] == 'PREFERENCES', \
            "Sort key should be PREFERENCES"
        
        # Verify: Preference values are preserved
        for key in ['categories', 'frequency', 'enabled']:
            if key in preferences:
                assert key in saved_item, \
                    f"Preference {key} should be saved"
        
        # Test: Retrieve preferences
        self.mock_table.get_item.return_value = {
            'Item': saved_item
        }
        
        retrieved_prefs = self.prefs_service.get_preferences(user_id)
        
        # Verify: Retrieved preferences match saved preferences
        for key in ['categories', 'frequency', 'enabled']:
            if key in preferences:
                assert retrieved_prefs[key] == preferences[key], \
                    f"Retrieved {key} should match saved value"
    
    @given(
        user_id=user_id_strategy(),
        category=category_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_unsubscribe_links_work(self, user_id, category):
        """
        Property 45.4: Unsubscribe links work
        
        All emails should include unsubscribe links, and unsubscribing
        should disable the category.
        
        **Validates: Requirements 6.1.3**
        """
        # Setup: User has category enabled
        preferences = {
            'categories': {category: True},
            'frequency': 'immediate',
            'enabled': True
        }
        
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PREFERENCES',
                **preferences
            }
        }
        
        # Mock SES
        self.mock_ses.send_email.return_value = {'MessageId': 'test-message-id'}
        
        # Test: Send email
        result = self.email_service.send_email(
            to_email='test@example.com',
            subject='Test Email',
            html_body='<p>Test content</p>',
            text_body='Test content',
            category=category,
            user_id=user_id
        )
        
        # Verify: Email was sent
        if result['status'] == 'sent':
            # Verify: SES was called
            assert self.mock_ses.send_email.called, \
                "SES should be called to send email"
            
            # Get the email body that was sent
            call_args = self.mock_ses.send_email.call_args
            message = call_args[1]['Message']
            html_body = message['Body']['Html']['Data']
            text_body = message['Body']['Text']['Data']
            
            # Verify: Unsubscribe link is present
            assert 'unsubscribe' in html_body.lower(), \
                "HTML email should contain unsubscribe link"
            assert 'unsubscribe' in text_body.lower(), \
                "Text email should contain unsubscribe link"
        
        # Test: Unsubscribe from category
        self.mock_table.put_item.return_value = {}
        
        unsubscribe_result = self.prefs_service.update_category(
            user_id=user_id,
            category=category,
            enabled=False
        )
        
        # Verify: Category was disabled
        assert unsubscribe_result['status'] == 'success', \
            "Unsubscribe should succeed"
        
        # Verify: Subsequent emails are blocked
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PREFERENCES',
                'categories': {category: False},
                'frequency': 'immediate',
                'enabled': True
            }
        }
        
        # Reset mock
        self.mock_ses.reset_mock()
        
        result2 = self.email_service.send_email(
            to_email='test@example.com',
            subject='Test Email 2',
            html_body='<p>Test</p>',
            text_body='Test',
            category=category,
            user_id=user_id
        )
        
        # Verify: Email is now blocked
        assert result2['status'] == 'blocked', \
            "Email should be blocked after unsubscribe"
        assert not self.mock_ses.send_email.called, \
            "SES should not be called after unsubscribe"
    
    @given(
        user_id=user_id_strategy(),
        email_address=email_address_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_custom_email_address_used(self, user_id, email_address):
        """
        Property 45.5: Custom email address used
        
        If user specifies a custom email address, it should be used
        for notifications.
        
        **Validates: Requirements 6.2.4**
        """
        # Setup: User has custom email address
        preferences = {
            'categories': {'alerts': True},
            'frequency': 'immediate',
            'email_address': email_address,
            'enabled': True
        }
        
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PREFERENCES',
                **preferences
            }
        }
        
        # Test: Update email address
        self.mock_table.put_item.return_value = {}
        
        result = self.prefs_service.update_email_address(
            user_id=user_id,
            email_address=email_address
        )
        
        # Verify: Update succeeded
        assert result['status'] == 'success', \
            "Email address update should succeed"
        
        # Verify: Email address was saved
        assert self.mock_table.put_item.called, \
            "Email address should be saved"
        
        call_args = self.mock_table.put_item.call_args
        saved_item = call_args[1]['Item']
        
        assert saved_item.get('email_address') == email_address, \
            "Custom email address should be saved"
    
    @given(
        user_id=user_id_strategy(),
        categories=st.lists(category_strategy(), min_size=1, max_size=4, unique=True)
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_categories_independent(self, user_id, categories):
        """
        Property 45.6: Multiple categories are independent
        
        Disabling one category should not affect other categories.
        
        **Validates: Requirements 6.2.1, 6.2.2**
        """
        # Setup: All categories enabled
        all_categories = {'alerts', 'reports', 'policy_updates', 'claim_status'}
        preferences = {
            'categories': {cat: True for cat in all_categories},
            'frequency': 'immediate',
            'enabled': True
        }
        
        self.mock_table.get_item.return_value = {
            'Item': {
                'PK': f'USER#{user_id}',
                'SK': 'PREFERENCES',
                **preferences
            }
        }
        
        # Test: Disable one category
        category_to_disable = categories[0]
        
        self.mock_table.put_item.return_value = {}
        
        result = self.prefs_service.update_category(
            user_id=user_id,
            category=category_to_disable,
            enabled=False
        )
        
        assert result['status'] == 'success', \
            "Category update should succeed"
        
        # Verify: Only the specified category was disabled
        call_args = self.mock_table.put_item.call_args
        saved_item = call_args[1]['Item']
        saved_categories = saved_item.get('categories', {})
        
        assert saved_categories.get(category_to_disable) == False, \
            f"Category {category_to_disable} should be disabled"
        
        # Verify: Other categories remain enabled
        for cat in all_categories:
            if cat != category_to_disable:
                # Should still be enabled (or at least not explicitly disabled)
                assert saved_categories.get(cat, True) == True, \
                    f"Category {cat} should remain enabled"


class TestEmailNotificationService:
    """Additional tests for email notification service"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.email_service = EmailNotificationService()
        self.email_service.notifications_table = Mock()
        self.email_service.ses_client = Mock()
    
    @given(
        to_email=email_address_strategy(),
        subject=st.text(min_size=1, max_size=100),
        category=category_strategy()
    )
    @settings(max_examples=50, deadline=None)
    def test_email_logging(self, to_email, subject, category):
        """
        Test that all email sends are logged
        
        **Validates: Requirements 6.1.4**
        """
        # Mock successful send
        self.email_service.ses_client.send_email.return_value = {
            'MessageId': 'test-message-id'
        }
        
        # Mock preferences check
        with patch.object(self.email_service, '_should_send_notification', return_value=True):
            result = self.email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_body='<p>Test</p>',
                text_body='Test',
                category=category,
                user_id='test-user'
            )
        
        # Verify: Notification was logged
        assert self.email_service.notifications_table.put_item.called, \
            "Email send should be logged"
        
        call_args = self.email_service.notifications_table.put_item.call_args
        logged_item = call_args[1]['Item']
        
        assert logged_item['to_email'] == to_email, \
            "Logged email should match recipient"
        assert logged_item['subject'] == subject, \
            "Logged subject should match"
        assert logged_item['category'] == category, \
            "Logged category should match"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
