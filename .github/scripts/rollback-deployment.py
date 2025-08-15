#!/usr/bin/env python3
"""
Automated Rollback Deployment Script

This script provides automated rollback capabilities for different deployment strategies
(Canary, Blue-Green, Rolling Update) with support for manual overrides and validation.
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
import os
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Supported deployment strategies."""
    CANARY = "canary"
    BLUE_GREEN = "blue-green"
    ROLLING_UPDATE = "rolling-update"


class RollbackStatus(Enum):
    """Rollback status enum."""
    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"
    VALIDATION_FAILED = "validation_failed"


class DeploymentRollback:
    """Handles automated rollback for different deployment strategies."""
    
    def __init__(self, deployment_strategy: str, namespace: str, rollback_timeout: int, manual_override: bool = False):
        self.deployment_strategy = DeploymentStrategy(deployment_strategy)
        self.namespace = namespace
        self.rollback_timeout = rollback_timeout
        self.manual_override = manual_override
        
        # Rollback configuration
        self.validation_timeout = 180  # 3 minutes
        self.health_check_timeout = 120  # 2 minutes
        self.traffic_switch_timeout = 60  # 1 minute
        
        # Store rollback state
        self.rollback_state = {
            'strategy': deployment_strategy,
            'start_time': datetime.now().isoformat(),
            'status': RollbackStatus.IN_PROGRESS.value,
            'steps_completed': [],
            'steps_failed': [],
            'validation_results': {}
        }
    
    def execute_rollback(self) -> bool:
        """
        Execute rollback based on deployment strategy.
        
        Returns:
            bool: True if rollback succeeded, False otherwise
        """
        logger.info(f"Starting rollback for {self.deployment_strategy.value} deployment")
        logger.info(f"Namespace: {self.namespace}")
        logger.info(f"Timeout: {self.rollback_timeout} seconds")
        logger.info(f"Manual override: {self.manual_override}")
        
        try:
            # Create rollback record
            self._create_rollback_record()
            
            # Execute strategy-specific rollback
            if self.deployment_strategy == DeploymentStrategy.CANARY:
                success = self._rollback_canary_deployment()
            elif self.deployment_strategy == DeploymentStrategy.BLUE_GREEN:
                success = self._rollback_blue_green_deployment()
            elif self.deployment_strategy == DeploymentStrategy.ROLLING_UPDATE:
                success = self._rollback_rolling_deployment()
            else:
                logger.error(f"Unknown deployment strategy: {self.deployment_strategy}")
                return False
            
            # Update rollback state
            self.rollback_state['status'] = RollbackStatus.SUCCESS.value if success else RollbackStatus.FAILURE.value
            self.rollback_state['end_time'] = datetime.now().isoformat()
            
            # Save final rollback record
            self._save_rollback_record()
            
            # Send notifications
            self._send_rollback_notification(success)
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed with exception: {e}")
            self.rollback_state['status'] = RollbackStatus.FAILURE.value
            self.rollback_state['exception'] = str(e)
            self._save_rollback_record()
            return False
    
    def _rollback_canary_deployment(self) -> bool:
        """Rollback canary deployment by removing canary and routing all traffic to stable."""
        logger.info("🔄 Executing Canary deployment rollback")
        
        try:
            # Step 1: Immediate traffic routing to stable
            logger.info("Step 1: Routing all traffic to stable version")
            if not self._route_traffic_to_stable():
                self.rollback_state['steps_failed'].append('traffic_routing')
                return False
            self.rollback_state['steps_completed'].append('traffic_routing')
            
            # Step 2: Validate stable version is handling traffic properly
            logger.info("Step 2: Validating stable version performance")
            if not self._validate_stable_performance():
                if not self.manual_override:
                    self.rollback_state['steps_failed'].append('stable_validation')
                    return False
                else:
                    logger.warning("Stable validation failed but manual override enabled")
            self.rollback_state['steps_completed'].append('stable_validation')
            
            # Step 3: Scale down canary deployments
            logger.info("Step 3: Scaling down canary deployments")
            if not self._scale_down_canary():
                logger.warning("Failed to scale down canary - continuing anyway")
            self.rollback_state['steps_completed'].append('canary_scale_down')
            
            # Step 4: Clean up canary resources
            logger.info("Step 4: Cleaning up canary resources")
            self._cleanup_canary_resources()
            self.rollback_state['steps_completed'].append('canary_cleanup')
            
            # Step 5: Update Istio VirtualService to remove canary routing
            logger.info("Step 5: Updating Istio configuration")
            if not self._update_istio_for_rollback():
                logger.warning("Failed to update Istio config - manual cleanup may be needed")
            self.rollback_state['steps_completed'].append('istio_cleanup')
            
            # Step 6: Final validation
            logger.info("Step 6: Running final health checks")
            if not self._run_post_rollback_validation():
                logger.warning("Post-rollback validation issues detected")
                if not self.manual_override:
                    return False
            self.rollback_state['steps_completed'].append('final_validation')
            
            logger.info("✅ Canary rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Canary rollback failed: {e}")
            return False
    
    def _rollback_blue_green_deployment(self) -> bool:
        """Rollback blue-green deployment by switching back to previous environment."""
        logger.info("🔄 Executing Blue-Green deployment rollback")
        
        try:
            # Step 1: Determine current and previous environments
            logger.info("Step 1: Determining environment states")
            env_state = self._get_blue_green_state()
            if not env_state:
                self.rollback_state['steps_failed'].append('environment_detection')
                return False
            
            current_env = env_state['active_environment']
            previous_env = 'blue' if current_env == 'green' else 'green'
            
            logger.info(f"Current environment: {current_env}")
            logger.info(f"Rolling back to: {previous_env}")
            
            self.rollback_state['steps_completed'].append('environment_detection')
            
            # Step 2: Validate previous environment is healthy
            logger.info("Step 2: Validating previous environment health")
            if not self._validate_environment_health(previous_env):
                logger.error(f"Previous environment {previous_env} is not healthy")
                if not self.manual_override:
                    self.rollback_state['steps_failed'].append('previous_env_health')
                    return False
                else:
                    logger.warning("Previous environment unhealthy but manual override enabled")
            self.rollback_state['steps_completed'].append('previous_env_health')
            
            # Step 3: Switch traffic to previous environment
            logger.info(f"Step 3: Switching traffic to {previous_env} environment")
            if not self._switch_blue_green_traffic(previous_env):
                self.rollback_state['steps_failed'].append('traffic_switch')
                return False
            self.rollback_state['steps_completed'].append('traffic_switch')
            
            # Step 4: Validate traffic switch
            logger.info("Step 4: Validating traffic switch")
            time.sleep(30)  # Allow traffic to stabilize
            if not self._validate_traffic_switch(previous_env):
                logger.error("Traffic switch validation failed")
                if not self.manual_override:
                    self.rollback_state['steps_failed'].append('traffic_validation')
                    return False
            self.rollback_state['steps_completed'].append('traffic_validation')
            
            # Step 5: Scale down failed environment
            logger.info(f"Step 5: Scaling down {current_env} environment")
            self._scale_down_environment(current_env)
            self.rollback_state['steps_completed'].append('failed_env_scale_down')
            
            # Step 6: Update monitoring and alerts
            logger.info("Step 6: Updating monitoring configuration")
            self._update_monitoring_for_rollback(previous_env)
            self.rollback_state['steps_completed'].append('monitoring_update')
            
            # Step 7: Final validation
            logger.info("Step 7: Running comprehensive validation")
            if not self._run_post_rollback_validation():
                logger.warning("Post-rollback validation issues detected")
                if not self.manual_override:
                    return False
            self.rollback_state['steps_completed'].append('final_validation')
            
            logger.info("✅ Blue-Green rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Blue-Green rollback failed: {e}")
            return False
    
    def _rollback_rolling_deployment(self) -> bool:
        """Rollback rolling deployment using kubectl rollout undo."""
        logger.info("🔄 Executing Rolling deployment rollback")
        
        try:
            # Step 1: Get rollout history
            logger.info("Step 1: Checking rollout history")
            history = self._get_rollout_history()
            if not history:
                self.rollback_state['steps_failed'].append('rollout_history')
                return False
            self.rollback_state['steps_completed'].append('rollout_history')
            
            # Step 2: Rollback API deployment
            logger.info("Step 2: Rolling back API deployment")
            if not self._rollback_deployment('socialmapper-api'):
                self.rollback_state['steps_failed'].append('api_rollback')
                return False
            self.rollback_state['steps_completed'].append('api_rollback')
            
            # Step 3: Rollback UI deployment
            logger.info("Step 3: Rolling back UI deployment")
            if not self._rollback_deployment('socialmapper-ui'):
                self.rollback_state['steps_failed'].append('ui_rollback')
                return False
            self.rollback_state['steps_completed'].append('ui_rollback')
            
            # Step 4: Wait for rollout completion
            logger.info("Step 4: Waiting for rollout completion")
            if not self._wait_for_rollout_completion():
                self.rollback_state['steps_failed'].append('rollout_completion')
                return False
            self.rollback_state['steps_completed'].append('rollout_completion')
            
            # Step 5: Validate rolled back deployments
            logger.info("Step 5: Validating rolled back deployments")
            if not self._validate_rolled_back_deployments():
                logger.warning("Rollback validation issues detected")
                if not self.manual_override:
                    return False
            self.rollback_state['steps_completed'].append('rollback_validation')
            
            logger.info("✅ Rolling deployment rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rolling deployment rollback failed: {e}")
            return False
    
    def _route_traffic_to_stable(self) -> bool:
        """Route all traffic to stable version (canary rollback)."""
        try:
            # Update Istio VirtualService to route 100% traffic to stable
            patch_data = [{
                "op": "replace",
                "path": "/spec/http/0/route/0/weight",
                "value": 100
            }, {
                "op": "replace",
                "path": "/spec/http/0/route/1/weight",
                "value": 0
            }]
            
            cmd = [
                'kubectl', 'patch', 'virtualservice', 'socialmapper-api-canary',
                '-n', self.namespace, '--type', 'json',
                '-p', json.dumps(patch_data)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Traffic successfully routed to stable version")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to route traffic to stable: {e}")
            return False
    
    def _validate_stable_performance(self) -> bool:
        """Validate that stable version is performing well after traffic routing."""
        try:
            # Wait for traffic to stabilize
            time.sleep(30)
            
            # Check health endpoints
            api_health = self._check_api_health('stable')
            ui_health = self._check_ui_health('stable')
            
            if not api_health or not ui_health:
                logger.error("Stable version health checks failed")
                return False
            
            # Check error rates (simplified)
            error_rate = self._get_current_error_rate()
            if error_rate > 0.05:  # 5% error rate threshold
                logger.error(f"High error rate detected: {error_rate:.3f}")
                return False
            
            logger.info("Stable version performance validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Stable performance validation failed: {e}")
            return False
    
    def _scale_down_canary(self) -> bool:
        """Scale down canary deployments."""
        try:
            # Scale down API canary
            cmd_api = [
                'kubectl', 'scale', 'deployment', 'socialmapper-api-canary',
                '-n', self.namespace, '--replicas=0'
            ]
            subprocess.run(cmd_api, check=True)
            
            # Scale down UI canary
            cmd_ui = [
                'kubectl', 'scale', 'deployment', 'socialmapper-ui-canary',
                '-n', self.namespace, '--replicas=0'
            ]
            subprocess.run(cmd_ui, check=True)
            
            logger.info("Canary deployments scaled down")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to scale down canary: {e}")
            return False
    
    def _cleanup_canary_resources(self) -> None:
        """Clean up canary resources (optional - for complete cleanup)."""
        try:
            # Delete canary deployments (optional)
            cleanup_commands = [
                ['kubectl', 'delete', 'deployment', 'socialmapper-api-canary', '-n', self.namespace, '--ignore-not-found=true'],
                ['kubectl', 'delete', 'deployment', 'socialmapper-ui-canary', '-n', self.namespace, '--ignore-not-found=true'],
                ['kubectl', 'delete', 'service', 'socialmapper-api-canary-service', '-n', self.namespace, '--ignore-not-found=true'],
                ['kubectl', 'delete', 'service', 'socialmapper-ui-canary-service', '-n', self.namespace, '--ignore-not-found=true']
            ]
            
            for cmd in cleanup_commands:
                subprocess.run(cmd, capture_output=True, text=True)
            
            logger.info("Canary resources cleaned up")
            
        except Exception as e:
            logger.warning(f"Canary cleanup had issues: {e}")
    
    def _update_istio_for_rollback(self) -> bool:
        """Update Istio configuration to remove canary routing."""
        try:
            # Delete canary VirtualServices
            cmd = [
                'kubectl', 'delete', 'virtualservice', 'socialmapper-api-canary',
                '-n', self.namespace, '--ignore-not-found=true'
            ]
            subprocess.run(cmd, check=True)
            
            cmd = [
                'kubectl', 'delete', 'virtualservice', 'socialmapper-ui-canary',
                '-n', self.namespace, '--ignore-not-found=true'
            ]
            subprocess.run(cmd, check=True)
            
            logger.info("Istio canary configuration removed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update Istio configuration: {e}")
            return False
    
    def _get_blue_green_state(self) -> Optional[Dict]:
        """Get current blue-green deployment state."""
        try:
            cmd = [
                'kubectl', 'get', 'service', 'socialmapper-api-active',
                '-n', self.namespace, '-o', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            service = json.loads(result.stdout)
            
            active_env = service.get('metadata', {}).get('labels', {}).get('active-environment', 'blue')
            
            return {
                'active_environment': active_env,
                'inactive_environment': 'green' if active_env == 'blue' else 'blue'
            }
            
        except Exception as e:
            logger.error(f"Failed to get blue-green state: {e}")
            return None
    
    def _validate_environment_health(self, environment: str) -> bool:
        """Validate health of specific environment."""
        try:
            # Check if environment deployments are ready
            api_deployment = f'socialmapper-api-{environment}'
            ui_deployment = f'socialmapper-ui-{environment}'
            
            # Check API deployment
            cmd = [
                'kubectl', 'get', 'deployment', api_deployment,
                '-n', self.namespace, '-o', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            api_status = json.loads(result.stdout)
            
            api_ready = api_status['status'].get('readyReplicas', 0)
            api_desired = api_status['spec']['replicas']
            
            if api_ready < api_desired:
                logger.warning(f"API {environment} not fully ready: {api_ready}/{api_desired}")
                return False
            
            # Check UI deployment
            cmd = [
                'kubectl', 'get', 'deployment', ui_deployment,
                '-n', self.namespace, '-o', 'json'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ui_status = json.loads(result.stdout)
            
            ui_ready = ui_status['status'].get('readyReplicas', 0)
            ui_desired = ui_status['spec']['replicas']
            
            if ui_ready < ui_desired:
                logger.warning(f"UI {environment} not fully ready: {ui_ready}/{ui_desired}")
                return False
            
            logger.info(f"Environment {environment} is healthy")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate {environment} environment health: {e}")
            return False
    
    def _switch_blue_green_traffic(self, target_environment: str) -> bool:
        """Switch blue-green traffic to target environment."""
        try:
            # Update service selectors
            patch_data = {
                'spec': {
                    'selector': {
                        'app.kubernetes.io/version': target_environment
                    }
                },
                'metadata': {
                    'labels': {
                        'active-environment': target_environment
                    }
                }
            }
            
            # Update API service
            cmd = [
                'kubectl', 'patch', 'service', 'socialmapper-api-active',
                '-n', self.namespace, '--type', 'merge',
                '-p', json.dumps(patch_data)
            ]
            subprocess.run(cmd, check=True)
            
            # Update UI service
            cmd = [
                'kubectl', 'patch', 'service', 'socialmapper-ui-active',
                '-n', self.namespace, '--type', 'merge',
                '-p', json.dumps(patch_data)
            ]
            subprocess.run(cmd, check=True)
            
            logger.info(f"Traffic switched to {target_environment} environment")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to switch traffic: {e}")
            return False
    
    def _validate_traffic_switch(self, target_environment: str) -> bool:
        """Validate that traffic is actually going to target environment."""
        try:
            # Simple validation - check service endpoints
            return self._validate_environment_health(target_environment)
        except Exception as e:
            logger.error(f"Traffic switch validation failed: {e}")
            return False
    
    def _scale_down_environment(self, environment: str) -> None:
        """Scale down specific environment."""
        try:
            # Scale down to minimal replicas for quick recovery if needed
            api_cmd = [
                'kubectl', 'scale', 'deployment', f'socialmapper-api-{environment}',
                '-n', self.namespace, '--replicas=1'
            ]
            subprocess.run(api_cmd, check=True)
            
            ui_cmd = [
                'kubectl', 'scale', 'deployment', f'socialmapper-ui-{environment}',
                '-n', self.namespace, '--replicas=1'
            ]
            subprocess.run(ui_cmd, check=True)
            
            logger.info(f"Environment {environment} scaled down")
            
        except Exception as e:
            logger.warning(f"Failed to scale down {environment}: {e}")
    
    def _update_monitoring_for_rollback(self, active_environment: str) -> None:
        """Update monitoring configuration after rollback."""
        try:
            # Update ConfigMap with new active environment
            patch_data = {
                'data': {
                    'bluegreen.active.environment': active_environment
                }
            }
            
            cmd = [
                'kubectl', 'patch', 'configmap', 'traffic-splitting-config',
                '-n', self.namespace, '--type', 'merge',
                '-p', json.dumps(patch_data)
            ]
            subprocess.run(cmd, check=True)
            
            logger.info("Monitoring configuration updated")
            
        except Exception as e:
            logger.warning(f"Failed to update monitoring config: {e}")
    
    def _get_rollout_history(self) -> bool:
        """Get rollout history for deployments."""
        try:
            cmd = [
                'kubectl', 'rollout', 'history', 'deployment/socialmapper-api',
                '-n', self.namespace
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if "No rollout history found" in result.stdout:
                logger.error("No rollout history found")
                return False
            
            logger.info("Rollout history available")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get rollout history: {e}")
            return False
    
    def _rollback_deployment(self, deployment_name: str) -> bool:
        """Rollback a specific deployment."""
        try:
            cmd = [
                'kubectl', 'rollout', 'undo', f'deployment/{deployment_name}',
                '-n', self.namespace
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Rollback initiated for {deployment_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rollback {deployment_name}: {e}")
            return False
    
    def _wait_for_rollout_completion(self) -> bool:
        """Wait for rollout completion."""
        try:
            deployments = ['socialmapper-api', 'socialmapper-ui']
            
            for deployment in deployments:
                cmd = [
                    'kubectl', 'rollout', 'status', f'deployment/{deployment}',
                    '-n', self.namespace, f'--timeout={self.rollback_timeout}s'
                ]
                subprocess.run(cmd, check=True)
            
            logger.info("All rollouts completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollout completion failed: {e}")
            return False
    
    def _validate_rolled_back_deployments(self) -> bool:
        """Validate that rolled back deployments are healthy."""
        try:
            # Check deployment status
            deployments = ['socialmapper-api', 'socialmapper-ui']
            
            for deployment in deployments:
                cmd = [
                    'kubectl', 'get', 'deployment', deployment,
                    '-n', self.namespace, '-o', 'json'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                deployment_status = json.loads(result.stdout)
                
                ready = deployment_status['status'].get('readyReplicas', 0)
                desired = deployment_status['spec']['replicas']
                
                if ready < desired:
                    logger.error(f"Deployment {deployment} not ready: {ready}/{desired}")
                    return False
            
            # Basic health checks
            return self._check_api_health('stable') and self._check_ui_health('stable')
            
        except Exception as e:
            logger.error(f"Deployment validation failed: {e}")
            return False
    
    def _run_post_rollback_validation(self) -> bool:
        """Run comprehensive post-rollback validation."""
        try:
            # Health checks
            if not self._check_api_health():
                logger.error("API health check failed")
                return False
            
            if not self._check_ui_health():
                logger.error("UI health check failed")
                return False
            
            # Basic functionality test
            if not self._test_basic_functionality():
                logger.error("Basic functionality test failed")
                return False
            
            # Error rate check
            error_rate = self._get_current_error_rate()
            if error_rate > 0.1:  # 10% error rate threshold for post-rollback
                logger.error(f"High error rate after rollback: {error_rate:.3f}")
                return False
            
            logger.info("Post-rollback validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Post-rollback validation failed: {e}")
            return False
    
    def _check_api_health(self, version: str = None) -> bool:
        """Check API health."""
        try:
            if version:
                service_name = f'socialmapper-api-{version}-service'
            else:
                service_name = 'socialmapper-api-service'
            
            url = f'http://{service_name}.{self.namespace}.svc.cluster.local:8000/api/v1/health'
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"API health check failed: {e}")
            return False
    
    def _check_ui_health(self, version: str = None) -> bool:
        """Check UI health."""
        try:
            if version:
                service_name = f'socialmapper-ui-{version}-service'
            else:
                service_name = 'socialmapper-ui-service'
            
            url = f'http://{service_name}.{self.namespace}.svc.cluster.local:8080/health'
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"UI health check failed: {e}")
            return False
    
    def _test_basic_functionality(self) -> bool:
        """Test basic application functionality."""
        try:
            # Test metadata endpoint
            url = f'http://socialmapper-api-service.{self.namespace}.svc.cluster.local:8000/api/v1/metadata/travel-modes'
            response = requests.get(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"Basic functionality test failed: {e}")
            return False
    
    def _get_current_error_rate(self) -> float:
        """Get current error rate (simplified)."""
        # In a real implementation, this would query Prometheus
        # For now, return a low error rate
        return 0.01
    
    def _create_rollback_record(self) -> None:
        """Create initial rollback record."""
        try:
            # Create rollback record in Kubernetes as a ConfigMap
            rollback_config = {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': f'rollback-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                    'namespace': self.namespace,
                    'labels': {
                        'rollback.socialmapper.com/strategy': self.deployment_strategy.value,
                        'rollback.socialmapper.com/timestamp': str(int(time.time()))
                    }
                },
                'data': {
                    'rollback_state': json.dumps(self.rollback_state)
                }
            }
            
            # Apply the ConfigMap
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                import yaml
                yaml.dump(rollback_config, f)
                f.flush()
                
                cmd = ['kubectl', 'apply', '-f', f.name]
                subprocess.run(cmd, check=True)
                
                os.unlink(f.name)
            
        except Exception as e:
            logger.warning(f"Failed to create rollback record: {e}")
    
    def _save_rollback_record(self) -> None:
        """Save rollback record to file."""
        try:
            filename = f"rollback-{self.deployment_strategy.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(self.rollback_state, f, indent=2)
            
            logger.info(f"Rollback record saved to: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to save rollback record: {e}")
    
    def _send_rollback_notification(self, success: bool) -> None:
        """Send rollback notification."""
        try:
            status = "SUCCESS" if success else "FAILURE"
            message = f"Rollback {status} for {self.deployment_strategy.value} deployment in {self.namespace}"
            
            # In a real implementation, send to Slack, email, etc.
            logger.info(f"Notification: {message}")
            
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")


def main():
    parser = argparse.ArgumentParser(description='Automated deployment rollback')
    parser.add_argument('--deployment-strategy', required=True,
                        choices=['canary', 'blue-green', 'rolling-update'],
                        help='Deployment strategy to rollback')
    parser.add_argument('--namespace', required=True, help='Kubernetes namespace')
    parser.add_argument('--rollback-timeout', type=int, default=300,
                        help='Rollback timeout in seconds')
    parser.add_argument('--manual-override', action='store_true',
                        help='Continue rollback even if validation fails')
    
    args = parser.parse_args()
    
    rollback = DeploymentRollback(
        deployment_strategy=args.deployment_strategy,
        namespace=args.namespace,
        rollback_timeout=args.rollback_timeout,
        manual_override=args.manual_override
    )
    
    success = rollback.execute_rollback()
    
    if success:
        logger.info("✅ Rollback completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Rollback failed")
        sys.exit(1)


if __name__ == '__main__':
    main()