# Hospital Insurance Claim Settlement Optimizer

A comprehensive cloud-based system for optimizing hospital insurance claim settlements, built on AWS infrastructure with a React frontend and serverless backend.

## Overview

This system provides intelligent claim processing, eligibility verification, bill auditing, and risk assessment for hospital insurance operations. It features multi-factor authentication, policy version management, batch processing capabilities, and real-time analytics.

## Architecture

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: AWS Lambda (Python) + API Gateway
- **Infrastructure**: AWS CDK (TypeScript)
- **Database**: DynamoDB
- **Storage**: S3
- **Authentication**: Cognito with MFA support

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher) and npm
- **Python** (v3.9 or higher)
- **AWS CLI** configured with appropriate credentials
- **AWS CDK CLI**: `npm install -g aws-cdk`
- **Git**

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ra7rajat/hospital_claim_opt_kiro_aws.git
cd hospital_claim_opt_kiro_aws
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will download approximately 183 MB of dependencies.

### 3. Install Backend Dependencies

```bash
cd ../hospital-claim-optimizer
npm install
```

This will download approximately 174 MB of dependencies.

### 4. Install Python Dependencies

```bash
# Install Python dependencies for Lambda functions
pip install boto3 hypothesis pytest
```

### 5. Configure Environment Variables

Create a `.env` file in the `frontend` directory:

```bash
cd ../frontend
cp .env.example .env
```

Edit `.env` with your AWS configuration:

```
VITE_API_URL=your-api-gateway-url
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
```

## Development

### Run Frontend Locally

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Run Tests

```bash
# Frontend tests
cd frontend
npm run lint

# Backend property-based tests
cd ../hospital-claim-optimizer
pytest tests/
```

### Build Frontend

```bash
cd frontend
npm run build
```

## Deployment

### Deploy Infrastructure and Backend

```bash
cd hospital-claim-optimizer
./deploy.sh
```

Or manually:

```bash
cdk bootstrap  # First time only
cdk deploy
```

### Deploy Frontend

After deploying the backend, update your `.env` file with the API Gateway URL, then:

```bash
cd frontend
npm run build
# Upload dist/ folder to S3 or your hosting service
```

## Project Structure

```
.
├── frontend/                    # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page components
│   │   ├── lib/                # Utilities and API client
│   │   └── types/              # TypeScript type definitions
│   └── package.json
│
├── hospital-claim-optimizer/   # AWS CDK backend
│   ├── lambda-functions/       # Lambda function handlers
│   │   ├── auth/              # Authentication handlers
│   │   ├── eligibility-checker/
│   │   ├── bill-audit/
│   │   ├── policy-management/
│   │   └── ...
│   ├── lambda-layers/         # Shared Lambda layer code
│   │   └── common/python/     # Common Python utilities
│   ├── lib/                   # CDK stack definitions
│   ├── tests/                 # Property-based tests
│   └── package.json
│
├── e2e/                       # End-to-end tests
│   └── tests/
│
└── .kiro/                     # Kiro specs and documentation
    └── specs/
```

## Key Features

- **Authentication & Authorization**: Cognito-based auth with MFA support
- **Eligibility Checking**: Real-time insurance eligibility verification
- **Bill Auditing**: Automated bill review and discrepancy detection
- **Policy Management**: Version-controlled policy management with rollback
- **Batch Processing**: CSV-based batch eligibility checking
- **Risk Assessment**: Multi-claim risk scoring and analytics
- **Reporting**: Comprehensive analytics and reporting dashboard
- **Webhooks**: Configurable webhook notifications
- **Audit Logging**: Complete audit trail for compliance

## Documentation

- [Quick Start Guide](QUICK_START.md)
- [User Guide](USER_GUIDE.md)
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
- [Engineering Reference](ENGINEERING_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

## Testing

The project uses property-based testing with Hypothesis for robust test coverage:

```bash
cd hospital-claim-optimizer
pytest tests/test_property_*.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the ISC License.

## Support

For issues and questions, please open an issue on GitHub.

## Authors

- Rajat Dixit

## Acknowledgments

Built with AWS CDK, React, and modern serverless architecture patterns.
