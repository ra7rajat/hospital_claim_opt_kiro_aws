#!/bin/bash

# Hospital Claim Optimizer - Deployment Script
# This script deploys the backend infrastructure to AWS

set -e

echo "========================================="
echo "Hospital Claim Optimizer - Deployment"
echo "========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "Error: AWS CDK is not installed"
    echo "Please install CDK: npm install -g aws-cdk"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured"
    echo "Please configure AWS CLI: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

echo "AWS Account: $ACCOUNT_ID"
echo "AWS Region: $REGION"
echo ""

# Install dependencies
echo "Installing dependencies..."
npm install
echo ""

# Run tests
echo "Running tests..."
cd ..
python3 -m pytest hospital-claim-optimizer/tests/ -v
if [ $? -ne 0 ]; then
    echo "Error: Tests failed"
    exit 1
fi
cd hospital-claim-optimizer
echo ""

# Bootstrap CDK (if not already done)
echo "Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit &> /dev/null; then
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://$ACCOUNT_ID/$REGION
else
    echo "CDK already bootstrapped"
fi
echo ""

# Synthesize CloudFormation template
echo "Synthesizing CloudFormation template..."
cdk synth
echo ""

# Deploy
echo "Deploying to AWS..."
echo "This may take 10-15 minutes..."
cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "Deployment Successful!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Note the API Gateway URL from the outputs above"
    echo "2. Update frontend/.env with the API URL"
    echo "3. Deploy frontend: cd ../frontend && npm run build"
    echo "4. Create Cognito users for testing"
    echo ""
else
    echo ""
    echo "========================================="
    echo "Deployment Failed"
    echo "========================================="
    echo "Please check the error messages above"
    exit 1
fi
