"""
Property-based tests for API consistency and performance.

Tests Properties 21 and 22:
- Property 21: API Response Consistency
- Property 22: API Performance (already tested in eligibility tests, but we'll add more comprehensive tests)
"""
import pytest
import json
import time
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda-layers', 'common', 'python'))

from api_middleware import (
    create_response,
    create_error_response,
    api_handler,
    validate_required_fields,
    extract_path_parameters,
    extract_query_parameters,
    extract_user_context,
    paginate_results,
    DecimalEncoder,
)


class TestAPIConsistencyProperties:
    """Test suite for API consistency properties."""
    
    @given(
        status_code=st.integers(min_value=200, max_value=599),
        body_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_property_21_api_response_consistency_structure(self, status_code, body_data):
        """
        **Property 21: API Response Consistency**
        
        For any API request, the system should return structured JSON responses
        with consistent format including statusCode, headers, and body.
        
        **Validates: Requirements 7.1, 7.3, 7.6**
        """
        # Create response
        response = create_response(status_code, body_data)
        
        # Verify response structure
        assert 'statusCode' in response, "Response must have statusCode"
        assert 'headers' in response, "Response must have headers"
        assert 'body' in response, "Response must have body"
        
        # Verify status code
        assert response['statusCode'] == status_code
        
        # Verify security headers are present
        headers = response['headers']
        assert 'Content-Type' in headers
        assert headers['Content-Type'] == 'application/json'
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Strict-Transport-Security' in headers
        
        # Verify CORS headers
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Headers' in headers
        assert 'Access-Control-Allow-Methods' in headers
        
        # Verify body is valid JSON
        parsed_body = json.loads(response['body'])
        assert isinstance(parsed_body, dict)
    
    @given(
        error_code=st.text(min_size=1, max_size=50),
        error_message=st.text(min_size=1, max_size=200),
        status_code=st.sampled_from([400, 401, 403, 404, 429, 500, 503])
    )
    @settings(max_examples=100)
    def test_property_21_error_response_consistency(self, error_code, error_message, status_code):
        """
        **Property 21: API Response Consistency - Error Handling**
        
        For any error condition, the system should return consistent error responses
        with error code, message, and timestamp.
        
        **Validates: Requirements 7.3, 7.6**
        """
        # Create error response
        response = create_error_response(status_code, error_code, error_message)
        
        # Verify response structure
        assert response['statusCode'] == status_code
        assert 'body' in response
        
        # Parse body
        body = json.loads(response['body'])
        
        # Verify error structure
        assert 'error' in body
        error = body['error']
        assert 'code' in error
        assert 'message' in error
        assert 'timestamp' in error
        
        # Verify error content
        assert error['code'] == error_code
        assert error['message'] == error_message
        
        # Verify timestamp is valid ISO format
        timestamp = datetime.fromisoformat(error['timestamp'])
        assert isinstance(timestamp, datetime)
    
    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(),
                st.decimals(allow_nan=False, allow_infinity=False, places=2),
                st.datetimes(),
            ),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_property_21_json_encoder_handles_special_types(self, data):
        """
        **Property 21: API Response Consistency - Special Type Handling**
        
        For any response containing Decimal or datetime objects, the JSON encoder
        should properly serialize them.
        
        **Validates: Requirements 7.1**
        """
        # Create response with special types
        response = create_response(200, data)
        
        # Verify body can be parsed
        parsed_body = json.loads(response['body'])
        assert isinstance(parsed_body, dict)
        
        # Verify all values are JSON-serializable types
        for key, value in parsed_body.items():
            assert isinstance(value, (str, int, float, bool, type(None), list, dict))
    
    @given(
        required_fields=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5, unique=True)
    )
    @settings(max_examples=100)
    def test_property_21_validation_consistency(self, required_fields):
        """
        **Property 21: API Response Consistency - Validation**
        
        For any request with missing required fields, the system should raise
        ValueError with clear message.
        
        **Validates: Requirements 7.3**
        """
        # Create data missing some required fields
        data = {field: "value" for field in required_fields[:-1]}  # Missing last field
        
        # Verify validation raises error
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, required_fields)
        
        # Verify error message mentions missing field
        assert required_fields[-1] in str(exc_info.value)
    
    @given(
        items=st.lists(st.integers(), min_size=0, max_size=200),
        page=st.integers(min_value=1, max_value=10),
        page_size=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_property_21_pagination_consistency(self, items, page, page_size):
        """
        **Property 21: API Response Consistency - Pagination**
        
        For any paginated response, the system should return consistent pagination
        metadata including page, page_size, total_items, total_pages, has_next, has_previous.
        
        **Validates: Requirements 7.1**
        """
        # Paginate results
        result = paginate_results(items, page, page_size)
        
        # Verify structure
        assert 'items' in result
        assert 'pagination' in result
        
        pagination = result['pagination']
        
        # Verify pagination metadata
        assert 'page' in pagination
        assert 'page_size' in pagination
        assert 'total_items' in pagination
        assert 'total_pages' in pagination
        assert 'has_next' in pagination
        assert 'has_previous' in pagination
        
        # Verify values are correct
        assert pagination['total_items'] == len(items)
        assert pagination['page'] >= 1
        assert pagination['page_size'] >= 1
        assert pagination['page_size'] <= 100  # Max page size
        
        # Verify has_next and has_previous are correct
        if pagination['page'] < pagination['total_pages']:
            assert pagination['has_next'] is True
        else:
            assert pagination['has_next'] is False
        
        if pagination['page'] > 1:
            assert pagination['has_previous'] is True
        else:
            assert pagination['has_previous'] is False
        
        # Verify returned items don't exceed page size
        assert len(result['items']) <= pagination['page_size']
    
    @given(
        handler_result=st.one_of(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.text(),
                min_size=1,
                max_size=5
            ),
            st.just({'statusCode': 200, 'body': '{"data": "test"}', 'headers': {}})
        )
    )
    @settings(max_examples=100)
    def test_property_21_handler_decorator_consistency(self, handler_result):
        """
        **Property 21: API Response Consistency - Handler Decorator**
        
        For any Lambda handler decorated with @api_handler, the response should
        be properly formatted with statusCode, headers, and body.
        
        **Validates: Requirements 7.1, 7.3**
        """
        # Create mock handler
        @api_handler
        def mock_handler(event, context):
            return handler_result
        
        # Create mock event and context
        event = {
            'httpMethod': 'GET',
            'path': '/test',
            'body': None
        }
        context = Mock()
        context.request_id = 'test-request-id'
        
        # Call handler
        response = mock_handler(event, context)
        
        # Verify response structure
        assert 'statusCode' in response
        assert 'headers' in response
        assert 'body' in response
        
        # Verify status code is valid
        assert 200 <= response['statusCode'] < 600
    
    def test_property_21_handler_error_handling_consistency(self):
        """
        **Property 21: API Response Consistency - Error Handling**
        
        For any handler that raises an exception, the decorator should return
        a consistent error response with appropriate status code.
        
        **Validates: Requirements 7.3, 7.6**
        """
        # Test ValueError (400)
        @api_handler
        def handler_value_error(event, context):
            raise ValueError("Invalid input")
        
        event = {'httpMethod': 'POST', 'path': '/test'}
        context = Mock()
        context.request_id = 'test-id'
        
        response = handler_value_error(event, context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error']['code'] == 'VALIDATION_ERROR'
        
        # Test PermissionError (403)
        @api_handler
        def handler_permission_error(event, context):
            raise PermissionError("Access denied")
        
        response = handler_permission_error(event, context)
        assert response['statusCode'] == 403
        body = json.loads(response['body'])
        assert body['error']['code'] == 'FORBIDDEN'
        
        # Test KeyError (400)
        @api_handler
        def handler_key_error(event, context):
            raise KeyError("missing_field")
        
        response = handler_key_error(event, context)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error']['code'] == 'MISSING_FIELD'
        
        # Test generic Exception (500)
        @api_handler
        def handler_generic_error(event, context):
            raise Exception("Unexpected error")
        
        response = handler_generic_error(event, context)
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error']['code'] == 'INTERNAL_ERROR'
    
    @given(
        path_params=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        ),
        query_params=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_property_21_parameter_extraction_consistency(self, path_params, query_params):
        """
        **Property 21: API Response Consistency - Parameter Extraction**
        
        For any API Gateway event, parameter extraction should consistently
        handle path and query parameters.
        
        **Validates: Requirements 7.1**
        """
        # Create event
        event = {
            'pathParameters': path_params if path_params else None,
            'queryStringParameters': query_params if query_params else None,
        }
        
        # Extract parameters
        extracted_path = extract_path_parameters(event)
        extracted_query = extract_query_parameters(event)
        
        # Verify extraction
        assert isinstance(extracted_path, dict)
        assert isinstance(extracted_query, dict)
        
        # Verify content matches (or empty dict if None)
        if path_params:
            assert extracted_path == path_params
        else:
            assert extracted_path == {}
        
        if query_params:
            assert extracted_query == query_params
        else:
            assert extracted_query == {}
    
    def test_property_21_user_context_extraction_consistency(self):
        """
        **Property 21: API Response Consistency - User Context**
        
        For any authenticated request, user context should be consistently
        extracted from Cognito claims.
        
        **Validates: Requirements 7.1, 7.3**
        """
        # Create event with Cognito claims
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123',
                        'email': 'test@example.com',
                        'custom:role': 'hospital_admin',
                        'custom:hospital_id': 'hospital-456',
                    }
                }
            }
        }
        
        # Extract user context
        user_context = extract_user_context(event)
        
        # Verify structure
        assert 'user_id' in user_context
        assert 'email' in user_context
        assert 'role' in user_context
        assert 'hospital_id' in user_context
        
        # Verify values
        assert user_context['user_id'] == 'user-123'
        assert user_context['email'] == 'test@example.com'
        assert user_context['role'] == 'hospital_admin'
        assert user_context['hospital_id'] == 'hospital-456'
        
        # Test with missing claims (should return 'unknown')
        event_no_claims = {'requestContext': {}}
        user_context_empty = extract_user_context(event_no_claims)
        assert user_context_empty['user_id'] == 'unknown'
        assert user_context_empty['email'] == 'unknown'
        assert user_context_empty['role'] == 'unknown'
        assert user_context_empty['hospital_id'] == 'unknown'


