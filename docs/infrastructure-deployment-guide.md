# SocialMapper Demo Platform - Infrastructure Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the SocialMapper demo platform infrastructure on AWS using Kubernetes (EKS), including monitoring, security, and CI/CD components.

## Architecture Overview

### Infrastructure Components

- **AWS EKS Cluster**: Managed Kubernetes cluster with auto-scaling node groups
- **VPC & Networking**: Private/public subnets with NAT gateways and security groups  
- **Application Load Balancer**: Layer 7 load balancer with SSL termination
- **CloudFront CDN**: Global content delivery network with WAF protection
- **ElastiCache Redis**: Session storage and caching
- **RDS PostgreSQL**: Persistent data storage (optional for demo)
- **ECR**: Container image registry
- **Monitoring Stack**: Prometheus, Grafana, and Alertmanager
- **Security**: Network policies, Pod security standards, and scanning

### Application Components

- **SocialMapper API**: FastAPI backend with analysis capabilities
- **UI Service**: Frontend interface (placeholder during Phase 1)
- **Redis**: Session management and caching
- **Monitoring**: Comprehensive observability stack

## Prerequisites

### Required Tools

```bash
# Install required tools
aws --version        # AWS CLI v2
kubectl version      # Kubernetes CLI
terraform --version  # Terraform >= 1.0
helm version         # Helm v3
docker --version     # Docker for local testing
```

### AWS Setup

1. **AWS Account** with appropriate permissions
2. **IAM User** with the following policies:
   - AmazonEKSClusterPolicy
   - AmazonEKSWorkerNodePolicy
   - AmazonEC2ContainerRegistryFullAccess
   - AmazonS3FullAccess (for Terraform state)
   - IAMFullAccess (for role creation)
   - VPCFullAccess

3. **Configure AWS CLI**:
```bash
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-east-1
# Default output format: json
```

### Required Secrets

Create these secrets before deployment:

```bash
# Census API Key (required for demographic analysis)
export CENSUS_API_KEY="your_census_api_key_here"

# Slack webhook for notifications (optional)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

## Deployment Process

### Phase 1: Infrastructure Setup

#### 1. Clone Repository and Prepare

```bash
git clone https://github.com/your-org/socialmapper.git
cd socialmapper
```

#### 2. Configure Deployment Parameters

Edit `infrastructure/terraform/terraform.tfvars`:

```hcl
# Basic Configuration
aws_region      = "us-east-1"
environment     = "production"
cluster_name    = "socialmapper"
domain_name     = "demo.socialmapper.com"

# SSL Certificate (get from ACM first)
cert_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."

# Node Groups for Different Workloads
node_groups = {
  main = {
    instance_types = ["t3.medium", "t3.large"]
    capacity_type  = "SPOT"
    min_size       = 2
    max_size       = 10
    desired_size   = 3
  }
  compute_intensive = {
    instance_types = ["c5.xlarge", "c5.2xlarge"] 
    capacity_type  = "SPOT"
    min_size       = 0
    max_size       = 5
    desired_size   = 0
  }
}

# Cost Optimization
redis_node_type = "cache.t3.micro"
rds_instance_class = "db.t3.micro"
```

#### 3. Run Automated Deployment

```bash
# Dry run to validate configuration
./scripts/deploy-infrastructure.sh --dry-run

# Deploy to production
./scripts/deploy-infrastructure.sh --environment production
```

### Phase 2: Manual Steps (if needed)

#### 1. SSL Certificate Setup

If not using existing certificate:

```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name demo.socialmapper.com \
  --validation-method DNS \
  --region us-east-1

# Follow validation process and update terraform.tfvars
```

#### 2. DNS Configuration

```bash
# Get CloudFront distribution domain
aws cloudfront list-distributions \
  --query 'DistributionList.Items[0].DomainName'

