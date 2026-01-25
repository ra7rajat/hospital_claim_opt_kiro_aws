# Hospital Insurance Claim Settlement Optimizer - Technical Documentation

**Version:** 1.0  
**Last Updated:** January 24, 2026  
**Product Name:** RevenueZ Hospital Claim Optimizer  
**Document Type:** Engineering Source of Truth

---

## Document Purpose

This document serves as the single source of truth for all engineering teams:
- Backend Engineers
- Frontend Engineers
- QA/Testing Teams
- DevOps/Infrastructure Teams
- Technical Architects

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [AWS Infrastructure](#4-aws-infrastructure)
5. [Backend Services](#5-backend-services)
6. [Frontend Application](#6-frontend-application)
7. [API Documentation](#7-api-documentation)
8. [Database Schema](#8-database-schema)
9. [Authentication & Security](#9-authentication--security)
10. [Configuration Management](#10-configuration-management)
11. [Testing Strategy](#11-testing-strategy)
12. [Deployment](#12-deployment)
13. [Monitoring & Observability](#13-monitoring--observability)
14. [Development Workflow](#14-development-workflow)
15. [Troubleshooting](#15-troubleshooting)

---


## 1. System Overview

### 1.1 Product Description

RevenueZ Hospital Claim Optimizer is an AI-powered B2B SaaS platform designed to maximize hospital insurance claim settlement ratios through:
- Intelligent policy document analysis
- Real-time eligibility checking
- Automated bill auditing
- Risk assessment and recommendations

### 1.2 Key Metrics

- Target Settlement Ratio: 85%+ (from industry average of ~70%)
- Processing Time Reduction: 60%
- Real-time Eligibility Check: < 2 seconds
- Batch Processing: ~30 seconds for 100 patients
- Policy Processing: 3-5 minutes per document

### 1.3 User Roles

1. **TPA Administrator** - Full system access, policy management
2. **Hospital Administrator** - Hospital-level access, reporting
3. **Billing Staff** - Claim creation and management
4. **Doctor** - Eligibility checking only

### 1.4 Core Features

- Policy upload and AI extraction
- Real-time and batch eligibility checking
- Bill audit with optimization suggestions
- Risk scoring and analytics
- Multi-claim patient analytics
- Policy version management
- Webhook integrations
- Email notifications
- Comprehensive audit logging

---


## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Browser    │  │   Mobile     │  │  External    │          │
│  │   (React)    │  │   (Future)   │  │  Systems     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CDN & Edge Layer                            │
│                    CloudFront + S3                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│              REST API + WebSocket (Future)                       │
│              Authentication & Rate Limiting                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Lambda Functions (14 handlers)               │  │
│  │  • Auth  • Policy  • Eligibility  • Audit  • Reports     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Lambda Layers (Common Services)                 │  │
│  │  • Data Models  • Auth  • Policy  • Notifications        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   DynamoDB   │  │      S3      │  │  ElastiCache │          │
│  │  (NoSQL DB)  │  │  (Storage)   │  │   (Cache)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     SES      │  │   EventBridge│  │   Webhooks   │          │
│  │   (Email)    │  │   (Events)   │  │  (External)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Patterns

**Serverless Architecture**
- Event-driven, auto-scaling Lambda functions
- Pay-per-use pricing model
- No server management overhead

**Microservices Pattern**
- Each Lambda function handles specific domain
- Loose coupling via API Gateway
- Independent deployment and scaling

**CQRS (Command Query Responsibility Segregation)**
- Separate read and write operations
- Optimized data models for queries
- Event sourcing for audit trails

**Cache-Aside Pattern**
- ElastiCache for frequently accessed data
- Reduces database load
- Improves response times

---


## 3. Technology Stack

### 3.1 Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | 5.6.2 | Type safety |
| Vite | 6.0.5 | Build tool & dev server |
| React Router | 7.1.3 | Client-side routing |
| TanStack Query | 5.62.11 | Server state management |
| Recharts | 2.15.0 | Data visualization |
| Tailwind CSS | 3.4.17 | Styling framework |
| Lucide React | 0.469.0 | Icon library |
| Axios | 1.7.9 | HTTP client |

**Build Configuration:**
- Path aliases: `@/*` → `./src/*`
- Code splitting by feature
- Terser minification
- Console.log removal in production
- Chunk size limit: 1000KB

### 3.2 Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Lambda runtime |
| AWS CDK | 2.x | Infrastructure as Code |
| TypeScript | 5.x | CDK language |
| Boto3 | Latest | AWS SDK for Python |
| Hypothesis | Latest | Property-based testing |
| Pytest | Latest | Unit testing |

### 3.3 AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| Lambda | Compute | Python 3.11, 512MB-3GB memory |
| API Gateway | REST API | Regional, CORS enabled |
| DynamoDB | Database | On-demand billing, GSI enabled |
| S3 | Storage | Versioning, encryption at rest |
| CloudFront | CDN | HTTPS only, edge caching |
| ElastiCache | Caching | Redis 7.x, cluster mode |
| SES | Email | DKIM, SPF configured |
| EventBridge | Events | Custom event bus |
| CloudWatch | Monitoring | Logs, metrics, alarms |
| IAM | Security | Least privilege policies |
| Secrets Manager | Secrets | Auto-rotation enabled |
| KMS | Encryption | Customer managed keys |

### 3.4 Development Tools

| Tool | Purpose |
|------|---------|
| Git | Version control |
| npm | Package management (frontend) |
| pip | Package management (backend) |
| ESLint | JavaScript linting |
| Prettier | Code formatting |
| Playwright | E2E testing |
| AWS CLI | AWS operations |
| CDK CLI | Infrastructure deployment |

---


## 4. AWS Infrastructure

### 4.1 Infrastructure as Code (CDK)

**Stack Definition:** `hospital-claim-optimizer-stack.ts`

```typescript
// Location: hospital-claim-optimizer/lib/hospital-claim-optimizer-stack.ts
// Defines all AWS resources using AWS CDK
```

**Key Resources:**
- 14 Lambda Functions
- 1 Lambda Layer (common services)
- 1 API Gateway REST API
- 6 DynamoDB Tables
- 3 S3 Buckets
- 1 CloudFront Distribution
- 1 ElastiCache Cluster
- Multiple IAM Roles and Policies

### 4.2 Lambda Functions

#### 4.2.1 Authentication Handler
**Path:** `lambda-functions/auth/auth_handler.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh
- POST /auth/mfa/setup
- POST /auth/mfa/verify
- POST /auth/password/change
- POST /auth/password/reset

**Environment Variables:**
- `USER_TABLE_NAME`
- `SESSION_TABLE_NAME`
- `JWT_SECRET_ARN`
- `MFA_SECRET_KEY_ARN`

#### 4.2.2 Policy Management Handler
**Path:** `lambda-functions/policy-management/policy_management.py`  
**Memory:** 1024MB  
**Timeout:** 60s  
**Endpoints:**
- GET /policies
- GET /policies/{id}
- PUT /policies/{id}
- DELETE /policies/{id}
- GET /policies/{id}/versions
- POST /policies/{id}/compare

**Dependencies:**
- policy_service.py
- version_comparison_service.py
- impact_analysis_service.py

#### 4.2.3 Policy Upload Handler
**Path:** `lambda-functions/policy-upload/policy_upload.py`  
**Memory:** 3008MB (max for AI processing)  
**Timeout:** 300s (5 minutes)  
**Endpoints:**
- POST /policy

**Process Flow:**
1. Upload PDF to S3
2. Extract text using Textract
3. AI analysis for policy rules
4. Structure data into DynamoDB
5. Generate confidence scores

#### 4.2.4 Eligibility Checker Handler
**Path:** `lambda-functions/eligibility-checker/eligibility_check.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- POST /check-eligibility

**Response Time:** < 2 seconds

#### 4.2.5 Batch Eligibility Handlers
**Orchestrator:** `lambda-functions/batch-eligibility/batch_orchestrator.py`  
**Worker:** `lambda-functions/batch-eligibility/eligibility_worker.py`  
**Parser:** `lambda-functions/batch-eligibility/csv_parser.py`  

**Memory:** 1024MB  
**Timeout:** 300s  
**Max Batch Size:** 100 patients

**Process Flow:**
1. Upload CSV to S3
2. Parse and validate CSV
3. Spawn parallel workers (up to 10)
4. Aggregate results
5. Store in DynamoDB
6. Return summary

#### 4.2.6 Bill Audit Handler
**Path:** `lambda-functions/bill-audit/bill_audit.py`  
**Memory:** 1024MB  
**Timeout:** 60s  
**Endpoints:**
- POST /audit-claim

**Audit Checks:**
- Policy coverage validation
- Procedure code verification
- Pricing reasonableness
- Documentation completeness
- Pre-authorization requirements

#### 4.2.7 Risk Scorer Handler
**Path:** `lambda-functions/risk-scorer/risk_scorer.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- POST /risk-score

**Risk Factors:**
- Claim amount vs. policy limits
- Historical rejection patterns
- Documentation quality
- Procedure complexity
- Patient history

#### 4.2.8 Dashboard Handler
**Path:** `lambda-functions/dashboard/dashboard.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- GET /dashboard

**Metrics Provided:**
- Total claims count
- Average CSR
- High-risk claims
- Processing time
- Cost savings

#### 4.2.9 Reports Handler
**Path:** `lambda-functions/reports/reports.py`  
**Memory:** 1024MB  
**Timeout:** 120s  
**Endpoints:**
- POST /reports/generate
- GET /reports/{id}

**Report Types:**
- Settlement ratio analysis
- Rejection patterns
- Hospital performance
- Procedure analysis
- Time-series trends

#### 4.2.10 Audit Logs Handler
**Path:** `lambda-functions/audit-logs/audit_logs.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- GET /audit-logs
- GET /audit-logs/{id}

**Logged Events:**
- User authentication
- Policy changes
- Claim submissions
- Configuration updates
- Data access

#### 4.2.11 Patient Profile Handler
**Path:** `lambda-functions/patient-profile/patient_profile.py`  
**Memory:** 512MB  
**Timeout:** 30s  
**Endpoints:**
- GET /patient/{id}
- GET /patient/{id}/claims
- GET /patient/{id}/analytics

**Data Provided:**
- Patient demographics
- Claim history
- Risk trends
- Multi-claim analytics
- Recommendations

#### 4.2.12 Webhook Config Handler
**Path:** `lambda-functions/webhook-config/webhook_config.py`  
**Memory:** 256MB  
**Timeout:** 30s  
**Endpoints:**
- GET /webhooks
- POST /webhooks
- PUT /webhooks/{id}
- DELETE /webhooks/{id}
- POST /webhooks/{id}/test

**Supported Events:**
- claim.submitted
- audit.completed
- risk.high
- policy.updated
- settlement.completed

### 4.3 Lambda Layer

**Path:** `lambda-layers/common/python/`  
**Size:** ~50MB  
**Python Version:** 3.11

**Included Modules (28 files):**

1. **Core Services:**
   - `common_utils.py` - Shared utilities
   - `data_models.py` - Pydantic models
   - `database_access.py` - DynamoDB operations
   - `api_middleware.py` - Request/response handling

2. **Authentication:**
   - `auth_middleware.py` - JWT validation
   - `session_manager.py` - Session handling
   - `mfa_service.py` - MFA operations
   - `password_service.py` - Password management
   - `security_config.py` - Security settings

3. **Policy Services:**
   - `policy_service.py` - Policy CRUD
   - `version_comparison_service.py` - Version diff
   - `impact_analysis_service.py` - Change impact
   - `version_rollback_service.py` - Rollback logic

4. **Audit & Risk:**
   - `audit_service.py` - Bill auditing
   - `audit_logger.py` - Audit trail
   - `risk_recommendation_service.py` - Risk analysis

5. **Analytics:**
   - `multi_claim_analytics_service.py` - Patient analytics
   - `patient_profile_service.py` - Profile data
   - `reporting_service.py` - Report generation
   - `alert_service.py` - Alert management

6. **Batch Processing:**
   - `batch_results_service.py` - Batch results

7. **Notifications:**
   - `email_notification_service.py` - Email sending
   - `notification_preferences_service.py` - User preferences
   - `email_templates.py` - Email templates
   - `webhook_delivery_service.py` - Webhook delivery

8. **Performance:**
   - `cache_service.py` - Redis caching
   - `performance_monitor.py` - Performance tracking

### 4.4 DynamoDB Tables

#### 4.4.1 Users Table
**Name:** `hospital-claim-optimizer-users`  
**Partition Key:** `user_id` (String)  
**Attributes:**
- email (String)
- password_hash (String)
- role (String)
- hospital_id (String)
- mfa_enabled (Boolean)
- mfa_secret (String, encrypted)
- created_at (Number)
- updated_at (Number)

**GSI:**
- `email-index`: email (PK)

#### 4.4.2 Sessions Table
**Name:** `hospital-claim-optimizer-sessions`  
**Partition Key:** `session_id` (String)  
**TTL:** `expires_at`  
**Attributes:**
- user_id (String)
- created_at (Number)
- last_activity (Number)
- ip_address (String)
- user_agent (String)

#### 4.4.3 Policies Table
**Name:** `hospital-claim-optimizer-policies`  
**Partition Key:** `policy_id` (String)  
**Sort Key:** `version` (Number)  
**Attributes:**
- policy_name (String)
- hospital_id (String)
- effective_date (String)
- expiration_date (String)
- status (String)
- confidence_score (Number)
- rules (Map)
- created_by (String)
- created_at (Number)

**GSI:**
- `hospital-index`: hospital_id (PK), effective_date (SK)
- `status-index`: status (PK)

#### 4.4.4 Claims Table
**Name:** `hospital-claim-optimizer-claims`  
**Partition Key:** `claim_id` (String)  
**Attributes:**
- patient_id (String)
- hospital_id (String)
- policy_id (String)
- claim_amount (Number)
- risk_level (String)
- status (String)
- line_items (List)
- audit_results (Map)
- created_at (Number)
- updated_at (Number)

**GSI:**
- `patient-index`: patient_id (PK), created_at (SK)
- `hospital-index`: hospital_id (PK), created_at (SK)
- `status-index`: status (PK), created_at (SK)

#### 4.4.5 Audit Logs Table
**Name:** `hospital-claim-optimizer-audit-logs`  
**Partition Key:** `log_id` (String)  
**Sort Key:** `timestamp` (Number)  
**Attributes:**
- user_id (String)
- action (String)
- resource_type (String)
- resource_id (String)
- changes (Map)
- ip_address (String)
- user_agent (String)

**GSI:**
- `user-index`: user_id (PK), timestamp (SK)
- `resource-index`: resource_id (PK), timestamp (SK)

#### 4.4.6 Webhooks Table
**Name:** `hospital-claim-optimizer-webhooks`  
**Partition Key:** `webhook_id` (String)  
**Attributes:**
- name (String)
- url (String)
- events (List)
- auth_type (String)
- auth_config (Map, encrypted)
- enabled (Boolean)
- created_at (Number)
- last_triggered (Number)

### 4.5 S3 Buckets

#### 4.5.1 Policy Documents Bucket
**Name:** `hospital-claim-optimizer-policies-{account-id}`  
**Versioning:** Enabled  
**Encryption:** AES-256  
**Lifecycle:**
- Transition to IA after 90 days
- Transition to Glacier after 365 days

**Structure:**
```
/policies/
  /{policy_id}/
    /original/
      policy.pdf
    /versions/
      /v1/
        extracted_text.txt
        structured_data.json
      /v2/
        ...
```

#### 4.5.2 Batch Processing Bucket
**Name:** `hospital-claim-optimizer-batch-{account-id}`  
**Versioning:** Disabled  
**Encryption:** AES-256  
**Lifecycle:**
- Delete after 30 days

**Structure:**
```
/uploads/
  /{batch_id}/
    input.csv
/results/
  /{batch_id}/
    results.csv
    summary.json
```

#### 4.5.3 Frontend Assets Bucket
**Name:** `hospital-claim-optimizer-frontend-{account-id}`  
**Versioning:** Enabled  
**Encryption:** AES-256  
**Public Access:** Via CloudFront only

**Structure:**
```
/assets/
  /js/
  /css/
  /images/
index.html
```

### 4.6 ElastiCache Configuration

**Cluster Name:** `hospital-claim-optimizer-cache`  
**Engine:** Redis 7.x  
**Node Type:** cache.t3.micro (dev), cache.r6g.large (prod)  
**Nodes:** 2 (primary + replica)  
**Encryption:** In-transit and at-rest enabled  
**Multi-AZ:** Enabled for high availability  
**Automatic Failover:** Enabled  
**Backup Retention:** 7 days  
**Maintenance Window:** Sunday 03:00-04:00 UTC  

**Configuration:**
```
Max Memory Policy: allkeys-lru
Max Memory: 1GB (dev), 16GB (prod)
Timeout: 300 seconds
TCP Keepalive: 300 seconds
```

**Cached Data:**
- Policy rules (TTL: 1 hour)
- User sessions (TTL: 30 minutes)
- Eligibility results (TTL: 5 minutes)
- Dashboard metrics (TTL: 5 minutes)
- Frequently accessed patient data (TTL: 15 minutes)

**Performance:**
- Cache hit ratio target: >90%
- Average latency: <1ms
- Throughput: 100K ops/sec (prod)

### 4.7 Cognito Configuration

#### User Pool Settings
**Pool Name:** `hospital-claim-optimizer-users`  
**Pool ID:** `us-east-1_xxxxxxxxx`  
**Region:** us-east-1  

**Password Policy:**
- Minimum length: 12 characters
- Require uppercase: Yes
- Require lowercase: Yes
- Require numbers: Yes
- Require symbols: Yes
- Temporary password validity: 7 days

**MFA Configuration:**
- MFA enforcement: Optional (user choice)
- MFA methods: TOTP (Time-based One-Time Password)
- Software token MFA: Enabled
- SMS MFA: Disabled (cost optimization)

**Account Recovery:**
- Email verification: Required
- Phone verification: Optional
- Recovery methods: Email only

**User Attributes:**
- Standard: email (required), name, phone_number
- Custom: hospital_id, role, department

**Email Configuration:**
- Provider: Amazon SES
- From address: noreply@yourdomain.com
- Reply-to: support@yourdomain.com

#### App Client Settings
**Client Name:** `hospital-claim-optimizer-web`  
**Client ID:** `xxxxxxxxxxxxxxxxxxxxxxxxxx`  

**Authentication Flows:**
- USER_PASSWORD_AUTH: Enabled
- REFRESH_TOKEN_AUTH: Enabled
- CUSTOM_AUTH: Disabled

**Token Validity:**
- ID Token: 1 hour
- Access Token: 1 hour
- Refresh Token: 30 days

**OAuth 2.0 Settings:**
- Allowed OAuth Flows: Authorization code grant
- Allowed OAuth Scopes: openid, email, profile
- Callback URLs: https://yourdomain.com/callback
- Sign out URLs: https://yourdomain.com/logout

#### Identity Pool (Optional)
**Pool Name:** `hospital_claim_optimizer_identity`  
**Allow unauthenticated access:** No  
**Authentication providers:** Cognito User Pool  

**IAM Roles:**
- Authenticated role: Limited S3 access for file uploads
- Unauthenticated role: None

### 4.8 API Gateway Configuration

**API Name:** `hospital-claim-optimizer-api`  
**API Type:** REST API  
**Endpoint Type:** Regional  
**Stage:** prod  

**Throttling Settings:**
- Rate limit: 10,000 requests/second
- Burst limit: 5,000 requests
- Per-method throttling: Enabled for expensive operations

**Usage Plans:**
- **Basic Plan:**
  - Rate: 1,000 requests/second
  - Burst: 500 requests
  - Quota: 1,000,000 requests/month
  
- **Premium Plan:**
  - Rate: 5,000 requests/second
  - Burst: 2,000 requests
  - Quota: 10,000,000 requests/month

**API Keys:**
- Enabled for external integrations
- Rotation: Every 90 days
- Associated with usage plans

**CORS Configuration:**
```json
{
  "allowOrigins": ["https://yourdomain.com"],
  "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  "allowHeaders": ["Content-Type", "Authorization", "X-Api-Key"],
  "exposeHeaders": ["X-Request-Id"],
  "maxAge": 3600,
  "allowCredentials": true
}
```

**Request Validation:**
- Body validation: Enabled
- Query string validation: Enabled
- Headers validation: Enabled

**Logging:**
- CloudWatch Logs: Enabled
- Log level: INFO (prod), DEBUG (dev)
- Data trace: Disabled (prod), Enabled (dev)
- Metrics: Enabled

**Caching:**
- Cache cluster size: 0.5 GB (prod only)
- Cache TTL: 300 seconds
- Encryption: Enabled
- Per-key invalidation: Enabled

### 4.9 VPC Configuration

**VPC Name:** `hospital-claim-optimizer-vpc`  
**CIDR Block:** 10.0.0.0/16  
**Region:** us-east-1  
**Availability Zones:** us-east-1a, us-east-1b, us-east-1c  

**Subnets:**

**Public Subnets:**
- 10.0.1.0/24 (us-east-1a) - NAT Gateway, Bastion
- 10.0.2.0/24 (us-east-1b) - NAT Gateway
- 10.0.3.0/24 (us-east-1c) - NAT Gateway

**Private Subnets (Lambda):**
- 10.0.11.0/24 (us-east-1a) - Lambda functions
- 10.0.12.0/24 (us-east-1b) - Lambda functions
- 10.0.13.0/24 (us-east-1c) - Lambda functions

**Private Subnets (Data):**
- 10.0.21.0/24 (us-east-1a) - ElastiCache, RDS (if used)
- 10.0.22.0/24 (us-east-1b) - ElastiCache, RDS (if used)
- 10.0.23.0/24 (us-east-1c) - ElastiCache, RDS (if used)

**Internet Gateway:**
- Attached to VPC
- Routes to public subnets

**NAT Gateways:**
- 3 NAT Gateways (one per AZ)
- Elastic IPs assigned
- Routes from private subnets

**Security Groups:**

**Lambda Security Group:**
- Inbound: None (Lambda initiated only)
- Outbound: All traffic to 0.0.0.0/0

**ElastiCache Security Group:**
- Inbound: Port 6379 from Lambda SG
- Outbound: None

**VPC Endpoints:**
- DynamoDB: Gateway endpoint (no cost)
- S3: Gateway endpoint (no cost)
- Secrets Manager: Interface endpoint
- CloudWatch Logs: Interface endpoint

### 4.10 CloudFront Distribution

**Distribution ID:** `E1XXXXXXXXXX`  
**Origin:** S3 Frontend Bucket  
**Price Class:** All edge locations  
**SSL Certificate:** ACM certificate (*.yourdomain.com)  
**HTTP Version:** HTTP/2 and HTTP/3  
**IPv6:** Enabled  

**Origins:**
1. **S3 Origin (Frontend):**
   - Origin Domain: hospital-claim-optimizer-frontend-xxxxx.s3.amazonaws.com
   - Origin Access: Origin Access Identity (OAI)
   - Origin Protocol: HTTPS only

2. **API Gateway Origin (Backend):**
   - Origin Domain: xxxxx.execute-api.us-east-1.amazonaws.com
   - Origin Path: /prod
   - Origin Protocol: HTTPS only

**Cache Behaviors:**
- **Default (/):**
  - Target: S3 Origin
  - Viewer Protocol: Redirect HTTP to HTTPS
  - Allowed Methods: GET, HEAD, OPTIONS
  - Cache Policy: CachingOptimized
  - Compress: Yes

- **API (/api/*):**
  - Target: API Gateway Origin
  - Viewer Protocol: HTTPS only
  - Allowed Methods: All
  - Cache Policy: CachingDisabled
  - Origin Request Policy: AllViewer

**Caching:**
- HTML: No cache (Cache-Control: no-cache)
- JS/CSS: 1 year (Cache-Control: max-age=31536000)
- Images: 1 year (Cache-Control: max-age=31536000)
- API responses: No cache

**Error Pages:**
- 403: /index.html (SPA routing)
- 404: /index.html (SPA routing)

**Geo Restrictions:**
- Type: None (available worldwide)
- Whitelist/Blacklist: Not configured

**WAF Integration:**
- AWS WAF: Enabled
- Rules: SQL injection, XSS protection, rate limiting

### 4.11 IAM Roles & Policies

#### Lambda Execution Role
**Role Name:** `hospital-claim-optimizer-lambda-role`  
**Permissions:**
- DynamoDB: Read/Write on all tables
- S3: Read/Write on all buckets
- ElastiCache: Connect
- SES: SendEmail, SendRawEmail
- CloudWatch: PutMetricData, CreateLogGroup, CreateLogStream, PutLogEvents
- Secrets Manager: GetSecretValue
- KMS: Decrypt, Encrypt
- VPC: CreateNetworkInterface, DescribeNetworkInterfaces, DeleteNetworkInterface
- X-Ray: PutTraceSegments, PutTelemetryRecords

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

#### API Gateway Role
**Role Name:** `hospital-claim-optimizer-apigateway-role`  
**Permissions:**
- Lambda: InvokeFunction
- CloudWatch: PutMetricData, CreateLogGroup, CreateLogStream, PutLogEvents

#### CloudFront Role
**Role Name:** `hospital-claim-optimizer-cloudfront-role`  
**Permissions:**
- S3: GetObject on frontend bucket (via OAI)

#### Cognito Authenticated Role
**Role Name:** `hospital-claim-optimizer-cognito-auth-role`  
**Permissions:**
- S3: PutObject on specific upload paths
- API Gateway: Execute-api on specific endpoints

### 4.12 Cost Estimation

**Monthly AWS Costs (Estimated):**

**Development Environment:**
- Lambda: $20-50 (low usage)
- DynamoDB: $10-25 (on-demand)
- S3: $5-10
- ElastiCache: $15 (t3.micro)
- API Gateway: $10-20
- CloudFront: $5-15
- Cognito: $0-5 (free tier)
- **Total: ~$65-140/month**

**Production Environment (1000 users, 100K requests/day):**
- Lambda: $200-400
- DynamoDB: $100-200 (on-demand)
- S3: $20-50
- ElastiCache: $150-300 (r6g.large)
- API Gateway: $100-200
- CloudFront: $50-100
- Cognito: $50-100
- Data Transfer: $50-100
- CloudWatch: $20-50
- **Total: ~$740-1,500/month**

**Cost Optimization Tips:**
- Use Reserved Instances for ElastiCache (save 30-50%)
- Enable S3 Intelligent-Tiering
- Use DynamoDB reserved capacity for predictable workloads
- Implement Lambda function optimization (memory, timeout)
- Enable CloudFront compression
- Use S3 lifecycle policies for old data

---


## 5. Backend Services

### 5.1 Service Layer Architecture

All backend services are located in the Lambda Layer for code reuse across Lambda functions.

**Location:** `hospital-claim-optimizer/lambda-layers/common/python/`

### 5.2 Core Services

#### 5.2.1 Common Utils (`common_utils.py`)
**Purpose:** Shared utility functions

**Key Functions:**
- `generate_id()` - UUID generation
- `format_date()` - Date formatting
- `validate_email()` - Email validation
- `sanitize_input()` - Input sanitization
- `calculate_hash()` - SHA-256 hashing
- `encrypt_data()` - AES encryption
- `decrypt_data()` - AES decryption

#### 5.2.2 Data Models (`data_models.py`)
**Purpose:** Pydantic models for data validation

**Models:**
- `User` - User entity
- `Policy` - Policy entity
- `Claim` - Claim entity
- `Patient` - Patient entity
- `AuditLog` - Audit log entry
- `Webhook` - Webhook configuration
- `Session` - User session
- `Notification` - Notification entity

**Example:**
```python
class Policy(BaseModel):
    policy_id: str
    policy_name: str
    hospital_id: str
    version: int
    effective_date: date
    expiration_date: date
    status: PolicyStatus
    rules: Dict[str, Any]
    confidence_score: float
```

#### 5.2.3 Database Access (`database_access.py`)
**Purpose:** DynamoDB operations wrapper

**Key Functions:**
- `get_item(table, key)` - Get single item
- `put_item(table, item)` - Create/update item
- `query(table, key_condition)` - Query with conditions
- `scan(table, filter)` - Scan table
- `batch_get(table, keys)` - Batch get items
- `batch_write(table, items)` - Batch write items
- `delete_item(table, key)` - Delete item
- `update_item(table, key, updates)` - Update attributes

**Features:**
- Automatic retry with exponential backoff
- Connection pooling
- Error handling and logging
- Pagination support

#### 5.2.4 API Middleware (`api_middleware.py`)
**Purpose:** Request/response handling

**Functions:**
- `parse_request(event)` - Parse API Gateway event
- `build_response(status, body)` - Build API response
- `validate_request(schema)` - Request validation
- `handle_error(error)` - Error response formatting
- `add_cors_headers(response)` - CORS headers
- `log_request(event)` - Request logging

**Response Format:**
```python
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    },
    "body": json.dumps({
        "success": True,
        "data": {...},
        "message": "Success"
    })
}
```

### 5.3 Authentication Services

#### 5.3.1 Auth Middleware (`auth_middleware.py`)
**Purpose:** JWT token validation and authorization

**Functions:**
- `validate_token(token)` - Validate JWT
- `decode_token(token)` - Decode JWT payload
- `check_permissions(user, resource)` - Permission check
- `require_auth(handler)` - Decorator for protected endpoints
- `require_role(roles)` - Role-based access control

**JWT Structure:**
```python
{
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "admin",
    "hospital_id": "hosp-123",
    "exp": 1234567890,
    "iat": 1234567890
}
```

#### 5.3.2 Session Manager (`session_manager.py`)
**Purpose:** User session management

**Functions:**
- `create_session(user_id)` - Create new session
- `get_session(session_id)` - Retrieve session
- `update_activity(session_id)` - Update last activity
- `invalidate_session(session_id)` - End session
- `cleanup_expired()` - Remove expired sessions

**Session Lifecycle:**
- Active: 8 hours
- Inactivity timeout: 30 minutes
- Remember me: 30 days

#### 5.3.3 MFA Service (`mfa_service.py`)
**Purpose:** Multi-factor authentication

**Functions:**
- `generate_secret()` - Generate TOTP secret
- `generate_qr_code(secret)` - QR code for setup
- `verify_totp(secret, code)` - Verify TOTP code
- `generate_backup_codes()` - Generate backup codes
- `verify_backup_code(user_id, code)` - Verify backup code

**TOTP Configuration:**
- Algorithm: SHA1
- Digits: 6
- Period: 30 seconds
- Window: ±1 period

#### 5.3.4 Password Service (`password_service.py`)
**Purpose:** Password management

**Functions:**
- `hash_password(password)` - Bcrypt hashing
- `verify_password(password, hash)` - Verify password
- `validate_strength(password)` - Strength check
- `generate_reset_token()` - Password reset token
- `verify_reset_token(token)` - Verify reset token

**Password Requirements:**
- Minimum 12 characters
- Uppercase, lowercase, number, special char
- No common passwords
- No password reuse (last 5)

#### 5.3.5 Security Config (`security_config.py`)
**Purpose:** Security settings and constants

**Configuration:**
- JWT secret key (from Secrets Manager)
- Token expiration times
- Password policy rules
- Rate limiting thresholds
- CORS allowed origins
- Encryption keys

---


### 5.4 Policy Services

#### 5.4.1 Policy Service (`policy_service.py`)
**Purpose:** Policy CRUD operations

**Functions:**
- `create_policy(data)` - Create new policy
- `get_policy(policy_id, version)` - Get policy version
- `update_policy(policy_id, updates)` - Update policy
- `delete_policy(policy_id)` - Soft delete policy
- `list_policies(filters)` - List with filters
- `search_policies(query)` - Full-text search
- `get_active_policies(hospital_id)` - Active policies

**Policy Processing:**
1. PDF upload to S3
2. Textract OCR extraction
3. AI analysis (rule extraction)
4. Data structuring
5. Confidence scoring
6. DynamoDB storage

#### 5.4.2 Version Comparison Service (`version_comparison_service.py`)
**Purpose:** Compare policy versions

**Functions:**
- `compare_versions(v1, v2)` - Detailed comparison
- `get_diff(v1, v2)` - Diff algorithm
- `highlight_changes(diff)` - Change highlighting
- `generate_summary(diff)` - Change summary

**Comparison Output:**
```python
{
    "added_rules": [...],
    "removed_rules": [...],
    "modified_rules": [...],
    "unchanged_rules": [...]
}
```

#### 5.4.3 Impact Analysis Service (`impact_analysis_service.py`)
**Purpose:** Analyze impact of policy changes

**Functions:**
- `analyze_impact(old_version, new_version)` - Impact analysis
- `get_affected_claims(changes)` - Find affected claims
- `estimate_csr_impact(changes)` - CSR impact
- `identify_risks(changes)` - Risk identification

**Impact Metrics:**
- Number of active claims affected
- Estimated CSR change
- Patients requiring notification
- Confidence level

#### 5.4.4 Version Rollback Service (`version_rollback_service.py`)
**Purpose:** Rollback policy versions

**Functions:**
- `rollback_version(policy_id, target_version)` - Rollback
- `validate_rollback(policy_id, version)` - Validation
- `create_rollback_version(policy_id)` - New version
- `notify_stakeholders(policy_id)` - Notifications

**Rollback Process:**
1. Validate target version exists
2. Check for dependent claims
3. Create new version (not delete)
4. Update active version pointer
5. Notify affected users
6. Log audit trail

### 5.5 Analytics Services

#### 5.5.1 Multi-Claim Analytics Service (`multi_claim_analytics_service.py`)
**Purpose:** Patient multi-claim analysis

**Functions:**
- `analyze_patient_claims(patient_id)` - Aggregate analysis
- `calculate_risk_trend(claims)` - Risk over time
- `identify_patterns(claims)` - Pattern detection
- `generate_insights(analytics)` - AI insights

**Analytics Provided:**
- Total claims count
- Average claim amount
- Risk trend (increasing/decreasing)
- Common procedures
- Settlement success rate
- Recommendations

#### 5.5.2 Patient Profile Service (`patient_profile_service.py`)
**Purpose:** Patient profile management

**Functions:**
- `get_patient_profile(patient_id)` - Full profile
- `get_claim_history(patient_id)` - Claim history
- `get_risk_score(patient_id)` - Current risk
- `get_recommendations(patient_id)` - Recommendations

**Profile Data:**
- Demographics
- Insurance information
- Claim history
- Risk scores
- Analytics
- Recommendations

#### 5.5.3 Reporting Service (`reporting_service.py`)
**Purpose:** Report generation

**Functions:**
- `generate_report(type, params)` - Generate report
- `get_report(report_id)` - Retrieve report
- `export_report(report_id, format)` - Export (PDF/CSV)
- `schedule_report(config)` - Scheduled reports

**Report Types:**
- Settlement ratio analysis
- Rejection patterns
- Hospital performance
- Procedure analysis
- Time-series trends
- Custom reports

#### 5.5.4 Alert Service (`alert_service.py`)
**Purpose:** Alert management

**Functions:**
- `create_alert(type, data)` - Create alert
- `get_alerts(user_id)` - User alerts
- `mark_read(alert_id)` - Mark as read
- `dismiss_alert(alert_id)` - Dismiss alert

**Alert Types:**
- High-risk claim detected
- Policy expiration warning
- Processing complete
- Error notifications
- System alerts

### 5.6 Audit Services

#### 5.6.1 Audit Service (`audit_service.py`)
**Purpose:** Bill auditing logic

**Functions:**
- `audit_claim(claim_data)` - Audit claim
- `check_coverage(procedure, policy)` - Coverage check
- `validate_pricing(amount, procedure)` - Price validation
- `check_documentation(claim)` - Doc completeness
- `generate_recommendations(audit)` - Optimization tips

**Audit Checks:**
1. Policy coverage validation
2. Procedure code verification
3. Pricing reasonableness
4. Documentation completeness
5. Pre-authorization requirements
6. Exclusion checks
7. Limit validations

**Audit Result:**
```python
{
    "claim_id": "CLM-123",
    "risk_level": "Medium",
    "settlement_ratio": 0.87,
    "approved_items": 45,
    "rejected_items": 5,
    "review_items": 3,
    "recommendations": [...]
}
```

#### 5.6.2 Audit Logger (`audit_logger.py`)
**Purpose:** Audit trail logging

**Functions:**
- `log_action(user, action, resource)` - Log action
- `log_change(user, resource, changes)` - Log changes
- `log_access(user, resource)` - Log access
- `query_logs(filters)` - Query logs

**Logged Events:**
- User authentication
- Policy changes
- Claim submissions
- Configuration updates
- Data access
- System events

### 5.7 Notification Services

#### 5.7.1 Email Notification Service (`email_notification_service.py`)
**Purpose:** Email sending via SES

**Functions:**
- `send_email(to, subject, body)` - Send email
- `send_template_email(to, template, data)` - Template email
- `send_bulk_email(recipients, template)` - Bulk send
- `track_delivery(message_id)` - Delivery tracking

**Email Types:**
- Welcome email
- Password reset
- MFA setup
- Alert notifications
- Report ready
- Policy updates

#### 5.7.2 Notification Preferences Service (`notification_preferences_service.py`)
**Purpose:** User notification preferences

**Functions:**
- `get_preferences(user_id)` - Get preferences
- `update_preferences(user_id, prefs)` - Update
- `check_enabled(user_id, type)` - Check if enabled

**Preference Options:**
- Email notifications (on/off)
- Alert types to receive
- Frequency (immediate/daily/weekly)
- Quiet hours

#### 5.7.3 Email Templates (`email_templates.py`)
**Purpose:** Email template management

**Templates:**
- `welcome_template` - Welcome email
- `password_reset_template` - Password reset
- `mfa_setup_template` - MFA setup
- `alert_template` - Alert notification
- `report_ready_template` - Report ready
- `policy_update_template` - Policy update

**Template Variables:**
- `{{user_name}}` - User name
- `{{link}}` - Action link
- `{{date}}` - Date
- `{{details}}` - Specific details

#### 5.7.4 Webhook Delivery Service (`webhook_delivery_service.py`)
**Purpose:** Webhook delivery

**Functions:**
- `deliver_webhook(webhook_id, event, data)` - Deliver
- `retry_failed(delivery_id)` - Retry delivery
- `get_delivery_status(delivery_id)` - Status
- `log_delivery(webhook_id, status)` - Log

**Delivery Process:**
1. Get webhook configuration
2. Build payload
3. Sign payload (HMAC-SHA256)
4. HTTP POST to URL
5. Handle response
6. Retry on failure (3 attempts)
7. Log delivery

**Webhook Payload:**
```python
{
    "event": "claim.submitted",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {...},
    "webhook_id": "WHK-001"
}
```

### 5.8 Performance Services

#### 5.8.1 Cache Service (`cache_service.py`)
**Purpose:** Redis caching operations

**Functions:**
- `get(key)` - Get cached value
- `set(key, value, ttl)` - Set cache
- `delete(key)` - Delete cache
- `exists(key)` - Check existence
- `increment(key)` - Increment counter
- `get_many(keys)` - Batch get

**Cached Data:**
- Policy rules (TTL: 1 hour)
- User sessions (TTL: 30 min)
- Eligibility results (TTL: 5 min)
- Dashboard metrics (TTL: 5 min)

**Cache Keys:**
- `policy:{policy_id}:{version}`
- `session:{session_id}`
- `eligibility:{patient_id}:{procedure}`
- `dashboard:{hospital_id}`

#### 5.8.2 Performance Monitor (`performance_monitor.py`)
**Purpose:** Performance tracking

**Functions:**
- `start_timer(operation)` - Start timing
- `end_timer(operation)` - End timing
- `log_metric(name, value)` - Log metric
- `track_error(error)` - Track error

**Metrics Tracked:**
- Lambda execution time
- Database query time
- Cache hit/miss rate
- API response time
- Error rates

### 5.9 Batch Processing Services

#### 5.9.1 Batch Results Service (`batch_results_service.py`)
**Purpose:** Batch processing results

**Functions:**
- `store_results(batch_id, results)` - Store results
- `get_results(batch_id)` - Get results
- `get_summary(batch_id)` - Get summary
- `export_results(batch_id, format)` - Export

**Result Structure:**
```python
{
    "batch_id": "BATCH-123",
    "total_patients": 100,
    "processed": 100,
    "fully_covered": 75,
    "partially_covered": 20,
    "not_covered": 5,
    "errors": 0,
    "processing_time": 28.5,
    "results": [...]
}
```

---


## 6. Frontend Application

### 6.1 Application Structure

```
frontend/src/
├── components/          # Reusable components
│   ├── ui/             # Base UI components
│   ├── batch/          # Batch processing
│   ├── patient/        # Patient components
│   ├── settings/       # Settings components
│   └── version/        # Version management
├── pages/              # Page components
│   ├── admin/          # Admin pages
│   ├── doctor/         # Doctor pages
│   └── billing/        # Billing pages
├── lib/                # Utilities
│   ├── api.ts          # API client
│   ├── queryClient.ts  # React Query config
│   └── utils.ts        # Helper functions
├── types/              # TypeScript types
├── router.tsx          # Route configuration
└── main.tsx            # Application entry

```

### 6.2 UI Components

#### 6.2.1 Base UI Components (`components/ui/`)

**Alert (`alert.tsx`):**
- Purpose: Display notifications and messages
- Variants: default, destructive
- Components: Alert, AlertDescription, AlertTitle

**Button (`button.tsx`):**
- Purpose: Interactive buttons
- Variants: default, destructive, outline, secondary, ghost, link
- Sizes: default, sm, lg, icon

**Card (`card.tsx`):**
- Purpose: Content containers
- Components: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter

**Input (`input.tsx`):**
- Purpose: Text input fields
- Types: text, password, email, number, etc.
- Features: Validation, error states

**Label (`label.tsx`):**
- Purpose: Form labels
- Features: Accessibility support

**Tabs (`tabs.tsx`):**
- Purpose: Tabbed navigation
- Components: Tabs, TabsList, TabsTrigger, TabsContent

### 6.3 Feature Components

#### 6.3.1 Authentication Components

**Login (`pages/Login.tsx`):**
- Email/password login
- Remember me option
- Password reset link
- MFA challenge redirect

**MFA Challenge (`components/MFAChallenge.tsx`):**
- TOTP code input
- Backup code option
- Resend code
- Trust device option

**MFA Setup (`components/MFASetup.tsx`):**
- QR code display
- Manual entry option
- Verification
- Backup codes download

**MFA Management (`components/MFAManagement.tsx`):**
- Enable/disable MFA
- Regenerate backup codes
- View trusted devices

**Password Reset (`components/PasswordReset.tsx`):**
- Email input
- Reset link sending
- Success confirmation

**Password Reset Confirm (`components/PasswordResetConfirm.tsx`):**
- New password input
- Password strength indicator
- Confirmation

**Password Change (`components/PasswordChange.tsx`):**
- Current password verification
- New password input
- Strength validation

**Session Manager (`components/SessionManager.tsx`):**
- Session timeout warning
- Auto-logout
- Session extension

#### 6.3.2 Policy Components

**Policy Upload (`components/PolicyUpload.tsx`):**
- Drag-and-drop upload
- File validation
- Progress tracking
- Metadata input

**Policy List (`components/PolicyList.tsx`):**
- Paginated list
- Sorting and filtering
- Status indicators
- Quick actions

**Policy Search (`components/PolicySearch.tsx`):**
- Full-text search
- Advanced filters
- Search suggestions

#### 6.3.3 Batch Processing Components

**CSV Uploader (`components/batch/CSVUploader.tsx`):**
- File upload
- Template download
- File validation
- Preview

**Column Mapper (`components/batch/ColumnMapper.tsx`):**
- Column mapping UI
- Auto-detection
- Manual mapping
- Validation

**Batch Progress (`components/batch/BatchProgress.tsx`):**
- Real-time progress
- Status updates
- Cancel option
- ETA display

**Batch Results (`components/batch/BatchResults.tsx`):**
- Results table
- Summary statistics
- Filtering
- Export options

#### 6.3.4 Patient Components

**Claims List (`components/patient/ClaimsList.tsx`):**
- Patient claims table
- Status indicators
- Amount display
- Detail view

**Risk Visualization (`components/patient/RiskVisualization.tsx`):**
- Risk gauge chart
- Color-coded levels
- Trend indicator

**Risk Trend (`components/patient/RiskTrend.tsx`):**
- Line chart
- Historical data
- Trend analysis

**Multi-Claim Analytics (`components/patient/MultiClaimAnalytics.tsx`):**
- Aggregate statistics
- Pattern analysis
- Insights display

**Recommendations List (`components/patient/RecommendationsList.tsx`):**
- Action items
- Priority indicators
- Implementation tips

#### 6.3.5 Settings Components

**Profile Settings (`components/settings/ProfileSettings.tsx`):**
- User information
- Password change
- MFA management
- Preferences

**Notification Settings (`components/settings/NotificationSettings.tsx`):**
- Email preferences
- Alert types
- Frequency settings
- Quiet hours

**Webhook Settings (`components/settings/WebhookSettings.tsx`):**
- Webhook list
- Add/edit webhooks
- Test webhooks
- Activity log

#### 6.3.6 Version Management Components

**Version Selector (`components/version/VersionSelector.tsx`):**
- Version dropdown
- Version details
- Comparison option

**Version Comparison (`components/version/VersionComparison.tsx`):**
- Side-by-side diff
- Change highlighting
- Navigation

**Change Summary (`components/version/ChangeSummary.tsx`):**
- Added/removed/modified
- Statistics
- Quick overview

**Impact Analysis (`components/version/ImpactAnalysis.tsx`):**
- Affected claims
- CSR impact
- Risk assessment

**Rollback Confirmation (`components/version/RollbackConfirmation.tsx`):**
- Confirmation dialog
- Impact warning
- Reason input

### 6.4 Pages

#### 6.4.1 Admin Pages (`pages/admin/`)

**Dashboard (`Dashboard.tsx`):**
- Key metrics cards
- Charts and graphs
- Recent activity
- Alerts panel

**Policy Management (`PolicyManagement.tsx`):**
- Policy list
- Upload interface
- Search and filter
- Version management

**Reports (`Reports.tsx`):**
- Report generation
- Report history
- Export options
- Scheduled reports

**Audit Logs (`AuditLogs.tsx`):**
- Log table
- Filtering
- Search
- Export

**Settings (`Settings.tsx`):**
- Tabbed interface
- Profile settings
- Notifications
- Webhooks

#### 6.4.2 Doctor Pages (`pages/doctor/`)

**Eligibility Check (`EligibilityCheck.tsx`):**
- Single check form
- Batch mode toggle
- Results display
- History

#### 6.4.3 Billing Pages (`pages/billing/`)

**Bill Audit (`BillAudit.tsx`):**
- Claim form
- Line items
- Document upload
- Audit results

**Patient Profile (`PatientProfile.tsx`):**
- Patient info
- Claims history
- Risk analytics
- Recommendations

### 6.5 State Management

#### 6.5.1 React Query Configuration

**Location:** `lib/queryClient.ts`

**Configuration:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});
```

**Query Keys:**
- `['policies']` - Policy list
- `['policy', id]` - Single policy
- `['claims']` - Claims list
- `['claim', id]` - Single claim
- `['dashboard']` - Dashboard data
- `['patient', id]` - Patient profile

#### 6.5.2 Local State

**useState:** Component-level state
**useReducer:** Complex state logic
**Context API:** Global state (auth, theme)

### 6.6 API Client

**Location:** `lib/api.ts`

**Axios Configuration:**
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error);
  }
);
```

**API Methods:**
- `api.get(url, config)`
- `api.post(url, data, config)`
- `api.put(url, data, config)`
- `api.delete(url, config)`

### 6.7 Routing

**Location:** `router.tsx`

**Routes:**
```typescript
/login                    → Login page
/mfa-challenge           → MFA challenge
/password-reset          → Password reset
/password-reset/confirm  → Reset confirmation
/                        → Redirect to dashboard
/admin/dashboard         → Admin dashboard
/admin/policies          → Policy management
/admin/reports           → Reports
/admin/audit-logs        → Audit logs
/admin/settings          → Settings
/doctor/eligibility      → Eligibility check
/billing/audit           → Bill audit
/billing/patient/:id     → Patient profile
```

**Protected Routes:**
- All routes except login require authentication
- Role-based access control
- Redirect to login if unauthorized

### 6.8 Styling

**Tailwind CSS Configuration:**

**Location:** `tailwind.config.js`

```javascript
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {...},
        secondary: {...},
      },
    },
  },
  plugins: [],
};
```

**Utility Classes:**
- Layout: `flex`, `grid`, `container`
- Spacing: `p-4`, `m-2`, `space-x-4`
- Typography: `text-lg`, `font-bold`
- Colors: `bg-blue-500`, `text-gray-900`
- Responsive: `md:flex`, `lg:grid-cols-3`

### 6.9 Build Configuration

**Vite Config:** `vite.config.ts`

**Features:**
- Path aliases (`@/*` → `./src/*`)
- Code splitting by feature
- Terser minification
- Console.log removal in production
- Chunk size optimization

**Build Output:**
```
dist/
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── [chunk]-[hash].js
└── index.html
```

---


## 7. API Documentation

### 7.1 API Overview

**Base URL:** `https://{api-id}.execute-api.{region}.amazonaws.com/prod`  
**Protocol:** HTTPS only  
**Authentication:** JWT Bearer token  
**Content-Type:** application/json

### 7.2 Authentication Endpoints

#### POST /auth/login
**Purpose:** User login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": true
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "user_id": "uuid",
      "email": "user@example.com",
      "role": "admin",
      "hospital_id": "hosp-123"
    },
    "mfa_required": false
  }
}
```

#### POST /auth/mfa/verify
**Purpose:** Verify MFA code

**Request:**
```json
{
  "user_id": "uuid",
  "code": "123456"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### POST /auth/password/reset
**Purpose:** Request password reset

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

### 7.3 Policy Endpoints

#### GET /policies
**Purpose:** List policies

**Query Parameters:**
- `hospital_id` (optional) - Filter by hospital
- `status` (optional) - Filter by status
- `page` (optional) - Page number
- `limit` (optional) - Items per page

**Response (200):**
```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "policy_id": "POL-123",
        "policy_name": "Apollo Munich Gold",
        "hospital_id": "HOSP-456",
        "version": 1,
        "status": "active",
        "effective_date": "2024-01-01",
        "confidence_score": 0.92
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45
    }
  }
}
```

#### POST /policy
**Purpose:** Upload new policy

**Request (multipart/form-data):**
```
file: [PDF file]
policy_name: "Apollo Munich Gold"
hospital_id: "HOSP-456"
effective_date: "2024-01-01"
expiration_date: "2024-12-31"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "policy_id": "POL-123",
    "status": "processing",
    "estimated_time": 180
  }
}
```

#### GET /policies/{id}/versions
**Purpose:** Get version history

**Response (200):**
```json
{
  "success": true,
  "data": {
    "versions": [
      {
        "version": 2,
        "created_at": "2024-01-15T10:00:00Z",
        "created_by": "user@example.com",
        "changes": "Updated coverage rules"
      },
      {
        "version": 1,
        "created_at": "2024-01-01T10:00:00Z",
        "created_by": "admin@example.com",
        "changes": "Initial version"
      }
    ]
  }
}
```

### 7.4 Eligibility Endpoints

#### POST /check-eligibility
**Purpose:** Check eligibility for procedure

**Request:**
```json
{
  "patient_id": "PAT-789",
  "policy_id": "POL-123",
  "procedure_code": "99213",
  "diagnosis_codes": ["Z00.00"],
  "procedure_date": "2024-01-20"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "coverage_status": "fully_covered",
    "coverage_percentage": 80,
    "patient_responsibility": 200.00,
    "copay": 50.00,
    "deductible_remaining": 500.00,
    "pre_authorization_required": false,
    "policy_references": [
      "Section 3.2: Outpatient coverage"
    ]
  }
}
```

#### POST /batch-eligibility
**Purpose:** Batch eligibility check

**Request (multipart/form-data):**
```
file: [CSV file]
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "batch_id": "BATCH-456",
    "status": "processing",
    "total_patients": 100,
    "estimated_time": 30
  }
}
```

#### GET /batch-eligibility/{id}
**Purpose:** Get batch status/results

**Response (200):**
```json
{
  "success": true,
  "data": {
    "batch_id": "BATCH-456",
    "status": "completed",
    "total_patients": 100,
    "processed": 100,
    "fully_covered": 75,
    "partially_covered": 20,
    "not_covered": 5,
    "results_url": "https://s3.../results.csv"
  }
}
```

### 7.5 Claim Endpoints

#### POST /audit-claim
**Purpose:** Audit medical bill

**Request:**
```json
{
  "patient_id": "PAT-789",
  "policy_id": "POL-123",
  "claim_amount": 5000.00,
  "line_items": [
    {
      "procedure_code": "99213",
      "description": "Office visit",
      "quantity": 1,
      "unit_price": 150.00,
      "total": 150.00,
      "date_of_service": "2024-01-20"
    }
  ],
  "documents": ["doc-url-1", "doc-url-2"]
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "claim_id": "CLM-123",
    "risk_level": "medium",
    "settlement_ratio": 0.87,
    "approved_amount": 4350.00,
    "rejected_amount": 650.00,
    "approved_items": 45,
    "rejected_items": 5,
    "recommendations": [
      {
        "type": "documentation",
        "message": "Add lab reports for procedure X",
        "impact": "May increase approval by $200"
      }
    ]
  }
}
```

#### POST /risk-score
**Purpose:** Calculate risk score

**Request:**
```json
{
  "claim_id": "CLM-123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "risk_score": 0.65,
    "risk_level": "medium",
    "factors": [
      {
        "factor": "claim_amount",
        "weight": 0.3,
        "score": 0.7
      },
      {
        "factor": "documentation",
        "weight": 0.25,
        "score": 0.6
      }
    ]
  }
}
```

### 7.6 Patient Endpoints

#### GET /patient/{id}
**Purpose:** Get patient profile

**Response (200):**
```json
{
  "success": true,
  "data": {
    "patient_id": "PAT-789",
    "name": "John Doe",
    "date_of_birth": "1980-05-15",
    "insurance": {
      "policy_id": "POL-123",
      "policy_name": "Apollo Munich Gold",
      "member_id": "MEM-456"
    },
    "statistics": {
      "total_claims": 15,
      "total_amount": 75000.00,
      "average_csr": 0.85,
      "current_risk": "low"
    }
  }
}
```

#### GET /patient/{id}/claims
**Purpose:** Get patient claims

**Response (200):**
```json
{
  "success": true,
  "data": {
    "claims": [
      {
        "claim_id": "CLM-123",
        "date": "2024-01-20",
        "amount": 5000.00,
        "status": "approved",
        "risk_level": "low"
      }
    ]
  }
}
```

### 7.7 Dashboard Endpoints

#### GET /dashboard
**Purpose:** Get dashboard metrics

**Query Parameters:**
- `hospital_id` (optional) - Filter by hospital
- `date_from` (optional) - Start date
- `date_to` (optional) - End date

**Response (200):**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "total_claims": 1250,
      "average_csr": 0.87,
      "high_risk_claims": 45,
      "processing_time": 28.5,
      "cost_savings": 125000.00
    },
    "charts": {
      "csr_trend": [...],
      "claims_by_status": {...},
      "risk_distribution": {...}
    },
    "alerts": [
      {
        "type": "high_risk",
        "message": "5 high-risk claims require attention",
        "count": 5
      }
    ]
  }
}
```

### 7.8 Report Endpoints

#### POST /reports/generate
**Purpose:** Generate report

**Request:**
```json
{
  "report_type": "settlement_analysis",
  "parameters": {
    "hospital_id": "HOSP-456",
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
  },
  "format": "pdf"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "report_id": "RPT-789",
    "status": "generating",
    "estimated_time": 60
  }
}
```

#### GET /reports/{id}
**Purpose:** Get report status/download

**Response (200):**
```json
{
  "success": true,
  "data": {
    "report_id": "RPT-789",
    "status": "completed",
    "download_url": "https://s3.../report.pdf",
    "expires_at": "2024-01-21T10:00:00Z"
  }
}
```

### 7.9 Webhook Endpoints

#### GET /webhooks
**Purpose:** List webhooks

**Response (200):**
```json
{
  "success": true,
  "data": {
    "webhooks": [
      {
        "webhook_id": "WHK-001",
        "name": "EMR Integration",
        "url": "https://emr.example.com/webhook",
        "events": ["claim.submitted", "audit.completed"],
        "enabled": true,
        "last_triggered": "2024-01-20T10:00:00Z"
      }
    ]
  }
}
```

#### POST /webhooks
**Purpose:** Create webhook

**Request:**
```json
{
  "name": "EMR Integration",
  "url": "https://emr.example.com/webhook",
  "events": ["claim.submitted", "audit.completed"],
  "auth_type": "api_key",
  "auth_config": {
    "header_name": "X-API-Key",
    "api_key": "secret-key"
  }
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "webhook_id": "WHK-001",
    "name": "EMR Integration",
    "enabled": true
  }
}
```

### 7.10 Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "email": "Invalid email format"
    }
  }
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

**403 Forbidden:**
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions"
  }
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found"
  }
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "request_id": "req-123"
  }
}
```

### 7.11 Rate Limiting

**Limits:**
- 1000 requests per hour per user
- 100 requests per minute per IP
- Burst: 20 requests per second

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1234567890
```

**429 Too Many Requests:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 3600
  }
}
```

---


## 8. Database Schema

### 8.1 DynamoDB Tables

#### 8.1.1 Users Table

**Table Name:** `hospital-claim-optimizer-users`  
**Billing Mode:** On-demand

**Primary Key:**
- Partition Key: `user_id` (String)

**Attributes:**
```
user_id: String (UUID)
email: String
password_hash: String (bcrypt)
role: String (admin|hospital_admin|billing_staff|doctor)
hospital_id: String (optional)
first_name: String
last_name: String
phone: String
mfa_enabled: Boolean
mfa_secret: String (encrypted)
backup_codes: List<String> (encrypted)
password_history: List<String> (last 5 hashes)
last_login: Number (timestamp)
created_at: Number (timestamp)
updated_at: Number (timestamp)
status: String (active|inactive|suspended)
```

**Global Secondary Indexes:**
- `email-index`: email (PK)

**Access Patterns:**
- Get user by ID
- Get user by email (login)
- List users by role
- List users by hospital

#### 8.1.2 Sessions Table

**Table Name:** `hospital-claim-optimizer-sessions`  
**Billing Mode:** On-demand  
**TTL Attribute:** `expires_at`

**Primary Key:**
- Partition Key: `session_id` (String)

**Attributes:**
```
session_id: String (UUID)
user_id: String
created_at: Number (timestamp)
last_activity: Number (timestamp)
expires_at: Number (timestamp, TTL)
ip_address: String
user_agent: String
device_info: Map
remember_me: Boolean
```

**Access Patterns:**
- Get session by ID
- List sessions by user
- Cleanup expired sessions (automatic via TTL)

#### 8.1.3 Policies Table

**Table Name:** `hospital-claim-optimizer-policies`  
**Billing Mode:** On-demand

**Primary Key:**
- Partition Key: `policy_id` (String)
- Sort Key: `version` (Number)

**Attributes:**
```
policy_id: String (UUID)
version: Number
policy_name: String
hospital_id: String
policy_number: String
effective_date: String (ISO date)
expiration_date: String (ISO date)
status: String (active|expired|draft)
confidence_score: Number (0-1)
rules: Map {
  coverage: Map
  exclusions: List
  limits: Map
  copay: Map
  deductible: Map
  preauth_required: List
}
s3_document_url: String
created_by: String (user_id)
created_at: Number (timestamp)
updated_at: Number (timestamp)
```

**Global Secondary Indexes:**
- `hospital-index`: hospital_id (PK), effective_date (SK)
- `status-index`: status (PK), created_at (SK)

**Access Patterns:**
- Get policy by ID and version
- Get latest version of policy
- List policies by hospital
- List active policies
- Get version history

#### 8.1.4 Claims Table

**Table Name:** `hospital-claim-optimizer-claims`  
**Billing Mode:** On-demand

**Primary Key:**
- Partition Key: `claim_id` (String)

**Attributes:**
```
claim_id: String (UUID)
patient_id: String
hospital_id: String
policy_id: String
policy_version: Number
claim_amount: Number
approved_amount: Number
rejected_amount: Number
risk_level: String (low|medium|high)
risk_score: Number (0-1)
settlement_ratio: Number (0-1)
status: String (draft|audited|submitted|approved|rejected)
line_items: List<Map> {
  procedure_code: String
  description: String
  quantity: Number
  unit_price: Number
  total: Number
  date_of_service: String
  status: String
  rejection_reason: String (optional)
}
audit_results: Map {
  approved_items: Number
  rejected_items: Number
  review_items: Number
  recommendations: List<Map>
}
documents: List<String> (S3 URLs)
created_by: String (user_id)
created_at: Number (timestamp)
updated_at: Number (timestamp)
submitted_at: Number (timestamp, optional)
```

**Global Secondary Indexes:**
- `patient-index`: patient_id (PK), created_at (SK)
- `hospital-index`: hospital_id (PK), created_at (SK)
- `status-index`: status (PK), created_at (SK)

**Access Patterns:**
- Get claim by ID
- List claims by patient
- List claims by hospital
- List claims by status
- Query claims by date range

#### 8.1.5 Audit Logs Table

**Table Name:** `hospital-claim-optimizer-audit-logs`  
**Billing Mode:** On-demand

**Primary Key:**
- Partition Key: `log_id` (String)
- Sort Key: `timestamp` (Number)

**Attributes:**
```
log_id: String (UUID)
timestamp: Number
user_id: String
user_email: String
action: String (login|logout|create|update|delete|view)
resource_type: String (policy|claim|user|webhook)
resource_id: String
changes: Map {
  before: Map (optional)
  after: Map (optional)
}
ip_address: String
user_agent: String
status: String (success|failure)
error_message: String (optional)
```

**Global Secondary Indexes:**
- `user-index`: user_id (PK), timestamp (SK)
- `resource-index`: resource_id (PK), timestamp (SK)

**Access Patterns:**
- Get log by ID
- List logs by user
- List logs by resource
- Query logs by date range
- Search logs by action

#### 8.1.6 Webhooks Table

**Table Name:** `hospital-claim-optimizer-webhooks`  
**Billing Mode:** On-demand

**Primary Key:**
- Partition Key: `webhook_id` (String)

**Attributes:**
```
webhook_id: String (UUID)
name: String
url: String (HTTPS only)
events: List<String>
auth_type: String (api_key|oauth2|none)
auth_config: Map (encrypted)
enabled: Boolean
created_by: String (user_id)
created_at: Number (timestamp)
updated_at: Number (timestamp)
last_triggered: Number (timestamp, optional)
delivery_stats: Map {
  total_deliveries: Number
  successful: Number
  failed: Number
  last_success: Number (timestamp)
  last_failure: Number (timestamp)
}
```

**Access Patterns:**
- Get webhook by ID
- List all webhooks
- List enabled webhooks
- List webhooks by event type

### 8.2 Data Relationships

```
User (1) ──────── (N) Session
  │
  │ (1)
  │
  ├─────────────── (N) Claim
  │
  │ (1)
  │
  └─────────────── (N) AuditLog

Hospital (1) ──── (N) Policy
  │
  │ (1)
  │
  └─────────────── (N) Claim

Policy (1) ────── (N) Claim

Patient (1) ───── (N) Claim

User (1) ──────── (N) Webhook
```

### 8.3 Data Access Patterns

**High-Frequency Queries:**
1. Get user by email (login) - `email-index`
2. Get session by ID - Primary key
3. Get active policies by hospital - `hospital-index`
4. Get claims by patient - `patient-index`
5. Get dashboard metrics - Aggregation query

**Medium-Frequency Queries:**
1. List policies by status - `status-index`
2. List claims by hospital - `hospital-index`
3. Get audit logs by user - `user-index`
4. Get policy versions - Sort key query

**Low-Frequency Queries:**
1. Full table scans (admin reports)
2. Complex aggregations
3. Historical data analysis

### 8.4 Data Retention

**Policies:**
- Active: Indefinite
- Expired: 7 years (compliance)
- Versions: All versions retained

**Claims:**
- Active: Indefinite
- Completed: 7 years (compliance)
- Rejected: 3 years

**Audit Logs:**
- All logs: 7 years (compliance)
- Archived to S3 after 1 year

**Sessions:**
- Automatic deletion via TTL
- Expired sessions removed within 48 hours

**Webhooks:**
- Active: Indefinite
- Delivery logs: 90 days

### 8.5 Backup Strategy

**DynamoDB Point-in-Time Recovery:**
- Enabled on all tables
- 35-day recovery window
- Continuous backups

**On-Demand Backups:**
- Weekly full backups
- Retained for 90 days
- Stored in separate AWS account

**S3 Versioning:**
- Enabled on all buckets
- 90-day version retention
- Glacier archival after 365 days

---


## 9. Authentication & Security

### 9.1 Authentication Flow

#### 9.1.1 Standard Login Flow

```
1. User submits email + password
2. Backend validates credentials
3. If MFA enabled:
   a. Return mfa_required: true
   b. User submits MFA code
   c. Backend verifies TOTP
4. Generate JWT token
5. Create session in DynamoDB
6. Return token + user data
7. Frontend stores token in localStorage
8. Include token in Authorization header
```

#### 9.1.2 JWT Token Structure

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "admin",
  "hospital_id": "hosp-123",
  "session_id": "session-uuid",
  "iat": 1234567890,
  "exp": 1234596690
}
```

**Signature:**
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret
)
```

**Token Expiration:**
- Access Token: 8 hours
- Refresh Token: 30 days
- Remember Me: 30 days

#### 9.1.3 Token Refresh Flow

```
1. Access token expires
2. Frontend detects 401 response
3. Send refresh token to /auth/refresh
4. Backend validates refresh token
5. Check session still valid
6. Generate new access token
7. Return new token
8. Frontend updates stored token
```

### 9.2 Multi-Factor Authentication

#### 9.2.1 TOTP (Time-based One-Time Password)

**Algorithm:** SHA1  
**Digits:** 6  
**Period:** 30 seconds  
**Window:** ±1 period (90 seconds total)

**Setup Flow:**
```
1. User enables MFA
2. Backend generates secret key
3. Encrypt and store secret
4. Generate QR code
5. User scans with authenticator app
6. User enters verification code
7. Backend verifies code
8. Generate backup codes
9. MFA enabled
```

**Verification Flow:**
```
1. User logs in successfully
2. Backend checks mfa_enabled
3. Request MFA code
4. User enters code from app
5. Backend verifies TOTP
6. If valid, complete login
7. If invalid, retry (3 attempts max)
```

#### 9.2.2 Backup Codes

**Generation:**
- 10 codes generated
- 8-character alphanumeric
- One-time use only
- Encrypted storage

**Usage:**
```
1. User lost authenticator access
2. Select "Use backup code"
3. Enter backup code
4. Backend verifies and marks used
5. Complete login
6. Prompt to regenerate codes
```

### 9.3 Password Security

#### 9.3.1 Password Requirements

**Minimum Requirements:**
- Length: 12 characters
- Uppercase: At least 1
- Lowercase: At least 1
- Number: At least 1
- Special character: At least 1
- No common passwords (check against list)
- No password reuse (last 5)

**Hashing:**
- Algorithm: bcrypt
- Cost factor: 12
- Salt: Automatic (per-password)

#### 9.3.2 Password Reset Flow

```
1. User clicks "Forgot Password"
2. Enter email address
3. Backend generates reset token
4. Token valid for 1 hour
5. Send email with reset link
6. User clicks link
7. Enter new password
8. Backend validates token
9. Hash new password
10. Update password
11. Invalidate all sessions
12. Send confirmation email
```

### 9.4 Session Management

#### 9.4.1 Session Lifecycle

**Creation:**
```python
session = {
    "session_id": generate_uuid(),
    "user_id": user_id,
    "created_at": now(),
    "last_activity": now(),
    "expires_at": now() + 8_hours,
    "ip_address": request.ip,
    "user_agent": request.user_agent,
    "remember_me": remember_me
}
```

**Activity Tracking:**
- Update `last_activity` on each request
- If inactive > 30 minutes, expire session
- If remember_me, extend to 30 days

**Termination:**
- User logout
- Token expiration
- Inactivity timeout
- Password change
- Security event

#### 9.4.2 Concurrent Sessions

**Policy:**
- Allow multiple sessions per user
- Track all active sessions
- User can view and revoke sessions
- Limit: 5 concurrent sessions

**Session List:**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "device": "Chrome on Windows",
      "ip_address": "192.168.1.1",
      "last_activity": "2024-01-20T10:00:00Z",
      "current": true
    }
  ]
}
```

### 9.5 Authorization

#### 9.5.1 Role-Based Access Control (RBAC)

**Roles:**
1. **TPA Administrator**
   - Full system access
   - Policy management
   - User management
   - System configuration

2. **Hospital Administrator**
   - Hospital-level access
   - View all hospital claims
   - Generate reports
   - Manage hospital users

3. **Billing Staff**
   - Create and manage claims
   - Run audits
   - View policies
   - Export data

4. **Doctor**
   - Eligibility checking only
   - View coverage information
   - No claim access

#### 9.5.2 Permission Matrix

```python
PERMISSIONS = {
    "tpa_admin": [
        "policy:create", "policy:read", "policy:update", "policy:delete",
        "claim:create", "claim:read", "claim:update", "claim:delete",
        "user:create", "user:read", "user:update", "user:delete",
        "webhook:create", "webhook:read", "webhook:update", "webhook:delete",
        "report:generate", "report:read",
        "audit:read",
        "eligibility:check"
    ],
    "hospital_admin": [
        "policy:read",
        "claim:read",
        "user:create", "user:read", "user:update",
        "report:generate", "report:read",
        "audit:read",
        "eligibility:check"
    ],
    "billing_staff": [
        "policy:read",
        "claim:create", "claim:read", "claim:update",
        "eligibility:check"
    ],
    "doctor": [
        "policy:read",
        "eligibility:check"
    ]
}
```

#### 9.5.3 Resource-Level Authorization

**Hospital Isolation:**
```python
def check_hospital_access(user, resource):
    if user.role == "tpa_admin":
        return True  # Full access
    if user.role == "hospital_admin":
        return resource.hospital_id == user.hospital_id
    if user.role in ["billing_staff", "doctor"]:
        return resource.hospital_id == user.hospital_id
    return False
```

**Claim Access:**
```python
def check_claim_access(user, claim):
    if user.role == "tpa_admin":
        return True
    if user.role == "hospital_admin":
        return claim.hospital_id == user.hospital_id
    if user.role == "billing_staff":
        return (claim.hospital_id == user.hospital_id and
                claim.created_by == user.user_id)
    return False
```

### 9.6 Data Encryption

#### 9.6.1 Encryption at Rest

**DynamoDB:**
- AWS-managed encryption
- KMS customer-managed keys
- Automatic encryption/decryption

**S3:**
- Server-side encryption (SSE-S3)
- Bucket-level encryption
- Object-level encryption

**Secrets Manager:**
- Automatic encryption
- KMS integration
- Automatic rotation

#### 9.6.2 Encryption in Transit

**HTTPS Only:**
- TLS 1.2 minimum
- Strong cipher suites
- Certificate from ACM

**API Gateway:**
- Regional endpoint
- Custom domain with SSL
- Certificate validation

**Internal Communication:**
- VPC endpoints (optional)
- Private subnets
- Security groups

#### 9.6.3 Field-Level Encryption

**Sensitive Fields:**
```python
ENCRYPTED_FIELDS = [
    "password_hash",
    "mfa_secret",
    "backup_codes",
    "webhook.auth_config",
    "patient.ssn",
    "patient.medical_record_number"
]
```

**Encryption Method:**
- Algorithm: AES-256-GCM
- Key: From KMS
- IV: Random per encryption
- Tag: Authentication tag

### 9.7 Security Best Practices

#### 9.7.1 Input Validation

**All Inputs:**
- Validate type and format
- Sanitize HTML/SQL
- Check length limits
- Whitelist allowed characters

**Example:**
```python
def validate_email(email):
    if not email or len(email) > 255:
        raise ValidationError("Invalid email length")
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValidationError("Invalid email format")
    return email.lower()
```

#### 9.7.2 SQL Injection Prevention

**Use Parameterized Queries:**
```python
# Bad
query = f"SELECT * FROM users WHERE email = '{email}'"

# Good
query = "SELECT * FROM users WHERE email = ?"
params = [email]
```

**DynamoDB:**
- Use boto3 SDK (automatic escaping)
- No raw query strings
- Validate all inputs

#### 9.7.3 XSS Prevention

**Frontend:**
- React automatic escaping
- No dangerouslySetInnerHTML
- Content Security Policy headers

**Backend:**
- Sanitize all outputs
- Set proper Content-Type headers
- Use CORS properly

#### 9.7.4 CSRF Prevention

**Tokens:**
- Generate CSRF token per session
- Include in forms
- Validate on submission

**SameSite Cookies:**
```
Set-Cookie: session=xxx; SameSite=Strict; Secure; HttpOnly
```

#### 9.7.5 Rate Limiting

**API Gateway:**
- 1000 requests/hour per user
- 100 requests/minute per IP
- Burst: 20 requests/second

**Lambda:**
- Concurrent execution limits
- Reserved concurrency per function

**DynamoDB:**
- On-demand scaling
- Automatic throttling protection

#### 9.7.6 Audit Logging

**Log All:**
- Authentication attempts
- Authorization failures
- Data access
- Configuration changes
- Security events

**Log Format:**
```json
{
  "timestamp": "2024-01-20T10:00:00Z",
  "user_id": "uuid",
  "action": "login",
  "resource": "user",
  "status": "success",
  "ip_address": "192.168.1.1",
  "user_agent": "Chrome/120.0"
}
```

### 9.8 Compliance

#### 9.8.1 HIPAA Compliance

**Requirements:**
- Encryption at rest and in transit
- Access controls and audit logs
- Data backup and recovery
- Business Associate Agreements (BAA)
- Regular security assessments

**Implementation:**
- AWS HIPAA-eligible services
- Encrypted storage (DynamoDB, S3)
- Audit logging (CloudWatch, DynamoDB)
- Access controls (IAM, RBAC)
- Backup strategy (Point-in-time recovery)

#### 9.8.2 GDPR Compliance

**Requirements:**
- Data minimization
- Right to access
- Right to erasure
- Data portability
- Consent management

**Implementation:**
- Collect only necessary data
- Provide data export API
- Implement data deletion
- Log consent records
- Privacy policy

#### 9.8.3 SOC 2 Compliance

**Requirements:**
- Security controls
- Availability monitoring
- Processing integrity
- Confidentiality measures
- Privacy protection

**Implementation:**
- Security best practices
- Monitoring and alerting
- Data validation
- Encryption
- Access controls

---


## 10. Configuration Management

### 10.1 Environment Variables

#### 10.1.1 Frontend Environment Variables

**File:** `frontend/.env`

```bash
# API Configuration
VITE_API_BASE_URL=https://api.example.com
VITE_APP_ENV=development|staging|production

# Feature Flags
VITE_ENABLE_MFA=true
VITE_ENABLE_WEBHOOKS=true
VITE_ENABLE_BATCH_PROCESSING=true

# Analytics
VITE_ANALYTICS_ID=UA-XXXXXXXXX

# Sentry (Error Tracking)
VITE_SENTRY_DSN=https://xxx@sentry.io/xxx
```

#### 10.1.2 Backend Environment Variables

**Lambda Functions:**

```bash
# Database
USER_TABLE_NAME=hospital-claim-optimizer-users
SESSION_TABLE_NAME=hospital-claim-optimizer-sessions
POLICY_TABLE_NAME=hospital-claim-optimizer-policies
CLAIMS_TABLE_NAME=hospital-claim-optimizer-claims
AUDIT_TABLE_NAME=hospital-claim-optimizer-audit-logs
WEBHOOKS_TABLE_NAME=hospital-claim-optimizer-webhooks

# Storage
POLICY_BUCKET=hospital-claim-optimizer-policies-{account}
BATCH_BUCKET=hospital-claim-optimizer-batch-{account}
FRONTEND_BUCKET=hospital-claim-optimizer-frontend-{account}

# Cache
REDIS_ENDPOINT=cache-cluster.xxxxx.cache.amazonaws.com:6379
REDIS_PORT=6379

# Secrets
JWT_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:jwt-secret
MFA_SECRET_KEY_ARN=arn:aws:secretsmanager:region:account:secret:mfa-key
ENCRYPTION_KEY_ARN=arn:aws:secretsmanager:region:account:secret:encryption-key

# Email
SES_FROM_EMAIL=noreply@example.com
SES_REGION=us-east-1
SES_CONFIGURATION_SET=claim-optimizer-emails

# Application
APP_ENV=development|staging|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
REGION=us-east-1
```

### 10.2 AWS Secrets Manager

**Secrets Stored:**

1. **JWT Secret**
   - Name: `claim-optimizer/jwt-secret`
   - Rotation: Every 90 days
   - Used for: Token signing

2. **MFA Secret Key**
   - Name: `claim-optimizer/mfa-key`
   - Rotation: Manual
   - Used for: TOTP generation

3. **Encryption Key**
   - Name: `claim-optimizer/encryption-key`
   - Rotation: Every 90 days
   - Used for: Field-level encryption

4. **Database Credentials** (if using RDS)
   - Name: `claim-optimizer/db-credentials`
   - Rotation: Every 30 days
   - Used for: Database access

5. **Third-Party API Keys**
   - Name: `claim-optimizer/api-keys`
   - Rotation: Manual
   - Used for: External integrations

**Access Pattern:**
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
jwt_secret = get_secret('claim-optimizer/jwt-secret')['secret']
```

### 10.3 Feature Flags

**Implementation:**
```python
FEATURE_FLAGS = {
    "enable_mfa": True,
    "enable_webhooks": True,
    "enable_batch_processing": True,
    "enable_policy_versioning": True,
    "enable_email_notifications": True,
    "enable_cache": True,
    "max_batch_size": 100,
    "session_timeout_minutes": 30,
    "max_file_size_mb": 50
}

def is_feature_enabled(feature_name):
    return FEATURE_FLAGS.get(feature_name, False)
```

### 10.4 CDK Configuration

**File:** `hospital-claim-optimizer/cdk.json`

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/hospital-claim-optimizer.ts",
  "context": {
    "@aws-cdk/core:enableStackNameDuplicates": true,
    "aws-cdk:enableDiffNoFail": true,
    "@aws-cdk/core:stackRelativeExports": true,
    "@aws-cdk/aws-ecr-assets:dockerIgnoreSupport": true,
    "@aws-cdk/aws-secretsmanager:parseOwnedSecretName": true,
    "@aws-cdk/aws-kms:defaultKeyPolicies": true,
    "@aws-cdk/aws-s3:grantWriteWithoutAcl": true
  }
}
```

### 10.5 Deployment Environments

#### 10.5.1 Development

**Purpose:** Local development and testing

**Configuration:**
- API Gateway: Development stage
- Lambda: 512MB memory
- DynamoDB: On-demand
- CloudWatch: DEBUG logging
- Cost: Minimal

#### 10.5.2 Staging

**Purpose:** Pre-production testing

**Configuration:**
- API Gateway: Staging stage
- Lambda: 1024MB memory
- DynamoDB: On-demand
- CloudWatch: INFO logging
- Cost: Moderate

#### 10.5.3 Production

**Purpose:** Live environment

**Configuration:**
- API Gateway: Production stage
- Lambda: 1024-3008MB memory
- DynamoDB: On-demand with auto-scaling
- CloudWatch: WARNING logging
- Cost: Variable based on usage

---

## 11. Testing Strategy

### 11.1 Testing Pyramid

```
        /\
       /  \
      / E2E \
     /--------\
    /          \
   / Integration \
  /--------------\
 /                \
/   Unit Tests     \
--------------------
```

### 11.2 Unit Tests

**Location:** `hospital-claim-optimizer/tests/`  
**Framework:** Pytest  
**Coverage Target:** 80%+

**Test Files:**
- `test_auth_middleware.py` - Authentication tests
- `test_policy_service.py` - Policy service tests
- `test_integration_complete.py` - Integration tests
- `test_integration_workflows.py` - Workflow tests

**Run Tests:**
```bash
cd hospital-claim-optimizer
pytest tests/ -v
pytest tests/ --cov=lambda-layers/common/python
```

### 11.3 Property-Based Tests

**Framework:** Hypothesis  
**Purpose:** Test properties across many inputs

**Test Files (25 total):**
1. `test_property_authentication.py`
2. `test_property_mfa.py`
3. `test_property_password.py`
4. `test_property_policy_processing.py`
5. `test_property_policy_versioning.py`
6. `test_property_eligibility_checking.py`
7. `test_property_bill_audit.py`
8. `test_property_risk_assessment.py`
9. `test_property_batch_processing.py`
10. `test_property_webhooks.py`
11. `test_property_email_notifications.py`
12. `test_property_multi_claim_risk.py`
13. `test_property_version_comparison.py`
14. `test_property_reporting.py`
15. `test_property_dashboard.py`
16. `test_property_security.py`
17. `test_property_performance.py`
18. `test_property_system_integration.py`
19. `test_property_api_consistency.py`
20. `test_property_data_models.py`
21. And 4 more...

**Example Test:**
```python
from hypothesis import given, strategies as st

@given(
    email=st.emails(),
    password=st.text(min_size=12, max_size=128)
)
def test_user_creation_properties(email, password):
    """Test user creation with various inputs"""
    user = create_user(email, password)
    assert user.email == email.lower()
    assert verify_password(password, user.password_hash)
```

**Run Property Tests:**
```bash
pytest tests/test_property_*.py -v
```

### 11.4 Integration Tests

**Purpose:** Test component interactions

**Test Scenarios:**
1. Complete authentication flow
2. Policy upload and processing
3. Eligibility check workflow
4. Claim audit workflow
5. Batch processing workflow
6. Webhook delivery
7. Email notification

**Example:**
```python
def test_complete_claim_workflow():
    # 1. Create user
    user = create_test_user()
    
    # 2. Upload policy
    policy = upload_test_policy()
    
    # 3. Create claim
    claim = create_test_claim(policy.policy_id)
    
    # 4. Audit claim
    audit_result = audit_claim(claim.claim_id)
    
    # 5. Verify results
    assert audit_result.risk_level in ['low', 'medium', 'high']
    assert 0 <= audit_result.settlement_ratio <= 1
```

### 11.5 E2E Tests

**Location:** `e2e/tests/`  
**Framework:** Playwright  
**Browser:** Chromium, Firefox, WebKit

**Test Files:**
1. `auth.spec.ts` - Authentication flows
2. `eligibility-check.spec.ts` - Eligibility checking
3. `bill-audit.spec.ts` - Bill auditing
4. `policy-management.spec.ts` - Policy management
5. `dashboard.spec.ts` - Dashboard functionality
6. `reports.spec.ts` - Report generation
7. `test-reliability.spec.ts` - Reliability tests

**Run E2E Tests:**
```bash
cd e2e
npx playwright test
npx playwright test --headed  # With browser UI
npx playwright test --debug   # Debug mode
```

**Example Test:**
```typescript
test('user can login and view dashboard', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:5173/login');
  
  // Fill credentials
  await page.fill('[name="email"]', 'admin@example.com');
  await page.fill('[name="password"]', 'SecurePass123!');
  
  // Submit
  await page.click('button[type="submit"]');
  
  // Verify redirect to dashboard
  await expect(page).toHaveURL('/admin/dashboard');
  
  // Verify dashboard elements
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### 11.6 Performance Tests

**Tools:**
- Apache JMeter
- AWS CloudWatch
- Custom performance monitors

**Metrics:**
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Error rate
- Resource utilization

**Test Scenarios:**
1. **Load Test:** Normal traffic
2. **Stress Test:** Peak traffic
3. **Spike Test:** Sudden traffic increase
4. **Endurance Test:** Sustained load

**Performance Targets:**
- API response time: < 500ms (p95)
- Eligibility check: < 2 seconds
- Policy processing: < 5 minutes
- Batch processing: < 30 seconds (100 patients)

### 11.7 Security Tests

**Tools:**
- OWASP ZAP
- AWS Inspector
- Snyk (dependency scanning)

**Test Areas:**
1. Authentication bypass
2. Authorization flaws
3. SQL injection
4. XSS vulnerabilities
5. CSRF attacks
6. Sensitive data exposure
7. Broken access control

**Run Security Scan:**
```bash
# Dependency vulnerabilities
npm audit
pip-audit

# OWASP ZAP scan
zap-cli quick-scan http://localhost:5173
```

### 11.8 Test Data Management

**Test Users:**
```python
TEST_USERS = {
    "admin": {
        "email": "admin@test.com",
        "password": "TestPass123!",
        "role": "tpa_admin"
    },
    "doctor": {
        "email": "doctor@test.com",
        "password": "TestPass123!",
        "role": "doctor"
    }
}
```

**Test Policies:**
- Sample policy PDFs
- Pre-extracted policy data
- Various coverage scenarios

**Test Claims:**
- Valid claims
- Invalid claims
- Edge cases

**Cleanup:**
```python
def cleanup_test_data():
    """Remove all test data after tests"""
    delete_test_users()
    delete_test_policies()
    delete_test_claims()
```

### 11.9 CI/CD Testing

**GitHub Actions Workflow:**
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: pytest tests/ -v --cov
      
      - name: Run property tests
        run: pytest tests/test_property_*.py -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---


## 12. Deployment

### 12.1 Deployment Architecture

```
Developer → Git Push → GitHub → CI/CD Pipeline → AWS
                                      ↓
                        ┌─────────────┴─────────────┐
                        │                           │
                    Frontend                    Backend
                        │                           │
                    S3 + CF                    CDK Deploy
                        │                           │
                    CloudFront              Lambda + API GW
```

### 12.2 Prerequisites

**Required Tools:**
- AWS CLI 2.x
- AWS CDK CLI 2.x
- Node.js 18+
- Python 3.11+
- npm 9+
- Git

**AWS Account Setup:**
1. Create AWS account
2. Configure IAM user with admin access
3. Generate access keys
4. Configure AWS CLI:
```bash
aws configure
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-1
# Default output format: json
```

**Verify Setup:**
```bash
aws sts get-caller-identity
cdk --version
node --version
python --version
```

### 12.3 Backend Deployment

#### 12.3.1 First-Time Deployment

**Step 1: Install Dependencies**
```bash
cd hospital-claim-optimizer
npm install
```

**Step 2: Bootstrap CDK**
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

**Step 3: Synthesize CloudFormation**
```bash
cdk synth
```

**Step 4: Deploy Stack**
```bash
cdk deploy --all
```

**Step 5: Note Outputs**
```
Outputs:
HospitalClaimOptimizerStack.ApiEndpoint = https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
HospitalClaimOptimizerStack.FrontendBucket = hospital-claim-optimizer-frontend-xxxxx
HospitalClaimOptimizerStack.CloudFrontUrl = https://xxxxx.cloudfront.net
```

#### 12.3.2 Update Deployment

**Deploy Changes:**
```bash
cd hospital-claim-optimizer
cdk deploy
```

**Deploy Specific Stack:**
```bash
cdk deploy HospitalClaimOptimizerStack
```

**Deploy with Approval:**
```bash
cdk deploy --require-approval never
```

#### 12.3.3 Rollback

**List Stacks:**
```bash
aws cloudformation list-stacks
```

**Rollback Stack:**
```bash
aws cloudformation rollback-stack --stack-name HospitalClaimOptimizerStack
```

**Or use CDK:**
```bash
cdk deploy --rollback
```

### 12.4 Frontend Deployment

#### 12.4.1 Build Frontend

**Step 1: Install Dependencies**
```bash
cd frontend
npm install
```

**Step 2: Configure Environment**
```bash
cp .env.example .env
# Edit .env with production values
VITE_API_BASE_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
```

**Step 3: Build**
```bash
npm run build
```

**Output:** `dist/` directory

#### 12.4.2 Deploy to S3

**Upload Files:**
```bash
aws s3 sync dist/ s3://FRONTEND_BUCKET/ --delete
```

**Set Cache Headers:**
```bash
# HTML files - no cache
aws s3 cp dist/index.html s3://FRONTEND_BUCKET/ \
  --cache-control "no-cache, no-store, must-revalidate"

# JS/CSS files - 1 year cache
aws s3 cp dist/assets/ s3://FRONTEND_BUCKET/assets/ \
  --recursive \
  --cache-control "public, max-age=31536000, immutable"
```

#### 12.4.3 Invalidate CloudFront

**Create Invalidation:**
```bash
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

**Check Status:**
```bash
aws cloudfront get-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --id INVALIDATION_ID
```

### 12.5 Deployment Script

**File:** `hospital-claim-optimizer/deploy.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Backend
echo "📦 Deploying backend..."
cd hospital-claim-optimizer
npm install
cdk deploy --require-approval never

# Get outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name HospitalClaimOptimizerStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name HospitalClaimOptimizerStack \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
  --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name HospitalClaimOptimizerStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

# Frontend
echo "🎨 Building frontend..."
cd ../frontend
echo "VITE_API_BASE_URL=$API_URL" > .env
npm install
npm run build

echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://$FRONTEND_BUCKET/ --delete

echo "🔄 Invalidating CloudFront..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo "✅ Deployment complete!"
echo "🌐 Frontend URL: https://$DISTRIBUTION_ID.cloudfront.net"
echo "🔌 API URL: $API_URL"
```

**Run Deployment:**
```bash
chmod +x hospital-claim-optimizer/deploy.sh
./hospital-claim-optimizer/deploy.sh
```

### 12.6 CI/CD Pipeline

#### 12.6.1 GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Install CDK
        run: npm install -g aws-cdk
      
      - name: Deploy backend
        run: |
          cd hospital-claim-optimizer
          npm install
          cdk deploy --require-approval never
      
      - name: Build and deploy frontend
        run: |
          cd frontend
          npm install
          npm run build
          aws s3 sync dist/ s3://${{ secrets.FRONTEND_BUCKET }}/ --delete
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.DISTRIBUTION_ID }} \
            --paths "/*"
```

#### 12.6.2 Environment-Specific Deployments

**Development:**
```yaml
on:
  push:
    branches: [develop]

env:
  ENVIRONMENT: development
  AWS_REGION: us-east-1
```

**Staging:**
```yaml
on:
  push:
    branches: [staging]

env:
  ENVIRONMENT: staging
  AWS_REGION: us-east-1
```

**Production:**
```yaml
on:
  push:
    branches: [main]

env:
  ENVIRONMENT: production
  AWS_REGION: us-east-1
```

### 12.7 Blue-Green Deployment

**Strategy:**
1. Deploy new version (green)
2. Run smoke tests
3. Switch traffic to green
4. Monitor for issues
5. Keep blue for rollback
6. Decommission blue after 24h

**Implementation:**
```bash
# Deploy green environment
cdk deploy --context environment=green

# Run smoke tests
./run-smoke-tests.sh

# Switch traffic
aws apigateway update-stage \
  --rest-api-id API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/deploymentId,value=NEW_DEPLOYMENT_ID

# Monitor
./monitor-deployment.sh

# Rollback if needed
aws apigateway update-stage \
  --rest-api-id API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/deploymentId,value=OLD_DEPLOYMENT_ID
```

### 12.8 Deployment Checklist

**Pre-Deployment:**
- [ ] Run all tests locally
- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Review code changes
- [ ] Check environment variables
- [ ] Backup database
- [ ] Notify team

**Deployment:**
- [ ] Deploy backend
- [ ] Verify Lambda functions
- [ ] Deploy frontend
- [ ] Invalidate CloudFront
- [ ] Run smoke tests
- [ ] Check logs

**Post-Deployment:**
- [ ] Monitor metrics
- [ ] Check error rates
- [ ] Verify functionality
- [ ] Update documentation
- [ ] Notify stakeholders
- [ ] Tag release in Git

### 12.9 Rollback Procedures

**Immediate Rollback:**
```bash
# Rollback CDK stack
cdk deploy --rollback

# Rollback frontend
aws s3 sync s3://BACKUP_BUCKET/ s3://FRONTEND_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

**Database Rollback:**
```bash
# DynamoDB point-in-time recovery
aws dynamodb restore-table-to-point-in-time \
  --source-table-name TABLE_NAME \
  --target-table-name TABLE_NAME_RESTORED \
  --restore-date-time 2024-01-20T10:00:00Z
```

**Lambda Rollback:**
```bash
# Revert to previous version
aws lambda update-alias \
  --function-name FUNCTION_NAME \
  --name prod \
  --function-version PREVIOUS_VERSION
```

---

## 13. Monitoring & Observability

### 13.1 CloudWatch Metrics

#### 13.1.1 Lambda Metrics

**Standard Metrics:**
- Invocations
- Errors
- Duration
- Throttles
- Concurrent Executions
- Dead Letter Errors

**Custom Metrics:**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def log_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='HospitalClaimOptimizer',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }]
    )

# Usage
log_metric('ClaimProcessed', 1)
log_metric('ProcessingTime', 1.5, 'Seconds')
```

#### 13.1.2 API Gateway Metrics

**Metrics:**
- Count (requests)
- 4XXError
- 5XXError
- Latency
- IntegrationLatency
- CacheHitCount
- CacheMissCount

#### 13.1.3 DynamoDB Metrics

**Metrics:**
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors
- ThrottledRequests

#### 13.1.4 Application Metrics

**Business Metrics:**
```python
# Track business KPIs
log_metric('ClaimsSubmitted', 1)
log_metric('SettlementRatio', 0.87, 'None')
log_metric('HighRiskClaims', 1)
log_metric('PolicyUploaded', 1)
log_metric('EligibilityChecks', 1)
```

### 13.2 CloudWatch Logs

#### 13.2.1 Log Groups

**Lambda Functions:**
- `/aws/lambda/auth-handler`
- `/aws/lambda/policy-management`
- `/aws/lambda/eligibility-checker`
- `/aws/lambda/bill-audit`
- And 10 more...

**API Gateway:**
- `/aws/apigateway/hospital-claim-optimizer`

**Retention:**
- Development: 7 days
- Staging: 30 days
- Production: 90 days

#### 13.2.2 Structured Logging

**Log Format:**
```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(event_type, data):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data,
        'request_id': context.aws_request_id
    }
    logger.info(json.dumps(log_entry))

# Usage
log_event('claim_processed', {
    'claim_id': 'CLM-123',
    'risk_level': 'medium',
    'processing_time': 1.5
})
```

#### 13.2.3 Log Insights Queries

**Error Rate:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
```

**Slow Requests:**
```
fields @timestamp, @duration
| filter @duration > 1000
| sort @duration desc
| limit 20
```

**User Activity:**
```
fields @timestamp, user_id, action
| filter event_type = "user_action"
| stats count() by user_id
```

### 13.3 CloudWatch Alarms

#### 13.3.1 Lambda Alarms

**Error Rate:**
```python
alarm = cloudwatch.Alarm(
    alarm_name='lambda-error-rate',
    metric=lambda_function.metric_errors(),
    threshold=10,
    evaluation_periods=2,
    comparison_operator='GreaterThanThreshold'
)
```

**Duration:**
```python
alarm = cloudwatch.Alarm(
    alarm_name='lambda-duration',
    metric=lambda_function.metric_duration(),
    threshold=5000,  # 5 seconds
    evaluation_periods=2,
    statistic='Average'
)
```

#### 13.3.2 API Gateway Alarms

**5XX Errors:**
```python
alarm = cloudwatch.Alarm(
    alarm_name='api-5xx-errors',
    metric_name='5XXError',
    namespace='AWS/ApiGateway',
    threshold=10,
    evaluation_periods=2
)
```

**Latency:**
```python
alarm = cloudwatch.Alarm(
    alarm_name='api-latency',
    metric_name='Latency',
    namespace='AWS/ApiGateway',
    threshold=1000,  # 1 second
    statistic='p95'
)
```

#### 13.3.3 DynamoDB Alarms

**Throttling:**
```python
alarm = cloudwatch.Alarm(
    alarm_name='dynamodb-throttling',
    metric_name='UserErrors',
    namespace='AWS/DynamoDB',
    threshold=10,
    evaluation_periods=2
)
```

#### 13.3.4 Notification Actions

**SNS Topic:**
```python
topic = sns.Topic(
    self, 'AlarmTopic',
    display_name='Claim Optimizer Alarms'
)

# Subscribe email
topic.add_subscription(
    subscriptions.EmailSubscription('ops@example.com')
)

# Add to alarm
alarm.add_alarm_action(
    actions.SnsAction(topic)
)
```

### 13.4 X-Ray Tracing

**Enable Tracing:**
```python
lambda_function = lambda_.Function(
    self, 'Function',
    tracing=lambda_.Tracing.ACTIVE
)
```

**Instrument Code:**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

@xray_recorder.capture('process_claim')
def process_claim(claim_data):
    # Function logic
    pass
```

**View Traces:**
- AWS Console → X-Ray → Traces
- Filter by service, error, latency
- View service map
- Analyze bottlenecks

### 13.5 Dashboards

#### 13.5.1 Operational Dashboard

**Widgets:**
1. API Request Count (line chart)
2. Error Rate (line chart)
3. Latency p95 (line chart)
4. Lambda Invocations (bar chart)
5. DynamoDB Operations (line chart)
6. Active Users (number)

**CloudFormation:**
```python
dashboard = cloudwatch.Dashboard(
    self, 'OperationalDashboard',
    dashboard_name='claim-optimizer-ops'
)

dashboard.add_widgets(
    cloudwatch.GraphWidget(
        title='API Requests',
        left=[api.metric_count()]
    ),
    cloudwatch.GraphWidget(
        title='Error Rate',
        left=[api.metric_client_error(), api.metric_server_error()]
    )
)
```

#### 13.5.2 Business Dashboard

**Metrics:**
1. Claims Submitted (today)
2. Average Settlement Ratio
3. High-Risk Claims
4. Processing Time
5. Cost Savings
6. Active Policies

### 13.6 Error Tracking

**Sentry Integration:**
```python
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    integrations=[AwsLambdaIntegration()],
    environment=os.environ['APP_ENV'],
    traces_sample_rate=0.1
)

# Errors automatically captured
```

**Custom Error Tracking:**
```python
def track_error(error, context):
    sentry_sdk.capture_exception(error)
    
    # Also log to CloudWatch
    logger.error(f"Error: {str(error)}", extra={
        'error_type': type(error).__name__,
        'context': context
    })
```

### 13.7 Performance Monitoring

**Response Time Tracking:**
```python
import time

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        log_metric('FunctionDuration', duration, 'Seconds')
        
        if duration > 1.0:
            logger.warning(f"Slow function: {func.__name__} took {duration}s")
        
        return result
    return wrapper

@monitor_performance
def process_claim(claim_data):
    # Function logic
    pass
```

**Database Query Monitoring:**
```python
def monitor_query(operation, table_name):
    start = time.time()
    # Execute query
    duration = time.time() - start
    
    log_metric(f'DynamoDB_{operation}', duration, 'Seconds')
```

### 13.8 Cost Monitoring

#### 13.8.1 AWS Cost Explorer

**Track Costs by Service:**
- Lambda invocations and duration
- DynamoDB read/write units
- S3 storage and requests
- CloudFront data transfer
- API Gateway requests

**Cost Allocation Tags:**
```python
# Tag resources for cost tracking
tags = {
    'Environment': 'production',
    'Project': 'claim-optimizer',
    'CostCenter': 'engineering',
    'Owner': 'platform-team'
}
```

**Budget Alerts:**
```python
budget = budgets.CfnBudget(
    self, 'MonthlyBudget',
    budget={
        'budgetName': 'claim-optimizer-monthly',
        'budgetLimit': {
            'amount': 5000,
            'unit': 'USD'
        },
        'timeUnit': 'MONTHLY',
        'budgetType': 'COST'
    },
    notifications_with_subscribers=[{
        'notification': {
            'notificationType': 'ACTUAL',
            'comparisonOperator': 'GREATER_THAN',
            'threshold': 80
        },
        'subscribers': [{
            'subscriptionType': 'EMAIL',
            'address': 'ops@example.com'
        }]
    }]
)
```

#### 13.8.2 Cost Optimization

**Lambda Optimization:**
- Right-size memory allocation
- Reduce cold starts
- Use reserved concurrency
- Optimize dependencies

**DynamoDB Optimization:**
- Use on-demand for variable workloads
- Implement caching
- Optimize query patterns
- Use batch operations

**S3 Optimization:**
- Implement lifecycle policies
- Use intelligent tiering
- Compress objects
- Delete unused objects

**CloudFront Optimization:**
- Optimize cache hit ratio
- Use appropriate TTLs
- Compress content
- Use regional edge caches

### 13.9 Alerting Strategy

#### 13.9.1 Alert Severity Levels

**Critical (P1):**
- System down
- Data loss
- Security breach
- Response: Immediate (< 5 minutes)

**High (P2):**
- Major feature broken
- High error rate
- Performance degradation
- Response: < 30 minutes

**Medium (P3):**
- Minor feature issue
- Elevated error rate
- Slow performance
- Response: < 2 hours

**Low (P4):**
- Cosmetic issues
- Non-critical warnings
- Optimization opportunities
- Response: Next business day

#### 13.9.2 Alert Routing

**PagerDuty Integration:**
```python
# Configure PagerDuty for critical alerts
pagerduty_topic = sns.Topic(
    self, 'PagerDutyTopic',
    display_name='Critical Alerts'
)

# Subscribe PagerDuty endpoint
pagerduty_topic.add_subscription(
    subscriptions.UrlSubscription(
        'https://events.pagerduty.com/integration/xxx/enqueue'
    )
)

# Add to critical alarms
critical_alarm.add_alarm_action(
    actions.SnsAction(pagerduty_topic)
)
```

**Slack Integration:**
```python
# Configure Slack for non-critical alerts
slack_topic = sns.Topic(
    self, 'SlackTopic',
    display_name='Non-Critical Alerts'
)

# Lambda function to format and send to Slack
slack_forwarder = lambda_.Function(
    self, 'SlackForwarder',
    runtime=lambda_.Runtime.PYTHON_3_11,
    handler='slack_forwarder.handler',
    code=lambda_.Code.from_asset('lambda/slack-forwarder'),
    environment={
        'SLACK_WEBHOOK_URL': slack_webhook_url
    }
)

slack_topic.add_subscription(
    subscriptions.LambdaSubscription(slack_forwarder)
)
```

#### 13.9.3 Alert Suppression

**Maintenance Windows:**
```python
# Suppress alerts during maintenance
def suppress_alerts(start_time, end_time):
    """Disable alarms during maintenance window"""
    alarms = cloudwatch.describe_alarms()
    
    for alarm in alarms['MetricAlarms']:
        cloudwatch.disable_alarm_actions(
            AlarmNames=[alarm['AlarmName']]
        )
    
    # Schedule re-enable
    schedule_enable_alarms(end_time)
```

**Alert Deduplication:**
- Group related alerts
- Suppress duplicate notifications
- Aggregate similar issues
- Rate limit notifications

### 13.10 Compliance Monitoring

#### 13.10.1 Audit Trail Monitoring

**Track Compliance Events:**
```python
# Monitor for compliance violations
compliance_events = [
    'unauthorized_access',
    'data_export',
    'policy_change',
    'user_deletion',
    'encryption_disabled'
]

for event in compliance_events:
    alarm = cloudwatch.Alarm(
        alarm_name=f'compliance-{event}',
        metric_name=event,
        namespace='Compliance',
        threshold=1,
        evaluation_periods=1,
        comparison_operator='GreaterThanOrEqualToThreshold'
    )
```

#### 13.10.2 Security Monitoring

**AWS GuardDuty:**
- Enable threat detection
- Monitor for suspicious activity
- Alert on security findings
- Integrate with incident response

**AWS Config:**
- Track resource configurations
- Monitor compliance rules
- Alert on non-compliant resources
- Automated remediation

**CloudTrail:**
- Log all API calls
- Monitor for unusual patterns
- Alert on sensitive operations
- Retain logs for compliance

---


## 14. Development Workflow

### 14.1 Local Development Setup

#### 14.1.1 Prerequisites Installation

**macOS Setup:**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node@18

# Install Python
brew install python@3.11

# Install AWS CLI
brew install awscli

# Install AWS CDK
npm install -g aws-cdk

# Install Git
brew install git
```

**Verify Installation:**
```bash
node --version  # v18.x.x
python3 --version  # 3.11.x
aws --version  # aws-cli/2.x.x
cdk --version  # 2.x.x
git --version  # 2.x.x
```

#### 14.1.2 Repository Setup

**Clone Repository:**
```bash
git clone https://github.com/your-org/hospital-claim-optimizer.git
cd hospital-claim-optimizer
```

**Install Backend Dependencies:**
```bash
cd hospital-claim-optimizer
npm install
pip install -r requirements.txt
```

**Install Frontend Dependencies:**
```bash
cd ../frontend
npm install
```


#### 14.1.3 Environment Configuration

**Backend Configuration:**
```bash
cd hospital-claim-optimizer
cp .env.example .env
# Edit .env with local values
```

**Frontend Configuration:**
```bash
cd frontend
cp .env.example .env
# Edit .env
VITE_API_BASE_URL=http://localhost:3000
VITE_APP_ENV=development
```

**AWS Configuration:**
```bash
aws configure
# Enter your AWS credentials
# Region: us-east-1
# Output format: json
```

#### 14.1.4 Running Locally

**Start Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

**Test Lambda Functions Locally:**
```bash
cd hospital-claim-optimizer
# Use SAM CLI for local testing
sam local start-api
```

**Run Tests:**
```bash
# Backend tests
cd hospital-claim-optimizer
pytest tests/ -v

# Frontend tests (if configured)
cd frontend
npm test
```


### 14.2 Git Workflow

#### 14.2.1 Branching Strategy

**Branch Types:**
- `main` - Production-ready code
- `staging` - Pre-production testing
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency production fixes

**Branch Naming:**
```bash
feature/user-authentication
feature/policy-versioning
bugfix/login-error
hotfix/security-patch
```

#### 14.2.2 Feature Development Flow

**1. Create Feature Branch:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/new-feature
```

**2. Make Changes:**
```bash
# Edit files
git add .
git commit -m "feat: add new feature"
```

**3. Keep Updated:**
```bash
git fetch origin
git rebase origin/develop
```

**4. Push Branch:**
```bash
git push origin feature/new-feature
```

**5. Create Pull Request:**
- Open PR on GitHub
- Request reviews
- Address feedback
- Merge when approved


#### 14.2.3 Hotfix Flow

**1. Create Hotfix Branch:**
```bash
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug
```

**2. Fix and Test:**
```bash
# Make fix
git add .
git commit -m "hotfix: fix critical bug"
```

**3. Merge to Main and Develop:**
```bash
# Merge to main
git checkout main
git merge hotfix/critical-bug
git push origin main

# Merge to develop
git checkout develop
git merge hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

### 14.3 Code Review Process

#### 14.3.1 Pull Request Guidelines

**PR Title Format:**
```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Build/tooling changes
```

**PR Description Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```


#### 14.3.2 Review Checklist

**Code Quality:**
- [ ] Code is readable and maintainable
- [ ] No code duplication
- [ ] Functions are small and focused
- [ ] Proper error handling
- [ ] No hardcoded values
- [ ] Security best practices followed

**Testing:**
- [ ] Unit tests included
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] No test coverage decrease

**Documentation:**
- [ ] Code comments where needed
- [ ] API documentation updated
- [ ] README updated if needed
- [ ] CHANGELOG updated

**Performance:**
- [ ] No performance regressions
- [ ] Efficient algorithms used
- [ ] Database queries optimized
- [ ] Caching implemented where appropriate

#### 14.3.3 Review Process

**1. Automated Checks:**
- Linting passes
- Tests pass
- Build succeeds
- Security scan passes

**2. Peer Review:**
- At least 2 approvals required
- Senior developer approval for critical changes
- All comments addressed

**3. Merge:**
- Squash and merge for feature branches
- Merge commit for release branches
- Delete branch after merge


### 14.4 Code Standards

#### 14.4.1 Python Code Standards

**Style Guide:** PEP 8

**Formatting:**
```python
# Use 4 spaces for indentation
# Maximum line length: 100 characters
# Use snake_case for functions and variables
# Use PascalCase for classes

# Good
def calculate_settlement_ratio(approved_amount, total_amount):
    """Calculate the settlement ratio for a claim."""
    if total_amount == 0:
        return 0.0
    return approved_amount / total_amount

# Bad
def CalculateSettlementRatio(ApprovedAmount,TotalAmount):
    if TotalAmount==0:return 0.0
    return ApprovedAmount/TotalAmount
```

**Docstrings:**
```python
def process_claim(claim_data: dict) -> dict:
    """
    Process a medical claim and generate audit results.
    
    Args:
        claim_data: Dictionary containing claim information
            - claim_id: Unique claim identifier
            - patient_id: Patient identifier
            - line_items: List of claim line items
    
    Returns:
        Dictionary containing audit results
            - risk_level: Risk assessment (low/medium/high)
            - settlement_ratio: Estimated settlement ratio
            - recommendations: List of optimization suggestions
    
    Raises:
        ValueError: If claim_data is invalid
        PolicyNotFoundError: If policy doesn't exist
    """
    pass
```


#### 14.4.2 TypeScript Code Standards

**Style Guide:** Airbnb TypeScript Style Guide

**Formatting:**
```typescript
// Use 2 spaces for indentation
// Maximum line length: 100 characters
// Use camelCase for functions and variables
// Use PascalCase for classes and interfaces

// Good
interface ClaimData {
  claimId: string;
  patientId: string;
  amount: number;
}

function calculateSettlementRatio(
  approvedAmount: number,
  totalAmount: number
): number {
  if (totalAmount === 0) {
    return 0;
  }
  return approvedAmount / totalAmount;
}

// Bad
interface claim_data {
  claim_id:string
  patient_id:string
  amount:number
}

function CalculateSettlementRatio(ApprovedAmount,TotalAmount) {
  if(TotalAmount===0)return 0
  return ApprovedAmount/TotalAmount
}
```

**JSDoc Comments:**
```typescript
/**
 * Process a medical claim and generate audit results
 * @param claimData - Claim information object
 * @returns Audit results with risk assessment
 * @throws {Error} If claim data is invalid
 */
function processClaim(claimData: ClaimData): AuditResult {
  // Implementation
}
```


#### 14.4.3 Linting Configuration

**Python (Flake8):**
```ini
# .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,node_modules
ignore = E203,W503
```

**TypeScript (ESLint):**
```javascript
// eslint.config.js
export default {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
  ],
  rules: {
    'max-len': ['error', { code: 100 }],
    'no-console': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'warn',
  },
};
```

**Run Linters:**
```bash
# Python
flake8 lambda-layers/common/python/

# TypeScript
npm run lint
npm run lint:fix
```

### 14.5 Commit Conventions

#### 14.5.1 Commit Message Format

**Structure:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes
- `perf`: Performance improvements


**Examples:**
```bash
# Feature
git commit -m "feat(auth): add MFA support"

# Bug fix
git commit -m "fix(policy): correct version comparison logic"

# Documentation
git commit -m "docs(api): update authentication endpoints"

# With body
git commit -m "feat(batch): add CSV batch processing

- Implement CSV parser
- Add batch orchestrator
- Create worker function
- Add progress tracking

Closes #123"
```

#### 14.5.2 Commit Best Practices

**Do:**
- Write clear, descriptive messages
- Use present tense ("add" not "added")
- Keep subject line under 50 characters
- Separate subject from body with blank line
- Reference issue numbers in footer
- Make atomic commits (one logical change)

**Don't:**
- Commit commented-out code
- Commit debug statements
- Commit sensitive data
- Make huge commits with multiple changes
- Use vague messages like "fix bug" or "update code"

### 14.6 Pull Request Templates

**Feature PR Template:**
```markdown
## Feature Description
[Describe the feature and its purpose]

## Implementation Details
- [Key implementation point 1]
- [Key implementation point 2]

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots]

## Related Issues
Closes #[issue number]
```


**Bug Fix PR Template:**
```markdown
## Bug Description
[Describe the bug]

## Root Cause
[Explain what caused the bug]

## Fix Description
[Explain how the bug was fixed]

## Testing
- [ ] Bug reproduced before fix
- [ ] Bug no longer occurs after fix
- [ ] Regression tests added
- [ ] Related functionality tested

## Related Issues
Fixes #[issue number]
```

### 14.7 Development Tools

#### 14.7.1 Recommended IDE Setup

**Visual Studio Code Extensions:**
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- AWS Toolkit
- GitLens
- Thunder Client (API testing)
- Error Lens

**VS Code Settings:**
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

#### 14.7.2 Command Line Tools

**Useful Aliases:**
```bash
# Add to ~/.zshrc or ~/.bashrc

# AWS shortcuts
alias awslogin='aws sso login'
alias awswho='aws sts get-caller-identity'

# CDK shortcuts
alias cdkdiff='cdk diff'
alias cdkdeploy='cdk deploy --require-approval never'
alias cdksynth='cdk synth'

# Testing shortcuts
alias pytest-all='pytest tests/ -v'
alias pytest-cov='pytest tests/ --cov=lambda-layers/common/python'
alias pytest-pbt='pytest tests/test_property_*.py -v'

# Frontend shortcuts
alias fe-dev='cd frontend && npm run dev'
alias fe-build='cd frontend && npm run build'
alias fe-lint='cd frontend && npm run lint'

# Git shortcuts
alias gs='git status'
alias gp='git pull'
alias gc='git commit -m'
alias gco='git checkout'
```

**Helper Scripts:**
```bash
# scripts/dev-setup.sh
#!/bin/bash
# Quick development environment setup

echo "Setting up development environment..."

# Install backend dependencies
cd hospital-claim-optimizer
npm install
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Configure AWS
aws configure

# Bootstrap CDK
cdk bootstrap

echo "Setup complete!"
```

#### 14.7.3 Debugging Tools

**Python Debugger (pdb):**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

**Browser DevTools:**
- Console: View logs and errors
- Network: Monitor API calls
- Application: Inspect localStorage/cookies
- Performance: Profile page load
- Sources: Debug JavaScript

**AWS CLI Debugging:**
```bash
# Enable debug output
aws lambda invoke --debug \
  --function-name FUNCTION_NAME \
  output.json

# View CloudWatch logs
aws logs tail /aws/lambda/FUNCTION_NAME --follow

# Test API Gateway locally
sam local start-api --debug
```

### 14.8 Code Quality Tools

#### 14.8.1 Static Analysis

**Python - Flake8:**
```bash
# Install
pip install flake8

# Run
flake8 lambda-layers/common/python/

# Configuration in .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv
ignore = E203,W503
```

**Python - Pylint:**
```bash
# Install
pip install pylint

# Run
pylint lambda-layers/common/python/

# Configuration in .pylintrc
[MASTER]
max-line-length=100
disable=C0111,R0903
```

**Python - MyPy (Type Checking):**
```bash
# Install
pip install mypy

# Run
mypy lambda-layers/common/python/

# Configuration in mypy.ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

**TypeScript - ESLint:**
```bash
# Run
npm run lint

# Fix automatically
npm run lint:fix

# Configuration in eslint.config.js
```

#### 14.8.2 Code Formatting

**Python - Black:**
```bash
# Install
pip install black

# Format files
black lambda-layers/common/python/

# Check without modifying
black --check lambda-layers/common/python/

# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**TypeScript - Prettier:**
```bash
# Format files
npm run format

# Check formatting
npm run format:check

# Configuration in .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

#### 14.8.3 Security Scanning

**Python Dependencies:**
```bash
# Install pip-audit
pip install pip-audit

# Scan for vulnerabilities
pip-audit

# Fix vulnerabilities
pip-audit --fix
```

**Node Dependencies:**
```bash
# Scan for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix

# Force fix (may break things)
npm audit fix --force
```

**OWASP Dependency Check:**
```bash
# Install
brew install dependency-check

# Scan project
dependency-check --project "Claim Optimizer" \
  --scan . \
  --format HTML \
  --out reports/
```

#### 14.8.4 Code Coverage

**Python Coverage:**
```bash
# Install
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=lambda-layers/common/python

# Generate HTML report
pytest tests/ --cov=lambda-layers/common/python --cov-report=html

# View report
open htmlcov/index.html
```

**Coverage Thresholds:**
```ini
# .coveragerc
[run]
source = lambda-layers/common/python

[report]
fail_under = 80
show_missing = True
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### 14.9 Documentation Standards

#### 14.9.1 Code Documentation

**Python Docstrings (Google Style):**
```python
def calculate_settlement_ratio(approved_amount: float, total_amount: float) -> float:
    """Calculate the settlement ratio for a claim.
    
    The settlement ratio represents the percentage of the claim amount
    that was approved by the insurance company.
    
    Args:
        approved_amount: The amount approved by insurance (in dollars)
        total_amount: The total claim amount (in dollars)
    
    Returns:
        The settlement ratio as a decimal between 0 and 1
    
    Raises:
        ValueError: If total_amount is zero or negative
        TypeError: If arguments are not numeric
    
    Example:
        >>> calculate_settlement_ratio(800, 1000)
        0.8
    """
    if total_amount <= 0:
        raise ValueError("Total amount must be positive")
    
    return approved_amount / total_amount
```

**TypeScript JSDoc:**
```typescript
/**
 * Calculate the settlement ratio for a claim
 * 
 * @param approvedAmount - The amount approved by insurance
 * @param totalAmount - The total claim amount
 * @returns The settlement ratio as a decimal between 0 and 1
 * @throws {Error} If total amount is zero or negative
 * 
 * @example
 * ```typescript
 * const ratio = calculateSettlementRatio(800, 1000);
 * console.log(ratio); // 0.8
 * ```
 */
function calculateSettlementRatio(
  approvedAmount: number,
  totalAmount: number
): number {
  if (totalAmount <= 0) {
    throw new Error('Total amount must be positive');
  }
  
  return approvedAmount / totalAmount;
}
```

#### 14.9.2 API Documentation

**OpenAPI/Swagger:**
```yaml
# Location: hospital-claim-optimizer/openapi.yaml
# Complete API specification with:
# - Endpoints
# - Request/response schemas
# - Authentication
# - Error codes
```

**Generate Documentation:**
```bash
# Install Swagger UI
npm install -g swagger-ui-watcher

# Serve documentation
swagger-ui-watcher openapi.yaml
```

#### 14.9.3 Architecture Documentation

**Architecture Decision Records (ADRs):**
```markdown
# ADR-001: Use DynamoDB for Data Storage

## Status
Accepted

## Context
We need a database solution that can scale automatically and handle
variable workloads without manual intervention.

## Decision
Use Amazon DynamoDB with on-demand billing mode.

## Consequences
Positive:
- Automatic scaling
- No server management
- Pay-per-use pricing
- Built-in backup and recovery

Negative:
- Limited query flexibility
- Learning curve for NoSQL
- Potential for higher costs at scale
```

**System Diagrams:**
- Use draw.io or Lucidchart
- Store in `docs/diagrams/`
- Include in technical documentation
- Update with architecture changes

### 14.10 Continuous Improvement

#### 14.10.1 Code Reviews

**Review Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Error handling is proper
- [ ] Logging is appropriate
- [ ] No breaking changes (or documented)

**Review Best Practices:**
- Review within 24 hours
- Provide constructive feedback
- Ask questions, don't demand changes
- Approve when ready, don't nitpick
- Learn from others' code

#### 14.10.2 Retrospectives

**Sprint Retrospectives:**
- Frequency: Every 2 weeks
- Duration: 1 hour
- Format: What went well, what didn't, action items

**Topics to Discuss:**
- Development velocity
- Code quality issues
- Testing challenges
- Deployment problems
- Team collaboration
- Tool improvements

**Action Items:**
- Document decisions
- Assign owners
- Set deadlines
- Track progress
- Review in next retro

#### 14.10.3 Technical Debt

**Track Technical Debt:**
```markdown
# Technical Debt Log

## High Priority
- [ ] Refactor policy extraction logic (complexity: high)
- [ ] Add caching to eligibility checks (impact: high)
- [ ] Optimize DynamoDB queries (cost: high)

## Medium Priority
- [ ] Improve error messages (UX: medium)
- [ ] Add integration tests (coverage: medium)
- [ ] Update dependencies (security: medium)

## Low Priority
- [ ] Refactor CSS styles (maintainability: low)
- [ ] Add code comments (documentation: low)
- [ ] Optimize images (performance: low)
```

**Debt Reduction:**
- Allocate 20% of sprint capacity
- Prioritize by impact and effort
- Track debt over time
- Celebrate debt reduction

#### 14.10.4 Learning and Development

**Knowledge Sharing:**
- Weekly tech talks
- Code walkthroughs
- Pair programming sessions
- Documentation reviews
- External conference attendance

**Training Resources:**
- AWS training and certification
- Online courses (Udemy, Coursera)
- Technical books
- Conference talks
- Internal workshops

**Skill Development:**
- Set learning goals
- Practice new technologies
- Contribute to open source
- Write technical blog posts
- Mentor junior developers

---


## 15. Troubleshooting

### 15.1 Common Issues

#### 15.1.1 Authentication Issues

**Problem: "Invalid or expired token" error**

**Symptoms:**
- 401 Unauthorized responses
- User logged out unexpectedly
- API calls failing

**Solutions:**
1. Check token expiration:
```bash
# Decode JWT token
echo "YOUR_TOKEN" | cut -d'.' -f2 | base64 -d | jq
```

2. Verify token in localStorage:
```javascript
// In browser console
console.log(localStorage.getItem('token'));
```

3. Clear and re-login:
```javascript
localStorage.clear();
// Navigate to /login
```

4. Check session in DynamoDB:
```bash
aws dynamodb get-item \
  --table-name hospital-claim-optimizer-sessions \
  --key '{"session_id": {"S": "SESSION_ID"}}'
```

**Problem: MFA code not working**

**Symptoms:**
- "Invalid MFA code" error
- Code always rejected

**Solutions:**
1. Check time synchronization:
```bash
# Ensure system time is correct
date
# Sync with NTP server if needed
sudo sntp -sS time.apple.com
```

2. Verify TOTP window:
- Code valid for 30 seconds
- Try entering code immediately after generation
- Check if backup codes work

3. Regenerate MFA secret:
- Disable MFA
- Re-enable and scan new QR code
- Verify with new code

#### 15.1.2 Policy Upload Issues

**Problem: Policy upload fails or times out**

**Symptoms:**
- Upload stuck at processing
- Timeout errors
- Low confidence scores

**Solutions:**
1. Check file size and format:
```bash
# File should be PDF, max 50MB
ls -lh policy.pdf
file policy.pdf
```

2. Verify S3 upload:
```bash
aws s3 ls s3://POLICY_BUCKET/policies/POLICY_ID/
```

3. Check Lambda logs:
```bash
aws logs tail /aws/lambda/policy-upload --follow
```

4. Check Textract status:
```bash
aws textract get-document-analysis \
  --job-id JOB_ID
```

5. Retry upload:
- Wait 5 minutes
- Try uploading again
- Check if policy already exists

**Problem: Low confidence scores**

**Symptoms:**
- Confidence score < 0.7
- Missing policy rules
- Incorrect extraction

**Solutions:**
1. Improve PDF quality:
- Ensure text is not scanned image
- Use high-resolution PDF
- Avoid handwritten content

2. Manual review:
- Review extracted text
- Manually correct rules
- Update policy in DynamoDB

3. Re-upload with better PDF:
- Get digital PDF from insurer
- Avoid scanned documents

#### 15.1.3 Eligibility Check Issues

**Problem: Eligibility check returns incorrect results**

**Symptoms:**
- Coverage status wrong
- Incorrect copay amounts
- Missing policy references

**Solutions:**
1. Verify policy data:
```bash
aws dynamodb get-item \
  --table-name hospital-claim-optimizer-policies \
  --key '{"policy_id": {"S": "POL-123"}, "version": {"N": "1"}}'
```

2. Check procedure code:
- Verify code format (CPT/ICD)
- Check if code exists in policy
- Try alternative codes

3. Review policy rules:
- Check coverage section
- Verify exclusions
- Check effective dates

4. Clear cache:
```bash
# Clear Redis cache
redis-cli -h REDIS_ENDPOINT
> DEL eligibility:PATIENT_ID:PROCEDURE
```

**Problem: Batch processing stuck**

**Symptoms:**
- Batch status "processing" for > 5 minutes
- No results returned
- Partial results only

**Solutions:**
1. Check batch status:
```bash
aws dynamodb get-item \
  --table-name hospital-claim-optimizer-batches \
  --key '{"batch_id": {"S": "BATCH-123"}}'
```

2. Check worker Lambda logs:
```bash
aws logs tail /aws/lambda/eligibility-worker --follow
```

3. Check SQS queue:
```bash
aws sqs get-queue-attributes \
  --queue-url QUEUE_URL \
  --attribute-names All
```

4. Retry batch:
- Cancel current batch
- Re-upload CSV
- Ensure CSV format is correct

#### 15.1.4 Claim Audit Issues

**Problem: Audit results seem incorrect**

**Symptoms:**
- Settlement ratio too low/high
- Items incorrectly rejected
- Missing recommendations

**Solutions:**
1. Verify claim data:
```bash
aws dynamodb get-item \
  --table-name hospital-claim-optimizer-claims \
  --key '{"claim_id": {"S": "CLM-123"}}'
```

2. Check policy coverage:
- Verify procedure codes
- Check policy limits
- Review exclusions

3. Review audit logic:
- Check audit_service.py
- Verify pricing validation
- Check documentation requirements

4. Manual review:
- Review audit results
- Override if necessary
- Add notes for future reference

**Problem: High-risk claims not flagged**

**Symptoms:**
- Risk level always "low"
- No high-risk alerts
- Risk score calculation wrong

**Solutions:**
1. Check risk scoring logic:
```python
# Review risk_scorer.py
# Verify risk factors
# Check thresholds
```

2. Verify claim amount:
- Check if amount exceeds limits
- Verify historical data
- Check procedure complexity

3. Update risk model:
- Adjust risk factors
- Update thresholds
- Retrain model if using ML

#### 15.1.5 Performance Issues

**Problem: Slow API responses**

**Symptoms:**
- Response time > 2 seconds
- Timeouts
- Poor user experience

**Solutions:**
1. Check CloudWatch metrics:
```bash
# View Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=FUNCTION_NAME \
  --start-time 2024-01-20T00:00:00Z \
  --end-time 2024-01-20T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum
```

2. Check DynamoDB throttling:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=TABLE_NAME \
  --start-time 2024-01-20T00:00:00Z \
  --end-time 2024-01-20T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

3. Enable caching:
- Check Redis connection
- Verify cache hit rate
- Increase TTL if needed

4. Optimize queries:
- Use GSI for queries
- Reduce data fetched
- Implement pagination

5. Increase Lambda memory:
```bash
aws lambda update-function-configuration \
  --function-name FUNCTION_NAME \
  --memory-size 1024
```

**Problem: High Lambda costs**

**Symptoms:**
- Unexpected AWS bill
- High invocation count
- Long execution times

**Solutions:**
1. Analyze CloudWatch metrics:
- Check invocation count
- Review duration metrics
- Identify expensive functions

2. Optimize code:
- Reduce cold starts
- Minimize dependencies
- Use connection pooling

3. Implement caching:
- Cache frequently accessed data
- Use ElastiCache
- Set appropriate TTLs

4. Review concurrency:
- Check concurrent executions
- Set reserved concurrency
- Implement throttling

#### 15.1.6 Database Issues

**Problem: DynamoDB throttling**

**Symptoms:**
- ProvisionedThroughputExceededException
- Slow queries
- Failed writes

**Solutions:**
1. Check capacity mode:
```bash
aws dynamodb describe-table \
  --table-name TABLE_NAME \
  | jq '.Table.BillingModeSummary'
```

2. Enable auto-scaling (if provisioned):
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/TABLE_NAME \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100
```

3. Switch to on-demand:
```bash
aws dynamodb update-table \
  --table-name TABLE_NAME \
  --billing-mode PAY_PER_REQUEST
```

4. Optimize queries:
- Use batch operations
- Implement exponential backoff
- Reduce query frequency

**Problem: Data inconsistency**

**Symptoms:**
- Stale data displayed
- Conflicting records
- Missing data

**Solutions:**
1. Check DynamoDB streams:
```bash
aws dynamodb describe-table \
  --table-name TABLE_NAME \
  | jq '.Table.StreamSpecification'
```

2. Verify cache invalidation:
- Clear Redis cache
- Check cache TTL
- Verify cache keys

3. Check for race conditions:
- Review concurrent updates
- Implement optimistic locking
- Use conditional writes

4. Restore from backup:
```bash
aws dynamodb restore-table-to-point-in-time \
  --source-table-name TABLE_NAME \
  --target-table-name TABLE_NAME_RESTORED \
  --restore-date-time 2024-01-20T10:00:00Z
```

#### 15.1.7 Frontend Issues

**Problem: Blank page or white screen**

**Symptoms:**
- Nothing displays
- Console errors
- Build errors

**Solutions:**
1. Check browser console:
```javascript
// Open DevTools (F12)
// Check Console tab for errors
// Check Network tab for failed requests
```

2. Verify API connection:
```javascript
// Check .env file
console.log(import.meta.env.VITE_API_BASE_URL);
```

3. Clear cache:
```bash
# Clear browser cache
# Or use incognito mode
```

4. Rebuild frontend:
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

**Problem: CORS errors**

**Symptoms:**
- "CORS policy" errors in console
- API calls blocked
- Preflight requests failing

**Solutions:**
1. Check API Gateway CORS:
```bash
aws apigateway get-method \
  --rest-api-id API_ID \
  --resource-id RESOURCE_ID \
  --http-method OPTIONS
```

2. Verify allowed origins:
- Check API Gateway configuration
- Ensure frontend URL is allowed
- Check for trailing slashes

3. Add CORS headers:
```python
# In Lambda response
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}
```

**Problem: Routing issues**

**Symptoms:**
- 404 on page refresh
- Routes not working
- Redirect loops

**Solutions:**
1. Check CloudFront configuration:
- Verify error pages
- Check origin settings
- Review cache behaviors

2. Update CloudFront error responses:
```bash
aws cloudfront update-distribution \
  --id DISTRIBUTION_ID \
  --distribution-config file://config.json
```

3. Add redirect rules to S3:
```json
{
  "IndexDocument": {
    "Suffix": "index.html"
  },
  "ErrorDocument": {
    "Key": "index.html"
  }
}
```

### 15.2 Debugging Tools

#### 15.2.1 CloudWatch Logs Insights

**Query Examples:**

**Find errors:**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Slow requests:**
```
fields @timestamp, @duration, @message
| filter @duration > 1000
| sort @duration desc
| limit 20
```

**User activity:**
```
fields @timestamp, user_id, action
| filter ispresent(user_id)
| stats count() by user_id
| sort count desc
```

**API errors by endpoint:**
```
fields @timestamp, endpoint, status_code
| filter status_code >= 400
| stats count() by endpoint, status_code
```

#### 15.2.2 X-Ray Debugging

**View service map:**
1. Open AWS Console → X-Ray
2. Select "Service map"
3. Identify bottlenecks
4. Click on service for details

**Analyze traces:**
1. Go to "Traces" tab
2. Filter by:
   - Error status
   - Response time
   - URL
   - User ID
3. Click trace for timeline
4. Review subsegments

**Common patterns:**
- Long database queries
- External API calls
- Cold starts
- Retry loops

#### 15.2.3 Local Debugging

**Debug Lambda locally:**
```bash
# Install SAM CLI
brew install aws-sam-cli

# Start local API
sam local start-api

# Invoke function
sam local invoke FunctionName --event event.json
```

**Debug with VS Code:**
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Lambda",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/lambda-functions/auth/auth_handler.py",
      "console": "integratedTerminal",
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  ]
}
```

**Test API endpoints:**
```bash
# Using curl
curl -X POST https://API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'

