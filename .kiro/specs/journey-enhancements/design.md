# Design: User Journey Enhancements

## Overview

This design document outlines the technical architecture and implementation approach for completing the partially implemented user journeys (7-10) and adding missing cross-journey features identified in the User Journey Implementation Status analysis.

**Design Philosophy:**
- Leverage existing infrastructure and patterns
- Maintain consistency with current implementation
- Prioritize security and performance
- Ensure backward compatibility

---

## 1. Authentication System Design

### 1.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  API Gateway │─────▶│   Cognito   │
│   (React)   │◀─────│  (Auth API)  │◀─────│   User Pool │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                      │
       │                     │                      │
       ▼                     ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Session   │      │   Lambda     │      │  DynamoDB   │
│   Storage   │      │  (Auth)      │      │  (Sessions) │
└─────────────┘      └──────────────┘      └─────────────┘
```

### 1.2 Components

#### Frontend Components
- **LoginForm.tsx** - Email/password input with validation
- **MFASetup.tsx** - QR code display and verification
- **MFAChallenge.tsx** - MFA code input during login
- **PasswordReset.tsx** - Password reset request and confirmation
- **SessionManager.tsx** - Session monitoring and renewal

#### Backend Components
- **auth_handler.py** - Lambda function for authentication operations
- **session_manager.py** - Session creation, validation, and expiration
- **mfa_service.py** - MFA setup, verification, and backup codes
- **password_service.py** - Password reset and validation

### 1.3 Data Models

```python
# Session Model
{
    "PK": "SESSION#<session_id>",
    "SK": "METADATA",
    "user_id": "string",
    "role": "string",
    "created_at": "timestamp",
    "expires_at": "timestamp",
    "last_activity": "timestamp",
    "ip_address": "string",
    "user_agent": "string"
}

# MFA Configuration Model
{
    "PK": "USER#<user_id>",
    "SK": "MFA_CONFIG",
    "enabled": "boolean",
    "secret": "encrypted_string",
    "backup_codes": ["encrypted_string"],
    "phone_number": "string (optional)"
}
```

### 1.4 API Endpoints

```yaml
POST /api/auth/login
  Request: { email, password }
  Response: { session_token, requires_mfa, user_info }

POST /api/auth/mfa/verify
  Request: { session_token, mfa_code }
  Response: { session_token, user_info }

POST /api/auth/logout
  Request: { session_token }
  Response: { success }

POST /api/auth/password/reset-request
  Request: { email }
  Response: { success }

POST /api/auth/password/reset-confirm
  Request: { token, new_password }
  Response: { success }

GET /api/auth/session/validate
  Request: { session_token }
  Response: { valid, user_info }
```

### 1.5 Security Measures

- **Password Hashing:** bcrypt with cost factor 12
- **Session Tokens:** 256-bit random tokens, httpOnly cookies
- **MFA Secrets:** Encrypted at rest with AWS KMS
- **Rate Limiting:** 5 failed attempts = 30-minute lockout
- **Token Expiration:** Sessions expire after 8 hours or 30 minutes inactivity

---

## 2. Batch Eligibility Processing Design

### 2.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  API Gateway │─────▶│   Lambda    │
│  (Upload)   │      │              │      │  (Batch)    │
└─────────────┘      └──────────────┘      └─────────────┘
                             │                      │
                             │                      │
                             ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │      S3      │      │   Lambda    │
                     │   (CSV)      │      │ (Eligibility│
                     └──────────────┘      │  Workers)   │
                                           └─────────────┘
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │  DynamoDB   │
                                           │  (Results)  │
                                           └─────────────┘
```

### 2.2 Processing Flow

1. **Upload Phase**
   - User uploads CSV file
   - Frontend validates file size and format
   - File uploaded to S3 with presigned URL
   - Batch job created in DynamoDB

2. **Parsing Phase**
   - Lambda triggered by S3 event
   - CSV parsed and validated
   - Rows split into batches of 10

3. **Processing Phase**
   - Batch Lambda invokes eligibility workers in parallel
   - Each worker processes 10 patients
   - Results written to DynamoDB
   - Progress updated in real-time

4. **Completion Phase**
   - All results aggregated
   - Summary statistics calculated
   - User notified via WebSocket/polling

### 2.3 Components

#### Frontend Components
- **BatchModeToggle.tsx** - Switch between single and batch mode
- **CSVUploader.tsx** - Drag-and-drop CSV upload
- **ColumnMapper.tsx** - Map CSV columns to required fields
- **BatchProgress.tsx** - Real-time progress indicator
- **BatchResults.tsx** - Results table with filtering and export

