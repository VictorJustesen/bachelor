const express = require('express');
const userService = require('../services/userService');
const { authenticateUser } = require('../middleware/auth');

const router = express.Router();

// Register a new user
router.post('/register', async (req, res) => {
  try {
    const { email, password, first_name, last_name } = req.body;
    
    // Basic validation
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    
    if (password.length < 6) {
      return res.status(400).json({ error: 'Password must be at least 6 characters long' });
    }

    const user = await userService.registerUser({
      email,
      password,
      first_name,
      last_name
    });

    res.status(201).json({
      message: 'User registered successfully',
      user
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Login user
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const result = await userService.loginUser(email, password);
    
    res.json({
      message: 'Login successful',
      user: result.user,
      token: result.sessionToken,
      expiresAt: result.expiresAt
    });
  } catch (error) {
    res.status(401).json({ error: error.message });
  }
});

// Logout user
router.post('/logout', authenticateUser, async (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    const sessionToken = authHeader.substring(7);
    
    const result = await userService.logoutUser(sessionToken);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get current user info
router.get('/me', authenticateUser, async (req, res) => {
  try {
    const user = await userService.getUserInfo(req.user.id);
    res.json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update user info
router.put('/me', authenticateUser, async (req, res) => {
  try {
    const user = await userService.updateUserInfo(req.user.id, req.body);
    res.json({
      message: 'User updated successfully',
      user
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get user info by ID (protected route)
router.get('/:userId', authenticateUser, async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Users can only access their own info unless they're admin (future feature)
    if (userId !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    const user = await userService.getUserInfo(userId);
    res.json(user);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Set user preference
router.post('/preferences', authenticateUser, async (req, res) => {
  try {
    const { key, value } = req.body;
    
    if (!key) {
      return res.status(400).json({ error: 'Preference key is required' });
    }
    
    const result = await userService.setUserPreference(req.user.id, key, value);
    res.json(result);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get user preference
router.get('/preferences/:key', authenticateUser, async (req, res) => {
  try {
    const { key } = req.params;
    const value = await userService.getUserPreference(req.user.id, key);
    
    res.json({
      key,
      value
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get user search history
router.get('/me/searches', authenticateUser, async (req, res) => {
  try {
    const { PropertySearch } = require('../models/User');
    const { Op } = require('sequelize');
    
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;
    
    const searches = await PropertySearch.findAndCountAll({
      where: { user_id: req.user.id },
      order: [['created_at', 'DESC']],
      limit,
      offset,
      attributes: ['id', 'search_parameters', 'prediction_result', 'created_at']
    });
    
    res.json({
      searches: searches.rows,
      totalCount: searches.count,
      currentPage: page,
      totalPages: Math.ceil(searches.count / limit)
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
