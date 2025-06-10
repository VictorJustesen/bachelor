const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Main API Routes - remove /api prefix since nginx handles it
app.use('/', apiRoutes);

app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${PORT}`);
});