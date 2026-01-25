# Hospital Claim Optimizer - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Hospital Insurance Claim Settlement Optimizer to AWS.

## Prerequisites

### Required Tools
- **Node.js** 18+ and npm
- **Python** 3.11+
- **AWS CLI** 2.x
- **AWS CDK** 2.x
- **Git**

### AWS Account Requirements
- AWS Account with appropriate permissions
- IAM user with AdministratorAccess or equivalent
- AWS credentials configured locally

### Installation Commands
```bash
# Install AWS CLI
# macOS
brew install awscli

# Install AWS CDK
npm install -g aws-cdk

# Verify installations
aws --version
cdk --version
node --version
python3 --version
```

## Pre-Deployment Steps

### 1. Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your default output format (json)
```

### 2. Clone Repository
```bash
git clone <repository-url>
cd hospital-claim-optimizer
```

### 3. Install Dependencies
```bash
# Backend dependencies
cd hospital-claim-optimizer
npm install

# Frontend dependencies
cd ../frontend
npm install
```

### 4. Run Tests
```bash
# Run all tests to ensure everything works
cd ..
python3 -m pytest hospital-claim-optimizer/tests/ -v
```

## Backend Deployment

### Option 1: Automated Deployment (Recommended)
```bash
cd hospital-claim-optimizer
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment
```bash
cd hospital-claim-optimizer

# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy
```

### Deployment Time
- First deployment: 10-15 minutes
- Subsequent deployments: 5-10 minutes

### Expected Outputs
After successful deployment, you'll see:
```
Outputs:
HospitalClaimOptimizerStack.ApiGatewayUrl = https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/
HospitalClaimOptimizerStack.UserPoolId = us-east-1_xxxxxxxxx
HospitalClaimOptimizerStack.UserPoolClientId = xxxxxxxxxxxxxxxxxxxxxxxxxx
HospitalClaimOptimizerStack.IdentityPoolId = us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
HospitalClaimOptimizerStack.DynamoDBTableName = RevenueZ_Main
HospitalClaimOptimizerStack.PolicyBucketName = hospital-policy-docs-xxxxx-us-east-1
HospitalClaimOptimizerStack.BillsBucketName = hospital-medical-bills-xxxxx-us-east-1
```

**Important:** Save these outputs - you'll need them for frontend configuration.

## Frontend Deployment

### 1. Configure Environment Variables
Create `frontend/.env` file:
```env
VITE_API_URL=https://xxxxx.execute-api.us-east-1.amazonaws.com/prod
VITE_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_IDENTITY_POOL_ID=us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
VITE_AWS_REGION=us-east-1
```

### 2. Build Frontend
```bash
cd frontend
npm run build
```

### 3. Deploy Frontend

#### Option A: AWS Amplify (Recommended)
```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize Amplify
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

#### Option B: AWS S3 + CloudFront
```bash
# Create S3 bucket
aws s3 mb s3://hospital-claim-optimizer-frontend

# Enable static website hosting
aws s3 website s3://hospital-claim-optimizer-frontend \
  --index-document index.html \
  --error-document index.html

# Upload build files
aws s3 sync dist/ s3://hospital-claim-optimizer-frontend

# Create CloudFront distribution (optional, for HTTPS)
# Use AWS Console or CLI to create distribution
```

#### Option C: Local Development
```bash
cd frontend
npm run dev
# Access at http://localhost:5173
```

## Post-Deployment Configuration

### 1. Create Cognito Users

#### Create Admin User
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username admin@hospital.com \
  --user-attributes Name=email,Value=admin@hospital.com Name=custom:role,Value=hospital_admin \
  --temporary-password TempPass123! \
  --message-action SUPPRESS
```

#### Create Doctor User
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username doctor@hospital.com \
  --user-attributes Name=email,Value=doctor@hospital.com Name=custom:role,Value=doctor \
  --temporary-password TempPass123! \
  --message-action SUPPRESS
```

#### Create Billing User
```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-east-1_xxxxxxxxx \
  --username billing@hospital.com \
  --user-attributes Name=email,Value=billing@hospital.com Name=custom:role,Value=billing_staff \
  --temporary-password TempPass123! \
  --message-action SUPPRESS
```

### 2. Configure Amazon SES (for email notifications)
```bash
# Verify email address for sending
aws ses verify-email-identity --email-address noreply@yourdomain.com

# Move out of sandbox (production)
# Request via AWS Console: SES > Account Dashboard > Request Production Access
```

### 3. Upload Sample Policy
1. Log in as admin user
2. Navigate to Policy Management
3. Upload a sample insurance policy PDF
4. Wait for AI extraction (30-60 seconds)
5. Review and approve policy

## Verification Steps

### 1. Test Backend APIs
```bash
# Get API URL from deployment outputs
API_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"

# Test health check (if implemented)
curl $API_URL/health

# Test authentication (requires token)
# Login via frontend first to get token
```

### 2. Test Frontend
1. Open frontend URL in browser
2. Log in with admin credentials
3. Navigate through all pages:
   - Dashboard
   - Policy Management
   - Reports
   - Audit Logs
   - Settings
4. Test key workflows:
   - Upload policy
   - Check eligibility
   - Audit bill
   - Generate report

### 3. Run E2E Tests
```bash
cd e2e
npm install
npx playwright test
```

## Monitoring and Observability

### CloudWatch Dashboard
Access the auto-created dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=HospitalClaimOptimizer
```

