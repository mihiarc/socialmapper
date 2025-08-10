#!/bin/bash
# SocialMapper Monitoring Setup Script
# Sets up comprehensive monitoring and alerting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE=${MONITORING_NAMESPACE:-"monitoring"}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-"changeme123!"}
ALERT_EMAIL=${ALERT_EMAIL:-"ops@socialmapper.com"}
SLACK_WEBHOOK=${SLACK_WEBHOOK:-""}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! kubectl cluster-info &>/dev/null; then
        error "Cannot access Kubernetes cluster"
    fi
    
    if ! helm version &>/dev/null; then
        error "Helm is required but not installed"
    fi
    
    log "Prerequisites check completed"
}

setup_monitoring_namespace() {
    log "Setting up monitoring namespace..."
    
    kubectl create namespace "$MONITORING_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Label namespace for network policies
    kubectl label namespace "$MONITORING_NAMESPACE" name="$MONITORING_NAMESPACE" --overwrite
    
    log "Monitoring namespace ready"
}

install_prometheus_operator() {
    log "Installing Prometheus Operator..."
    
    # Add Prometheus Community Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Create values file for Prometheus Operator
    cat > /tmp/prometheus-operator-values.yaml << EOF
prometheus:
  prometheusSpec:
    retention: 15d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    
    # Service monitor selector
    serviceMonitorSelectorNilUsesHelmValues: false
    serviceMonitorSelector: {}
    serviceMonitorNamespaceSelector: {}
    
    # Pod monitor selector  
    podMonitorSelectorNilUsesHelmValues: false
    podMonitorSelector: {}
    podMonitorNamespaceSelector: {}
    
    # Rule selector
    ruleSelectorNilUsesHelmValues: false
    ruleSelector: {}
    ruleNamespaceSelector: {}

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 5Gi

grafana:
  enabled: true
  adminPassword: "$GRAFANA_ADMIN_PASSWORD"
  
  persistence:
    enabled: true
    storageClassName: gp3
    size: 10Gi
  
  plugins:
    - grafana-piechart-panel
    - grafana-worldmap-panel
    - grafana-clock-panel
  
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
      - name: 'default'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        editable: true
        options:
          path: /var/lib/grafana/dashboards/default

  dashboards:
    default:
      kubernetes-cluster:
        gnetId: 7249
        revision: 1
        datasource: Prometheus
      kubernetes-pods:
        gnetId: 6336
        revision: 1  
        datasource: Prometheus
      redis:
        gnetId: 763
        revision: 1
        datasource: Prometheus

nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true

defaultRules:
  create: true
  rules:
    alertmanager: true
    etcd: true
    configReloaders: true
    general: true
    k8s: true
    kubeApiserver: true
    kubeApiserverAvailability: true
    kubeApiserverSlos: true
    kubelet: true
    kubeProxy: true
    kubePrometheusGeneral: true
    kubePrometheusNodeRecording: true
    kubernetesApps: true
    kubernetesResources: true
    kubernetesStorage: true
    kubernetesSystem: true
    node: true
    nodeExporterAlerting: true
    nodeExporterRecording: true
    prometheus: true
    prometheusOperator: true
EOF

    # Install or upgrade
    helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace "$MONITORING_NAMESPACE" \
        --values /tmp/prometheus-operator-values.yaml \
        --wait
    
    log "Prometheus Operator installed successfully"
}

configure_alertmanager() {
    log "Configuring Alertmanager..."
    
    # Create Alertmanager configuration
    cat > /tmp/alertmanager-config.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-prometheus-stack-kube-prom-alertmanager
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: alertmanager
stringData:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'smtp.gmail.com:587'
      smtp_from: '$ALERT_EMAIL'
      smtp_auth_username: '$ALERT_EMAIL'
      smtp_auth_password: 'your-app-password'
      
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h
      receiver: 'web.hook'
      routes:
      - match:
          severity: critical
        receiver: critical-alerts
        group_wait: 10s
        repeat_interval: 1h
      - match:
          severity: warning  
        receiver: warning-alerts
        repeat_interval: 4h

    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://localhost:5001/'
        send_resolved: true

    - name: 'critical-alerts'
      email_configs:
      - to: '$ALERT_EMAIL'
        subject: '🚨 CRITICAL Alert - SocialMapper {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          Instance: {{ .Labels.instance }}
          Time: {{ .StartsAt }}
          {{ end }}
        headers:
          Priority: 'urgent'
      
      slack_configs:
      - api_url: '$SLACK_WEBHOOK'
        channel: '#alerts-critical'
        title: '🚨 CRITICAL Alert - SocialMapper'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}  
          *Severity:* {{ .Labels.severity }}
          *Instance:* {{ .Labels.instance }}
          {{ end }}
        send_resolved: true

    - name: 'warning-alerts'
      email_configs:
      - to: '$ALERT_EMAIL'
        subject: '⚠️ Warning Alert - SocialMapper {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          {{ end }}

    inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'dev', 'instance']
