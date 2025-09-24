const mongoose = require('mongoose');

const categorySchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Ensure category names are unique per user
categorySchema.index({ name: 1, user: 1 }, { unique: true });

// Additional indexes for performance
categorySchema.index({ user: 1, createdAt: -1 }); // For listing user categories by creation date

module.exports = mongoose.model('Category', categorySchema);