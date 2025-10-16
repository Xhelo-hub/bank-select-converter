#!/usr/bin/env python3
"""
Performance and load testing for Bank Statement Converter API

This script tests the API performance under various load conditions
and measures response times, throughput, and error rates.
"""

import asyncio
import aiohttp
import time
import statistics
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
import os


class LoadTester:
    """Load testing class for the API"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.results = {
            'requests': 0,
            'success': 0,
            'errors': 0,
            'response_times': [],
            'error_types': {},
            'start_time': None,
            'end_time': None
        }
        self.lock = threading.Lock()
    
    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def record_request(self, success=True, response_time=0, error_type=None):
        """Record request result"""
        with self.lock:
            self.results['requests'] += 1
            if success:
                self.results['success'] += 1
            else:
                self.results['errors'] += 1
                if error_type:
                    self.results['error_types'][error_type] = \
                        self.results['error_types'].get(error_type, 0) + 1
            
            if response_time > 0:
                self.results['response_times'].append(response_time)
    
    async def test_api_info(self):
        """Test /api/info endpoint"""
        start_time = time.time()
        
        try:
            async with self.session.get(f'{self.base_url}/api/info') as response:
                await response.text()
                response_time = time.time() - start_time
                
                if response.status == 200:
                    self.record_request(True, response_time)
                else:
                    self.record_request(False, response_time, f'HTTP_{response.status}')
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.record_request(False, response_time, type(e).__name__)
    
    async def test_health_check(self):
        """Test /health endpoint"""
        start_time = time.time()
        
        try:
            async with self.session.get(f'{self.base_url}/health') as response:
                await response.text()
                response_time = time.time() - start_time
                
                if response.status == 200:
                    self.record_request(True, response_time)
                else:
                    self.record_request(False, response_time, f'HTTP_{response.status}')
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.record_request(False, response_time, type(e).__name__)
    
    async def test_file_upload(self, file_data, filename='test.pdf'):
        """Test file upload endpoint"""
        start_time = time.time()
        
        try:
            form_data = aiohttp.FormData()
            form_data.add_field('file', file_data, filename=filename)
            
            async with self.session.post(f'{self.base_url}/api/upload', 
                                       data=form_data) as response:
                await response.text()
                response_time = time.time() - start_time
                
                if response.status in [200, 400]:  # 400 might be expected for test files
                    self.record_request(True, response_time)
                else:
                    self.record_request(False, response_time, f'HTTP_{response.status}')
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.record_request(False, response_time, type(e).__name__)
    
    async def run_concurrent_requests(self, test_func, concurrent_users=10, 
                                    requests_per_user=10, *args, **kwargs):
        """Run concurrent requests"""
        await self.create_session()
        
        async def user_session():
            for _ in range(requests_per_user):
                await test_func(*args, **kwargs)
                await asyncio.sleep(0.1)  # Small delay between requests
        
        # Create tasks for concurrent users
        tasks = [user_session() for _ in range(concurrent_users)]
        
        self.results['start_time'] = time.time()
        await asyncio.gather(*tasks)
        self.results['end_time'] = time.time()
        
        await self.close_session()
    
    def generate_sample_pdf(self):
        """Generate sample PDF content for testing"""
        return b"""%%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(BKT Bank Statement Test File) Tj