### Key Metrics to Monitor
- API Gateway request count and latency
- Lambda invocations and errors
- DynamoDB read/write capacity
- S3 bucket size
- Cognito user activity

### CloudWatch Alarms
Pre-configured alarms for:
- High Lambda error rates
- High Lambda duration
- DynamoDB throttling
- API Gateway 5xx errors

### X-Ray Tracing
View distributed traces:
```
https://console.aws.amazon.com/xray/home?region=us-east-1#/service-map
```

## Troubleshooting

### Deployment Fails
```bash
# Check CDK version
cdk --version

# Update CDK
npm install -g aws-cdk@latest

# Clear CDK cache
rm -rf cdk.out

# Re-run deployment
cdk deploy
```

### Lambda Timeout Errors
- Check CloudWatch Logs for specific Lambda function
- Increase timeout in CDK stack if needed
- Check DynamoDB capacity

### Authentication Issues
- Verify Cognito User Pool configuration
- Check user attributes (custom:role)
- Verify frontend environment variables
- Check browser console for errors

### Policy Extraction Fails
- Verify Textract permissions in IAM role
- Verify Bedrock permissions in IAM role
- Check CloudWatch Logs for policy-upload Lambda
- Ensure PDF is valid and < 50MB

## Rollback Procedure

### Rollback Backend
```bash
cd hospital-claim-optimizer

# List previous deployments
aws cloudformation describe-stacks --stack-name HospitalClaimOptimizerStack

# Rollback to previous version
cdk deploy --rollback
```

### Rollback Frontend
```bash
# If using S3
aws s3 sync s3://hospital-claim-optimizer-frontend-backup/ \
  s3://hospital-claim-optimizer-frontend/

# If using Amplify
amplify publish --rollback
```

## Cleanup (Destroy Resources)

**Warning:** This will delete all resources and data!

```bash
cd hospital-claim-optimizer

# Destroy CDK stack
cdk destroy

# Manually delete S3 buckets (if not empty)
aws s3 rb s3://hospital-policy-docs-xxxxx-us-east-1 --force
aws s3 rb s3://hospital-medical-bills-xxxxx-us-east-1 --force
```

## Cost Estimation

### Monthly Costs (Approximate)
- **Lambda:** $20-50 (based on usage)
- **DynamoDB:** $10-30 (on-demand pricing)
- **S3:** $5-20 (based on storage)
- **API Gateway:** $10-30 (based on requests)
- **Cognito:** Free tier (up to 50,000 MAUs)
- **Textract:** $1.50 per 1,000 pages
- **Bedrock:** $3 per 1M input tokens, $15 per 1M output tokens
- **CloudWatch:** $5-15 (logs and metrics)

**Total Estimated Cost:** $50-200/month (varies by usage)

### Cost Optimization Tips
- Use DynamoDB on-demand pricing for variable workloads
- Enable S3 lifecycle policies for old documents
- Use Lambda reserved concurrency wisely
- Monitor and optimize Lambda memory settings
- Use CloudWatch Logs retention policies

## Security Best Practices

### 1. Enable MFA for AWS Root Account
```bash
# Use AWS Console to enable MFA
```

### 2. Rotate AWS Credentials Regularly
```bash
# Create new access key
aws iam create-access-key --user-name your-username

# Update local credentials
aws configure

# Delete old access key
aws iam delete-access-key --access-key-id OLD_KEY_ID --user-name your-username
```

### 3. Enable CloudTrail
```bash
# Enable CloudTrail for audit logging
aws cloudtrail create-trail --name hospital-claim-optimizer-trail \
  --s3-bucket-name your-cloudtrail-bucket
```

### 4. Review IAM Policies
- Follow principle of least privilege
- Use IAM roles instead of access keys where possible
- Enable MFA for sensitive operations

### 5. Enable AWS WAF (Optional)
- Protect API Gateway from common attacks
- Configure rate limiting
- Block malicious IPs

## Support and Maintenance

### Regular Maintenance Tasks
- **Weekly:** Review CloudWatch alarms and metrics
- **Monthly:** Review and optimize costs
- **Quarterly:** Update dependencies and security patches
- **Annually:** Review and update disaster recovery plan

### Backup Strategy
- **DynamoDB:** Enable point-in-time recovery
- **S3:** Enable versioning and cross-region replication
- **Code:** Maintain Git repository with tags for releases

### Disaster Recovery
- **RTO (Recovery Time Objective):** 4 hours
- **RPO (Recovery Point Objective):** 1 hour
- **Backup Frequency:** Continuous (DynamoDB PITR)
- **Recovery Procedure:** Documented in runbook

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Cognito Documentation](https://docs.aws.amazon.com/cognito/)

## Contact and Support

For issues or questions:
1. Check CloudWatch Logs
2. Review this deployment guide
3. Check AWS Service Health Dashboard
4. Contact AWS Support (if applicable)

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
