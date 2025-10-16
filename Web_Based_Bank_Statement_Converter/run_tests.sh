#!/bin/bash
# Test Runner Script for Web-Based Bank Statement Converter API

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
TEST_RESULTS_DIR="$PROJECT_ROOT/test_results"
API_URL="http://localhost:5000"
API_PID=""

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Setup test environment
setup_test_environment() {
    print_header "Setting up test environment"
    
    cd "$PROJECT_ROOT"
    
    # Create test results directory
    mkdir -p "$TEST_RESULTS_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
    fi
    
    # Activate virtual environment
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    elif [ -f "$VENV_PATH/Scripts/activate" ]; then
        source "$VENV_PATH/Scripts/activate"
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    # Install test requirements
    print_info "Installing test dependencies..."
    pip install -q -r requirements.txt
    pip install -q -r requirements-test.txt
    
    print_success "Test environment ready"
}

# Start API server for testing
start_api_server() {
    print_header "Starting API server for testing"
    
    cd "$PROJECT_ROOT"
    
    # Check if server is already running
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        print_warning "API server already running at $API_URL"
        return 0
    fi
    
    # Start the API server in background
    print_info "Starting API server..."
    export FLASK_ENV=testing
    export TESTING=true
    
    python app.py &
    API_PID=$!
    
    # Wait for server to start
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$API_URL/health" > /dev/null 2>&1; then
            print_success "API server started at $API_URL (PID: $API_PID)"
            return 0
        fi
        
        sleep 1
        attempt=$((attempt + 1))
        print_info "Waiting for API to start... ($attempt/$max_attempts)"
    done
    
    print_error "Failed to start API server"
    return 1
}

# Stop API server
stop_api_server() {
    if [ ! -z "$API_PID" ]; then
        print_info "Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
        wait $API_PID 2>/dev/null || true
        print_success "API server stopped"
    fi
}

# Run unit tests
run_unit_tests() {
    print_header "Running Unit Tests"
    
    cd "$PROJECT_ROOT"
    
    # Run pytest with coverage
    pytest tests/ \
        --verbose \
        --cov=src \
        --cov=app \
        --cov-report=html:$TEST_RESULTS_DIR/coverage_html \
        --cov-report=xml:$TEST_RESULTS_DIR/coverage.xml \
        --cov-report=term-missing \
        --junit-xml=$TEST_RESULTS_DIR/unit_test_results.xml \
        --tb=short
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
    fi
    
    return $exit_code
}

# Run integration tests
run_integration_tests() {
    print_header "Running Integration Tests"
    
    cd "$PROJECT_ROOT"
    
    # Ensure API is running
    if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
        print_error "API server not running. Start it first."
        return 1
    fi
    
    # Run integration tests
    pytest tests/test_api.py::TestAPIEndpoints \
        --verbose \
        --tb=short
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
    fi
    
    return $exit_code
}

# Run load tests
run_load_tests() {
    print_header "Running Load Tests"
    
    cd "$PROJECT_ROOT"
    
    # Ensure API is running
    if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
        print_error "API server not running. Start it first."
        return 1
    fi
    
    # Run load tests
    python tests/load_test.py \
        --url "$API_URL" \
        --test all \
        --concurrent-users 5 \
        --requests-per-user 10 \
        --duration 30 \
        --output "$TEST_RESULTS_DIR/load_test_results.json"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Load tests completed"
    else
        print_error "Load tests failed"
    fi
    
    return $exit_code
}

# Run code quality checks
run_code_quality_checks() {
    print_header "Running Code Quality Checks"
    
    cd "$PROJECT_ROOT"
    
    local all_passed=true
    
    # Black formatting check
    print_info "Checking code formatting with Black..."
    if black --check --diff src/ app.py; then
        print_success "Code formatting check passed"
    else
        print_error "Code formatting check failed. Run 'black src/ app.py' to fix."
        all_passed=false
    fi
    
    # Flake8 linting
    print_info "Running Flake8 linting..."
    if flake8 src/ app.py --max-line-length=100 --ignore=E203,W503; then
        print_success "Linting check passed"
    else
        print_error "Linting check failed"
        all_passed=false
    fi
    
    # Import sorting check
    print_info "Checking import sorting with isort..."
    if isort --check-only --diff src/ app.py; then
        print_success "Import sorting check passed"
    else
        print_error "Import sorting check failed. Run 'isort src/ app.py' to fix."
        all_passed=false
    fi
    
    if $all_passed; then
        print_success "All code quality checks passed"
        return 0
    else
        print_error "Some code quality checks failed"
        return 1
    fi
}

