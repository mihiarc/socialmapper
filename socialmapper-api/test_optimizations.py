#!/usr/bin/env python3
"""Test script for demonstrating backend optimizations."""

import asyncio
import json
import time
from typing import List, Dict, Any
import aiohttp
import websockets
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import print as rprint

console = Console()

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/api/v1"


async def test_websocket_progress():
    """Test WebSocket real-time progress tracking."""
    console.print("\n[bold cyan]Testing WebSocket Progress Tracking[/bold cyan]")
    
    async with aiohttp.ClientSession() as session:
        # Submit a job
        payload = {
            "location": "Portland, OR",
            "poi_type": "amenity",
            "poi_name": "library",
            "travel_time": 15,
            "geographic_level": "tract",
            "census_variables": ["B01003_001E"]
        }
        
        headers = {
            "X-Session-Id": "test-session-123",
            "X-Demo-Mode": "true"
        }
        
        async with session.post(
            f"{API_BASE_URL}/analysis/location",
            json=payload,
            headers=headers
        ) as response:
            result = await response.json()
            job_id = result["job_id"]
            console.print(f"Created job: [green]{job_id}[/green]")
    
    # Connect to WebSocket for progress updates
    uri = f"{WS_BASE_URL}/ws/jobs/{job_id}"
    console.print(f"Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            console.print("[green]WebSocket connected![/green]")
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                console.print(f"[yellow]Event:[/yellow] {data['type']}")
                console.print(f"[dim]Data:[/dim] {json.dumps(data['data'], indent=2)}")
                
                if data['type'] in ['completed', 'failed']:
                    break
                    
    except Exception as e:
        console.print(f"[red]WebSocket error:[/red] {e}")


async def test_concurrent_jobs():
    """Test concurrent job processing with priorities."""
    console.print("\n[bold cyan]Testing Concurrent Jobs with Prioritization[/bold cyan]")
    
    jobs = []
    
    async with aiohttp.ClientSession() as session:
        # Submit demo jobs (high priority)
        for i in range(3):
            payload = {
                "location": f"Portland, OR",
                "poi_type": "amenity",
                "poi_name": f"test_{i}",
                "travel_time": 15,
                "geographic_level": "tract",
                "census_variables": ["B01003_001E"]
            }
            
            headers = {
                "X-Session-Id": f"demo-session-{i}",
                "X-Demo-Mode": "true"
            }
            
            async with session.post(
                f"{API_BASE_URL}/analysis/location",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                jobs.append({
                    "id": result["job_id"],
                    "type": "demo",
                    "start_time": time.time()
                })
                console.print(f"Submitted demo job {i+1}: [green]{result['job_id']}[/green]")
        
        # Submit normal jobs
        for i in range(5):
            payload = {
                "location": f"Seattle, WA",
                "poi_type": "shop",
                "poi_name": f"store_{i}",
                "travel_time": 20,
                "geographic_level": "tract",
                "census_variables": ["B01003_001E", "B25001_001E"]
            }
            
            headers = {
                "X-Session-Id": f"normal-session-{i}",
                "X-Priority": "normal"
            }
            
            async with session.post(
                f"{API_BASE_URL}/analysis/location",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                jobs.append({
                    "id": result["job_id"],
                    "type": "normal",
                    "start_time": time.time()
                })
                console.print(f"Submitted normal job {i+1}: [yellow]{result['job_id']}[/yellow]")
        
        # Monitor job completion
        console.print("\n[bold]Monitoring job completion order (demo jobs should complete first):[/bold]")
        
        completed = []
        while len(completed) < len(jobs):
            await asyncio.sleep(1)
            
            for job in jobs:
                if job["id"] in [c["id"] for c in completed]:
                    continue
                
                async with session.get(f"{API_BASE_URL}/analysis/{job['id']}/status") as response:
                    status = await response.json()
                    
                    if status["status"] == "completed":
                        completion_time = time.time() - job["start_time"]
                        completed.append({
                            **job,
                            "completion_time": completion_time
                        })
                        
                        color = "green" if job["type"] == "demo" else "yellow"
                        console.print(
                            f"[{color}]Completed:[/{color}] {job['type'].upper()} job "
                            f"{job['id'][:8]}... in {completion_time:.2f}s"
                        )
    
    # Display results table
    table = Table(title="Job Completion Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Job ID", style="magenta")
    table.add_column("Completion Time", style="green")
    
    for job in sorted(completed, key=lambda x: x["completion_time"]):
        table.add_row(
            job["type"].upper(),
            job["id"][:12] + "...",
            f"{job['completion_time']:.2f}s"
        )
    
    console.print(table)


async def test_cache_performance():
    """Test cache performance improvements."""
    console.print("\n[bold cyan]Testing Cache Performance[/bold cyan]")
    
    # Test location for cache testing
    test_payload = {
        "location": "Portland, OR",
        "poi_type": "amenity",
        "poi_name": "library",
        "travel_time": 15,
        "geographic_level": "tract",
        "census_variables": ["B01003_001E"]
    }
    
    async with aiohttp.ClientSession() as session:
        # First request (cache miss)
        console.print("\n[yellow]First request (cache miss):[/yellow]")
        start_time = time.time()
        
        async with session.post(
            f"{API_BASE_URL}/analysis/location",
            json=test_payload
        ) as response:
            result = await response.json()
            job_id_1 = result["job_id"]
        
        # Wait for completion
        while True:
            await asyncio.sleep(0.5)
            async with session.get(f"{API_BASE_URL}/analysis/{job_id_1}/status") as response:
                status = await response.json()
                if status["status"] in ["completed", "failed"]:
                    break
        
        first_time = time.time() - start_time
        console.print(f"First request completed in: [red]{first_time:.2f}s[/red]")
        
        # Second request (cache hit)
        console.print("\n[yellow]Second request (cache hit):[/yellow]")
        start_time = time.time()
        
        async with session.post(
            f"{API_BASE_URL}/analysis/location",
            json=test_payload
        ) as response:
            result = await response.json()
            job_id_2 = result["job_id"]
        
        # Wait for completion
        while True:
            await asyncio.sleep(0.5)
            async with session.get(f"{API_BASE_URL}/analysis/{job_id_2}/status") as response:
                status = await response.json()
                if status["status"] in ["completed", "failed"]:
                    break
        
        second_time = time.time() - start_time
        console.print(f"Second request completed in: [green]{second_time:.2f}s[/green]")
        
        # Calculate improvement
        improvement = ((first_time - second_time) / first_time) * 100
        console.print(f"\n[bold green]Cache improved response time by {improvement:.1f}%[/bold green]")


async def test_performance_metrics():
    """Test performance metrics endpoint."""
    console.print("\n[bold cyan]Testing Performance Metrics[/bold cyan]")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/analysis/performance") as response:
            metrics = await response.json()
            
            console.print("\n[bold]System Performance Metrics:[/bold]")
            console.print(json.dumps(metrics, indent=2))


async def load_test(num_requests: int = 50):
    """Perform load testing to measure response times."""
    console.print(f"\n[bold cyan]Load Testing with {num_requests} Concurrent Requests[/bold cyan]")
    
    async def make_request(session: aiohttp.ClientSession, index: int) -> Dict[str, Any]:
        """Make a single analysis request."""
        payload = {
            "location": ["Portland, OR", "Seattle, WA", "San Francisco, CA"][index % 3],
            "poi_type": ["amenity", "shop", "leisure"][index % 3],
            "poi_name": f"test_{index}",
            "travel_time": 15 + (index % 3) * 5,
            "geographic_level": "tract",
            "census_variables": ["B01003_001E"]
        }
        
        headers = {
            "X-Session-Id": f"load-test-{index % 10}",
            "X-Demo-Mode": "true" if index % 5 == 0 else "false"
        }
        
        start_time = time.time()
        
        try:
            async with session.post(
                f"{API_BASE_URL}/analysis/location",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                result = await response.json()
                response_time = time.time() - start_time
                
                return {
                    "success": True,
                    "status_code": response.status,
                    "response_time": response_time,
                    "job_id": result.get("job_id")
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for concurrent requests
        tasks = [make_request(session, i) for i in range(num_requests)]
        
        # Execute with progress bar
        console.print("\n[yellow]Sending requests...[/yellow]")
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    response_times = [r["response_time"] for r in successful]
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
    else:
        avg_time = min_time = max_time = p50 = p95 = p99 = 0
    
    # Display results
    table = Table(title="Load Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Requests", str(num_requests))
    table.add_row("Successful", f"{len(successful)} ({len(successful)/num_requests*100:.1f}%)")
    table.add_row("Failed", f"{len(failed)} ({len(failed)/num_requests*100:.1f}%)")
    table.add_row("Avg Response Time", f"{avg_time:.3f}s")
    table.add_row("Min Response Time", f"{min_time:.3f}s")
    table.add_row("Max Response Time", f"{max_time:.3f}s")
    table.add_row("P50 (Median)", f"{p50:.3f}s")
    table.add_row("P95", f"{p95:.3f}s")
    table.add_row("P99", f"{p99:.3f}s")
    
    console.print(table)
    
    # Check if we meet the <3 second requirement
    if p95 < 3.0:
        console.print("\n[bold green]✓ Meeting <3 second response time target (P95)[/bold green]")
    else:
        console.print(f"\n[bold red]✗ Not meeting <3 second target. P95: {p95:.2f}s[/bold red]")


async def main():
    """Run all optimization tests."""
    console.print("[bold magenta]SocialMapper Backend Optimization Tests[/bold magenta]")
    console.print("=" * 60)
    
    tests = [
        ("WebSocket Progress Tracking", test_websocket_progress),
        ("Concurrent Jobs with Prioritization", test_concurrent_jobs),
        ("Cache Performance", test_cache_performance),
        ("Performance Metrics", test_performance_metrics),
        ("Load Testing (50 concurrent requests)", lambda: load_test(50)),
    ]
    
    for name, test_func in tests:
        try:
            console.print(f"\n[bold]Running: {name}[/bold]")
            console.print("-" * 40)
            await test_func()
        except Exception as e:
            console.print(f"[red]Test failed: {e}[/red]")
    
    console.print("\n" + "=" * 60)
    console.print("[bold green]All tests completed![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())