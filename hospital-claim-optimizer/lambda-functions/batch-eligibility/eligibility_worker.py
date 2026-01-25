"""
Eligibility Worker Lambda
Processes individual patient eligibility checks in parallel
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
BATCH_JOBS_TABLE = os.environ.get('BATCH_JOBS_TABLE', 'BatchJobs')
BATCH_RESULTS_TABLE = os.environ.get('BATCH_RESULTS_TABLE', 'BatchResults')
ELIGIBILITY_CHECKER_LAMBDA = os.environ.get('ELIGIBILITY_CHECKER_LAMBDA', 'eligibility-checker')

batch_jobs_table = dynamodb.Table(BATCH_JOBS_TABLE)
batch_results_table = dynamodb.Table(BATCH_RESULTS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for eligibility worker
    Processes a batch of patients (typically 10)
    """
    try:
        batch_id = event.get('batchId')
        patients = event.get('patients', [])
        
        if not batch_id or not patients:
            raise ValueError('batchId and patients are required')
        
        results = []
        success_count = 0
        failure_count = 0
        
        # Process each patient
        for patient in patients:
            try:
                result = check_patient_eligibility(patient)
                result['batchId'] = batch_id
                result['patientId'] = patient['patientId']
                result['rowNumber'] = patient.get('rowNumber')
                
                # Store result in DynamoDB
                store_result(result)
                
                results.append(result)
                
                if result['status'] != 'ERROR':
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                print(f"Error processing patient {patient.get('patientId')}: {str(e)}")
                
                # Store error result
                error_result = {
                    'batchId': batch_id,
                    'patientId': patient.get('patientId'),
                    'rowNumber': patient.get('rowNumber'),
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                store_result(error_result)
                results.append(error_result)
                failure_count += 1
        
        # Update batch job progress
        update_batch_progress(batch_id, len(patients), success_count, failure_count)
        
        # Check if batch is complete
        check_batch_completion(batch_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'processed': len(patients),
                'success': success_count,
                'failures': failure_count
            })
        }
        
    except Exception as e:
        print(f"Error in eligibility worker: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def check_patient_eligibility(patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check eligibility for a single patient
    Calls the existing eligibility checker Lambda
    """
    try:
        # Invoke eligibility checker Lambda synchronously
        response = lambda_client.invoke(
            FunctionName=ELIGIBILITY_CHECKER_LAMBDA,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({
                    'patientId': patient['patientId'],
                    'patientName': patient['patientName'],
                    'dateOfBirth': patient['dateOfBirth'],
                    'policyNumber': patient['policyNumber'],
                    'procedureCode': patient['procedureCode']
                })
            })
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] != 200:
            raise Exception(f"Eligibility check failed: {response_payload}")
        
        # Extract eligibility result
        body = json.loads(response_payload.get('body', '{}'))
        
        return {
            'status': 'COVERED' if body.get('covered') else 'NOT_COVERED',
            'covered': body.get('covered', False),
            'coveragePercentage': body.get('coveragePercentage', 0),
            'preAuthRequired': body.get('preAuthRequired', False),
            'copay': body.get('copay', 0),
            'deductible': body.get('deductible', 0),
            'outOfPocketMax': body.get('outOfPocketMax', 0),
            'policyDetails': body.get('policyDetails', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Error checking eligibility: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def store_result(result: Dict[str, Any]) -> None:
    """
    Store eligibility result in DynamoDB
    """
    try:
        # Generate result ID
        result_id = f"{result['batchId']}#{result['patientId']}"
        result['resultId'] = result_id
        
        batch_results_table.put_item(Item=result)
        
    except Exception as e:
        print(f"Error storing result: {str(e)}")
        raise


def update_batch_progress(
    batch_id: str, 
    processed: int, 
    success: int, 
    failures: int
) -> None:
    """
    Update batch job progress atomically
    """
    try:
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression='''
                SET processedRecords = processedRecords + :processed,
                    successCount = successCount + :success,
                    failureCount = failureCount + :failures,
                    updatedAt = :timestamp
            ''',
            ExpressionAttributeValues={
                ':processed': processed,
                ':success': success,
                ':failures': failures,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Error updating batch progress: {str(e)}")


def check_batch_completion(batch_id: str) -> None:
    """
    Check if batch processing is complete and update status
    """
    try:
        # Get current batch job status
        response = batch_jobs_table.get_item(Key={'batchId': batch_id})
        
        if 'Item' not in response:
            return
        
        batch_job = response['Item']
        total = batch_job.get('totalRecords', 0)
        processed = batch_job.get('processedRecords', 0)
        
        # Check if all records are processed
        if total > 0 and processed >= total:
            # Mark batch as completed
            batch_jobs_table.update_item(
                Key={'batchId': batch_id},
                UpdateExpression='''
                    SET #status = :status,
                        completedAt = :timestamp,
                        updatedAt = :timestamp
                ''',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            print(f"Batch {batch_id} completed: {processed}/{total} records processed")
            
            # TODO: Send completion notification (email, webhook, etc.)
            
    except Exception as e:
        print(f"Error checking batch completion: {str(e)}")
