import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class HospitalClaimOptimizerStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // AWS Cognito User Pool for Authentication
    const userPool = new cognito.UserPool(this, 'HospitalClaimOptimizerUserPool', {
      userPoolName: 'hospital-claim-optimizer-users',
      selfSignUpEnabled: false, // Admin-only registration
      signInAliases: {
        email: true,
        username: true,
      },
      passwordPolicy: {
        minLength: 12,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      mfa: cognito.Mfa.REQUIRED,
      mfaSecondFactor: {
        sms: true,
        otp: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // User Pool Client
    const userPoolClient = new cognito.UserPoolClient(this, 'HospitalClaimOptimizerClient', {
      userPool,
      userPoolClientName: 'hospital-claim-optimizer-client',
      generateSecret: false, // For web applications
      authFlows: {
        userSrp: true,
        userPassword: false, // Disable less secure flows
        adminUserPassword: true, // For admin operations
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
      },
      refreshTokenValidity: cdk.Duration.days(30),
      accessTokenValidity: cdk.Duration.hours(1),
      idTokenValidity: cdk.Duration.hours(1),
    });

    // Identity Pool for AWS resource access
    const identityPool = new cognito.CfnIdentityPool(this, 'HospitalClaimOptimizerIdentityPool', {
      identityPoolName: 'hospital-claim-optimizer-identity',
      allowUnauthenticatedIdentities: false,
      cognitoIdentityProviders: [{
        clientId: userPoolClient.userPoolClientId,
        providerName: userPool.userPoolProviderName,
      }],
    });

    // IAM Roles for different user types
    const hospitalAdminRole = new iam.Role(this, 'HospitalAdminRole', {
      assumedBy: new iam.FederatedPrincipal(
        'cognito-identity.amazonaws.com',
        {
          StringEquals: {
            'cognito-identity.amazonaws.com:aud': identityPool.ref,
          },
          'ForAnyValue:StringLike': {
            'cognito-identity.amazonaws.com:amr': 'authenticated',
          },
        },
        'sts:AssumeRoleWithWebIdentity'
      ),
      description: 'Role for hospital administrators with full access',
    });

    const doctorRole = new iam.Role(this, 'DoctorRole', {
      assumedBy: new iam.FederatedPrincipal(
        'cognito-identity.amazonaws.com',
        {
          StringEquals: {
            'cognito-identity.amazonaws.com:aud': identityPool.ref,
          },
          'ForAnyValue:StringLike': {
            'cognito-identity.amazonaws.com:amr': 'authenticated',
          },
        },
        'sts:AssumeRoleWithWebIdentity'
      ),
      description: 'Role for doctors with limited access to eligibility checking',
    });

    const tpaRole = new iam.Role(this, 'TPARole', {
      assumedBy: new iam.FederatedPrincipal(
        'cognito-identity.amazonaws.com',
        {
          StringEquals: {
            'cognito-identity.amazonaws.com:aud': identityPool.ref,
          },
          'ForAnyValue:StringLike': {
            'cognito-identity.amazonaws.com:amr': 'authenticated',
          },
        },
        'sts:AssumeRoleWithWebIdentity'
      ),
      description: 'Role for TPA users with audit and reporting access',
    });

    // DynamoDB Single Table Design with Auto-Scaling
    const mainTable = new dynamodb.Table(this, 'RevenueZMainTable', {
      tableName: 'RevenueZ_Main',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 5,
      writeCapacity: 5,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // Enable auto-scaling for DynamoDB table
    const readScaling = mainTable.autoScaleReadCapacity({
      minCapacity: 5,
      maxCapacity: 100,
    });

    readScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    const writeScaling = mainTable.autoScaleWriteCapacity({
      minCapacity: 5,
      maxCapacity: 100,
    });

    writeScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    // Global Secondary Indexes for access patterns with Auto-Scaling
    mainTable.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
      readCapacity: 5,
      writeCapacity: 5,
      projectionType: dynamodb.ProjectionType.ALL, // Optimize for read performance
    });

    mainTable.addGlobalSecondaryIndex({
      indexName: 'GSI2',
      partitionKey: { name: 'GSI2PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI2SK', type: dynamodb.AttributeType.STRING },
      readCapacity: 5,
      writeCapacity: 5,
      projectionType: dynamodb.ProjectionType.ALL, // Optimize for read performance
    });

    // Additional GSI for session lookups (authentication optimization)
    mainTable.addGlobalSecondaryIndex({
      indexName: 'GSI_SessionsByUser',
      partitionKey: { name: 'user_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'expires_at', type: dynamodb.AttributeType.STRING },
      readCapacity: 10,
      writeCapacity: 5,
      projectionType: dynamodb.ProjectionType.KEYS_ONLY, // Minimal projection for fast lookups
    });

    // Additional GSI for batch job lookups (batch processing optimization)
    mainTable.addGlobalSecondaryIndex({
      indexName: 'GSI_BatchJobsByUser',
      partitionKey: { name: 'user_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'created_at', type: dynamodb.AttributeType.STRING },
      readCapacity: 5,
      writeCapacity: 5,
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Additional GSI for webhook deliveries (webhook optimization)
    mainTable.addGlobalSecondaryIndex({
      indexName: 'GSI_WebhookDeliveriesByStatus',
      partitionKey: { name: 'webhook_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'status_timestamp', type: dynamodb.AttributeType.STRING },
      readCapacity: 5,
      writeCapacity: 5,
      projectionType: dynamodb.ProjectionType.ALL,
    });

    // Auto-scale GSI1
    const gsi1ReadScaling = mainTable.autoScaleGlobalSecondaryIndexReadCapacity('GSI1', {
      minCapacity: 5,
      maxCapacity: 50,
    });

    gsi1ReadScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    const gsi1WriteScaling = mainTable.autoScaleGlobalSecondaryIndexWriteCapacity('GSI1', {
      minCapacity: 5,
      maxCapacity: 50,
    });

    gsi1WriteScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    // Auto-scale GSI2
    const gsi2ReadScaling = mainTable.autoScaleGlobalSecondaryIndexReadCapacity('GSI2', {
      minCapacity: 5,
      maxCapacity: 50,
    });

    gsi2ReadScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    const gsi2WriteScaling = mainTable.autoScaleGlobalSecondaryIndexWriteCapacity('GSI2', {
      minCapacity: 5,
      maxCapacity: 50,
    });

    gsi2WriteScaling.scaleOnUtilization({
      targetUtilizationPercent: 70,
    });

    // S3 Buckets for document storage with AES-256 encryption
    const policyDocumentsBucket = new s3.Bucket(this, 'PolicyDocumentsBucket', {
      bucketName: `hospital-policy-docs-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED, // Uses AES-256
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      enforceSSL: true, // Require TLS for all requests
      lifecycleRules: [{
        id: 'DeleteOldVersions',
        expiration: cdk.Duration.days(365),
        noncurrentVersionExpiration: cdk.Duration.days(90),
      }],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    const medicalBillsBucket = new s3.Bucket(this, 'MedicalBillsBucket', {
      bucketName: `hospital-medical-bills-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED, // Uses AES-256
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      enforceSSL: true, // Require TLS for all requests
      lifecycleRules: [{
        id: 'DeleteOldVersions',
        expiration: cdk.Duration.days(2555), // 7 years for compliance
        noncurrentVersionExpiration: cdk.Duration.days(90),
      }],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // IAM Role for Lambda functions
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('AWSXRayDaemonWriteAccess'), // X-Ray tracing
      ],
      inlinePolicies: {
        DynamoDBAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'dynamodb:GetItem',
                'dynamodb:PutItem',
                'dynamodb:UpdateItem',
                'dynamodb:DeleteItem',
                'dynamodb:Query',
                'dynamodb:Scan',
                'dynamodb:BatchGetItem',
                'dynamodb:BatchWriteItem',
              ],
              resources: [
                mainTable.tableArn,
                `${mainTable.tableArn}/index/*`,
              ],
            }),
          ],
        }),
        S3Access: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                's3:GetObject',
                's3:PutObject',
                's3:DeleteObject',
                's3:GetObjectVersion',
              ],
              resources: [
                `${policyDocumentsBucket.bucketArn}/*`,
                `${medicalBillsBucket.bucketArn}/*`,
              ],
            }),
          ],
        }),
        TextractAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'textract:AnalyzeDocument',
                'textract:DetectDocumentText',
                'textract:StartDocumentAnalysis',
                'textract:GetDocumentAnalysis',
              ],
              resources: ['*'],
            }),
          ],
        }),
        BedrockAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                'bedrock:InvokeModel',
                'bedrock:InvokeModelWithResponseStream',
              ],
              resources: [
                `arn:aws:bedrock:${this.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
              ],
            }),
          ],
        }),
      },
    });

    // Lambda Layer for common dependencies
    const commonLayer = new lambda.LayerVersion(this, 'CommonLayer', {
      code: lambda.Code.fromAsset('lambda-layers/common'),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      description: 'Common dependencies for Hospital Claim Optimizer',
    });

    // Policy Upload Handler Lambda
    const policyUploadHandler = new lambda.Function(this, 'PolicyUploadHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'policy_upload.handler',
      code: lambda.Code.fromAsset('lambda-functions/policy-upload'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.minutes(5),
      memorySize: 1024,
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      environment: {
        TABLE_NAME: mainTable.tableName,
        POLICY_BUCKET: policyDocumentsBucket.bucketName,
      },
    });

    // Eligibility Checker Lambda with Reserved Concurrency and Optimizations
    const eligibilityChecker = new lambda.Function(this, 'EligibilityChecker', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'eligibility_check.handler',
      code: lambda.Code.fromAsset('lambda-functions/eligibility-checker'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024, // Increased for better performance
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      reservedConcurrentExecutions: 100, // Reserve capacity for high-priority function
      environment: {
        TABLE_NAME: mainTable.tableName,
        ENABLE_CACHE: 'true',
        CACHE_TTL_SECONDS: '300',
      },
    });

    // Bill Audit Engine Lambda with Reserved Concurrency
    const billAuditEngine = new lambda.Function(this, 'BillAuditEngine', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'bill_audit.handler',
      code: lambda.Code.fromAsset('lambda-functions/bill-audit'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.minutes(5),
      memorySize: 2048,
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      reservedConcurrentExecutions: 50, // Reserve capacity for resource-intensive function
      environment: {
        TABLE_NAME: mainTable.tableName,
        BILLS_BUCKET: medicalBillsBucket.bucketName,
      },
    });

    // Risk Scorer Lambda
    const riskScorer = new lambda.Function(this, 'RiskScorer', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'risk_scorer.handler',
      code: lambda.Code.fromAsset('lambda-functions/risk-scorer'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      environment: {
        TABLE_NAME: mainTable.tableName,
      },
    });

    // Dashboard API Lambda with Optimizations
    const dashboardApi = new lambda.Function(this, 'DashboardApi', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'dashboard.handler',
      code: lambda.Code.fromAsset('lambda-functions/dashboard'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 2048, // Increased for aggregation performance
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      environment: {
        TABLE_NAME: mainTable.tableName,
        ENABLE_CACHE: 'true',
        CACHE_TTL_SECONDS: '180', // 3 minutes cache for dashboard data
      },
    });

    // Policy Management Lambda
    const policyManagement = new lambda.Function(this, 'PolicyManagement', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'policy_management.handler',
      code: lambda.Code.fromAsset('lambda-functions/policy-management'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      environment: {
        TABLE_NAME: mainTable.tableName,
      },
    });

    // Reports Lambda
    const reportsHandler = new lambda.Function(this, 'ReportsHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'reports.handler',
      code: lambda.Code.fromAsset('lambda-functions/reports'),
      role: lambdaExecutionRole,
      layers: [commonLayer],
      timeout: cdk.Duration.minutes(2),
      memorySize: 1024,
      tracing: lambda.Tracing.ACTIVE, // Enable X-Ray tracing
      environment: {
        TABLE_NAME: mainTable.tableName,
      },
    });

    // API Gateway with Cognito Authorization
    const api = new apigateway.RestApi(this, 'HospitalClaimOptimizerApi', {
      restApiName: 'Hospital Claim Optimizer API',
      description: 'API for Hospital Insurance Claim Settlement Optimizer',
      deployOptions: {
        stageName: 'prod',
        throttlingBurstLimit: 1000,
        throttlingRateLimit: 500,
        metricsEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        tracingEnabled: true, // Enable X-Ray tracing
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        maxAge: cdk.Duration.hours(1),
      },
    });

    // Cognito Authorizer
    const cognitoAuthorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
      identitySource: 'method.request.header.Authorization',
      authorizerName: 'HospitalClaimOptimizerAuthorizer',
    });

    // Identity Pool Role Attachments
    new cognito.CfnIdentityPoolRoleAttachment(this, 'IdentityPoolRoleAttachment', {
      identityPoolId: identityPool.ref,
      roles: {
        authenticated: hospitalAdminRole.roleArn, // Default authenticated role
      },
      roleMappings: {
        'cognito-idp.us-east-1.amazonaws.com/' + userPool.userPoolId + ':' + userPoolClient.userPoolClientId: {
          type: 'Rules',
          ambiguousRoleResolution: 'AuthenticatedRole',
          rulesConfiguration: {
            rules: [
              {
                claim: 'custom:role',
                matchType: 'Equals',
                value: 'hospital_admin',
                roleArn: hospitalAdminRole.roleArn,
              },
              {
                claim: 'custom:role',
                matchType: 'Equals',
                value: 'doctor',
                roleArn: doctorRole.roleArn,
              },
              {
                claim: 'custom:role',
                matchType: 'Equals',
                value: 'tpa_user',
                roleArn: tpaRole.roleArn,
              },
            ],
          },
        },
      },
    });

    // API Routes with Authorization
    
    // Policy Management Routes
    const policyResource = api.root.addResource('policy');
    
    // POST /policy - Upload new policy
    policyResource.addMethod('POST', new apigateway.LambdaIntegration(policyUploadHandler), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
      requestValidator: new apigateway.RequestValidator(this, 'PolicyUploadValidator', {
        restApi: api,
        validateRequestBody: true,
        validateRequestParameters: true,
      }),
    });
    
    // GET /policy - List policies
    policyResource.addMethod('GET', new apigateway.LambdaIntegration(policyManagement), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /policy/{policyId} - Get specific policy
    const policyIdResource = policyResource.addResource('{policyId}');
    policyIdResource.addMethod('GET', new apigateway.LambdaIntegration(policyManagement), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // PUT /policy/{policyId} - Update policy
    policyIdResource.addMethod('PUT', new apigateway.LambdaIntegration(policyManagement), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // DELETE /policy/{policyId} - Delete policy
    policyIdResource.addMethod('DELETE', new apigateway.LambdaIntegration(policyManagement), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Eligibility Checking Routes
    const eligibilityResource = api.root.addResource('check-eligibility');
    eligibilityResource.addMethod('POST', new apigateway.LambdaIntegration(eligibilityChecker, {
      timeout: cdk.Duration.seconds(29), // Just under Lambda timeout
    }), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
      requestValidator: new apigateway.RequestValidator(this, 'EligibilityValidator', {
        restApi: api,
        validateRequestBody: true,
      }),
    });

    // Bill Audit Routes
    const auditResource = api.root.addResource('audit-claim');
    auditResource.addMethod('POST', new apigateway.LambdaIntegration(billAuditEngine, {
      timeout: cdk.Duration.seconds(29),
    }), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /audit-claim/{claimId} - Get audit results
    const auditIdResource = auditResource.addResource('{claimId}');
    auditIdResource.addMethod('GET', new apigateway.LambdaIntegration(billAuditEngine), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Risk Scoring Routes
    const riskResource = api.root.addResource('risk-score');
    riskResource.addMethod('POST', new apigateway.LambdaIntegration(riskScorer), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /risk-score/{claimId} - Get risk score
    const riskIdResource = riskResource.addResource('{claimId}');
    riskIdResource.addMethod('GET', new apigateway.LambdaIntegration(riskScorer), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Dashboard Routes
    const dashboardResource = api.root.addResource('dashboard');
    
    // GET /dashboard - Get dashboard data
    dashboardResource.addMethod('GET', new apigateway.LambdaIntegration(dashboardApi), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /dashboard/alerts - Get alerts
    const alertsResource = dashboardResource.addResource('alerts');
    alertsResource.addMethod('GET', new apigateway.LambdaIntegration(dashboardApi), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // POST /dashboard/alerts/{alertId}/acknowledge - Acknowledge alert
    const alertIdResource = alertsResource.addResource('{alertId}');
    const acknowledgeResource = alertIdResource.addResource('acknowledge');
    acknowledgeResource.addMethod('POST', new apigateway.LambdaIntegration(dashboardApi), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Reports Routes
    const reportsResource = api.root.addResource('reports');
    
    // POST /reports/generate - Generate report
    const generateResource = reportsResource.addResource('generate');
    generateResource.addMethod('POST', new apigateway.LambdaIntegration(reportsHandler, {
      timeout: cdk.Duration.seconds(29),
    }), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /reports - List reports
    reportsResource.addMethod('GET', new apigateway.LambdaIntegration(reportsHandler), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });
    
    // GET /reports/{reportId} - Get specific report
    const reportIdResource = reportsResource.addResource('{reportId}');
    reportIdResource.addMethod('GET', new apigateway.LambdaIntegration(reportsHandler), {
      authorizer: cognitoAuthorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Add role-based permissions to IAM roles
    hospitalAdminRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'execute-api:Invoke',
      ],
      resources: [
        `${api.arnForExecuteApi()}/*`,
      ],
    }));

    doctorRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'execute-api:Invoke',
      ],
      resources: [
        `${api.arnForExecuteApi()}/*/check-eligibility`,
      ],
    }));

    tpaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'execute-api:Invoke',
      ],
      resources: [
        `${api.arnForExecuteApi()}/*/audit-claim`,
        `${api.arnForExecuteApi()}/*/dashboard`,
      ],
    }));

    // Outputs
    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      value: api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      description: 'Cognito User Pool ID',
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
    });

    new cdk.CfnOutput(this, 'IdentityPoolId', {
      value: identityPool.ref,
      description: 'Cognito Identity Pool ID',
    });

    new cdk.CfnOutput(this, 'DynamoDBTableName', {
      value: mainTable.tableName,
      description: 'DynamoDB Table Name',
    });

    new cdk.CfnOutput(this, 'PolicyBucketName', {
      value: policyDocumentsBucket.bucketName,
      description: 'Policy Documents S3 Bucket',
    });

    new cdk.CfnOutput(this, 'BillsBucketName', {
      value: medicalBillsBucket.bucketName,
      description: 'Medical Bills S3 Bucket',
    });

    // CloudWatch Dashboard for Monitoring
    const dashboard = new cloudwatch.Dashboard(this, 'HospitalClaimOptimizerDashboard', {
      dashboardName: 'HospitalClaimOptimizer',
    });

    // API Gateway Metrics
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API Gateway Requests',
        left: [
          api.metricCount({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'API Gateway Latency',
        left: [
          api.metricLatency({ statistic: 'Average', period: cdk.Duration.minutes(5) }),
          api.metricLatency({ statistic: 'p99', period: cdk.Duration.minutes(5) }),
        ],
        width: 12,
      })
    );

    // Lambda Function Metrics
    const lambdaFunctions = [
      { name: 'Policy Upload', func: policyUploadHandler },
      { name: 'Eligibility Checker', func: eligibilityChecker },
      { name: 'Bill Audit', func: billAuditEngine },
      { name: 'Risk Scorer', func: riskScorer },
      { name: 'Dashboard', func: dashboardApi },
      { name: 'Reports', func: reportsHandler },
    ];

    lambdaFunctions.forEach(({ name, func }) => {
      dashboard.addWidgets(
        new cloudwatch.GraphWidget({
          title: `${name} - Invocations & Errors`,
          left: [
            func.metricInvocations({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
          ],
          right: [
            func.metricErrors({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
          ],
          width: 12,
        })
      );

      // Create alarms for high error rates
      const errorAlarm = new cloudwatch.Alarm(this, `${name}ErrorAlarm`, {
        metric: func.metricErrors({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
        threshold: 10,
        evaluationPeriods: 2,
        alarmDescription: `High error rate for ${name} Lambda function`,
        alarmName: `${name}-high-errors`,
      });

      // Create alarms for high duration
      const durationAlarm = new cloudwatch.Alarm(this, `${name}DurationAlarm`, {
        metric: func.metricDuration({ statistic: 'Average', period: cdk.Duration.minutes(5) }),
        threshold: func.timeout ? func.timeout.toMilliseconds() * 0.8 : 25000,
        evaluationPeriods: 2,
        alarmDescription: `High duration for ${name} Lambda function`,
        alarmName: `${name}-high-duration`,
      });
    });

    // DynamoDB Metrics
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'DynamoDB Read/Write Capacity',
        left: [
          mainTable.metricConsumedReadCapacityUnits({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
          mainTable.metricConsumedWriteCapacityUnits({ statistic: 'Sum', period: cdk.Duration.minutes(5) }),
        ],
        width: 12,
      })
    );

    // Custom Business Metrics
    const csrMetric = new cloudwatch.Metric({
      namespace: 'HospitalClaimOptimizer',
      metricName: 'ClaimSettlementRatio',
      statistic: 'Average',
      period: cdk.Duration.hours(1),
    });

    const processingTimeMetric = new cloudwatch.Metric({
      namespace: 'HospitalClaimOptimizer',
      metricName: 'AuditProcessingTime',
      statistic: 'Average',
      period: cdk.Duration.minutes(5),
    });

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Business Metrics - CSR',
        left: [csrMetric],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Business Metrics - Processing Time',
        left: [processingTimeMetric],
        width: 12,
      })
    );

    // Output dashboard URL
    new cdk.CfnOutput(this, 'DashboardUrl', {
      value: `https://console.aws.amazon.com/cloudwatch/home?region=${this.region}#dashboards:name=${dashboard.dashboardName}`,
      description: 'CloudWatch Dashboard URL',
    });
  }
}