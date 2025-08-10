#!/bin/bash
# SocialMapper Rollback Script
# Quick rollback capability for deployments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-"socialmapper"}
ROLLBACK_STEPS=${ROLLBACK_STEPS:-1}
COMPONENTS=${COMPONENTS:-"all"}

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

check_cluster_access() {
    log "Verifying cluster access..."
    
    if ! kubectl cluster-info &>/dev/null; then
        error "Cannot access Kubernetes cluster. Please check your kubeconfig."
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        error "Namespace '$NAMESPACE' does not exist."
    fi
    
    log "Cluster access verified"
}

show_deployment_history() {
    log "Current deployment history:"
    
    local deployments=("socialmapper-api" "socialmapper-ui" "redis")
    
    for deployment in "${deployments[@]}"; do
        if kubectl get deployment "$deployment" -n "$NAMESPACE" &>/dev/null; then
            echo "=== $deployment ==="
            kubectl rollout history deployment/"$deployment" -n "$NAMESPACE"
            echo ""
        fi
    done
}

rollback_deployment() {
    local deployment=$1
    local steps=${2:-$ROLLBACK_STEPS}
    
    if ! kubectl get deployment "$deployment" -n "$NAMESPACE" &>/dev/null; then
        warn "Deployment '$deployment' not found, skipping..."
        return 0
    fi
    
    log "Rolling back deployment '$deployment' by $steps steps..."
    
    # Get current revision
    local current_revision=$(kubectl get deployment "$deployment" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    info "Current revision: $current_revision"
    
    # Perform rollback
    if kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE" --to-revision=$((current_revision - steps)) 2>/dev/null; then
        log "Rollback initiated for $deployment"
        
        # Wait for rollback to complete
        if kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s; then
            log "✓ Rollback completed successfully for $deployment"
        else
            error "✗ Rollback failed for $deployment"
        fi
    else
        # If specific revision fails, try simple undo
        warn "Specific revision rollback failed, trying simple undo..."
        if kubectl rollout undo deployment/"$deployment" -n "$NAMESPACE"; then
            kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout=300s
            log "✓ Simple rollback completed for $deployment"
        else
            error "✗ All rollback attempts failed for $deployment"
        fi
    fi
}

rollback_configmaps_and_secrets() {
    log "Rolling back ConfigMaps and Secrets (if backed up)..."
    
    # This assumes you have a backup mechanism in place
    local backup_dir="/tmp/k8s-backup/$(date -d '1 day ago' +%Y%m%d)"
    
    if [[ -d "$backup_dir" ]]; then
        info "Found backup directory: $backup_dir"
        
        # Rollback ConfigMaps
        if [[ -f "$backup_dir/configmaps.yaml" ]]; then
            kubectl apply -f "$backup_dir/configmaps.yaml"
            log "ConfigMaps rolled back"
        fi
        
        # Rollback Secrets (be careful with this)
        if [[ -f "$backup_dir/secrets.yaml" ]]; then
            warn "Rolling back secrets - this may affect authentication"
            kubectl apply -f "$backup_dir/secrets.yaml"
            log "Secrets rolled back"
        fi
    else
        warn "No backup found for ConfigMaps and Secrets"
    fi
}

emergency_scale_down() {
    log "Emergency scale down of all deployments..."
    
    local deployments=($(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}'))
    
    for deployment in "${deployments[@]}"; do
        info "Scaling down $deployment to 0 replicas"
        kubectl scale deployment "$deployment" --replicas=0 -n "$NAMESPACE"
    done
    
    warn "All deployments scaled down. Use --scale-up to restore."
}

emergency_scale_up() {
    log "Emergency scale up to restore service..."
    
    # Restore to default replica counts
    kubectl scale deployment socialmapper-api --replicas=3 -n "$NAMESPACE" 2>/dev/null || true
    kubectl scale deployment socialmapper-ui --replicas=2 -n "$NAMESPACE" 2>/dev/null || true
    kubectl scale deployment redis --replicas=1 -n "$NAMESPACE" 2>/dev/null || true
    
    # Wait for pods to be ready
    sleep 10
    
    log "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/socialmapper-api -n "$NAMESPACE" || true
    kubectl wait --for=condition=available --timeout=300s deployment/socialmapper-ui -n "$NAMESPACE" || true
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n "$NAMESPACE" || true
}

run_health_checks() {
    log "Running post-rollback health checks..."
    
    # Check pod status
    info "Pod status:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    # Check service endpoints
    local api_ready=false
    local ui_ready=false
    
    # Wait for services to be ready
    for i in {1..30}; do
        if kubectl exec -n "$NAMESPACE" deployment/socialmapper-api -- curl -f -s http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            api_ready=true
            break
        fi
        sleep 5
    done
    
    for i in {1..30}; do
        if kubectl exec -n "$NAMESPACE" deployment/socialmapper-ui -- curl -f -s http://localhost:8080/health >/dev/null 2>&1; then
            ui_ready=true
            break
        fi
        sleep 5
    done
    
    # Report results
    if [[ "$api_ready" == true ]]; then
        log "✓ API health check passed"
    else
        error "✗ API health check failed"
    fi
    
    if [[ "$ui_ready" == true ]]; then
        log "✓ UI health check passed"
    else
        warn "✗ UI health check failed"
    fi
    
    # Test Redis connectivity
    if kubectl exec -n "$NAMESPACE" deployment/redis -- redis-cli ping >/dev/null 2>&1; then
        log "✓ Redis connectivity check passed"
    else
        warn "✗ Redis connectivity check failed"
    fi
}

create_incident_report() {
    log "Creating incident report..."
    
    local report_file="/tmp/rollback-incident-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Rollback Incident Report
Date: $(date)
Namespace: $NAMESPACE
Components: $COMPONENTS
Rollback Steps: $ROLLBACK_STEPS

## Pre-Rollback State
$(kubectl get pods -n "$NAMESPACE" -o wide)

## Deployment History
$(show_deployment_history)

## Current State
$(kubectl get pods -n "$NAMESPACE" -o wide)

## Events (Last 30 minutes)
$(kubectl get events -n "$NAMESPACE" --sort-by='.metadata.creationTimestamp' | tail -20)

## Logs (API - Last 100 lines)
$(kubectl logs -n "$NAMESPACE" deployment/socialmapper-api --tail=100 || echo "API logs not available")

## Next Steps
1. Investigate root cause of the issue that triggered rollback
2. Fix underlying issues before next deployment
3. Update monitoring and alerting if needed
4. Review deployment procedures
EOF
    
    info "Incident report created: $report_file"
}

main() {
    case "${1:-rollback}" in
        "rollback")
            log "Starting rollback process..."
            check_cluster_access
            show_deployment_history
            
            if [[ "$COMPONENTS" == "all" ]]; then
                rollback_deployment "socialmapper-api"
                rollback_deployment "socialmapper-ui"
                rollback_deployment "redis"
            else
                for component in ${COMPONENTS//,/ }; do
                    rollback_deployment "$component"
                done
            fi
            
            run_health_checks
            create_incident_report
            log "Rollback process completed"
            ;;
            
        "emergency-down")
            log "Emergency scale down initiated..."
            check_cluster_access
            emergency_scale_down
            log "Emergency scale down completed"
            ;;
            
        "emergency-up")
            log "Emergency scale up initiated..."
            check_cluster_access
            emergency_scale_up
            run_health_checks
            log "Emergency scale up completed"
            ;;
            
        "status")
            log "Current deployment status..."
            check_cluster_access
            kubectl get deployments,pods,services -n "$NAMESPACE" -o wide
            run_health_checks
            ;;
            
        "history")
            log "Deployment history..."
            check_cluster_access
            show_deployment_history
            ;;
            
        *)
            echo "Usage: $0 [rollback|emergency-down|emergency-up|status|history]"
            echo ""
            echo "Commands:"
            echo "  rollback        - Rollback deployments (default)"
            echo "  emergency-down  - Scale all deployments to 0"
            echo "  emergency-up    - Scale deployments back up"
            echo "  status          - Show current status and run health checks"
            echo "  history         - Show deployment rollout history"
            echo ""
            echo "Environment Variables:"
            echo "  NAMESPACE       - Kubernetes namespace (default: socialmapper)"
            echo "  ROLLBACK_STEPS  - Number of revisions to rollback (default: 1)"
            echo "  COMPONENTS      - Components to rollback (default: all)"
            echo ""
            echo "Examples:"
            echo "  $0 rollback"
            echo "  COMPONENTS=socialmapper-api $0 rollback"
            echo "  ROLLBACK_STEPS=2 $0 rollback"
            exit 1
            ;;
    esac
}

# Trap for cleanup
trap 'echo "Rollback script interrupted"' INT TERM

# Run main function
main "$@"