EOF

    kubectl apply -f /tmp/alertmanager-config.yaml
    
    log "Alertmanager configured"
}

create_socialmapper_monitoring() {
    log "Creating SocialMapper specific monitoring rules..."
    
    # Create PrometheusRule for SocialMapper
    cat > /tmp/socialmapper-rules.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: socialmapper-rules
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: socialmapper
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: socialmapper.rules
    rules:
    - alert: SocialMapperAPIDown
      expr: up{job="socialmapper-api"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "SocialMapper API is down"
        description: "SocialMapper API has been down for more than 1 minute."

    - alert: SocialMapperHighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="socialmapper-api"}[5m])) > 5
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High API response time"
        description: "95th percentile response time is {{ \$value }} seconds."

    - alert: SocialMapperHighErrorRate
      expr: |
        (
          rate(http_requests_total{job="socialmapper-api",status=~"5.."}[5m]) /
          rate(http_requests_total{job="socialmapper-api"}[5m])
        ) * 100 > 5
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "High API error rate"
        description: "API error rate is {{ \$value }}% for more than 2 minutes."

    - alert: SocialMapperRedisDown
      expr: up{job="redis"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Redis is down"
        description: "Redis instance is not responding."

    - alert: SocialMapperHighMemoryUsage
      expr: |
        (
          container_memory_usage_bytes{namespace="socialmapper", pod=~"socialmapper-api-.*"} / 
          container_spec_memory_limit_bytes{namespace="socialmapper", pod=~"socialmapper-api-.*"}
        ) * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage in API pods"
        description: "Memory usage is {{ \$value }}% for pod {{ \$labels.pod }}."

    - alert: SocialMapperPodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total{namespace="socialmapper"}[15m]) > 0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Pod crash looping"
        description: "Pod {{ \$labels.pod }} is crash looping."

    - alert: SocialMapperPVCAlmostFull
      expr: |
        (
          kubelet_volume_stats_used_bytes{namespace="socialmapper"} / 
          kubelet_volume_stats_capacity_bytes{namespace="socialmapper"}
        ) * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "PVC almost full"
        description: "PVC {{ \$labels.persistentvolumeclaim }} is {{ \$value }}% full."
EOF

    kubectl apply -f /tmp/socialmapper-rules.yaml
    
    log "SocialMapper monitoring rules created"
}

setup_service_monitors() {
    log "Setting up ServiceMonitors..."
    
    # SocialMapper API ServiceMonitor
    cat > /tmp/api-servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: socialmapper-api
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: socialmapper-api
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: socialmapper-api
  namespaceSelector:
    matchNames:
    - socialmapper
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
    honorLabels: true
EOF

    # Redis ServiceMonitor  
    cat > /tmp/redis-servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: redis
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: redis
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: redis
  namespaceSelector:
    matchNames:
    - socialmapper
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF

    kubectl apply -f /tmp/api-servicemonitor.yaml
    kubectl apply -f /tmp/redis-servicemonitor.yaml
    
    log "ServiceMonitors configured"
}

create_grafana_dashboards() {
    log "Creating custom Grafana dashboards..."
    
    # Wait for Grafana to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus-stack-grafana -n "$MONITORING_NAMESPACE"
    
    # Get Grafana admin password
    local grafana_password=$(kubectl get secret prometheus-stack-grafana -n "$MONITORING_NAMESPACE" -o jsonpath='{.data.admin-password}' | base64 -d)
    
    info "Grafana admin password: $grafana_password"
    info "Access Grafana with: kubectl port-forward -n $MONITORING_NAMESPACE service/prometheus-stack-grafana 3000:80"
    
    log "Custom dashboards ready"
}

setup_log_aggregation() {
    log "Setting up log aggregation (optional)..."
    
    # Install Fluent Bit for log collection
    helm repo add fluent https://fluent.github.io/helm-charts
    helm repo update
    
    cat > /tmp/fluent-bit-values.yaml << EOF
config:
  outputs: |
    [OUTPUT]
        Name cloudwatch_logs
        Match *
        region us-east-1
        log_group_name /aws/eks/socialmapper/fluent-bit
        log_stream_prefix fluent-bit-
        auto_create_group true

  filters: |
    [FILTER]
        Name kubernetes
        Match kube.*
        Merge_Log On
        Keep_Log Off
        K8S-Logging.Parser On
        K8S-Logging.Exclude On

tolerations:
- key: node-role.kubernetes.io/master
  operator: Exists
  effect: NoSchedule
EOF

    # Install Fluent Bit
    helm upgrade --install fluent-bit fluent/fluent-bit \
        --namespace "$MONITORING_NAMESPACE" \
        --values /tmp/fluent-bit-values.yaml \
        --wait || warn "Fluent Bit installation failed - continuing without log aggregation"
    
    log "Log aggregation setup completed"
}