# Using httpie
http POST https://API_URL/auth/login \
  email=user@example.com \
  password=pass
```

### 15.3 Error Messages Reference

#### 15.3.1 Authentication Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| AUTH001 | Invalid credentials | Wrong email/password | Verify credentials, reset password |
| AUTH002 | Account locked | Too many failed attempts | Wait 30 minutes or contact admin |
| AUTH003 | MFA required | MFA enabled but not provided | Enter MFA code |
| AUTH004 | Invalid MFA code | Wrong TOTP code | Check time sync, try new code |
| AUTH005 | Session expired | Token expired | Re-login |
| AUTH006 | Insufficient permissions | User lacks required role | Contact admin for access |

#### 15.3.2 Policy Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| POL001 | Policy not found | Invalid policy ID | Verify policy exists |
| POL002 | Policy expired | Past expiration date | Upload new policy version |
| POL003 | Invalid PDF format | Corrupted or wrong format | Re-upload valid PDF |
| POL004 | Extraction failed | Textract error | Retry or use better quality PDF |
| POL005 | Low confidence score | Poor extraction quality | Manual review required |
| POL006 | Version conflict | Concurrent updates | Retry with latest version |

#### 15.3.3 Claim Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| CLM001 | Invalid claim data | Missing required fields | Provide all required data |
| CLM002 | Policy not active | Policy expired or inactive | Use active policy |
| CLM003 | Procedure not covered | Not in policy coverage | Review policy or change procedure |
| CLM004 | Amount exceeds limit | Over policy limit | Reduce amount or split claim |
| CLM005 | Pre-auth required | Procedure needs authorization | Obtain pre-authorization |
| CLM006 | Duplicate claim | Claim already exists | Check existing claims |

#### 15.3.4 System Errors

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| SYS001 | Internal server error | Unexpected error | Check logs, contact support |
| SYS002 | Service unavailable | AWS service down | Wait and retry |
| SYS003 | Rate limit exceeded | Too many requests | Slow down requests |
| SYS004 | Database error | DynamoDB issue | Check CloudWatch, retry |
| SYS005 | Cache error | Redis connection failed | Check ElastiCache status |
| SYS006 | Timeout | Request took too long | Optimize query or increase timeout |

### 15.4 Support Escalation

#### 15.4.1 Support Levels

**Level 1: Self-Service**
- Check documentation
- Review error messages
- Search knowledge base
- Try troubleshooting steps

**Level 2: Team Support**
- Contact team lead
- Post in team Slack channel
- Create internal ticket
- Pair with senior developer

**Level 3: AWS Support**
- Open AWS support case
- Provide detailed information
- Include logs and metrics
- Follow up regularly

**Level 4: Vendor Support**
- Contact third-party vendors
- Provide integration details
- Share error logs
- Coordinate with AWS if needed

#### 15.4.2 Information to Collect

**For Bug Reports:**
- Error message (exact text)
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/videos
- Browser/device info
- User role and permissions
- Timestamp of occurrence
- Request ID (from logs)

**For Performance Issues:**
- CloudWatch metrics
- X-Ray traces
- Response times
- Affected endpoints
- Number of users impacted
- Time period
- Recent changes

**For Security Issues:**
- Incident description
- Affected resources
- Potential impact
- Discovery method
- Mitigation steps taken
- Evidence/logs

#### 15.4.3 Emergency Contacts

**On-Call Rotation:**
- Primary: [Name] - [Phone] - [Email]
- Secondary: [Name] - [Phone] - [Email]
- Manager: [Name] - [Phone] - [Email]

**Escalation Path:**
1. On-call engineer (immediate)
2. Team lead (15 minutes)
3. Engineering manager (30 minutes)
4. CTO (1 hour)

**Communication Channels:**
- Slack: #incidents
- PagerDuty: [Integration]
- Email: ops@example.com
- Phone: [Emergency number]

### 15.5 Disaster Recovery

#### 15.5.1 Backup Verification

**Check DynamoDB backups:**
```bash
aws dynamodb list-backups \
  --table-name TABLE_NAME
