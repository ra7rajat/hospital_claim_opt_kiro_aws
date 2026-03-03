/**
 * Mock Data for Local Development
 * This file contains dummy data for all modules
 */

// Dashboard Data
export const mockDashboardData = {
  metrics: {
    totalClaims: 1247,
    pendingReview: 89,
    highRiskClaims: 23,
    avgProcessingTime: 2.4,
    approvalRate: 87.5,
    rejectionRate: 12.5,
  },
  recentClaims: [
    {
      claim_id: 'CLM-2024-001',
      patient_name: 'John Smith',
      policy_number: 'POL-12345',
      claim_amount: 15000,
      status: 'pending',
      risk_score: 0.75,
      submitted_date: '2024-01-20T10:30:00Z',
    },
    {
      claim_id: 'CLM-2024-002',
      patient_name: 'Sarah Johnson',
      policy_number: 'POL-12346',
      claim_amount: 8500,
      status: 'approved',
      risk_score: 0.25,
      submitted_date: '2024-01-20T09:15:00Z',
    },
    {
      claim_id: 'CLM-2024-003',
      patient_name: 'Michael Brown',
      policy_number: 'POL-12347',
      claim_amount: 22000,
      status: 'high_risk',
      risk_score: 0.92,
      submitted_date: '2024-01-19T16:45:00Z',
    },
  ],
  alerts: [
    {
      alert_id: 'ALT-001',
      type: 'high_risk',
      message: 'High-risk claim detected: CLM-2024-003',
      severity: 'critical',
      timestamp: '2024-01-19T16:50:00Z',
    },
    {
      alert_id: 'ALT-002',
      type: 'policy_expiring',
      message: '15 policies expiring in next 30 days',
      severity: 'warning',
      timestamp: '2024-01-20T08:00:00Z',
    },
  ],
};

// Eligibility Check Data
export const mockEligibilityData = {
  patient_id: 'PAT-12345',
  patient_name: 'John Smith',
  policy_number: 'POL-12345',
  policy_status: 'active',
  coverage_start: '2023-01-01',
  coverage_end: '2024-12-31',
  eligible: true,
  coverage_details: {
    inpatient: { covered: true, limit: 100000, used: 15000 },
    outpatient: { covered: true, limit: 50000, used: 8500 },
    emergency: { covered: true, limit: 25000, used: 0 },
    pharmacy: { covered: true, limit: 10000, used: 2300 },
  },
  deductible: {
    annual: 5000,
    met: 3500,
    remaining: 1500,
  },
};

// Bill Audit Data
export const mockBillAuditData = {
  audit_id: 'AUD-2024-001',
  claim_id: 'CLM-2024-001',
  patient_name: 'John Smith',
  total_billed: 15000,
  total_approved: 13500,
  discrepancies: [
    {
      item: 'MRI Scan',
      billed: 3000,
      approved: 2500,
      reason: 'Exceeds standard rate',
      severity: 'medium',
    },
    {
      item: 'Consultation Fee',
      billed: 500,
      approved: 0,
      reason: 'Not covered under policy',
      severity: 'high',
    },
  ],
  recommendations: [
    'Review MRI pricing with provider',
    'Verify consultation coverage terms',
  ],
  audit_status: 'completed',
  audited_by: 'System',
  audit_date: '2024-01-20T11:00:00Z',
};

// Policy Management Data
export const mockPoliciesData = [
  {
    policy_id: 'POL-12345',
    policy_number: 'POL-12345',
    policy_holder: 'John Smith',
    policy_type: 'Individual Health',
    status: 'active',
    start_date: '2023-01-01',
    end_date: '2024-12-31',
    premium: 5000,
    coverage_amount: 100000,
    version: 2,
    last_updated: '2024-01-15T10:00:00Z',
  },
  {
    policy_id: 'POL-12346',
    policy_number: 'POL-12346',
    policy_holder: 'Sarah Johnson',
    policy_type: 'Family Health',
    status: 'active',
    start_date: '2023-06-01',
    end_date: '2024-05-31',
    premium: 8500,
    coverage_amount: 250000,
    version: 1,
    last_updated: '2023-06-01T09:00:00Z',
  },
  {
    policy_id: 'POL-12347',
    policy_number: 'POL-12347',
    policy_holder: 'Michael Brown',
    policy_type: 'Senior Citizen',
    status: 'expiring_soon',
    start_date: '2023-02-01',
    end_date: '2024-01-31',
    premium: 12000,
    coverage_amount: 150000,
    version: 3,
    last_updated: '2024-01-10T14:30:00Z',
  },
];

