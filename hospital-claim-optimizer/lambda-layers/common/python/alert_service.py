"""
Alert and Notification Service
Handles alert generation, notification display, and webhook notifications
"""
import json
import os
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from data_models import RiskLevel, ClaimStatus
from database_access import DynamoDBAccessLayer
from common_utils import generate_id, get_timestamp

class AlertType(Enum):
    HIGH_RISK_CLAIM = "HIGH_RISK_CLAIM"
    LARGE_CLAIM_AMOUNT = "LARGE_CLAIM_AMOUNT"
    HIGH_REJECTION_RATE = "HIGH_REJECTION_RATE"
    POLICY_EXPIRING = "POLICY_EXPIRING"
    DOCUMENTATION_MISSING = "DOCUMENTATION_MISSING"
    SETTLEMENT_RATIO_LOW = "SETTLEMENT_RATIO_LOW"

class AlertPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AlertService:
    """Service for managing alerts and notifications"""
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
        # Initialize SNS client for notifications
        try:
            self.sns_client = boto3.client('sns', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        except Exception as e:
            print(f"Warning: Could not initialize SNS client: {str(e)}")
            self.sns_client = None
    
    def generate_alert(
        self,
        hospital_id: str,
        alert_type: str,
        priority: str,
        title: str,
        message: str,
        related_entity_id: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        action_items: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new alert
        
        Args:
            hospital_id: Hospital identifier
            alert_type: Type of alert
            priority: Alert priority
            title: Alert title
            message: Alert message
            related_entity_id: ID of related entity (claim, patient, etc.)
            related_entity_type: Type of related entity
            action_items: List of recommended actions
            metadata: Additional metadata
        
        Returns:
            Created alert
        """
        alert_id = generate_id('alert')
        
        alert = {
            'PK': f"HOSPITAL#{hospital_id}",
            'SK': f"ALERT#{alert_id}",
            'alert_id': alert_id,
            'hospital_id': hospital_id,
            'alert_type': alert_type,
            'priority': priority,
            'title': title,
            'message': message,
            'related_entity_id': related_entity_id,
            'related_entity_type': related_entity_type,
            'action_items': action_items or [],
            'metadata': metadata or {},
            'status': 'ACTIVE',
            'created_at': get_timestamp(),
            'acknowledged': False,
            'acknowledged_at': None,
            'acknowledged_by': None
        }
        
        # Store alert
        success = self.db_client.put_item(alert)
        
        if success:
            return {
                'success': True,
                'alert': alert
            }
        else:
            return {
                'success': False,
                'error': 'Failed to create alert'
            }
    
    def check_and_generate_alerts(
        self,
        hospital_id: str,
        claim_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check claim data and generate appropriate alerts
        
        Args:
            hospital_id: Hospital identifier
            claim_data: Claim data to check
        
        Returns:
            List of generated alerts
        """
        alerts = []
        
        claim_id = claim_data.get('claim_id', '')
        patient_id = claim_data.get('patient_id', '')
        
        # Check for high-risk claim
        if claim_data.get('risk_level') == RiskLevel.HIGH.value:
            alert = self.generate_alert(
                hospital_id=hospital_id,
                alert_type=AlertType.HIGH_RISK_CLAIM.value,
                priority=AlertPriority.HIGH.value,
                title=f"High Risk Claim Detected: {claim_id}",
                message=f"Claim {claim_id} has been flagged as high risk with a risk score of {claim_data.get('risk_score', 0)}.",
                related_entity_id=claim_id,
                related_entity_type='claim',
                action_items=[
                    "Review claim details and supporting documentation",
                    "Verify all policy requirements are met",
                    "Consider pre-authorization if not already obtained"
                ],
                metadata={
                    'risk_score': claim_data.get('risk_score', 0),
                    'patient_id': patient_id
                }
            )
            if alert['success']:
                alerts.append(alert['alert'])
        
        # Check for large claim amount
        total_amount = claim_data.get('total_amount', 0.0)
        if total_amount >= 200000:
            alert = self.generate_alert(
                hospital_id=hospital_id,
                alert_type=AlertType.LARGE_CLAIM_AMOUNT.value,
                priority=AlertPriority.MEDIUM.value,
                title=f"Large Claim Amount: ${total_amount:,.2f}",
                message=f"Claim {claim_id} has a total amount of ${total_amount:,.2f}, which exceeds the threshold for special review.",
                related_entity_id=claim_id,
                related_entity_type='claim',
                action_items=[
                    "Verify all line items are properly documented",
                    "Ensure pre-authorization was obtained for high-value procedures",
                    "Review policy coverage limits"
                ],
                metadata={
                    'total_amount': total_amount,
                    'patient_id': patient_id
                }
            )
            if alert['success']:
                alerts.append(alert['alert'])
        
        # Check for low settlement ratio
        settlement_ratio = claim_data.get('predicted_settlement_ratio', 1.0)
        if settlement_ratio < 0.7:
            alert = self.generate_alert(
                hospital_id=hospital_id,
                alert_type=AlertType.SETTLEMENT_RATIO_LOW.value,
                priority=AlertPriority.MEDIUM.value,
                title=f"Low Settlement Ratio: {settlement_ratio:.1%}",
                message=f"Claim {claim_id} has a predicted settlement ratio of {settlement_ratio:.1%}, indicating potential issues.",
                related_entity_id=claim_id,
                related_entity_type='claim',
                action_items=[
                    "Review rejected items and reasons",
                    "Consider AI optimization suggestions",
                    "Verify procedure coding accuracy"
                ],
                metadata={
                    'settlement_ratio': settlement_ratio,
                    'patient_id': patient_id
                }
            )
            if alert['success']:
                alerts.append(alert['alert'])
        
        # Check for missing documentation
        audit_results = claim_data.get('audit_results', {})
        review_items = audit_results.get('review_items', 0)
        if review_items > 0:
            alert = self.generate_alert(
                hospital_id=hospital_id,
                alert_type=AlertType.DOCUMENTATION_MISSING.value,
                priority=AlertPriority.LOW.value,
                title=f"Documentation Review Required: {review_items} items",
                message=f"Claim {claim_id} has {review_items} items requiring additional documentation or review.",
                related_entity_id=claim_id,
                related_entity_type='claim',
                action_items=[
                    "Gather supporting documentation for review items",
                    "Provide medical necessity justification",
                    "Submit additional evidence to support claim"
                ],
                metadata={
                    'review_items': review_items,
                    'patient_id': patient_id
                }
            )
            if alert['success']:
                alerts.append(alert['alert'])
        
        return alerts
    
    def get_alerts(
        self,
        hospital_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alerts for a hospital
        
        Args:
            hospital_id: Hospital identifier
            filters: Optional filters (status, priority, type)
            limit: Maximum number of alerts to return
        
        Returns:
            List of alerts
        """
        # Query alerts for hospital
        alerts = self.db_client.query_items(
            f"HOSPITAL#{hospital_id}",
            "ALERT#"
        )
        
        # Apply filters
        if filters:
            if 'status' in filters:
                alerts = [a for a in alerts if a.get('status') == filters['status']]
            
            if 'priority' in filters:
                priority = filters['priority']
                if isinstance(priority, list):
                    alerts = [a for a in alerts if a.get('priority') in priority]
                else:
                    alerts = [a for a in alerts if a.get('priority') == priority]
            
            if 'alert_type' in filters:
                alert_type = filters['alert_type']
                if isinstance(alert_type, list):
                    alerts = [a for a in alerts if a.get('alert_type') in alert_type]
                else:
                    alerts = [a for a in alerts if a.get('alert_type') == alert_type]
            
            if 'acknowledged' in filters:
                acknowledged = filters['acknowledged']
                alerts = [a for a in alerts if a.get('acknowledged') == acknowledged]
        
        # Sort by created_at (newest first)
        alerts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply limit
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def acknowledge_alert(
        self,
        hospital_id: str,
        alert_id: str,
        user_id: str
    ) -> bool:
        """
        Acknowledge an alert
        
        Args:
            hospital_id: Hospital identifier
            alert_id: Alert identifier
            user_id: User acknowledging the alert
        
        Returns:
            Success status
        """
        # Get alert
        alert = self.db_client.get_item(
            f"HOSPITAL#{hospital_id}",
            f"ALERT#{alert_id}"
        )
        
        if not alert:
            return False
        
        # Update alert
        alert['acknowledged'] = True
        alert['acknowledged_at'] = get_timestamp()
        alert['acknowledged_by'] = user_id
        alert['status'] = 'ACKNOWLEDGED'
        
        return self.db_client.put_item(alert)
    
    def dismiss_alert(
        self,
        hospital_id: str,
        alert_id: str,
        user_id: str
    ) -> bool:
        """
        Dismiss an alert
        
        Args:
            hospital_id: Hospital identifier
            alert_id: Alert identifier
            user_id: User dismissing the alert
        
        Returns:
            Success status
        """
        # Get alert
        alert = self.db_client.get_item(
            f"HOSPITAL#{hospital_id}",
            f"ALERT#{alert_id}"
        )
        
        if not alert:
            return False
        
        # Update alert
        alert['status'] = 'DISMISSED'
        alert['dismissed_at'] = get_timestamp()
        alert['dismissed_by'] = user_id
        
        return self.db_client.put_item(alert)

class WebhookNotificationService:
    """Service for sending webhook notifications"""
    
    def __init__(self):
        # Initialize HTTP client for webhooks
        import urllib3
        self.http = urllib3.PoolManager()
    
    def send_webhook_notification(
        self,
        webhook_url: str,
        event_type: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send webhook notification to external system
        
        Args:
            webhook_url: Webhook URL
            event_type: Type of event
            data: Event data
            headers: Optional custom headers
        
        Returns:
            Response from webhook
        """
        try:
            # Prepare payload
            payload = {
                'event_type': event_type,
                'timestamp': get_timestamp(),
                'data': data
            }
            
            # Prepare headers
            request_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'HospitalClaimOptimizer/1.0'
            }
            
            if headers:
                request_headers.update(headers)
            
            # Send request
            response = self.http.request(
                'POST',
                webhook_url,
                body=json.dumps(payload).encode('utf-8'),
                headers=request_headers,
                timeout=10.0
            )
            
            return {
                'success': response.status == 200,
                'status_code': response.status,
                'response': response.data.decode('utf-8') if response.data else None
            }
            
        except Exception as e:
            print(f"Error sending webhook notification: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_claim_audited(
        self,
        webhook_url: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification when claim is audited"""
        return self.send_webhook_notification(
            webhook_url=webhook_url,
            event_type='claim.audited',
            data={
                'claim_id': claim_data.get('claim_id'),
                'patient_id': claim_data.get('patient_id'),
                'hospital_id': claim_data.get('hospital_id'),
                'total_amount': claim_data.get('total_amount'),
                'risk_level': claim_data.get('risk_level'),
                'settlement_ratio': claim_data.get('predicted_settlement_ratio'),
                'audit_results': claim_data.get('audit_results', {})
            }
        )
    
    def notify_high_risk_claim(
        self,
        webhook_url: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification for high-risk claim"""
        return self.send_webhook_notification(
            webhook_url=webhook_url,
            event_type='claim.high_risk',
            data={
                'claim_id': claim_data.get('claim_id'),
                'patient_id': claim_data.get('patient_id'),
                'hospital_id': claim_data.get('hospital_id'),
                'risk_score': claim_data.get('risk_score'),
                'risk_level': claim_data.get('risk_level'),
                'total_amount': claim_data.get('total_amount')
            }
        )
    
    def notify_policy_uploaded(
        self,
        webhook_url: str,
        policy_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification when policy is uploaded"""
        return self.send_webhook_notification(
            webhook_url=webhook_url,
            event_type='policy.uploaded',
            data={
                'policy_id': policy_data.get('policy_id'),
                'hospital_id': policy_data.get('hospital_id'),
                'policy_name': policy_data.get('policy_name'),
                'extraction_status': policy_data.get('extraction_status')
            }
        )
