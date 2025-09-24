const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../server');
const User = require('../models/User');
const Category = require('../models/Category');

let mongoServer;
let authToken;
let testUser;

describe('Category Routes', () => {
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
    await Category.deleteMany({});

    // Create test user
    testUser = await User.create({
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123'
    });

    // Login to get token
    const loginRes = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'test@example.com',
        password: 'password123'
      });

    authToken = loginRes.body.token;
  });

  describe('GET /api/categories', () => {
    it('should get all categories for authenticated user', async () => {
      await Category.create([
        { name: 'Work', user: testUser._id },
        { name: 'Personal', user: testUser._id }
      ]);

      const res = await request(app)
        .get('/api/categories')
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(2);
      expect(res.body[0].name).toBe('Work');
      expect(res.body[1].name).toBe('Personal');
    });
  });

  describe('POST /api/categories', () => {
    it('should create a new category', async () => {
      const categoryData = {
        name: 'New Category'
      };

      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${authToken}`)
        .send(categoryData);

      expect(res.statusCode).toEqual(201);
      expect(res.body.name).toBe('New Category');
      expect(res.body.user).toBe(testUser._id.toString());
    });

    it('should not create category with duplicate name', async () => {
      await Category.create({
        name: 'Duplicate',
        user: testUser._id
      });

      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ name: 'Duplicate' });

      expect(res.statusCode).toEqual(400);
      expect(res.body.message).toBe('Category name already exists');
    });

    it('should validate required fields', async () => {
      const res = await request(app)
        .post('/api/categories')
        .set('Authorization', `Bearer ${authToken}`)
        .send({});

      expect(res.statusCode).toEqual(400);
    });
  });

  describe('PUT /api/categories/:id', () => {
    it('should update a category', async () => {
      const category = await Category.create({
        name: 'Original Name',
        user: testUser._id
      });

      const updateData = {
        name: 'Updated Name'
      };

      const res = await request(app)
        .put(`/api/categories/${category._id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send(updateData);

      expect(res.statusCode).toEqual(200);
      expect(res.body.name).toBe('Updated Name');
    });

    it('should return 404 for non-existent category', async () => {
      const fakeId = new mongoose.Types.ObjectId();

      const res = await request(app)
        .put(`/api/categories/${fakeId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ name: 'Updated' });

      expect(res.statusCode).toEqual(404);
    });
  });

  describe('DELETE /api/categories/:id', () => {
    it('should delete a category', async () => {
      const category = await Category.create({
        name: 'Category to Delete',
        user: testUser._id
      });

      const res = await request(app)
        .delete(`/api/categories/${category._id}`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.message).toBe('Category deleted');

      const deletedCategory = await Category.findById(category._id);
      expect(deletedCategory).toBeNull();
    });

    it('should return 404 for non-existent category', async () => {
      const fakeId = new mongoose.Types.ObjectId();

      const res = await request(app)
        .delete(`/api/categories/${fakeId}`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(404);
    });
  });
});