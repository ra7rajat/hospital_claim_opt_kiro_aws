"""
Policy Service Module
Handles policy storage, versioning, search, and retrieval operations
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from data_models import Policy, AuditTrail
from database_access import DynamoDBAccessLayer
from common_utils import generate_id, get_timestamp

class PolicyVersioningError(Exception):
    """Raised when policy versioning operations fail"""
    pass

class PolicyService:
    """Service class for policy management operations"""
    
    def __init__(self, dynamodb_client: DynamoDBAccessLayer):
        self.db_client = dynamodb_client
    
    def create_policy(
        self, 
        hospital_id: str, 
        policy_name: str, 
        file_size: int,
        content_type: str,
        s3_key: str,
        created_by: str
    ) -> Policy:
        """
        Create a new policy with version 1
        """
        policy_id = generate_id('pol')
        
        policy = Policy(
            policy_id=policy_id,
            hospital_id=hospital_id,
            policy_name=policy_name,
            file_size=file_size,
            content_type=content_type,
            s3_key=s3_key,
            version=1
        )
        
        # Store policy in DynamoDB
        policy_item = policy.to_dynamodb_item()
        policy_item['created_by'] = created_by
        
        success = self.db_client.put_item(policy_item)
        if not success:
            raise PolicyVersioningError("Failed to create policy")
        
        # Create audit trail for policy creation
        self._create_audit_trail(
            policy_id=policy_id,
            action="CREATE_POLICY",
            user_id=created_by,
            changes={
                "policy_name": policy_name,
                "version": 1,
                "status": "created"
            }
        )
        
        return policy
    
    def update_policy(
        self, 
        policy_id: str, 
        hospital_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Policy:
        """
        Update an existing policy and increment version
        """
        # Get current policy
        current_policy = self.get_policy(hospital_id, policy_id)
        if not current_policy:
            raise PolicyVersioningError(f"Policy {policy_id} not found")
        
        # Create updated policy with incremented version
        new_version = current_policy.version + 1
        
        # Apply updates
        updated_data = {
            'policy_id': current_policy.policy_id,
            'hospital_id': current_policy.hospital_id,
            'policy_name': current_policy.policy_name,
            'file_size': current_policy.file_size,
            'content_type': current_policy.content_type,
            's3_key': current_policy.s3_key,
            'extraction_status': current_policy.extraction_status,
            'extracted_rules': current_policy.extracted_rules,
            'raw_text': current_policy.raw_text,
            'extraction_confidence': current_policy.extraction_confidence,
            'version': new_version,
            'effective_date': current_policy.effective_date,
            'expiration_date': current_policy.expiration_date,
            'error_message': current_policy.error_message
        }
        
        # Apply the updates
        updated_data.update(updates)
        
        # Create new policy instance
        updated_policy = Policy(**updated_data)
        
        # Store updated policy
        policy_item = updated_policy.to_dynamodb_item()
        policy_item['updated_by'] = updated_by
        
        success = self.db_client.put_item(policy_item)
        if not success:
            raise PolicyVersioningError("Failed to update policy")
        
        # Create audit trail for policy update
        self._create_audit_trail(
            policy_id=policy_id,
            action="UPDATE_POLICY",
            user_id=updated_by,
            changes=updates,
            before_state=asdict(current_policy),
            after_state=asdict(updated_policy)
        )
        
        return updated_policy
    
    def get_policy(self, hospital_id: str, policy_id: str) -> Optional[Policy]:
        """
        Retrieve a policy by hospital_id and policy_id
        """
        item = self.db_client.get_item(f"HOSPITAL#{hospital_id}", f"POLICY#{policy_id}")
        if not item:
            return None
        
        # Convert DynamoDB item back to Policy object
        return self._item_to_policy(item)
    
    def get_policy_versions(self, hospital_id: str, policy_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a policy
        """
        # In this implementation, we store only the current version
        # For full version history, you'd need a separate table or GSI
        current_policy = self.get_policy(hospital_id, policy_id)
        if not current_policy:
            return []
        
        # Get audit trail to reconstruct version history
        audit_trail = self.get_policy_audit_trail(policy_id)
        
        versions = []
        for audit_entry in audit_trail:
            if audit_entry.get('action') in ['CREATE_POLICY', 'UPDATE_POLICY']:
                version_info = {
                    'version': audit_entry.get('changes', {}).get('version', 1),
                    'timestamp': audit_entry.get('created_at'),
                    'updated_by': audit_entry.get('user_id'),
                    'changes': audit_entry.get('changes', {}),
                    'action': audit_entry.get('action')
                }
                versions.append(version_info)
        
        return sorted(versions, key=lambda x: x['version'])
    
    def search_policies(
        self, 
        hospital_id: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Policy]:
        """
        Search policies for a hospital with optional filters
        """
        # Query all policies for the hospital
        items = self.db_client.query_items(f"HOSPITAL#{hospital_id}", "POLICY#")
        
        policies = []
        for item in items:
            policy = self._item_to_policy(item)
            if policy and self._matches_filters(policy, filters):
                policies.append(policy)
        
        return policies
    
    def search_policies_by_name(self, hospital_id: str, policy_name_pattern: str) -> List[Policy]:
        """
        Search policies by name pattern
        """
        all_policies = self.search_policies(hospital_id)
        
        matching_policies = []
        pattern_lower = policy_name_pattern.lower()
        
        for policy in all_policies:
            if pattern_lower in policy.policy_name.lower():
                matching_policies.append(policy)
        
        return matching_policies
    
    def get_policies_by_status(self, hospital_id: str, status: str) -> List[Policy]:
        """
        Get policies filtered by extraction status
        """
        filters = {'extraction_status': status}
        return self.search_policies(hospital_id, filters)
    
    def delete_policy(self, hospital_id: str, policy_id: str, deleted_by: str) -> bool:
        """
        Soft delete a policy (mark as deleted, don't actually remove)
        """
        # Get current policy
        current_policy = self.get_policy(hospital_id, policy_id)
        if not current_policy:
            return False
        
        # Update policy to mark as deleted
        updates = {
            'extraction_status': 'DELETED',
            'deleted_at': get_timestamp(),
            'deleted_by': deleted_by
        }
        
        try:
            self.update_policy(policy_id, hospital_id, updates, deleted_by)
            
            # Create audit trail for deletion
            self._create_audit_trail(
                policy_id=policy_id,
                action="DELETE_POLICY",
                user_id=deleted_by,
                changes={'status': 'deleted'}
            )
            
            return True
        except PolicyVersioningError:
            return False
    
    def get_policy_audit_trail(self, policy_id: str) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a policy
        """
        items = self.db_client.query_items(f"AUDIT#{policy_id}")
        
        audit_entries = []
        for item in items:
            audit_entries.append(item)
        
        # Sort by timestamp (newest first)
        return sorted(audit_entries, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def get_policy_statistics(self, hospital_id: str) -> Dict[str, Any]:
        """
        Get statistics about policies for a hospital
        """
        all_policies = self.search_policies(hospital_id)
        
        stats = {
            'total_policies': len(all_policies),
            'by_status': {},
            'by_version': {},
            'total_file_size': 0,
            'average_confidence': 0.0,
            'latest_upload': None
        }
        
        if not all_policies:
            return stats
        
        # Calculate statistics
        confidence_scores = []
        latest_timestamp = None
        
        for policy in all_policies:
            # Count by status
            status = policy.extraction_status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Count by version
            version = policy.version
            stats['by_version'][version] = stats['by_version'].get(version, 0) + 1
            
            # Sum file sizes
            stats['total_file_size'] += policy.file_size
            
            # Collect confidence scores
            if policy.extraction_confidence > 0:
                confidence_scores.append(policy.extraction_confidence)
            
            # Track latest upload
            if not latest_timestamp or policy.created_at > latest_timestamp:
                latest_timestamp = policy.created_at
                stats['latest_upload'] = {
                    'policy_id': policy.policy_id,
                    'policy_name': policy.policy_name,
                    'created_at': policy.created_at
                }
        
        # Calculate average confidence
        if confidence_scores:
            stats['average_confidence'] = sum(confidence_scores) / len(confidence_scores)
        
        return stats
    
    def _item_to_policy(self, item: Dict[str, Any]) -> Optional[Policy]:
        """
        Convert DynamoDB item to Policy object
        """
        try:
            # Extract policy fields from item
            policy_data = {
                'policy_id': item.get('policy_id'),
                'hospital_id': item.get('hospital_id'),
                'policy_name': item.get('policy_name'),
                'file_size': item.get('file_size', 0),
                'content_type': item.get('content_type', 'application/pdf'),
                's3_key': item.get('s3_key'),
                'extraction_status': item.get('extraction_status', 'PENDING_UPLOAD'),
                'extracted_rules': item.get('extracted_rules', {}),
                'raw_text': item.get('raw_text', ''),
                'extraction_confidence': item.get('extraction_confidence', 0.0),
                'version': item.get('version', 1),
                'effective_date': item.get('effective_date'),
                'expiration_date': item.get('expiration_date'),
                'error_message': item.get('error_message', '')
            }
            
            # Create Policy instance
            policy = Policy(**policy_data)
            
            # Set computed fields
            policy.pk = item.get('PK', f"HOSPITAL#{policy_data['hospital_id']}")
            policy.sk = item.get('SK', f"POLICY#{policy_data['policy_id']}")
            policy.entity_type = item.get('entity_type', 'POLICY')
            policy.created_at = item.get('created_at', get_timestamp())
            policy.updated_at = item.get('updated_at', get_timestamp())
            
            return policy
            
        except Exception as e:
            print(f"Error converting item to policy: {str(e)}")
            return None
    
    def _matches_filters(self, policy: Policy, filters: Optional[Dict[str, Any]]) -> bool:
        """
        Check if policy matches the given filters
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            policy_value = getattr(policy, key, None)
            
            if key == 'extraction_status' and policy_value != value:
                return False
            elif key == 'version' and policy_value != value:
                return False
            elif key == 'min_confidence' and policy.extraction_confidence < value:
                return False
            elif key == 'max_file_size' and policy.file_size > value:
                return False
            elif key == 'created_after' and policy.created_at < value:
                return False
            elif key == 'created_before' and policy.created_at > value:
                return False
        
        return True
    
    def _create_audit_trail(
        self,
        policy_id: str,
        action: str,
        user_id: str,
        changes: Dict[str, Any],
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create audit trail entry for policy operations
        """
        audit_id = generate_id('audit')
        
        audit = AuditTrail(
            audit_id=audit_id,
            entity_id=policy_id,
            action=action,
            user_id=user_id,
            changes=changes,
            before_state=before_state or {},
            after_state=after_state or {}
        )
        
        audit_item = audit.to_dynamodb_item()
        self.db_client.put_item(audit_item)

class PolicySearchService:
    """Advanced search service for policies"""
    
    def __init__(self, policy_service: PolicyService):
        self.policy_service = policy_service
    
    def advanced_search(
        self,
        hospital_id: str,
        search_criteria: Dict[str, Any]
    ) -> List[Policy]:
        """
        Perform advanced search with multiple criteria
        """
        # Start with all policies
        policies = self.policy_service.search_policies(hospital_id)
        
        # Apply search criteria
        if 'policy_name' in search_criteria:
            name_pattern = search_criteria['policy_name'].lower()
            policies = [p for p in policies if name_pattern in p.policy_name.lower()]
        
        if 'extraction_status' in search_criteria:
            status = search_criteria['extraction_status']
            policies = [p for p in policies if p.extraction_status == status]
        
        if 'min_confidence' in search_criteria:
            min_conf = search_criteria['min_confidence']
            policies = [p for p in policies if p.extraction_confidence >= min_conf]
        
        if 'version' in search_criteria:
            version = search_criteria['version']
            policies = [p for p in policies if p.version == version]
        
        if 'date_range' in search_criteria:
            date_range = search_criteria['date_range']
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            
            if start_date:
                policies = [p for p in policies if p.created_at >= start_date]
            if end_date:
                policies = [p for p in policies if p.created_at <= end_date]
        
        # Sort results
        sort_by = search_criteria.get('sort_by', 'created_at')
        sort_order = search_criteria.get('sort_order', 'desc')
        
        reverse = sort_order == 'desc'
        
        if sort_by == 'created_at':
            policies.sort(key=lambda p: p.created_at, reverse=reverse)
        elif sort_by == 'policy_name':
            policies.sort(key=lambda p: p.policy_name.lower(), reverse=reverse)
        elif sort_by == 'version':
            policies.sort(key=lambda p: p.version, reverse=reverse)
        elif sort_by == 'confidence':
            policies.sort(key=lambda p: p.extraction_confidence, reverse=reverse)
        
        # Apply pagination
        limit = search_criteria.get('limit')
        offset = search_criteria.get('offset', 0)
        
        if limit:
            policies = policies[offset:offset + limit]
        
        return policies
    
    def search_by_extracted_rules(
        self,
        hospital_id: str,
        rule_criteria: Dict[str, Any]
    ) -> List[Policy]:
        """
        Search policies by their extracted rules content
        """
        policies = self.policy_service.search_policies(hospital_id)
        matching_policies = []
        
        for policy in policies:
            if self._matches_rule_criteria(policy.extracted_rules, rule_criteria):
                matching_policies.append(policy)
        
        return matching_policies
    
    def _matches_rule_criteria(
        self,
        extracted_rules: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> bool:
        """
        Check if extracted rules match the search criteria
        """
        if 'room_rent_cap' in criteria:
            room_rent = extracted_rules.get('room_rent_cap', {})
            if criteria['room_rent_cap'].get('type') and room_rent.get('type') != criteria['room_rent_cap']['type']:
                return False
        
        if 'has_copay' in criteria:
            copay_conditions = extracted_rules.get('copay_conditions', [])
            has_copay = len(copay_conditions) > 0
            if criteria['has_copay'] != has_copay:
                return False
        
        if 'exclusion_count' in criteria:
            exclusions = extracted_rules.get('procedure_exclusions', [])
            if len(exclusions) < criteria['exclusion_count']:
                return False
        
        return True