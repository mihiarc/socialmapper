#!/bin/bash
# SocialMapper Infrastructure Deployment Script
# This script deploys the complete production infrastructure on AWS

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"
K8S_DIR="$PROJECT_ROOT/infrastructure/kubernetes"
MONITORING_DIR="$PROJECT_ROOT/infrastructure/monitoring"

# Default values
AWS_REGION=${AWS_REGION:-"us-east-1"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
CLUSTER_NAME=${CLUSTER_NAME:-"socialmapper"}
DOMAIN_NAME=${DOMAIN_NAME:-"demo.socialmapper.com"}
DRY_RUN=${DRY_RUN:-"false"}

# Functions
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
    
    # Check required tools
    local tools=("terraform" "kubectl" "aws" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
    fi
    
    # Check environment variables
    if [[ -z "${CENSUS_API_KEY:-}" ]]; then
        warn "CENSUS_API_KEY not set. Some features may not work."
    fi
    
    log "Prerequisites check completed"
}

setup_terraform_backend() {
    log "Setting up Terraform backend..."
    
    local bucket_name="socialmapper-terraform-state"
    local table_name="socialmapper-terraform-locks"
    
    # Create S3 bucket for Terraform state
    if ! aws s3api head-bucket --bucket "$bucket_name" 2>/dev/null; then
        info "Creating Terraform state bucket: $bucket_name"
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$bucket_name" \
            --server-side-encryption-configuration '{
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }'
    fi
    
    # Create DynamoDB table for state locking
    if ! aws dynamodb describe-table --table-name "$table_name" &>/dev/null; then
        info "Creating Terraform state lock table: $table_name"
        aws dynamodb create-table \
            --table-name "$table_name" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
        
        # Wait for table to be created
        aws dynamodb wait table-exists --table-name "$table_name"
    fi
    
    log "Terraform backend setup completed"
}

deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars if it doesn't exist
    if [[ ! -f terraform.tfvars ]]; then
        info "Creating terraform.tfvars from example"
        cp terraform.tfvars.example terraform.tfvars
        warn "Please update terraform.tfvars with your specific values"
        
        # Update basic values
        sed -i.bak "s/demo.socialmapper.com/$DOMAIN_NAME/g" terraform.tfvars
        sed -i.bak "s/us-east-1/$AWS_REGION/g" terraform.tfvars
        rm terraform.tfvars.bak
    fi
    
    # Validate configuration
    terraform validate
    
    # Plan deployment
    terraform plan -out=tfplan
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Dry run mode - skipping actual deployment"
        return 0
    fi
    
    # Apply deployment
    terraform apply tfplan
    
    # Save important outputs
    terraform output -json > "$PROJECT_ROOT/terraform-outputs.json"
    
    log "Infrastructure deployment completed"
    
    cd - > /dev/null
}

setup_kubernetes() {
    log "Setting up Kubernetes cluster access..."
    
    local cluster_name=$(terraform output -raw cluster_id 2>/dev/null || echo "$CLUSTER_NAME-$(date +%s | tail -c 9)")
    
    # Update kubeconfig
    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$cluster_name"
    
    # Verify cluster access
    kubectl cluster-info
    
    log "Kubernetes cluster access configured"
}

deploy_kubernetes_resources() {
    log "Deploying Kubernetes resources..."
    
    # Deploy in order of dependencies
    local manifests=(
        "$K8S_DIR/namespace.yaml"
        "$K8S_DIR/configmap.yaml"
        "$K8S_DIR/secrets.yaml"
        "$K8S_DIR/redis.yaml"
        "$K8S_DIR/api-deployment.yaml"
        "$K8S_DIR/ui-deployment.yaml"
        "$K8S_DIR/ingress.yaml"
    )
    
    for manifest in "${manifests[@]}"; do
        if [[ -f "$manifest" ]]; then
            info "Applying $(basename "$manifest")"
            if [[ "$DRY_RUN" == "true" ]]; then
                kubectl apply --dry-run=client -f "$manifest"
            else
                kubectl apply -f "$manifest"
            fi
        fi
    done
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Wait for deployments to be ready
        info "Waiting for deployments to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/redis -n socialmapper
        kubectl wait --for=condition=available --timeout=300s deployment/socialmapper-api -n socialmapper
        kubectl wait --for=condition=available --timeout=300s deployment/socialmapper-ui -n socialmapper
    fi
    
    log "Kubernetes resources deployed successfully"
}

deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    local monitoring_manifests=(
        "$MONITORING_DIR/prometheus.yaml"
        "$MONITORING_DIR/grafana.yaml"
        "$MONITORING_DIR/alertmanager.yaml"
    )
    
    for manifest in "${monitoring_manifests[@]}"; do
        if [[ -f "$manifest" ]]; then
            info "Applying $(basename "$manifest")"
            if [[ "$DRY_RUN" == "true" ]]; then
                kubectl apply --dry-run=client -f "$manifest"
            else
                kubectl apply -f "$manifest"
            fi
        fi
    done
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Wait for monitoring stack
        info "Waiting for monitoring stack to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring || true
        kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring || true
        kubectl wait --for=condition=available --timeout=300s deployment/alertmanager -n monitoring || true
    fi
    
    log "Monitoring stack deployed successfully"
}

