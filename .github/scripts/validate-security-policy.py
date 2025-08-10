#!/usr/bin/env python3
"""
Validate security policies and configurations.
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any


class SecurityPolicyValidator:
    """Validate security policies across the project."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path(__file__).parent.parent.parent
    
    def validate_docker_security(self) -> bool:
        """Validate Docker security best practices."""
        dockerfiles = list(self.project_root.glob('**/Dockerfile'))
        
        for dockerfile in dockerfiles:
            with open(dockerfile, 'r') as f:
                content = f.read()
                
                # Check for non-root user
                if 'USER' not in content:
                    self.errors.append(f"{dockerfile}: No USER instruction found - container runs as root")
                
                # Check for latest tags
                if ':latest' in content:
                    self.warnings.append(f"{dockerfile}: Using :latest tag - pin to specific version")
                
                # Check for HEALTHCHECK
                if 'HEALTHCHECK' not in content:
                    self.warnings.append(f"{dockerfile}: No HEALTHCHECK defined")
                
                # Check for sensitive data
                if any(word in content.lower() for word in ['password=', 'api_key=', 'secret=']):
                    self.errors.append(f"{dockerfile}: Potential hardcoded secrets found")
        
        return len(self.errors) == 0
    
    def validate_kubernetes_security(self) -> bool:
        """Validate Kubernetes security configurations."""
        k8s_files = list(self.project_root.glob('infrastructure/kubernetes/*.yaml'))
        
        for k8s_file in k8s_files:
            with open(k8s_file, 'r') as f:
                content = f.read()
                
                # Check for security context
                if 'kind: Deployment' in content and 'securityContext' not in content:
                    self.warnings.append(f"{k8s_file}: No securityContext defined in Deployment")
                
                # Check for resource limits
                if 'kind: Deployment' in content and 'limits' not in content:
                    self.warnings.append(f"{k8s_file}: No resource limits defined")
                
                # Check for network policies
                if 'kind: NetworkPolicy' not in content and 'deployment' in str(k8s_file).lower():
                    self.warnings.append(f"No NetworkPolicy found for {k8s_file}")
        
        return True
    
    def validate_terraform_security(self) -> bool:
        """Validate Terraform security configurations."""
        tf_files = list(self.project_root.glob('infrastructure/terraform/**/*.tf'))
        
        for tf_file in tf_files:
            with open(tf_file, 'r') as f:
                content = f.read()
                
                # Check for hardcoded credentials
                if 'access_key' in content or 'secret_key' in content:
                    self.errors.append(f"{tf_file}: Hardcoded AWS credentials found")
                
                # Check for encrypted storage
                if 'aws_s3_bucket' in content and 'server_side_encryption_configuration' not in content:
                    self.warnings.append(f"{tf_file}: S3 bucket without encryption configuration")
                
                # Check for public access
                if 'publicly_accessible = true' in content:
                    self.warnings.append(f"{tf_file}: Resource configured with public access")
        
        return len(self.errors) == 0
    
    def validate_dependency_security(self) -> bool:
        """Validate dependency security configurations."""
        # Check for package-lock.json
        if not (self.project_root / 'socialmapper-ui' / 'package-lock.json').exists():
            self.warnings.append("No package-lock.json found - dependency versions not locked")
        
        # Check for requirements pinning
        requirements_files = list(self.project_root.glob('**/requirements*.txt'))
        for req_file in requirements_files:
            with open(req_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '==' not in line and '>=' not in line:
                            self.warnings.append(f"{req_file}: Unpinned dependency: {line.strip()}")
        
        return True
    
    def validate_secrets_management(self) -> bool:
        """Validate secrets management practices."""
        # Check for .env files
        env_files = list(self.project_root.glob('**/.env'))
        for env_file in env_files:
            if not env_file.name.endswith('.example'):
                self.errors.append(f"Found .env file: {env_file} - should not be committed")
        
        # Check for secrets baseline
        if not (self.project_root / '.secrets.baseline').exists():
            self.warnings.append("No .secrets.baseline file found for detect-secrets")
        
        # Check GitHub Actions secrets usage
        workflow_files = list(self.project_root.glob('.github/workflows/*.yml'))
        for workflow in workflow_files:
            with open(workflow, 'r') as f:
                content = f.read()
                if '${{ secrets.' in content:
                    # This is good - using secrets properly
                    pass
                if 'env:' in content and ('KEY' in content or 'TOKEN' in content):
                    if not '${{ secrets.' in content:
                        self.warnings.append(f"{workflow}: Potential hardcoded secrets in environment variables")
        
        return len(self.errors) == 0
    
    def validate_security_headers(self) -> bool:
        """Validate security headers configuration."""
        nginx_configs = list(self.project_root.glob('**/nginx*.conf'))
        
        required_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Content-Security-Policy',
            'Strict-Transport-Security'
        ]
        
        for nginx_conf in nginx_configs:
            with open(nginx_conf, 'r') as f:
                content = f.read()
                for header in required_headers:
                    if header not in content:
                        self.warnings.append(f"{nginx_conf}: Missing security header: {header}")
        
        return True
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            'passed': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def run_validation(self) -> bool:
        """Run all validations."""
        print("Validating security policies...")
        
        validations = [
            ('Docker Security', self.validate_docker_security),
            ('Kubernetes Security', self.validate_kubernetes_security),
            ('Terraform Security', self.validate_terraform_security),
            ('Dependency Security', self.validate_dependency_security),
            ('Secrets Management', self.validate_secrets_management),
            ('Security Headers', self.validate_security_headers)
        ]
        
        all_passed = True
        for name, validator in validations:
            print(f"  Checking {name}...")
            if not validator():
                all_passed = False
                print(f"    FAILED")
            else:
                print(f"    PASSED")
        
        report = self.generate_report()
        
        print("\n" + "="*50)
        print("SECURITY POLICY VALIDATION REPORT")
        print("="*50)
        
        if report['errors']:
            print(f"\nERRORS ({report['error_count']}):")
            for error in report['errors']:
                print(f"  - {error}")
        
        if report['warnings']:
            print(f"\nWARNINGS ({report['warning_count']}):")
            for warning in report['warnings']:
                print(f"  - {warning}")
        
        if report['passed']:
            print("\nResult: PASSED (with warnings)")
        else:
            print("\nResult: FAILED")
        
        # Save report
        report_file = self.project_root / 'security-policy-report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to {report_file}")
        
        return report['passed']


def main():
    validator = SecurityPolicyValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()