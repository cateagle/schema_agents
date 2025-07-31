#!/bin/bash
# FILE: dev-setup.sh
# Development environment setup script for FalkorDB Media Manager

set -e

# Configuration
PYTHON_VERSION="3.12.6"
VENV_DIR=".venv"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Help function
show_help() {
    cat << EOF
FalkorDB Media Manager - Development Environment Setup

USAGE:
    ./dev-setup.sh [OPTIONS]

OPTIONS:
    --reinstall     Reinstall everything from scratch (removes .venv)
    --help, -h      Show this help message

DESCRIPTION:
    This script sets up the complete development environment including:
    - Python ${PYTHON_VERSION} via pyenv
    - Virtual environment in ${VENV_DIR}/
    - All requirements and dev dependencies  
    - Script permissions
    - Development aliases (temporary, session-only)

EXAMPLES:
    ./dev-setup.sh                # Normal setup/activation
    ./dev-setup.sh --reinstall    # Clean reinstall
    ./dev-setup.sh --help         # Show this help

EOF
}

# Check if pyenv is installed
check_pyenv() {
    if ! command -v pyenv &> /dev/null; then
        print_error "pyenv is not installed. Please install pyenv first:"
        echo "  curl https://pyenv.run | bash"
        echo "  Then restart your shell and run this script again."
        exit 1
    fi
}

# Install Python version if needed
setup_python() {
    print_header "Setting up Python ${PYTHON_VERSION}"
    
    # Check if version is installed
    if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
        print_warning "Python ${PYTHON_VERSION} is not installed."
        echo "Available options:"
        echo "  1) Install Python ${PYTHON_VERSION} (recommended)"
        echo "  2) Choose a different version"
        echo "  3) Abort"
        
        read -p "Enter your choice (1-3): " choice
        
        case $choice in
            1)
                print_info "Installing Python ${PYTHON_VERSION}..."
                pyenv install "${PYTHON_VERSION}"
                ;;
            2)
                echo "Available Python versions:"
                pyenv versions
                read -p "Enter the version you want to use: " PYTHON_VERSION
                if ! pyenv versions | grep -q "${PYTHON_VERSION}"; then
                    print_error "Version ${PYTHON_VERSION} is not installed."
                    exit 1
                fi
                ;;
            3)
                print_info "Aborted by user."
                exit 0
                ;;
            *)
                print_error "Invalid choice. Aborting."
                exit 1
                ;;
        esac
    fi
    
    # Set local Python version
    print_info "Setting local Python version to ${PYTHON_VERSION}"
    pyenv local "${PYTHON_VERSION}"
    
    # Verify Python version
    python_path=$(which python)
    current_version=$(python --version | cut -d' ' -f2)
    print_success "Using Python ${current_version} at ${python_path}"
}

# Create and setup virtual environment
setup_venv() {
    print_header "Setting up Virtual Environment"
    
    if [ -d "${VENV_DIR}" ]; then
        print_info "Virtual environment already exists at ${VENV_DIR}"
    else
        print_info "Creating virtual environment in ${VENV_DIR}"
        python -m venv "${VENV_DIR}"
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment"
    source "${VENV_DIR}/bin/activate"
    print_success "Virtual environment activated"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
}

# Install requirements
install_requirements() {
    print_header "Installing Requirements"
    
    # Main requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing main requirements..."
        pip install -r requirements.txt
        print_success "Main requirements installed"
    else
        print_warning "requirements.txt not found, skipping"
    fi
    
    # Dev requirements
    if [ -f "dev-requirements.txt" ]; then
        print_info "Installing dev requirements..."
        pip install -r dev-requirements.txt
        print_success "Dev requirements installed"
    else
        print_warning "dev-requirements.txt not found, skipping"
    fi
}

