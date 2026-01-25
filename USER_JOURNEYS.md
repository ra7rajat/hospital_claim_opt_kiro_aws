# Hospital Insurance Claim Settlement Optimizer - User Journeys

## Overview

This document outlines all user journeys for the Hospital Insurance Claim Settlement Optimizer, a B2B SaaS platform that streamlines insurance claim processing for hospitals, TPAs (Third-Party Administrators), doctors, and billing staff.

## User Personas

### 1. TPA Administrator
**Role**: Manages insurance policies, monitors claims, and oversees the entire claim settlement process.
**Goals**: Maximize claim settlement ratios, reduce processing time, identify high-risk claims early.

### 2. Hospital Billing Staff
**Role**: Submits and manages medical bills for insurance claims.
**Goals**: Ensure accurate billing, maximize approved amounts, reduce claim rejections.

### 3. Doctor
**Role**: Provides medical care and needs to verify patient insurance coverage.
**Goals**: Quickly check eligibility, understand coverage limits, know pre-authorization requirements.

### 4. Hospital Administrator
**Role**: Oversees hospital operations and financial performance.
**Goals**: Monitor claim settlement performance, track revenue, ensure compliance.

---

## Journey 1: TPA Administrator - Policy Upload and Management

### Scenario
A TPA administrator needs to upload a new insurance policy document and make it available for eligibility checking and claim auditing.

### Steps

#### 1.1 Login
- Navigate to application URL
- Enter credentials (email/password)
- Complete MFA if enabled
- Redirected to TPA Command Center Dashboard

#### 1.2 Navigate to Policy Management
- Click "Policies" in the main navigation
- View list of existing policies with status indicators

#### 1.3 Upload New Policy
- Click "Upload Policy" button
- Drag and drop PDF file (up to 50MB) or click to browse
- System validates file format and size
- Enter policy metadata:
  - Policy name
  - Hospital association
  - Effective date
  - Expiration date
- Click "Upload" button

#### 1.4 Policy Processing
- System uploads file to S3
- Amazon Textract extracts text from PDF (OCR)
- Amazon Bedrock (Claude 3.5 Sonnet) analyzes and extracts:
  - Coverage rules
  - Procedure codes and coverage percentages
  - Exclusions and limitations
  - Room rent caps
  - Co-pay conditions
  - Pre-authorization requirements
- Progress indicator shows processing status
- Extraction confidence score displayed

#### 1.5 Review Extracted Policy
- View structured policy data
- Review coverage rules in organized format
- Check extraction confidence score
- Edit any incorrect extractions if needed
- Approve policy for use

#### 1.6 Policy Versioning
- System automatically creates version 1
- All changes tracked in audit trail
- Can view version history
- Can compare versions

### Success Criteria
- Policy uploaded successfully
- Extraction confidence > 85%
- Policy available for eligibility checks within 2 minutes
- Audit trail created

### Alternative Flows
- **Low Confidence**: If extraction confidence < 70%, system flags for manual review
- **Upload Failure**: Retry mechanism with error details
- **Duplicate Policy**: System warns if similar policy exists

---

## Journey 2: Doctor - Real-time Eligibility Check

### Scenario
A doctor needs to quickly verify if a patient's insurance covers a specific procedure before treatment.

### Steps

#### 2.1 Access Eligibility Checker
- Login with doctor credentials
- Navigate to "Eligibility Check" page
- Mobile-responsive interface loads

#### 2.2 Enter Patient Information
- Enter patient ID or search by name
- System auto-fills patient details if found
- Select hospital/insurance policy

#### 2.3 Enter Procedure Details
- Enter procedure code (e.g., 99213) or search by name
- Add diagnosis codes (ICD-10)
- Specify procedure date
- Add any additional procedures (bundling check)

#### 2.4 Submit Eligibility Check
- Click "Check Eligibility" button
- System processes in < 2 seconds
- Real-time policy lookup via DynamoDB GSI

