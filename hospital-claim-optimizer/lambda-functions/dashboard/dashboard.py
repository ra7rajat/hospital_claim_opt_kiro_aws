"""
Dashboard API Lambda Function
Provides data aggregation and analytics for TPA Command Center
"""
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add common layer to path
sys.path.append('/opt/python')

from auth_middleware import require_auth, Permission, audit_action
from security_config import create_secure_response, validate_input_data, check_rate_limit
from database_access import DynamoDBAccessLayer
from data_models import RiskLevel, ClaimStatus
from audit_service import AuditResultsService
from common_utils import get_timestamp

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'RevenueZ_Main')

# Initialize clients
db_client = DynamoDBAccessLayer(TABLE_NAME)
audit_service = AuditResultsService(db_client)

class DashboardService:
    """Service for dashboard data aggregation and analytics"""
    
    def __init__(self, db_client: DynamoDBAccessLayer, audit_service: AuditResultsService):
        self.db_client = db_client
        self.audit_service = audit_service
    
    def get_dashboard_overview(
        self,
        hospital_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview
        
        Args:
            hospital_id: Hospital identifier
            filters: Optional filters (date range, status, etc.)
        
        Returns:
            Dashboard data with patients, claims, and analytics
        """
        # Get all patients for hospital
        patients = self.db_client.query_items(
            f"HOSPITAL#{hospital_id}",
            "PATIENT#"
        )
        
        # Get all claims for the hospital
        all_claims = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            if patient_id:
                claims = self.db_client.query_items(
                    f"PATIENT#{patient_id}",
                    "CLAIM#"
                )
                all_claims.extend(claims)
        
        # Apply filters
        if filters:
            all_claims = self._apply_filters(all_claims, filters)
        
        # Calculate analytics
        analytics = self._calculate_analytics(all_claims)
        
        # Get high-risk claims
        high_risk_claims = [
            claim for claim in all_claims
            if claim.get('risk_level') == RiskLevel.HIGH.value
        ]
        
        # Get recent claims
        recent_claims = sorted(
            all_claims,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )[:10]
        
        # Prepare patient summaries
        patient_summaries = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            patient_claims = [c for c in all_claims if c.get('patient_id') == patient_id]
            
            if patient_claims:
                patient_summaries.append({
                    'patient_id': patient_id,
                    'name': patient.get('name', ''),
                    'age': patient.get('age', 0),
                    'policy_number': patient.get('policy_number', ''),
                    'insurer_name': patient.get('insurer_name', ''),
                    'total_claims': len(patient_claims),
                    'total_amount': sum(c.get('total_amount', 0.0) for c in patient_claims),
                    'high_risk_claims': len([c for c in patient_claims if c.get('risk_level') == RiskLevel.HIGH.value]),
                    'latest_claim_date': max(c.get('created_at', '') for c in patient_claims) if patient_claims else None
                })
        
        return {
            'success': True,
            'hospital_id': hospital_id,
            'summary': {
                'total_patients': len(patients),
                'total_claims': len(all_claims),
                'high_risk_claims': len(high_risk_claims),
                'total_claim_amount': analytics['total_amount'],
                'average_settlement_ratio': analytics['average_settlement_ratio'],
                'claims_by_status': analytics['by_status'],
                'claims_by_risk': analytics['by_risk']
            },
            'patients': patient_summaries,
            'recent_claims': recent_claims,
            'high_risk_claims': high_risk_claims[:5],  # Top 5 high-risk
            'analytics': analytics,
            'generated_at': get_timestamp()
        }
    
    def get_patient_details(
        self,
        hospital_id: str,
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific patient
        
        Args:
            hospital_id: Hospital identifier
            patient_id: Patient identifier
        
        Returns:
            Patient details with claims and history
        """
        # Get patient data
        patient = self.db_client.get_item(
            f"HOSPITAL#{hospital_id}",
            f"PATIENT#{patient_id}"
        )
        
        if not patient:
            return {
                'success': False,
                'error': f'Patient {patient_id} not found'
            }
        
        # Get patient claims
        claims = self.db_client.query_items(
            f"PATIENT#{patient_id}",
            "CLAIM#"
        )
        
        # Calculate patient-specific analytics
        total_amount = sum(c.get('total_amount', 0.0) for c in claims)
        approved_amount = sum(
            c.get('audit_results', {}).get('approved_amount', 0.0)
            for c in claims
        )
        
        settlement_ratios = [
            c.get('predicted_settlement_ratio', 0.0)
            for c in claims
            if c.get('predicted_settlement_ratio', 0.0) > 0
        ]
        
        avg_settlement_ratio = (
            sum(settlement_ratios) / len(settlement_ratios)
            if settlement_ratios else 0.0
        )
        
        # Risk distribution
        risk_distribution = {
            'high': len([c for c in claims if c.get('risk_level') == RiskLevel.HIGH.value]),
            'medium': len([c for c in claims if c.get('risk_level') == RiskLevel.MEDIUM.value]),
            'low': len([c for c in claims if c.get('risk_level') == RiskLevel.LOW.value])
        }
        
        return {
            'success': True,
            'patient': patient,
            'claims': claims,
            'analytics': {
                'total_claims': len(claims),
                'total_amount': total_amount,
                'approved_amount': approved_amount,
                'average_settlement_ratio': avg_settlement_ratio,
                'risk_distribution': risk_distribution
            }
        }
    
    def get_filtered_claims(
        self,
        hospital_id: str,
        filters: Dict[str, Any],
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get filtered and sorted claims
        
        Args:
            hospital_id: Hospital identifier
            filters: Filter criteria
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            Filtered claims with pagination
        """
        # Get all patients for hospital
        patients = self.db_client.query_items(
            f"HOSPITAL#{hospital_id}",
            "PATIENT#"
        )
        
        # Get all claims
        all_claims = []
        for patient in patients:
            patient_id = patient.get('patient_id', '')
            if patient_id:
                claims = self.db_client.query_items(
                    f"PATIENT#{patient_id}",
                    "CLAIM#"
                )
                all_claims.extend(claims)
        
        # Apply filters
        filtered_claims = self._apply_filters(all_claims, filters)
        
        # Sort claims
        reverse = sort_order == 'desc'
        
        if sort_by == 'created_at':
            filtered_claims.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
        elif sort_by == 'total_amount':
            filtered_claims.sort(key=lambda x: x.get('total_amount', 0.0), reverse=reverse)
        elif sort_by == 'risk_score':
            filtered_claims.sort(key=lambda x: x.get('risk_score', 0), reverse=reverse)
        elif sort_by == 'settlement_ratio':
            filtered_claims.sort(key=lambda x: x.get('predicted_settlement_ratio', 0.0), reverse=reverse)
        
        # Apply pagination
        total_count = len(filtered_claims)
        
        if limit:
            filtered_claims = filtered_claims[offset:offset + limit]
        else:
            filtered_claims = filtered_claims[offset:]
        
        return {
            'success': True,
            'claims': filtered_claims,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'returned': len(filtered_claims)
            }
        }
    
    def get_analytics(
        self,
        hospital_id: str,
        time_period: str = '30d'
    ) -> Dict[str, Any]:
        """
        Get detailed analytics for dashboard
        
        Args:
            hospital_id: Hospital identifier
            time_period: Time period (7d, 30d, 90d, 1y)
        
        Returns:
            Detailed analytics
        """
        # Calculate date range
        days_map = {
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '1y': 365
        }
        
        days = days_map.get(time_period, 30)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get claims in date range
        filters = {
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
        result = self.get_dashboard_overview(hospital_id, filters)
        
        if not result['success']:
            return result
        
        # Add time-series data (simplified)
        analytics = result['analytics']
        
        # Calculate trends
        trends = {
            'settlement_ratio_trend': 'stable',  # Would calculate from historical data
            'claim_volume_trend': 'increasing',
            'risk_level_trend': 'stable'
        }
        
        return {
            'success': True,
            'time_period': time_period,
            'analytics': analytics,
            'trends': trends,
            'summary': result['summary']
        }
    
    def _apply_filters(
        self,
        claims: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to claims list"""
        filtered = claims
        
        # Filter by status
        if 'status' in filters:
            status = filters['status']
            if isinstance(status, list):
                filtered = [c for c in filtered if c.get('status') in status]
            else:
                filtered = [c for c in filtered if c.get('status') == status]
        
        # Filter by risk level
        if 'risk_level' in filters:
            risk_level = filters['risk_level']
            if isinstance(risk_level, list):
                filtered = [c for c in filtered if c.get('risk_level') in risk_level]
            else:
                filtered = [c for c in filtered if c.get('risk_level') == risk_level]
        
        # Filter by date range
        if 'date_range' in filters:
            date_range = filters['date_range']
            start_date = date_range.get('start')
            end_date = date_range.get('end')
            
            if start_date:
                filtered = [c for c in filtered if c.get('created_at', '') >= start_date]
            if end_date:
                filtered = [c for c in filtered if c.get('created_at', '') <= end_date]
        
        # Filter by amount range
        if 'min_amount' in filters:
            min_amount = filters['min_amount']
            filtered = [c for c in filtered if c.get('total_amount', 0.0) >= min_amount]
        
        if 'max_amount' in filters:
            max_amount = filters['max_amount']
            filtered = [c for c in filtered if c.get('total_amount', 0.0) <= max_amount]
        
        # Filter by patient
        if 'patient_id' in filters:
            patient_id = filters['patient_id']
            filtered = [c for c in filtered if c.get('patient_id') == patient_id]
        
        return filtered
    
    def _calculate_analytics(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate analytics from claims"""
        if not claims:
            return {
                'total_amount': 0.0,
                'approved_amount': 0.0,
                'rejected_amount': 0.0,
                'average_settlement_ratio': 0.0,
                'by_status': {},
                'by_risk': {}
            }
        
        total_amount = 0.0
        approved_amount = 0.0
        rejected_amount = 0.0
        settlement_ratios = []
        
        status_counts = {}
        risk_counts = {}
        
        for claim in claims:
            total_amount += claim.get('total_amount', 0.0)
            
            audit_results = claim.get('audit_results', {})
            approved_amount += audit_results.get('approved_amount', 0.0)
            rejected_amount += audit_results.get('rejected_amount', 0.0)
            
            settlement_ratio = claim.get('predicted_settlement_ratio', 0.0)
            if settlement_ratio > 0:
                settlement_ratios.append(settlement_ratio)
            
            status = claim.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            risk_level = claim.get('risk_level', 'UNKNOWN')
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        avg_settlement_ratio = (
            sum(settlement_ratios) / len(settlement_ratios)
            if settlement_ratios else 0.0
        )
        
        return {
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'rejected_amount': rejected_amount,
            'average_settlement_ratio': avg_settlement_ratio,
            'by_status': status_counts,
            'by_risk': risk_counts
        }

# Initialize dashboard service
dashboard_service = DashboardService(db_client, audit_service)

@require_auth([Permission.VIEW_DASHBOARD])
@audit_action("view_dashboard", "dashboard")
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for dashboard API requests
    """
    try:
        # Rate limiting
        user_info = event.get('user_info', {})
        user_id = user_info.get('user_id', 'unknown')
        
        if not check_rate_limit(user_id, limit=100):
            return create_secure_response(429, {
                'error': 'Rate limit exceeded. Please try again later.'
            })
        
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        # Get hospital_id from user context
        hospital_id = user_info.get('hospital_id')
        if not hospital_id:
            return create_secure_response(400, {
                'error': 'Hospital ID not found in user context'
            })
        
        # Route to appropriate handler
        if '/dashboard/overview' in path:
            # Dashboard overview
            filters = {}
            
            if 'status' in query_params:
                filters['status'] = query_params['status'].split(',')
            if 'risk_level' in query_params:
                filters['risk_level'] = query_params['risk_level'].split(',')
            if 'start_date' in query_params and 'end_date' in query_params:
                filters['date_range'] = {
                    'start': query_params['start_date'],
                    'end': query_params['end_date']
                }
            
            result = dashboard_service.get_dashboard_overview(hospital_id, filters)
            
        elif '/dashboard/patient/' in path:
            # Patient details
            patient_id = path.split('/dashboard/patient/')[-1]
            result = dashboard_service.get_patient_details(hospital_id, patient_id)
            
        elif '/dashboard/claims' in path:
            # Filtered claims
            filters = {}
            
            if 'status' in query_params:
                filters['status'] = query_params['status'].split(',')
            if 'risk_level' in query_params:
                filters['risk_level'] = query_params['risk_level'].split(',')
            if 'patient_id' in query_params:
                filters['patient_id'] = query_params['patient_id']
            
            sort_by = query_params.get('sort_by', 'created_at')
            sort_order = query_params.get('sort_order', 'desc')
            limit = int(query_params.get('limit', 50))
            offset = int(query_params.get('offset', 0))
            
            result = dashboard_service.get_filtered_claims(
                hospital_id=hospital_id,
                filters=filters,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset
            )
            
        elif '/dashboard/analytics' in path:
            # Analytics
            time_period = query_params.get('period', '30d')
            result = dashboard_service.get_analytics(hospital_id, time_period)
            
        else:
            # Default: overview
            result = dashboard_service.get_dashboard_overview(hospital_id)
        
        if not result.get('success', True):
            return create_secure_response(400, {
                'error': result.get('error', 'Dashboard request failed')
            })
        
        return create_secure_response(200, {
            'message': 'Dashboard data retrieved successfully',
            'data': result
        })
        
    except Exception as e:
        print(f"Error in dashboard handler: {str(e)}")
        return create_secure_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })
