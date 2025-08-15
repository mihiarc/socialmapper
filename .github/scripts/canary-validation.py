#!/usr/bin/env python3
"""
Canary Deployment Validation Script

This script validates canary deployments by monitoring metrics, health checks,
and performance indicators to determine if a canary deployment is successful.
"""

import argparse
import json
import logging
import time
import sys
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CanaryValidator:
    """Validates canary deployments using multiple metrics and health checks."""
    
    def __init__(self, namespace: str, canary_percentage: int, validation_duration: int, success_threshold: float):
        self.namespace = namespace
        self.canary_percentage = canary_percentage
        self.validation_duration = validation_duration
        self.success_threshold = success_threshold
        self.prometheus_url = "http://prometheus.monitoring.svc.cluster.local:9090"
        self.grafana_url = "http://grafana.monitoring.svc.cluster.local:3000"
        
        # Validation thresholds
        self.error_rate_threshold = 0.01  # 1% error rate
        self.latency_p99_threshold = 2.0  # 2 seconds
        self.availability_threshold = 0.999  # 99.9% availability
        
    def validate_canary_deployment(self) -> bool:
        """
        Comprehensive validation of canary deployment.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        logger.info(f"Starting canary validation with {self.canary_percentage}% traffic")
        logger.info(f"Validation duration: {self.validation_duration} seconds")
        logger.info(f"Success threshold: {self.success_threshold}")
        
        start_time = datetime.now()
        validation_results = []
        
        try:
            # Wait for canary deployment to stabilize
            logger.info("Waiting for canary deployment to stabilize...")
            time.sleep(30)
            
            # Validate canary pods are healthy
            if not self._validate_canary_health():
                logger.error("Canary health validation failed")
                return False
            
            # Run validation checks at intervals
            check_interval = min(60, self.validation_duration // 10)  # At least 10 checks
            checks_completed = 0
            
            while (datetime.now() - start_time).total_seconds() < self.validation_duration:
                logger.info(f"Running validation check #{checks_completed + 1}")
                
                check_result = self._run_validation_check()
                validation_results.append(check_result)
                
                logger.info(f"Check result: {check_result}")
                checks_completed += 1
                
                # Early exit if consistent failures
                if checks_completed >= 3:
                    recent_results = validation_results[-3:]
                    if all(not result['success'] for result in recent_results):
                        logger.error("Three consecutive validation failures - aborting")
                        return False
                
                # Sleep until next check
                time.sleep(check_interval)
            
            # Analyze overall results
            success_rate = sum(1 for result in validation_results if result['success']) / len(validation_results)
            
            logger.info(f"Validation completed: {success_rate:.2%} success rate")
            logger.info(f"Required threshold: {self.success_threshold:.2%}")
            
            if success_rate >= self.success_threshold:
                logger.info("✅ Canary validation PASSED")
                self._log_validation_summary(validation_results, True)
                return True
            else:
                logger.error("❌ Canary validation FAILED")
                self._log_validation_summary(validation_results, False)
                return False
                
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            return False
    
    def _validate_canary_health(self) -> bool:
        """Validate that canary pods are healthy and ready."""
        try:
            # Check canary API deployment
            api_cmd = [
                'kubectl', 'get', 'deployment', 'socialmapper-api-canary',
                '-n', self.namespace, '-o', 'json'
            ]
            api_result = subprocess.run(api_cmd, capture_output=True, text=True, check=True)
            api_deployment = json.loads(api_result.stdout)
            
            api_ready = api_deployment['status'].get('readyReplicas', 0)
            api_desired = api_deployment['spec']['replicas']
            
            if api_ready < api_desired:
                logger.error(f"API canary not ready: {api_ready}/{api_desired} replicas")
                return False
            
            # Check canary UI deployment
            ui_cmd = [
                'kubectl', 'get', 'deployment', 'socialmapper-ui-canary',
                '-n', self.namespace, '-o', 'json'
            ]
            ui_result = subprocess.run(ui_cmd, capture_output=True, text=True, check=True)
            ui_deployment = json.loads(ui_result.stdout)
            
            ui_ready = ui_deployment['status'].get('readyReplicas', 0)
            ui_desired = ui_deployment['spec']['replicas']
            
            if ui_ready < ui_desired:
                logger.error(f"UI canary not ready: {ui_ready}/{ui_desired} replicas")
                return False
            
            logger.info(f"Canary deployments healthy: API ({api_ready}/{api_desired}), UI ({ui_ready}/{ui_desired})")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check canary health: {e}")
            return False
    
    def _run_validation_check(self) -> Dict:
        """Run a single validation check with multiple metrics."""
        check_result = {
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'metrics': {},
            'issues': []
        }
        
        # Health check validation
        health_check = self._check_health_endpoints()
        check_result['metrics']['health_check'] = health_check
        if not health_check['success']:
            check_result['success'] = False
            check_result['issues'].append(f"Health check failed: {health_check['message']}")
        
        # Error rate validation
        error_rate = self._check_error_rate()
        check_result['metrics']['error_rate'] = error_rate
        if error_rate['canary_error_rate'] > self.error_rate_threshold:
            check_result['success'] = False
            check_result['issues'].append(f"High error rate: {error_rate['canary_error_rate']:.3f}")
        
        # Latency validation
        latency = self._check_latency()
        check_result['metrics']['latency'] = latency
        if latency['canary_p99'] > self.latency_p99_threshold:
            check_result['success'] = False
            check_result['issues'].append(f"High latency: {latency['canary_p99']:.2f}s")
        
        # Availability validation
        availability = self._check_availability()
        check_result['metrics']['availability'] = availability
        if availability['canary_availability'] < self.availability_threshold:
            check_result['success'] = False
            check_result['issues'].append(f"Low availability: {availability['canary_availability']:.3f}")
        
        # Resource utilization validation
        resources = self._check_resource_utilization()
        check_result['metrics']['resources'] = resources
        if resources['memory_usage_percent'] > 90 or resources['cpu_usage_percent'] > 90:
            check_result['success'] = False
            check_result['issues'].append("High resource utilization")
        
        return check_result
    
    def _check_health_endpoints(self) -> Dict:
        """Check health endpoints for both stable and canary versions."""
        try:
            # Test canary API health
            canary_api_response = requests.get(
                "https://demo.socialmapper.com/api/v1/health",
                headers={"X-Canary-Request": "true"},
                timeout=10
            )
            
            canary_healthy = canary_api_response.status_code == 200
            
            return {
                'success': canary_healthy,
                'canary_status_code': canary_api_response.status_code,
                'message': 'Healthy' if canary_healthy else f'Unhealthy: {canary_api_response.status_code}'
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Request failed: {str(e)}'
            }
    
    def _check_error_rate(self) -> Dict:
        """Check error rates from Prometheus metrics."""
        try:
            # Query for canary error rate
            canary_query = f'''
            rate(http_requests_total{{
                namespace="{self.namespace}",
                version="canary",
                status=~"5.."
            }}[5m])
            '''
            
            stable_query = f'''
            rate(http_requests_total{{
                namespace="{self.namespace}",
                version="stable",
                status=~"5.."
            }}[5m])
            '''
            
            canary_errors = self._query_prometheus(canary_query)
            stable_errors = self._query_prometheus(stable_query)
            
            canary_error_rate = float(canary_errors[0]['value'][1]) if canary_errors else 0.0
            stable_error_rate = float(stable_errors[0]['value'][1]) if stable_errors else 0.0
            
            return {
                'canary_error_rate': canary_error_rate,
                'stable_error_rate': stable_error_rate,
                'comparison': 'Better' if canary_error_rate <= stable_error_rate else 'Worse'
            }
            
        except Exception as e:
            logger.warning(f"Error rate check failed: {e}")
            return {
                'canary_error_rate': 0.0,
                'stable_error_rate': 0.0,
                'comparison': 'Unknown'
            }
    
    def _check_latency(self) -> Dict:
        """Check latency metrics from Prometheus."""
        try:
            # Query for P99 latency
            canary_query = f'''
            histogram_quantile(0.99,
                rate(http_request_duration_seconds_bucket{{
                    namespace="{self.namespace}",
                    version="canary"
                }}[5m])
            )
            '''
            
            stable_query = f'''
            histogram_quantile(0.99,
                rate(http_request_duration_seconds_bucket{{
                    namespace="{self.namespace}",
                    version="stable"
                }}[5m])
            )
            '''
            
            canary_p99 = self._query_prometheus(canary_query)
            stable_p99 = self._query_prometheus(stable_query)
            
            canary_latency = float(canary_p99[0]['value'][1]) if canary_p99 else 0.0
            stable_latency = float(stable_p99[0]['value'][1]) if stable_p99 else 0.0
            
            return {
                'canary_p99': canary_latency,
                'stable_p99': stable_latency,
                'comparison': 'Better' if canary_latency <= stable_latency * 1.1 else 'Worse'
            }
            
        except Exception as e:
            logger.warning(f"Latency check failed: {e}")
            return {
                'canary_p99': 0.0,
                'stable_p99': 0.0,
                'comparison': 'Unknown'
            }
    
    def _check_availability(self) -> Dict:
        """Check availability metrics from Prometheus."""
        try:
            # Calculate availability over the last 5 minutes
            canary_query = f'''
            (
                rate(http_requests_total{{
                    namespace="{self.namespace}",
                    version="canary"
                }}[5m]) -
                rate(http_requests_total{{
                    namespace="{self.namespace}",
                    version="canary",
                    status=~"5.."
                }}[5m])
            ) /
            rate(http_requests_total{{
                namespace="{self.namespace}",
                version="canary"
            }}[5m])
            '''
            
            canary_availability = self._query_prometheus(canary_query)
            availability = float(canary_availability[0]['value'][1]) if canary_availability else 1.0
            
            return {
                'canary_availability': availability,
                'healthy': availability >= self.availability_threshold
            }
            
        except Exception as e:
            logger.warning(f"Availability check failed: {e}")
            return {
                'canary_availability': 1.0,
                'healthy': True
            }
    
    def _check_resource_utilization(self) -> Dict:
        """Check resource utilization of canary pods."""
        try:
            # Memory utilization
            memory_query = f'''
            avg(container_memory_usage_bytes{{
                namespace="{self.namespace}",
                pod=~".*-canary-.*"
            }}) /
            avg(container_spec_memory_limit_bytes{{
                namespace="{self.namespace}",
                pod=~".*-canary-.*"
            }}) * 100
            '''
            
            # CPU utilization
            cpu_query = f'''
            avg(rate(container_cpu_usage_seconds_total{{
                namespace="{self.namespace}",
                pod=~".*-canary-.*"
            }}[5m])) /
            avg(container_spec_cpu_quota{{
                namespace="{self.namespace}",
                pod=~".*-canary-.*"
            }} / container_spec_cpu_period{{
                namespace="{self.namespace}",
                pod=~".*-canary-.*"
            }}) * 100
            '''
            
            memory_usage = self._query_prometheus(memory_query)
            cpu_usage = self._query_prometheus(cpu_query)
            
            memory_percent = float(memory_usage[0]['value'][1]) if memory_usage else 0.0
            cpu_percent = float(cpu_usage[0]['value'][1]) if cpu_usage else 0.0
            
            return {
                'memory_usage_percent': memory_percent,
                'cpu_usage_percent': cpu_percent,
                'healthy': memory_percent < 90 and cpu_percent < 90
            }
            
        except Exception as e:
            logger.warning(f"Resource utilization check failed: {e}")
            return {
                'memory_usage_percent': 0.0,
                'cpu_usage_percent': 0.0,
                'healthy': True
            }
    
    def _query_prometheus(self, query: str) -> List[Dict]:
        """Query Prometheus for metrics."""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'success':
                return data['data']['result']
            else:
                logger.warning(f"Prometheus query failed: {data}")
                return []
                
        except requests.RequestException as e:
            logger.warning(f"Failed to query Prometheus: {e}")
            return []
    
    def _log_validation_summary(self, results: List[Dict], passed: bool) -> None:
        """Log a summary of validation results."""
        total_checks = len(results)
        successful_checks = sum(1 for r in results if r['success'])
        
        logger.info("=" * 60)
        logger.info("CANARY VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Status: {'PASSED' if passed else 'FAILED'}")
        logger.info(f"Total checks: {total_checks}")
        logger.info(f"Successful checks: {successful_checks}")
        logger.info(f"Success rate: {successful_checks/total_checks:.2%}")
        logger.info(f"Canary percentage: {self.canary_percentage}%")
        logger.info(f"Validation duration: {self.validation_duration}s")
        
        # Log recent issues
        recent_results = results[-3:] if len(results) >= 3 else results
        issues = []
        for result in recent_results:
            issues.extend(result['issues'])
        
        if issues:
            logger.info("Recent issues:")
            for issue in set(issues):  # Remove duplicates
                logger.info(f"  - {issue}")
        
        # Save detailed results
        summary_file = f"canary-validation-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'summary': {
                    'passed': passed,
                    'total_checks': total_checks,
                    'successful_checks': successful_checks,
                    'success_rate': successful_checks / total_checks,
                    'canary_percentage': self.canary_percentage
                },
                'detailed_results': results
            }, f, indent=2)
        
        logger.info(f"Detailed results saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description='Validate canary deployment')
    parser.add_argument('--namespace', required=True, help='Kubernetes namespace')
    parser.add_argument('--canary-percentage', type=int, required=True,
                        help='Percentage of traffic going to canary')
    parser.add_argument('--validation-duration', type=int, required=True,
                        help='Validation duration in seconds')
    parser.add_argument('--success-threshold', type=float, default=0.99,
                        help='Success threshold (0.0-1.0)')
    
    args = parser.parse_args()
    
    validator = CanaryValidator(
        namespace=args.namespace,
        canary_percentage=args.canary_percentage,
        validation_duration=args.validation_duration,
        success_threshold=args.success_threshold
    )
    
    success = validator.validate_canary_deployment()
    
    if success:
        print("validation_passed=true")
        sys.exit(0)
    else:
        print("validation_passed=false")
        sys.exit(1)


if __name__ == '__main__':
    main()