run_monitoring_tests() {
    log "Running monitoring tests..."
    
    # Test Prometheus connectivity
    if kubectl port-forward -n "$MONITORING_NAMESPACE" service/prometheus-stack-kube-prom-prometheus 9090:9090 &>/dev/null &
    then
        local pf_pid=$!
        sleep 5
        
        if curl -s http://localhost:9090/-/healthy > /dev/null; then
            log "✓ Prometheus health check passed"
        else
            warn "✗ Prometheus health check failed"
        fi
        
        kill $pf_pid 2>/dev/null || true
    fi
    
    # Check if targets are discovered
    local targets=$(kubectl exec -n "$MONITORING_NAMESPACE" statefulset/prometheus-prometheus-stack-kube-prom-prometheus -- \
        wget -qO- http://localhost:9090/api/v1/targets | grep -o '"health":"up"' | wc -l)
    
    info "Prometheus targets up: $targets"
    
    # Test Alertmanager
    if kubectl get pods -n "$MONITORING_NAMESPACE" -l app.kubernetes.io/name=alertmanager | grep Running > /dev/null; then
        log "✓ Alertmanager is running"
    else
        warn "✗ Alertmanager issues detected"
    fi
    
    log "Monitoring tests completed"
}

print_access_info() {
    log "Monitoring Setup Complete! 🎉"
    echo ""
    echo "Access Information:"
    echo "=================="
    
    # Grafana
    local grafana_password=$(kubectl get secret prometheus-stack-grafana -n "$MONITORING_NAMESPACE" -o jsonpath='{.data.admin-password}' | base64 -d 2>/dev/null || echo "admin")
    echo "📊 Grafana:"
    echo "  Command: kubectl port-forward -n $MONITORING_NAMESPACE service/prometheus-stack-grafana 3000:80"
    echo "  URL: http://localhost:3000"
    echo "  Username: admin"
    echo "  Password: $grafana_password"
    echo ""
    
    # Prometheus
    echo "📈 Prometheus:"
    echo "  Command: kubectl port-forward -n $MONITORING_NAMESPACE service/prometheus-stack-kube-prom-prometheus 9090:9090"
    echo "  URL: http://localhost:9090"
    echo ""
    
    # Alertmanager
    echo "🚨 Alertmanager:"
    echo "  Command: kubectl port-forward -n $MONITORING_NAMESPACE service/prometheus-stack-kube-prom-alertmanager 9093:9093"
    echo "  URL: http://localhost:9093"
    echo ""
    
    echo "Configuration:"
    echo "============="
    echo "Monitoring Namespace: $MONITORING_NAMESPACE"
    echo "Alert Email: $ALERT_EMAIL"
    echo "Slack Webhook: ${SLACK_WEBHOOK:0:50}..."
    echo ""
    
    echo "Next Steps:"
    echo "==========="
    echo "1. Access Grafana and explore the dashboards"
    echo "2. Configure alert notifications in Alertmanager"
    echo "3. Set up additional custom dashboards as needed"
    echo "4. Test alerting by triggering test alerts"
    echo "5. Set up log aggregation if not already configured"
}

cleanup_temp_files() {
    rm -f /tmp/prometheus-operator-values.yaml
    rm -f /tmp/alertmanager-config.yaml  
    rm -f /tmp/socialmapper-rules.yaml
    rm -f /tmp/api-servicemonitor.yaml
    rm -f /tmp/redis-servicemonitor.yaml
    rm -f /tmp/fluent-bit-values.yaml
}

main() {
    log "Starting SocialMapper monitoring setup..."
    
    trap cleanup_temp_files EXIT
    
    check_prerequisites
    setup_monitoring_namespace
    install_prometheus_operator
    configure_alertmanager
    create_socialmapper_monitoring
    setup_service_monitors
    create_grafana_dashboards
    setup_log_aggregation
    run_monitoring_tests
    print_access_info
    
    log "Monitoring setup completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            MONITORING_NAMESPACE="$2"
            shift 2
            ;;
        --grafana-password)
            GRAFANA_ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --alert-email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        --slack-webhook)
            SLACK_WEBHOOK="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --namespace NAME          Monitoring namespace (default: monitoring)"
            echo "  --grafana-password PASS   Grafana admin password"
            echo "  --alert-email EMAIL       Email for alerts"
            echo "  --slack-webhook URL       Slack webhook URL for alerts"
            echo "  --help                    Show this help"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main