#### 2.5 View Coverage Results
- Coverage status displayed with color coding:
  - Green: Fully covered
  - Yellow: Partially covered
  - Red: Not covered
- Coverage percentage shown
- Patient responsibility amount calculated
- Pre-authorization requirement indicated
- Detailed explanation provided

#### 2.6 Pre-authorization Template (if required)
- System generates pre-authorization template
- Includes required documentation
- Provides submission instructions
- Can download or email template

#### 2.7 Save or Print Results
- Save eligibility check to patient record
- Print summary for patient
- Email results to billing department

### Success Criteria
- Response time < 2 seconds
- Accurate coverage information
- Clear pre-authorization guidance
- Mobile-friendly interface

### Alternative Flows
- **Patient Not Found**: Option to add new patient
- **Multiple Policies**: Select applicable policy
- **Uncertain Coverage**: System provides confidence level and suggests verification

---

## Journey 3: Billing Staff - Bill Audit and Optimization

### Scenario
Hospital billing staff submits a medical bill for audit to identify potential issues before submission to insurance.

### Steps

#### 3.1 Access Bill Audit Interface
- Login with billing staff credentials
- Navigate to "Bill Audit" page
- View pending bills dashboard

#### 3.2 Create New Bill
- Click "New Bill" button
- Enter patient information
- Select applicable insurance policy
- Add claim metadata (admission date, discharge date, etc.)

#### 3.3 Add Line Items
- Add individual bill items:
  - Procedure code
  - Description
  - Quantity
  - Unit price
  - Total amount
  - Date of service
- Import from CSV if available
- System validates procedure codes

#### 3.4 Submit for Audit
- Review bill summary
- Click "Submit for Audit" button
- System processes bill (target: 30 seconds for 100 items)

#### 3.5 Audit Processing
- Policy rule validation for each line item
- AI-powered analysis using Bedrock
- Procedure bundling validation
- Coverage percentage calculation
- Risk assessment

#### 3.6 Review Audit Results
- View categorized line items:
  - Approved items (green)
  - Rejected items (red)
  - Items requiring review (yellow)
- See rejection reasons with policy clause references
- View predicted settlement ratio
- Check risk score (High/Medium/Low)

#### 3.7 Optimization Suggestions
- AI-generated suggestions for rejected items:
  - Alternative procedure codes
  - Documentation requirements
  - Bundling opportunities
  - Appeal strategies
- Estimated impact on settlement ratio

#### 3.8 Make Corrections
- Edit line items based on suggestions
- Add supporting documentation
- Re-submit for audit
- Compare before/after settlement ratios

#### 3.9 Finalize and Submit
- Approve final bill
- Generate submission package
- Submit to insurance via API or download
- Track submission status

### Success Criteria
- Audit completed in < 30 seconds for 100 items
- Clear rejection explanations
- Actionable optimization suggestions
- Improved settlement ratio

### Alternative Flows
- **High Risk Bill**: Escalate to supervisor for review
- **Missing Information**: System highlights required fields
- **Policy Not Found**: Prompt to upload policy first

---

## Journey 4: TPA Administrator - Command Center Dashboard Monitoring

### Scenario
TPA administrator monitors overall claim performance, identifies trends, and responds to alerts.

### Steps

#### 4.1 Access Dashboard
- Login to system
- Land on TPA Command Center Dashboard
- Dashboard loads in < 3 seconds

#### 4.2 View Key Metrics
- Total claims processed
- Average Claim Settlement Ratio (CSR)
- High-risk claims count
- Processing time trends
- Cost savings achieved

#### 4.3 Review Active Claims
- View list of all active claims
- Filter by:
  - Hospital
  - Status (Draft, Audited, Submitted, Approved, Rejected)
  - Risk level
  - Date range
  - Amount range
- Sort by various columns
- Search by patient name or claim ID

