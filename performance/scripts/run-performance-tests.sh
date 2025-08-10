#!/bin/bash

# Performance Testing Automation Script for SocialMapper
# This script runs comprehensive performance tests using k6 and Lighthouse CI

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERFORMANCE_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$PERFORMANCE_DIR")"
RESULTS_DIR="$PERFORMANCE_DIR/results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Default values
TEST_ENV="${TEST_ENV:-staging}"
LOAD_PROFILE="${LOAD_PROFILE:-load}"
RUN_K6="${RUN_K6:-true}"
RUN_LIGHTHOUSE="${RUN_LIGHTHOUSE:-true}"
PARALLEL_EXECUTION="${PARALLEL_EXECUTION:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check k6
    if ! command -v k6 &> /dev/null; then
        log_error "k6 is not installed. Please install k6: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    
    # Check Node.js and npm
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js"
        exit 1
    fi
    
    # Check Lighthouse CI
    if ! command -v lhci &> /dev/null; then
        log_warning "Lighthouse CI not found, installing..."
        npm install -g @lhci/cli
    fi
    
    log_success "All dependencies are available"
}

# Create results directory
setup_results_directory() {
    log_info "Setting up results directory..."
    mkdir -p "$RESULTS_DIR/$TIMESTAMP"
    mkdir -p "$RESULTS_DIR/$TIMESTAMP/k6"
    mkdir -p "$RESULTS_DIR/$TIMESTAMP/lighthouse"
    mkdir -p "$RESULTS_DIR/$TIMESTAMP/reports"
}

# Run k6 load tests
run_k6_tests() {
    if [ "$RUN_K6" != "true" ]; then
        log_info "Skipping k6 tests (RUN_K6=false)"
        return 0
    fi

    log_info "Running k6 load tests..."
    
    local k6_results_dir="$RESULTS_DIR/$TIMESTAMP/k6"
    local k6_tests_dir="$PERFORMANCE_DIR/k6/tests"
    
    # Array of test files
    local test_files=(
        "health-endpoints.js"
        "metadata-endpoints.js"
        "comprehensive-api.js"
    )
    
    local failed_tests=0
    
    for test_file in "${test_files[@]}"; do
        local test_name=$(basename "$test_file" .js)
        log_info "Running k6 test: $test_name"
        
        local output_file="$k6_results_dir/${test_name}_${TIMESTAMP}.json"
        
        if k6 run \
            --env TEST_ENV="$TEST_ENV" \
            --env LOAD_PROFILE="$LOAD_PROFILE" \
            --out json="$output_file" \
            "$k6_tests_dir/$test_file"; then
            log_success "k6 test '$test_name' completed successfully"
        else
            log_error "k6 test '$test_name' failed"
            ((failed_tests++))
        fi
        
        # Brief pause between tests
        sleep 5
    done
    
    if [ $failed_tests -gt 0 ]; then
        log_warning "$failed_tests k6 tests failed"
        return 1
    else
        log_success "All k6 tests completed successfully"
        return 0
    fi
}

# Run Lighthouse CI tests
run_lighthouse_tests() {
    if [ "$RUN_LIGHTHOUSE" != "true" ]; then
        log_info "Skipping Lighthouse tests (RUN_LIGHTHOUSE=false)"
        return 0
    fi

    log_info "Running Lighthouse CI tests..."
    
    # Change to frontend directory
    cd "$PROJECT_ROOT/socialmapper-ui"
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm ci
    fi
    
    local lighthouse_results_dir="$RESULTS_DIR/$TIMESTAMP/lighthouse"
    
    # Run desktop tests
    log_info "Running Lighthouse tests for desktop..."
    if LHCI_BUILD_CONTEXT__EXTERNAL_BUILD_URL="$lighthouse_results_dir/desktop" \
       lhci autorun --config="$PERFORMANCE_DIR/lighthouse/lighthouserc.json"; then
        log_success "Desktop Lighthouse tests completed"
    else
        log_error "Desktop Lighthouse tests failed"
        return 1
    fi
    
    sleep 10
    
    # Run mobile tests
    log_info "Running Lighthouse tests for mobile..."
    if LHCI_BUILD_CONTEXT__EXTERNAL_BUILD_URL="$lighthouse_results_dir/mobile" \
       lhci autorun --config="$PERFORMANCE_DIR/lighthouse/mobile-config.json"; then
        log_success "Mobile Lighthouse tests completed"
    else
        log_error "Mobile Lighthouse tests failed"
        return 1
    fi
    
    # Return to script directory
    cd "$SCRIPT_DIR"
    
    log_success "All Lighthouse tests completed successfully"
    return 0
}