# Create DNS CNAME record
# demo.socialmapper.com -> d123xyz.cloudfront.net
```

#### 3. Application Secrets

Update Kubernetes secrets with real values:

```bash
kubectl create secret generic socialmapper-secrets \
  --from-literal=SOCIALMAPPER_API_CENSUS_API_KEY="$CENSUS_API_KEY" \
  --from-literal=REDIS_PASSWORD="$(openssl rand -base64 32)" \
  --namespace=socialmapper \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Phase 3: CI/CD Pipeline Setup

#### 1. GitHub Secrets

Add these secrets to your GitHub repository:

```
AWS_ACCESS_KEY_ID: [Your deployment key]
AWS_SECRET_ACCESS_KEY: [Your deployment secret]  
AWS_ACCOUNT_ID: [Your AWS account ID]
CENSUS_API_KEY: [Census Bureau API key]
SLACK_WEBHOOK_URL: [Slack notification webhook]
```

#### 2. ECR Repository Setup

```bash
# Create ECR repositories
aws ecr create-repository --repository-name socialmapper-api --region us-east-1
aws ecr create-repository --repository-name socialmapper-ui --region us-east-1
```

#### 3. Initial Image Push

```bash
# Build and push initial images
cd socialmapper-api
docker build -t socialmapper-api .
docker tag socialmapper-api:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socialmapper-api:latest

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/socialmapper-api:latest
```

## Monitoring and Observability

### Access Monitoring Dashboard

```bash
# Port forward to access Grafana locally
kubectl port-forward -n monitoring service/grafana 3000:3000

# Open http://localhost:3000
# Default credentials: admin/changeme123!
```

### Key Metrics to Monitor

1. **Application Metrics**
   - API request rate and response times
   - Error rates (4xx, 5xx)
   - Active user sessions
   - Database connection pool usage

2. **Infrastructure Metrics**  
   - Pod CPU/memory usage
   - Node resource utilization
   - Network traffic patterns
   - Storage usage

3. **Business Metrics**
   - Analysis requests per hour
   - Geographic distribution of users
   - Most popular features
   - Session duration

### Alerting Rules

Key alerts are configured for:
- High CPU/memory usage (>80%)
- API response time >5 seconds
- Error rate >5%
- Pod restart rate
- Storage space <10%

## Security Configuration

### Network Security

- **Network Policies**: Restrict inter-pod communication
- **Security Groups**: Control AWS-level network access
- **WAF Rules**: Protect against common attacks
- **VPC Isolation**: Private subnets for workloads

### Container Security  

- **Pod Security Standards**: Enforce restricted policies
- **Non-root Containers**: All containers run as non-root
- **Read-only Filesystems**: Minimize attack surface
- **Resource Limits**: Prevent resource exhaustion

### Monitoring Security

- **Falco Rules**: Runtime security monitoring
- **Image Scanning**: Vulnerability scanning with Trivy
- **Audit Logging**: Kubernetes audit logs
- **Network Monitoring**: Unusual network patterns

## Scaling Configuration

### Horizontal Pod Autoscaler (HPA)

```yaml
# API scaling based on CPU and memory
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      averageUtilization: 70
- type: Resource  
  resource:
    name: memory
    target:
      averageUtilization: 80
```

### Cluster Autoscaler

- **Node Groups**: Separate groups for different workloads
- **Spot Instances**: Cost optimization with spot pricing
- **Multi-AZ**: High availability across zones
- **Taints/Tolerations**: Workload isolation

### Traffic Management

- **CloudFront CDN**: Global edge caching
- **Application Load Balancer**: Layer 7 routing
- **Ingress Controller**: Kubernetes-native routing
- **Connection Pooling**: Efficient database connections

## Cost Optimization

### Current Architecture Costs (Estimated)

| Component | Monthly Cost (USD) | Notes |
|-----------|-------------------|-------|
| EKS Cluster | $75 | Managed control plane |
| EC2 Instances (Spot) | $200-400 | 2-10 nodes, spot pricing |
| RDS (t3.micro) | $15 | Small PostgreSQL instance |
| ElastiCache (t3.micro) | $12 | Redis instance |
| Load Balancer | $25 | Application Load Balancer |
| CloudFront | $10-50 | Based on traffic |
| Data Transfer | $20-100 | Based on usage |
| **Total** | **$357-677** | **Well under $2K budget** |