#### Backend Components
- **batch_eligibility_handler.py** - Main batch orchestrator
- **csv_parser.py** - CSV parsing and validation
- **eligibility_worker.py** - Individual eligibility checks
- **batch_aggregator.py** - Results aggregation and statistics

### 2.4 Data Models

```python
# Batch Job Model
{
    "PK": "BATCH#<batch_id>",
    "SK": "METADATA",
    "user_id": "string",
    "status": "pending|processing|completed|failed",
    "total_rows": "number",
    "processed_rows": "number",
    "successful_rows": "number",
    "failed_rows": "number",
    "created_at": "timestamp",
    "completed_at": "timestamp",
    "s3_key": "string"
}

# Batch Result Model
{
    "PK": "BATCH#<batch_id>",
    "SK": "RESULT#<row_number>",
    "patient_id": "string",
    "procedure_code": "string",
    "coverage_status": "covered|not_covered|partial",
    "coverage_percentage": "number",
    "error": "string (optional)"
}
```

### 2.5 Performance Optimization

- **Parallel Processing:** Up to 10 concurrent Lambda invocations
- **Batch Size:** 10 patients per worker for optimal performance
- **Timeout:** 5 minutes per worker, 15 minutes total
- **Retry Logic:** Failed rows retried up to 3 times
- **Caching:** Policy data cached in Lambda memory

---

## 3. Webhook Configuration UI Design

### 3.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  API Gateway │─────▶│   Lambda    │
│  (Settings) │      │              │      │  (Webhook)  │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │  DynamoDB   │
                                           │  (Webhooks) │
                                           └─────────────┘
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │   External  │
                                           │   Endpoint  │
                                           └─────────────┘
```

### 3.2 Components

#### Frontend Components
- **SettingsLayout.tsx** - Settings page with tabbed navigation
- **WebhookList.tsx** - List of configured webhooks
- **WebhookForm.tsx** - Add/edit webhook configuration
- **WebhookTest.tsx** - Test webhook delivery
- **WebhookActivity.tsx** - Delivery logs and monitoring

#### Backend Components
- **webhook_config_handler.py** - CRUD operations for webhooks
- **webhook_delivery.py** - Webhook delivery with retry logic
- **webhook_test.py** - Test webhook endpoint
- **webhook_logger.py** - Log delivery attempts and responses

### 3.3 Data Models

```python
# Webhook Configuration Model
{
    "PK": "WEBHOOK#<webhook_id>",
    "SK": "CONFIG",
    "name": "string",
    "url": "string",
    "enabled": "boolean",
    "events": ["claim_submitted", "audit_completed", ...],
    "auth_type": "api_key|oauth2",
    "auth_config": {
        "api_key": "encrypted_string",
        # or
        "client_id": "string",
        "client_secret": "encrypted_string",
        "token_url": "string"
    },
    "retry_policy": {
        "max_attempts": 3,
        "backoff_multiplier": 2
    }
}

# Webhook Delivery Log Model
{
    "PK": "WEBHOOK#<webhook_id>",
    "SK": "DELIVERY#<timestamp>",
    "event_type": "string",
    "status": "success|failed",
    "status_code": "number",
    "response_time_ms": "number",
    "payload": "json",
    "response": "string",
    "error": "string (optional)",
    "attempt": "number"
}
```

### 3.4 Webhook Events

```yaml
Events:
  - claim_submitted
  - claim_approved
  - claim_rejected
  - audit_completed
  - high_risk_detected
  - policy_updated
  - policy_expired
  - settlement_completed
```

### 3.5 Delivery Guarantees

- **At-least-once delivery:** Retries ensure delivery
- **Retry Strategy:** Exponential backoff (1s, 2s, 4s)
- **Timeout:** 30 seconds per delivery attempt
- **Circuit Breaker:** Disable webhook after 10 consecutive failures
- **Idempotency:** Include event ID in payload for deduplication

---

## 4. Policy Version Comparison UI Design

### 4.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  API Gateway │─────▶│   Lambda    │
│ (Comparison)│      │              │      │  (Policy)   │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │  DynamoDB   │
                                           │  (Policies) │
                                           └─────────────┘
```

### 4.2 Components

#### Frontend Components
- **VersionSelector.tsx** - Dropdown to select two versions
- **VersionComparison.tsx** - Side-by-side diff view
- **ChangeSummary.tsx** - Summary of changes with counts
- **ImpactAnalysis.tsx** - Impact on claims and settlement ratios
- **RollbackConfirmation.tsx** - Confirmation dialog for rollback