// Patient Profile Data
export const mockPatientProfileData = {
  patient_id: 'PAT-12345',
  name: 'John Smith',
  dob: '1985-05-15',
  gender: 'Male',
  contact: {
    email: 'john.smith@email.com',
    phone: '+1-555-0123',
    address: '123 Main St, New York, NY 10001',
  },
  policy_number: 'POL-12345',
  claims: [
    {
      claim_id: 'CLM-2024-001',
      date: '2024-01-20',
      amount: 15000,
      status: 'pending',
      type: 'Inpatient',
      risk_score: 0.75,
    },
    {
      claim_id: 'CLM-2023-089',
      date: '2023-12-15',
      amount: 5000,
      status: 'approved',
      type: 'Outpatient',
      risk_score: 0.15,
    },
    {
      claim_id: 'CLM-2023-067',
      date: '2023-10-08',
      amount: 3500,
      status: 'approved',
      type: 'Emergency',
      risk_score: 0.30,
    },
  ],
  risk_analytics: {
    overall_risk_score: 0.45,
    risk_trend: 'increasing',
    risk_factors: [
      'Multiple high-value claims',
      'Recent hospitalization',
      'Chronic condition indicators',
    ],
    recommendations: [
      'Schedule preventive care consultation',
      'Review medication adherence',
      'Consider wellness program enrollment',
    ],
  },
  claim_history: {
    total_claims: 12,
    total_amount: 45000,
    approved_amount: 38500,
    avg_claim_amount: 3750,
  },
};

// Reports Data
export const mockReportsData = {
  summary: {
    period: 'Last 30 Days',
    total_claims: 342,
    total_amount: 1250000,
    approved_amount: 1087500,
    rejected_amount: 162500,
    avg_processing_time: 2.4,
  },
  claimsByStatus: [
    { status: 'Approved', count: 298, percentage: 87.1 },
    { status: 'Rejected', count: 32, percentage: 9.4 },
    { status: 'Pending', count: 12, percentage: 3.5 },
  ],
  claimsByType: [
    { type: 'Inpatient', count: 145, amount: 750000 },
    { type: 'Outpatient', count: 167, amount: 350000 },
    { type: 'Emergency', count: 30, amount: 150000 },
  ],
  topProcedures: [
    { procedure: 'MRI Scan', count: 45, avg_cost: 2500 },
    { procedure: 'Blood Tests', count: 89, avg_cost: 150 },
    { procedure: 'X-Ray', count: 67, avg_cost: 200 },
  ],
  riskDistribution: [
    { range: 'Low (0-0.3)', count: 245, percentage: 71.6 },
    { range: 'Medium (0.3-0.7)', count: 74, percentage: 21.6 },
    { range: 'High (0.7-1.0)', count: 23, percentage: 6.7 },
  ],
};

// Audit Logs Data
export const mockAuditLogsData = [
  {
    log_id: 'LOG-001',
    timestamp: '2024-01-20T14:30:00Z',
    user: 'admin@hospital.com',
    action: 'POLICY_UPDATE',
    resource: 'POL-12345',
    details: 'Updated policy coverage limits',
    ip_address: '192.168.1.100',
    status: 'success',
  },
  {
    log_id: 'LOG-002',
    timestamp: '2024-01-20T14:15:00Z',
    user: 'doctor@hospital.com',
    action: 'ELIGIBILITY_CHECK',
    resource: 'PAT-12345',
    details: 'Checked eligibility for patient',
    ip_address: '192.168.1.101',
    status: 'success',
  },
  {
    log_id: 'LOG-003',
    timestamp: '2024-01-20T13:45:00Z',
    user: 'billing@hospital.com',
    action: 'CLAIM_SUBMIT',
    resource: 'CLM-2024-001',
    details: 'Submitted new claim for review',
    ip_address: '192.168.1.102',
    status: 'success',
  },
  {
    log_id: 'LOG-004',
    timestamp: '2024-01-20T13:30:00Z',
    user: 'admin@hospital.com',
    action: 'LOGIN_FAILED',
    resource: 'N/A',
    details: 'Failed login attempt - invalid password',
    ip_address: '192.168.1.200',
    status: 'failed',
  },
];

