const { Sequelize } = require('sequelize');

// Check for production environment
const isProduction = process.env.NODE_ENV === 'prod';

// Define SSL options based on the environment
const sslOptions = isProduction 
  ? { ssl: { require: true } } // Enable SSL for production (Azure)
  : { ssl: false };            // Disable SSL for development (local)

// Define all configuration in one place
const dbConfig = {
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  username: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
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
console.log('Database config loaded. SSL required:', isProduction);

// Create a single Sequelize instance using the config object
const sequelize = new Sequelize(
  dbConfig.database,
  dbConfig.username,
  dbConfig.password,
  dbConfig // Pass the whole config object as options
);

module.exports = { sequelize };