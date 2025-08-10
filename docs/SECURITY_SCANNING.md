# Security Scanning Documentation

## Overview

SocialMapper implements comprehensive security scanning throughout the CI/CD pipeline to ensure the highest level of application security. Our multi-layered security approach covers static analysis, dependency scanning, container security, infrastructure validation, and runtime protection.

## Security Architecture

### Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  1. Code Security (SAST)                                     │
│     ├── CodeQL Analysis                                      │
│     ├── Semgrep Rules                                        │
│     ├── Bandit (Python)                                      │
│     └── ESLint Security (JavaScript/TypeScript)              │
├─────────────────────────────────────────────────────────────┤
│  2. Dependency Security                                      │
│     ├── npm audit & Safety                                   │
│     ├── OWASP Dependency Check                               │
│     ├── Snyk Vulnerability Scanning                          │
│     └── License Compliance                                   │
├─────────────────────────────────────────────────────────────┤
│  3. Container Security                                       │
│     ├── Trivy Scanning                                       │
│     ├── Grype Analysis                                       │
│     ├── Container Structure Tests                            │
│     └── Dockerfile Best Practices (Hadolint)                 │
├─────────────────────────────────────────────────────────────┤
│  4. Infrastructure Security                                  │
│     ├── Terraform Security (tfsec)                           │
│     ├── Checkov Policy Scanning                              │
│     ├── Kubernetes Security (Kubesec)                        │
│     └── Cloud Security Posture                               │
├─────────────────────────────────────────────────────────────┤
│  5. Secret Detection                                         │
│     ├── Gitleaks                                             │
│     ├── TruffleHog                                           │
│     └── Custom Pattern Matching                              │
├─────────────────────────────────────────────────────────────┤
│  6. Compliance & Governance                                  │
│     ├── OWASP Top 10                                         │
│     ├── CIS Benchmarks                                       │
│     ├── GDPR/HIPAA/PCI-DSS                                   │
│     └── Security Policy Enforcement                          │
└─────────────────────────────────────────────────────────────┘
```

## CI/CD Integration

### 1. Pull Request Security Checks

Every pull request triggers:
- **Fast Security Scan**: Quick vulnerability assessment
- **Secret Detection**: Prevents credential leaks
- **Dependency Audit**: Checks for vulnerable packages
- **Code Quality**: Security-focused linting

### 2. Main Branch Protection

Merges to main branch include:
- **Comprehensive Security Analysis**: Full SAST/DAST scanning
- **Container Security**: Image vulnerability scanning
- **Infrastructure Validation**: IaC security checks
- **Security Gate**: Blocks deployment if critical issues found

### 3. Scheduled Security Scans

Daily comprehensive scans:
- **Deep Vulnerability Analysis**: Extended scanning depth
- **Supply Chain Security**: SBOM generation and analysis
- **Compliance Checks**: Regulatory compliance validation
- **Penetration Testing**: Automated security testing

## Security Tools Configuration

### Static Application Security Testing (SAST)

#### CodeQL Configuration
```yaml
languages: [javascript-typescript, python]
queries: 
  - security-extended
  - security-and-quality
```

#### Semgrep Rulesets
- OWASP Top 10
- Security Audit
- Framework-specific rules (Flask, React)
- Custom rules for business logic

#### Bandit (Python)
```yaml
severity: medium
confidence: medium
exclude_dirs: [tests, venv]
```

### Dependency Security

#### npm Audit Configuration
```json
{
  "audit-level": "moderate",
  "production": true,
  "registry": "https://registry.npmjs.org"
}
```

#### Safety (Python)
```yaml
check: requirements.txt
ignore: []
output: json
```

### Container Security

#### Trivy Configuration
```yaml
severity: [CRITICAL, HIGH, MEDIUM]
scanners: [vuln, secret, config]
ignore-unfixed: false
```

#### Container Structure Tests
- Non-root user enforcement
- No sensitive files in images
- Security headers validation
- Minimal attack surface

### Infrastructure Security

#### tfsec Rules
- AWS security best practices
- Encryption at rest/transit
- IAM least privilege
- Network segmentation

#### Checkov Policies
```yaml
frameworks: [terraform, kubernetes, dockerfile]
skip-check: []
soft-fail: false
```

## Security Workflows

### 1. Enhanced CI/CD Workflow (`ci-cd.yml`)

Integrated security scanning in main pipeline:
```yaml
jobs:
  security-scan:
    - CodeQL analysis
    - Trivy filesystem scan
    - Semgrep security audit
    - Bandit Python analysis
    - Secret detection
    
  frontend-security:
    - npm audit with remediation
    - ESLint security plugins
    - License compliance
    - Bundle security analysis
    
  container-security:
    - Multi-stage scanning
    - SBOM generation
    - Runtime configuration validation
