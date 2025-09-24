const express = require('express');
const Category = require('../models/Category');
const auth = require('../middleware/auth');
const { validate, schemas } = require('../middleware/validation');

const router = express.Router();

// Get all categories for the authenticated user
router.get('/', auth, async (req, res) => {
  try {
    const categories = await Category.find({ user: req.user._id }).sort({ createdAt: -1 });
    res.json(categories);
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

// Create a new category
router.post('/', auth, validate(schemas.category), async (req, res) => {
  try {
    const { name } = req.body;

    const category = new Category({
      name,
      user: req.user._id
    });

    await category.save();
    res.status(201).json(category);
  } catch (error) {
    if (error.code === 11000) {
      res.status(400).json({ message: 'Category name already exists' });
    } else {
      res.status(500).json({ message: 'Server error' });
    }
  }
});

// Update a category
router.put('/:id', auth, validate(schemas.categoryUpdate), async (req, res) => {
  try {
    const category = await Category.findOne({ _id: req.params.id, user: req.user._id });

    if (!category) {
      return res.status(404).json({ message: 'Category not found' });
    }

    const { name } = req.body;

    category.name = name || category.name;

    await category.save();
    res.json(category);
  } catch (error) {
    if (error.code === 11000) {
      res.status(400).json({ message: 'Category name already exists' });
    } else {
      res.status(500).json({ message: 'Server error' });
    }
  }
});

// Delete a category
router.delete('/:id', auth, async (req, res) => {
  try {
    const category = await Category.findOneAndDelete({ _id: req.params.id, user: req.user._id });

    if (!category) {
      return res.status(404).json({ message: 'Category not found' });
    }

    res.json({ message: 'Category deleted' });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;