#!/bin/bash

# Ethiopian Medical Business Data Platform Setup Script
# This script helps you set up the project quickly

set -e

echo "🚀 Setting up Ethiopian Medical Business Data Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. This is optional for local development."
    else
        print_success "Python 3 is installed"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating project directories..."
    
    directories=(
        "data/raw"
        "data/processed"
        "models"
        "logs"
        "dbt/models"
        "dbt/macros"
        "dbt/profiles"
        "scripts"
        "tests"
        "app/api"
        "app/core"
        "app/models"
        "app/services"
        "app/utils"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
    
    print_success "All directories created"
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Skipping environment setup."
        return
    fi
    
    if [ -f "env.template" ]; then
        cp env.template .env
        print_success "Created .env file from template"
        print_warning "Please edit .env file with your actual configuration values"
    else
        print_error "env.template file not found. Please create .env file manually."
    fi
}

# Create initial configuration files
create_config_files() {
    print_status "Creating initial configuration files..."
    
    # Create dbt profiles.yml
    if [ ! -f "dbt/profiles/profiles.yml" ]; then
        cat > dbt/profiles/profiles.yml << EOF
ethiopian_medical:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: "{{ env_var('POSTGRES_USER') }}"
      pass: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: public
      threads: 4
      keepalives_idle: 0
      search_path: public
      role: null
      sslmode: prefer
    prod:
      type: postgres
      host: "{{ env_var('POSTGRES_HOST') }}"
      port: 5432
      user: "{{ env_var('POSTGRES_USER') }}"
      pass: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: "{{ env_var('POSTGRES_DB') }}"
      schema: public
      threads: 4
      keepalives_idle: 0
      search_path: public
      role: null
      sslmode: require
EOF
        print_success "Created dbt profiles.yml"
    fi
    
    # Create dbt_project.yml
    if [ ! -f "dbt/dbt_project.yml" ]; then
        cat > dbt/dbt_project.yml << EOF
name: 'ethiopian_medical'
version: '1.0.0'
config-version: 2

profile: 'ethiopian_medical'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  ethiopian_medical:
    staging:
      +materialized: view
    marts:
      +materialized: table
EOF
        print_success "Created dbt_project.yml"
    fi
}

# Test Docker setup
test_docker() {
    print_status "Testing Docker setup..."
    
    if docker-compose config > /dev/null 2>&1; then
        print_success "Docker Compose configuration is valid"
    else
        print_error "Docker Compose configuration has errors"
        exit 1
    fi
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Edit .env file with your actual configuration:"
    echo "   - TELEGRAM_API_ID"
    echo "   - TELEGRAM_API_HASH"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - SECRET_KEY"
    echo "   - JWT_SECRET_KEY"
    echo ""
    echo "2. Start the platform:"
    echo "   docker-compose up -d"
    echo ""
    echo "3. Access the services:"
    echo "   - FastAPI: http://localhost:8000"
    echo "   - Dagster: http://localhost:3000"
    echo "   - PostgreSQL: localhost:5432"
    echo ""
    echo "4. Check the logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "📚 For more information, see README.md"
}

# Main setup function
main() {
    echo "🏥 Ethiopian Medical Business Data Platform Setup"
    echo "================================================"
    echo ""
    
    check_docker
    check_python
    create_directories
    setup_env
    create_config_files
    test_docker
    show_next_steps
}

# Run main function
main "$@" 