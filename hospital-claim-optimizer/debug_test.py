#!/usr/bin/env python3
import sys
sys.path.append('lambda-layers/common/python')

from data_models import Hospital

h = Hospital(hospital_id='test', org_name='Test Hospital', license_key='TEST123')
print('Hospital object:', h)
print('PK:', h.pk)
print('SK:', h.sk)
print('DynamoDB item:', h.to_dynamodb_item())
print('Keys in item:', list(h.to_dynamodb_item().keys()))