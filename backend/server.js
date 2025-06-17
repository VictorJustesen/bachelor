const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');
const { testConnection, sequelize } = require('./config/database');
const userService = require('./services/userService');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize database connection
async function initializeDatabase() {
  try {
    await testConnection();
    
    // Sync database models (create tables if they don't exist)
    if (process.env.ENVIRONMENT === 'development' || process.env.ENVIRONMENT === 'dev') {
      await sequelize.sync({ force: true }); // Use force in development
      console.log('Database synchronized successfully.');
    }
    
    // Skip session cleanup for now since we don't have session management set up
    console.log('Database initialization complete.');
    
  } catch (error) {
    console.error('Failed to initialize database:', error);
    process.exit(1);
  }
}

// Routes
app.use('/api', apiRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Start server
async function startServer() {
  try {
    await initializeDatabase();
    
    app.listen(PORT, () => {
      console.log(`Backend server running on port ${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();