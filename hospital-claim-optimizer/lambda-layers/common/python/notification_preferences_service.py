"""
Notification Preferences Service

Manages user notification preferences including categories, frequency,
and email address settings.

Requirements: 6.2.1, 6.2.2, 6.2.3, 6.2.4, 6.2.5
"""

import boto3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
import os
PREFERENCES_TABLE = os.environ.get('PREFERENCES_TABLE', 'claim-optimizer-notification-preferences')

# Get DynamoDB table
preferences_table = dynamodb.Table(PREFERENCES_TABLE)

# Default preferences
DEFAULT_PREFERENCES = {
    'categories': {
        'alerts': True,
        'reports': True,
        'policy_updates': True,
        'claim_status': True
    },
    'frequency': 'immediate',  # immediate, daily, weekly
    'email_address': None,  # Use account email by default
    'enabled': True
}


class NotificationPreferencesService:
    """Service for managing user notification preferences"""
    
    def __init__(self):
        self.preferences_table = preferences_table
        self.default_preferences = DEFAULT_PREFERENCES.copy()
    
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification preferences for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with user preferences or defaults
        
        Requirements: 6.2.1, 6.2.2, 6.2.3, 6.2.4
        """
        try:
            response = self.preferences_table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': 'PREFERENCES'
                }
            )
            
            if 'Item' in response:
                preferences = response['Item']
                
                # Convert Decimal to int/float for JSON serialization
                preferences = self._convert_decimals(preferences)
                
                # Ensure all default keys exist
                for key, value in self.default_preferences.items():
                    if key not in preferences:
                        preferences[key] = value
                
                logger.info(f"Retrieved preferences for user: {user_id}")
                return preferences
            else:
                # Return defaults if no preferences found
                logger.info(f"No preferences found for user {user_id}, returning defaults")
                return self.default_preferences.copy()
        
        except Exception as e:
            logger.error(f"Error getting preferences: {str(e)}")
            return self.default_preferences.copy()
    
    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update notification preferences for a user
        
        Args:
            user_id: User ID
            preferences: Dict with preference updates
        
        Returns:
            Dict with updated preferences
        
        Requirements: 6.2.1, 6.2.2, 6.2.3, 6.2.4, 6.2.5
        """
        try:
            # Get current preferences
            current_prefs = self.get_preferences(user_id)
            
            # Merge with updates
            updated_prefs = {**current_prefs, **preferences}
            
            # Validate preferences
            validation_result = self._validate_preferences(updated_prefs)
            if not validation_result['valid']:
                return {
                    'status': 'error',
                    'error': validation_result['error']
                }
            
            # Add metadata
            updated_prefs['user_id'] = user_id
            updated_prefs['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to DynamoDB
            self.preferences_table.put_item(
                Item={
                    'PK': f'USER#{user_id}',
                    'SK': 'PREFERENCES',
                    **updated_prefs
                }
            )
            
            logger.info(f"Updated preferences for user: {user_id}")
            
            return {
                'status': 'success',
                'preferences': self._convert_decimals(updated_prefs)
            }
        
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_category(
        self,
        user_id: str,
        category: str,
        enabled: bool
    ) -> Dict[str, Any]:
        """
        Enable or disable a specific notification category
        
        Args:
            user_id: User ID
            category: Category name (alerts, reports, policy_updates, claim_status)
            enabled: True to enable, False to disable
        
        Returns:
            Dict with status
        
        Requirements: 6.2.1, 6.2.2
        """
        try:
            # Validate category
            valid_categories = ['alerts', 'reports', 'policy_updates', 'claim_status']
            if category not in valid_categories:
                return {
                    'status': 'error',
                    'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
                }
            
            # Get current preferences
            current_prefs = self.get_preferences(user_id)
            
            # Update category
            if 'categories' not in current_prefs:
                current_prefs['categories'] = {}
            
            current_prefs['categories'][category] = enabled
            
            # Save
            result = self.update_preferences(user_id, current_prefs)
            
            logger.info(f"Updated category {category} to {enabled} for user: {user_id}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating category: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_frequency(
        self,
        user_id: str,
        frequency: str
    ) -> Dict[str, Any]:
        """
        Update notification frequency
        
        Args:
            user_id: User ID
            frequency: Frequency setting (immediate, daily, weekly)
        
        Returns:
            Dict with status
        
        Requirements: 6.2.3
        """
        try:
            # Validate frequency
            valid_frequencies = ['immediate', 'daily', 'weekly']
            if frequency not in valid_frequencies:
                return {
                    'status': 'error',
                    'error': f'Invalid frequency. Must be one of: {", ".join(valid_frequencies)}'
                }
            
            # Get current preferences
            current_prefs = self.get_preferences(user_id)
            
            # Update frequency
            current_prefs['frequency'] = frequency
            
            # Save
            result = self.update_preferences(user_id, current_prefs)
            
            logger.info(f"Updated frequency to {frequency} for user: {user_id}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating frequency: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_email_address(
        self,
        user_id: str,
        email_address: Optional[str]
    ) -> Dict[str, Any]:
        """
        Update notification email address
        
        Args:
            user_id: User ID
            email_address: Email address or None to use account email
        
        Returns:
            Dict with status
        
        Requirements: 6.2.4
        """
        try:
            # Validate email if provided
            if email_address:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email_address):
                    return {
                        'status': 'error',
                        'error': 'Invalid email address format'
                    }
            
            # Get current preferences
            current_prefs = self.get_preferences(user_id)
            
            # Update email address
            current_prefs['email_address'] = email_address
            
            # Save
            result = self.update_preferences(user_id, current_prefs)
            
            logger.info(f"Updated email address for user: {user_id}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating email address: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_users_for_digest(
        self,
        frequency: str
    ) -> List[str]:
        """
        Get list of user IDs who should receive digest emails
        
        Args:
            frequency: Digest frequency (daily, weekly)
        
        Returns:
            List of user IDs
        
        Requirements: 6.2.3
        """
        try:
            # Query users with this frequency setting
            # In production, this would use a GSI on frequency
            
            # For now, scan table (not efficient for large datasets)
            response = self.preferences_table.scan(
                FilterExpression='frequency = :freq AND enabled = :enabled',
                ExpressionAttributeValues={
                    ':freq': frequency,
                    ':enabled': True
                }
            )
            
            user_ids = []
            for item in response.get('Items', []):
                pk = item.get('PK', '')
                if pk.startswith('USER#'):
                    user_id = pk.replace('USER#', '')
                    user_ids.append(user_id)
            
            logger.info(f"Found {len(user_ids)} users for {frequency} digest")
            
            return user_ids
        
        except Exception as e:
            logger.error(f"Error getting users for digest: {str(e)}")
            return []
    
    def get_pending_notifications(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending notifications for a user (for digest generation)
        
        Args:
            user_id: User ID
            since: Get notifications since this timestamp
        
        Returns:
            List of pending notifications
        
        Requirements: 6.2.3
        """
        try:
            if since is None:
                # Default to last 24 hours for daily digest
                since = datetime.utcnow() - timedelta(days=1)
            
            # Query notifications table for pending notifications
            # This would integrate with the email notification service
            
            # For now, return empty list (would be implemented with actual notification queue)
            logger.info(f"Getting pending notifications for user: {user_id} since {since}")
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting pending notifications: {str(e)}")
            return []
    
    def should_send_notification(
        self,
        user_id: str,
        category: str
    ) -> bool:
        """
        Check if a notification should be sent based on user preferences
        
        Args:
            user_id: User ID
            category: Notification category
        
        Returns:
            True if notification should be sent, False otherwise
        
        Requirements: 6.2.1, 6.2.2
        """
        try:
            preferences = self.get_preferences(user_id)
            
            # Check if notifications are enabled
            if not preferences.get('enabled', True):
                return False
            
            # Check if category is enabled
            categories = preferences.get('categories', {})
            if not categories.get(category, True):
                return False
            
            # Check frequency
            frequency = preferences.get('frequency', 'immediate')
            if frequency != 'immediate':
                # For daily/weekly, notifications are queued for digest
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking if should send notification: {str(e)}")
            return True  # Default to sending if error
    
    # Private helper methods
    
    def _validate_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate preference values"""
        try:
            # Validate frequency
            if 'frequency' in preferences:
                valid_frequencies = ['immediate', 'daily', 'weekly']
                if preferences['frequency'] not in valid_frequencies:
                    return {
                        'valid': False,
                        'error': f'Invalid frequency. Must be one of: {", ".join(valid_frequencies)}'
                    }
            
            # Validate categories
            if 'categories' in preferences:
                valid_categories = ['alerts', 'reports', 'policy_updates', 'claim_status']
                for category in preferences['categories'].keys():
                    if category not in valid_categories:
                        return {
                            'valid': False,
                            'error': f'Invalid category: {category}'
                        }
            
            # Validate email address
            if 'email_address' in preferences and preferences['email_address']:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, preferences['email_address']):
                    return {
                        'valid': False,
                        'error': 'Invalid email address format'
                    }
            
            return {'valid': True}
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to int/float for JSON serialization"""
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj


# Singleton instance
_preferences_service = None

def get_preferences_service() -> NotificationPreferencesService:
    """Get singleton instance of NotificationPreferencesService"""
    global _preferences_service
    if _preferences_service is None:
        _preferences_service = NotificationPreferencesService()
    return _preferences_service
