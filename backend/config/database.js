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

let dbConfig;

if(process.env.ENVIRONMENT === 'production') { 
  dbConfig = {
    host: process.env.POSTGRES_HOST,
    port: process.env.POSTGRES_PORT || 5432,
    database: process.env.POSTGRES_DB,
    username: process.env.POSTGRES_USER,
    password: process.env.POSTGRES_PASSWORD,
    dialect: 'postgres',
    logging: false,
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
} else {
  dbConfig = {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME,
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    dialect: 'postgres',
    logging: console.log,
    dialectOptions: {
      ...sslOptions
    }
  };
}

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
  dbConfig
);

module.exports = { sequelize };