```

**Check S3 versioning:**
```bash
aws s3api list-object-versions \
  --bucket BUCKET_NAME \
  --prefix policies/
```

**Verify point-in-time recovery:**
```bash
aws dynamodb describe-continuous-backups \
  --table-name TABLE_NAME
```

#### 15.5.2 Recovery Procedures

**Restore DynamoDB table:**
```bash
# From backup
aws dynamodb restore-table-from-backup \
  --target-table-name TABLE_NAME_RESTORED \
  --backup-arn BACKUP_ARN

# From point-in-time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name TABLE_NAME \
  --target-table-name TABLE_NAME_RESTORED \
  --restore-date-time 2024-01-20T10:00:00Z
```

**Restore S3 objects:**
```bash
# Restore specific version
aws s3api copy-object \
  --bucket BUCKET_NAME \
  --copy-source BUCKET_NAME/KEY?versionId=VERSION_ID \
  --key KEY

# Restore entire bucket
aws s3 sync s3://BACKUP_BUCKET/ s3://BUCKET_NAME/
```

**Rollback Lambda function:**
```bash
# List versions
aws lambda list-versions-by-function \
  --function-name FUNCTION_NAME

# Update alias to previous version
aws lambda update-alias \
  --function-name FUNCTION_NAME \
  --name prod \
  --function-version PREVIOUS_VERSION
