const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../server');
const User = require('../models/User');
const Task = require('../models/Task');
const Category = require('../models/Category');

let mongoServer;
let token;
let userId;
let categoryId;

describe('Task Routes', () => {
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

    // Create test category
    const category = await Category.create({
      name: 'Test Category',
      user: userId
    });
    categoryId = category._id;

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
    await Task.deleteMany({});
  });

  describe('POST /api/tasks', () => {
    it('should create a new task', async () => {
      const taskData = {
        title: 'Test Task',
        description: 'This is a test task',
        priority: 'High',
        status: 'Pending',
        category: categoryId
      };

      const res = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${token}`)
        .send(taskData);

      expect(res.statusCode).toEqual(201);
      expect(res.body).toHaveProperty('title', 'Test Task');
      expect(res.body).toHaveProperty('user');
    });

    it('should not create task without title', async () => {
      const taskData = {
        description: 'This is a test task',
        priority: 'High'
      };

      const res = await request(app)
        .post('/api/tasks')
        .set('Authorization', `Bearer ${token}`)
        .send(taskData);

      expect(res.statusCode).toEqual(400);
    });
  });

  describe('GET /api/tasks', () => {
    beforeEach(async () => {
      await Task.create([
        {
          title: 'Task 1',
          description: 'Description 1',
          priority: 'High',
          status: 'Pending',
          user: userId,
          category: categoryId
        },
        {
          title: 'Task 2',
          description: 'Description 2',
          priority: 'Medium',
          status: 'Completed',
          user: userId
        }
      ]);
    });

    it('should get all tasks for user', async () => {
      const res = await request(app)
        .get('/api/tasks')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(Array.isArray(res.body)).toBe(true);
      expect(res.body.length).toBe(2);
    });

    it('should filter tasks by status', async () => {
      const res = await request(app)
        .get('/api/tasks?status=Completed')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.length).toBe(1);
      expect(res.body[0].status).toBe('Completed');
    });

    it('should search tasks by title', async () => {
      const res = await request(app)
        .get('/api/tasks?searchTerm=Task 1')
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body.length).toBe(1);
      expect(res.body[0].title).toBe('Task 1');
    });
  });

  describe('PUT /api/tasks/:id', () => {
    let taskId;

    beforeEach(async () => {
      const task = await Task.create({
        title: 'Original Task',
        description: 'Original description',
        priority: 'Medium',
        status: 'Pending',
        user: userId
      });
      taskId = task._id;
    });

    it('should update a task', async () => {
      const updateData = {
        title: 'Updated Task',
        status: 'Completed'
      };

      const res = await request(app)
        .put(`/api/tasks/${taskId}`)
        .set('Authorization', `Bearer ${token}`)
        .send(updateData);

      expect(res.statusCode).toEqual(200);
      expect(res.body.title).toBe('Updated Task');
      expect(res.body.status).toBe('Completed');
    });

    it('should not update task of another user', async () => {
      // Create another user
      const otherUser = await User.create({
        username: 'otheruser',
        email: 'other@example.com',
        password: 'password123'
      });

      const otherTask = await Task.create({
        title: 'Other User Task',
        user: otherUser._id
      });

      const res = await request(app)
        .put(`/api/tasks/${otherTask._id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({ title: 'Hacked Title' });

      expect(res.statusCode).toEqual(404);
    });
  });

  describe('DELETE /api/tasks/:id', () => {
    let taskId;

    beforeEach(async () => {
      const task = await Task.create({
        title: 'Task to Delete',
        user: userId
      });
      taskId = task._id;
    });

    it('should delete a task', async () => {
      const res = await request(app)
        .delete(`/api/tasks/${taskId}`)
        .set('Authorization', `Bearer ${token}`);

      expect(res.statusCode).toEqual(200);
      expect(res.body).toHaveProperty('message', 'Task deleted');

      // Verify task is deleted
      const deletedTask = await Task.findById(taskId);
      expect(deletedTask).toBeNull();
    });
  });
});