### Cost Optimization Strategies

1. **Spot Instances**: 60-70% cost savings on EC2
2. **Right-sizing**: Start small and scale based on usage
3. **Reserved Capacity**: For predictable workloads
4. **S3 Lifecycle Policies**: Automatic log archival
5. **CloudWatch Logs Retention**: Limited retention periods

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n socialmapper
kubectl logs <pod-name> -n socialmapper

# Check resource constraints
kubectl top pods -n socialmapper
```

#### 2. Network Connectivity

```bash
# Test service connectivity
kubectl exec -it <pod-name> -n socialmapper -- nslookup redis-service

# Check network policies
kubectl get networkpolicies -n socialmapper
```

#### 3. Certificate Issues

```bash
# Check certificate status
aws acm list-certificates --region us-east-1
kubectl get ingress -n socialmapper -o yaml
```

#### 4. Resource Limits

```bash
# Check resource quotas
kubectl describe resourcequota -n socialmapper

# Check node capacity
kubectl describe nodes
```

### Log Analysis

```bash
# Application logs
kubectl logs -f deployment/socialmapper-api -n socialmapper

# Infrastructure logs  
aws logs tail /aws/eks/socialmapper/cluster --follow

# ALB access logs
aws s3 ls s3://socialmapper-alb-logs/ --recursive
```

### Performance Debugging

```bash
# API performance testing
kubectl run curl-test --image=curlimages/curl -it --rm -- \
  curl -w "@curl-format.txt" https://demo.socialmapper.com/api/v1/health

# Resource utilization
kubectl top pods -n socialmapper --sort-by=cpu
kubectl top nodes --sort-by=memory
```

## Maintenance Procedures

### Regular Maintenance

1. **Weekly**:
   - Review monitoring alerts
   - Check security scan results
   - Update cost analysis

2. **Monthly**:
   - Update container images
   - Review resource utilization
   - Security policy audit

3. **Quarterly**:
   - Kubernetes version updates
   - Infrastructure security review
   - Disaster recovery testing

### Backup Procedures

```bash
# Backup Kubernetes configurations
kubectl get all,configmaps,secrets,pvc -n socialmapper -o yaml > backup.yaml

# Database backup (if using RDS)
aws rds create-db-snapshot \
  --db-instance-identifier socialmapper-postgres \
  --db-snapshot-identifier socialmapper-backup-$(date +%Y%m%d)
```

### Disaster Recovery

1. **Infrastructure**: Terraform state allows full recreation
2. **Application Data**: Redis is ephemeral, RDS has automated backups  
3. **Configuration**: GitOps approach with version control
4. **RTO/RPO**: ~15 minutes recovery time, <1 hour data loss

## Success Metrics

### Technical Metrics

- **Uptime**: >99.5% (Target: 99.9%)
- **Response Time**: <2 seconds global (Target: <10 seconds)  
- **Error Rate**: <1% (Target: <5%)
- **Scaling**: Handle 100+ concurrent users (Target: 500+)

### Operational Metrics

- **Deployment Time**: <5 minutes for application updates
- **Mean Time to Recovery**: <15 minutes
- **Security Scan**: Zero critical vulnerabilities
- **Cost**: <$700/month (Target: <$2000/month)

## Next Steps

1. **Phase 2**: Implement production UI interface
2. **Phase 3**: Advanced analytics and reporting
3. **Phase 4**: Multi-region deployment
4. **Phase 5**: Advanced security features (OIDC, RBAC)

## Support and Documentation

- **Repository**: https://github.com/your-org/socialmapper
- **API Documentation**: https://demo.socialmapper.com/api/docs  
- **Monitoring Dashboard**: https://monitoring.socialmapper.com
- **Issue Tracking**: GitHub Issues
- **Team Contact**: ops-team@socialmapper.com