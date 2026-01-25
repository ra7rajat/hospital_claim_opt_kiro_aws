"""
Common utilities for Hospital Claim Optimizer Lambda functions
"""
import json
import boto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class DynamoDBClient:
    """DynamoDB client wrapper with common operations"""
    
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def put_item(self, item: Dict[str, Any]) -> bool:
        """Put item into DynamoDB table"""
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            logger.error(f"Error putting item to DynamoDB: {str(e)}")
            return False
    
    def get_item(self, pk: str, sk: str) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB table"""
        try:
            response = self.table.get_item(
                Key={'PK': pk, 'SK': sk}
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error getting item from DynamoDB: {str(e)}")
            return None
    
    def query_items(self, pk: str, sk_prefix: Optional[str] = None) -> list:
        """Query items from DynamoDB table"""
        try:
            if sk_prefix:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                    ExpressionAttributeValues={
                        ':pk': pk,
                        ':sk_prefix': sk_prefix
                    }
                )
            else:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={':pk': pk}
                )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error querying items from DynamoDB: {str(e)}")
            return []

class S3Client:
    """S3 client wrapper with common operations"""
    
    def __init__(self):
        self.s3 = boto3.client('s3')
    
    def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for S3 object upload"""
        try:
            response = self.s3.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
    
    def get_object(self, bucket: str, key: str) -> Optional[bytes]:
        """Get object from S3 bucket"""
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting object from S3: {str(e)}")
            return None

class TextractClient:
    """Textract client wrapper"""
    
    def __init__(self):
        self.textract = boto3.client('textract')
    
    def analyze_document(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """Analyze document using Textract"""
        try:
            response = self.textract.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            return response
        except Exception as e:
            logger.error(f"Error analyzing document with Textract: {str(e)}")
            return None

class BedrockClient:
    """Bedrock client wrapper"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
    
    def invoke_claude(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Invoke Claude 3.5 Sonnet model"""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        except Exception as e:
            logger.error(f"Error invoking Bedrock: {str(e)}")
            return None

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key',
        },
        'body': json.dumps(body, default=str)
    }

def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()

def extract_text_from_textract(textract_response: Dict[str, Any]) -> str:
    """Extract plain text from Textract response"""
    text_blocks = []
    
    for block in textract_response.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            text_blocks.append(block.get('Text', ''))
    
    return '\n'.join(text_blocks)

def extract_tables_from_textract(textract_response: Dict[str, Any]) -> list:
    """Extract table data from Textract response"""
    tables = []
    
    # This is a simplified extraction - in production, you'd want more robust table parsing
    for block in textract_response.get('Blocks', []):
        if block['BlockType'] == 'TABLE':
            # Extract table structure and cells
            # Implementation would be more complex for full table parsing
            pass
    
    return tables