"""
Version Rollback Service Module
Handles policy version rollback operations with audit trail
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from data_models import Policy, AuditTrail
from policy_service import PolicyService, PolicyVersioningError
from database_access import DynamoDBAccessLayer
from common_utils import generate_id, get_timestamp


@dataclass
class RollbackResult:
    """Represents the result of a rollback operation"""
    success: bool
    policy_id: str
    from_version: int
    to_version: int
    new_version_number: int
    rollback_reason: str
    rollback_by: str
    rollback_timestamp: str
    affected_users: list
    error_message: Optional[str] = None


class VersionRollbackService:
    """Service for rolling back policy versions"""
    
    def __init__(
        self,
        policy_service: PolicyService,
        db_client: DynamoDBAccessLayer
    ):
        self.policy_service = policy_service
        self.db_client = db_client
    
    def rollback_to_version(
        self,
        hospital_id: str,
        policy_id: str,
        target_version: int,
        rollback_reason: str,
        rollback_by: str
    ) -> RollbackResult:
        """
        Rollback policy to a previous version
        
        This creates a new version with the content of the target version,
        rather than deleting history.
        
        Args:
            hospital_id: Hospital identifier
            policy_id: Policy identifier
            target_version: Version number to rollback to
            rollback_reason: Reason for rollback
            rollback_by: User performing rollback
            
        Returns:
            RollbackResult with operation details
        """
        try:
            # Get current policy
            current_policy = self.policy_service.get_policy(hospital_id, policy_id)
            if not current_policy:
                return RollbackResult(
                    success=False,
                    policy_id=policy_id,
                    from_version=0,
                    to_version=target_version,
                    new_version_number=0,
                    rollback_reason=rollback_reason,
                    rollback_by=rollback_by,
                    rollback_timestamp=get_timestamp(),
                    affected_users=[],
                    error_message=f"Policy {policy_id} not found"
                )
            
            current_version = current_policy.version
            
            # Validate rollback
            validation_error = self._validate_rollback(
                current_version,
                target_version
            )
            if validation_error:
                return RollbackResult(
                    success=False,
                    policy_id=policy_id,
                    from_version=current_version,
                    to_version=target_version,
                    new_version_number=current_version,
                    rollback_reason=rollback_reason,
                    rollback_by=rollback_by,
                    rollback_timestamp=get_timestamp(),
                    affected_users=[],
                    error_message=validation_error
                )
            
            # Get target version data
            target_policy = self._get_version_data(policy_id, target_version)
            if not target_policy:
                return RollbackResult(
                    success=False,
                    policy_id=policy_id,
                    from_version=current_version,
                    to_version=target_version,
                    new_version_number=current_version,
                    rollback_reason=rollback_reason,
                    rollback_by=rollback_by,
                    rollback_timestamp=get_timestamp(),
                    affected_users=[],
                    error_message=f"Version {target_version} not found in history"
                )
            
            # Create new version with target version's data
            new_version = current_version + 1
            
            updates = {
                'extracted_rules': target_policy.get('extracted_rules', {}),
                'raw_text': target_policy.get('raw_text', ''),
                'extraction_confidence': target_policy.get('extraction_confidence', 0.0),
                'effective_date': target_policy.get('effective_date'),
                'expiration_date': target_policy.get('expiration_date'),
                'rollback_info': {
                    'is_rollback': True,
                    'from_version': current_version,
                    'to_version': target_version,
                    'reason': rollback_reason,
                    'rollback_by': rollback_by,
                    'rollback_at': get_timestamp()
                }
            }
            
            # Update policy
            updated_policy = self.policy_service.update_policy(
                policy_id,
                hospital_id,
                updates,
                rollback_by
            )
            
            # Create audit trail entry
            self._create_rollback_audit_trail(
                policy_id=policy_id,
                from_version=current_version,
                to_version=target_version,
                new_version=new_version,
                reason=rollback_reason,
                user_id=rollback_by
            )
            
            # Get affected users
            affected_users = self._get_affected_users(hospital_id, policy_id)
            
            # Notify affected users
            self._notify_affected_users(
                hospital_id,
                policy_id,
                affected_users,
                current_version,
                target_version,
                rollback_reason
            )
            
            return RollbackResult(
                success=True,
                policy_id=policy_id,
                from_version=current_version,
                to_version=target_version,
                new_version_number=new_version,
                rollback_reason=rollback_reason,
                rollback_by=rollback_by,
                rollback_timestamp=get_timestamp(),
                affected_users=affected_users
            )
            
        except Exception as e:
            return RollbackResult(
                success=False,
                policy_id=policy_id,
                from_version=0,
                to_version=target_version,
                new_version_number=0,
                rollback_reason=rollback_reason,
                rollback_by=rollback_by,
                rollback_timestamp=get_timestamp(),
                affected_users=[],
                error_message=f"Rollback failed: {str(e)}"
            )
    
    def _validate_rollback(
        self,
        current_version: int,
        target_version: int
    ) -> Optional[str]:
        """
        Validate rollback operation
        
        Returns error message if invalid, None if valid
        """
        if target_version >= current_version:
            return f"Cannot rollback to version {target_version} - must be earlier than current version {current_version}"
        
        if target_version < 1:
            return f"Invalid target version {target_version} - must be >= 1"
        
        return None
    
    def _get_version_data(
        self,
        policy_id: str,
        version: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific version from audit trail
        """
        audit_trail = self.policy_service.get_policy_audit_trail(policy_id)
        
        # Find the audit entry for this version
        for entry in audit_trail:
            if entry.get('action') in ['CREATE_POLICY', 'UPDATE_POLICY']:
                entry_version = entry.get('changes', {}).get('version')
                if entry_version == version:
                    # Return the after_state which contains the policy data
                    return entry.get('after_state', {})
        
        return None
    
    def _get_affected_users(
        self,
        hospital_id: str,
        policy_id: str
    ) -> list:
        """
        Get list of users who should be notified about rollback
        """
        affected_users = []
        
        # Get all users who have active claims with this policy
        items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "CLAIM#")
        
        user_ids = set()
        for item in items:
            if (item.get('policy_id') == policy_id and
                item.get('status') in ['PENDING', 'IN_REVIEW', 'SUBMITTED']):
                user_id = item.get('created_by') or item.get('user_id')
                if user_id:
                    user_ids.add(user_id)
        
        # Get hospital admins
        admin_items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "USER#")
        for item in admin_items:
            if item.get('role') in ['admin', 'tpa_admin']:
                user_ids.add(item.get('user_id'))
        
        return list(user_ids)
    
    def _notify_affected_users(
        self,
        hospital_id: str,
        policy_id: str,
        user_ids: list,
        from_version: int,
        to_version: int,
        reason: str
    ) -> None:
        """
        Send notifications to affected users about rollback
        """
        # Create notification entries in DynamoDB
        for user_id in user_ids:
            notification_id = generate_id('notif')
            
            notification = {
                'PK': f"USER#{user_id}",
                'SK': f"NOTIFICATION#{notification_id}",
                'notification_id': notification_id,
                'type': 'POLICY_ROLLBACK',
                'policy_id': policy_id,
                'hospital_id': hospital_id,
                'message': f"Policy rolled back from version {from_version} to {to_version}",
                'reason': reason,
                'from_version': from_version,
                'to_version': to_version,
                'created_at': get_timestamp(),
                'read': False,
                'priority': 'high'
            }
            
            self.db_client.put_item(notification)
    
    def _create_rollback_audit_trail(
        self,
        policy_id: str,
        from_version: int,
        to_version: int,
        new_version: int,
        reason: str,
        user_id: str
    ) -> None:
        """
        Create audit trail entry for rollback operation
        """
        audit_id = generate_id('audit')
        
        audit = AuditTrail(
            audit_id=audit_id,
            entity_id=policy_id,
            action="ROLLBACK_POLICY",
            user_id=user_id,
            changes={
                'from_version': from_version,
                'to_version': to_version,
                'new_version': new_version,
                'reason': reason,
                'rollback_timestamp': get_timestamp()
            },
            before_state={'version': from_version},
            after_state={'version': new_version, 'rolled_back_to': to_version}
        )
        
        audit_item = audit.to_dynamodb_item()
        self.db_client.put_item(audit_item)
    
    def get_rollback_history(
        self,
        policy_id: str
    ) -> list:
        """
        Get history of all rollback operations for a policy
        """
        audit_trail = self.policy_service.get_policy_audit_trail(policy_id)
        
        rollback_history = []
        for entry in audit_trail:
            if entry.get('action') == 'ROLLBACK_POLICY':
                rollback_history.append({
                    'audit_id': entry.get('audit_id'),
                    'from_version': entry.get('changes', {}).get('from_version'),
                    'to_version': entry.get('changes', {}).get('to_version'),
                    'new_version': entry.get('changes', {}).get('new_version'),
                    'reason': entry.get('changes', {}).get('reason'),
                    'rollback_by': entry.get('user_id'),
                    'rollback_at': entry.get('created_at')
                })
        
        return sorted(rollback_history, key=lambda x: x['rollback_at'], reverse=True)
    
    def can_rollback(
        self,
        hospital_id: str,
        policy_id: str,
        target_version: int
    ) -> Dict[str, Any]:
        """
        Check if rollback is possible and safe
        
        Returns:
            Dict with 'can_rollback' boolean and 'reasons' list
        """
        current_policy = self.policy_service.get_policy(hospital_id, policy_id)
        
        if not current_policy:
            return {
                'can_rollback': False,
                'reasons': ['Policy not found']
            }
        
        current_version = current_policy.version
        reasons = []
        
        # Check version validity
        validation_error = self._validate_rollback(current_version, target_version)
        if validation_error:
            reasons.append(validation_error)
        
        # Check if target version exists
        target_data = self._get_version_data(policy_id, target_version)
        if not target_data:
            reasons.append(f"Version {target_version} not found in history")
        
        # Check for active claims
        items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "CLAIM#")
        active_claims = sum(
            1 for item in items
            if item.get('policy_id') == policy_id and
            item.get('status') in ['PENDING', 'IN_REVIEW', 'SUBMITTED']
        )
        
        if active_claims > 0:
            reasons.append(
                f"Warning: {active_claims} active claims will be affected by this rollback"
            )
        
        can_rollback = len([r for r in reasons if not r.startswith('Warning:')]) == 0
        
        return {
            'can_rollback': can_rollback,
            'reasons': reasons,
            'active_claims_affected': active_claims,
            'current_version': current_version,
            'target_version': target_version
        }
