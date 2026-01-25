"""
Batch Eligibility Orchestrator Lambda
Handles batch job creation, S3 upload, and orchestration of batch processing
"""

import json
import os
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
BATCH_JOBS_TABLE = os.environ.get('BATCH_JOBS_TABLE', 'BatchJobs')
BATCH_RESULTS_TABLE = os.environ.get('BATCH_RESULTS_TABLE', 'BatchResults')
S3_BUCKET = os.environ.get('BATCH_UPLOAD_BUCKET', 'hospital-claim-batch-uploads')
CSV_PARSER_LAMBDA = os.environ.get('CSV_PARSER_LAMBDA', 'csv-parser')
ELIGIBILITY_WORKER_LAMBDA = os.environ.get('ELIGIBILITY_WORKER_LAMBDA', 'eligibility-worker')

batch_jobs_table = dynamodb.Table(BATCH_JOBS_TABLE)
batch_results_table = dynamodb.Table(BATCH_RESULTS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for batch eligibility orchestration
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        if http_method == 'POST' and '/batch/create' in path:
            return create_batch_job(event)
        elif http_method == 'GET' and '/batch/status' in path:
            return get_batch_status(event)
        elif http_method == 'POST' and '/batch/process' in path:
            return process_batch(event)
        elif http_method == 'GET' and '/batch/results' in path:
            return get_batch_results(event)
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"Error in batch orchestrator: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def create_batch_job(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new batch job and generate S3 presigned URL for CSV upload
    """
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = event['requestContext']['authorizer']['claims']['sub']
        hospital_id = body.get('hospitalId')
        file_name = body.get('fileName', 'batch.csv')
        
        if not hospital_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'hospitalId is required'})
            }
        
        # Generate batch job ID
        batch_id = str(uuid.uuid4())
        s3_key = f"uploads/{hospital_id}/{batch_id}/{file_name}"
        
        # Create batch job record
        timestamp = datetime.utcnow().isoformat()
        batch_job = {
            'batchId': batch_id,
            'userId': user_id,
            'hospitalId': hospital_id,
            'fileName': file_name,
            's3Key': s3_key,
            'status': 'CREATED',
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'totalRecords': 0,
            'processedRecords': 0,
            'successCount': 0,
            'failureCount': 0
        }
        
        batch_jobs_table.put_item(Item=batch_job)
        
        # Generate presigned URL for upload (valid for 15 minutes)
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': s3_key,
                'ContentType': 'text/csv'
            },
            ExpiresIn=900
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'uploadUrl': presigned_url,
                's3Key': s3_key,
                'expiresIn': 900
            })
        }
        
    except Exception as e:
        print(f"Error creating batch job: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_batch_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the status of a batch job
    """
    try:
        batch_id = event['queryStringParameters'].get('batchId')
        
        if not batch_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'batchId is required'})
            }
        
        response = batch_jobs_table.get_item(Key={'batchId': batch_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Batch job not found'})
            }
        
        batch_job = response['Item']
        
        # Calculate progress percentage
        total = batch_job.get('totalRecords', 0)
        processed = batch_job.get('processedRecords', 0)
        progress = (processed / total * 100) if total > 0 else 0
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'status': batch_job['status'],
                'totalRecords': total,
                'processedRecords': processed,
                'successCount': batch_job.get('successCount', 0),
                'failureCount': batch_job.get('failureCount', 0),
                'progress': round(progress, 2),
                'createdAt': batch_job['createdAt'],
                'updatedAt': batch_job['updatedAt'],
                'completedAt': batch_job.get('completedAt')
            })
        }
        
    except Exception as e:
        print(f"Error getting batch status: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_batch(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start processing a batch job after CSV upload
    """
    try:
        body = json.loads(event.get('body', '{}'))
        batch_id = body.get('batchId')
        column_mapping = body.get('columnMapping', {})
        
        if not batch_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'batchId is required'})
            }
        
        # Get batch job
        response = batch_jobs_table.get_item(Key={'batchId': batch_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Batch job not found'})
            }
        
        batch_job = response['Item']
        
        # Update status to PROCESSING
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression='SET #status = :status, updatedAt = :timestamp',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Invoke CSV parser Lambda asynchronously
        lambda_client.invoke(
            FunctionName=CSV_PARSER_LAMBDA,
            InvocationType='Event',
            Payload=json.dumps({
                'batchId': batch_id,
                's3Key': batch_job['s3Key'],
                'columnMapping': column_mapping
            })
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'status': 'PROCESSING',
                'message': 'Batch processing started'
            })
        }
        
    except Exception as e:
        print(f"Error processing batch: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_batch_results(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get results for a completed batch job
    """
    try:
        batch_id = event['queryStringParameters'].get('batchId')
        status_filter = event['queryStringParameters'].get('status')
        
        if not batch_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'batchId is required'})
            }
        
        # Query results from DynamoDB
        query_params = {
            'IndexName': 'BatchIdIndex',
            'KeyConditionExpression': 'batchId = :batchId',
            'ExpressionAttributeValues': {':batchId': batch_id}
        }
        
        # Add status filter if provided
        if status_filter:
            query_params['FilterExpression'] = '#status = :status'
            query_params['ExpressionAttributeNames'] = {'#status': 'status'}
            query_params['ExpressionAttributeValues'][':status'] = status_filter
        
        response = batch_results_table.query(**query_params)
        results = response.get('Items', [])
        
        # Calculate summary statistics
        summary = {
            'total': len(results),
            'covered': sum(1 for r in results if r.get('status') == 'COVERED'),
            'notCovered': sum(1 for r in results if r.get('status') == 'NOT_COVERED'),
            'errors': sum(1 for r in results if r.get('status') == 'ERROR'),
            'preAuthRequired': sum(1 for r in results if r.get('preAuthRequired', False))
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'summary': summary,
                'results': results
            })
        }
        
    except Exception as e:
        print(f"Error getting batch results: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def update_batch_progress(batch_id: str, increment: int = 1, success: bool = True) -> None:
    """
    Update batch job progress (called by worker Lambdas)
    """
    try:
        update_expr = 'SET processedRecords = processedRecords + :inc, updatedAt = :timestamp'
        expr_values = {
            ':inc': increment,
            ':timestamp': datetime.utcnow().isoformat()
        }
        
        if success:
            update_expr += ', successCount = successCount + :inc'
        else:
            update_expr += ', failureCount = failureCount + :inc'
        
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
    except Exception as e:
        print(f"Error updating batch progress: {str(e)}")


def complete_batch_job(batch_id: str) -> None:
    """
    Mark batch job as completed
    """
    try:
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression='SET #status = :status, completedAt = :timestamp, updatedAt = :timestamp',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Error completing batch job: {str(e)}")
