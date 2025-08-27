const userService = require('../services/userService');
const User = require('../models/User');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

jest.mock('../models/User');
jest.mock('bcrypt');
jest.mock('jsonwebtoken');

describe('UserService', () => {
  afterEach(() => jest.clearAllMocks());

  describe('register', () => {
    it('should create a user and return a token on successful registration', async () => {
      const userData = { username: 'testuser', email: 'test@example.com', password: 'password123' };
      
      User.findOne.mockResolvedValue(null); 
      User.create.mockResolvedValue({ id: 1, ...userData });
      jwt.sign.mockReturnValue('test-jwt-token');

      const result = await userService.register(userData);

      expect(result.user.username).toBe('testuser');
      expect(result.token).toBe('test-jwt-token');
    });

    it('should throw an error if the user already exists', async () => {
      User.findOne.mockResolvedValue({ username: 'testuser' }); 

      await expect(userService.register({})).rejects.toThrow('Username or email already exists');
    });
  });

  describe('login', () => {
    it('should return user data and a token with valid credentials', async () => {
      const mockUser = { username: 'testuser', password_hash: 'hashedpassword' };
      
      User.findOne.mockResolvedValue(mockUser);
      bcrypt.compare.mockResolvedValue(true); 
      jwt.sign.mockReturnValue('test-jwt-token');

      const result = await userService.login('testuser', 'password123');
      
      expect(result.user.username).toBe('testuser');
      expect(result.token).toBe('test-jwt-token');
    });

    it.each([
      ['user not found', null, false],
      ['wrong password', { password_hash: 'hashed' }, false],
    ])('should throw "Invalid credentials" when %s', async (scenario, foundUser, isPasswordCorrect) => {
      User.findOne.mockResolvedValue(foundUser);

      await expect(userService.login('user', 'pass')).rejects.toThrow('Invalid credentials');
    });
  });
});