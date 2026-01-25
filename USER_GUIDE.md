# Hospital Insurance Claim Settlement Optimizer - User Guide

**Version:** 1.0  
**Last Updated:** January 2026  
**Product Name:** RevenueZ Hospital Claim Optimizer

---

## 🚀 Quick Access - Application URLs

**Base URL (Development):** http://localhost:5173/  
**Base URL (Production):** https://your-domain.com/

### Authentication Pages
- **Login:** http://localhost:5173/login
- **MFA Challenge:** http://localhost:5173/mfa-challenge
- **Password Reset:** http://localhost:5173/password-reset
- **Password Reset Confirm:** http://localhost:5173/password-reset/confirm

### TPA Administrator Pages
- **Dashboard:** http://localhost:5173/admin/dashboard
- **Policy Management:** http://localhost:5173/admin/policies
- **Reports:** http://localhost:5173/admin/reports
- **Audit Logs:** http://localhost:5173/admin/audit-logs
- **Settings:** http://localhost:5173/admin/settings

### Doctor Pages
- **Eligibility Check:** http://localhost:5173/doctor/eligibility

### Billing Staff Pages
- **Bill Audit:** http://localhost:5173/billing/audit
- **Patient Profile:** http://localhost:5173/billing/patient/:patientId (replace :patientId with actual patient ID)

### Hospital Administrator Pages
- **Dashboard:** http://localhost:5173/admin/dashboard
- **Audit Logs:** http://localhost:5173/admin/audit-logs
- **Reports:** http://localhost:5173/admin/reports

### API Endpoints (Backend - After Deployment)
- **Base API URL:** https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/
- **Policy Upload:** POST /policy
- **Eligibility Check:** POST /check-eligibility
- **Bill Audit:** POST /audit-claim
- **Risk Score:** POST /risk-score
- **Dashboard:** GET /dashboard
- **Reports:** POST /reports/generate

