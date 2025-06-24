
const { Sequelize } = require('sequelize');

// Check for production environment
const isProduction = process.env.ENVIRONMENT === 'prod' || process.env.NODE_ENV === 'production';

// Define SSL options based on the environment
const sslOptions = isProduction 
  ? { 
      ssl: { 
        require: true,
        rejectUnauthorized: false // For Azure PostgreSQL certificates
      } 
    } 
  : { ssl: false }; // Disable SSL for development (local)

// Define all configuration in one place using the correct env var names from Kubernetes secret
const dbConfig = {
  host: process.env.POSTGRES_HOST,      // From Kubernetes secret
  port: process.env.POSTGRES_PORT || 5432,
  database: process.env.POSTGRES_DB,    // From Kubernetes secret
  username: process.env.POSTGRES_USER,  // From Kubernetes secret
  password: process.env.POSTGRES_PASSWORD, // From Kubernetes secret
  dialect: 'postgres',
  logging: false, // Disable verbose logging in production
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  },
  dialectOptions: {
    ...sslOptions
  }
};

// Log the configuration for debugging, but avoid logging the password
console.log('Database config loaded:', {
  host: dbConfig.host,
  database: dbConfig.database,
  username: dbConfig.username,
  ssl: isProduction,
  environment: process.env.ENVIRONMENT || 'dev'
});

// Create a single Sequelize instance using the config object
const sequelize = new Sequelize(
  dbConfig.database,
  dbConfig.username,
  dbConfig.password,
  dbConfig // Pass the whole config object as options
);

module.exports = { sequelize };