```

### 2. Comprehensive Security Workflow (`comprehensive-security.yml`)

Deep security analysis on schedule/demand:
```yaml
jobs:
  advanced-sast:
    - SonarCloud analysis
    - Custom security rules
    - Cross-site scripting detection
    
  supply-chain-security:
    - SBOM generation
    - Dependency confusion checks
    - Package integrity verification
    
  runtime-security:
    - DAST with OWASP ZAP
    - API security testing
    - Nuclei vulnerability scanning
    
  cloud-security:
    - AWS Security Hub
    - Prowler scanning
    - ScoutSuite audit
    
  compliance-governance:
    - GDPR compliance
    - HIPAA validation
    - PCI-DSS checks
    - SOC 2 assessment
    
  penetration-testing:
    - Automated pen testing
    - SQL injection testing
    - XSS vulnerability scanning
```

## Security Gates and Thresholds

### Build Blocking Criteria

The build will fail if:
- **Critical vulnerabilities** detected
- **Secrets** found in code
- **High-risk dependencies** identified
- **Security score** < 50/100

### Security Score Calculation

```python
Score = 100 - (
    critical_issues * 40 +
    high_issues * 30 +
    medium_issues * 20 +
    low_issues * 10
) / max_possible_weight * 100
```

### Deployment Gates

| Environment | Minimum Score | Additional Requirements |
|------------|---------------|------------------------|
| Development | 50 | No critical issues |
| Staging | 70 | No critical/high issues |
| Production | 85 | Manual approval for < 90 |

## Security Reporting

### Report Types

1. **Pull Request Comments**: Summary of security findings
2. **SARIF Upload**: GitHub Security tab integration
3. **HTML Dashboard**: Comprehensive visual report
4. **JSON Metrics**: Machine-readable metrics
5. **PDF Reports**: Executive summaries

### Metrics Tracked

- Total vulnerabilities by severity
- Secret detection count
- License compliance status
- Container security posture
- Infrastructure misconfigurations
- Dependency vulnerabilities
- Code quality issues
- Compliance violations

### Notifications

- **Slack**: Critical security alerts
- **Email**: Daily security summaries
- **GitHub Issues**: Automated issue creation
- **PagerDuty**: Production security incidents

## Security Best Practices

### For Developers

1. **Pre-commit Hooks**: Run security checks locally
2. **IDE Integration**: Security plugins for real-time feedback
3. **Secure Coding**: Follow OWASP guidelines
4. **Dependency Management**: Regular updates and audits
5. **Secret Management**: Use environment variables and vaults

### For DevOps

1. **Infrastructure as Code**: Version control all configurations
2. **Least Privilege**: Minimal permissions for services
3. **Network Segmentation**: Isolated environments
4. **Encryption**: At rest and in transit
5. **Monitoring**: Real-time security monitoring

## Remediation Process

### Priority Levels

| Severity | SLA | Action Required |
|----------|-----|----------------|
| Critical | 24 hours | Immediate patch or rollback |
| High | 1 week | Priority fix in current sprint |
| Medium | 1 month | Schedule for next release |
| Low | 3 months | Include in technical debt backlog |

### Remediation Workflow

1. **Detection**: Automated scanning identifies issue
2. **Triage**: Security team assesses impact
3. **Assignment**: Issue assigned to responsible team
4. **Fix**: Developer implements remediation
5. **Verification**: Automated re-scan confirms fix
6. **Documentation**: Update security knowledge base

## False Positive Management

### Suppression Rules

Located in `.github/security/`:
- `dependency-check-suppressions.xml`: OWASP suppressions
- `gitleaks.toml`: Secret scanning allowlist
- `.semgrepignore`: Semgrep exclusions

### Suppression Process

1. Verify false positive status
2. Document reasoning
3. Add suppression with expiry date
4. Review suppressions quarterly

## Continuous Improvement

### Security Metrics Review

Monthly review of:
- Security score trends
- Vulnerability introduction rate
- Mean time to remediation
- False positive rate
- Tool effectiveness

### Tool Updates

- Weekly rule updates for scanners
- Monthly tool version updates
- Quarterly security tool evaluation
- Annual security architecture review

## Emergency Response

### Security Incident Response

1. **Detection**: Automated or manual discovery
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove security threat
4. **Recovery**: Restore normal operations
5. **Lessons Learned**: Post-incident review

### Contact Information

- **Security Team**: security@socialmapper.com
- **On-Call**: PagerDuty rotation
- **Escalation**: CTO/CISO for critical incidents

## Compliance and Auditing

### Audit Trail

All security events logged with:
- Timestamp
- Actor (user/system)
- Action performed
- Result/outcome
- Related artifacts

### Compliance Reports

Generated monthly:
- OWASP Top 10 compliance
- CIS Benchmark adherence
- Regulatory compliance status
- Security KPI dashboard

## Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Training
- Security awareness training (quarterly)
- Secure coding workshops
- Tool-specific training sessions
- Incident response drills

### Support
- Internal wiki: security.wiki.socialmapper.com
- Slack channel: #security
- Security office hours: Wednesdays 2-3 PM