deploy_security_policies() {
    log "Deploying security policies..."
    
    local security_dir="$PROJECT_ROOT/infrastructure/security"
    
    if [[ -d "$security_dir" ]]; then
        local security_manifests=(
            "$security_dir/network-policies.yaml"
            "$security_dir/pod-security-policies.yaml"
        )
        
        for manifest in "${security_manifests[@]}"; do
            if [[ -f "$manifest" ]]; then
                info "Applying $(basename "$manifest")"
                if [[ "$DRY_RUN" == "true" ]]; then
                    kubectl apply --dry-run=client -f "$manifest"
                else
                    kubectl apply -f "$manifest"
                fi
            fi
        done
    fi
    
    log "Security policies deployed successfully"
}

run_smoke_tests() {
    log "Running smoke tests..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "Skipping smoke tests in dry run mode"
        return 0
    fi
    
    # Get service endpoints
    local api_endpoint
    local ui_endpoint
    
    # Try to get load balancer endpoints
    api_endpoint=$(kubectl get service socialmapper-api-service -n socialmapper -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    ui_endpoint=$(kubectl get service socialmapper-ui-service -n socialmapper -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    
    # Fallback to port forwarding for testing
    if [[ -z "$api_endpoint" ]]; then
        info "Using port forwarding for API testing"
        kubectl port-forward -n socialmapper service/socialmapper-api-service 8000:8000 &
        local pf_pid=$!
        sleep 5
        api_endpoint="localhost:8000"
    fi
    
    # Test API health
    if curl -f -s "http://$api_endpoint/api/v1/health" > /dev/null; then
        log "✓ API health check passed"
    else
        error "✗ API health check failed"
    fi
    
    # Test API metadata endpoint
    if curl -f -s "http://$api_endpoint/api/v1/metadata/census-variables" > /dev/null; then
        log "✓ API metadata endpoint test passed"
    else
        warn "✗ API metadata endpoint test failed (may require Census API key)"
    fi
    
    # Clean up port forwarding
    if [[ -n "${pf_pid:-}" ]]; then
        kill $pf_pid 2>/dev/null || true
    fi
    
    log "Smoke tests completed"
}

print_summary() {
    log "Deployment Summary"
    echo "===================="
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Get cluster info
        local cluster_endpoint=$(kubectl cluster-info | grep "Kubernetes control plane" | awk '{print $7}')
        local api_service=$(kubectl get service socialmapper-api-service -n socialmapper -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending")
        local ui_service=$(kubectl get service socialmapper-ui-service -n socialmapper -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending")
        
        echo "Cluster Endpoint: $cluster_endpoint"
        echo "API Service: $api_service"
        echo "UI Service: $ui_service"
        echo "Domain: $DOMAIN_NAME"
        
        # Get pod status
        echo ""
        echo "Pod Status:"
        kubectl get pods -n socialmapper -o wide
        
        echo ""
        echo "Service Status:"
        kubectl get services -n socialmapper
        
        # Check if ingress is ready
        if kubectl get ingress socialmapper-ingress -n socialmapper &>/dev/null; then
            echo ""
            echo "Ingress Status:"
            kubectl get ingress socialmapper-ingress -n socialmapper
        fi
    fi
    
    echo ""
    echo "Next Steps:"
    echo "1. Update DNS records to point $DOMAIN_NAME to the load balancer"
    echo "2. Configure SSL certificates (if not using ACM)"
    echo "3. Set up monitoring alerts and notifications"
    echo "4. Review and update security policies as needed"
    echo "5. Run comprehensive tests against the deployed environment"
    echo ""
    echo "Access Points:"
    echo "- Demo Application: https://$DOMAIN_NAME"
    echo "- API Documentation: https://$DOMAIN_NAME/api/docs"
    echo "- Monitoring (if configured): https://monitoring.$DOMAIN_NAME"
}

cleanup() {
    log "Cleaning up temporary files..."
    rm -f "$TERRAFORM_DIR/tfplan"
    rm -f "$PROJECT_ROOT/terraform-outputs.json.bak"
}

# Main execution
main() {
    log "Starting SocialMapper infrastructure deployment"
    log "Environment: $ENVIRONMENT"
    log "Region: $AWS_REGION"
    log "Domain: $DOMAIN_NAME"
    log "Dry Run: $DRY_RUN"
    
    # Trap for cleanup
    trap cleanup EXIT
    
    check_prerequisites
    setup_terraform_backend
    deploy_infrastructure
    
    if [[ "$DRY_RUN" == "false" ]]; then
        setup_kubernetes
        deploy_kubernetes_resources
        deploy_monitoring
        deploy_security_policies
        run_smoke_tests
    fi
    
    print_summary
    
    log "Deployment completed successfully! 🚀"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run              Run without making changes"
            echo "  --environment ENV      Set environment (default: production)"
            echo "  --region REGION        Set AWS region (default: us-east-1)"
            echo "  --domain DOMAIN        Set domain name (default: demo.socialmapper.com)"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main