```

#### 15.5.3 Incident Response

**1. Detection:**
- Monitor alerts
- User reports
- Automated checks

**2. Assessment:**
- Determine severity
- Identify affected systems
- Estimate impact

**3. Communication:**
- Notify stakeholders
- Update status page
- Post in incident channel

**4. Mitigation:**
- Implement temporary fix
- Restore from backup if needed
- Switch to backup systems

**5. Resolution:**
- Deploy permanent fix
- Verify functionality
- Monitor for recurrence

**6. Post-Mortem:**
- Document incident
- Identify root cause
- Create action items
- Update runbooks

### 15.6 Health Checks

#### 15.6.1 System Health Endpoints

**API Health Check:**
```bash
curl https://API_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  }
}
```

#### 15.6.2 Automated Health Checks

**CloudWatch Synthetics:**
```python
# Create canary for health monitoring
canary = synthetics.Canary(
    self, 'ApiHealthCanary',
    schedule=synthetics.Schedule.rate(Duration.minutes(5)),
    test=synthetics.Test.custom(
        handler='health_check.handler',
        code=synthetics.Code.from_asset('canaries/')
    )
)
```

**Health Check Script:**
```python
def handler(event, context):
    """Health check canary"""
    import requests
    
    # Check API
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    
    # Check critical endpoints
    endpoints = ['/auth/login', '/policies', '/dashboard']
    for endpoint in endpoints:
        response = requests.options(f"{API_URL}{endpoint}")
        assert response.status_code in [200, 204]
    
    return {'statusCode': 200, 'body': 'All checks passed'}