#### 4.4 Monitor Alerts
- View real-time alerts:
  - High-risk claims detected
  - Claims requiring review
  - Policy expiration warnings
  - System performance issues
- Alert count badge on notification icon
- Click to view alert details

#### 4.5 Investigate High-Risk Claim
- Click on high-risk alert
- View claim details
- See risk factors:
  - High claim amount
  - Complex procedures
  - Low predicted settlement ratio
  - Historical rejection patterns
- Review audit results
- Check supporting documentation

#### 4.6 Take Action
- Assign claim to specialist
- Add notes and comments
- Request additional documentation
- Approve or reject claim
- Escalate to insurance company

#### 4.7 Analytics and Trends
- View CSR trend chart over time
- Compare performance across hospitals
- Identify top rejection reasons
- Track processing time improvements

#### 4.8 Acknowledge Alerts
- Mark alerts as reviewed
- Set reminders for follow-up
- Archive resolved alerts

### Success Criteria
- Dashboard loads in < 3 seconds
- Real-time data updates
- Clear visualization of trends
- Actionable alerts

### Alternative Flows
- **No Active Alerts**: Dashboard shows "All Clear" status
- **System Performance Issue**: Alert with link to diagnostics
- **Multiple Hospitals**: Filter by specific hospital

---

## Journey 5: TPA Administrator - Generate Reports and Analytics

### Scenario
TPA administrator needs to generate monthly performance reports for stakeholders.

### Steps

#### 5.1 Access Reports Interface
- Navigate to "Reports" section
- View available report types

#### 5.2 Select Report Type
- Choose from:
  - CSR Trend Analysis
  - Rejection Reason Analysis
  - Policy Clause Frequency
  - Hospital Performance Comparison
  - Processing Time Analysis
  - Cost Savings Report

#### 5.3 Configure Report Parameters
- Select date range (last month, quarter, year, custom)
- Choose hospitals to include
- Select policies to analyze
- Set comparison benchmarks

#### 5.4 Generate Report
- Click "Generate Report" button
- System processes data
- Progress indicator shown

#### 5.5 View Interactive Report
- View report with interactive charts
- Drill down into specific data points
- Click on chart elements for details
- Filter and sort data tables

#### 5.6 Analyze Insights
- Review key findings:
  - CSR trends over time
  - Top rejection reasons
  - Most frequently cited policy clauses
  - Hospital performance rankings
  - Processing time improvements
- Compare against benchmarks

#### 5.7 Export Report
- Choose export format:
  - PDF (formatted report)
  - Excel (raw data)
  - CSV (data export)
- Download to local machine
- Email to stakeholders

#### 5.8 Schedule Recurring Reports
- Set up automated report generation
- Choose frequency (daily, weekly, monthly)
- Configure email distribution list
- Set report parameters

### Success Criteria
- Report generated in < 10 seconds
- Interactive visualizations
- Multiple export formats
- Drill-down capabilities

### Alternative Flows
- **No Data Available**: Message indicating date range has no data
- **Large Dataset**: Pagination or sampling for performance
- **Custom Report**: Build custom report with selected metrics

---

## Journey 6: Hospital Administrator - Audit Log Review

### Scenario
Hospital administrator needs to review audit logs for compliance and security purposes.

### Steps

#### 6.1 Access Audit Logs
- Navigate to "Audit Logs" section
- View comprehensive audit trail

#### 6.2 Filter Audit Logs
- Filter by:
  - Date range
  - User
  - Action type (Create, Update, Delete, View)
  - Entity type (Policy, Claim, Patient)
  - Hospital
- Apply multiple filters

#### 6.3 Search Audit Logs
- Search by:
  - User email
  - Entity ID
  - Action description
  - IP address

#### 6.4 View Audit Details
- Click on audit entry
- View detailed information:
  - Timestamp
  - User who performed action
  - Action type
  - Entity affected
  - Before state (for updates)
  - After state (for updates)
  - IP address
  - User agent
  - Session ID