# Set script permissions
set_permissions() {
    print_header "Setting Script Permissions"
    
    # Find and chmod +x all .sh files
    find . -name "*.sh" -type f | while read -r script; do
        if [ ! -x "$script" ]; then
            print_info "Making $script executable"
            chmod +x "$script"
        fi
    done
    
    # Make Python dev scripts executable
    if [ -d "dev" ]; then
        find dev -name "*.py" -type f | while read -r script; do
            if [ ! -x "$script" ]; then
                print_info "Making $script executable"
                chmod +x "$script"
            fi
        done
    fi
    
    print_success "Script permissions set"
}

# Create development aliases
create_aliases() {
    print_header "Creating Development Aliases"
    
    # Get the absolute path to the project root
    local project_path="$(pwd)"
    
    # Create aliases for this session only
    print_info "Creating temporary development aliases..."
    
    # Development script aliases (using absolute paths)
    alias dev-run="${project_path}/dev/venv-run.sh"
    alias dev-test="${project_path}/test-services.sh"
    alias dev-mypy="${project_path}/dev/venv-run.sh python ${project_path}/dev/run_mypy.py"
    alias dev-black="${project_path}/dev/venv-run.sh python -m black ${project_path}"
    alias dev-headers="${project_path}/dev/venv-run.sh python ${project_path}/dev/check_file_headers.py"
    
    # Service test aliases
    alias test-backend="(cd ${project_path}/services/backend && ./test.sh)"
    alias test-ml="(cd ${project_path}/services/ml_service && ./test.sh)"
    alias test-storage="(cd ${project_path}/services/storage_service && ./test.sh)"
    
    # Quick shortcuts
    alias vrun="${project_path}/dev/venv-run.sh"
    alias pytest-all="${project_path}/dev/venv-run.sh python -m pytest"
    
    print_success "Development aliases created (session-only)"
    print_info "Available aliases:"
    echo "  dev-run       - Run commands in venv"
    echo "  dev-test      - Run all service tests"  
    echo "  dev-mypy      - Run type checking"
    echo "  dev-black     - Format code"
    echo "  dev-headers   - Check file headers"
    echo "  test-backend  - Test backend service"
    echo "  test-ml       - Test ML service"
    echo "  test-storage  - Test storage service"
    echo "  vrun          - Short alias for venv-run.sh"
    echo "  pytest-all    - Run all pytest tests"
}

# Show completion message
show_completion() {
    print_header "Setup Complete!"
    
    echo "Your development environment is now ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Source this script to get aliases: source dev-setup.sh"
    echo "  2. Or activate the virtual environment: source ${VENV_DIR}/bin/activate"
    echo "  3. Start developing!"
    echo ""
    echo "Quick commands:"
    echo "  ./dev/venv-run.sh python -c 'import fastapi; print(\"Ready!\")'  # Test setup"
    echo "  ./dev-setup.sh --help                                           # Show help"
    echo "  ./dev-setup.sh --reinstall                                      # Clean reinstall"
    echo ""
    print_success "Happy coding! 🚀"
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"
    
    # Parse arguments
    REINSTALL=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --reinstall)
                REINSTALL=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_header "FalkorDB Media Manager - Development Setup"
    
    # Handle reinstall
    if [ "$REINSTALL" = true ]; then
        print_warning "Reinstall requested - removing existing virtual environment"
        if [ -d "${VENV_DIR}" ]; then
            rm -rf "${VENV_DIR}"
            print_info "Removed ${VENV_DIR}"
        fi
    fi
    
    # Run setup steps
    check_pyenv
    setup_python
    setup_venv
    install_requirements
    set_permissions
    create_aliases
    show_completion
}

# If script is sourced, only create aliases
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Script is being sourced, just activate environment and set aliases
    if [ -d "${VENV_DIR}" ]; then
        source "${VENV_DIR}/bin/activate"
        create_aliases
        print_success "Environment activated and aliases loaded!"
    else
        print_error "Virtual environment not found. Run ./dev-setup.sh first."
    fi
else
    # Script is being executed, run full setup
    main "$@"
fi