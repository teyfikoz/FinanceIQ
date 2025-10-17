#!/bin/bash

# Global Liquidity Dashboard - Startup Script

set -e

echo "🌍 Starting Global Liquidity & Market Correlation Dashboard"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker and Docker Compose are installed
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Docker is available${NC}"
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Docker Compose is available${NC}"
    fi
}

# Create necessary directories
create_directories() {
    echo -e "${BLUE}Creating directories...${NC}"

    mkdir -p data/{raw,processed,exports,backups}
    mkdir -p logs
    mkdir -p deployment/ssl

    echo -e "${GREEN}✅ Directories created${NC}"
}

# Check if .env file exists
check_environment() {
    echo -e "${BLUE}Checking environment configuration...${NC}"

    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found, copying from .env.example${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your API keys and configuration${NC}"
    else
        echo -e "${GREEN}✅ .env file found${NC}"
    fi
}

# Start services
start_services() {
    echo -e "${BLUE}Starting services with Docker Compose...${NC}"

    # Pull latest images
    docker-compose pull

    # Build and start services
    docker-compose up -d --build

    echo -e "${GREEN}✅ Services started${NC}"
}

# Wait for services to be ready
wait_for_services() {
    echo -e "${BLUE}Waiting for services to be ready...${NC}"

    # Wait for database
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
    while ! docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

    # Wait for backend
    echo -e "${YELLOW}Waiting for FastAPI backend...${NC}"
    while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}✅ FastAPI backend is ready${NC}"

    # Wait for dashboard
    echo -e "${YELLOW}Waiting for Streamlit dashboard...${NC}"
    while ! curl -f http://localhost:8501 > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}✅ Streamlit dashboard is ready${NC}"
}

# Show service status
show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    docker-compose ps

    echo ""
    echo -e "${GREEN}🎉 Global Liquidity Dashboard is now running!${NC}"
    echo ""
    echo -e "${BLUE}Access URLs:${NC}"
    echo -e "  📊 Dashboard: ${GREEN}http://localhost:8501${NC}"
    echo -e "  🔧 API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  ❤️  Health:   ${GREEN}http://localhost:8000/health${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  View logs:    ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  Stop services: ${YELLOW}docker-compose down${NC}"
    echo -e "  Restart:      ${YELLOW}docker-compose restart${NC}"
    echo ""
}

# Main execution
main() {
    check_requirements
    create_directories
    check_environment
    start_services
    wait_for_services
    show_status
}

# Handle script interruption
trap 'echo -e "\n${RED}❌ Startup interrupted${NC}"; exit 1' INT

# Run main function
main