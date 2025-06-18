const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { Op } = require('sequelize'); // Add this import
const User = require('../models/User');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRY = '24h';

class UserService {
  async register(userData) {
    try {
      const { username, email, password, first_name, last_name } = userData;
      console.log('Registering user with data:', { username, email,password, first_name, last_name }); // Debug log
      // Add validation
      if (!username || !email || !password) {
        throw new Error('Username, email, and password are required');
      }
      
      console.log('Registering user with data:', { username, email, first_name, last_name }); // Debug log
      
      // Check if user already exists - Fix the syntax
      const existingUser = await User.findOne({
        where: {
          [Op.or]: [{ username }, { email }]  // Use Op.or instead of $or
        }
      });
      
      if (existingUser) {
        throw new Error('Username or email already exists');
      }
      
      // Hash password
      const saltRounds = 10;
      const password_hash = await bcrypt.hash(password, saltRounds);
      
      // Create user
      const user = await User.create({
        username,
        email,
        password_hash,
        first_name,
        last_name,
        is_active: true
      });
      
      // Generate JWT token
      const token = jwt.sign(
        { userId: user.id, username: user.username },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRY }
      );
      
      return {
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          first_name: user.first_name,
          last_name: user.last_name
        },
        token
      };
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  async login(username, password) {
    try {
      // Add validation
      if (!username || !password) {
        throw new Error('Username and password are required');
      }
      
      console.log('Login attempt for username:', username); // Debug log
      
      // Find user
      const user = await User.findOne({
        where: { username, is_active: true }
      });
      
      if (!user) {
        throw new Error('Invalid credentials');
      }
      
      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password_hash);
      
      if (!isValidPassword) {
        throw new Error('Invalid credentials');
      }
      
      // Generate JWT token
      const token = jwt.sign(
        { userId: user.id, username: user.username },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRY }
      );
      
      return {
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          first_name: user.first_name,
          last_name: user.last_name
        },
        token
      };
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async getUserById(userId) {
    try {
      const user = await User.findByPk(userId, {
        attributes: ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
      });
      
      return user;
    } catch (error) {
      console.error('Get user error:', error);
      throw error;
    }
  }

  verifyToken(token) {
    try {
      return jwt.verify(token, JWT_SECRET);
    } catch (error) {
      throw new Error('Invalid token');
    }
  }
}

module.exports = new UserService();