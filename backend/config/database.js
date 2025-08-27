const { Sequelize } = require('sequelize');

// This is the key: We check for the environment variable that is ONLY available in your production Kubernetes environment.
// If it exists, we know we are in production. Otherwise, we assume development.
const isProduction = !!process.env.POSTGRES_HOST;

// Define the database configuration based on the environment
const dbConfig = {
  host: isProduction ? process.env.POSTGRES_HOST : process.env.DB_HOST,
  port: isProduction ? process.env.POSTGRES_PORT : process.env.DB_PORT || 5432,
  database: isProduction ? process.env.POSTGRES_DB : process.env.DB_NAME,
  username: isProduction ? process.env.POSTGRES_USER : process.env.DB_USER,
  password: isProduction ? process.env.POSTGRES_PASSWORD : process.env.DB_PASSWORD,
  dialect: 'postgres',
  logging: isProduction ? false : console.log, // Disable verbose logging in production
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  },
  dialectOptions: {
    // Enable SSL for Azure, disable for local development
    ssl: isProduction ? { 
      require: true,
      rejectUnauthorized: false // Required for Azure PostgreSQL
    } : false
  }
};

// Log the configuration for debugging (without the password)
console.log('Database config loaded:', {
  host: dbConfig.host,
  database: dbConfig.database,
  username: dbConfig.username,
  ssl: isProduction,
  environment: isProduction ? 'production' : 'development'
});

// Create the single Sequelize instance with the correct configuration
const sequelize = new Sequelize(
  dbConfig.database,
  dbConfig.username,
  dbConfig.password,
  dbConfig
);

module.exports = { sequelize };