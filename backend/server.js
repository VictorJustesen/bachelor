const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');
const { testConnection, sequelize } = require('./config/database');
const userService = require('./services/userService');

const app = express();
const PORT = process.env.PORT || 8000;

const HOST = process.env.HOST || '0.0.0.0';



// Middleware
app.use(cors());
app.use(express.json());

app.use('/api', apiRoutes);


app.listen(PORT, HOST, () => {
  console.log(`Backend server running on http://${HOST}:${PORT}`);
});