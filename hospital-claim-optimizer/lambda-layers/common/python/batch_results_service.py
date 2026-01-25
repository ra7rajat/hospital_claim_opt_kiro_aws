"""
Batch Results Aggregation Service
Provides advanced aggregation, filtering, sorting, and export functionality
"""

import csv
import io
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Environment variables
BATCH_RESULTS_TABLE = 'BatchResults'
EXPORT_BUCKET = 'hospital-claim-batch-exports'

batch_results_table = dynamodb.Table(BATCH_RESULTS_TABLE)


class BatchResultsAggregator:
    """
    Aggregates and processes batch eligibility results
    """
    
    def __init__(self):
        self.results_table = batch_results_table
    
    def get_results(
        self,
        batch_id: str,
        status_filter: Optional[str] = None,
        sort_by: str = 'rowNumber',
        sort_order: str = 'asc'
    ) -> Dict[str, Any]:
        """
        Get batch results with filtering and sorting
        """
        try:
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
            
            response = self.results_table.query(**query_params)
            results = response.get('Items', [])
            
            # Sort results
            results = self._sort_results(results, sort_by, sort_order)
            
            # Calculate summary statistics
            summary = self._calculate_summary(results)
            
            return {
                'batchId': batch_id,
                'summary': summary,
                'results': results,
                'totalResults': len(results)
            }
            
        except Exception as e:
            raise Exception(f"Error getting batch results: {str(e)}")
    
    def _sort_results(
        self,
        results: List[Dict[str, Any]],
        sort_by: str,
        sort_order: str
    ) -> List[Dict[str, Any]]:
        """
        Sort results by specified field
        """
        reverse = (sort_order.lower() == 'desc')
        
        # Define sort key function
        def get_sort_key(item):
            value = item.get(sort_by)
            # Handle None values
            if value is None:
                return '' if isinstance(value, str) else 0
            return value
        
        try:
            return sorted(results, key=get_sort_key, reverse=reverse)
        except Exception as e:
            print(f"Error sorting results: {str(e)}")
            return results
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for batch results
        """
        total = len(results)
        
        if total == 0:
            return {
                'total': 0,
                'covered': 0,
                'notCovered': 0,
                'errors': 0,
                'preAuthRequired': 0,
                'coverageRate': 0,
                'errorRate': 0,
                'avgCoveragePercentage': 0,
                'totalCopay': 0,
                'totalDeductible': 0
            }
        
        covered = sum(1 for r in results if r.get('status') == 'COVERED')
        not_covered = sum(1 for r in results if r.get('status') == 'NOT_COVERED')
        errors = sum(1 for r in results if r.get('status') == 'ERROR')
        pre_auth_required = sum(1 for r in results if r.get('preAuthRequired', False))
        
        # Calculate financial metrics
        coverage_percentages = [
            r.get('coveragePercentage', 0) 
            for r in results 
            if r.get('status') != 'ERROR'
        ]
        avg_coverage = (
            sum(coverage_percentages) / len(coverage_percentages)
            if coverage_percentages else 0
        )
        
        total_copay = sum(r.get('copay', 0) for r in results)
        total_deductible = sum(r.get('deductible', 0) for r in results)
        
        return {
            'total': total,
            'covered': covered,
            'notCovered': not_covered,
            'errors': errors,
            'preAuthRequired': pre_auth_required,
            'coverageRate': round((covered / total) * 100, 2) if total > 0 else 0,
            'errorRate': round((errors / total) * 100, 2) if total > 0 else 0,
            'avgCoveragePercentage': round(avg_coverage, 2),
            'totalCopay': round(total_copay, 2),
            'totalDeductible': round(total_deductible, 2)
        }
    
    def export_to_csv(
        self,
        batch_id: str,
        status_filter: Optional[str] = None
    ) -> str:
        """
        Export batch results to CSV and upload to S3
        Returns S3 URL
        """
        try:
            # Get results
            results_data = self.get_results(batch_id, status_filter)
            results = results_data['results']
            
            if not results:
                raise Exception("No results to export")
            
            # Generate CSV
            csv_content = self._generate_csv(results)
            
            # Upload to S3
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"exports/{batch_id}/results_{timestamp}.csv"
            
            s3.put_object(
                Bucket=EXPORT_BUCKET,
                Key=s3_key,
                Body=csv_content.encode('utf-8'),
                ContentType='text/csv'
            )
            
            # Generate presigned URL (valid for 1 hour)
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': EXPORT_BUCKET, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            return url
            
        except Exception as e:
            raise Exception(f"Error exporting to CSV: {str(e)}")
    
    def _generate_csv(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate CSV content from results
        """
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            'rowNumber',
            'patientId',
            'status',
            'covered',
            'coveragePercentage',
            'preAuthRequired',
            'copay',
            'deductible',
            'outOfPocketMax',
            'error',
            'timestamp'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for result in results:
            # Flatten result for CSV
            row = {
                'rowNumber': result.get('rowNumber', ''),
                'patientId': result.get('patientId', ''),
                'status': result.get('status', ''),
                'covered': result.get('covered', False),
                'coveragePercentage': result.get('coveragePercentage', 0),
                'preAuthRequired': result.get('preAuthRequired', False),
                'copay': result.get('copay', 0),
                'deductible': result.get('deductible', 0),
                'outOfPocketMax': result.get('outOfPocketMax', 0),
                'error': result.get('error', ''),
                'timestamp': result.get('timestamp', '')
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_pdf(
        self,
        batch_id: str,
        status_filter: Optional[str] = None
    ) -> str:
        """
        Export batch results to PDF report
        Returns S3 URL
        
        Note: This is a placeholder. Full PDF generation would require
        a library like ReportLab or WeasyPrint
        """
        try:
            # Get results
            results_data = self.get_results(batch_id, status_filter)
            
            # Generate PDF content (simplified - would use proper PDF library)
            pdf_content = self._generate_pdf_report(results_data)
            
            # Upload to S3
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"exports/{batch_id}/report_{timestamp}.pdf"
            
            s3.put_object(
                Bucket=EXPORT_BUCKET,
                Key=s3_key,
                Body=pdf_content,
                ContentType='application/pdf'
            )
            
            # Generate presigned URL (valid for 1 hour)
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': EXPORT_BUCKET, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            return url
            
        except Exception as e:
            raise Exception(f"Error exporting to PDF: {str(e)}")
    
    def _generate_pdf_report(self, results_data: Dict[str, Any]) -> bytes:
        """
        Generate PDF report content
        
        Note: This is a placeholder implementation
        In production, use a proper PDF library like ReportLab
        """
        # Simplified text-based report
        report_lines = [
            f"Batch Eligibility Report",
            f"Batch ID: {results_data['batchId']}",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            "Summary Statistics:",
            f"  Total Records: {results_data['summary']['total']}",
            f"  Covered: {results_data['summary']['covered']}",
            f"  Not Covered: {results_data['summary']['notCovered']}",
            f"  Errors: {results_data['summary']['errors']}",
            f"  Pre-Auth Required: {results_data['summary']['preAuthRequired']}",
            f"  Coverage Rate: {results_data['summary']['coverageRate']}%",
            f"  Average Coverage: {results_data['summary']['avgCoveragePercentage']}%",
            "",
            "Detailed Results:",
            ""
        ]
        
        for result in results_data['results'][:50]:  # Limit to first 50
            report_lines.append(
                f"  Patient {result.get('patientId')}: "
                f"{result.get('status')} - "
                f"{result.get('coveragePercentage', 0)}% coverage"
            )
        
        report_text = "\n".join(report_lines)
        return report_text.encode('utf-8')
    
    def get_patients_requiring_preauth(self, batch_id: str) -> List[Dict[str, Any]]:
        """
        Get list of patients requiring pre-authorization
        """
        try:
            results_data = self.get_results(batch_id)
            
            preauth_patients = [
                {
                    'patientId': r.get('patientId'),
                    'rowNumber': r.get('rowNumber'),
                    'coveragePercentage': r.get('coveragePercentage'),
                    'copay': r.get('copay'),
                    'deductible': r.get('deductible')
                }
                for r in results_data['results']
                if r.get('preAuthRequired', False)
            ]
            
            return preauth_patients
            
        except Exception as e:
            raise Exception(f"Error getting pre-auth patients: {str(e)}")
