#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { HospitalClaimOptimizerStack } from '../lib/hospital-claim-optimizer-stack';

const app = new cdk.App();
new HospitalClaimOptimizerStack(app, 'HospitalClaimOptimizerStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});