const mongoose = require('mongoose');

const taskSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true
  },
  description: {
    type: String,
    trim: true
  },
  dueDate: {
    type: Date
  },
  priority: {
    type: String,
    enum: ['Low', 'Medium', 'High'],
    default: 'Medium'
  },
  status: {
    type: String,
    enum: ['Pending', 'In Progress', 'Completed'],
    default: 'Pending'
  },
  category: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Category'
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// Update the updatedAt field before saving
taskSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// Indexes for performance optimization
taskSchema.index({ user: 1, status: 1 }); // For filtering tasks by user and status
taskSchema.index({ user: 1, priority: 1 }); // For filtering by user and priority
taskSchema.index({ user: 1, category: 1 }); // For filtering by user and category
taskSchema.index({ user: 1, dueDate: 1 }); // For due date queries
taskSchema.index({ user: 1, createdAt: -1 }); // For sorting by creation date
taskSchema.index({ user: 1, updatedAt: -1 }); // For sorting by update date
taskSchema.index({ user: 1, title: 'text', description: 'text' }); // For text search

module.exports = mongoose.model('Task', taskSchema);