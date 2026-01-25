"""
Audit Service Module
Handles audit result storage, retrieval, and history tracking
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import asdict

from data_models import Claim, ClaimItem, AuditTrail
from database_access import DynamoDBAccessLayer
from common_utils import generate_id, get_timestamp

class AuditResultsService:
    """Service for managing audit results and history"""
    
    def __init__(self, db_client: DynamoDBAccessLayer):
        self.db_client = db_client
    
    def store_audit_result(
        self,
        claim: Claim,
        claim_items: List[ClaimItem],
        user_id: str
    ) -> bool:
        """
        Store complete audit result including claim and all items
        
        Args:
            claim: Claim entity with audit results
            claim_items: List of claim items
            user_id: User who performed the audit
        
        Returns:
            Success status
        """
        try:
            # Store claim
            claim_item = claim.to_dynamodb_item()
            claim_item['audited_by'] = user_id
            
            success = self.db_client.put_item(claim_item)
            if not success:
                return False
            
            # Store all claim items
            for item in claim_items:
                item_data = item.to_dynamodb_item()
                success = self.db_client.put_item(item_data)
                if not success:
                    return False
            
            # Create audit trail
            self._create_audit_trail(
                claim_id=claim.claim_id,
                action="AUDIT_COMPLETED",
                user_id=user_id,
                changes={
                    'status': claim.status,
                    'total_amount': claim.total_amount,
                    'predicted_settlement_ratio': claim.predicted_settlement_ratio,
                    'audit_results': claim.audit_results
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing audit result: {str(e)}")
            return False
    
    def get_audit_result(
        self,
        claim_id: str,
        patient_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete audit result for a claim
        
        Args:
            claim_id: Claim identifier
            patient_id: Patient identifier
        
        Returns:
            Complete audit result with claim and items
        """
        try:
            # Get claim
            claim_data = self.db_client.get_item(
                f"PATIENT#{patient_id}",
                f"CLAIM#{claim_id}"
            )
            
            if not claim_data:
                return None
            
            # Get claim items
            claim_items = self.db_client.query_items(
                f"CLAIM#{claim_id}",
                "ITEM#"
            )
            
            # Organize items by status
            approved_items = []
            rejected_items = []
            review_items = []
            
            for item in claim_items:
                status = item.get('audit_status', '')
                
                if status == 'APPROVED':
                    approved_items.append(item)
                elif status == 'REJECTED':
                    rejected_items.append(item)
                else:
                    review_items.append(item)
            
            return {
                'claim': claim_data,
                'all_items': claim_items,
                'approved_items': approved_items,
                'rejected_items': rejected_items,
                'review_items': review_items,
                'summary': claim_data.get('audit_results', {})
            }
            
        except Exception as e:
            print(f"Error retrieving audit result: {str(e)}")
            return None
    
    def get_audit_history(
        self,
        patient_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit history for a patient
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of results
        
        Returns:
            List of audit results sorted by date
        """
        try:
            # Query all claims for patient
            claims = self.db_client.query_items(
                f"PATIENT#{patient_id}",
                "CLAIM#"
            )
            
            # Filter for audited claims
            audited_claims = [
                claim for claim in claims
                if claim.get('status') in ['AUDITED', 'SUBMITTED', 'APPROVED', 'REJECTED', 'PARTIALLY_APPROVED']
            ]
            
            # Sort by audit date (newest first)
            audited_claims.sort(
                key=lambda x: x.get('audit_results', {}).get('audit_date', ''),
                reverse=True
            )
            
            # Apply limit if specified
            if limit:
                audited_claims = audited_claims[:limit]
            
            return audited_claims
            
        except Exception as e:
            print(f"Error retrieving audit history: {str(e)}")
            return []
    
    def compare_audits(
        self,
        claim_id_1: str,
        patient_id_1: str,
        claim_id_2: str,
        patient_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two audit results
        
        Args:
            claim_id_1: First claim ID
            patient_id_1: First patient ID
            claim_id_2: Second claim ID
            patient_id_2: Second patient ID
        
        Returns:
            Comparison analysis
        """
        # Get both audit results
        audit1 = self.get_audit_result(claim_id_1, patient_id_1)
        audit2 = self.get_audit_result(claim_id_2, patient_id_2)
        
        if not audit1 or not audit2:
            return {
                'error': 'One or both audit results not found'
            }
        
        # Extract summaries
        summary1 = audit1['summary']
        summary2 = audit2['summary']
        
        # Calculate differences
        comparison = {
            'claim_1': {
                'claim_id': claim_id_1,
                'total_amount': summary1.get('total_amount', 0.0),
                'approved_amount': summary1.get('approved_amount', 0.0),
                'rejected_amount': summary1.get('rejected_amount', 0.0),
                'settlement_ratio': summary1.get('predicted_settlement_ratio', 0.0),
                'total_items': summary1.get('total_items', 0),
                'approved_items': summary1.get('approved_items', 0),
                'rejected_items': summary1.get('rejected_items', 0)
            },
            'claim_2': {
                'claim_id': claim_id_2,
                'total_amount': summary2.get('total_amount', 0.0),
                'approved_amount': summary2.get('approved_amount', 0.0),
                'rejected_amount': summary2.get('rejected_amount', 0.0),
                'settlement_ratio': summary2.get('predicted_settlement_ratio', 0.0),
                'total_items': summary2.get('total_items', 0),
                'approved_items': summary2.get('approved_items', 0),
                'rejected_items': summary2.get('rejected_items', 0)
            },
            'differences': {
                'total_amount_diff': summary2.get('total_amount', 0.0) - summary1.get('total_amount', 0.0),
                'approved_amount_diff': summary2.get('approved_amount', 0.0) - summary1.get('approved_amount', 0.0),
                'settlement_ratio_diff': summary2.get('predicted_settlement_ratio', 0.0) - summary1.get('predicted_settlement_ratio', 0.0),
                'items_diff': summary2.get('total_items', 0) - summary1.get('total_items', 0)
            }
        }
        
        return comparison
    
    def search_audits(
        self,
        hospital_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search audit results with filters
        
        Args:
            hospital_id: Hospital identifier
            filters: Search filters (status, date range, amount range, etc.)
        
        Returns:
            List of matching audit results
        """
        try:
            # Query claims by hospital using GSI2
            # This would use GSI2PK = HOSPITAL#{hospital_id}
            # For now, we'll use a simple query approach
            
            # Get all patients for hospital
            patients = self.db_client.query_items(
                f"HOSPITAL#{hospital_id}",
                "PATIENT#"
            )
            
            all_audits = []
            
            # Get audits for each patient
            for patient in patients:
                patient_id = patient.get('patient_id', '')
                if patient_id:
                    audits = self.get_audit_history(patient_id)
                    all_audits.extend(audits)
            
            # Apply filters
            if filters:
                all_audits = self._apply_filters(all_audits, filters)
            
            return all_audits
            
        except Exception as e:
            print(f"Error searching audits: {str(e)}")
            return []
    
    def get_audit_statistics(
        self,
        hospital_id: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get audit statistics for a hospital
        
        Args:
            hospital_id: Hospital identifier
            date_range: Optional date range filter
        
        Returns:
            Audit statistics
        """
        # Get all audits
        filters = {}
        if date_range:
            filters['date_range'] = date_range
        
        audits = self.search_audits(hospital_id, filters)
        
        if not audits:
            return {
                'total_audits': 0,
                'total_amount': 0.0,
                'total_approved': 0.0,
                'total_rejected': 0.0,
                'average_settlement_ratio': 0.0,
                'by_status': {}
            }
        
        # Calculate statistics
        total_audits = len(audits)
        total_amount = 0.0
        total_approved = 0.0
        total_rejected = 0.0
        settlement_ratios = []
        status_counts = {}
        
        for audit in audits:
            audit_results = audit.get('audit_results', {})
            
            total_amount += audit_results.get('total_amount', 0.0)
            total_approved += audit_results.get('approved_amount', 0.0)
            total_rejected += audit_results.get('rejected_amount', 0.0)
            
            settlement_ratio = audit_results.get('predicted_settlement_ratio', 0.0)
            if settlement_ratio > 0:
                settlement_ratios.append(settlement_ratio)
            
            status = audit.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate averages
        avg_settlement_ratio = 0.0
        if settlement_ratios:
            avg_settlement_ratio = sum(settlement_ratios) / len(settlement_ratios)
        
        return {
            'total_audits': total_audits,
            'total_amount': total_amount,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'average_settlement_ratio': avg_settlement_ratio,
            'by_status': status_counts,
            'date_range': date_range
        }
    
    def _apply_filters(
        self,
        audits: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to audit results"""
        filtered = audits
        
        # Filter by status
        if 'status' in filters:
            status = filters['status']
            filtered = [a for a in filtered if a.get('status') == status]
        
        # Filter by date range
        if 'date_range' in filters:
            date_range = filters['date_range']
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            
            if start_date:
                filtered = [
                    a for a in filtered
                    if a.get('audit_results', {}).get('audit_date', '') >= start_date
                ]
            
            if end_date:
                filtered = [
                    a for a in filtered
                    if a.get('audit_results', {}).get('audit_date', '') <= end_date
                ]
        
        # Filter by amount range
        if 'min_amount' in filters:
            min_amount = filters['min_amount']
            filtered = [
                a for a in filtered
                if a.get('total_amount', 0.0) >= min_amount
            ]
        
        if 'max_amount' in filters:
            max_amount = filters['max_amount']
            filtered = [
                a for a in filtered
                if a.get('total_amount', 0.0) <= max_amount
            ]
        
        # Filter by settlement ratio
        if 'min_settlement_ratio' in filters:
            min_ratio = filters['min_settlement_ratio']
            filtered = [
                a for a in filtered
                if a.get('predicted_settlement_ratio', 0.0) >= min_ratio
            ]
        
        return filtered
    
    def _create_audit_trail(
        self,
        claim_id: str,
        action: str,
        user_id: str,
        changes: Dict[str, Any]
    ) -> None:
        """Create audit trail entry"""
        audit_id = generate_id('audit')
        
        audit = AuditTrail(
            audit_id=audit_id,
            entity_id=claim_id,
            action=action,
            user_id=user_id,
            changes=changes
        )
        
        self.db_client.put_item(audit.to_dynamodb_item())

class AuditComparisonService:
    """Service for comparing and analyzing audit results"""
    
    def __init__(self, audit_service: AuditResultsService):
        self.audit_service = audit_service
    
    def compare_multiple_audits(
        self,
        audit_ids: List[tuple]  # List of (claim_id, patient_id) tuples
    ) -> Dict[str, Any]:
        """
        Compare multiple audit results
        
        Args:
            audit_ids: List of (claim_id, patient_id) tuples
        
        Returns:
            Comprehensive comparison analysis
        """
        if len(audit_ids) < 2:
            return {'error': 'At least 2 audits required for comparison'}
        
        # Get all audit results
        audits = []
        for claim_id, patient_id in audit_ids:
            audit = self.audit_service.get_audit_result(claim_id, patient_id)
            if audit:
                audits.append({
                    'claim_id': claim_id,
                    'patient_id': patient_id,
                    'data': audit
                })
        
        if len(audits) < 2:
            return {'error': 'Could not retrieve enough audit results'}
        
        # Calculate aggregate statistics
        total_amounts = []
        approved_amounts = []
        settlement_ratios = []
        
        for audit in audits:
            summary = audit['data']['summary']
            total_amounts.append(summary.get('total_amount', 0.0))
            approved_amounts.append(summary.get('approved_amount', 0.0))
            settlement_ratios.append(summary.get('predicted_settlement_ratio', 0.0))
        
        return {
            'audit_count': len(audits),
            'audits': audits,
            'aggregate_stats': {
                'total_amount_sum': sum(total_amounts),
                'total_amount_avg': sum(total_amounts) / len(total_amounts),
                'approved_amount_sum': sum(approved_amounts),
                'approved_amount_avg': sum(approved_amounts) / len(approved_amounts),
                'settlement_ratio_avg': sum(settlement_ratios) / len(settlement_ratios),
                'settlement_ratio_min': min(settlement_ratios),
                'settlement_ratio_max': max(settlement_ratios)
            }
        }
    
    def identify_trends(
        self,
        hospital_id: str,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Identify trends in audit results over time
        
        Args:
            hospital_id: Hospital identifier
            time_period_days: Number of days to analyze
        
        Returns:
            Trend analysis
        """
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=time_period_days)
        
        date_range = {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
        
        # Get statistics
        stats = self.audit_service.get_audit_statistics(hospital_id, date_range)
        
        # Calculate trends (simplified - in production would use time series analysis)
        return {
            'time_period_days': time_period_days,
            'statistics': stats,
            'trends': {
                'average_settlement_ratio': stats['average_settlement_ratio'],
                'total_audits': stats['total_audits'],
                'approval_rate': stats['total_approved'] / stats['total_amount'] if stats['total_amount'] > 0 else 0.0
            }
        }
