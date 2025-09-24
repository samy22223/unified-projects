const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../server');
const User = require('../models/User');
const Task = require('../models/Task');
const Category = require('../models/Category');

let mongoServer;
let authToken;
let testUser;
let testCategory;

describe('Task Routes', () => {
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

    // Create test user
    testUser = await User.create({
      username: 'testuser',
      email: 'test@example.com',
      password: 'password123'
    });

    // Create test category
    testCategory = await Category.create({
      name: 'Test Category',
      user: testUser._id
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

  describe('GET /api/tasks', () => {
    it('should get all tasks for authenticated user', async () => {
      await Task.create({
        title: 'Test Task',
        description: 'Test Description',
        user: testUser._id,
        category: testCategory._id
      });

      const res = await request(app)
        .get('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(1);
      expect(res.body[0].title).toBe('Test Task');
    });

    it('should filter tasks by status', async () => {
      await Task.create([
        { title: 'Task 1', status: 'Pending', user: testUser._id },
        { title: 'Task 2', status: 'Completed', user: testUser._id }
      ]);

      const res = await request(app)
        .get('/api/tasks?status=Completed')
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.length).toBe(1);
      expect(res.body[0].status).toBe('Completed');
    });

    it('should search tasks by title', async () => {
      await Task.create([
        { title: 'Buy groceries', user: testUser._id },
        { title: 'Clean house', user: testUser._id }
      ]);

      const res = await request(app)
        .get('/api/tasks?searchTerm=groceries')
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.length).toBe(1);
      expect(res.body[0].title).toBe('Buy groceries');
    });
  });

  describe('POST /api/tasks', () => {
    it('should create a new task', async () => {
      const taskData = {
        title: 'New Task',
        description: 'Task description',
        priority: 'High',
        status: 'Pending',
        category: testCategory._id.toString()
      };

      const res = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send(taskData);

      expect(res.statusCode).toEqual(201);
      expect(res.body.title).toBe('New Task');
      expect(res.body.user).toBe(testUser._id.toString());
    });

    it('should validate required fields', async () => {
      const res = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${authToken}`)
        .send({});

      expect(res.statusCode).toEqual(400);
    });
  });

  describe('PUT /api/tasks/:id', () => {
    it('should update a task', async () => {
      const task = await Task.create({
        title: 'Original Task',
        user: testUser._id
      });

      const updateData = {
        title: 'Updated Task',
        status: 'Completed'
      };

      const res = await request(app)
        .put(`/api/tasks/${task._id}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send(updateData);

      expect(res.statusCode).toEqual(200);
      expect(res.body.title).toBe('Updated Task');
      expect(res.body.status).toBe('Completed');
    });

    it('should return 404 for non-existent task', async () => {
      const fakeId = new mongoose.Types.ObjectId();

      const res = await request(app)
        .put(`/api/tasks/${fakeId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ title: 'Updated' });

      expect(res.statusCode).toEqual(404);
    });
  });

  describe('DELETE /api/tasks/:id', () => {
    it('should delete a task', async () => {
      const task = await Task.create({
        title: 'Task to Delete',
        user: testUser._id
      });

      const res = await request(app)
        .delete(`/api/tasks/${task._id}`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.message).toBe('Task deleted');

      const deletedTask = await Task.findById(task._id);
      expect(deletedTask).toBeNull();
    });

    it('should return 404 for non-existent task', async () => {
      const fakeId = new mongoose.Types.ObjectId();

      const res = await request(app)
        .delete(`/api/tasks/${fakeId}`)
        .set('Authorization', `Bearer ${authToken}`);

      expect(res.statusCode).toEqual(404);
    });
  });
});