"""
CSV Parser and Validator Lambda
Parses uploaded CSV files, validates data, and triggers eligibility workers
"""

import json
import csv
import io
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
BATCH_JOBS_TABLE = os.environ.get('BATCH_JOBS_TABLE', 'BatchJobs')
S3_BUCKET = os.environ.get('BATCH_UPLOAD_BUCKET', 'hospital-claim-batch-uploads')
ELIGIBILITY_WORKER_LAMBDA = os.environ.get('ELIGIBILITY_WORKER_LAMBDA', 'eligibility-worker')
BATCH_SIZE = 10  # Process 10 patients per worker Lambda

batch_jobs_table = dynamodb.Table(BATCH_JOBS_TABLE)

# Required fields for eligibility check
REQUIRED_FIELDS = [
    'patientId',
    'patientName',
    'dateOfBirth',
    'policyNumber',
    'procedureCode'
]

# Common column name variations for auto-detection
COLUMN_MAPPINGS = {
    'patientId': ['patient_id', 'patient id', 'id', 'patient number', 'mrn'],
    'patientName': ['patient_name', 'patient name', 'name', 'full name', 'patient'],
    'dateOfBirth': ['date_of_birth', 'date of birth', 'dob', 'birth date', 'birthdate'],
    'policyNumber': ['policy_number', 'policy number', 'policy', 'insurance number', 'policy id'],
    'procedureCode': ['procedure_code', 'procedure code', 'procedure', 'cpt code', 'cpt']
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for CSV parsing
    """
    try:
        batch_id = event.get('batchId')
        s3_key = event.get('s3Key')
        column_mapping = event.get('columnMapping', {})
        
        if not batch_id or not s3_key:
            raise ValueError('batchId and s3Key are required')
        
        # Download CSV from S3
        csv_content = download_csv_from_s3(s3_key)
        
        # Parse and validate CSV
        patients, validation_errors = parse_and_validate_csv(
            csv_content, 
            column_mapping
        )
        
        if validation_errors:
            # Update batch job with validation errors
            update_batch_status(batch_id, 'VALIDATION_FAILED', validation_errors)
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'CSV validation failed',
                    'errors': validation_errors
                })
            }
        
        # Update batch job with total record count
        total_records = len(patients)
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression='SET totalRecords = :total, updatedAt = :timestamp',
            ExpressionAttributeValues={
                ':total': total_records,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Split patients into batches and invoke worker Lambdas
        invoke_eligibility_workers(batch_id, patients)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'batchId': batch_id,
                'totalRecords': total_records,
                'message': 'CSV parsed successfully, processing started'
            })
        }
        
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}")
        if 'batch_id' in locals():
            update_batch_status(batch_id, 'FAILED', [str(e)])
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def download_csv_from_s3(s3_key: str) -> str:
    """
    Download CSV file from S3
    """
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return response['Body'].read().decode('utf-8')
    except ClientError as e:
        raise Exception(f"Failed to download CSV from S3: {str(e)}")


def parse_and_validate_csv(
    csv_content: str, 
    column_mapping: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Parse CSV content and validate data
    Returns: (patients, validation_errors)
    """
    patients = []
    validation_errors = []
    
    try:
        # Parse CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        if not reader.fieldnames:
            validation_errors.append("CSV file is empty or has no headers")
            return [], validation_errors
        
        # Auto-detect column mapping if not provided
        if not column_mapping:
            column_mapping = auto_detect_columns(reader.fieldnames)
        
        # Validate that all required fields are mapped
        missing_fields = []
        for required_field in REQUIRED_FIELDS:
            if required_field not in column_mapping:
                missing_fields.append(required_field)
        
        if missing_fields:
            validation_errors.append(
                f"Missing required field mappings: {', '.join(missing_fields)}"
            )
            return [], validation_errors
        
        # Validate column names exist in CSV
        for field, csv_column in column_mapping.items():
            if csv_column not in reader.fieldnames:
                validation_errors.append(
                    f"Mapped column '{csv_column}' not found in CSV"
                )
        
        if validation_errors:
            return [], validation_errors
        
        # Parse and validate each row
        row_number = 1
        for row in reader:
            row_number += 1
            
            # Extract patient data using column mapping
            patient = {}
            row_errors = []
            
            for field, csv_column in column_mapping.items():
                value = row.get(csv_column, '').strip()
                
                # Validate required fields are not empty
                if field in REQUIRED_FIELDS and not value:
                    row_errors.append(f"Row {row_number}: {field} is required")
                    continue
                
                # Validate data types
                if field == 'dateOfBirth':
                    if not validate_date(value):
                        row_errors.append(
                            f"Row {row_number}: Invalid date format for {field}"
                        )
                
                patient[field] = value
            
            if row_errors:
                validation_errors.extend(row_errors)
                if len(validation_errors) >= 10:  # Limit error messages
                    validation_errors.append("... and more errors")
                    break
            else:
                patient['rowNumber'] = row_number
                patients.append(patient)
        
        # Validate file size (max 100 patients per batch)
        if len(patients) > 100:
            validation_errors.append(
                f"Batch size exceeds maximum of 100 patients (found {len(patients)})"
            )
            return [], validation_errors
        
        if len(patients) == 0 and not validation_errors:
            validation_errors.append("No valid patient records found in CSV")
        
        return patients, validation_errors
        
    except csv.Error as e:
        validation_errors.append(f"CSV parsing error: {str(e)}")
        return [], validation_errors
    except Exception as e:
        validation_errors.append(f"Unexpected error: {str(e)}")
        return [], validation_errors


def auto_detect_columns(fieldnames: List[str]) -> Dict[str, str]:
    """
    Auto-detect column mappings based on common variations
    """
    mapping = {}
    
    for required_field in REQUIRED_FIELDS:
        variations = COLUMN_MAPPINGS.get(required_field, [])
        
        # Check for exact match first
        if required_field in fieldnames:
            mapping[required_field] = required_field
            continue
        
        # Check for variations (case-insensitive)
        for fieldname in fieldnames:
            if fieldname.lower() in variations:
                mapping[required_field] = fieldname
                break
    
    return mapping


def validate_date(date_str: str) -> bool:
    """
    Validate date format (supports multiple formats)
    """
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d'
    ]
    
    for fmt in date_formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    
    return False


def invoke_eligibility_workers(batch_id: str, patients: List[Dict[str, Any]]) -> None:
    """
    Split patients into batches and invoke worker Lambdas in parallel
    """
    # Split into batches of BATCH_SIZE
    for i in range(0, len(patients), BATCH_SIZE):
        batch = patients[i:i + BATCH_SIZE]
        
        # Invoke worker Lambda asynchronously
        lambda_client.invoke(
            FunctionName=ELIGIBILITY_WORKER_LAMBDA,
            InvocationType='Event',
            Payload=json.dumps({
                'batchId': batch_id,
                'patients': batch
            })
        )


def update_batch_status(
    batch_id: str, 
    status: str, 
    errors: List[str] = None
) -> None:
    """
    Update batch job status
    """
    try:
        update_expr = 'SET #status = :status, updatedAt = :timestamp'
        expr_names = {'#status': 'status'}
        expr_values = {
            ':status': status,
            ':timestamp': datetime.utcnow().isoformat()
        }
        
        if errors:
            update_expr += ', validationErrors = :errors'
            expr_values[':errors'] = errors
        
        batch_jobs_table.update_item(
            Key={'batchId': batch_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
    except Exception as e:
        print(f"Error updating batch status: {str(e)}")
