const userService = require('../services/userService');
const User = require('../models/User');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { Op } = require('sequelize');

jest.mock('../models/User');
jest.mock('bcrypt');
jest.mock('jsonwebtoken');

describe('UserService', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
      };

      User.findOne.mockResolvedValue(null);
      bcrypt.hash.mockResolvedValue('hashedpassword');
      User.create.mockResolvedValue({ id: 1, ...userData });
      jwt.sign.mockReturnValue('testtoken');

      const result = await userService.register(userData);

      expect(User.findOne).toHaveBeenCalledWith({
        where: { [Op.or]: [{ username: userData.username }, { email: userData.email }] },
      });
      expect(bcrypt.hash).toHaveBeenCalledWith(userData.password, 10);
      expect(User.create).toHaveBeenCalled();
      expect(jwt.sign).toHaveBeenCalled();
      expect(result).toHaveProperty('token', 'testtoken');
      expect(result.user).toEqual({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
      });
    });

    it('should throw an error if username or email already exists', async () => {
      const userData = { username: 'testuser', email: 'test@example.com', password: 'password123' };
      User.findOne.mockResolvedValue({ id: 1, ...userData });

      await expect(userService.register(userData)).rejects.toThrow('Username or email already exists');
    });
  });

  describe('login', () => {
    it('should log in a user with valid credentials', async () => {
      const user = {
        id: 1,
        username: 'testuser',
        password_hash: 'hashedpassword',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
      };

      User.findOne.mockResolvedValue(user);
      bcrypt.compare.mockResolvedValue(true);
      jwt.sign.mockReturnValue('testtoken');

      const result = await userService.login('testuser', 'password123');

      expect(User.findOne).toHaveBeenCalledWith({ where: { username: 'testuser', is_active: true } });
      expect(bcrypt.compare).toHaveBeenCalledWith('password123', 'hashedpassword');
      expect(result).toHaveProperty('token', 'testtoken');
      expect(result.user.username).toBe('testuser');
    });

    it('should throw an error for invalid credentials', async () => {
      User.findOne.mockResolvedValue(null);
      await expect(userService.login('wronguser', 'password')).rejects.toThrow('Invalid credentials');
    });

    it('should throw an error for a wrong password', async () => {
      const user = { id: 1, username: 'testuser', password_hash: 'hashedpassword' };
      User.findOne.mockResolvedValue(user);
      bcrypt.compare.mockResolvedValue(false);

      await expect(userService.login('testuser', 'wrongpassword')).rejects.toThrow('Invalid credentials');
    });
  });
});