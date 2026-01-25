"""
Performance monitoring and metrics collection service.
Tracks system performance and publishes custom CloudWatch metrics.
"""

import time
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import json

cloudwatch = boto3.client('cloudwatch')


class PerformanceMonitor:
    """Monitors and tracks performance metrics for the system."""
    
    def __init__(self, namespace: str = 'HospitalClaimOptimizer'):
        self.namespace = namespace
        self.metrics_buffer = []
        
    def track_execution_time(self, operation_name: str):
        """
        Decorator to track execution time of functions.
        
        Usage:
            @performance_monitor.track_execution_time('policy_upload')
            def upload_policy(...):
                ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    success = False
                    raise
                finally:
                    duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                    self.record_metric(
                        metric_name=f'{operation_name}_Duration',
                        value=duration,
                        unit='Milliseconds',
                        dimensions={'Operation': operation_name, 'Success': str(success)}
                    )
            return wrapper
        return decorator
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'None',
        dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Record a custom metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Count, Milliseconds, Percent, etc.)
            dimensions: Optional dimensions for the metric
        """
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow(),
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        self.metrics_buffer.append(metric_data)
        
        # Flush buffer if it gets too large
        if len(self.metrics_buffer) >= 20:
            self.flush_metrics()
    
    def flush_metrics(self):
        """Flush buffered metrics to CloudWatch."""
        if not self.metrics_buffer:
            return
            
        try:
            cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=self.metrics_buffer
            )
            self.metrics_buffer = []
        except Exception as e:
            print(f"Error flushing metrics to CloudWatch: {e}")
    
    def record_csr(self, hospital_id: str, csr_value: float):
        """Record Claim Settlement Ratio metric."""
        self.record_metric(
            metric_name='ClaimSettlementRatio',
            value=csr_value,
            unit='Percent',
            dimensions={'HospitalId': hospital_id}
        )
    
    def record_processing_time(self, operation: str, duration_ms: float, success: bool = True):
        """Record processing time for an operation."""
        self.record_metric(
            metric_name='ProcessingTime',
            value=duration_ms,
            unit='Milliseconds',
            dimensions={
                'Operation': operation,
                'Success': str(success)
            }
        )
    
    def record_api_call(self, endpoint: str, status_code: int, duration_ms: float):
        """Record API call metrics."""
        self.record_metric(
            metric_name='APILatency',
            value=duration_ms,
            unit='Milliseconds',
            dimensions={
                'Endpoint': endpoint,
                'StatusCode': str(status_code)
            }
        )
        
        # Record success/failure
        self.record_metric(
            metric_name='APIRequests',
            value=1,
            unit='Count',
            dimensions={
                'Endpoint': endpoint,
                'Status': 'Success' if 200 <= status_code < 300 else 'Error'
            }
        )
    
    def record_concurrent_requests(self, count: int):
        """Record number of concurrent requests."""
        self.record_metric(
            metric_name='ConcurrentRequests',
            value=count,
            unit='Count'
        )
    
    def record_database_query(self, table_name: str, operation: str, duration_ms: float):
        """Record database query performance."""
        self.record_metric(
            metric_name='DatabaseQueryTime',
            value=duration_ms,
            unit='Milliseconds',
            dimensions={
                'Table': table_name,
                'Operation': operation
            }
        )
    
    def record_cache_hit(self, cache_name: str, hit: bool):
        """Record cache hit/miss."""
        self.record_metric(
            metric_name='CacheHitRate',
            value=1 if hit else 0,
            unit='Count',
            dimensions={
                'Cache': cache_name,
                'Result': 'Hit' if hit else 'Miss'
            }
        )
    
    def record_business_metric(self, metric_name: str, value: float, dimensions: Optional[Dict[str, str]] = None):
        """Record custom business metrics."""
        self.record_metric(
            metric_name=metric_name,
            value=value,
            unit='None',
            dimensions=dimensions
        )


class PerformanceContext:
    """Context manager for tracking operation performance."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str, dimensions: Optional[Dict[str, str]] = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.dimensions = dimensions or {}
        self.start_time = None
        self.success = False
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000
        self.success = exc_type is None
        
        self.monitor.record_metric(
            metric_name=f'{self.operation_name}_Duration',
            value=duration,
            unit='Milliseconds',
            dimensions={**self.dimensions, 'Success': str(self.success)}
        )
        
        self.monitor.flush_metrics()
        return False  # Don't suppress exceptions


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str, dimensions: Optional[Dict[str, str]] = None):
    """
    Decorator to monitor function performance.
    
    Usage:
        @monitor_performance('eligibility_check', {'service': 'eligibility'})
        def check_eligibility(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceContext(performance_monitor, operation_name, dimensions):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def track_api_performance(func):
    """
    Decorator specifically for API endpoint handlers.
    Tracks latency, success rate, and other API-specific metrics.
    """
    @wraps(func)
    def wrapper(event, context):
        start_time = time.time()
        endpoint = event.get('path', 'unknown')
        
        try:
            result = func(event, context)
            status_code = result.get('statusCode', 200)
            duration = (time.time() - start_time) * 1000
            
            performance_monitor.record_api_call(endpoint, status_code, duration)
            performance_monitor.flush_metrics()
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            performance_monitor.record_api_call(endpoint, 500, duration)
            performance_monitor.flush_metrics()
            raise
    
    return wrapper