100 680 Td
(Date: 01/12/2023 Amount: 1000.00) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000195 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
340
%%EOF"""
    
    def print_results(self):
        """Print test results"""
        if not self.results['response_times']:
            print("No successful requests completed")
            return
        
        duration = self.results['end_time'] - self.results['start_time']
        
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        
        print(f"Test Duration: {duration:.2f} seconds")
        print(f"Total Requests: {self.results['requests']}")
        print(f"Successful Requests: {self.results['success']}")
        print(f"Failed Requests: {self.results['errors']}")
        print(f"Success Rate: {(self.results['success']/self.results['requests']*100):.2f}%")
        
        if self.results['response_times']:
            print(f"Requests per Second: {self.results['requests']/duration:.2f}")
            print(f"Average Response Time: {statistics.mean(self.results['response_times']):.3f}s")
            print(f"Median Response Time: {statistics.median(self.results['response_times']):.3f}s")
            print(f"Min Response Time: {min(self.results['response_times']):.3f}s")
            print(f"Max Response Time: {max(self.results['response_times']):.3f}s")
            
            if len(self.results['response_times']) > 1:
                print(f"Std Deviation: {statistics.stdev(self.results['response_times']):.3f}s")
        
        if self.results['error_types']:
            print(f"\nError Breakdown:")
            for error_type, count in self.results['error_types'].items():
                print(f"  {error_type}: {count}")
        
        print("="*60)


async def run_api_info_test(base_url, concurrent_users=10, requests_per_user=20):
    """Run API info endpoint test"""
    print(f"Testing /api/info endpoint with {concurrent_users} concurrent users, "
          f"{requests_per_user} requests per user...")
    
    tester = LoadTester(base_url)
    await tester.run_concurrent_requests(
        tester.test_api_info, 
        concurrent_users=concurrent_users,
        requests_per_user=requests_per_user
    )
    
    print(f"\n--- API Info Test Results ---")
    tester.print_results()
    return tester.results


async def run_health_check_test(base_url, concurrent_users=20, requests_per_user=30):
    """Run health check endpoint test"""
    print(f"Testing /health endpoint with {concurrent_users} concurrent users, "
          f"{requests_per_user} requests per user...")
    
    tester = LoadTester(base_url)
    await tester.run_concurrent_requests(
        tester.test_health_check,
        concurrent_users=concurrent_users, 
        requests_per_user=requests_per_user
    )
    
    print(f"\n--- Health Check Test Results ---")
    tester.print_results()
    return tester.results


async def run_upload_test(base_url, concurrent_users=5, requests_per_user=5):
    """Run file upload test"""
    print(f"Testing /api/upload endpoint with {concurrent_users} concurrent users, "
          f"{requests_per_user} requests per user...")
    
    tester = LoadTester(base_url)
    sample_pdf = tester.generate_sample_pdf()
    
    await tester.run_concurrent_requests(
        tester.test_file_upload,
        concurrent_users=concurrent_users,
        requests_per_user=requests_per_user,
        file_data=sample_pdf
    )
    
    print(f"\n--- Upload Test Results ---")
    tester.print_results()
    return tester.results


async def run_mixed_load_test(base_url, duration_seconds=60):
    """Run mixed load test for specified duration"""
    print(f"Running mixed load test for {duration_seconds} seconds...")
    
    tester = LoadTester(base_url)
    await tester.create_session()
    
    start_time = time.time()
    tester.results['start_time'] = start_time
    
    # Create different types of concurrent tasks
    async def info_worker():
        while time.time() - start_time < duration_seconds:
            await tester.test_api_info()
            await asyncio.sleep(0.5)
    
    async def health_worker():
        while time.time() - start_time < duration_seconds:
            await tester.test_health_check()
            await asyncio.sleep(0.2)
    
    async def upload_worker():
        sample_pdf = tester.generate_sample_pdf()
        while time.time() - start_time < duration_seconds:
            await tester.test_file_upload(sample_pdf)
            await asyncio.sleep(2)  # Slower for uploads
    
    # Run different workers concurrently
    tasks = [
        info_worker(),
        info_worker(),
        health_worker(),
        health_worker(),
        health_worker(),
        upload_worker()
    ]
    
    await asyncio.gather(*tasks)
    
    tester.results['end_time'] = time.time()
    await tester.close_session()
    
    print(f"\n--- Mixed Load Test Results ---")
    tester.print_results()
    return tester.results


def save_results_to_file(results, filename):
    """Save test results to JSON file"""
    # Convert results to JSON-serializable format
    json_results = {}
    for key, value in results.items():
        if key == 'response_times' and value:
            json_results[key] = {
                'count': len(value),
                'mean': statistics.mean(value),
                'median': statistics.median(value),
                'min': min(value),
                'max': max(value),
                'std_dev': statistics.stdev(value) if len(value) > 1 else 0
            }
        else:
            json_results[key] = value
    
    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"Results saved to {filename}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Load test the Bank Statement Converter API')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the API (default: http://localhost:5000)')
    parser.add_argument('--test', choices=['info', 'health', 'upload', 'mixed', 'all'],
                       default='all', help='Test type to run (default: all)')
    parser.add_argument('--concurrent-users', type=int, default=10,
                       help='Number of concurrent users (default: 10)')
    parser.add_argument('--requests-per-user', type=int, default=20,
                       help='Number of requests per user (default: 20)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration for mixed test in seconds (default: 60)')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    print(f"Starting load tests for {args.url}")
    print(f"Target API should be running and accessible")
    
    all_results = {}
    
    try:
        if args.test in ['info', 'all']:
            results = await run_api_info_test(
                args.url, args.concurrent_users, args.requests_per_user
            )
            all_results['api_info'] = results
        
        if args.test in ['health', 'all']:
            results = await run_health_check_test(
                args.url, args.concurrent_users, args.requests_per_user
            )
            all_results['health_check'] = results
        
        if args.test in ['upload', 'all']:
            # Use fewer concurrent users for upload tests
            upload_users = min(args.concurrent_users, 5)
            upload_requests = min(args.requests_per_user, 5)
            results = await run_upload_test(args.url, upload_users, upload_requests)
            all_results['upload'] = results
        
        if args.test in ['mixed', 'all']:
            results = await run_mixed_load_test(args.url, args.duration)
            all_results['mixed_load'] = results
        
        if args.output:
            save_results_to_file(all_results, args.output)
    
    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure the API is running and accessible at the specified URL")


if __name__ == '__main__':
    asyncio.run(main())