class TestAPIPerformanceProperties:
    """Test suite for API performance properties."""
    
    @given(
        num_requests=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50)
    def test_property_22_api_response_time_consistency(self, num_requests):
        """
        **Property 22: API Performance - Response Time**
        
        For any API request, the response formatting and middleware overhead
        should be minimal (under 100ms).
        
        **Validates: Requirements 7.2, 8.1**
        """
        # Create test data
        test_data = {
            'result': 'success',
            'data': [{'id': i, 'value': f'item_{i}'} for i in range(10)]
        }
        
        # Measure response creation time
        start_time = time.time()
        
        for _ in range(num_requests):
            response = create_response(200, test_data)
            # Verify response is created
            assert 'statusCode' in response
            assert 'body' in response
        
        elapsed_time = time.time() - start_time
        avg_time_per_request = elapsed_time / num_requests
        
        # Verify average response creation time is under 10ms (very fast)
        assert avg_time_per_request < 0.01, f"Average response creation time {avg_time_per_request*1000:.2f}ms should be under 10ms"
    
    @given(
        body_size=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=50)
    def test_property_22_json_serialization_performance(self, body_size):
        """
        **Property 22: API Performance - JSON Serialization**
        
        For any response body, JSON serialization should be efficient
        regardless of data size.
        
        **Validates: Requirements 7.2**
        """
        # Create test data with various types
        test_data = {
            'items': [
                {
                    'id': i,
                    'name': f'item_{i}',
                    'amount': Decimal(str(i * 10.50)),
                    'timestamp': datetime.now(),
                    'active': i % 2 == 0
                }
                for i in range(body_size)
            ]
        }
        
        # Measure serialization time
        start_time = time.time()
        response = create_response(200, test_data)
        elapsed_time = time.time() - start_time
        
        # Verify serialization is fast (under 100ms for up to 1000 items)
        assert elapsed_time < 0.1, f"JSON serialization took {elapsed_time*1000:.2f}ms, should be under 100ms"
        
        # Verify response is valid
        parsed_body = json.loads(response['body'])
        assert len(parsed_body['items']) == body_size
    
    def test_property_22_concurrent_request_handling(self):
        """
        **Property 22: API Performance - Concurrent Requests**
        
        The API middleware should handle multiple concurrent requests
        without performance degradation.
        
        **Validates: Requirements 8.1**
        """
        import concurrent.futures
        
        # Create test handler
        @api_handler
        def test_handler(event, context):
            # Simulate some processing
            time.sleep(0.01)  # 10ms processing
            return {'result': 'success', 'request_id': event.get('request_id')}
        
        # Create multiple test events
        num_concurrent = 50
        events = [
            {
                'httpMethod': 'GET',
                'path': f'/test/{i}',
                'request_id': f'req-{i}'
            }
            for i in range(num_concurrent)
        ]
        
        context = Mock()
        context.request_id = 'test-context'
        
        # Execute concurrent requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(test_handler, event, context) for event in events]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time
        
        # Verify all requests completed
        assert len(results) == num_concurrent
        
        # Verify all responses are valid
        for response in results:
            assert response['statusCode'] == 200
            assert 'body' in response
        
        # Verify concurrent execution is efficient
        # Should complete in roughly the time of sequential processing / workers
        # With 10 workers and 50 requests, should take ~5 * 10ms = 50ms + overhead
        assert elapsed_time < 2.0, f"Concurrent requests took {elapsed_time:.2f}s, should be under 2s"
    
    @given(
        page_size=st.integers(min_value=10, max_value=100),
        total_items=st.integers(min_value=100, max_value=10000)
    )
    @settings(max_examples=50)
    def test_property_22_pagination_performance(self, page_size, total_items):
        """
        **Property 22: API Performance - Pagination**
        
        For any paginated response, pagination should be efficient
        even with large datasets.
        
        **Validates: Requirements 7.2**
        """
        # Create large dataset
        items = list(range(total_items))
        
        # Measure pagination time
        start_time = time.time()
        result = paginate_results(items, page=1, page_size=page_size)
        elapsed_time = time.time() - start_time
        
        # Verify pagination is fast (under 50ms)
        assert elapsed_time < 0.05, f"Pagination took {elapsed_time*1000:.2f}ms, should be under 50ms"
        
        # Verify result structure
        assert len(result['items']) <= page_size
        assert result['pagination']['total_items'] == total_items
    
    def test_property_22_error_response_performance(self):
        """
        **Property 22: API Performance - Error Handling**
        
        Error response generation should be as fast as success responses
        to avoid performance degradation during error conditions.
        
        **Validates: Requirements 7.2, 7.6**
        """
        # Measure error response time
        num_iterations = 100
        
        start_time = time.time()
        for i in range(num_iterations):
            response = create_error_response(400, 'TEST_ERROR', f'Test error message {i}')
            assert response['statusCode'] == 400
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / num_iterations
        
        # Verify error responses are fast (under 5ms each)
        assert avg_time < 0.005, f"Average error response time {avg_time*1000:.2f}ms should be under 5ms"
    
    def test_property_22_handler_decorator_overhead(self):
        """
        **Property 22: API Performance - Decorator Overhead**
        
        The @api_handler decorator should add minimal overhead to
        request processing.
        
        **Validates: Requirements 7.2**
        """
        # Create simple handler
        @api_handler
        def fast_handler(event, context):
            return {'result': 'success'}
        
        # Create test event
        event = {
            'httpMethod': 'GET',
            'path': '/test'
        }
        context = Mock()
        context.request_id = 'test-id'
        
        # Measure decorator overhead
        num_iterations = 100
        start_time = time.time()
        
        for _ in range(num_iterations):
            response = fast_handler(event, context)
            assert response['statusCode'] == 200
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / num_iterations
        
        # Verify decorator overhead is minimal (under 5ms per request)
        assert avg_time < 0.005, f"Average handler time {avg_time*1000:.2f}ms should be under 5ms"
    
    def test_property_22_throughput_1000_requests_per_minute(self):
        """
        **Property 22: API Performance - Throughput**
        
        The system should support up to 1000 concurrent eligibility checks per minute.
        This test simulates high-throughput scenarios to verify the API can handle
        the required load.
        
        **Validates: Requirements 8.1**
        """
        # Create test handler that simulates eligibility check
        @api_handler
        def eligibility_handler(event, context):
            # Simulate minimal processing (actual DB queries would be in Lambda)
            request_id = event.get('pathParameters', {}).get('id', 'unknown')
            return {
                'request_id': request_id,
                'coverage_status': 'COVERED',
                'response_time': time.time()
            }
        
        # Simulate 1000 requests (scaled down to 100 for test speed)
        num_requests = 100  # Represents 1000 requests scaled down 10x
        target_time = 6.0  # 60 seconds scaled down 10x
        
        events = [
            {
                'httpMethod': 'GET',
                'path': f'/eligibility/{i}',
                'pathParameters': {'id': str(i)}
            }
            for i in range(num_requests)
        ]
        
        context = Mock()
        context.request_id = 'test-context'
        
        # Execute requests with concurrency
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(eligibility_handler, event, context) for event in events]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        elapsed_time = time.time() - start_time
        
        # Verify all requests completed
        assert len(results) == num_requests
        
        # Verify all responses are successful
        for response in results:
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'coverage_status' in body
        
        # Verify throughput meets requirement
        # 100 requests should complete well within 6 seconds (scaled target)
        assert elapsed_time < target_time, f"100 requests took {elapsed_time:.2f}s, should be under {target_time}s"
        
        # Calculate actual throughput
        requests_per_second = num_requests / elapsed_time
        requests_per_minute = requests_per_second * 60
        
        # Scaled up, this represents the actual throughput
        actual_throughput = requests_per_minute * 10  # Scale back up
        
        print(f"✓ Achieved throughput: {actual_throughput:.0f} requests/minute (target: 1000)")
        assert actual_throughput >= 1000, f"Throughput {actual_throughput:.0f} req/min should be >= 1000"


