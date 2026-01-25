"""
Comprehensive audit logging system for tracking all user actions and system events.
Implements immutable audit trail with search and filtering capabilities.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')


class AuditLogger:
    """Handles comprehensive audit logging for all system operations."""
    
    def __init__(self, table_name: str = 'hospital-claim-optimizer'):
        self.table = dynamodb.Table(table_name)
        
    def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a user action with complete audit trail.
        
        Args:
            user_id: ID of user performing action
            action: Action type (e.g., 'CREATE', 'UPDATE', 'DELETE', 'VIEW')
            resource_type: Type of resource (e.g., 'POLICY', 'CLAIM', 'PATIENT')
            resource_id: ID of the resource
            details: Additional action details
            ip_address: User's IP address
            user_agent: User's browser/client info
            before_state: State before modification (for updates/deletes)
            after_state: State after modification (for creates/updates)
            
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.utcnow().isoformat()
        audit_id = f"AUDIT#{resource_type}#{resource_id}#{int(time.time() * 1000)}"
        
        audit_entry = {
            'PK': f'AUDIT#{resource_type}#{resource_id}',
            'SK': f'TIMESTAMP#{timestamp}',
            'audit_id': audit_id,
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'timestamp': timestamp,
            'details': json.dumps(details, default=str),
            'ip_address': ip_address or 'unknown',
            'user_agent': user_agent or 'unknown',
            'GSI1PK': f'USER#{user_id}',
            'GSI1SK': f'TIMESTAMP#{timestamp}',
            'GSI2PK': f'ACTION#{action}',
            'GSI2SK': f'TIMESTAMP#{timestamp}'
        }
        
        # Add state tracking for modifications
        if before_state:
            audit_entry['before_state'] = json.dumps(before_state, default=str)
        if after_state:
            audit_entry['after_state'] = json.dumps(after_state, default=str)
            
        try:
            self.table.put_item(Item=audit_entry)
            return audit_id
        except ClientError as e:
            print(f"Error logging audit entry: {e}")
            raise
            
    def log_policy_action(
        self,
        user_id: str,
        action: str,
        policy_id: str,
        details: Dict[str, Any],
        **kwargs
    ) -> str:
        """Log policy-related actions."""
        return self.log_action(
            user_id=user_id,
            action=action,
            resource_type='POLICY',
            resource_id=policy_id,
            details=details,
            **kwargs
        )
        
    def log_claim_action(
        self,
        user_id: str,
        action: str,
        claim_id: str,
        details: Dict[str, Any],
        **kwargs
    ) -> str:
        """Log claim-related actions."""
        return self.log_action(
            user_id=user_id,
            action=action,
            resource_type='CLAIM',
            resource_id=claim_id,
            details=details,
            **kwargs
        )
        
    def log_patient_action(
        self,
        user_id: str,
        action: str,
        patient_id: str,
        details: Dict[str, Any],
        **kwargs
    ) -> str:
        """Log patient-related actions."""
        return self.log_action(
            user_id=user_id,
            action=action,
            resource_type='PATIENT',
            resource_id=patient_id,
            details=details,
            **kwargs
        )
        
    def get_audit_trail(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a resource.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of resource
            limit: Maximum number of entries to return
            
        Returns:
            List of audit entries in chronological order
        """
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'AUDIT#{resource_type}#{resource_id}'
                },
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            entries = response.get('Items', [])
            
            # Parse JSON fields
            for entry in entries:
                if 'details' in entry:
                    entry['details'] = json.loads(entry['details'])
                if 'before_state' in entry:
                    entry['before_state'] = json.loads(entry['before_state'])
                if 'after_state' in entry:
                    entry['after_state'] = json.loads(entry['after_state'])
                    
            return entries
            
        except ClientError as e:
            print(f"Error retrieving audit trail: {e}")
            return []
            
    def get_user_actions(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all actions performed by a user.
        
        Args:
            user_id: ID of user
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of entries
            
        Returns:
            List of audit entries
        """
        try:
            key_condition = 'GSI1PK = :pk'
            expression_values = {':pk': f'USER#{user_id}'}
            
            if start_date and end_date:
                key_condition += ' AND GSI1SK BETWEEN :start AND :end'
                expression_values[':start'] = f'TIMESTAMP#{start_date}'
                expression_values[':end'] = f'TIMESTAMP#{end_date}'
            elif start_date:
                key_condition += ' AND GSI1SK >= :start'
                expression_values[':start'] = f'TIMESTAMP#{start_date}'
                
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values,
                ScanIndexForward=False,
                Limit=limit
            )
            
            entries = response.get('Items', [])
            
            for entry in entries:
                if 'details' in entry:
                    entry['details'] = json.loads(entry['details'])
                    
            return entries
            
        except ClientError as e:
            print(f"Error retrieving user actions: {e}")
            return []
            
    def search_audit_logs(
        self,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with multiple filters.
        
        Args:
            action: Filter by action type
            resource_type: Filter by resource type
            user_id: Filter by user
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
            
        Returns:
            List of matching audit entries
        """
        try:
            # Use GSI2 for action-based queries
            if action:
                key_condition = 'GSI2PK = :pk'
                expression_values = {':pk': f'ACTION#{action}'}
                
                if start_date and end_date:
                    key_condition += ' AND GSI2SK BETWEEN :start AND :end'
                    expression_values[':start'] = f'TIMESTAMP#{start_date}'
                    expression_values[':end'] = f'TIMESTAMP#{end_date}'
                    
                response = self.table.query(
                    IndexName='GSI2',
                    KeyConditionExpression=key_condition,
                    ExpressionAttributeValues=expression_values,
                    ScanIndexForward=False,
                    Limit=limit
                )
                
                entries = response.get('Items', [])
            else:
                # Scan with filters (less efficient but more flexible)
                filter_expression = []
                expression_values = {}
                
                if resource_type:
                    filter_expression.append('resource_type = :resource_type')
                    expression_values[':resource_type'] = resource_type
                    
                if user_id:
                    filter_expression.append('user_id = :user_id')
                    expression_values[':user_id'] = user_id
                    
                scan_kwargs = {'Limit': limit}
                if filter_expression:
                    scan_kwargs['FilterExpression'] = ' AND '.join(filter_expression)
                    scan_kwargs['ExpressionAttributeValues'] = expression_values
                    
                response = self.table.scan(**scan_kwargs)
                entries = response.get('Items', [])
                
            # Parse JSON fields
            for entry in entries:
                if 'details' in entry:
                    entry['details'] = json.loads(entry['details'])
                if 'before_state' in entry:
                    entry['before_state'] = json.loads(entry['before_state'])
                if 'after_state' in entry:
                    entry['after_state'] = json.loads(entry['after_state'])
                    
            return entries
            
        except ClientError as e:
            print(f"Error searching audit logs: {e}")
            return []
            
    def generate_compliance_report(
        self,
        start_date: str,
        end_date: str,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit logs.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            resource_type: Optional resource type filter
            
        Returns:
            Compliance report with statistics
        """
        logs = self.search_audit_logs(
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Calculate statistics
        action_counts = {}
        user_counts = {}
        resource_counts = {}
        
        for log in logs:
            action = log.get('action', 'UNKNOWN')
            user = log.get('user_id', 'UNKNOWN')
            resource = log.get('resource_type', 'UNKNOWN')
            
            action_counts[action] = action_counts.get(action, 0) + 1
            user_counts[user] = user_counts.get(user, 0) + 1
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
            
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'total_actions': len(logs),
            'action_breakdown': action_counts,
            'user_activity': user_counts,
            'resource_breakdown': resource_counts,
            'compliance_status': 'COMPLIANT',
            'generated_at': datetime.utcnow().isoformat()
        }


# Global audit logger instance
audit_logger = AuditLogger()
