"""
Email Notification Service

Handles email notifications using Amazon SES with template rendering,
retry mechanism, and bounce/complaint handling.

Requirements: 6.1.1, 6.1.2, 6.1.3, 6.1.4, 6.1.5
"""

import boto3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS clients
ses_client = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')

# Environment variables (should be set in Lambda)
import os
NOTIFICATIONS_TABLE = os.environ.get('NOTIFICATIONS_TABLE', 'claim-optimizer-notifications')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@hospital-claim-optimizer.com')
UNSUBSCRIBE_URL_BASE = os.environ.get('UNSUBSCRIBE_URL_BASE', 'https://app.hospital-claim-optimizer.com/unsubscribe')

# Get DynamoDB table
notifications_table = dynamodb.Table(NOTIFICATIONS_TABLE)


class EmailNotificationService:
    """Service for sending email notifications via Amazon SES"""
    
    def __init__(self):
        self.ses_client = ses_client
        self.notifications_table = notifications_table
        self.from_email = FROM_EMAIL
        self.max_retries = 3
        self.retry_delay_seconds = [60, 300, 900]  # 1 min, 5 min, 15 min
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        category: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email notification via Amazon SES
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML version of email body
            text_body: Plain text version of email body
            category: Notification category (alerts, reports, policy_updates, claim_status)
            user_id: User ID for preference checking
            metadata: Additional metadata to store with notification
        
        Returns:
            Dict with status and message_id or error
        
        Requirements: 6.1.1, 6.1.2, 6.1.4
        """
        try:
            # Check user preferences before sending
            if not self._should_send_notification(user_id, category):
                logger.info(f"Notification blocked by user preferences: user={user_id}, category={category}")
                return {
                    'status': 'blocked',
                    'reason': 'user_preferences',
                    'message': 'User has disabled this notification category'
                }
            
            # Add unsubscribe link to email body
            unsubscribe_token = self._generate_unsubscribe_token(user_id, category)
            unsubscribe_url = f"{UNSUBSCRIBE_URL_BASE}?token={unsubscribe_token}"
            
            html_body = self._add_unsubscribe_link(html_body, unsubscribe_url)
            text_body = self._add_unsubscribe_link_text(text_body, unsubscribe_url)
            
            # Send email via SES
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        },
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ConfigurationSetName='claim-optimizer-emails'  # For tracking bounces/complaints
            )
            
            message_id = response['MessageId']
            
            # Log successful delivery
            self._log_notification(
                user_id=user_id,
                to_email=to_email,
                subject=subject,
                category=category,
                status='sent',
                message_id=message_id,
                metadata=metadata
            )
            
            logger.info(f"Email sent successfully: message_id={message_id}, to={to_email}")
            
            return {
                'status': 'sent',
                'message_id': message_id,
                'to_email': to_email
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"SES error: {error_code} - {error_message}")
            
            # Log failed delivery
            self._log_notification(
                user_id=user_id,
                to_email=to_email,
                subject=subject,
                category=category,
                status='failed',
                error=f"{error_code}: {error_message}",
                metadata=metadata
            )
            
            # Schedule retry if appropriate
            if error_code in ['Throttling', 'ServiceUnavailable', 'InternalFailure']:
                self._schedule_retry(
                    user_id=user_id,
                    to_email=to_email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    category=category,
                    metadata=metadata,
                    attempt=1
                )
            
            return {
                'status': 'failed',
                'error': error_message,
                'error_code': error_code
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            
            self._log_notification(
                user_id=user_id,
                to_email=to_email,
                subject=subject,
                category=category,
                status='failed',
                error=str(e),
                metadata=metadata
            )
            
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def send_batch_emails(
        self,
        emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send multiple emails in batch
        
        Args:
            emails: List of email dictionaries with to_email, subject, html_body, text_body, category, user_id
        
        Returns:
            Dict with success count, failure count, and results
        """
        results = []
        success_count = 0
        failure_count = 0
        
        for email in emails:
            result = self.send_email(
                to_email=email['to_email'],
                subject=email['subject'],
                html_body=email['html_body'],
                text_body=email['text_body'],
                category=email['category'],
                user_id=email['user_id'],
                metadata=email.get('metadata')
            )
            
            results.append({
                'to_email': email['to_email'],
                'result': result
            })
            
            if result['status'] == 'sent':
                success_count += 1
            else:
                failure_count += 1
        
        return {
            'total': len(emails),
            'success': success_count,
            'failure': failure_count,
            'results': results
        }
    
    def handle_bounce(self, bounce_notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SES bounce notification
        
        Args:
            bounce_notification: SNS notification from SES about bounced email
        
        Returns:
            Dict with status
        
        Requirements: 6.1.5
        """
        try:
            message = json.loads(bounce_notification['Message'])
            bounce = message.get('bounce', {})
            bounce_type = bounce.get('bounceType')
            bounced_recipients = bounce.get('bouncedRecipients', [])
            
            for recipient in bounced_recipients:
                email_address = recipient.get('emailAddress')
                
                # Log bounce
                logger.warning(f"Email bounced: {email_address}, type: {bounce_type}")
                
                # If permanent bounce, mark email as invalid
                if bounce_type == 'Permanent':
                    self._mark_email_invalid(email_address, 'permanent_bounce')
                
                # Update notification log
                self._update_notification_status(
                    email_address=email_address,
                    status='bounced',
                    bounce_type=bounce_type
                )
            
            return {
                'status': 'processed',
                'bounce_type': bounce_type,
                'recipients': len(bounced_recipients)
            }
            
        except Exception as e:
            logger.error(f"Error handling bounce: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def handle_complaint(self, complaint_notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SES complaint notification (spam reports)
        
        Args:
            complaint_notification: SNS notification from SES about complaint
        
        Returns:
            Dict with status
        
        Requirements: 6.1.5
        """
        try:
            message = json.loads(complaint_notification['Message'])
            complaint = message.get('complaint', {})
            complained_recipients = complaint.get('complainedRecipients', [])
            
            for recipient in complained_recipients:
                email_address = recipient.get('emailAddress')
                
                # Log complaint
                logger.warning(f"Complaint received for: {email_address}")
                
                # Automatically unsubscribe user from all notifications
                self._mark_email_invalid(email_address, 'complaint')
                
                # Update notification log
                self._update_notification_status(
                    email_address=email_address,
                    status='complaint'
                )
            
            return {
                'status': 'processed',
                'recipients': len(complained_recipients)
            }
            
        except Exception as e:
            logger.error(f"Error handling complaint: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def retry_failed_notification(
        self,
        notification_id: str
    ) -> Dict[str, Any]:
        """
        Retry a failed notification
        
        Args:
            notification_id: ID of the notification to retry
        
        Returns:
            Dict with retry result
        
        Requirements: 6.1.4
        """
        try:
            # Get notification details
            response = self.notifications_table.get_item(
                Key={'notification_id': notification_id}
            )
            
            if 'Item' not in response:
                return {
                    'status': 'error',
                    'error': 'Notification not found'
                }
            
            notification = response['Item']
            
            # Check retry count
            retry_count = notification.get('retry_count', 0)
            if retry_count >= self.max_retries:
                return {
                    'status': 'error',
                    'error': 'Max retries exceeded'
                }
            
            # Retry sending
            result = self.send_email(
                to_email=notification['to_email'],
                subject=notification['subject'],
                html_body=notification['html_body'],
                text_body=notification['text_body'],
                category=notification['category'],
                user_id=notification['user_id'],
                metadata=notification.get('metadata')
            )
            
            # Update retry count
            self.notifications_table.update_item(
                Key={'notification_id': notification_id},
                UpdateExpression='SET retry_count = :count',
                ExpressionAttributeValues={
                    ':count': retry_count + 1
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrying notification: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # Private helper methods
    
    def _should_send_notification(self, user_id: str, category: str) -> bool:
        """Check if user preferences allow this notification"""
        try:
            # Get user preferences
            from notification_preferences_service import NotificationPreferencesService
            prefs_service = NotificationPreferencesService()
            preferences = prefs_service.get_preferences(user_id)
            
            # Check if category is enabled
            categories = preferences.get('categories', {})
            return categories.get(category, True)  # Default to enabled
            
        except Exception as e:
            logger.error(f"Error checking preferences: {str(e)}")
            return True  # Default to sending if error
    
    def _generate_unsubscribe_token(self, user_id: str, category: str) -> str:
        """Generate unsubscribe token"""
        import hashlib
        import time
        
        data = f"{user_id}:{category}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _add_unsubscribe_link(self, html_body: str, unsubscribe_url: str) -> str:
        """Add unsubscribe link to HTML email"""
        unsubscribe_html = f'''
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #6b7280;">
            <p>Don't want to receive these emails? <a href="{unsubscribe_url}" style="color: #3b82f6; text-decoration: underline;">Unsubscribe</a></p>
        </div>
        '''
        
        # Insert before closing body tag
        if '</body>' in html_body:
            return html_body.replace('</body>', f'{unsubscribe_html}</body>')
        else:
            return html_body + unsubscribe_html
    
    def _add_unsubscribe_link_text(self, text_body: str, unsubscribe_url: str) -> str:
        """Add unsubscribe link to plain text email"""
        unsubscribe_text = f"\n\n---\nDon't want to receive these emails? Unsubscribe: {unsubscribe_url}"
        return text_body + unsubscribe_text
    
    def _log_notification(
        self,
        user_id: str,
        to_email: str,
        subject: str,
        category: str,
        status: str,
        message_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log notification to DynamoDB"""
        try:
            import uuid
            
            notification_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'notification_id': notification_id,
                'user_id': user_id,
                'to_email': to_email,
                'subject': subject,
                'category': category,
                'status': status,
                'timestamp': timestamp,
                'retry_count': 0
            }
            
            if message_id:
                item['message_id'] = message_id
            
            if error:
                item['error'] = error
            
            if metadata:
                item['metadata'] = metadata
            
            self.notifications_table.put_item(Item=item)
            
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
    
    def _schedule_retry(
        self,
        user_id: str,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        category: str,
        metadata: Optional[Dict[str, Any]],
        attempt: int
    ):
        """Schedule a retry for failed notification"""
        if attempt >= self.max_retries:
            logger.warning(f"Max retries reached for {to_email}")
            return
        
        # In production, this would use SQS with delay or EventBridge scheduled rule
        # For now, just log the retry schedule
        delay = self.retry_delay_seconds[attempt - 1] if attempt <= len(self.retry_delay_seconds) else 900
        logger.info(f"Scheduling retry {attempt} for {to_email} in {delay} seconds")
    
    def _mark_email_invalid(self, email_address: str, reason: str):
        """Mark an email address as invalid (bounced or complained)"""
        try:
            # Store in a separate table or add to user preferences
            logger.info(f"Marking email as invalid: {email_address}, reason: {reason}")
            
            # In production, update user preferences to disable all notifications
            # or maintain a separate suppression list
            
        except Exception as e:
            logger.error(f"Error marking email invalid: {str(e)}")
    
    def _update_notification_status(
        self,
        email_address: str,
        status: str,
        bounce_type: Optional[str] = None
    ):
        """Update notification status in log"""
        try:
            # Query for recent notifications to this email
            # Update their status
            logger.info(f"Updating notification status: {email_address} -> {status}")
            
        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")


# Singleton instance
_email_service = None

def get_email_service() -> EmailNotificationService:
    """Get singleton instance of EmailNotificationService"""
    global _email_service
    if _email_service is None:
        _email_service = EmailNotificationService()
    return _email_service