#### Backend Components
- **version_comparison.py** - Compare two policy versions
- **diff_generator.py** - Generate structured diff
- **impact_analyzer.py** - Analyze impact of changes
- **version_rollback.py** - Rollback to previous version

### 4.3 Diff Algorithm

```python
def compare_policies(version1, version2):
    """
    Compare two policy versions and generate structured diff.
    
    Returns:
    {
        "added": [rules added in version2],
        "removed": [rules removed from version1],
        "modified": [
            {
                "rule_id": "string",
                "field": "string",
                "old_value": "any",
                "new_value": "any"
            }
        ],
        "unchanged": [rules that didn't change]
    }
    """
    # Implementation uses deep comparison of policy rules
    # Groups changes by category (coverage, exclusions, limits)
    # Calculates similarity score for modified rules
```

### 4.4 Impact Analysis

```python
def analyze_impact(policy_id, version1, version2):
    """
    Analyze impact of policy changes on active claims.
    
    Returns:
    {
        "affected_claims": number,
        "estimated_settlement_change": percentage,
        "patients_to_notify": [patient_ids],
        "confidence": "high|medium|low",
        "risk_level": "high|medium|low"
    }
    """
    # Query active claims using this policy
    # Simulate audit with both versions
    # Compare settlement ratios
    # Identify patients with significant changes
```

---

## 5. Multi-Claim Risk Patient View Design

### 5.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  API Gateway │─────▶│   Lambda    │
│  (Patient)  │      │              │      │   (Risk)    │
└─────────────┘      └──────────────┘      └─────────────┘
                                                   │
                                                   ▼
                                           ┌─────────────┐
                                           │  DynamoDB   │
                                           │  (Claims)   │
                                           └─────────────┘
```

### 5.2 Components

#### Frontend Components
- **PatientProfile.tsx** - Patient demographics and summary
- **ClaimsList.tsx** - All claims for patient
- **RiskVisualization.tsx** - Risk score with breakdown
- **RiskTrend.tsx** - Risk over time chart
- **RecommendationsList.tsx** - Risk mitigation recommendations

#### Backend Components
- **patient_profile_handler.py** - Patient data aggregation
- **multi_claim_risk.py** - Aggregated risk calculation
- **risk_recommendations.py** - Generate mitigation recommendations
- **risk_trend_analyzer.py** - Calculate risk trends

### 5.3 Risk Aggregation Algorithm

```python
def calculate_aggregated_risk(patient_id):
    """
    Calculate aggregated risk across all patient claims.
    
    Factors:
    - Total claim amount (weight: 0.3)
    - Average settlement ratio (weight: 0.25)
    - Number of high-risk claims (weight: 0.2)
    - Rejection patterns (weight: 0.15)
    - Policy complexity (weight: 0.1)
    
    Returns:
    {
        "risk_score": 0-100,
        "risk_level": "high|medium|low",
        "factors": [
            {
                "name": "string",
                "value": "number",
                "weight": "number",
                "contribution": "number"
            }
        ],
        "trend": "increasing|stable|decreasing"
    }
    """
```

### 5.4 Recommendation Engine

```python
def generate_recommendations(patient_id, risk_factors):
    """
    Generate actionable recommendations to reduce risk.
    
    Returns:
    [
        {
            "priority": "high|medium|low",
            "title": "string",
            "description": "string",
            "action_steps": ["string"],
            "expected_impact": "percentage",
            "effort": "high|medium|low"
        }
    ]
    """
    # Analyze risk factors
    # Match to recommendation templates
    # Prioritize by impact and effort
    # Personalize based on patient history
```

---

## 6. Email Notifications Design

### 6.1 Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Event     │─────▶│   Lambda     │─────▶│  Amazon SES │
│   Source    │      │  (Notifier)  │      │             │
└─────────────┘      └──────────────┘      └─────────────┘
                             │                      │
                             │                      │
                             ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │  DynamoDB    │      │   User      │
                     │ (Preferences)│      │   Email     │
                     └──────────────┘      └─────────────┘
```

### 6.2 Components

#### Frontend Components
- **NotificationPreferences.tsx** - Email notification settings
- **EmailFrequency.tsx** - Frequency selection (immediate, daily, weekly)
- **CategoryToggles.tsx** - Enable/disable by category

#### Backend Components
- **email_notifier.py** - Send email notifications
- **email_template_renderer.py** - Render email templates
- **notification_preferences.py** - Manage user preferences
- **email_digest.py** - Generate daily/weekly digests

