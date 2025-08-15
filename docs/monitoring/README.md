# SocialMapper Monitoring and Observability Documentation

This documentation covers the comprehensive monitoring and observability infrastructure for the SocialMapper project, including Prometheus, Grafana, AlertManager, and performance monitoring systems.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Components](#components)
5. [Deployment](#deployment)
6. [Configuration](#configuration)
7. [Dashboards](#dashboards)
8. [Alerting](#alerting)
9. [Troubleshooting](#troubleshooting)
10. [Cost Optimization](#cost-optimization)
11. [Security](#security)
12. [Maintenance](#maintenance)

## Overview

The SocialMapper monitoring stack provides comprehensive observability for the entire application ecosystem, including:

- **Application Metrics**: FastAPI backend and React frontend performance
- **Infrastructure Metrics**: Kubernetes cluster and node health
- **Business Metrics**: Analysis success rates, user engagement, and feature usage
- **Security Monitoring**: Error tracking and anomaly detection
- **Cost Optimization**: Resource usage and cost management

### Key Features

- 🔍 **Real-time Monitoring**: Sub-second metric collection and alerting
- 📊 **Rich Dashboards**: Pre-built dashboards for all system components
- 🚨 **Smart Alerting**: Intelligent escalation with context-aware notifications
- 💰 **Cost Optimization**: Automated resource scaling and cost management
- 🔒 **Security Focused**: Built-in security scanning and compliance monitoring
- 🚀 **Production Ready**: High availability, backup, and disaster recovery

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    External Access Layer                    │
├─────────────────────────────────────────────────────────────┤
│  Grafana UI  │  Prometheus UI  │  AlertManager UI          │
│  Port: 3000  │  Port: 9090     │  Port: 9093               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Monitoring Stack                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │ Prometheus  │  │   Grafana    │  │  AlertManager   │     │
│  │ (Metrics)   │  │ (Dashboards) │  │  (Alerting)     │     │
│  └─────────────┘  └──────────────┘  └─────────────────┘     │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │ kube-state-     │  │       Node Exporter            │   │
│  │ metrics         │  │    (System Metrics)            │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐            ┌─────────────────────────┐ │
│  │ SocialMapper    │            │  SocialMapper Frontend │ │
│  │ FastAPI Backend │  ◄──────►  │  React Application     │ │
│  │ /metrics        │            │  Web Vitals            │ │
│  └─────────────────┘            └─────────────────────────┘ │
│                                                             │
│  ┌─────────────────┐            ┌─────────────────────────┐ │
│  │     Redis       │            │      PostgreSQL        │ │
│  │   (Caching)     │            │     (Database)         │ │
│  └─────────────────┘            └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Metric Collection**: Prometheus scrapes metrics from all application and infrastructure components
2. **Data Storage**: Metrics are stored in Prometheus with configurable retention policies
3. **Visualization**: Grafana queries Prometheus and presents data in interactive dashboards
4. **Alerting**: AlertManager receives alerts from Prometheus and routes them based on severity and time
5. **Notification**: Alerts are sent via multiple channels (Slack, email, PagerDuty) with intelligent escalation

## Getting Started

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm 3.12+
- Docker (for building custom images)
- AWS CLI configured (for AWS deployments)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/socialmapper.git
   cd socialmapper
   ```

2. **Deploy using Helm**:
   ```bash
   # Add required Helm repositories
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   
   # Install the monitoring stack
   helm install socialmapper-monitoring ./helm/socialmapper-monitoring \
     --namespace monitoring \
     --create-namespace \
     --values ./helm/socialmapper-monitoring/values-production.yaml
   ```

3. **Verify deployment**:
   ```bash
   kubectl get pods -n monitoring
   kubectl get services -n monitoring
   ```

4. **Access dashboards**:
   - Grafana: https://monitoring.socialmapper.com
   - Prometheus: https://prometheus.socialmapper.com  
   - AlertManager: https://alertmanager.socialmapper.com

### Alternative: Manual Deployment

If you prefer manual deployment using kubectl:

```bash
# Create namespace
kubectl apply -f infrastructure/monitoring/namespace.yaml

# Deploy core components
kubectl apply -f infrastructure/monitoring/prometheus.yaml
kubectl apply -f infrastructure/monitoring/kube-state-metrics.yaml
kubectl apply -f infrastructure/monitoring/grafana.yaml
kubectl apply -f infrastructure/monitoring/grafana-dashboards.yaml
kubectl apply -f infrastructure/monitoring/enhanced-alertmanager.yaml

# Apply cost optimization
kubectl apply -f infrastructure/monitoring/cost-optimization.yaml
```

## Components

### Prometheus

**Purpose**: Metrics collection and storage
**Port**: 9090
**Configuration**: `/Users/mihiarc/repos/socialmapper/infrastructure/monitoring/prometheus.yaml`

Key features:
- 15-second scrape interval for real-time monitoring
- 15-day retention period with compression
- Multi-target service discovery
- Custom recording rules for efficient queries
- Built-in alerting rules

**Metrics Collected**:
- HTTP request metrics (rate, duration, errors)
- Business metrics (analysis success rates, queue depth)
- System metrics (CPU, memory, disk, network)
- Custom application metrics

### Grafana

**Purpose**: Visualization and dashboards
**Port**: 3000
**Configuration**: `/Users/mihiarc/repos/socialmapper/infrastructure/monitoring/grafana.yaml`

**Pre-built Dashboards**:
- **Application Overview**: Request rates, response times, error rates
- **Business Metrics**: Analysis success rates, user engagement, feature usage
- **Infrastructure**: Cluster health, resource utilization, capacity planning
- **Performance**: Web Vitals, frontend performance, API performance

**Access**: 
- URL: https://monitoring.socialmapper.com
- Default credentials: admin/changeme123! (change in production)

### AlertManager

**Purpose**: Alert routing and notification management
**Port**: 9093
**Configuration**: `/Users/mihiarc/repos/socialmapper/infrastructure/monitoring/enhanced-alertmanager.yaml`

**Features**:
- Smart escalation policies
- Business hours vs off-hours routing
- Multi-channel notifications (Slack, email, PagerDuty)
- Alert grouping and inhibition rules
- Template-based notifications

### kube-state-metrics

**Purpose**: Kubernetes object metrics
**Port**: 8080
**Configuration**: `/Users/mihiarc/repos/socialmapper/infrastructure/monitoring/kube-state-metrics.yaml`

Provides metrics about Kubernetes objects like pods, deployments, services, and nodes.

### Node Exporter

**Purpose**: System-level metrics
**Port**: 9100
**Deployment**: DaemonSet on all nodes

Collects hardware and OS metrics from each node in the cluster.

## Deployment

### Production Deployment

1. **Configure secrets**:
   ```bash
   # Create monitoring secrets
   kubectl create secret generic monitoring-secrets \
     --from-literal=grafana-admin-password='your-secure-password' \
     --from-literal=smtp-password='your-smtp-password' \
     --from-literal=slack-webhook-url='your-slack-webhook' \
     --from-literal=pagerduty-service-key='your-pagerduty-key' \
     --namespace monitoring
   ```

2. **Update values for production**:
   ```yaml
   # values-production.yaml
   global:
     environment: production
     domain: socialmapper.com
   
   prometheus:
     server:
       replicas: 2
       resources:
         requests:
           memory: "2Gi"
           cpu: "1"
         limits:
           memory: "4Gi"
           cpu: "2"
       storage:
         size: 100Gi
   
   grafana:
     replicas: 2
     adminPassword: ""  # Will use secret
   
   alertmanager:
     replicas: 2
   ```

3. **Deploy with GitHub Actions**:
   
   The repository includes automated deployment via GitHub Actions. Push to the main branch to trigger production deployment:
   
   ```bash
   git push origin main
   ```
   
   Or manually trigger deployment:
   ```bash
   gh workflow run deploy-monitoring.yml \
     --ref main \
     --field environment=production \
     --field monitoring_components=all
   ```

### Staging Deployment

For staging environment:

```bash
helm install socialmapper-monitoring-staging ./helm/socialmapper-monitoring \
  --namespace monitoring-staging \
  --create-namespace \
  --values ./helm/socialmapper-monitoring/values-staging.yaml
```

### Development Deployment

For local development:

```bash
# Use reduced resource requirements
helm install socialmapper-monitoring-dev ./helm/socialmapper-monitoring \
  --namespace monitoring-dev \
  --create-namespace \
  --values ./helm/socialmapper-monitoring/values-development.yaml
```

## Configuration

### Environment-Specific Configuration

The monitoring stack supports multiple environments with different resource allocations:

| Environment | CPU Request | Memory Request | Storage Size | Retention |
|-------------|-------------|----------------|--------------|-----------|
| Development | 0.5 cores   | 1 GB          | 10 GB       | 3 days    |
| Staging     | 1.5 cores   | 4 GB          | 30 GB       | 7 days    |
| Production  | 4 cores     | 8 GB          | 100 GB      | 15 days   |

### Custom Configuration

#### Adding New Metrics

1. **Application Metrics** (FastAPI):
   ```python
   from api_server.middleware.metrics import get_business_metrics
   
   metrics = get_business_metrics()
   metrics.record_analysis_completion("poi_discovery", "success", 45.2)
   ```

2. **Custom Prometheus Rules**:
   ```yaml
   # Add to prometheus.yaml
   - alert: CustomBusinessMetric
     expr: my_business_metric > 100
     for: 5m
     labels:
       severity: warning
     annotations:
       summary: "Custom metric exceeded threshold"
   ```

3. **New Grafana Dashboard**:
   Create JSON dashboard and add to `grafana-dashboards.yaml`

#### Modifying Alert Rules

Edit `/Users/mihiarc/repos/socialmapper/infrastructure/monitoring/prometheus.yaml`:

```yaml
- alert: HighAPIErrorRate
  expr: |
    (
      rate(fastapi_requests_total{job="socialmapper-api",status=~"5.."}[5m])
      /
      rate(fastapi_requests_total{job="socialmapper-api"}[5m])
    ) * 100 > 5
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "API error rate is {{ $value }}%"
    runbook_url: "https://docs.socialmapper.com/runbooks/high-error-rate"
```

## Dashboards

### Available Dashboards

1. **SocialMapper - Application Overview**
   - Request rates by endpoint
   - Response time percentiles
   - Error rates (4xx, 5xx)
   - API performance trends

2. **SocialMapper - Business Metrics**
   - Analysis success rates
   - Queue depth and processing times
   - User engagement metrics
   - Feature usage statistics

3. **SocialMapper - Infrastructure Metrics**
   - Cluster resource utilization
   - Node health and capacity
   - Pod status and restart rates
   - Storage usage trends

4. **Kubernetes Cluster Overview**
   - Cluster-wide resource usage
   - Pod distribution by namespace
   - Network traffic patterns
   - Storage utilization

### Dashboard Management

**Import Custom Dashboard**:
1. Create dashboard JSON file
2. Add to ConfigMap in `grafana-dashboards.yaml`
3. Redeploy Grafana

**Dashboard Best Practices**:
- Use template variables for filtering
- Set appropriate refresh intervals (30s for real-time, 5m for historical)
- Include links to related dashboards
- Add annotations for important events

## Alerting

### Alert Severity Levels

| Severity | Response Time | Escalation | Examples |
|----------|---------------|------------|----------|
| Critical | Immediate | PagerDuty + Slack + Email | API down, High error rate |
| Warning | 15 minutes | Slack + Email | High CPU, Slow responses |
| Info | Best effort | Slack only | Deployment events |

### Alert Routing

Alerts are routed based on:
- **Severity**: Critical alerts get immediate attention
- **Time**: Different routing for business hours vs off-hours  
- **Component**: API alerts go to API team, infrastructure alerts to ops team
- **Environment**: Production alerts have higher priority than staging

### Notification Channels

1. **Slack**:
   - #alerts-critical (Critical alerts)
   - #alerts-warning (Warning alerts)
   - #alerts-off-hours (Off-hours alerts)

2. **Email**:
   - ops-team@socialmapper.com (Critical/Warning)
   - dev-team@socialmapper.com (Application alerts)
   - infra-team@socialmapper.com (Infrastructure alerts)

3. **PagerDuty**:
   - Critical alerts only
   - 24/7 escalation policy

### Alert Inhibition

Smart inhibition rules prevent alert spam:
- Critical alerts suppress related warnings
- Node down alerts suppress node-specific alerts
- Service down alerts suppress service-specific alerts

### Creating Custom Alerts

1. **Define the alert rule**:
   ```yaml
   - alert: MyCustomAlert
     expr: my_metric > threshold
     for: 5m
     labels:
       severity: warning
       team: platform
     annotations:
       summary: "My custom alert fired"
       description: "Value is {{ $value }}"
       runbook_url: "https://wiki.company.com/my-runbook"
   ```

2. **Add routing rule** (if needed):
   ```yaml
   routes:
   - match:
       alertname: MyCustomAlert
     receiver: custom-team-alerts
   ```

3. **Create receiver**:
   ```yaml
   receivers:
   - name: custom-team-alerts
     slack_configs:
     - channel: '#my-team'
       title: 'Custom Alert'
   ```

## Troubleshooting

### Common Issues

#### Prometheus Not Collecting Metrics

**Symptoms**: Missing metrics in Grafana dashboards

**Troubleshooting**:
1. Check Prometheus targets:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   # Visit http://localhost:9090/targets
   ```

2. Verify service discovery:
   ```bash
   kubectl get endpoints -n monitoring
   kubectl get services -n monitoring
   ```

3. Check pod logs:
   ```bash
   kubectl logs -n monitoring deployment/prometheus
   ```

**Common fixes**:
- Ensure services have correct labels and annotations
- Verify network policies allow traffic
- Check if metrics endpoint is accessible

#### Grafana Dashboard Showing No Data

**Symptoms**: Dashboard panels show "No data"

**Troubleshooting**:
1. Check Prometheus data source:
   - Go to Grafana → Configuration → Data Sources
   - Test the Prometheus connection

2. Verify query syntax:
   - Use Prometheus UI to test queries
   - Check metric names and labels

3. Check time range:
   - Ensure time range covers period with data
   - Verify timezone settings

#### AlertManager Not Sending Notifications

**Symptoms**: Alerts showing in Prometheus but no notifications received

**Troubleshooting**:
1. Check AlertManager config:
   ```bash
   kubectl logs -n monitoring deployment/enhanced-alertmanager
   ```

2. Verify webhook URLs and credentials:
   ```bash
   kubectl get secret -n monitoring enhanced-alertmanager-secret -o yaml
   ```

3. Test notification channels manually:
   - Send test Slack message
   - Verify email configuration

#### High Resource Usage

**Symptoms**: Monitoring components using excessive CPU/memory

**Troubleshooting**:
1. Check resource usage:
   ```bash
   kubectl top pods -n monitoring
   ```

2. Analyze queries and cardinality:
   ```bash
   # Check high cardinality metrics
   kubectl exec -n monitoring deployment/prometheus -- \
     promtool query instant 'prometheus_tsdb_symbol_table_size_bytes'
   ```

3. Optimize configuration:
   - Reduce scrape intervals for non-critical metrics
   - Add recording rules for expensive queries
   - Filter high-cardinality metrics

### Performance Optimization

#### Query Optimization

1. **Use recording rules** for expensive queries:
   ```yaml
   recording_rules:
     - record: socialmapper:request_rate_5m
       expr: sum(rate(fastapi_requests_total[5m])) by (job, method)
   ```

2. **Reduce query range** in dashboards:
   - Use shorter time ranges when possible
   - Limit data points (max 1000-2000)

3. **Optimize PromQL queries**:
   ```yaml
   # Good: Specific label matching
   http_requests_total{job="socialmapper-api", method="POST"}
   
   # Avoid: Expensive regex
   http_requests_total{job=~".*api.*", method=~"POST|PUT"}
   ```

#### Storage Optimization

1. **Configure retention policies**:
   ```yaml
   prometheus:
     retention: "15d"  # Keep 15 days of data
     retentionSize: "50GB"  # Or size-based retention
   ```

2. **Use external storage** for long-term data:
   - Configure Prometheus remote write to S3
   - Use Thanos for long-term storage

3. **Compress data**:
   ```yaml
   prometheus:
     config:
       storage:
         tsdb:
           compression: "snappy"
   ```

### Health Checks

#### Monitoring Stack Health

Create a monitoring health check script:

```bash
#!/bin/bash
# health-check.sh

echo "Checking Prometheus..."
if curl -s http://prometheus.monitoring.svc.cluster.local:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is unhealthy"
fi

echo "Checking Grafana..."
if curl -s http://grafana.monitoring.svc.cluster.local:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is unhealthy"
fi

echo "Checking AlertManager..."
if curl -s http://enhanced-alertmanager.monitoring.svc.cluster.local:9093/-/healthy > /dev/null; then
    echo "✅ AlertManager is healthy"
else
    echo "❌ AlertManager is unhealthy"
fi
```

## Cost Optimization

The monitoring stack includes several cost optimization features:

### Resource Scaling

**Horizontal Pod Autoscaler (HPA)**:
- Automatically scales pods based on CPU/memory usage
- Prometheus: 1-3 replicas, scales at 70% CPU
- Grafana: 1-3 replicas, scales at 80% CPU

**Resource Efficiency**:
- Development: 50% of production resources
- Staging: 70% of production resources
- Production: Full resources with auto-scaling

### Storage Optimization

**Tiered Storage**:
- Hot data (2 days): Fast SSD storage
- Warm data (7 days): Standard storage
- Cold data (15 days): Cheap storage with compression

**Data Retention**:
- Automatic cleanup of old data
- Configurable retention per environment
- Metric sampling for less critical data

### Query Optimization

**Recording Rules**:
Pre-compute expensive queries to reduce resource usage:

```yaml
recording_rules:
  - record: socialmapper:api_request_rate_5m
    expr: sum(rate(fastapi_requests_total[5m])) by (method, status)
    
  - record: socialmapper:error_rate_5m
    expr: sum(rate(fastapi_requests_total{status=~"5.."}[5m])) / sum(rate(fastapi_requests_total[5m]))
```

### Cost Monitoring

Track monitoring costs with built-in metrics:
- Resource usage by component
- Storage costs by data type
- Query costs by dashboard/user

## Security

### Network Security

**Network Policies**: Restrict traffic between components
- Monitoring namespace isolation
- Allow traffic only on required ports
- Deny all by default with explicit allow rules

**TLS/SSL**:
- All external traffic encrypted with TLS
- Internal service-to-service encryption available
- Certificate management via cert-manager

### Access Control

**Authentication**:
- Basic auth for web interfaces
- Integration with OAuth providers (optional)
- Service account-based API access

**Authorization**:
- RBAC for Kubernetes resources
- Grafana role-based access control
- API key management for external integrations

### Data Security

**Sensitive Data**:
- Secrets management via Kubernetes secrets
- No sensitive data in logs or metrics
- PII scrubbing for user-related metrics

**Compliance**:
- Audit logging enabled
- Data retention policies
- GDPR compliance features

## Maintenance

### Regular Tasks

#### Daily
- Monitor alert fatigue (excessive alerting)
- Review dashboard performance
- Check resource usage trends

#### Weekly
- Review and tune alert thresholds
- Update dashboard queries
- Analyze cost trends

#### Monthly
- Review retention policies
- Update monitoring stack versions
- Conduct disaster recovery tests

### Backup and Disaster Recovery

**Data Backup**:
```bash
# Backup Prometheus data
kubectl exec -n monitoring prometheus-0 -- tar czf /tmp/prometheus-backup.tar.gz /prometheus

# Backup Grafana dashboards and config
kubectl get configmaps -n monitoring -o yaml > grafana-backup.yaml
```

**Disaster Recovery**:
1. **Prometheus**: Data is stored on persistent volumes with automated backups
2. **Grafana**: Configuration and dashboards backed up to Git
3. **AlertManager**: Configuration stored in version control

**Recovery Testing**:
- Monthly disaster recovery drills
- Automated backup verification
- RTO/RPO testing and documentation

### Updates and Upgrades

**Update Process**:
1. Test updates in development environment
2. Deploy to staging for validation
3. Schedule maintenance window for production
4. Deploy with rolling updates (zero-downtime)
5. Monitor for issues and rollback if needed

**Version Management**:
- Use semantic versioning for chart releases
- Pin component versions in production
- Automated security updates for non-breaking changes

### Monitoring the Monitoring

**Meta-monitoring**:
- Monitor Prometheus query performance
- Track Grafana dashboard load times
- AlertManager notification success rates
- Monitor monitoring stack resource usage

**SLIs/SLOs**:
- Prometheus uptime: 99.9%
- Query response time: <2s (95th percentile)
- Alert delivery time: <30s
- Dashboard load time: <3s

---

## Support and Contributing

### Getting Help

1. **Documentation**: Check this guide and component-specific docs
2. **Issues**: Open GitHub issues for bugs or feature requests
3. **Discussions**: Use GitHub Discussions for questions
4. **Team Contact**: reach out to the platform team

### Contributing

1. Fork the repository
2. Create feature branch
3. Test changes thoroughly
4. Submit pull request with description
5. Ensure CI/CD passes

### Runbooks

Detailed troubleshooting guides are available at:
- [High CPU Usage Runbook](https://docs.socialmapper.com/runbooks/high-cpu-usage)
- [High Memory Usage Runbook](https://docs.socialmapper.com/runbooks/high-memory-usage)
- [High API Error Rate Runbook](https://docs.socialmapper.com/runbooks/high-error-rate)
- [Analysis Failures Runbook](https://docs.socialmapper.com/runbooks/analysis-failures)

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Maintainers**: SocialMapper Platform Team