#### 6.5 Track Changes
- View change history for specific entity
- Compare versions
- See who made each change
- Understand change rationale from notes

#### 6.6 Export Audit Logs
- Select date range
- Choose export format (CSV, JSON)
- Download for compliance reporting
- Archive for record retention

#### 6.7 Compliance Reporting
- Generate compliance reports
- Verify HIPAA compliance
- Track data access patterns
- Identify unusual activity

### Success Criteria
- Complete audit trail
- Immutable logs
- Fast search and filtering
- Compliance-ready exports

### Alternative Flows
- **Suspicious Activity**: Alert generated for unusual patterns
- **Bulk Export**: Large date ranges handled efficiently
- **Retention Policy**: Automatic archival of old logs

---

## Journey 7: Billing Staff - Multi-Claim Risk Assessment

### Scenario
Billing staff reviews multiple claims for a patient to understand aggregated risk.

### Steps

#### 7.1 Access Patient Record
- Search for patient by ID or name
- View patient profile

#### 7.2 View All Claims
- See list of all claims for patient
- View individual risk scores
- See claim statuses

#### 7.3 Aggregate Risk Analysis
- System calculates aggregated risk across all claims
- Factors considered:
  - Total claim amounts
  - Average settlement ratios
  - Rejection patterns
  - Policy complexity
  - Historical performance

#### 7.4 View Risk Breakdown
- See risk factors contributing to score
- Understand risk trends over time
- Compare to hospital averages

#### 7.5 Risk Mitigation
- Review recommendations for reducing risk
- Identify claims needing attention
- Prioritize high-risk claims

#### 7.6 Update Risk Assessment
- Add new claim information
- System recalculates aggregated risk
- Track risk changes over time

### Success Criteria
- Accurate risk aggregation
- Clear risk factors
- Actionable recommendations
- Real-time updates

---

## Journey 8: TPA Administrator - Webhook Integration Setup

### Scenario
TPA administrator sets up webhook notifications for external systems.

### Steps

#### 8.1 Access Integration Settings
- Navigate to Settings > Integrations
- View webhook configuration

#### 8.2 Configure Webhook
- Enter webhook URL
- Select events to trigger notifications:
  - Claim submitted
  - Audit completed
  - High-risk claim detected
  - Policy updated
  - Settlement completed
- Configure authentication (API key, OAuth)

#### 8.3 Test Webhook
- Send test notification
- Verify receipt at endpoint
- Check payload format

#### 8.4 Activate Webhook
- Enable webhook
- Set retry policy
- Configure failure notifications

#### 8.5 Monitor Webhook Activity
- View webhook delivery logs
- Check success/failure rates
- Retry failed deliveries
- Debug payload issues

### Success Criteria
- Successful webhook delivery
- Proper authentication
- Reliable retry mechanism
- Clear error messages

---

## Journey 9: Doctor - Batch Eligibility Checking

### Scenario
Doctor needs to check eligibility for multiple patients scheduled for the day.

### Steps

#### 9.1 Access Batch Checker
- Navigate to Eligibility Check
- Select "Batch Mode"

#### 9.2 Upload Patient List
- Upload CSV with patient details
- Map columns to required fields
- Validate data format

#### 9.3 Process Batch
- System processes all patients
- Shows progress indicator
- Handles errors gracefully

#### 9.4 Review Results
- View summary of all checks
- Filter by coverage status
- Identify patients needing pre-auth

#### 9.5 Export Results
- Download results as CSV
- Print summary report
- Email to billing department

### Success Criteria
- Fast batch processing
- Clear results summary
- Error handling
- Export capabilities

---

## Journey 10: TPA Administrator - Policy Version Comparison

### Scenario
TPA administrator needs to compare two versions of a policy to understand changes.

### Steps

#### 10.1 Access Policy Management
- Navigate to Policies
- Select policy to review