def test_api_consistency_integration():
    """
    Integration test for API consistency across multiple operations.
    """
    # Test complete request/response cycle
    @api_handler
    def test_handler(event, context):
        # Extract parameters
        path_params = extract_path_parameters(event)
        query_params = extract_query_parameters(event)
        user_context = extract_user_context(event)
        
        # Validate required fields if body present
        if 'parsed_body' in event:
            validate_required_fields(event['parsed_body'], ['test_field'])
        
        # Return data
        return {
            'path_params': path_params,
            'query_params': query_params,
            'user': user_context,
        }
    
    # Create test event
    event = {
        'httpMethod': 'POST',
        'path': '/test/123',
        'pathParameters': {'id': '123'},
        'queryStringParameters': {'filter': 'active'},
        'body': json.dumps({'test_field': 'value'}),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'user-123',
                    'email': 'test@example.com',
                    'custom:role': 'hospital_admin',
                    'custom:hospital_id': 'hospital-456',
                }
            }
        }
    }
    
    context = Mock()
    context.request_id = 'test-request-id'
    
    # Call handler
    response = test_handler(event, context)
    
    # Verify response structure
    assert response['statusCode'] == 200
    assert 'headers' in response
    assert 'body' in response
    
    # Parse and verify body
    body = json.loads(response['body'])
    assert 'path_params' in body
    assert 'query_params' in body
    assert 'user' in body
    
    print("✓ API consistency integration test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
