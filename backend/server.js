const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors()); // Allows your React frontend to communicate with this backend
app.use(express.json()); // Parses incoming JSON requests

// Main API Routes
app.use('/api', apiRoutes);

app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${PORT}`);
});