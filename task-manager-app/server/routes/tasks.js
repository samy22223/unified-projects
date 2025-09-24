const express = require('express');
const Task = require('../models/Task');
const auth = require('../middleware/auth');
const { validate, schemas } = require('../middleware/validation');

const router = express.Router();

// Get all tasks for the authenticated user with optional search and filters
router.get('/', auth, async (req, res) => {
  try {
    const {
      searchTerm,
      status,
      priority,
      category,
      dueDateFrom,
      dueDateTo,
      createdFrom,
      createdTo
    } = req.query;

    // Build match conditions
    const matchConditions = { user: req.user._id };

    if (status) matchConditions.status = status;
    if (priority) matchConditions.priority = priority;
    if (category) matchConditions.category = category;

    if (dueDateFrom || dueDateTo) {
      matchConditions.dueDate = {};
      if (dueDateFrom) matchConditions.dueDate.$gte = new Date(dueDateFrom);
      if (dueDateTo) matchConditions.dueDate.$lte = new Date(dueDateTo);
    }

    if (createdFrom || createdTo) {
      matchConditions.createdAt = {};
      if (createdFrom) matchConditions.createdAt.$gte = new Date(createdFrom);
      if (createdTo) matchConditions.createdAt.$lte = new Date(createdTo);
    }

    // Use aggregation for search including category name
    let pipeline = [
      { $match: matchConditions },
      {
        $lookup: {
          from: 'categories',
          localField: 'category',
          foreignField: '_id',
          as: 'category'
        }
      },
      { $unwind: { path: '$category', preserveNullAndEmptyArrays: true } }
    ];

    // Add text search if searchTerm provided
    if (searchTerm) {
      const regex = new RegExp(searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'); // escape and case insensitive
      pipeline.push({
        $match: {
          $or: [
            { title: regex },
            { description: regex },
            { 'category.name': regex }
          ]
        }
      });
    }

    pipeline.push({ $sort: { createdAt: -1 } });

    const tasks = await Task.aggregate(pipeline);
    res.json(tasks);
  } catch (error) {
    console.error('Error fetching tasks:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Create a new task
router.post('/', auth, validate(schemas.task), async (req, res) => {
  try {
    const { title, description, dueDate, priority, status, category } = req.body;

    const task = new Task({
      title,
      description,
      dueDate,
      priority,
      status,
      category,
      user: req.user._id
    });

    await task.save();
    await task.populate('category');
    res.status(201).json(task);
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

// Update a task
router.put('/:id', auth, validate(schemas.taskUpdate), async (req, res) => {
  try {
    const task = await Task.findOne({ _id: req.params.id, user: req.user._id });

    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    const { title, description, dueDate, priority, status, category } = req.body;

    task.title = title || task.title;
    task.description = description || task.description;
    task.dueDate = dueDate || task.dueDate;
    task.priority = priority || task.priority;
    task.status = status || task.status;
    task.category = category || task.category;

    await task.save();
    await task.populate('category');
    res.json(task);
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

// Delete a task
router.delete('/:id', auth, async (req, res) => {
  try {
    const task = await Task.findOneAndDelete({ _id: req.params.id, user: req.user._id });

    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    res.json({ message: 'Task deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;