# Run security scan
run_security_scan() {
    print_header "Running Security Scan"
    
    cd "$PROJECT_ROOT"
    
    # Install safety if not present
    pip install -q safety
    
    # Check for known security vulnerabilities
    print_info "Checking for known security vulnerabilities..."
    if safety check --json > "$TEST_RESULTS_DIR/security_scan.json"; then
        print_success "Security scan passed - no known vulnerabilities found"
    else
        print_warning "Security scan found potential issues. Check $TEST_RESULTS_DIR/security_scan.json"
    fi
    
    # Basic file permission checks
    print_info "Checking file permissions..."
    find . -name "*.py" -perm -o+w -ls > "$TEST_RESULTS_DIR/world_writable_files.txt" 2>/dev/null || true
    
    if [ -s "$TEST_RESULTS_DIR/world_writable_files.txt" ]; then
        print_warning "Found world-writable Python files. Check $TEST_RESULTS_DIR/world_writable_files.txt"
    else
        print_success "File permission check passed"
    fi
}

# Generate test report
generate_test_report() {
    print_header "Generating Test Report"
    
    local report_file="$TEST_RESULTS_DIR/test_report.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - Web-Based Bank Statement Converter API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f4f4f4; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background-color: #d4edda; border-color: #c3e6cb; }
        .warning { background-color: #fff3cd; border-color: #ffeaa7; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Report</h1>
        <p>Web-Based Bank Statement Converter API</p>
        <p class="timestamp">Generated: $(date)</p>
    </div>
    
    <div class="section">
        <h2>Test Results Summary</h2>
        <p>Find detailed results in the following files:</p>
        <ul>
            <li><a href="unit_test_results.xml">Unit Test Results (XML)</a></li>
            <li><a href="coverage_html/index.html">Code Coverage Report</a></li>
            <li><a href="load_test_results.json">Load Test Results (JSON)</a></li>
            <li><a href="security_scan.json">Security Scan Results</a></li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Test Artifacts</h2>
        <p>All test artifacts are stored in: <code>$TEST_RESULTS_DIR</code></p>
    </div>
</body>
</html>
EOF
    
    print_success "Test report generated: $report_file"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    stop_api_server
    
    # Clean up temporary files
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Main function
main() {
    # Set trap to cleanup on exit
    trap cleanup EXIT
    
    local run_unit=false
    local run_integration=false
    local run_load=false
    local run_quality=false
    local run_security=false
    local start_server=false
    local run_all=true
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                run_unit=true
                run_all=false
                shift
                ;;
            --integration)
                run_integration=true
                run_all=false
                shift
                ;;
            --load)
                run_load=true
                run_all=false
                shift
                ;;
            --quality)
                run_quality=true
                run_all=false
                shift
                ;;
            --security)
                run_security=true
                run_all=false
                shift
                ;;
            --start-server)
                start_server=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --unit        Run unit tests only"
                echo "  --integration Run integration tests only"
                echo "  --load        Run load tests only"
                echo "  --quality     Run code quality checks only"
                echo "  --security    Run security scan only"
                echo "  --start-server Start API server before tests"
                echo "  --help        Show this help message"
                echo ""
                echo "If no specific test type is specified, all tests will be run."
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_header "Web-Based Bank Statement Converter API - Test Suite"
    
    # Setup test environment
    setup_test_environment
    
    # Start server if requested or if running integration/load tests
    if $start_server || $run_integration || $run_load || $run_all; then
        start_api_server
    fi
    
    local overall_success=true
    
    # Run tests based on arguments
    if $run_all || $run_unit; then
        if ! run_unit_tests; then
            overall_success=false
        fi
    fi
    
    if $run_all || $run_integration; then
        if ! run_integration_tests; then
            overall_success=false
        fi
    fi
    
    if $run_all || $run_load; then
        if ! run_load_tests; then
            overall_success=false
        fi
    fi
    
    if $run_all || $run_quality; then
        if ! run_code_quality_checks; then
            overall_success=false
        fi
    fi
    
    if $run_all || $run_security; then
        run_security_scan  # Security scan doesn't fail the build
    fi
    
    # Generate test report
    generate_test_report
    
    # Final result
    if $overall_success; then
        print_success "All tests completed successfully!"
        exit 0
    else
        print_error "Some tests failed. Check the results above."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"