# Generate performance report
generate_report() {
    log_info "Generating performance report..."
    
    local report_file="$RESULTS_DIR/$TIMESTAMP/reports/performance_report_$TIMESTAMP.md"
    
    cat > "$report_file" << EOF
# Performance Test Report

**Test Run:** $TIMESTAMP
**Environment:** $TEST_ENV
**Load Profile:** $LOAD_PROFILE

## Test Configuration

- k6 Tests: $RUN_K6
- Lighthouse Tests: $RUN_LIGHTHOUSE
- Parallel Execution: $PARALLEL_EXECUTION

## Results Summary

### k6 Load Test Results

$(if [ "$RUN_K6" = "true" ]; then
    echo "Load test results can be found in: \`results/$TIMESTAMP/k6/\`"
    echo ""
    echo "Key metrics measured:"
    echo "- API response times"
    echo "- Error rates"  
    echo "- Throughput (requests/second)"
    echo "- Concurrent user handling"
else
    echo "k6 tests were skipped"
fi)

### Lighthouse CI Results

$(if [ "$RUN_LIGHTHOUSE" = "true" ]; then
    echo "Lighthouse results can be found in: \`results/$TIMESTAMP/lighthouse/\`"
    echo ""
    echo "Key metrics measured:"
    echo "- Core Web Vitals"
    echo "- Performance scores"
    echo "- Accessibility scores"
    echo "- Best practices compliance"
    echo "- SEO optimization"
else
    echo "Lighthouse tests were skipped"
fi)

## Next Steps

1. Review detailed results in the respective directories
2. Compare results with previous runs for regression analysis
3. Address any performance issues identified
4. Update performance budgets if necessary

---
*Generated by SocialMapper Performance Testing Pipeline*
EOF

    log_success "Performance report generated: $report_file"
}

# Main execution function
main() {
    log_info "Starting SocialMapper performance testing pipeline..."
    log_info "Environment: $TEST_ENV"
    log_info "Load Profile: $LOAD_PROFILE"
    log_info "Timestamp: $TIMESTAMP"
    
    # Setup
    check_dependencies
    setup_results_directory
    
    local overall_success=true
    
    if [ "$PARALLEL_EXECUTION" = "true" ]; then
        log_info "Running tests in parallel..."
        
        # Run tests in parallel
        run_k6_tests &
        local k6_pid=$!
        
        run_lighthouse_tests &
        local lighthouse_pid=$!
        
        # Wait for both to complete
        if ! wait $k6_pid; then
            overall_success=false
        fi
        
        if ! wait $lighthouse_pid; then
            overall_success=false
        fi
        
    else
        log_info "Running tests sequentially..."
        
        # Run tests sequentially
        if ! run_k6_tests; then
            overall_success=false
        fi
        
        if ! run_lighthouse_tests; then
            overall_success=false
        fi
    fi
    
    # Generate report regardless of test outcomes
    generate_report
    
    # Final status
    if [ "$overall_success" = "true" ]; then
        log_success "Performance testing pipeline completed successfully!"
        exit 0
    else
        log_error "Performance testing pipeline completed with failures!"
        exit 1
    fi
}

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --env ENVIRONMENT          Test environment (staging|production) [default: staging]"
    echo "  --profile LOAD_PROFILE     Load profile (smoke|load|stress|spike|soak) [default: load]"
    echo "  --skip-k6                  Skip k6 load tests"
    echo "  --skip-lighthouse          Skip Lighthouse CI tests"
    echo "  --parallel                 Run tests in parallel"
    echo "  --help                     Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  TEST_ENV                   Test environment"
    echo "  LOAD_PROFILE              Load profile"
    echo "  RUN_K6                     Run k6 tests (true|false)"
    echo "  RUN_LIGHTHOUSE             Run Lighthouse tests (true|false)"
    echo "  PARALLEL_EXECUTION         Run tests in parallel (true|false)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            TEST_ENV="$2"
            shift 2
            ;;
        --profile)
            LOAD_PROFILE="$2"
            shift 2
            ;;
        --skip-k6)
            RUN_K6="false"
            shift
            ;;
        --skip-lighthouse)
            RUN_LIGHTHOUSE="false"
            shift
            ;;
        --parallel)
            PARALLEL_EXECUTION="true"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main