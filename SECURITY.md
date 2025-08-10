# SocialMapper Security Documentation

## Overview

This document outlines the comprehensive security measures, scanning tools, and processes implemented in the SocialMapper CI/CD pipeline to ensure application and infrastructure security.

## Security Architecture

### Defense in Depth Strategy

Our security implementation follows a defense-in-depth approach with multiple layers:

1. **Pre-commit Security**: Local security checks before code commits
2. **CI/CD Security Gates**: Automated security scanning in pipelines
3. **Runtime Security**: Container and infrastructure security measures
4. **Post-deployment Validation**: Production security monitoring

## Security Scanning Tools

### Static Application Security Testing (SAST)

#### CodeQL
- **Purpose**: Deep semantic code analysis
- **Languages**: Python, JavaScript/TypeScript
- **Configuration**: `.github/codeql/codeql-config.yml`
- **Queries**: Security-extended, security-and-quality
- **Integration**: GitHub Advanced Security

#### Bandit (Python)
- **Purpose**: Python-specific security linting
- **Configuration**: `.bandit`
- **Severity Levels**: Medium, High, Critical
- **Focus**: Common security issues in Python code

#### ESLint Security Plugins (JavaScript/TypeScript)
- **Purpose**: JavaScript/TypeScript security analysis
- **Configuration**: `.github/security/eslint-security.json`
- **Plugins**:
  - eslint-plugin-security
  - eslint-plugin-no-unsanitized
  - eslint-plugin-no-secrets
  - @microsoft/eslint-plugin-sdl

#### Semgrep
- **Purpose**: Multi-language semantic analysis
- **Rulesets**:
  - OWASP Top 10
  - Security audit
  - Language-specific rules
- **Languages**: Python, JavaScript, TypeScript, Docker, Kubernetes

### Dependency Security

#### npm audit
- **Purpose**: Node.js dependency vulnerability scanning
- **Configuration**: `.github/security/audit-ci.json`
- **Features**:
  - Vulnerability detection
  - License compliance
  - Dependency confusion protection

#### Safety (Python)
- **Purpose**: Python dependency vulnerability scanning
- **Configuration**: `.github/security/safety-policy.json`
- **Database**: Safety DB
- **Checks**: Known CVEs and security advisories

#### pip-audit
- **Purpose**: Python package vulnerability detection
- **Features**:
  - SBOM generation
  - CVE tracking
  - Fix recommendations

#### OWASP Dependency Check
- **Purpose**: Comprehensive dependency analysis
- **Configuration**: `.github/security/dependency-check-suppressions.xml`
- **Features**:
  - Multi-language support
  - NVD database integration
  - False positive suppression

### Container Security

#### Trivy
- **Purpose**: Container vulnerability scanning
- **Scanners**:
  - Vulnerabilities
  - Secrets
  - Misconfigurations
  - Licenses
- **Severity Levels**: Critical, High, Medium, Low

#### Grype
- **Purpose**: Container vulnerability detection
- **Features**:
  - Fast scanning
  - Multiple vulnerability databases
  - SBOM support

#### Hadolint
- **Purpose**: Dockerfile linting
- **Checks**:
  - Best practices
  - Security configurations
  - Optimization opportunities

#### Container Structure Tests
- **Purpose**: Container compliance validation
- **Configuration**: `.github/security/container-structure-*.yaml`
- **Tests**:
  - File existence
  - Permissions
  - User configuration
  - Security settings

### Infrastructure as Code (IaC) Security

#### tfsec
- **Purpose**: Terraform security scanning
- **Checks**:
  - AWS security best practices
  - Encryption requirements
  - Access controls

#### Checkov
- **Purpose**: Multi-framework IaC scanning
- **Frameworks**: Terraform, Kubernetes, Docker
- **Features**:
  - Policy as code
  - Compliance checking
  - Custom policies

#### Terrascan
- **Purpose**: IaC security validation
- **Support**: Terraform, Kubernetes, Docker
- **Policies**: 500+ built-in policies

#### KICS
- **Purpose**: Infrastructure as Code security
- **Languages**: Terraform, Kubernetes, Docker, CloudFormation
- **Queries**: 2000+ security queries

### Secret Scanning

#### Gitleaks
- **Purpose**: Git repository secret detection
- **Configuration**: `.github/security/gitleaks.toml`
- **Features**:
  - Custom patterns
  - Allowlisting
  - Historical scanning

#### TruffleHog
- **Purpose**: High-entropy secret detection
- **Features**:
  - Verified secrets
  - Git history scanning
  - Multiple secret types

#### detect-secrets
- **Purpose**: Pre-commit secret prevention
- **Configuration**: `.secrets.baseline`
- **Integration**: Pre-commit hooks

### Dynamic Application Security Testing (DAST)

#### OWASP ZAP
- **Purpose**: Web application security testing
- **Configuration**: `.github/security/zap-rules.tsv`
- **Scans**:
  - Baseline scan
  - Full scan
  - API scan

## Security Workflows

### 1. Security Scan Workflow
**File**: `.github/workflows/security-scan.yml`
**Trigger**: Push, PR, Daily schedule
**Components**:
- CodeQL analysis
- Language-specific security scans
- Dependency checking
- Container security
- Infrastructure security
- Secret scanning
- Compliance validation

