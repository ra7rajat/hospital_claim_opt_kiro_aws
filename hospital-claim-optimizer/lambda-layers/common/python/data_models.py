"""
Data Models for Hospital Claim Settlement Optimizer
Implements DynamoDB single-table design with adjacency list pattern
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
import json

class EntityType(Enum):
    HOSPITAL = "HOSPITAL"
    PATIENT = "PATIENT"
    POLICY = "POLICY"
    CLAIM = "CLAIM"
    CLAIM_ITEM = "CLAIM_ITEM"
    AUDIT = "AUDIT"

class ClaimStatus(Enum):
    DRAFT = "DRAFT"
    AUDITED = "AUDITED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AuditStatus(Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"

@dataclass
class BaseEntity:
    """Base class for all DynamoDB entities"""
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        item = asdict(self)
        # Remove None values but keep empty strings and other falsy values that are valid
        filtered_item = {k: v for k, v in item.items() if v is not None}
        
        # Convert lowercase keys to DynamoDB convention (uppercase)
        if 'pk' in filtered_item:
            filtered_item['PK'] = filtered_item.pop('pk')
        if 'sk' in filtered_item:
            filtered_item['SK'] = filtered_item.pop('sk')
            
        return filtered_item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]):
        """Create instance from DynamoDB item"""
        # This would need to be implemented per subclass
        raise NotImplementedError

@dataclass
class Hospital(BaseEntity):
    """Hospital entity"""
    hospital_id: str
    org_name: str
    license_key: str
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    total_claims_processed: int = 0
    subscription_tier: str = "basic"
    contact_email: str = ""
    contact_phone: str = ""
    address: str = ""
    
    def __post_init__(self):
        self.pk = f"HOSPITAL#{self.hospital_id}"
        self.sk = "METADATA"
        self.entity_type = EntityType.HOSPITAL.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

@dataclass
class Patient(BaseEntity):
    """Patient entity"""
    patient_id: str
    hospital_id: str
    name: str
    age: int
    policy_number: str
    insurer_name: str
    admit_date: str
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    discharge_date: Optional[str] = None
    active_policies: List[str] = field(default_factory=list)
    medical_history: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.pk = f"HOSPITAL#{self.hospital_id}"
        self.sk = f"PATIENT#{self.patient_id}"
        self.entity_type = EntityType.PATIENT.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

@dataclass
class CoverageRule:
    """Coverage rule within a policy"""
    procedure_codes: List[str]
    coverage_percentage: float
    annual_limit: Optional[float] = None
    lifetime_limit: Optional[float] = None
    pre_auth_required: bool = False
    exclusions: List[str] = None
    
    def __post_init__(self):
        if self.exclusions is None:
            self.exclusions = []

@dataclass
class Policy(BaseEntity):
    """Policy entity"""
    policy_id: str
    hospital_id: str
    policy_name: str
    file_size: int
    content_type: str
    s3_key: str
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    extraction_status: str = "PENDING_UPLOAD"
    extracted_rules: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    extraction_confidence: float = 0.0
    version: int = 1
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    error_message: str = ""
    
    def __post_init__(self):
        self.pk = f"HOSPITAL#{self.hospital_id}"
        self.sk = f"POLICY#{self.policy_id}"
        self.entity_type = EntityType.POLICY.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

@dataclass
class Claim(BaseEntity):
    """Claim entity"""
    claim_id: str
    patient_id: str
    hospital_id: str
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    status: str = ClaimStatus.DRAFT.value
    total_amount: float = 0.0
    risk_score: int = 0
    risk_level: str = RiskLevel.MEDIUM.value
    predicted_settlement_ratio: float = 0.0
    audit_results: Dict[str, Any] = field(default_factory=dict)
    submission_date: Optional[str] = None
    approval_date: Optional[str] = None
    rejection_reasons: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.pk = f"PATIENT#{self.patient_id}"
        self.sk = f"CLAIM#{self.claim_id}"
        self.entity_type = EntityType.CLAIM.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

@dataclass
class ClaimItem(BaseEntity):
    """Individual line item within a claim"""
    item_id: str
    claim_id: str
    description: str
    cost: float
    category: str
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    audit_status: str = AuditStatus.REQUIRES_REVIEW.value
    rejection_reason: str = ""
    policy_clause_reference: str = ""
    optimization_suggestion: str = ""
    procedure_code: str = ""
    
    def __post_init__(self):
        self.pk = f"CLAIM#{self.claim_id}"
        self.sk = f"ITEM#{self.item_id}"
        self.entity_type = EntityType.CLAIM_ITEM.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

@dataclass
class AuditTrail(BaseEntity):
    """Audit trail entity for tracking changes"""
    audit_id: str
    entity_id: str
    action: str
    user_id: str
    changes: Dict[str, Any]
    pk: str = field(default="", init=False)
    sk: str = field(default="", init=False)
    entity_type: str = field(default="", init=False)
    created_at: str = field(default="", init=False)
    updated_at: str = field(default="", init=False)
    before_state: Dict[str, Any] = field(default_factory=dict)
    after_state: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.pk = f"AUDIT#{self.entity_id}"
        self.sk = f"TIMESTAMP#{datetime.utcnow().isoformat()}"
        self.entity_type = EntityType.AUDIT.value
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

class DynamoDBRepository:
    """Repository pattern for DynamoDB operations"""
    
    def __init__(self, dynamodb_client):
        self.client = dynamodb_client
    
    def save_hospital(self, hospital: Hospital) -> bool:
        """Save hospital entity"""
        return self.client.put_item(hospital.to_dynamodb_item())
    
    def get_hospital(self, hospital_id: str) -> Optional[Dict[str, Any]]:
        """Get hospital by ID"""
        return self.client.get_item(f"HOSPITAL#{hospital_id}", "METADATA")
    
    def save_patient(self, patient: Patient) -> bool:
        """Save patient entity"""
        return self.client.put_item(patient.to_dynamodb_item())
    
    def get_patient(self, hospital_id: str, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        return self.client.get_item(f"HOSPITAL#{hospital_id}", f"PATIENT#{patient_id}")
    
    def get_patients_by_hospital(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Get all patients for a hospital"""
        return self.client.query_items(f"HOSPITAL#{hospital_id}", "PATIENT#")
    
    def save_policy(self, policy: Policy) -> bool:
        """Save policy entity"""
        item = policy.to_dynamodb_item()
        # Add GSI attributes for policy queries
        item['GSI1PK'] = f"POLICY#{policy.policy_id}"
        item['GSI1SK'] = policy.created_at
        return self.client.put_item(item)
    
    def get_policy(self, hospital_id: str, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get policy by ID"""
        return self.client.get_item(f"HOSPITAL#{hospital_id}", f"POLICY#{policy_id}")
    
    def get_policies_by_hospital(self, hospital_id: str) -> List[Dict[str, Any]]:
        """Get all policies for a hospital"""
        return self.client.query_items(f"HOSPITAL#{hospital_id}", "POLICY#")
    
    def save_claim(self, claim: Claim) -> bool:
        """Save claim entity"""
        item = claim.to_dynamodb_item()
        # Add GSI attributes for claim queries
        item['GSI1PK'] = f"RISK#{claim.risk_level}"
        item['GSI1SK'] = claim.created_at
        item['GSI2PK'] = f"HOSPITAL#{claim.hospital_id}"
        item['GSI2SK'] = f"CLAIM#{claim.claim_id}"
        return self.client.put_item(item)
    
    def get_claim(self, patient_id: str, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get claim by ID"""
        return self.client.get_item(f"PATIENT#{patient_id}", f"CLAIM#{claim_id}")
    
    def get_claims_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a patient"""
        return self.client.query_items(f"PATIENT#{patient_id}", "CLAIM#")
    
    def get_claims_by_risk_level(self, risk_level: str) -> List[Dict[str, Any]]:
        """Get claims by risk level using GSI1"""
        # This would use GSI1 query
        # Implementation depends on your DynamoDB client wrapper
        pass
    
    def save_claim_item(self, claim_item: ClaimItem) -> bool:
        """Save claim item entity"""
        return self.client.put_item(claim_item.to_dynamodb_item())
    
    def get_claim_items(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get all items for a claim"""
        return self.client.query_items(f"CLAIM#{claim_id}", "ITEM#")
    
    def save_audit_trail(self, audit: AuditTrail) -> bool:
        """Save audit trail entity"""
        return self.client.put_item(audit.to_dynamodb_item())
    
    def get_audit_trail(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for an entity"""
        return self.client.query_items(f"AUDIT#{entity_id}")

def create_sample_data():
    """Create sample data for testing"""
    
    # Sample Hospital
    hospital = Hospital(
        hospital_id="hosp_001",
        org_name="City General Hospital",
        license_key="CGH-2024-001",
        total_claims_processed=1250,
        subscription_tier="premium",
        contact_email="admin@citygeneral.com",
        contact_phone="+1-555-0123",
        address="123 Medical Center Dr, Healthcare City, HC 12345"
    )
    
    # Sample Patient
    patient = Patient(
        patient_id="pat_001",
        hospital_id="hosp_001",
        name="John Doe",
        age=45,
        policy_number="POL123456789",
        insurer_name="HealthCare Plus Insurance",
        admit_date="2024-01-15T08:30:00Z",
        active_policies=["pol_001"],
        medical_history={"diabetes": True, "hypertension": False}
    )
    
    # Sample Policy
    policy = Policy(
        policy_id="pol_001",
        hospital_id="hosp_001",
        policy_name="HealthCare Plus Premium Policy",
        file_size=2048576,  # 2MB
        content_type="application/pdf",
        s3_key="policies/hosp_001/pol_001.pdf",
        extraction_status="COMPLETED",
        extracted_rules={
            "room_rent_cap": {
                "type": "percentage",
                "value": 1.0,
                "description": "1% of Sum Insured"
            },
            "copay_conditions": [
                {
                    "procedure_type": "surgery",
                    "copay_percentage": 10.0,
                    "description": "10% copay for surgical procedures"
                }
            ],
            "procedure_exclusions": [
                {
                    "procedure_name": "Cosmetic Surgery",
                    "exclusion_reason": "Not medically necessary",
                    "clause_reference": "Section 4.2.1"
                }
            ]
        },
        extraction_confidence=0.95,
        version=1
    )
    
    # Sample Claim
    claim = Claim(
        claim_id="clm_001",
        patient_id="pat_001",
        hospital_id="hosp_001",
        status=ClaimStatus.AUDITED.value,
        total_amount=15000.0,
        risk_score=75,
        risk_level=RiskLevel.MEDIUM.value,
        predicted_settlement_ratio=0.85,
        audit_results={
            "total_items": 5,
            "approved_items": 4,
            "rejected_items": 1,
            "total_approved_amount": 12750.0,
            "total_rejected_amount": 2250.0
        }
    )
    
    # Sample Claim Items
    claim_items = [
        ClaimItem(
            item_id="item_001",
            claim_id="clm_001",
            description="Room Charges - Deluxe",
            cost=8000.0,
            category="accommodation",
            audit_status=AuditStatus.APPROVED.value,
            procedure_code="ROOM_DELUXE"
        ),
        ClaimItem(
            item_id="item_002",
            claim_id="clm_001",
            description="N95 Mask",
            cost=400.0,
            category="consumables",
            audit_status=AuditStatus.REJECTED.value,
            rejection_reason="Non-medical consumables not covered",
            policy_clause_reference="Section 3.1.5",
            procedure_code="MASK_N95"
        )
    ]
    
    return {
        "hospital": hospital,
        "patient": patient,
        "policy": policy,
        "claim": claim,
        "claim_items": claim_items
    }