#!/bin/bash

# Database backup and restore script for Docker environment

set -e

CONTAINER_NAME="database-container"
DB_NAME="realestate_db"
DB_USER="dev_user"
BACKUP_DIR="./database/backups"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Function to create backup
backup_database() {
    echo "Creating database backup..."
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
    
    echo "Backup created: $BACKUP_FILE"
}

# Function to restore from backup
restore_database() {
    if [ -z "$1" ]; then
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    echo "Restoring database from: $BACKUP_FILE"
    
    # Drop and recreate database
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    
    # Restore from backup
    docker exec -i $CONTAINER_NAME psql -U $DB_USER $DB_NAME < $BACKUP_FILE
    
    echo "Database restored successfully"
}

# Function to reset database to initial state
reset_database() {
    echo "Resetting database to initial state..."
    
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    docker exec -i $CONTAINER_NAME psql -U $DB_USER $DB_NAME < ./database/init.sql
    
    echo "Database reset successfully"
}

# Function to check database status
check_database() {
    echo "Checking database status..."
    
    if docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME; then
        echo "Database is ready"
        
        # Show table count
        TABLE_COUNT=$(docker exec $CONTAINER_NAME psql -U $DB_USER $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        echo "Tables in database: $TABLE_COUNT"
        
        # Show user count
        USER_COUNT=$(docker exec $CONTAINER_NAME psql -U $DB_USER $DB_NAME -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
        echo "Users in database: $USER_COUNT"
    else
        echo "Database is not ready"
        exit 1
    fi
}

# Main script logic
case "$1" in
    backup)
        backup_database
        ;;
    restore)
        restore_database "$2"
        ;;
    reset)
        reset_database
        ;;
    status)
        check_database
        ;;
    *)
        echo "Usage: $0 {backup|restore <file>|reset|status}"
        echo ""
        echo "Commands:"
        echo "  backup                 Create a backup of the database"
        echo "  restore <backup_file>  Restore database from backup file"
        echo "  reset                  Reset database to initial state"
        echo "  status                 Check database status"
        exit 1
        ;;
esac