### 6.3 Email Templates

```html
<!-- Base Template -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Responsive styles */
        /* Brand colors */
        /* Mobile-friendly layout */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="logo.png" alt="Logo">
        </div>
        <div class="content">
            {{ content }}
        </div>
        <div class="footer">
            <a href="{{ unsubscribe_url }}">Unsubscribe</a>
        </div>
    </div>
</body>
</html>
```

### 6.4 Notification Categories

```yaml
Categories:
  - alerts:
      - high_risk_claim
      - policy_expiration
      - system_alert
  - reports:
      - daily_summary
      - weekly_report
      - monthly_analytics
  - policy_updates:
      - policy_uploaded
      - policy_approved
      - policy_modified
  - claim_status:
      - claim_submitted
      - claim_approved
      - claim_rejected
```

---

## 7. End-to-End Testing Design

### 7.1 Test Infrastructure

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Playwright │─────▶│   Frontend   │─────▶│   Backend   │
│   Runner    │      │  (Test Env)  │      │  (Mocked)   │
└─────────────┘      └──────────────┘      └─────────────┘
       │
       ▼
┌─────────────┐
│   Test      │
│   Reports   │
└─────────────┘
```

### 7.2 Test Structure

```typescript
// tests/e2e/policy-upload.spec.ts
describe('Policy Upload Workflow', () => {
  test('should upload policy and extract data', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@test.com');
    await page.fill('[name="password"]', 'Test123!');
    await page.click('button[type="submit"]');
    
    // Navigate to policies
    await page.click('text=Policies');
    
    // Upload policy
    await page.click('text=Upload Policy');
    await page.setInputFiles('input[type="file"]', 'test-policy.pdf');
    await page.fill('[name="policyName"]', 'Test Policy');
    await page.click('text=Upload');
    
    // Wait for processing
    await page.waitForSelector('text=Processing complete');
    
    // Verify extraction
    await expect(page.locator('text=Confidence: 85%')).toBeVisible();
  });
});
```

### 7.3 Test Coverage

```yaml
Critical Paths:
  - Authentication:
      - Login with valid credentials
      - Login with invalid credentials
      - MFA challenge flow
      - Password reset flow
  
  - Policy Management:
      - Upload policy
      - View policy details
      - Compare versions
      - Rollback version
  
  - Eligibility Check:
      - Single eligibility check
      - Batch eligibility check
      - View coverage results
  
  - Bill Audit:
      - Create bill
      - Submit for audit
      - View results
      - Apply suggestions
  
  - Dashboard:
      - View metrics
      - Filter claims
      - Respond to alerts
  
  - Reports:
      - Generate report
      - Export report
      - Schedule report
```

---

## 8. Correctness Properties

### Property 40: Authentication Security
**Statement:** All authentication operations maintain security invariants.

**Validation:**
- Password hashes never stored in plain text
- Session tokens are cryptographically random
- MFA secrets encrypted at rest
- Failed login attempts properly rate-limited
- Session expiration enforced

### Property 41: Batch Processing Consistency
**Statement:** Batch eligibility processing produces same results as individual checks.

**Validation:**
- For any patient in batch, result matches individual check
- Batch failures don't corrupt results
- Partial batch completion handled correctly
- Results properly associated with batch job

### Property 42: Webhook Delivery Reliability
**Statement:** Webhook deliveries are reliable and idempotent.

**Validation:**
- Failed deliveries retried with exponential backoff
- Successful deliveries logged
- Duplicate deliveries prevented
- Circuit breaker prevents infinite retries

### Property 43: Version Comparison Accuracy
**Statement:** Version comparison correctly identifies all changes.

**Validation:**
- All added rules detected
- All removed rules detected
- All modified rules detected
- No false positives or negatives
- Comparison is symmetric

### Property 44: Risk Aggregation Correctness
**Statement:** Aggregated risk accurately reflects individual claim risks.

**Validation:**
- Aggregated risk increases with high-risk claims
- Risk factors properly weighted
- Risk trends calculated correctly
- Recommendations match risk factors

### Property 45: Email Notification Preferences
**Statement:** Email notifications respect user preferences.

**Validation:**
- Disabled categories don't send emails
- Frequency settings honored
- Unsubscribe links work
- Preferences persist across sessions

### Property 46: E2E Test Reliability
**Statement:** E2E tests are deterministic and reliable.

**Validation:**
- Tests pass consistently
- No flaky tests
- Test data properly isolated
- Cleanup after test completion

---

## 9. API Specifications

### Authentication APIs

```yaml
POST /api/auth/login:
  request:
    email: string
    password: string
  response:
    session_token: string
    requires_mfa: boolean
    user_info: object
  errors:
    401: Invalid credentials
    429: Too many attempts

