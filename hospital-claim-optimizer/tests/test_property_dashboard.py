"""
Property-Based Tests for Dashboard Functionality
Tests Properties 15-17, 23 for dashboard and notification validation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-functions', 'dashboard'))

import unittest
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List

from dashboard import DashboardService
from alert_service import AlertService, WebhookNotificationService, AlertType, AlertPriority
from data_models import RiskLevel, ClaimStatus, AuditStatus
from database_access import DynamoDBAccessLayer
from audit_service import AuditResultsService

# Test data generators
@st.composite
def patient_strategy(draw):
    """Generate patient data"""
    patient_id = f"pat_{draw(st.integers(min_value=100, max_value=999))}"
    hospital_id = f"hosp_{draw(st.integers(min_value=10, max_value=99))}"
    
    return {
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=['L', 'P']))),
        'age': draw(st.integers(min_value=1, max_value=100)),
        'policy_number': f"POL{draw(st.integers(min_value=100000, max_value=999999))}",
        'insurer_name': draw(st.sampled_from(['HealthCare Plus', 'MediCare Pro', 'Insurance Corp'])),
        'PK': f"HOSPITAL#{hospital_id}",
        'SK': f"PATIENT#{patient_id}"
    }

@st.composite
def claim_strategy(draw, patient_id: str, hospital_id: str):
    """Generate claim data"""
    claim_id = f"clm_{draw(st.integers(min_value=1000, max_value=9999))}"
    
    total_items = draw(st.integers(min_value=1, max_value=50))
    approved_items = draw(st.integers(min_value=0, max_value=total_items))
    rejected_items = draw(st.integers(min_value=0, max_value=total_items - approved_items))
    review_items = total_items - approved_items - rejected_items
    
    total_amount = draw(st.floats(min_value=1000.0, max_value=500000.0))
    approved_amount = draw(st.floats(min_value=0.0, max_value=total_amount))
    
    return {
        'claim_id': claim_id,
        'patient_id': patient_id,
        'hospital_id': hospital_id,
        'status': draw(st.sampled_from([
            ClaimStatus.AUDITED.value,
            ClaimStatus.SUBMITTED.value,
            ClaimStatus.APPROVED.value
        ])),
        'total_amount': total_amount,
        'risk_score': draw(st.integers(min_value=0, max_value=100)),
        'risk_level': draw(st.sampled_from([
            RiskLevel.HIGH.value,
            RiskLevel.MEDIUM.value,
            RiskLevel.LOW.value
        ])),
        'predicted_settlement_ratio': draw(st.floats(min_value=0.0, max_value=1.0)),
        'audit_results': {
            'total_items': total_items,
            'approved_items': approved_items,
            'rejected_items': rejected_items,
            'review_items': review_items,
            'total_amount': total_amount,
            'approved_amount': approved_amount,
            'rejected_amount': total_amount - approved_amount
        },
        'created_at': draw(st.datetimes(min_value=None, max_value=None)).isoformat(),
        'PK': f"PATIENT#{patient_id}",
        'SK': f"CLAIM#{claim_id}"
    }

class TestDashboardProperties(unittest.TestCase):
    """Property-based tests for dashboard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_client = Mock(spec=DynamoDBAccessLayer)
        self.mock_audit_service = Mock(spec=AuditResultsService)
        self.dashboard_service = DashboardService(self.mock_db_client, self.mock_audit_service)
        self.alert_service = AlertService(self.mock_db_client)
    
    @given(
        num_patients=st.integers(min_value=1, max_value=10),
        claims_per_patient=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_15_dashboard_data_completeness(self, num_patients, claims_per_patient):
        """
        Property 15: Dashboard Data Completeness
        **Validates: Requirements 5.1, 5.2, 5.6**
        
        Dashboard must display:
        1. Complete patient list with claim summaries
        2. All claims with proper categorization
        3. Accurate analytics and statistics
        """
        hospital_id = "hosp_test"
        
        # Generate test data
        patients = []
        all_claims = []
        
        for i in range(num_patients):
            patient_id = f"pat_{i}"
            patient = {
                'patient_id': patient_id,
                'hospital_id': hospital_id,
                'name': f"Patient {i}",
                'age': 30 + i,
                'policy_number': f"POL{i}",
                'insurer_name': 'Test Insurance',
                'PK': f"HOSPITAL#{hospital_id}",
                'SK': f"PATIENT#{patient_id}"
            }
            patients.append(patient)
            
            # Generate claims for patient
            for j in range(claims_per_patient):
                claim = {
                    'claim_id': f"clm_{i}_{j}",
                    'patient_id': patient_id,
                    'hospital_id': hospital_id,
                    'status': ClaimStatus.AUDITED.value,
                    'total_amount': 10000.0 * (j + 1),
                    'risk_score': 50,
                    'risk_level': RiskLevel.MEDIUM.value,
                    'predicted_settlement_ratio': 0.85,
                    'audit_results': {
                        'total_items': 10,
                        'approved_items': 8,
                        'rejected_items': 2,
                        'review_items': 0,
                        'total_amount': 10000.0 * (j + 1),
                        'approved_amount': 8500.0 * (j + 1),
                        'rejected_amount': 1500.0 * (j + 1)
                    },
                    'created_at': '2024-01-01T00:00:00Z',
                    'PK': f"PATIENT#{patient_id}",
                    'SK': f"CLAIM#clm_{i}_{j}"
                }
                all_claims.append(claim)
        
        # Setup mocks
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            patients if "HOSPITAL#" in pk else
            [c for c in all_claims if c['patient_id'] in pk]
        )
        
        # Get dashboard overview
        result = self.dashboard_service.get_dashboard_overview(hospital_id)
        
        # Verify success
        self.assertTrue(result['success'], "Dashboard should load successfully")
        
        # Property: All patients must be included
        self.assertEqual(
            result['summary']['total_patients'],
            num_patients,
            "All patients must be included in dashboard"
        )
        
        # Property: All claims must be included
        expected_total_claims = num_patients * claims_per_patient
        self.assertEqual(
            result['summary']['total_claims'],
            expected_total_claims,
            "All claims must be included in dashboard"
        )
        
        # Property: Patient summaries must be complete
        patient_summaries = result['patients']
        self.assertEqual(len(patient_summaries), num_patients)
        
        for patient_summary in patient_summaries:
            self.assertIn('patient_id', patient_summary)
            self.assertIn('name', patient_summary)
            self.assertIn('total_claims', patient_summary)
            self.assertIn('total_amount', patient_summary)
            
            # Property: Claim count must match
            self.assertEqual(
                patient_summary['total_claims'],
                claims_per_patient,
                "Patient claim count must be accurate"
            )
        
        # Property: Analytics must be present
        self.assertIn('analytics', result)
        analytics = result['analytics']
        
        self.assertIn('total_amount', analytics)
        self.assertIn('average_settlement_ratio', analytics)
        self.assertIn('by_status', analytics)
        self.assertIn('by_risk', analytics)
        
        # Property: Total amount must be sum of all claims
        expected_total = sum(c['total_amount'] for c in all_claims)
        self.assertAlmostEqual(
            analytics['total_amount'],
            expected_total,
            places=2,
            msg="Total amount must match sum of all claims"
        )
    
    @given(
        num_claims=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_16_dashboard_filtering_and_analytics(self, num_claims):
        """
        Property 16: Dashboard Filtering and Analytics
        **Validates: Requirements 5.2, 5.3, 5.5**
        
        Dashboard filtering must:
        1. Correctly filter by status, risk level, date range
        2. Maintain data consistency after filtering
        3. Provide accurate analytics for filtered data
        """
        hospital_id = "hosp_test"
        patient_id = "pat_test"
        
        # Generate claims with different statuses and risk levels
        claims = []
        for i in range(num_claims):
            claim = {
                'claim_id': f"clm_{i}",
                'patient_id': patient_id,
                'hospital_id': hospital_id,
                'status': ClaimStatus.AUDITED.value if i % 2 == 0 else ClaimStatus.SUBMITTED.value,
                'total_amount': 10000.0 * (i + 1),
                'risk_score': 30 + (i * 5),
                'risk_level': RiskLevel.HIGH.value if i % 3 == 0 else RiskLevel.MEDIUM.value,
                'predicted_settlement_ratio': 0.8,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 8,
                    'rejected_items': 2,
                    'review_items': 0,
                    'total_amount': 10000.0 * (i + 1),
                    'approved_amount': 8000.0 * (i + 1),
                    'rejected_amount': 2000.0 * (i + 1)
                },
                'created_at': f"2024-01-{(i % 28) + 1:02d}T00:00:00Z",
                'PK': f"PATIENT#{patient_id}",
                'SK': f"CLAIM#clm_{i}"
            }
            claims.append(claim)
        
        # Setup mocks
        patients = [{
            'patient_id': patient_id,
            'hospital_id': hospital_id,
            'name': 'Test Patient',
            'age': 45,
            'policy_number': 'POL123',
            'insurer_name': 'Test Insurance'
        }]
        
        self.mock_db_client.query_items.side_effect = lambda pk, sk=None: (
            patients if "HOSPITAL#" in pk else claims
        )
        
        # Test filtering by status
        filters = {'status': [ClaimStatus.AUDITED.value]}
        result = self.dashboard_service.get_dashboard_overview(hospital_id, filters)
        
        # Property: Filtered count should match filter criteria
        audited_count = len([c for c in claims if c['status'] == ClaimStatus.AUDITED.value])
        self.assertEqual(
            result['summary']['total_claims'],
            audited_count,
            "Filtered claim count must match filter criteria"
        )
        
        # Test filtering by risk level
        filters = {'risk_level': RiskLevel.HIGH.value}
        result = self.dashboard_service.get_dashboard_overview(hospital_id, filters)
        
        high_risk_count = len([c for c in claims if c['risk_level'] == RiskLevel.HIGH.value])
        self.assertEqual(
            result['summary']['total_claims'],
            high_risk_count,
            "Risk level filter must work correctly"
        )
    
    @given(
        risk_level=st.sampled_from([RiskLevel.HIGH.value, RiskLevel.MEDIUM.value, RiskLevel.LOW.value]),
        total_amount=st.floats(min_value=50000.0, max_value=500000.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_17_alert_display(self, risk_level, total_amount):
        """
        Property 17: Alert Display
        **Validates: Requirements 5.4**
        
        Alerts must:
        1. Be generated for high-risk claims
        2. Include clear action items
        3. Be properly categorized by priority
        """
        hospital_id = "hosp_test"
        
        # Create claim data
        claim_data = {
            'claim_id': 'clm_test',
            'patient_id': 'pat_test',
            'hospital_id': hospital_id,
            'status': ClaimStatus.AUDITED.value,
            'total_amount': total_amount,
            'risk_score': 75 if risk_level == RiskLevel.HIGH.value else 45,
            'risk_level': risk_level,
            'predicted_settlement_ratio': 0.65,
            'audit_results': {
                'total_items': 10,
                'approved_items': 6,
                'rejected_items': 3,
                'review_items': 1,
                'total_amount': total_amount,
                'approved_amount': total_amount * 0.65,
                'rejected_amount': total_amount * 0.35
            }
        }
        
        # Setup mock
        self.mock_db_client.put_item.return_value = True
        
        # Generate alerts
        alerts = self.alert_service.check_and_generate_alerts(hospital_id, claim_data)
        
        # Property: Alerts should be generated
        self.assertIsInstance(alerts, list, "Alerts should be a list")
        
        # Property: High-risk claims should generate alerts
        if risk_level == RiskLevel.HIGH.value:
            self.assertGreater(
                len(alerts),
                0,
                "High-risk claims must generate alerts"
            )
            
            # Property: Alerts must have required fields
            for alert in alerts:
                self.assertIn('alert_id', alert)
                self.assertIn('alert_type', alert)
                self.assertIn('priority', alert)
                self.assertIn('title', alert)
                self.assertIn('message', alert)
                self.assertIn('action_items', alert)
                
                # Property: Action items must be present
                self.assertIsInstance(alert['action_items'], list)
                self.assertGreater(
                    len(alert['action_items']),
                    0,
                    "Alerts must include action items"
                )
        
        # Property: Large amounts should generate alerts
        if total_amount >= 200000:
            large_amount_alerts = [
                a for a in alerts
                if a.get('alert_type') == AlertType.LARGE_CLAIM_AMOUNT.value
            ]
            self.assertGreater(
                len(large_amount_alerts),
                0,
                "Large claim amounts must generate alerts"
            )
    
    @given(
        event_type=st.sampled_from(['claim.audited', 'claim.high_risk', 'policy.uploaded'])
    )
    @settings(max_examples=50, deadline=None)
    def test_property_23_webhook_notifications(self, event_type):
        """
        Property 23: Webhook Notifications
        **Validates: Requirements 7.4**
        
        Webhook notifications must:
        1. Include all required event data
        2. Be properly formatted
        3. Handle different event types
        """
        webhook_service = WebhookNotificationService()
        
        # Prepare test data based on event type
        if event_type == 'claim.audited':
            data = {
                'claim_id': 'clm_test',
                'patient_id': 'pat_test',
                'hospital_id': 'hosp_test',
                'total_amount': 50000.0,
                'risk_level': RiskLevel.MEDIUM.value,
                'settlement_ratio': 0.85,
                'audit_results': {
                    'total_items': 10,
                    'approved_items': 8,
                    'rejected_items': 2
                }
            }
        elif event_type == 'claim.high_risk':
            data = {
                'claim_id': 'clm_test',
                'patient_id': 'pat_test',
                'hospital_id': 'hosp_test',
                'risk_score': 85,
                'risk_level': RiskLevel.HIGH.value,
                'total_amount': 200000.0
            }
        else:  # policy.uploaded
            data = {
                'policy_id': 'pol_test',
                'hospital_id': 'hosp_test',
                'policy_name': 'Test Policy',
                'extraction_status': 'COMPLETED'
            }
        
        # Mock webhook URL
        webhook_url = 'https://example.com/webhook'
        
        # Mock HTTP client
        with patch.object(webhook_service, 'http') as mock_http:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.data = b'{"success": true}'
            mock_http.request.return_value = mock_response
            
            # Send webhook
            result = webhook_service.send_webhook_notification(
                webhook_url=webhook_url,
                event_type=event_type,
                data=data
            )
            
            # Property: Webhook should succeed
            self.assertTrue(result['success'], "Webhook should send successfully")
            
            # Property: HTTP request should be made
            self.assertTrue(mock_http.request.called, "HTTP request should be made")
            
            # Verify request parameters
            call_args = mock_http.request.call_args
            self.assertEqual(call_args[0][0], 'POST', "Should use POST method")
            self.assertEqual(call_args[0][1], webhook_url, "Should use correct URL")
            
            # Property: Payload should include event type and data
            import json
            payload = json.loads(call_args[1]['body'].decode('utf-8'))
            
            self.assertIn('event_type', payload)
            self.assertEqual(payload['event_type'], event_type)
            self.assertIn('data', payload)
            self.assertIn('timestamp', payload)
    
    @given(
        num_alerts=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_alert_filtering(self, num_alerts):
        """
        Additional Property: Alert Filtering
        
        Alert filtering must correctly filter by status, priority, and type.
        """
        hospital_id = "hosp_test"
        
        # Generate alerts with different properties
        alerts = []
        for i in range(num_alerts):
            alert = {
                'PK': f"HOSPITAL#{hospital_id}",
                'SK': f"ALERT#alert_{i}",
                'alert_id': f"alert_{i}",
                'hospital_id': hospital_id,
                'alert_type': AlertType.HIGH_RISK_CLAIM.value if i % 2 == 0 else AlertType.LARGE_CLAIM_AMOUNT.value,
                'priority': AlertPriority.HIGH.value if i % 3 == 0 else AlertPriority.MEDIUM.value,
                'status': 'ACTIVE' if i % 2 == 0 else 'ACKNOWLEDGED',
                'acknowledged': i % 2 != 0,
                'created_at': f"2024-01-{(i % 28) + 1:02d}T00:00:00Z"
            }
            alerts.append(alert)
        
        # Setup mock
        self.mock_db_client.query_items.return_value = alerts
        
        # Test filtering by status
        filtered = self.alert_service.get_alerts(
            hospital_id=hospital_id,
            filters={'status': 'ACTIVE'}
        )
        
        active_count = len([a for a in alerts if a['status'] == 'ACTIVE'])
        self.assertEqual(len(filtered), active_count, "Status filter must work correctly")
        
        # Test filtering by priority
        filtered = self.alert_service.get_alerts(
            hospital_id=hospital_id,
            filters={'priority': AlertPriority.HIGH.value}
        )
        
        high_priority_count = len([a for a in alerts if a['priority'] == AlertPriority.HIGH.value])
        self.assertEqual(len(filtered), high_priority_count, "Priority filter must work correctly")

def test_dashboard_integration():
    """Integration test for dashboard workflow"""
    # Setup
    mock_db_client = Mock(spec=DynamoDBAccessLayer)
    mock_audit_service = Mock(spec=AuditResultsService)
    dashboard_service = DashboardService(mock_db_client, mock_audit_service)
    
    # Create test data
    hospital_id = "hosp_test"
    patients = [{
        'patient_id': 'pat_001',
        'hospital_id': hospital_id,
        'name': 'John Doe',
        'age': 45,
        'policy_number': 'POL123',
        'insurer_name': 'Test Insurance'
    }]
    
    claims = [{
        'claim_id': 'clm_001',
        'patient_id': 'pat_001',
        'hospital_id': hospital_id,
        'status': ClaimStatus.AUDITED.value,
        'total_amount': 50000.0,
        'risk_score': 60,
        'risk_level': RiskLevel.MEDIUM.value,
        'predicted_settlement_ratio': 0.85,
        'audit_results': {
            'total_items': 10,
            'approved_items': 8,
            'rejected_items': 2,
            'review_items': 0,
            'total_amount': 50000.0,
            'approved_amount': 42500.0,
            'rejected_amount': 7500.0
        },
        'created_at': '2024-01-15T00:00:00Z'
    }]
    
    mock_db_client.query_items.side_effect = lambda pk, sk=None: (
        patients if "HOSPITAL#" in pk else claims
    )
    
    # Get dashboard overview
    result = dashboard_service.get_dashboard_overview(hospital_id)
    
    # Verify
    assert result['success'] is True
    assert result['summary']['total_patients'] == 1
    assert result['summary']['total_claims'] == 1
    assert result['summary']['total_claim_amount'] == 50000.0

if __name__ == '__main__':
    unittest.main()
