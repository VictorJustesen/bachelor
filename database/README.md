# Database Setup and Management

This directory contains the database configuration for the Real Estate Application.

## Overview

The application uses PostgreSQL as the database with Docker volumes for data persistence. The setup supports both development and production environments.

## Architecture

- **Development**: PostgreSQL container with local Docker volume
- **Production**: Azure SQL Database (or other cloud provider)
- **Data Persistence**: Docker volumes ensure data survives container restarts

## Files

- `Dockerfile` - PostgreSQL container configuration
- `init.sql` - Database schema initialization
- `config.js` - Environment-based database configuration
- `manage-db.sh` - Database management script
- `.env.dev` - Development environment variables

## Data Persistence

### How it works
The application uses Docker named volumes to persist database data:

```yaml
volumes:
  postgres_data:/var/lib/postgresql/data
```

This means:
- ✅ Data survives container restarts
- ✅ Data survives `docker-compose down`
- ❌ Data is lost with `docker-compose down -v` (volumes deleted)
- ❌ Data is lost if you remove the volume manually

### Volume Management

**Check existing volumes:**
```bash
docker volume ls
```

**Inspect volume details:**
```bash
docker volume inspect bachelor_postgres_data
```

**Remove volume (⚠️ DELETES ALL DATA):**
```bash
docker volume rm bachelor_postgres_data
```

## Database Management

Use the provided management script for common database operations:

### Check Database Status
```bash
./database/manage-db.sh status
```

### Create Backup
```bash
./database/manage-db.sh backup
```
Backups are saved to `database/backups/` directory.

### Restore from Backup
```bash
./database/manage-db.sh restore database/backups/backup_20231201_120000.sql
```

### Reset Database
```bash
./database/manage-db.sh reset
```
This drops all data and recreates the schema.

## Environment Configuration

### Development (.env.dev)
```bash
ENVIRONMENT=dev
DB_HOST=database
DB_PORT=5432
DB_NAME=realestate_db
DB_USER=dev_user
DB_PASSWORD=dev_password
```

### Production (Azure SQL)
```bash
ENVIRONMENT=prod
AZURE_SQL_HOST=your-server.database.windows.net
AZURE_SQL_PORT=1433
AZURE_SQL_DATABASE=realestate_db
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
```

## Development Workflow

### First Time Setup
1. Start services: `docker-compose up -d`
2. Check database: `./database/manage-db.sh status`
3. The database will be automatically initialized with the schema

### Daily Development
- Database data persists between container restarts
- No need to recreate data unless you want a fresh start
- Use backups before major schema changes

### Fresh Start
If you need a completely fresh database:
```bash
docker-compose down
docker volume rm bachelor_postgres_data
docker-compose up -d
```

## Production Migration

To switch to production (Azure SQL):

1. Update environment variables in production deployment
2. Set `ENVIRONMENT=prod`
3. Configure Azure SQL connection details
4. Run database migrations if needed

The same codebase works with both PostgreSQL (dev) and Azure SQL (prod) thanks to Sequelize ORM.

## Database Schema

### Tables
- `users` - User accounts and profiles
- `user_sessions` - Authentication sessions
- `user_preferences` - User-specific settings
- `property_searches` - Search history and predictions

### Features
- UUID primary keys
- Automatic timestamps
- Foreign key constraints
- Indexes for performance
- JSON columns for flexible data

## Troubleshooting

### Database won't start
```bash
docker logs database-container
```

### Connection refused
- Check if container is running: `docker ps`
- Check health status: `docker-compose ps`
- Verify environment variables

### Data corruption
- Restore from backup: `./database/manage-db.sh restore <backup_file>`
- Or reset completely: `./database/manage-db.sh reset`

### Performance issues
- Check connection pool settings in `config.js`
- Monitor with: `docker stats database-container`