**Note:** Replace `localhost:5173` with your production domain after deployment.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Authentication and Security](#authentication-and-security)
5. [TPA Administrator Guide](#tpa-administrator-guide)
6. [Doctor Guide](#doctor-guide)
7. [Billing Staff Guide](#billing-staff-guide)
8. [Hospital Administrator Guide](#hospital-administrator-guide)
9. [Settings and Configuration](#settings-and-configuration)
10. [Reports and Analytics](#reports-and-analytics)
11. [Troubleshooting](#troubleshooting)
12. [FAQs](#faqs)
13. [Support and Contact](#support-and-contact)

---

## 1. Introduction

### What is RevenueZ Hospital Claim Optimizer?

RevenueZ Hospital Claim Optimizer is an AI-powered B2B SaaS platform designed to help hospitals maximize their insurance claim settlement ratios (CSR) through intelligent document analysis, real-time eligibility checking, and automated bill auditing.

### Key Benefits

- **Increase Settlement Ratios**: Improve from industry average of ~70% to 85%+
- **Reduce Processing Time**: Cut claim processing time by 60%
- **Minimize Rejections**: AI-powered pre-submission audits catch issues early
- **Real-time Insights**: Instant eligibility checks and risk assessments
- **Compliance Ready**: HIPAA-compliant with comprehensive audit trails

### System Requirements

**Supported Browsers:**
- Google Chrome 90+ (Recommended)
- Mozilla Firefox 88+
- Safari 14+
- Microsoft Edge 90+

**Internet Connection:**
- Minimum 5 Mbps for optimal performance
- Stable connection required for real-time features

**Screen Resolution:**
- Minimum: 1280x720
- Recommended: 1920x1080 or higher


---

## 2. Getting Started

### Accessing the System

1. **Navigate to the Application URL**
   - Open your web browser
   - Enter the URL provided by your administrator (e.g., `https://app.revenuez.com`)
   - Bookmark the page for easy access

2. **First-Time Login**
   - You will receive an email invitation with temporary credentials
   - Click the activation link in the email
   - Set your permanent password (minimum 12 characters, must include uppercase, lowercase, number, and special character)
   - Complete Multi-Factor Authentication (MFA) setup if required

3. **Dashboard Overview**
   - After login, you'll land on your role-specific dashboard
   - Navigation menu on the left side
   - Notifications and alerts in the top-right corner
   - User profile menu in the top-right corner

### Quick Start Checklist

**For TPA Administrators:**
- [ ] Upload first insurance policy
- [ ] Review policy extraction results
- [ ] Configure webhook integrations
- [ ] Set up email notification preferences
- [ ] Invite team members

**For Doctors:**
- [ ] Complete profile setup
- [ ] Perform first eligibility check
- [ ] Download CSV template for batch checks
- [ ] Save frequently used procedure codes

**For Billing Staff:**
- [ ] Review pending claims
- [ ] Submit first bill for audit
- [ ] Review optimization suggestions
- [ ] Set up notification preferences

**For Hospital Administrators:**
- [ ] Review dashboard metrics
- [ ] Generate first performance report
- [ ] Review audit logs
- [ ] Configure user roles and permissions


---

## 3. User Roles and Permissions

### Role Overview

The system supports four primary user roles, each with specific permissions and access levels:

#### TPA Administrator
**Full Access** - Complete system control

**Permissions:**
- Upload and manage insurance policies
- View and manage all claims across hospitals
- Configure system settings and integrations
- Generate reports and analytics
- Manage user accounts and permissions
- Access audit logs
- Configure webhooks and notifications
- Compare policy versions and rollback changes

**Typical Users:** TPA managers, system administrators, compliance officers

#### Hospital Administrator
**Hospital-Level Access** - Full access within assigned hospital(s)

**Permissions:**
- View all claims for their hospital
- Generate hospital-specific reports
- Access audit logs for their hospital
- Manage hospital staff accounts
- View policy information
- Monitor performance metrics

**Typical Users:** Hospital CFOs, operations managers, compliance officers

#### Billing Staff
**Claim Management Access** - Create and manage claims

**Permissions:**
- Create and submit medical bills
- Run bill audits
- View audit results and optimization suggestions
- Access patient profiles and claim history
- View policy information
- Export claim data

**Typical Users:** Medical billing specialists, revenue cycle staff, claims processors

#### Doctor
**Limited Access** - Eligibility checking only

**Permissions:**
- Perform real-time eligibility checks
- Run batch eligibility checks
- View coverage information
- Generate pre-authorization templates
- View patient insurance information

**Typical Users:** Physicians, nurses, medical assistants, front desk staff

### Permission Matrix

| Feature | TPA Admin | Hospital Admin | Billing Staff | Doctor |
|---------|-----------|----------------|---------------|--------|
| Policy Upload | ✓ | ✗ | ✗ | ✗ |
| Policy View | ✓ | ✓ | ✓ | ✓ |
| Eligibility Check | ✓ | ✓ | ✓ | ✓ |
| Batch Eligibility | ✓ | ✓ | ✓ | ✓ |
| Bill Creation | ✓ | ✓ | ✓ | ✗ |
| Bill Audit | ✓ | ✓ | ✓ | ✗ |
| Dashboard Access | ✓ | ✓ | ✓ | ✗ |
| Reports | ✓ | ✓ | ✗ | ✗ |
| Audit Logs | ✓ | ✓ | ✗ | ✗ |
| User Management | ✓ | ✓ | ✗ | ✗ |
| System Settings | ✓ | ✗ | ✗ | ✗ |
| Webhooks | ✓ | ✗ | ✗ | ✗ |


---

## 4. Authentication and Security

### Logging In

1. **Navigate to Login Page**
   - Enter your email address
   - Enter your password
   - Click "Sign In"

2. **Multi-Factor Authentication (MFA)**
   - If MFA is enabled, you'll be prompted for a verification code
   - Open your authenticator app (Google Authenticator, Authy, etc.)
   - Enter the 6-digit code
   - Click "Verify"

3. **Remember Me Option**
   - Check "Remember Me" to stay logged in for 30 days
   - Only use on trusted devices
   - Session will still expire after 8 hours of activity or 30 minutes of inactivity

### Setting Up Multi-Factor Authentication (MFA)

**Why MFA?** MFA adds an extra layer of security by requiring both your password and a verification code from your phone.

**Setup Steps:**

1. **Navigate to Profile Settings**
   - Click your profile icon in the top-right corner
   - Select "Profile Settings"
   - Click on "Security" tab

2. **Enable MFA**
   - Click "Enable MFA" button
   - Choose authentication method:
     - **TOTP (Recommended)**: Use authenticator app
     - **SMS**: Receive codes via text message

3. **For TOTP (Authenticator App):**
   - Download an authenticator app if you don't have one:
     - Google Authenticator (iOS/Android)
     - Authy (iOS/Android/Desktop)
     - Microsoft Authenticator (iOS/Android)
   - Scan the QR code displayed on screen
   - Enter the 6-digit code from your app
   - Click "Verify and Enable"

4. **Save Backup Codes**
   - System generates 10 backup codes
   - Download and store securely
   - Use these if you lose access to your authenticator app
   - Each code can only be used once

5. **Test MFA**
   - Log out and log back in
   - Verify MFA prompt appears
   - Enter code from authenticator app

### Password Management

#### Changing Your Password

1. Navigate to Profile Settings > Security
2. Click "Change Password"
3. Enter current password
4. Enter new password (must meet requirements)
5. Confirm new password
6. Click "Update Password"

**Password Requirements:**
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)
- Cannot reuse last 5 passwords

#### Forgot Password

1. Click "Forgot Password?" on login page
2. Enter your email address
3. Check your email for reset link
4. Click the link (valid for 1 hour)
5. Enter new password
6. Confirm new password
7. Click "Reset Password"
8. Log in with new password

### Session Management

**Session Duration:**
- Active session: 8 hours
- Inactivity timeout: 30 minutes
- "Remember Me": 30 days (with activity)

**Session Warnings:**
- You'll receive a warning 5 minutes before session expires
- Click "Stay Logged In" to extend session
- Unsaved work will be lost if session expires

**Manual Logout:**
- Click profile icon > "Logout"
- Always log out when using shared computers
- Logout ends session immediately

### Security Best Practices

1. **Password Security**
   - Never share your password
   - Use a unique password (not used elsewhere)
   - Consider using a password manager
   - Change password if compromised

2. **MFA Security**
   - Keep backup codes in a secure location
   - Don't share authenticator app access
   - Update phone number if it changes
   - Report lost devices immediately

3. **Device Security**
   - Only use "Remember Me" on personal devices
   - Log out on shared computers
   - Keep browser updated
   - Use antivirus software

4. **Suspicious Activity**
   - Report unusual login notifications
   - Check audit logs for unexpected activity
   - Contact support if account compromised
   - Change password immediately if suspicious


---

## 5. TPA Administrator Guide

### 5.1 Policy Management

#### Uploading a New Policy

**Step-by-Step Instructions:**

1. **Navigate to Policy Management**
   - Click "Policies" in the left navigation menu
   - Click "Upload Policy" button (top-right)

2. **Upload Policy Document**
   - Drag and drop PDF file into upload area, OR
   - Click "Browse" to select file from computer
   - **File Requirements:**
     - Format: PDF only
     - Maximum size: 50MB
     - Clear, readable text (not scanned images if possible)

3. **Enter Policy Metadata**
   - **Policy Name**: Descriptive name (e.g., "Apollo Munich Gold Plan 2024")
   - **Hospital**: Select associated hospital from dropdown
   - **Effective Date**: When policy becomes active
   - **Expiration Date**: When policy expires
   - **Policy Number**: Insurance policy reference number
   - **Description** (Optional): Additional notes

4. **Submit for Processing**
   - Review entered information
   - Click "Upload and Process"
   - Processing begins immediately

5. **Monitor Processing Status**
   - Progress bar shows processing stages:
     - ✓ File Upload (5-10 seconds)
     - ✓ OCR Extraction (1-3 minutes)
     - ✓ AI Analysis (2-4 minutes)
     - ✓ Structuring Data (30 seconds)
   - Total time: 3-5 minutes for typical policy

6. **Review Extraction Results**
   - System displays extracted policy data
   - **Confidence Score** shown (aim for >85%)
   - Review extracted sections:
     - Coverage Rules
     - Procedure Codes and Coverage %
     - Exclusions and Limitations
     - Room Rent Caps
     - Co-pay Conditions
     - Pre-authorization Requirements

7. **Verify and Edit**
   - Click on any section to expand details
   - Edit incorrect extractions:
     - Click "Edit" icon next to field
     - Make corrections
     - Click "Save"
   - Add missing information if needed

8. **Approve Policy**
   - Review all sections
   - Click "Approve Policy" button
   - Policy becomes active immediately
   - Available for eligibility checks and audits

**Tips for Best Results:**
- Use high-quality PDF files (not scanned images)
- Ensure text is selectable in PDF
- Break very large policies into sections if needed
- Review extraction confidence scores carefully
- Manually verify critical coverage rules

#### Managing Existing Policies

**Viewing Policies:**
- Navigate to Policies page
- View list of all policies with:
  - Policy name
  - Hospital
  - Status (Active, Expired, Draft)
  - Effective dates
  - Last updated
  - Confidence score

**Searching Policies:**
- Use search bar to find policies by:
  - Policy name
  - Hospital name
  - Policy number
- Use filters:
  - Status (Active/Expired/Draft)
  - Hospital
  - Date range

**Editing Policies:**
1. Click on policy name to open details
2. Click "Edit" button
3. Make changes to:
   - Metadata (dates, description)
   - Coverage rules
   - Exclusions
   - Limits
4. Click "Save Changes"
5. System creates new version automatically

**Deactivating Policies:**
1. Open policy details
2. Click "Deactivate" button
3. Confirm deactivation
4. Policy no longer used for new checks
5. Historical data preserved

#### Policy Version Management

**Viewing Version History:**
1. Open policy details
2. Click "Version History" tab
3. View list of all versions with:
   - Version number
   - Date created
   - Created by (user)
   - Change summary
   - Status

**Comparing Versions:**
1. In Version History, select two versions
2. Click "Compare Versions"
3. View side-by-side comparison:
   - **Green**: Added rules
   - **Red**: Removed rules
   - **Yellow**: Modified rules
4. Click on changes for detailed view

**Impact Analysis:**
- System shows impact of version changes:
  - Number of active claims affected
  - Estimated impact on settlement ratios
  - Patients requiring notification
  - Confidence level of analysis

**Rolling Back Versions:**
1. In version comparison, click "Rollback"
2. Enter reason for rollback
3. Confirm rollback
4. System creates new version (doesn't delete history)
5. Affected users notified automatically
6. Audit trail updated


### 5.2 TPA Command Center Dashboard

The Command Center is your central hub for monitoring all claim activity, identifying risks, and managing the settlement process.

#### Dashboard Overview

**Key Metrics (Top Cards):**
- **Total Claims**: Count of all active claims
- **Average CSR**: Current claim settlement ratio
- **High-Risk Claims**: Count requiring attention
- **Processing Time**: Average time to process claims
- **Cost Savings**: Estimated savings from optimization

**Real-Time Charts:**
- **CSR Trend**: Line chart showing settlement ratio over time
- **Claims by Status**: Pie chart of claim statuses
- **Risk Distribution**: Bar chart of High/Medium/Low risk claims
- **Top Rejection Reasons**: Bar chart of common issues

#### Managing Claims

**Claims List View:**
- All active claims displayed in table format
- Columns:
  - Patient Name
  - Claim ID
  - Hospital
  - Claim Amount
  - Risk Level (color-coded)
  - Status
  - Submission Date
  - Actions

**Filtering Claims:**
1. Click "Filters" button above table
2. Select filter criteria:
   - **Hospital**: Choose specific hospital(s)
   - **Status**: Draft, Audited, Submitted, Approved, Rejected
   - **Risk Level**: High, Medium, Low
   - **Date Range**: Custom date picker
   - **Amount Range**: Min and max values
3. Click "Apply Filters"
4. Click "Clear Filters" to reset

**Sorting Claims:**
- Click column headers to sort
- Click again to reverse sort order
- Multi-column sort: Hold Shift and click multiple headers

**Searching Claims:**
- Use search bar to find by:
  - Patient name
  - Claim ID
  - Hospital name
- Search is instant (no need to press Enter)

**Viewing Claim Details:**
1. Click on any claim row
2. Claim details panel opens showing:
   - Patient information
   - Insurance policy details
   - Line items with audit results
   - Risk assessment
   - Audit history
   - Supporting documents
   - Comments and notes

#### Alert Management

**Alert Types:**
- 🔴 **Critical**: High-risk claims, policy expirations
- 🟡 **Warning**: Claims requiring review, missing documentation
- 🔵 **Info**: Processing complete, reports ready

**Viewing Alerts:**
- Alert count badge on bell icon (top-right)
- Click bell icon to open alert panel
- Alerts sorted by priority and time

**Alert Actions:**
1. Click on alert to view details
2. Take appropriate action:
   - **High-Risk Claim**: Review claim details, assign to specialist
   - **Missing Documentation**: Request from billing staff
   - **Policy Expiration**: Upload new policy version
3. Mark alert as "Acknowledged" or "Resolved"
4. Add notes if needed

**Alert Notifications:**
- In-app notifications (real-time)
- Email notifications (configurable)
- Webhook notifications (for integrations)

#### Analytics and Insights

**Performance Metrics:**
- **CSR Improvement**: Compare current vs. baseline
- **Processing Time Reduction**: Time saved per claim
- **Rejection Rate**: Percentage of rejected claims
- **Cost Savings**: Estimated financial impact

**Trend Analysis:**
- View trends over time periods:
  - Last 7 days
  - Last 30 days
  - Last 90 days
  - Custom date range
- Compare across hospitals
- Identify patterns and anomalies

**Drill-Down Capabilities:**
- Click on any chart element for details
- Navigate from summary to individual claims
- Export detailed data for further analysis


### 5.3 Webhook Configuration

Webhooks allow external systems to receive real-time notifications about events in the claim optimizer.

#### Setting Up Webhooks

1. **Navigate to Settings**
   - Click profile icon > "Settings"
   - Select "Integrations" tab
   - Click "Webhooks" section

2. **Add New Webhook**
   - Click "Add Webhook" button
   - Fill in webhook details:
     - **Name**: Descriptive name (e.g., "EMR Integration")
     - **URL**: Endpoint URL (must be HTTPS)
     - **Description**: Purpose of webhook
     - **Authentication Method**:
       - API Key (in header)
       - OAuth 2.0
       - None (not recommended)

3. **Select Events**
   - Choose which events trigger this webhook:
     - ☐ Claim Submitted
     - ☐ Audit Completed
     - ☐ High-Risk Claim Detected
     - ☐ Policy Updated
     - ☐ Settlement Completed
     - ☐ Claim Rejected
     - ☐ Pre-authorization Required

4. **Configure Authentication**
   - **For API Key:**
     - Enter header name (e.g., "X-API-Key")
     - Enter API key value
     - Key is encrypted and stored securely
   - **For OAuth 2.0:**
     - Enter client ID
     - Enter client secret
     - Enter token URL
     - Test authentication

5. **Test Webhook**
   - Click "Test Webhook" button
   - System sends sample payload
   - View response:
     - Status code
     - Response body
     - Response time
   - Verify webhook receives and processes correctly

6. **Save and Activate**
   - Click "Save Webhook"
   - Toggle "Enabled" switch to activate
   - Webhook starts receiving events immediately

#### Managing Webhooks

**Viewing Webhook Activity:**
1. Click on webhook name in list
2. View "Activity" tab showing:
   - Recent deliveries
   - Success/failure status
   - Response times
   - Payload details
   - Error messages

**Retry Failed Deliveries:**
1. In Activity tab, find failed delivery
2. Click "Retry" button
3. System attempts redelivery
4. View updated status

**Editing Webhooks:**
1. Click "Edit" button on webhook
2. Modify settings as needed
3. Click "Save Changes"
4. Changes take effect immediately

**Disabling Webhooks:**
1. Toggle "Enabled" switch to off
2. Webhook stops receiving events
3. Configuration preserved for re-enabling

**Deleting Webhooks:**
1. Click "Delete" button
2. Confirm deletion
3. Webhook permanently removed
4. Activity history archived

#### Webhook Payload Format

**Example Payload (Audit Completed):**
```json
{
  "event": "audit.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "claim_id": "CLM-2024-001234",
  "patient_id": "PAT-789456",
  "hospital_id": "HOSP-123",
  "audit_results": {
    "settlement_ratio": 0.87,
    "risk_level": "Medium",
    "approved_items": 45,
    "rejected_items": 5,
    "review_items": 3
  },
  "webhook_id": "WHK-001"
}
```

**Webhook Security:**
- All webhooks use HTTPS only
- Payloads signed with HMAC-SHA256
- Signature in `X-Webhook-Signature` header
- Verify signature to ensure authenticity


---

## 6. Doctor Guide

### 6.1 Real-Time Eligibility Checking

Quickly verify if a patient's insurance covers specific procedures before treatment.

#### Single Patient Eligibility Check

**Step-by-Step Instructions:**

1. **Navigate to Eligibility Checker**
   - Click "Eligibility Check" in left navigation
   - Mobile-optimized interface loads

2. **Enter Patient Information**
   - **Patient ID**: Enter or search by name
   - System auto-fills if patient exists:
     - Name
     - Date of birth
     - Insurance policy
   - **New Patient**: Click "Add New Patient" if not found

3. **Select Insurance Policy**
   - Choose from dropdown of active policies
   - Policy details displayed:
     - Policy name
     - Effective dates
     - Coverage type

4. **Enter Procedure Details**
   - **Procedure Code**: Enter CPT code (e.g., 99213)
     - Or search by procedure name
     - System suggests matching codes
   - **Diagnosis Codes**: Add ICD-10 codes
     - Multiple diagnoses supported
     - Search by code or description
   - **Procedure Date**: Select date (default: today)
   - **Additional Procedures**: Click "Add Procedure" for bundling check

5. **Submit Check**
   - Click "Check Eligibility" button
   - System processes in < 2 seconds
   - Real-time policy validation

6. **View Results**
   - **Coverage Status** (color-coded):
     - 🟢 **Fully Covered**: Procedure approved
     - 🟡 **Partially Covered**: Co-pay required
     - 🔴 **Not Covered**: Procedure excluded
   
   - **Coverage Details**:
     - Coverage percentage (e.g., 80%)
     - Patient responsibility amount
     - Co-pay amount
     - Deductible status
     - Annual limit remaining
   
   - **Policy References**:
     - Specific policy clauses
     - Coverage rules applied
     - Exclusion reasons (if applicable)
   
   - **Pre-authorization**:
     - Required: Yes/No
     - Documentation needed
     - Submission process

7. **Pre-authorization Template** (if required)
   - Click "Generate Template" button
   - System creates pre-filled form with:
     - Patient information
     - Procedure details
     - Medical necessity justification
     - Required documentation checklist
   - Download as PDF or email to billing

8. **Save or Print Results**
   - Click "Save to Patient Record"
   - Click "Print" for patient copy
   - Click "Email to Billing" to notify billing staff

#### Understanding Coverage Results

**Fully Covered (Green):**
- Procedure is covered at specified percentage
- No pre-authorization required
- Proceed with treatment
- Patient responsibility clearly shown

**Partially Covered (Yellow):**
- Procedure covered with conditions
- Co-pay or deductible applies
- May require pre-authorization
- Review patient responsibility with patient

**Not Covered (Red):**
- Procedure excluded from policy
- Policy clause reference provided
- Alternative procedures suggested (if available)
- Patient must pay out-of-pocket or appeal

**Uncertain Coverage:**
- Insufficient information to determine
- Manual verification recommended
- Contact insurance company
- Document uncertainty in patient record

#### Tips for Doctors

- **Save Frequently Used Codes**: Star favorite procedures for quick access
- **Check Before Treatment**: Always verify coverage before expensive procedures
- **Review Pre-auth Requirements**: Some procedures require advance approval
- **Document Everything**: Save all eligibility checks to patient records
- **Communicate with Patients**: Explain coverage and costs clearly
- **Use Batch Mode**: Check multiple patients at once (see next section)


### 6.2 Batch Eligibility Checking

Check eligibility for multiple patients at once - perfect for daily patient schedules.

#### Preparing Your CSV File

**Download Template:**
1. Click "Batch Mode" toggle
2. Click "Download CSV Template"
3. Open template in Excel or Google Sheets

**Required Columns:**
- `patient_id` - Unique patient identifier
- `patient_name` - Full name
- `date_of_birth` - Format: YYYY-MM-DD
- `policy_id` - Insurance policy ID
- `procedure_code` - CPT code
- `diagnosis_code` - ICD-10 code
- `procedure_date` - Format: YYYY-MM-DD

**Optional Columns:**
- `additional_procedures` - Comma-separated CPT codes
- `notes` - Any special notes

**Example CSV:**
```csv
patient_id,patient_name,date_of_birth,policy_id,procedure_code,diagnosis_code,procedure_date
PAT001,John Smith,1980-05-15,POL123,99213,Z00.00,2024-01-20
PAT002,Jane Doe,1975-08-22,POL123,99214,M79.3,2024-01-20
PAT003,Bob Johnson,1990-03-10,POL456,99215,I10,2024-01-20
```

#### Uploading and Processing Batch

1. **Upload CSV File**
   - Click "Upload CSV" button
   - Drag and drop file or browse
   - **File Requirements:**
     - Format: CSV only
     - Maximum size: 10MB
     - Maximum rows: 100 patients
   - File preview shows:
     - File name
     - File size
     - Row count

2. **Map Columns**
   - System auto-detects column names
   - Verify mappings are correct:
     - Required fields highlighted
     - Dropdown to manually map if needed
   - Click "Validate Mapping"
   - Fix any errors shown

3. **Review and Submit**
   - Preview first 5 rows
   - Check for data errors
   - Click "Process Batch"
   - Processing begins immediately

4. **Monitor Progress**
   - Real-time progress bar
   - Shows:
     - Patients processed
     - Estimated time remaining
     - Current status
   - Processing time: ~30 seconds for 100 patients

5. **View Results Summary**
   - **Summary Statistics:**
     - Total patients processed
     - Fully covered count
     - Partially covered count
     - Not covered count
     - Errors count
   
   - **Quick Filters:**
     - Show only not covered
     - Show only requiring pre-auth
     - Show only errors

6. **Review Individual Results**
   - Results table shows all patients
   - Columns:
     - Patient name
     - Procedure
     - Coverage status (color-coded)
     - Coverage %
     - Patient responsibility
     - Pre-auth required
     - Actions
   - Click row to view full details

7. **Export Results**
   - Click "Export Results" button
   - Choose format:
     - **CSV**: For spreadsheet analysis
     - **PDF**: For printing/sharing
   - Download includes:
     - All patient results
     - Coverage details
     - Pre-auth requirements
     - Summary statistics

#### Handling Batch Errors

**Common Errors:**
- **Invalid Patient ID**: Patient not found in system
- **Invalid Policy**: Policy doesn't exist or expired
- **Invalid Procedure Code**: CPT code not recognized
- **Missing Required Field**: Required data not provided

**Error Resolution:**
1. View error details in results table
2. Fix errors in original CSV
3. Re-upload corrected file
4. Or manually check individual patients

#### Best Practices for Batch Processing

- **Prepare CSV Night Before**: Have file ready for morning
- **Validate Data**: Check for typos and missing information
- **Use Consistent Formatting**: Follow template exactly
- **Save Mapping Configuration**: Reuse for future uploads
- **Process Early**: Run batch before patient appointments
- **Review High-Risk Cases**: Manually verify uncertain results
- **Share with Billing**: Email results to billing staff
- **Keep Records**: Save batch results for documentation


---

## 7. Billing Staff Guide

### 7.1 Creating and Submitting Claims

#### Creating a New Claim

1. **Navigate to Bill Audit**
   - Click "Bill Audit" in left navigation
   - Click "New Claim" button

2. **Enter Patient Information**
   - **Patient ID**: Search or enter manually
   - System auto-fills:
     - Patient name
     - Date of birth
     - Insurance information
   - **Admission Date**: Date patient admitted
   - **Discharge Date**: Date patient discharged
   - **Claim Type**: Inpatient, Outpatient, Emergency

3. **Select Insurance Policy**
   - Choose applicable policy from dropdown
   - Verify policy is active
   - Check coverage dates

4. **Add Line Items**
   - Click "Add Line Item" button
   - For each item, enter:
     - **Procedure Code** (CPT): Required
     - **Description**: Auto-filled from code
     - **Quantity**: Number of times performed
     - **Unit Price**: Cost per unit
     - **Total Amount**: Auto-calculated
     - **Date of Service**: When performed
     - **Provider**: Doctor/department
   
   - **Bulk Import Option:**
     - Click "Import from CSV"
     - Upload CSV with line items
     - System validates and imports

5. **Add Supporting Documents**
   - Click "Attach Documents"
   - Upload:
     - Medical records
     - Lab reports
     - Prescriptions
     - Discharge summary
   - Supported formats: PDF, JPG, PNG
   - Maximum 10MB per file

6. **Review Claim Summary**
   - Total claim amount displayed
   - Line item count
   - Document count
   - Patient responsibility estimate

7. **Save as Draft**
   - Click "Save Draft" to save progress
   - Return later to complete
   - Drafts auto-saved every 2 minutes

### 7.2 Running Bill Audit

The audit engine analyzes your claim against policy rules before submission to identify potential issues.

#### Submitting for Audit

1. **Review Claim Completeness**
   - Ensure all required fields filled
   - Verify line items are accurate
   - Check supporting documents attached

2. **Submit for Audit**
   - Click "Submit for Audit" button
   - Confirm submission
   - Processing begins immediately

3. **Monitor Audit Progress**
   - Progress indicator shows stages:
     - ✓ Validating line items
     - ✓ Checking policy rules
     - ✓ AI analysis
     - ✓ Risk assessment
     - ✓ Generating recommendations
   - Typical time: 20-30 seconds for 100 items

#### Understanding Audit Results

**Result Categories:**

1. **Approved Items (Green)**
   - Fully covered by policy
   - No issues detected
   - Ready for submission
   - Shows coverage percentage

2. **Rejected Items (Red)**
   - Not covered by policy
   - Policy violation detected
   - Requires action before submission
   - Shows specific rejection reason

3. **Review Required (Yellow)**
   - Uncertain coverage
   - Missing information
   - Requires manual verification
   - May need additional documentation

**Audit Summary Dashboard:**
- **Predicted Settlement Ratio**: Estimated approval rate (e.g., 87%)
- **Risk Level**: High, Medium, or Low
- **Total Claim Amount**: Sum of all line items
- **Approved Amount**: Expected payout
- **Patient Responsibility**: Out-of-pocket cost
- **Items by Category**: Count of approved/rejected/review

**Detailed Line Item Results:**
- Table showing all line items with:
  - Procedure code and description
  - Amount
  - Status (Approved/Rejected/Review)
  - Coverage percentage
  - Rejection reason (if applicable)
  - Policy clause reference
  - Recommendation

**Rejection Reasons:**
- "Procedure not covered under policy"
- "Exceeds room rent limit"
- "Pre-authorization not obtained"
- "Procedure bundling violation"
- "Diagnosis code mismatch"
- "Service date outside coverage period"


### 7.3 Optimization and Corrections

The AI provides actionable suggestions to improve your claim's approval chances.

#### Viewing Optimization Suggestions

1. **Access Suggestions Panel**
   - After audit completes, click "View Suggestions"
   - Suggestions prioritized by impact

2. **Suggestion Types:**

   **Alternative Procedure Codes:**
   - "Consider using code 99214 instead of 99215"
   - Shows coverage difference
   - Explains why alternative is better
   - One-click to apply change

   **Documentation Requirements:**
   - "Add medical necessity justification"
   - "Attach lab reports for diagnosis"
   - "Include doctor's notes"
   - Checklist of required documents

   **Bundling Opportunities:**
   - "Procedures X and Y can be bundled"
   - Shows cost savings
   - Explains bundling rules
   - Auto-applies bundling

   **Timing Adjustments:**
   - "Procedure date outside coverage period"
   - "Adjust to fall within policy dates"
   - Shows valid date ranges

   **Pre-authorization:**
   - "Pre-authorization required for this procedure"
   - Links to pre-auth template
   - Shows submission process

3. **Applying Suggestions**
   - Review each suggestion carefully
   - Click "Apply" to accept suggestion
   - System updates claim automatically
   - Or click "Dismiss" if not applicable

4. **Re-audit After Changes**
   - Click "Re-audit" button
   - System re-analyzes with changes
   - Compare before/after settlement ratios
   - Repeat until optimal

#### Making Manual Corrections

1. **Edit Line Items**
   - Click "Edit" icon on line item
   - Modify:
     - Procedure code
     - Quantity
     - Unit price
     - Date of service
   - Click "Save"

2. **Remove Line Items**
   - Click "Delete" icon
   - Confirm removal
   - Item removed from claim

3. **Add Missing Items**
   - Click "Add Line Item"
   - Enter details
   - Submit for re-audit

4. **Update Documentation**
   - Add missing documents
   - Remove incorrect documents
   - Rename documents for clarity

### 7.4 Patient Profile and Multi-Claim Risk

View comprehensive patient information and risk across all claims.

#### Accessing Patient Profile

1. **From Claims List:**
   - Click patient name in any claim
   - Patient profile opens

2. **From Search:**
   - Use global search bar
   - Enter patient name or ID
   - Select patient from results

#### Patient Profile Overview

**Patient Information Card:**
- Full name
- Patient ID
- Date of birth
- Contact information
- Insurance policy details
- Primary doctor

**Claims List:**
- All claims for this patient
- Sortable by:
  - Date
  - Amount
  - Status
  - Risk level
- Click claim to view details

**Aggregated Risk Score:**
- Overall risk level (High/Medium/Low)
- Color-coded indicator
- Risk trend chart over time
- Comparison to hospital average

**Risk Factors Breakdown:**
- Chart showing risk contributors:
  - High claim amounts
  - Complex procedures
  - Historical rejections
  - Policy complexity
  - Documentation issues

**Risk Trend Timeline:**
- Line chart showing risk over time
- Markers for significant events
- Hover for details

**Multi-Claim Analytics:**
- **Total Claim Amount**: Sum across all claims
- **Average Settlement Ratio**: Historical performance
- **Common Rejection Reasons**: Top issues
- **Policy Utilization**: Coverage usage patterns
- **Historical Performance**: Trends and patterns

#### Risk Mitigation Recommendations

**Viewing Recommendations:**
- Prioritized list of actions
- Each shows:
  - Recommendation description
  - Expected risk reduction
  - Effort level (Low/Medium/High)
  - Specific action steps

**Example Recommendations:**
- "Obtain pre-authorization for pending procedures"
- "Add supporting documentation for high-value claims"
- "Review and correct diagnosis code mismatches"
- "Bundle related procedures to reduce complexity"

**Taking Action:**
1. Click on recommendation
2. View detailed action steps
3. Complete actions
4. Mark as "Completed"
5. System tracks effectiveness

**Tracking Progress:**
- Completed recommendations marked
- Risk score updates in real-time
- Historical effectiveness shown
- Learn from successful strategies


### 7.5 Finalizing and Submitting Claims

#### Final Review Checklist

Before submission, verify:
- [ ] All line items accurate
- [ ] Supporting documents attached
- [ ] Audit results reviewed
- [ ] Optimization suggestions applied
- [ ] Risk level acceptable
- [ ] Patient information correct
- [ ] Policy details verified
- [ ] Pre-authorizations obtained (if required)

#### Submitting to Insurance

1. **Generate Submission Package**
   - Click "Finalize Claim" button
   - System generates:
     - Claim form (standard format)
     - Line item details
     - Supporting documents
     - Pre-authorization documents
     - Audit summary

2. **Choose Submission Method:**
   
   **Option A: API Submission (Recommended)**
   - Click "Submit via API"
   - System sends directly to insurance
   - Confirmation received immediately
   - Tracking number provided
   
   **Option B: Manual Download**
   - Click "Download Package"
   - Choose format (PDF, Excel)
   - Submit through insurance portal
   - Enter tracking number manually

3. **Track Submission Status**
   - Status updates automatically (if API)
   - Manual status updates (if downloaded)
   - Statuses:
     - Submitted
     - Under Review
     - Approved
     - Partially Approved
     - Rejected
     - Appealed

4. **Receive Notifications**
   - Email when status changes
   - In-app notifications
   - Webhook notifications (if configured)

#### Handling Rejections

**If Claim Rejected:**

1. **Review Rejection Details**
   - Click on rejected claim
   - View rejection reasons
   - Check insurance company notes

2. **Compare with Audit Predictions**
   - See if rejection was predicted
   - Review audit recommendations
   - Identify what was missed

3. **Prepare Appeal**
   - Click "Prepare Appeal" button
   - System generates appeal template
   - Includes:
     - Original claim details
     - Rejection reasons
     - Counter-arguments
     - Supporting evidence
     - Policy references

4. **Submit Appeal**
   - Add additional documentation
   - Review appeal letter
   - Submit through system or manually
   - Track appeal status

5. **Learn from Rejections**
   - System tracks rejection patterns
   - Improves future predictions
   - Suggests process improvements

---

## 8. Hospital Administrator Guide

### 8.1 User Management

#### Adding New Users

1. **Navigate to User Management**
   - Click "Settings" > "Users"
   - Click "Add User" button

2. **Enter User Details**
   - **Email**: User's work email
   - **First Name**: User's first name
   - **Last Name**: User's last name
   - **Role**: Select from dropdown
     - TPA Administrator
     - Hospital Administrator
     - Billing Staff
     - Doctor
   - **Hospital**: Assign to hospital(s)
   - **Department**: Optional

3. **Set Permissions**
   - Role-based permissions auto-applied
   - Custom permissions (if needed):
     - View only
     - Edit
     - Delete
     - Admin

4. **Send Invitation**
   - Click "Send Invitation"
   - User receives email with:
     - Activation link
     - Temporary password
     - Setup instructions
   - Link expires in 7 days

#### Managing Existing Users

**Viewing Users:**
- List of all users with:
  - Name
  - Email
  - Role
  - Hospital
  - Status (Active/Inactive)
  - Last login

**Editing Users:**
1. Click on user name
2. Modify details
3. Click "Save Changes"

**Deactivating Users:**
1. Click "Deactivate" button
2. Confirm deactivation
3. User loses access immediately
4. Data preserved for audit

**Resetting Passwords:**
1. Click "Reset Password"
2. User receives reset email
3. Must set new password

**Viewing User Activity:**
- Click "Activity Log"
- View user's actions:
  - Login history
  - Claims accessed
  - Changes made
  - Documents viewed


### 8.2 Audit Log Review

Comprehensive audit trails for compliance and security monitoring.

#### Accessing Audit Logs

1. **Navigate to Audit Logs**
   - Click "Audit Logs" in left navigation
   - Or Settings > "Audit & Compliance"

2. **Audit Log Interface**
   - Table view of all audit entries
   - Columns:
     - Timestamp
     - User
     - Action
     - Entity Type
     - Entity ID
     - IP Address
     - Status

#### Filtering and Searching

**Filter Options:**
- **Date Range**: Custom date picker
- **User**: Select specific user(s)
- **Action Type**:
  - Create
  - Read
  - Update
  - Delete
  - Login
  - Logout
  - Export
- **Entity Type**:
  - Policy
  - Claim
  - Patient
  - User
  - Document
- **Status**: Success, Failed, Warning
- **Hospital**: Filter by hospital

**Search Functionality:**
- Search by:
  - User email
  - Entity ID
  - IP address
  - Action description
- Real-time search results

**Advanced Filters:**
- Combine multiple filters
- Save filter configurations
- Export filtered results

#### Viewing Audit Details

1. **Click on Audit Entry**
   - Detailed view opens

2. **Information Displayed:**
   - **Timestamp**: Exact date and time
   - **User Information**:
     - Name
     - Email
     - Role
     - Hospital
   - **Action Details**:
     - Action type
     - Description
     - Result (success/failure)
   - **Entity Information**:
     - Entity type
     - Entity ID
     - Entity name
   - **Change Details** (for updates):
     - Before state
     - After state
     - Fields changed
   - **Technical Details**:
     - IP address
     - User agent (browser)
     - Session ID
     - Request ID

3. **Change Comparison**
   - For update actions, view side-by-side:
     - Original values
     - New values
     - Highlighted differences

#### Compliance Reporting

**Generate Compliance Reports:**

1. **Select Report Type:**
   - HIPAA Access Report
   - Data Modification Report
   - User Activity Report
   - Security Incident Report
   - Export Activity Report

2. **Configure Parameters:**
   - Date range
   - Users to include
   - Entity types
   - Actions to include

3. **Generate Report:**
   - Click "Generate Report"
   - Processing time: 10-30 seconds
   - View in browser or download

4. **Report Contents:**
   - Executive summary
   - Detailed audit entries
   - Statistics and charts
   - Compliance checklist
   - Recommendations

**Exporting Audit Logs:**
- Select date range
- Choose format:
  - CSV (for analysis)
  - JSON (for systems)
  - PDF (for documentation)
- Download or email

**Retention Policy:**
- Audit logs retained for 7 years
- Automatic archival of old logs
- Archived logs accessible on request
- Immutable storage (cannot be modified)

#### Security Monitoring

**Suspicious Activity Alerts:**
- Multiple failed login attempts
- Access from unusual locations
- Bulk data exports
- After-hours access
- Permission escalation attempts

**Alert Actions:**
1. Review alert details
2. Investigate user activity
3. Contact user if needed
4. Disable account if compromised
5. Document incident
6. Report to security team


---

## 9. Settings and Configuration

### 9.1 Profile Settings

#### Personal Information

1. **Navigate to Profile**
   - Click profile icon (top-right)
   - Select "Profile Settings"

2. **Update Information:**
   - First name
   - Last name
   - Email (requires verification)
   - Phone number
   - Department
   - Job title

3. **Profile Photo:**
   - Click "Upload Photo"
   - Select image (JPG, PNG)
   - Maximum 5MB
   - Crop and adjust
   - Click "Save"

#### Security Settings

**Password Management:**
- Change password
- View password requirements
- See last password change date

**Multi-Factor Authentication:**
- Enable/disable MFA
- Change MFA method
- Regenerate backup codes
- View trusted devices

**Active Sessions:**
- View all active sessions
- See device and location
- Revoke sessions remotely
- Set session timeout preferences

### 9.2 Notification Preferences

#### Email Notifications

**Configure Email Settings:**

1. **Navigate to Notifications**
   - Settings > "Notifications"
   - Select "Email" tab

2. **Notification Categories:**
   
   **Alerts (Critical):**
   - ☐ High-risk claims detected
   - ☐ Policy expiration warnings
   - ☐ System security alerts
   - ☐ Account security notifications
   
   **Claims (Important):**
   - ☐ Claim submitted
   - ☐ Audit completed
   - ☐ Claim approved
   - ☐ Claim rejected
   - ☐ Appeal status updates
   
   **Reports (Informational):**
   - ☐ Scheduled reports ready
   - ☐ Monthly performance summary
   - ☐ Weekly digest
   
   **Policy Updates:**
   - ☐ New policy uploaded
   - ☐ Policy version changed
   - ☐ Policy expiring soon
   
   **System Updates:**
   - ☐ New features available
   - ☐ Scheduled maintenance
   - ☐ System announcements

3. **Notification Frequency:**
   - **Immediate**: Real-time emails
   - **Daily Digest**: Once per day summary
   - **Weekly Digest**: Once per week summary
   - **Off**: No emails for this category

4. **Email Address:**
   - Primary email (account email)
   - Add secondary email
   - Verify email addresses

5. **Quiet Hours:**
   - Set hours to suppress notifications
   - Example: 10 PM - 7 AM
   - Emergency alerts still sent

#### In-App Notifications

**Configure In-App Settings:**
- Enable/disable notification bell
- Sound notifications
- Desktop notifications (browser)
- Notification retention (days)

**Notification Actions:**
- Mark as read
- Mark all as read
- Delete notification
- Snooze notification
- Go to related item

### 9.3 Integration Settings

#### API Access

**Generating API Keys:**

1. **Navigate to Integrations**
   - Settings > "Integrations"
   - Select "API Access" tab

2. **Create API Key:**
   - Click "Generate New Key"
   - Enter key name
   - Select permissions:
     - Read only
     - Read and write
     - Admin
   - Set expiration (optional)
   - Click "Generate"

3. **Copy API Key:**
   - Key shown once only
   - Copy and store securely
   - Cannot be retrieved later

4. **Using API Key:**
   - Include in request header:
     ```
     Authorization: Bearer YOUR_API_KEY
     ```
   - See API documentation for endpoints

**Managing API Keys:**
- View all active keys
- See last used date
- Revoke keys
- Regenerate keys
- Set usage limits

#### Webhook Configuration

(See Section 5.3 for detailed webhook setup)

**Quick Setup:**
1. Add webhook URL
2. Select events
3. Configure authentication
4. Test webhook
5. Activate

#### External System Integrations

**Available Integrations:**
- EMR Systems (Epic, Cerner, etc.)
- Billing Systems
- Insurance Portals
- Document Management Systems
- Analytics Platforms

**Setup Process:**
1. Select integration
2. Enter credentials
3. Map data fields
4. Test connection
5. Activate integration


---

## 10. Reports and Analytics

### 10.1 Standard Reports

#### CSR Trend Analysis Report

**Purpose:** Track claim settlement ratio improvements over time.

**Generating the Report:**

1. **Navigate to Reports**
   - Click "Reports" in left navigation
   - Select "CSR Trend Analysis"

2. **Configure Parameters:**
   - **Date Range**: 
     - Last 30 days
     - Last 90 days
     - Last 12 months
     - Custom range
   - **Hospitals**: Select specific or all
   - **Policies**: Filter by policy
   - **Comparison**: Compare to:
     - Previous period
     - Industry benchmark
     - Target goal

3. **Generate Report:**
   - Click "Generate Report"
   - Processing: 5-10 seconds
   - View in browser

4. **Report Contents:**
   - **Executive Summary:**
     - Current CSR
     - Change from previous period
     - Trend direction
     - Key insights
   
   - **Trend Chart:**
     - Line graph showing CSR over time
     - Comparison lines (if selected)
     - Milestone markers
     - Interactive hover details
   
   - **Performance Breakdown:**
     - By hospital
     - By policy
     - By claim type
     - By time period
   
   - **Top Performers:**
     - Best performing hospitals
     - Most improved hospitals
     - Success factors
   
   - **Areas for Improvement:**
     - Underperforming areas
     - Common issues
     - Recommendations

5. **Export Report:**
   - **PDF**: Formatted report with charts
   - **Excel**: Raw data with pivot tables
   - **PowerPoint**: Presentation slides
   - **CSV**: Data export for analysis

#### Rejection Reason Analysis Report

**Purpose:** Identify most common reasons for claim rejections.

**Report Contents:**
- Top 10 rejection reasons
- Frequency and percentage
- Financial impact per reason
- Trend over time
- Affected hospitals
- Recommended actions

**Key Insights:**
- Which policy clauses cause most rejections
- Preventable vs. non-preventable rejections
- Training opportunities
- Process improvements

#### Policy Clause Frequency Report

**Purpose:** Understand which policy rules are most commonly applied.

**Report Contents:**
- Most frequently cited clauses
- Coverage rules usage
- Exclusion frequency
- Pre-authorization requirements
- Room rent limit applications

**Use Cases:**
- Policy optimization
- Staff training focus
- Documentation improvements
- Negotiation with insurers

#### Hospital Performance Comparison

**Purpose:** Compare performance across multiple hospitals.

**Report Contents:**
- Side-by-side metrics
- CSR comparison
- Processing time comparison
- Cost savings comparison
- Best practices identification

**Benchmarking:**
- Internal benchmarks
- Industry standards
- Regional comparisons
- Peer group analysis

#### Processing Time Analysis

**Purpose:** Track efficiency improvements in claim processing.

**Report Contents:**
- Average processing time
- Time by claim type
- Bottleneck identification
- Improvement trends
- Staff productivity

**Metrics:**
- Time to audit
- Time to submission
- Time to approval
- Total cycle time

#### Cost Savings Report

**Purpose:** Quantify financial impact of using the system.

**Report Contents:**
- Total cost savings
- Savings by category:
  - Reduced rejections
  - Faster processing
  - Fewer appeals
  - Improved settlement ratios
- ROI calculation
- Projected annual savings

### 10.2 Custom Reports

#### Building Custom Reports

1. **Navigate to Custom Reports**
   - Reports > "Custom Report Builder"

2. **Select Data Sources:**
   - Claims
   - Policies
   - Patients
   - Audit results
   - User activity

3. **Choose Metrics:**
   - Drag and drop metrics
   - Available metrics:
     - Count
     - Sum
     - Average
     - Minimum
     - Maximum
     - Percentage
     - Trend

4. **Add Dimensions:**
   - Group by:
     - Hospital
     - Policy
     - Time period
     - Claim type
     - Risk level
     - Status

5. **Apply Filters:**
   - Date range
   - Hospital
   - Amount range
   - Status
   - Risk level
   - Custom conditions

6. **Choose Visualizations:**
   - Bar chart
   - Line chart
   - Pie chart
   - Table
   - Heatmap
   - Scatter plot

7. **Save and Schedule:**
   - Save report template
   - Schedule automatic generation
   - Set email distribution
   - Choose frequency


### 10.3 Interactive Analytics

#### Dashboard Analytics

**Real-Time Metrics:**
- Live updates every 30 seconds
- Current day statistics
- Trend indicators (↑↓)
- Comparison to yesterday/last week

**Interactive Charts:**
- Click to drill down
- Hover for details
- Zoom and pan
- Export chart as image

**Filtering:**
- Apply filters to all charts
- Save filter presets
- Share filtered views
- Reset to defaults

#### Drill-Down Analysis

**From Summary to Detail:**

1. **Start with Summary Metric**
   - Example: "Average CSR: 87%"
   - Click on metric

2. **View Breakdown**
   - By hospital
   - By policy
   - By time period

3. **Drill into Specific Item**
   - Click on hospital
   - View hospital-specific CSR

4. **View Individual Claims**
   - See all claims for hospital
   - Filter and sort
   - Open claim details

5. **Analyze Root Causes**
   - Review rejection reasons
   - Check audit results
   - Identify patterns

**Navigation:**
- Breadcrumb trail shows path
- Back button returns to previous level
- Home button returns to summary

### 10.4 Scheduled Reports

#### Setting Up Scheduled Reports

1. **Select Report Type**
   - Choose from standard or custom reports

2. **Configure Schedule:**
   - **Frequency:**
     - Daily (weekdays only option)
     - Weekly (choose day)
     - Monthly (choose date)
     - Quarterly
   - **Time**: Select time of day
   - **Timezone**: Set timezone

3. **Set Recipients:**
   - Add email addresses
   - Select user groups
   - Include external stakeholders
   - Set CC and BCC

4. **Choose Format:**
   - PDF (default)
   - Excel
   - Both

5. **Add Message:**
   - Custom email subject
   - Email body text
   - Include summary in email

6. **Activate Schedule:**
   - Review settings
   - Click "Activate"
   - Receive confirmation

#### Managing Scheduled Reports

**View Scheduled Reports:**
- List of all scheduled reports
- Next run date/time
- Recipients
- Status (Active/Paused)

**Edit Schedule:**
- Modify frequency
- Update recipients
- Change format
- Adjust parameters

**Pause/Resume:**
- Temporarily pause reports
- Resume when needed
- Maintains configuration

**View History:**
- See past report runs
- Download previous reports
- Check delivery status
- View error logs

---

## 11. Troubleshooting

### 11.1 Common Issues and Solutions

#### Login Issues

**Problem: Cannot log in**

**Solutions:**
1. Verify email and password are correct
2. Check Caps Lock is off
3. Try "Forgot Password" to reset
4. Clear browser cache and cookies
5. Try different browser
6. Check internet connection
7. Contact administrator if account locked

**Problem: MFA code not working**

**Solutions:**
1. Verify time on phone is correct (auto-sync)
2. Generate new code (codes expire after 30 seconds)
3. Try backup code if available
4. Use SMS option if configured
5. Contact administrator to reset MFA

#### Policy Upload Issues

**Problem: Policy upload fails**

**Solutions:**
1. Check file size (max 50MB)
2. Verify file is PDF format
3. Ensure PDF is not password-protected
4. Try uploading from different browser
5. Check internet connection stability
6. Contact support if issue persists

**Problem: Low extraction confidence**

**Solutions:**
1. Verify PDF quality (not scanned image)
2. Check if text is selectable in PDF
3. Try re-scanning document at higher quality
4. Manually review and correct extractions
5. Contact support for assistance

#### Eligibility Check Issues

**Problem: Eligibility check times out**

**Solutions:**
1. Check internet connection
2. Verify policy is active
3. Try again (may be temporary)
4. Use simpler query (fewer procedures)
5. Contact support if persistent

**Problem: Unexpected coverage results**

**Solutions:**
1. Verify correct policy selected
2. Check procedure code is correct
3. Review policy effective dates
4. Check for policy updates
5. Manually verify with insurance if uncertain

#### Bill Audit Issues

**Problem: Audit takes too long**

**Solutions:**
1. Check number of line items (max 100)
2. Verify internet connection
3. Try submitting in smaller batches
4. Check system status page
5. Contact support if exceeds 60 seconds

**Problem: Unexpected rejection predictions**

**Solutions:**
1. Review policy rules carefully
2. Check procedure codes are correct
3. Verify diagnosis codes match
4. Review supporting documentation
5. Compare with similar approved claims
6. Contact support for clarification


### 11.2 Performance Issues

#### Slow Page Loading

**Solutions:**
1. Check internet speed (minimum 5 Mbps)
2. Close unnecessary browser tabs
3. Clear browser cache:
   - Chrome: Settings > Privacy > Clear browsing data
   - Firefox: Options > Privacy > Clear Data
   - Safari: Preferences > Privacy > Manage Website Data
4. Disable browser extensions temporarily
5. Try different browser
6. Check system status page for outages

#### Dashboard Not Updating

**Solutions:**
1. Refresh page (F5 or Cmd+R)
2. Check internet connection
3. Verify you're logged in
4. Clear cache and reload
5. Check browser console for errors
6. Contact support if issue persists

### 11.3 Data Issues

#### Missing Claims or Patients

**Solutions:**
1. Check filters are not hiding data
2. Verify date range is correct
3. Check hospital filter
4. Use search function
5. Verify you have permission to view
6. Contact administrator

#### Incorrect Data Displayed

**Solutions:**
1. Refresh page to get latest data
2. Check if viewing correct hospital
3. Verify policy version is current
4. Clear cache and reload
5. Report issue to support with:
   - Screenshot
   - Claim/Policy ID
   - Expected vs. actual data

### 11.4 Export and Download Issues

#### Export Fails

**Solutions:**
1. Check file size (large exports may timeout)
2. Try smaller date range
3. Try different format (CSV vs. PDF)
4. Check browser download settings
5. Disable popup blocker
6. Try different browser

#### Downloaded File Won't Open

**Solutions:**
1. Verify file downloaded completely
2. Check file extension is correct
3. Try opening with different program
4. Re-download file
5. Contact support if file corrupted

### 11.5 Browser Compatibility

**Recommended Browsers:**
- Chrome 90+ ✓ (Best performance)
- Firefox 88+ ✓
- Safari 14+ ✓
- Edge 90+ ✓

**Not Supported:**
- Internet Explorer (any version)
- Opera Mini
- UC Browser

**Browser Settings:**
- Enable JavaScript
- Enable cookies
- Allow popups for this site
- Enable local storage

### 11.6 Mobile Issues

**Mobile Browser Support:**
- iOS Safari 14+
- Chrome Mobile 90+
- Samsung Internet 14+

**Common Mobile Issues:**

**Problem: Interface not responsive**
- Rotate device to landscape
- Zoom out if needed
- Use desktop mode for complex tasks
- Some features optimized for desktop

**Problem: Touch controls not working**
- Ensure screen is clean
- Remove screen protector if interfering
- Try different finger/stylus
- Restart browser

---

## 12. FAQs

### General Questions

**Q: What is the Hospital Insurance Claim Settlement Optimizer?**
A: It's an AI-powered platform that helps hospitals maximize insurance claim approval rates through intelligent policy analysis, real-time eligibility checking, and automated bill auditing.

**Q: Who can use the system?**
A: TPA administrators, hospital administrators, billing staff, and doctors. Each role has specific permissions and features.

**Q: Is my data secure?**
A: Yes. All data is encrypted in transit (TLS 1.3) and at rest (AES-256). The system is HIPAA-compliant with comprehensive audit trails.

**Q: How accurate is the AI analysis?**
A: Policy extraction typically achieves 85%+ confidence. Audit predictions are based on historical data and policy rules, with accuracy improving over time.

**Q: Can I integrate with my existing systems?**
A: Yes. The system provides REST APIs and webhook notifications for integration with EMR, billing, and other systems.

### Policy Management

**Q: What file formats are supported for policy upload?**
A: PDF files only, up to 50MB in size.

**Q: How long does policy processing take?**
A: Typically 3-5 minutes for standard policies. Complex policies may take longer.

**Q: Can I edit extracted policy data?**
A: Yes. You can review and correct any extraction errors before approving the policy.

**Q: How are policy versions managed?**
A: System automatically creates new versions for any changes. All versions are preserved with complete audit trails.

**Q: Can I rollback to a previous policy version?**
A: Yes. You can compare versions and rollback if needed. Rollback creates a new version (doesn't delete history).

### Eligibility Checking

**Q: How fast are eligibility checks?**
A: Single checks complete in under 2 seconds. Batch checks process 100 patients in approximately 30 seconds.

**Q: What if coverage is uncertain?**
A: System indicates uncertainty level and recommends manual verification with insurance company.

**Q: Can I check multiple procedures at once?**
A: Yes. You can add multiple procedures to check for bundling rules and combined coverage.

**Q: How do I get pre-authorization templates?**
A: If pre-authorization is required, click "Generate Template" button in eligibility results.

### Bill Auditing

**Q: How many line items can I audit at once?**
A: Up to 100 line items per claim. Larger bills should be split into multiple claims.

**Q: How long does audit take?**
A: Typically 20-30 seconds for 100 line items.

**Q: What if I disagree with audit results?**
A: Review the policy clause references provided. You can manually override results or contact support for clarification.

**Q: Can I re-audit after making changes?**
A: Yes. Click "Re-audit" button after applying optimization suggestions or making corrections.

**Q: How accurate are settlement ratio predictions?**
A: Predictions are based on historical data and policy rules. Accuracy improves as system learns from more claims.

### Reports and Analytics

**Q: Can I schedule automatic reports?**
A: Yes. You can schedule reports to run daily, weekly, monthly, or quarterly with automatic email delivery.

**Q: What export formats are available?**
A: PDF (formatted reports), Excel (data with pivot tables), CSV (raw data), and PowerPoint (presentation slides).

**Q: Can I create custom reports?**
A: Yes. Use the Custom Report Builder to select metrics, dimensions, and visualizations.

**Q: How far back does historical data go?**
A: Data is retained for 7 years for compliance. Older data may be archived but accessible on request.

### Technical Questions

**Q: What browsers are supported?**
A: Chrome 90+, Firefox 88+, Safari 14+, and Edge 90+. Internet Explorer is not supported.

**Q: Do I need to install any software?**
A: No. The system is entirely web-based. Just use a supported browser.

**Q: Can I use the system on mobile devices?**
A: Yes. The eligibility checker is optimized for mobile. Other features work on tablets but are best on desktop.

**Q: What internet speed do I need?**
A: Minimum 5 Mbps for optimal performance. Stable connection required for real-time features.

**Q: Is offline mode available?**
A: No. The system requires internet connection for real-time policy lookups and AI analysis.


---

## 13. Support and Contact

### 13.1 Getting Help

#### In-App Help

**Contextual Help:**
- Hover over (?) icons for tooltips
- Click "Help" button on any page
- Access relevant documentation
- View video tutorials

**Help Center:**
- Click "Help" in top navigation
- Search knowledge base
- Browse articles by category
- Watch tutorial videos
- Download user guides

#### Support Channels

**Email Support:**
- Email: support@revenuez.com
- Response time: Within 4 business hours
- Include:
  - Your name and hospital
  - Detailed description of issue
  - Screenshots if applicable
  - Steps to reproduce
  - Browser and OS information

**Phone Support:**
- Phone: 1-800-REVENUEZ (1-800-738-3683)
- Hours: Monday-Friday, 8 AM - 8 PM EST
- Emergency support: 24/7 for critical issues

**Live Chat:**
- Click chat icon (bottom-right)
- Available: Monday-Friday, 9 AM - 6 PM EST
- Average response time: < 2 minutes
- Chat history saved in your account

**Support Portal:**
- URL: support.revenuez.com
- Submit tickets
- Track ticket status
- View ticket history
- Access knowledge base

### 13.2 Training and Onboarding

#### New User Onboarding

**Welcome Email:**
- Sent upon account creation
- Includes:
  - Login credentials
  - Quick start guide
  - Training schedule
  - Support contacts

**Onboarding Checklist:**
- Complete profile setup
- Watch introduction video (15 min)
- Complete role-specific tutorial
- Perform first task with guidance
- Schedule training session

**Role-Specific Training:**

**TPA Administrators (2 hours):**
- System overview
- Policy management
- Dashboard navigation
- Report generation
- User management
- Webhook configuration

**Hospital Administrators (1.5 hours):**
- Dashboard overview
- Report generation
- User management
- Audit log review
- Compliance features

**Billing Staff (1.5 hours):**
- Claim creation
- Bill auditing
- Optimization suggestions
- Patient profiles
- Submission process

**Doctors (1 hour):**
- Eligibility checking
- Batch processing
- Pre-authorization templates
- Mobile interface

#### Ongoing Training

**Monthly Webinars:**
- New features overview
- Best practices
- Q&A sessions
- Advanced tips
- Register: training.revenuez.com

**Video Library:**
- 100+ tutorial videos
- Organized by topic
- Searchable
- Downloadable
- Updated regularly

**Documentation:**
- User guides (this document)
- API documentation
- Integration guides
- Best practices
- Release notes

### 13.3 System Status and Updates

#### System Status Page

**URL:** status.revenuez.com

**Information Available:**
- Current system status
- Scheduled maintenance
- Past incidents
- Performance metrics
- Subscribe to updates

**Status Indicators:**
- 🟢 Operational: All systems normal
- 🟡 Degraded: Some features affected
- 🔴 Outage: Service unavailable
- 🔵 Maintenance: Planned downtime

#### Maintenance Windows

**Scheduled Maintenance:**
- Announced 7 days in advance
- Typically: Sundays 2-4 AM EST
- Duration: Usually < 2 hours
- Email notifications sent
- Status page updated

**Emergency Maintenance:**
- Announced as soon as possible
- Performed only when critical
- Minimized duration
- Real-time status updates

#### Release Notes

**Accessing Release Notes:**
- Click "What's New" in help menu
- View recent updates
- See new features
- Read bug fixes
- Check known issues

**Release Schedule:**
- Major releases: Quarterly
- Minor releases: Monthly
- Patches: As needed
- Security updates: Immediate

### 13.4 Feedback and Feature Requests

#### Providing Feedback

**Feedback Form:**
- Click "Feedback" button (bottom-right)
- Rate your experience
- Describe issue or suggestion
- Attach screenshots
- Submit anonymously or with contact info

**Feature Requests:**
- Submit via feedback form
- Vote on existing requests
- Track request status
- Get notified when implemented

**User Community:**
- Forum: community.revenuez.com
- Share best practices
- Ask questions
- Connect with other users
- Vote on feature requests

### 13.5 Emergency Contacts

**Critical Issues (24/7):**
- Phone: 1-800-REVENUEZ, Option 1
- Email: emergency@revenuez.com
- Response time: Within 1 hour

**Security Issues:**
- Email: security@revenuez.com
- Phone: 1-800-REVENUEZ, Option 9
- Report immediately:
  - Data breaches
  - Unauthorized access
  - Security vulnerabilities
  - Suspicious activity

**Compliance Issues:**
- Email: compliance@revenuez.com
- Phone: 1-800-REVENUEZ, Option 8
- Report:
  - HIPAA violations
  - Audit trail concerns
  - Data retention issues
  - Privacy concerns

---

## Appendix A: Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Global search |
| `Ctrl/Cmd + /` | Show keyboard shortcuts |
| `Ctrl/Cmd + ,` | Open settings |
| `Esc` | Close modal/dialog |
| `?` | Open help |

### Navigation Shortcuts

| Shortcut | Action |
|----------|--------|
| `G then D` | Go to Dashboard |
| `G then P` | Go to Policies |
| `G then E` | Go to Eligibility Check |
| `G then B` | Go to Bill Audit |
| `G then R` | Go to Reports |

### Action Shortcuts

| Shortcut | Action |
|----------|--------|
| `N` | New (context-dependent) |
| `Ctrl/Cmd + S` | Save |
| `Ctrl/Cmd + Enter` | Submit |
| `Ctrl/Cmd + P` | Print |
| `Ctrl/Cmd + E` | Export |

---

## Appendix B: Glossary

**API (Application Programming Interface):** Interface for software systems to communicate.

**Audit Trail:** Complete record of all system actions and changes.

**Batch Processing:** Processing multiple items simultaneously.

**Claim Settlement Ratio (CSR):** Percentage of insurance claims approved and paid.

**CPT Code:** Current Procedural Terminology code for medical procedures.

**HIPAA:** Health Insurance Portability and Accountability Act - US healthcare privacy law.

**ICD-10:** International Classification of Diseases, 10th revision - diagnosis codes.

**MFA (Multi-Factor Authentication):** Security requiring multiple verification methods.

**OCR (Optical Character Recognition):** Technology to extract text from images/PDFs.

**Pre-authorization:** Insurance approval required before certain procedures.

**Settlement Ratio:** See Claim Settlement Ratio (CSR).

**TPA (Third Party Administrator):** Entity that processes insurance claims.

**Webhook:** Automated message sent when specific event occurs.

---

## Appendix C: Quick Reference Cards

### TPA Administrator Quick Reference

**Daily Tasks:**
- [ ] Review dashboard alerts
- [ ] Check high-risk claims
- [ ] Monitor CSR trends
- [ ] Review new policy uploads
- [ ] Respond to user questions

**Weekly Tasks:**
- [ ] Generate performance reports
- [ ] Review audit logs
- [ ] Check webhook activity
- [ ] Update policies as needed
- [ ] Conduct team training

**Monthly Tasks:**
- [ ] Generate monthly CSR report
- [ ] Review user access
- [ ] Analyze rejection trends
- [ ] Update documentation
- [ ] Plan improvements

### Doctor Quick Reference

**Before Patient Appointment:**
1. Run batch eligibility check for day's patients
2. Review coverage results
3. Identify pre-auth requirements
4. Prepare alternative treatment options

**During Patient Visit:**
1. Verify coverage for recommended procedures
2. Explain coverage and costs to patient
3. Generate pre-auth templates if needed
4. Document eligibility check

**After Patient Visit:**
1. Save eligibility results to patient record
2. Send pre-auth to billing if needed
3. Update treatment plan based on coverage

### Billing Staff Quick Reference

**Creating Claims:**
1. Gather all documentation
2. Enter patient and policy information
3. Add all line items accurately
4. Attach supporting documents
5. Save draft

**Auditing Claims:**
1. Review claim completeness
2. Submit for audit
3. Review audit results carefully
4. Apply optimization suggestions
5. Re-audit after changes
6. Finalize when optimal

**Submitting Claims:**
1. Complete final review checklist
2. Generate submission package
3. Submit via API or download
4. Track submission status
5. Handle rejections promptly

---

## Document Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | January 2026 | Initial release | RevenueZ Team |

---

**End of User Guide**

For the latest version of this guide, visit: docs.revenuez.com/user-guide

For technical documentation, visit: docs.revenuez.com/technical

For API documentation, visit: api.revenuez.com/docs

---

© 2026 RevenueZ Hospital Claim Optimizer. All rights reserved.
