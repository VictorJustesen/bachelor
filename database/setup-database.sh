#!/bin/bash

# Database setup script for Real Estate Application

set -e

echo "🏠 Real Estate App Database Setup"
echo "=================================="

# Check if environment is specified
ENVIRONMENT=${1:-dev}

if [ "$ENVIRONMENT" = "dev" ]; then
    echo "Setting up DEVELOPMENT database..."
    
    # Load development environment variables
    if [ -f .env.dev ]; then
        export $(cat .env.dev | grep -v '^#' | xargs)
    fi
    
    # Start database container
    echo "Starting PostgreSQL database container..."
    docker-compose up -d database
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    until docker-compose exec database pg_isready -U $DB_USER -d $DB_NAME; do
        sleep 2
    done
    
    echo "✅ Development database is ready!"
    echo "Database URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:$DB_PORT/$DB_NAME"
    
elif [ "$ENVIRONMENT" = "prod" ]; then
    echo "Setting up PRODUCTION database (Azure)..."
    
    # Load production environment variables
    if [ -f .env.prod ]; then
        export $(cat .env.prod | grep -v '^#' | xargs)
    fi
    
    echo "⚠️  Production setup requires manual Azure SQL Database configuration"
    echo "Please ensure the following:"
    echo "1. Azure SQL Database/PostgreSQL server is created"
    echo "2. Firewall rules allow your application to connect"
    echo "3. Environment variables in .env.prod are correctly set"
    echo "4. Run database migrations: npm run migrate"
    
else
    echo "❌ Invalid environment. Use 'dev' or 'prod'"
    echo "Usage: ./setup-database.sh [dev|prod]"
    exit 1
fi

echo ""
echo "🚀 Next steps:"
echo "1. Install backend dependencies: cd backend && npm install"
echo "2. Start the application: docker-compose up"
echo "3. Test the API endpoints:"
echo "   - POST /api/users/register"
echo "   - POST /api/users/login"
echo "   - GET /api/users/me"
