FROM postgres:15

# Set environment variables
ENV POSTGRES_DB=realestate_db
ENV POSTGRES_USER=dev_user
ENV POSTGRES_PASSWORD=dev_password

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Expose PostgreSQL port
EXPOSE 5432
