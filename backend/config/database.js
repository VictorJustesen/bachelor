const { Sequelize } = require('sequelize');

// Direct configuration using environment variables
const dbConfig = {
  host: process.env.DB_HOST || 'database',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'realestate_db',
  username: process.env.DB_USER || 'dev_user',
  password: process.env.DB_PASSWORD || 'dev_password',
  dialect: 'postgres',
  logging: process.env.ENVIRONMENT === 'development' ? console.log : false,
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  }
};

console.log('Database config:', {
  host: dbConfig.host,
  port: dbConfig.port,
  database: dbConfig.database,
  username: dbConfig.username,
  dialect: dbConfig.dialect
});

// Create Sequelize instance
const sequelize = new Sequelize(
  dbConfig.database,
  dbConfig.username,
  dbConfig.password,
  {
    host: dbConfig.host,
    port: dbConfig.port,
    dialect: dbConfig.dialect,
    logging: dbConfig.logging,
    pool: dbConfig.pool,

    // Add this block to enable SSL and connect to Azure
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false // This is important for Azure
      }
    }
  }
); 



module.exports = { sequelize};