### 2. Enhanced CI/CD Workflow
**File**: `.github/workflows/ci-cd-enhanced.yml`
**Features**:
- Pre-flight security checks
- Security gates
- Progressive security levels
- Post-deployment validation

## Security Gates and Thresholds

### Gate Configuration
```yaml
MAX_CRITICAL_ISSUES: 0
MAX_HIGH_ISSUES: 3
MAX_MEDIUM_ISSUES: 10
```

### Gate Logic
1. **Critical Issues**: Pipeline fails immediately
2. **High Issues**: Fails on main branch, warning on others
3. **Medium Issues**: Warning only
4. **Force Deploy**: Override option for emergencies

## Security Policies

### Container Security Policy
- Non-root user execution
- Read-only root filesystem
- No privileged containers
- Security capabilities dropped
- Health checks required

### Kubernetes Security Policy
- Pod Security Standards enforced
- Network policies required
- Resource limits mandatory
- Security contexts defined
- RBAC configured

### Dependency Management Policy
- All dependencies pinned to specific versions
- Regular dependency updates
- License compliance checking
- Vulnerability scanning before merge

### Secret Management Policy
- No secrets in code
- Environment variables for configuration
- Secrets rotation every 90 days
- Encrypted storage only
- Audit logging enabled

## Security Reporting

### Report Generation
- **HTML Report**: Comprehensive security findings
- **JSON Summary**: Machine-readable summary
- **SARIF Format**: IDE integration
- **PR Comments**: Automated PR feedback

### Report Contents
- Executive summary
- Findings by severity
- Tool-specific results
- Remediation recommendations
- Compliance status

## Compliance and Standards

### Standards Compliance
- OWASP Top 10
- CIS Benchmarks
- PCI DSS (where applicable)
- GDPR requirements
- SOC 2 controls

### Security Baselines
- Dockerfile best practices
- Kubernetes security standards
- Cloud security principles
- Zero-trust architecture

## Security Operations

### Monitoring
- Real-time security alerts
- Vulnerability tracking
- Compliance monitoring
- Incident response metrics

### Incident Response
1. **Detection**: Automated scanning and alerting
2. **Triage**: Severity assessment and prioritization
3. **Containment**: Immediate mitigation measures
4. **Remediation**: Fix implementation and testing
5. **Post-mortem**: Learning and improvement

### Security Maintenance
- Weekly dependency updates
- Monthly security reviews
- Quarterly penetration testing
- Annual security audits

## Developer Guidelines

### Secure Coding Practices
1. Input validation on all user inputs
2. Output encoding for XSS prevention
3. Parameterized queries for SQL injection prevention
4. Secure session management
5. Proper error handling without information disclosure

### Pre-commit Security
```bash
# Install pre-commit hooks
pre-commit install

# Run security checks locally
npm run security:check
uv run bandit -r socialmapper-api/
```

### Security Testing
```bash
# Run local security scan
make security-scan

# Check dependencies
npm audit
safety check

# Scan containers
trivy image socialmapper-api:latest
```

## Security Contacts

### Security Team
- **Security Lead**: security@socialmapper.com
- **Incident Response**: incident-response@socialmapper.com
- **Vulnerability Disclosure**: security@socialmapper.com

### Escalation Path
1. Development Team Lead
2. Security Team
3. CTO/Engineering Leadership
4. Executive Team (for critical incidents)

## Vulnerability Disclosure

### Responsible Disclosure Process
1. Report vulnerabilities to security@socialmapper.com
2. Include detailed description and proof of concept
3. Allow 90 days for remediation
4. Coordinated disclosure after fix

### Bug Bounty Program
- **Scope**: Production applications and infrastructure
- **Rewards**: Based on severity and impact
- **Rules**: No destructive testing, respect user privacy
- **Contact**: bugbounty@socialmapper.com

## Security Training

### Required Training
- OWASP Top 10 awareness
- Secure coding practices
- Security tool usage
- Incident response procedures

### Resources
- Internal security wiki
- Security champions program
- Monthly security workshops
- External security conferences

## Appendix

### Tool Installation

```bash
# Python security tools
pip install bandit safety pip-audit semgrep

# JavaScript security tools
npm install -g eslint-plugin-security snyk

# Container security tools
brew install trivy
brew install hadolint

# Infrastructure security tools
brew install tfsec
brew install checkov
```

### Quick Security Commands

```bash
# Full security scan
.github/scripts/run-security-scan.sh

# Python security
bandit -r socialmapper-api/
safety check

# JavaScript security
npm audit
npx eslint --ext .js,.ts,.tsx src/

# Container security
trivy image socialmapper-api:latest
hadolint Dockerfile

# Infrastructure security
tfsec infrastructure/terraform
checkov -d infrastructure/
```

### Security Checklist

- [ ] Code reviewed for security issues
- [ ] Dependencies scanned for vulnerabilities
- [ ] Secrets scanning passed
- [ ] Container security validated
- [ ] Infrastructure security checked
- [ ] Security tests passing
- [ ] Documentation updated
- [ ] Security gate approved

## Version History

- **v1.0.0** (2025-01-10): Initial comprehensive security implementation
- **v1.1.0** (Planned): Add runtime security monitoring
- **v1.2.0** (Planned): Implement security metrics dashboard

---

For questions or concerns about security, please contact the security team at security@socialmapper.com