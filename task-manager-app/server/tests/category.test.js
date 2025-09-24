const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../server');
const User = require('../models/User');
const Category = require('../models/Category');

let mongoServer;
let token;
let userId;

describe('Category Routes', () => {
  beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);

    // Create test user
    const user = await User.create({
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123'
    });
    userId = user._id;

    // Generate token
    const jwt = require('jsonwebtoken');
    token = jwt.sign({ userId: userId }, process.env.JWT_SECRET);
  });

  afterAll(async () => {
    await mongoose.connection.dropDatabase();
    await mongoose.connection.close();
    await mongoServer.stop();
  });

  beforeEach(async () => {
    await Category.deleteMany({});
  });

  describe('POST /api/categories', () => {
    it('should create a new category', async () => {
      const categoryData = {
        name: 'Work Projects'
      };

      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${token}`)
        .send(categoryData);

      expect(res.statusCode).toEqual(201);
      expect(res.body).toHaveProperty('name', 'Work Projects');
      expect(res.body).toHaveProperty('user');
    });

    it('should not create category without name', async () => {
      const categoryData = {};

      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${token}`)
        .send(categoryData);

      expect(res.statusCode).toEqual(400);
    });

    it('should not create duplicate category names for same user', async () => {
      // Create first category
      await Category.create({
        name: 'Work Projects',
        user: userId
      });

      // Try to create duplicate
      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${token}`)
        .send({ name: 'Work Projects' });

      expect(res.statusCode).toEqual(500); // MongoDB duplicate key error
    });
  });

  describe('GET /api/categories', () => {
    beforeEach(async () => {
      await Category.create([
        {
          name: 'Work',
          user: userId
        },
        {
          name: 'Personal',
          user: userId
        }
      ]);
    });

    it('should get all categories for user', async () => {
      const res = await request(app)
        .get('/api/categories')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(2);
      expect(res.body[0]).toHaveProperty('name');
      expect(res.body[0]).toHaveProperty('user');
    });

    it('should return empty array when no categories exist', async () => {
      await Category.deleteMany({});

      const res = await request(app)
        .get('/api/categories')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(0);
    });
  });

  describe('PUT /api/categories/:id', () => {
    let categoryId;

    beforeEach(async () => {
      const category = await Category.create({
        name: 'Original Category',
        user: userId
      });
      categoryId = category._id;
    });

    it('should update a category', async () => {
      const updateData = {
        name: 'Updated Category'
      };

      const res = await request(app)
        .put(`/api/categories/${categoryId}`)
        .set('Authorization', `Bearer ${token}`)
        .send(updateData);

      expect(res.statusCode).toEqual(200);
      expect(res.body.name).toBe('Updated Category');
    });

    it('should not update category of another user', async () => {
      // Create another user
      const otherUser = await User.create({
        username: 'otheruser',
        email: 'other@example.com',
        password: 'password123'
      });

      const otherCategory = await Category.create({
        name: 'Other User Category',
        user: otherUser._id
      });

      const res = await request(app)
        .put(`/api/categories/${otherCategory._id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({ name: 'Hacked Name' });

      expect(res.statusCode).toEqual(404);
    });
  });

  describe('DELETE /api/categories/:id', () => {
    let categoryId;

    beforeEach(async () => {
      const category = await Category.create({
        name: 'Category to Delete',
        user: userId
      });
      categoryId = category._id;
    });

    it('should delete a category', async () => {
      const res = await request(app)
        .delete(`/api/categories/${categoryId}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('message', 'Category deleted');

      // Verify category is deleted
      const deletedCategory = await Category.findById(categoryId);
      expect(deletedCategory).toBeNull();
    });

    it('should not delete category of another user', async () => {
      // Create another user
      const otherUser = await User.create({
        username: 'otheruser',
        email: 'other@example.com',
        password: 'password123'
      });

      const otherCategory = await Category.create({
        name: 'Other User Category',
        user: otherUser._id
      });

      const res = await request(app)
        .delete(`/api/categories/${otherCategory._id}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(404);
    });
  });
});