// Batch Processing Data
export const mockBatchData = {
  batch_id: 'BATCH-2024-001',
  status: 'processing',
  total_records: 150,
  processed: 87,
  successful: 82,
  failed: 5,
  started_at: '2024-01-20T10:00:00Z',
  estimated_completion: '2024-01-20T10:15:00Z',
  results: [
    {
      row: 1,
      patient_id: 'PAT-001',
      patient_name: 'Alice Williams',
      policy_number: 'POL-001',
      eligible: true,
      status: 'success',
    },
    {
      row: 2,
      patient_id: 'PAT-002',
      patient_name: 'Bob Davis',
      policy_number: 'POL-002',
      eligible: false,
      status: 'success',
      reason: 'Policy expired',
    },
    {
      row: 3,
      patient_id: 'PAT-003',
      patient_name: 'Carol Martinez',
      policy_number: 'INVALID',
      eligible: false,
      status: 'error',
      reason: 'Invalid policy number',
    },
  ],
};

// Webhooks Data
export const mockWebhooksData = [
  {
    webhook_id: 'WH-001',
    name: 'Production Webhook',
    url: 'https://api.example.com/webhook',
    description: 'Main production webhook for claim events',
    enabled: true,
    events: ['claim_submitted', 'claim_approved', 'high_risk_detected'],
    auth_type: 'api_key',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  {
    webhook_id: 'WH-002',
    name: 'Audit Webhook',
    url: 'https://audit.example.com/webhook',
    description: 'Webhook for audit and compliance events',
    enabled: true,
    events: ['audit_completed', 'policy_updated'],
    auth_type: 'oauth2',
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
  },
];

// Notification Preferences Data
export const mockNotificationPreferences = {
  email: 'user@hospital.com',
  frequency: 'immediate',
  categories: {
    alerts: true,
    reports: true,
    policy_updates: true,
    claim_status: false,
  },
};

// User Profile Data
export const mockUserProfile = {
  user_id: 'USR-001',
  name: 'Admin User',
  email: 'admin@hospital.com',
  role: 'Admin',
  department: 'Claims Management',
  created_at: '2023-01-01T00:00:00Z',
  last_login: '2024-01-20T09:00:00Z',
  mfa_enabled: true,
};

// Version Comparison Data
export const mockVersionComparisonData = {
  policy_id: 'POL-12345',
  versions: [
    {
      version: 2,
      created_at: '2024-01-15T10:00:00Z',
      created_by: 'admin@hospital.com',
      changes: ['Increased coverage limit', 'Added dental coverage'],
      status: 'active',
    },
    {
      version: 1,
      created_at: '2023-01-01T00:00:00Z',
      created_by: 'admin@hospital.com',
      changes: ['Initial policy creation'],
      status: 'archived',
    },
  ],
  comparison: {
    coverage_limit: { v1: 100000, v2: 150000, change: '+50%' },
    premium: { v1: 5000, v2: 5500, change: '+10%' },
    dental_coverage: { v1: false, v2: true, change: 'Added' },
  },
};

// Generate more dummy patients
export const generateMockPatients = (count: number) => {
  const firstNames = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'William', 'Mary'];
  const lastNames = ['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson'];
  
  return Array.from({ length: count }, (_, i) => ({
    patient_id: `PAT-${String(i + 1).padStart(5, '0')}`,
    name: `${firstNames[i % firstNames.length]} ${lastNames[i % lastNames.length]}`,
    dob: `19${60 + (i % 40)}-${String((i % 12) + 1).padStart(2, '0')}-15`,
    policy_number: `POL-${String(i + 1).padStart(5, '0')}`,
    status: i % 10 === 0 ? 'inactive' : 'active',
  }));
};

// Generate more dummy claims
export const generateMockClaims = (count: number) => {
  const statuses = ['pending', 'approved', 'rejected', 'high_risk'];
  const types = ['Inpatient', 'Outpatient', 'Emergency', 'Pharmacy'];
  
  return Array.from({ length: count }, (_, i) => ({
    claim_id: `CLM-2024-${String(i + 1).padStart(3, '0')}`,
    patient_name: `Patient ${i + 1}`,
    policy_number: `POL-${String(i + 1).padStart(5, '0')}`,
    claim_amount: Math.floor(Math.random() * 50000) + 1000,
    status: statuses[i % statuses.length],
    type: types[i % types.length],
    risk_score: Math.random(),
    submitted_date: new Date(2024, 0, Math.floor(Math.random() * 20) + 1).toISOString(),
  }));
};
