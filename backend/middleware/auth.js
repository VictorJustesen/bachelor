const userService = require('../services/userService');

// Middleware to authenticate requests using session tokens
const authenticateUser = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'No valid authorization token provided' });
    }

    const sessionToken = authHeader.substring(7); // Remove 'Bearer ' prefix
    
    const user = await userService.verifySession(sessionToken);
    req.user = user; // Attach user to request object
    
    next();
  } catch (error) {
    return res.status(401).json({ error: error.message });
  }
};

// Optional authentication - if token is provided, validate it, but don't fail if missing
const optionalAuth = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const sessionToken = authHeader.substring(7);
      const user = await userService.verifySession(sessionToken);
      req.user = user;
    }
    
    next();
  } catch (error) {
    // Continue without authentication if token is invalid
    next();
  }
};

module.exports = {
  authenticateUser,
  optionalAuth
};