#### 10.2 View Version History
- Click "Version History"
- See list of all versions with timestamps

#### 10.3 Select Versions to Compare
- Select two versions
- Click "Compare"

#### 10.4 View Comparison
- Side-by-side comparison
- Highlighted differences:
  - Added rules (green)
  - Removed rules (red)
  - Modified rules (yellow)
- See who made changes and when

#### 10.5 Understand Impact
- View claims affected by changes
- See potential impact on settlement ratios
- Identify patients needing notification

#### 10.6 Rollback if Needed
- Option to rollback to previous version
- Requires approval
- Audit trail maintained

### Success Criteria
- Clear version comparison
- Impact analysis
- Rollback capability
- Audit trail

---

## Cross-Journey Features

### Authentication and Authorization
- All journeys start with secure login
- Multi-factor authentication supported
- Role-based access control enforced
- Session timeout after inactivity
- Audit trail for all actions

### Performance
- Dashboard loads in < 3 seconds
- Eligibility checks in < 2 seconds
- Bill audit in < 30 seconds for 100 items
- Real-time updates via WebSocket
- Auto-scaling handles load spikes

### Mobile Responsiveness
- All interfaces work on tablets
- Eligibility checker optimized for mobile
- Touch-friendly controls
- Responsive layouts

### Data Security
- TLS 1.3 encryption in transit
- AES-256 encryption at rest
- Multi-tenant data isolation
- HIPAA compliance
- Regular security audits

### Notifications
- In-app notifications
- Email notifications
- Webhook notifications
- SMS notifications (optional)
- Configurable preferences

### Help and Support
- Contextual help tooltips
- User guide documentation
- Video tutorials
- In-app chat support
- Knowledge base

---

## Error Handling Patterns

### Common Error Scenarios

#### Network Errors
- Automatic retry with exponential backoff
- Offline mode with queue
- Clear error messages
- Recovery instructions

#### Validation Errors
- Inline field validation
- Clear error messages
- Suggested corrections
- Prevent submission until fixed

#### Processing Errors
- Detailed error logs
- Retry mechanism
- Fallback options
- Support contact information

#### Permission Errors
- Clear access denied messages
- Request access workflow
- Contact administrator option

---

## Success Metrics

### User Experience
- Task completion rate > 95%
- Average task time reduced by 60%
- User satisfaction score > 4.5/5
- Support ticket reduction by 70%

### Business Impact
- Claim settlement ratio improvement: +15%
- Processing time reduction: 60%
- Cost savings: $500K+ annually per hospital
- Claim rejection rate reduction: 40%

### System Performance
- 99.9% uptime
- < 2 second response time for 95% of requests
- Zero data loss
- < 1 hour recovery time

---

## Future Journey Enhancements

### Planned Features
1. **AI-Powered Predictions**: Predict claim outcomes before submission
2. **Automated Appeals**: Generate appeal letters automatically
3. **Patient Portal**: Allow patients to track their claims
4. **Mobile App**: Native iOS/Android apps
5. **Voice Interface**: Voice-activated eligibility checks
6. **Blockchain Integration**: Immutable claim records
7. **Advanced Analytics**: Machine learning insights
8. **Multi-language Support**: Support for regional languages

---

## Conclusion

These user journeys represent the complete experience of all stakeholders in the Hospital Insurance Claim Settlement Optimizer. Each journey is designed to be intuitive, efficient, and value-driven, ultimately improving claim settlement ratios and reducing processing time for hospitals and TPAs.

The system's architecture supports these journeys with:
- Scalable AWS infrastructure
- Real-time processing capabilities
- Comprehensive security measures
- Extensive audit trails
- Property-based testing for correctness
- Continuous monitoring and optimization

For technical implementation details, refer to:
- `requirements.md` - Detailed requirements
- `design.md` - System design and architecture
- `tasks.md` - Implementation task breakdown
- `openapi.yaml` - API specifications