POST /api/auth/mfa/setup:
  request:
    session_token: string
  response:
    secret: string
    qr_code: string
    backup_codes: array
  errors:
    401: Unauthorized
    409: MFA already enabled

POST /api/auth/mfa/verify:
  request:
    session_token: string
    mfa_code: string
  response:
    session_token: string
    user_info: object
  errors:
    401: Invalid code
    429: Too many attempts
```

### Batch Eligibility APIs

```yaml
POST /api/eligibility/batch:
  request:
    file: multipart/form-data
    column_mapping: object
  response:
    batch_id: string
    total_rows: number
  errors:
    400: Invalid file format
    413: File too large

GET /api/eligibility/batch/{batch_id}:
  response:
    batch_id: string
    status: string
    progress: number
    results: array
  errors:
    404: Batch not found

GET /api/eligibility/batch/{batch_id}/results:
  response:
    results: array
    summary: object
  errors:
    404: Batch not found
```

### Webhook APIs

```yaml
POST /api/webhooks:
  request:
    name: string
    url: string
    events: array
    auth_config: object
  response:
    webhook_id: string
  errors:
    400: Invalid configuration

POST /api/webhooks/{webhook_id}/test:
  response:
    status_code: number
    response_time_ms: number
    response_body: string
  errors:
    404: Webhook not found
    500: Test failed

GET /api/webhooks/{webhook_id}/activity:
  query:
    limit: number
    offset: number
  response:
    deliveries: array
    total: number
  errors:
    404: Webhook not found
```

---

## 10. Database Schema Extensions

### New Tables/Indexes

```python
# Sessions Table (GSI)
GSI_SessionsByUser = {
    "PK": "USER#<user_id>",
    "SK": "SESSION#<session_id>",
    "expires_at": "timestamp"
}

# Batch Jobs Table (GSI)
GSI_BatchJobsByUser = {
    "PK": "USER#<user_id>",
    "SK": "BATCH#<batch_id>",
    "status": "string",
    "created_at": "timestamp"
}

# Webhook Deliveries Table (GSI)
GSI_WebhookDeliveriesByStatus = {
    "PK": "WEBHOOK#<webhook_id>",
    "SK": "STATUS#<status>#<timestamp>",
    "event_type": "string"
}
```

---

## 11. Performance Considerations

### Caching Strategy
- **Session Data:** Cache in Lambda memory for 5 minutes
- **Policy Data:** Cache in Lambda memory for 15 minutes
- **Webhook Configs:** Cache in Lambda memory for 10 minutes
- **User Preferences:** Cache in Lambda memory for 5 minutes

### Optimization Techniques
- **Batch Processing:** Parallel Lambda invocations
- **Database Queries:** Use GSIs for efficient lookups
- **API Responses:** Compress large payloads
- **Frontend:** Lazy load components, code splitting

---

## 12. Monitoring and Observability

### Metrics to Track
- Authentication success/failure rates
- Batch processing completion times
- Webhook delivery success rates
- Version comparison response times
- Email delivery rates
- E2E test pass rates

### Alarms
- Authentication failure rate > 10%
- Batch processing failures > 5%
- Webhook delivery failures > 10%
- Email bounce rate > 5%
- E2E test failures > 1%

---

## 13. Rollout Strategy

### Phase 1: High Priority (Weeks 1-2)
- Authentication system
- Batch eligibility processing
- Webhook configuration UI

### Phase 2: Medium Priority (Weeks 3-4)
- Policy version comparison UI
- Multi-claim risk patient view
- Email notifications

### Phase 3: Testing & Polish (Weeks 5-6)
- E2E testing infrastructure
- Performance optimization
- Documentation updates
- User acceptance testing

---

## 14. Backward Compatibility

### Compatibility Guarantees
- Existing API endpoints unchanged
- Existing data models extended, not modified
- Existing UI components reused where possible
- Existing tests continue to pass

### Migration Strategy
- New features behind feature flags
- Gradual rollout to users
- Rollback plan for each feature
- Data migration scripts tested

---

## Conclusion

This design provides a comprehensive technical blueprint for completing the user journey enhancements. The architecture leverages existing infrastructure, maintains consistency with current patterns, and prioritizes security, performance, and user experience.

**Next Steps:**
1. Review and approve design
2. Create detailed implementation tasks
3. Begin Phase 1 development
4. Iterate based on feedback
