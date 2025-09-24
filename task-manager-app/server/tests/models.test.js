const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const User = require('../models/User');
const Task = require('../models/Task');
const Category = require('../models/Category');

let mongoServer;

describe('Models', () => {
  beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);
  });

  afterAll(async () => {
    await mongoose.connection.dropDatabase();
    await mongoose.connection.close();
    await mongoServer.stop();
  });

  beforeEach(async () => {
    await User.deleteMany({});
    await Task.deleteMany({});
    await Category.deleteMany({});
  });

  describe('User Model', () => {
    it('should hash password before saving', async () => {
      const user = new User({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      await user.save();

      expect(user.password).not.toBe('password123');
      expect(user.password).toHaveLength(60); // bcrypt hash length
    });

    it('should compare password correctly', async () => {
      const user = new User({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      await user.save();

      const isMatch = await user.comparePassword('password123');
      const isNotMatch = await user.comparePassword('wrongpassword');

      expect(isMatch).toBe(true);
      expect(isNotMatch).toBe(false);
    });

    it('should require username, email, and password', async () => {
      const user = new User({});

      let error;
      try {
        await user.save();
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
      expect(error.errors.username).toBeDefined();
      expect(error.errors.email).toBeDefined();
      expect(error.errors.password).toBeDefined();
    });

    it('should enforce unique username and email', async () => {
      await User.create({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      let error;
      try {
        await User.create({
          username: 'testuser',
          email: 'different@example.com',
          password: 'password123'
        });
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
      expect(error.code).toBe(11000); // MongoDB duplicate key error
    });
  });

  describe('Category Model', () => {
    it('should require name and user', async () => {
      const category = new Category({});

      let error;
      try {
        await category.save();
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
      expect(error.errors.name).toBeDefined();
      expect(error.errors.user).toBeDefined();
    });

    it('should enforce unique name per user', async () => {
      const user = await User.create({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      await Category.create({
        name: 'Test Category',
        user: user._id
      });

      let error;
      try {
        await Category.create({
          name: 'Test Category',
          user: user._id
        });
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
      expect(error.code).toBe(11000);
    });

    it('should allow same name for different users', async () => {
      const user1 = await User.create({
        username: 'user1',
        email: 'user1@example.com',
        password: 'password123'
      });

      const user2 = await User.create({
        username: 'user2',
        email: 'user2@example.com',
        password: 'password123'
      });

      await Category.create({
        name: 'Shared Name',
        user: user1._id
      });

      const category2 = await Category.create({
        name: 'Shared Name',
        user: user2._id
      });

      expect(category2.name).toBe('Shared Name');
    });
  });

  describe('Task Model', () => {
    it('should require title and user', async () => {
      const task = new Task({});

      let error;
      try {
        await task.save();
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
      expect(error.errors.title).toBeDefined();
      expect(error.errors.user).toBeDefined();
    });

    it('should have default values', async () => {
      const user = await User.create({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      const task = await Task.create({
        title: 'Test Task',
        user: user._id
      });

      expect(task.priority).toBe('Medium');
      expect(task.status).toBe('Pending');
      expect(task.createdAt).toBeDefined();
      expect(task.updatedAt).toBeDefined();
    });

    it('should update updatedAt on save', async () => {
      const user = await User.create({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      const task = await Task.create({
        title: 'Test Task',
        user: user._id
      });

      const originalUpdatedAt = task.updatedAt;

      // Wait a bit and update
      await new Promise(resolve => setTimeout(resolve, 10));
      task.title = 'Updated Title';
      await task.save();

      expect(task.updatedAt.getTime()).toBeGreaterThan(originalUpdatedAt.getTime());
    });

    it('should validate enum values', async () => {
      const user = await User.create({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123'
      });

      const task = new Task({
        title: 'Test Task',
        user: user._id,
        priority: 'Invalid',
        status: 'Invalid'
      });

      let error;
      try {
        await task.save();
      } catch (err) {
        error = err;
      }

      expect(error).toBeDefined();
    });
  });
});