# Hospital Claim Optimizer - Engineering Quick Reference

**Complete Technical Documentation:** See `TECHNICAL_DOCUMENTATION.md` for full details

---

## Quick Links

- [Full Technical Docs](./TECHNICAL_DOCUMENTATION.md)
- [User Guide](./USER_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [API Specification](./hospital-claim-optimizer/openapi.yaml)

---

## System Architecture Summary

**Type:** Serverless, Event-Driven, Microservices  
**Cloud Provider:** AWS  
**Frontend:** React + TypeScript + Vite  
**Backend:** Python 3.11 Lambda Functions  
**Database:** DynamoDB (NoSQL)  
**Cache:** ElastiCache (Redis)  
**CDN:** CloudFront  
**IaC:** AWS CDK (TypeScript)

---

## Component Inventory

### Frontend Components (30+)
**Location:** `frontend/src/`

**Pages (8):**
- `pages/Login.tsx`
- `pages/admin/Dashboard.tsx`
- `pages/admin/PolicyManagement.tsx`
- `pages/admin/Reports.tsx`
- `pages/admin/AuditLogs.tsx`
- `pages/admin/Settings.tsx`
- `pages/doctor/EligibilityCheck.tsx`
- `pages/billing/BillAudit.tsx`
- `pages/billing/PatientProfile.tsx`

**UI Components (6):**
- `components/ui/alert.tsx`
- `components/ui/button.tsx`
- `components/ui/card.tsx`
- `components/ui/input.tsx`
- `components/ui/label.tsx`
- `components/ui/tabs.tsx`

**Feature Components (20+):**
- Authentication: MFA, Password Reset, Session Manager
- Batch: CSV Uploader, Column Mapper, Progress, Results
- Patient: Claims List, Risk Visualization, Analytics
- Settings: Profile, Notifications, Webhooks
- Version: Comparison, Impact Analysis, Rollback
- Policy: Upload, Search, List

### Backend Services (28 modules)
**Location:** `hospital-claim-optimizer/lambda-layers/common/python/`

**Core (4):**
- `common_utils.py` - Utilities
- `data_models.py` - Pydantic models
- `database_access.py` - DynamoDB ops
- `api_middleware.py` - Request handling

**Auth (5):**
- `auth_middleware.py`
- `session_manager.py`
- `mfa_service.py`
- `password_service.py`
- `security_config.py`

**Policy (4):**
- `policy_service.py`
- `version_comparison_service.py`
- `impact_analysis_service.py`
- `version_rollback_service.py`

**Analytics (5):**
- `multi_claim_analytics_service.py`
- `patient_profile_service.py`
- `reporting_service.py`
- `alert_service.py`
- `audit_service.py`

**Notifications (4):**
- `email_notification_service.py`
- `notification_preferences_service.py`
- `email_templates.py`
- `webhook_delivery_service.py`

**Others (6):**
- `audit_logger.py`
- `risk_recommendation_service.py`
- `batch_results_service.py`
- `cache_service.py`
- `performance_monitor.py`

### Lambda Functions (14)
**Location:** `hospital-claim-optimizer/lambda-functions/`

1. `auth/auth_handler.py` - Authentication
2. `policy-management/policy_management.py` - Policy CRUD
3. `policy-upload/policy_upload.py` - Policy upload & AI extraction
4. `eligibility-checker/eligibility_check.py` - Real-time eligibility
5. `batch-eligibility/batch_orchestrator.py` - Batch coordinator
6. `batch-eligibility/eligibility_worker.py` - Batch worker
7. `batch-eligibility/csv_parser.py` - CSV parsing
8. `bill-audit/bill_audit.py` - Bill auditing
9. `risk-scorer/risk_scorer.py` - Risk assessment
10. `dashboard/dashboard.py` - Dashboard metrics
11. `reports/reports.py` - Report generation
12. `audit-logs/audit_logs.py` - Audit logging
13. `patient-profile/patient_profile.py` - Patient data
14. `webhook-config/webhook_config.py` - Webhook management

### AWS Resources

**Compute:**
- 14 Lambda Functions
- 1 Lambda Layer

**Storage:**
- 6 DynamoDB Tables
- 3 S3 Buckets
- 1 ElastiCache Cluster

**Networking:**
- 1 API Gateway
- 1 CloudFront Distribution
- VPC (optional)

**Security:**
- IAM Roles & Policies
- Secrets Manager
- KMS Keys

**Monitoring:**
- CloudWatch Logs
- CloudWatch Metrics
- CloudWatch Alarms

---

## API Endpoints

**Base URL:** `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `POST /auth/mfa/setup` - Setup MFA
- `POST /auth/mfa/verify` - Verify MFA
- `POST /auth/password/change` - Change password
- `POST /auth/password/reset` - Reset password

### Policy Management
- `GET /policies` - List policies
- `GET /policies/{id}` - Get policy
- `POST /policy` - Upload policy
- `PUT /policies/{id}` - Update policy
- `DELETE /policies/{id}` - Delete policy
- `GET /policies/{id}/versions` - Version history
- `POST /policies/{id}/compare` - Compare versions

### Eligibility
- `POST /check-eligibility` - Single check
- `POST /batch-eligibility` - Batch check
- `GET /batch-eligibility/{id}` - Batch status

### Claims
- `POST /audit-claim` - Audit claim
- `POST /risk-score` - Calculate risk
- `GET /patient/{id}` - Patient profile
- `GET /patient/{id}/claims` - Patient claims

### Dashboard & Reports
- `GET /dashboard` - Dashboard data
- `POST /reports/generate` - Generate report
- `GET /reports/{id}` - Get report

### Admin
- `GET /audit-logs` - Audit logs
- `GET /webhooks` - List webhooks
- `POST /webhooks` - Create webhook
- `PUT /webhooks/{id}` - Update webhook
- `DELETE /webhooks/{id}` - Delete webhook

---

## Database Schema

### Users Table
```
PK: user_id
Attributes: email, password_hash, role, hospital_id, mfa_enabled
GSI: email-index
```

### Policies Table
```
PK: policy_id
SK: version
Attributes: policy_name, hospital_id, rules, confidence_score
GSI: hospital-index, status-index
```

### Claims Table
```
PK: claim_id
Attributes: patient_id, hospital_id, policy_id, amount, risk_level
GSI: patient-index, hospital-index, status-index
```

### Sessions Table
```
PK: session_id
TTL: expires_at
Attributes: user_id, created_at, last_activity
```

### Audit Logs Table
```
PK: log_id
SK: timestamp
Attributes: user_id, action, resource_type, changes
GSI: user-index, resource-index
```

### Webhooks Table
```
PK: webhook_id
Attributes: name, url, events, auth_config, enabled
```

---

## Configuration Files

### Frontend
- `frontend/vite.config.ts` - Vite configuration
- `frontend/tsconfig.json` - TypeScript config
- `frontend/tailwind.config.js` - Tailwind CSS
- `frontend/package.json` - Dependencies
- `frontend/.env.example` - Environment variables

### Backend
- `hospital-claim-optimizer/cdk.json` - CDK config
- `hospital-claim-optimizer/package.json` - CDK dependencies
- `hospital-claim-optimizer/tsconfig.json` - TypeScript config
- `hospital-claim-optimizer/lib/hospital-claim-optimizer-stack.ts` - Infrastructure

### Testing
- `e2e/playwright.config.ts` - E2E test config
- `hospital-claim-optimizer/tests/` - Property-based tests (25 files)

---

## Environment Variables

### Frontend (.env)
```
VITE_API_BASE_URL=https://api.example.com
VITE_APP_ENV=development|production
```

### Lambda Functions
```
USER_TABLE_NAME=hospital-claim-optimizer-users
SESSION_TABLE_NAME=hospital-claim-optimizer-sessions
POLICY_TABLE_NAME=hospital-claim-optimizer-policies
CLAIMS_TABLE_NAME=hospital-claim-optimizer-claims
AUDIT_TABLE_NAME=hospital-claim-optimizer-audit-logs
WEBHOOKS_TABLE_NAME=hospital-claim-optimizer-webhooks

POLICY_BUCKET=hospital-claim-optimizer-policies-{account}
BATCH_BUCKET=hospital-claim-optimizer-batch-{account}

REDIS_ENDPOINT=cache-cluster.xxxxx.cache.amazonaws.com:6379

JWT_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:jwt-secret
MFA_SECRET_KEY_ARN=arn:aws:secretsmanager:region:account:secret:mfa-key

SES_FROM_EMAIL=noreply@example.com
SES_REGION=us-east-1
```

---

## Testing

### Unit Tests (Python)
**Location:** `hospital-claim-optimizer/tests/`  
**Framework:** Pytest  
**Count:** 25 test files

**Run:**
```bash
cd hospital-claim-optimizer
pytest tests/
```

### Property-Based Tests
**Framework:** Hypothesis  
**Files:**
- `test_property_authentication.py`
- `test_property_mfa.py`
- `test_property_password.py`
- `test_property_policy_processing.py`
- `test_property_eligibility_checking.py`
- `test_property_bill_audit.py`
- `test_property_risk_assessment.py`
- `test_property_batch_processing.py`
- `test_property_webhooks.py`
- `test_property_email_notifications.py`
- And 15 more...

### E2E Tests (Playwright)
**Location:** `e2e/tests/`  
**Count:** 7 test files

**Run:**
```bash
cd e2e
npx playwright test
```

**Tests:**
- `auth.spec.ts` - Authentication flows
- `eligibility-check.spec.ts` - Eligibility checking
- `bill-audit.spec.ts` - Bill auditing
- `policy-management.spec.ts` - Policy management
- `dashboard.spec.ts` - Dashboard
- `reports.spec.ts` - Reports
- `test-reliability.spec.ts` - Reliability tests

---

## Deployment

### Prerequisites
- AWS Account with admin access
- AWS CLI configured
- Node.js 18+ and npm
- Python 3.11+
- AWS CDK CLI installed

### Deploy Backend
```bash
cd hospital-claim-optimizer
npm install
cdk bootstrap  # First time only
cdk deploy
```

### Deploy Frontend
```bash
cd frontend
npm install
npm run build
aws s3 sync dist/ s3://frontend-bucket/
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

### Full Deployment Script
```bash
./hospital-claim-optimizer/deploy.sh
```

---

## Monitoring

### CloudWatch Metrics
- Lambda invocations
- Lambda errors
- Lambda duration
- API Gateway requests
- API Gateway latency
- DynamoDB read/write capacity
- ElastiCache CPU/memory

### CloudWatch Alarms
- Lambda error rate > 1%
- API Gateway 5xx errors > 10
- DynamoDB throttling
- ElastiCache memory > 80%

### Logs
- Lambda logs: `/aws/lambda/{function-name}`
- API Gateway logs: `/aws/apigateway/{api-id}`

---

## Development Workflow

### Local Development

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

**Backend (Local Testing):**
```bash
cd hospital-claim-optimizer
python -m pytest tests/
```

### Git Workflow
1. Create feature branch from `main`
2. Implement changes
3. Run tests locally
4. Commit with descriptive message
5. Push and create PR
6. Code review
7. Merge to `main`
8. Auto-deploy (CI/CD)

### Code Standards
- **Frontend:** ESLint + Prettier
- **Backend:** Black + Flake8
- **Commits:** Conventional Commits format

---

## Troubleshooting

### Common Issues

**Frontend won't start:**
- Check Node.js version (18+)
- Delete `node_modules` and reinstall
- Check for port conflicts (5173)

**Lambda timeout:**
- Increase timeout in CDK stack
- Check DynamoDB capacity
- Review CloudWatch logs

**API Gateway 403:**
- Check IAM permissions
- Verify API key/auth token
- Check CORS configuration

**DynamoDB throttling:**
- Switch to on-demand billing
- Increase provisioned capacity
- Implement caching

**Cache miss rate high:**
- Increase TTL values
- Review cache key strategy
- Check ElastiCache memory

---

## Security Best Practices

1. **Never commit secrets** - Use Secrets Manager
2. **Use least privilege IAM** - Minimal permissions
3. **Enable MFA** - For all admin users
4. **Encrypt at rest** - All S3 and DynamoDB
5. **Encrypt in transit** - HTTPS only
6. **Regular audits** - Review audit logs
7. **Dependency updates** - Keep packages current
8. **Input validation** - Validate all inputs
9. **Rate limiting** - API Gateway throttling
10. **Backup strategy** - DynamoDB point-in-time recovery

---

## Support & Contacts

**Technical Lead:** [Name]  
**DevOps Lead:** [Name]  
**QA Lead:** [Name]  

**Slack Channels:**
- `#claim-optimizer-dev` - Development
- `#claim-optimizer-ops` - Operations
- `#claim-optimizer-alerts` - Alerts

**Documentation:**
- Technical Docs: `TECHNICAL_DOCUMENTATION.md`
- User Guide: `USER_GUIDE.md`
- API Spec: `openapi.yaml`
- Deployment: `DEPLOYMENT_GUIDE.md`

---

**Last Updated:** January 24, 2026  
**Version:** 1.0