```

---

## Appendix

### A. Glossary

**Terms:**
- **CSR (Claim Settlement Ratio):** Percentage of claim amount approved by insurance
- **TPA (Third-Party Administrator):** Organization managing insurance claims
- **TOTP (Time-based One-Time Password):** MFA authentication method
- **GSI (Global Secondary Index):** DynamoDB index for alternate queries
- **TTL (Time To Live):** Cache or session expiration time
- **CDK (Cloud Development Kit):** Infrastructure as Code framework
- **IAM (Identity and Access Management):** AWS access control service
- **KMS (Key Management Service):** AWS encryption key management
- **SES (Simple Email Service):** AWS email sending service

### B. Acronyms

- **API:** Application Programming Interface
- **AWS:** Amazon Web Services
- **CDN:** Content Delivery Network
- **CORS:** Cross-Origin Resource Sharing
- **CSRF:** Cross-Site Request Forgery
- **DDoS:** Distributed Denial of Service
- **GDPR:** General Data Protection Regulation
- **HIPAA:** Health Insurance Portability and Accountability Act
- **HTTPS:** Hypertext Transfer Protocol Secure
- **JWT:** JSON Web Token
- **MFA:** Multi-Factor Authentication
- **RBAC:** Role-Based Access Control
- **REST:** Representational State Transfer
- **SDK:** Software Development Kit
- **SQL:** Structured Query Language
- **SSL/TLS:** Secure Sockets Layer / Transport Layer Security
- **XSS:** Cross-Site Scripting

### C. References

**AWS Documentation:**
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [CDK Developer Guide](https://docs.aws.amazon.com/cdk/)

**Framework Documentation:**
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Python Documentation](https://docs.python.org/3/)
- [Pytest Documentation](https://docs.pytest.org/)

**Security Standards:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [GDPR Guidelines](https://gdpr.eu/)

### D. Change Log

**Version 1.0 - January 24, 2026**
- Initial release
- Complete system documentation
- All features documented
- Troubleshooting guide added

---

**Document End**

For questions or updates, contact: engineering@example.com
