"""
Enhanced DynamoDB access layer with connection pooling and advanced patterns
"""
import boto3
import json
import logging
from typing import Dict, Any, List, Optional, Union
from botocore.exceptions import ClientError
from decimal import Decimal
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class DynamoDBAccessLayer:
    """Enhanced DynamoDB access layer with connection pooling and retry logic"""
    
    def __init__(self, table_name: str, region_name: str = 'us-east-1'):
        self.table_name = table_name
        self.region_name = region_name
        self._dynamodb = None
        self._table = None
        self.max_retries = 3
        self.base_delay = 0.1
    
    @property
    def dynamodb(self):
        """Lazy initialization of DynamoDB resource"""
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        return self._dynamodb
    
    @property
    def table(self):
        """Lazy initialization of DynamoDB table"""
        if self._table is None:
            self._table = self.dynamodb.Table(self.table_name)
        return self._table
    
    def _retry_with_backoff(self, operation, *args, **kwargs):
        """Retry operation with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code in ['ProvisionedThroughputExceededException', 'ThrottlingException']:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(f"Throttling detected, retrying in {delay}s (attempt {attempt + 1})")
                        time.sleep(delay)
                        continue
                raise e
            except Exception as e:
                logger.error(f"Unexpected error in DynamoDB operation: {str(e)}")
                raise e
    
    def put_item(self, item: Dict[str, Any], condition_expression: str = None) -> bool:
        """Put item with optional condition"""
        try:
            put_kwargs = {'Item': item}
            if condition_expression:
                put_kwargs['ConditionExpression'] = condition_expression
            
            self._retry_with_backoff(self.table.put_item, **put_kwargs)
            logger.info(f"Successfully put item with PK: {item.get('PK')}, SK: {item.get('SK')}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for item: {item.get('PK')}")
                return False
            logger.error(f"Error putting item: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error putting item: {str(e)}")
            return False
    
    def get_item(self, pk: str, sk: str, consistent_read: bool = False) -> Optional[Dict[str, Any]]:
        """Get single item by primary key"""
        try:
            response = self._retry_with_backoff(
                self.table.get_item,
                Key={'PK': pk, 'SK': sk},
                ConsistentRead=consistent_read
            )
            item = response.get('Item')
            if item:
                logger.debug(f"Retrieved item: PK={pk}, SK={sk}")
            return item
        except Exception as e:
            logger.error(f"Error getting item PK={pk}, SK={sk}: {str(e)}")
            return None
    
    def query_items(
        self, 
        pk: str, 
        sk_prefix: Optional[str] = None,
        sk_between: Optional[tuple] = None,
        index_name: Optional[str] = None,
        filter_expression: Optional[str] = None,
        limit: Optional[int] = None,
        scan_forward: bool = True
    ) -> List[Dict[str, Any]]:
        """Query items with various conditions"""
        try:
            query_kwargs = {
                'ScanIndexForward': scan_forward
            }
            
            if index_name:
                query_kwargs['IndexName'] = index_name
                # For GSI queries, use GSI1PK/GSI1SK or GSI2PK/GSI2SK
                if index_name == 'GSI1':
                    query_kwargs['KeyConditionExpression'] = 'GSI1PK = :pk'
                    query_kwargs['ExpressionAttributeValues'] = {':pk': pk}
                elif index_name == 'GSI2':
                    query_kwargs['KeyConditionExpression'] = 'GSI2PK = :pk'
                    query_kwargs['ExpressionAttributeValues'] = {':pk': pk}
            else:
                # Main table query
                if sk_prefix:
                    query_kwargs['KeyConditionExpression'] = 'PK = :pk AND begins_with(SK, :sk_prefix)'
                    query_kwargs['ExpressionAttributeValues'] = {
                        ':pk': pk,
                        ':sk_prefix': sk_prefix
                    }
                elif sk_between:
                    query_kwargs['KeyConditionExpression'] = 'PK = :pk AND SK BETWEEN :sk_start AND :sk_end'
                    query_kwargs['ExpressionAttributeValues'] = {
                        ':pk': pk,
                        ':sk_start': sk_between[0],
                        ':sk_end': sk_between[1]
                    }
                else:
                    query_kwargs['KeyConditionExpression'] = 'PK = :pk'
                    query_kwargs['ExpressionAttributeValues'] = {':pk': pk}
            
            if filter_expression:
                query_kwargs['FilterExpression'] = filter_expression
            
            if limit:
                query_kwargs['Limit'] = limit
            
            items = []
            response = self._retry_with_backoff(self.table.query, **query_kwargs)
            items.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                query_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                if limit:
                    query_kwargs['Limit'] = limit - len(items)
                
                response = self._retry_with_backoff(self.table.query, **query_kwargs)
                items.extend(response.get('Items', []))
            
            logger.debug(f"Query returned {len(items)} items for PK={pk}")
            return items
            
        except Exception as e:
            logger.error(f"Error querying items PK={pk}: {str(e)}")
            return []
    
    def update_item(
        self, 
        pk: str, 
        sk: str, 
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
        expression_attribute_names: Optional[Dict[str, str]] = None,
        condition_expression: Optional[str] = None
    ) -> bool:
        """Update item with expression"""
        try:
            update_kwargs = {
                'Key': {'PK': pk, 'SK': sk},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_attribute_values,
                'ReturnValues': 'UPDATED_NEW'
            }
            
            if expression_attribute_names:
                update_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            if condition_expression:
                update_kwargs['ConditionExpression'] = condition_expression
            
            self._retry_with_backoff(self.table.update_item, **update_kwargs)
            logger.info(f"Successfully updated item: PK={pk}, SK={sk}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for update: PK={pk}, SK={sk}")
                return False
            logger.error(f"Error updating item: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating item: {str(e)}")
            return False
    
    def delete_item(self, pk: str, sk: str, condition_expression: str = None) -> bool:
        """Delete item with optional condition"""
        try:
            delete_kwargs = {'Key': {'PK': pk, 'SK': sk}}
            if condition_expression:
                delete_kwargs['ConditionExpression'] = condition_expression
            
            self._retry_with_backoff(self.table.delete_item, **delete_kwargs)
            logger.info(f"Successfully deleted item: PK={pk}, SK={sk}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Conditional check failed for delete: PK={pk}, SK={sk}")
                return False
            logger.error(f"Error deleting item: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting item: {str(e)}")
            return False
    
    def batch_write_items(self, items: List[Dict[str, Any]], delete_keys: List[Dict[str, str]] = None) -> bool:
        """Batch write items (put and delete operations)"""
        try:
            with self.table.batch_writer() as batch:
                # Put items
                for item in items:
                    batch.put_item(Item=item)
                
                # Delete items
                if delete_keys:
                    for key in delete_keys:
                        batch.delete_item(Key=key)
            
            logger.info(f"Successfully batch wrote {len(items)} items and deleted {len(delete_keys or [])} items")
            return True
            
        except Exception as e:
            logger.error(f"Error in batch write: {str(e)}")
            return False
    
    def scan_items(
        self, 
        filter_expression: Optional[str] = None,
        expression_attribute_values: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Scan table with optional filter (use sparingly)"""
        try:
            scan_kwargs = {}
            
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
            
            if expression_attribute_values:
                scan_kwargs['ExpressionAttributeValues'] = expression_attribute_values
            
            if limit:
                scan_kwargs['Limit'] = limit
            
            items = []
            response = self._retry_with_backoff(self.table.scan, **scan_kwargs)
            items.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                if limit:
                    scan_kwargs['Limit'] = limit - len(items)
                
                response = self._retry_with_backoff(self.table.scan, **scan_kwargs)
                items.extend(response.get('Items', []))
            
            logger.warning(f"Scan operation returned {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"Error scanning table: {str(e)}")
            return []
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get table information and statistics"""
        try:
            response = self.table.meta.client.describe_table(TableName=self.table_name)
            table_info = response['Table']
            
            return {
                'table_name': table_info['TableName'],
                'table_status': table_info['TableStatus'],
                'item_count': table_info.get('ItemCount', 0),
                'table_size_bytes': table_info.get('TableSizeBytes', 0),
                'creation_date': table_info.get('CreationDateTime'),
                'billing_mode': table_info.get('BillingModeSummary', {}).get('BillingMode'),
                'global_secondary_indexes': [
                    {
                        'index_name': gsi['IndexName'],
                        'index_status': gsi['IndexStatus'],
                        'item_count': gsi.get('ItemCount', 0)
                    }
                    for gsi in table_info.get('GlobalSecondaryIndexes', [])
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            return {}

# Access pattern implementations
class HospitalClaimAccessPatterns:
    """Specific access patterns for Hospital Claim Optimizer"""
    
    def __init__(self, db_access: DynamoDBAccessLayer):
        self.db = db_access
    
    def get_hospital_dashboard_data(self, hospital_id: str) -> Dict[str, Any]:
        """Get all data needed for hospital dashboard"""
        try:
            # Get hospital info
            hospital = self.db.get_item(f"HOSPITAL#{hospital_id}", "METADATA")
            
            # Get all patients
            patients = self.db.query_items(f"HOSPITAL#{hospital_id}", "PATIENT#")
            
            # Get all policies
            policies = self.db.query_items(f"HOSPITAL#{hospital_id}", "POLICY#")
            
            # Get claims for all patients (this could be optimized with GSI)
            all_claims = []
            for patient in patients:
                patient_id = patient['SK'].replace('PATIENT#', '')
                claims = self.db.query_items(f"PATIENT#{patient_id}", "CLAIM#")
                all_claims.extend(claims)
            
            return {
                'hospital': hospital,
                'patients': patients,
                'policies': policies,
                'claims': all_claims,
                'summary': {
                    'total_patients': len(patients),
                    'total_policies': len(policies),
                    'total_claims': len(all_claims),
                    'active_claims': len([c for c in all_claims if c.get('status') in ['DRAFT', 'AUDITED']])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for hospital {hospital_id}: {str(e)}")
            return {}
    
    def get_high_risk_claims(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get high-risk claims using GSI1"""
        return self.db.query_items(
            pk="RISK#HIGH",
            index_name="GSI1",
            limit=limit,
            scan_forward=False  # Most recent first
        )
    
    def get_patient_complete_record(self, hospital_id: str, patient_id: str) -> Dict[str, Any]:
        """Get complete patient record with all claims and items"""
        try:
            # Get patient info
            patient = self.db.get_item(f"HOSPITAL#{hospital_id}", f"PATIENT#{patient_id}")
            if not patient:
                return {}
            
            # Get all claims for patient
            claims = self.db.query_items(f"PATIENT#{patient_id}", "CLAIM#")
            
            # Get all claim items for each claim
            for claim in claims:
                claim_id = claim['SK'].replace('CLAIM#', '')
                claim_items = self.db.query_items(f"CLAIM#{claim_id}", "ITEM#")
                claim['items'] = claim_items
            
            # Get audit trail
            audit_trail = self.db.query_items(f"AUDIT#{patient_id}")
            
            return {
                'patient': patient,
                'claims': claims,
                'audit_trail': audit_trail
            }
            
        except Exception as e:
            logger.error(f"Error getting complete record for patient {patient_id}: {str(e)}")
            return {}
    
    def search_policies_by_status(self, extraction_status: str) -> List[Dict[str, Any]]:
        """Search policies by extraction status"""
        return self.db.scan_items(
            filter_expression="extraction_status = :status",
            expression_attribute_values={":status": extraction_status}
        )
    
    def get_claims_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get claims within date range (requires scan - not optimal)"""
        return self.db.scan_items(
            filter_expression="created_at BETWEEN :start_date AND :end_date",
            expression_attribute_values={
                ":start_date": start_date,
                ":end_date": end_date
            }
        )