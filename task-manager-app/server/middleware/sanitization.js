const validator = require('validator');
const xss = require('xss');

// Input sanitization middleware
const sanitizeInput = (req, res, next) => {
  // Sanitize query parameters
  if (req.query) {
    sanitizeObject(req.query);
  }

  // Sanitize route parameters
  if (req.params) {
    sanitizeObject(req.params);
  }

  // Sanitize body
  if (req.body) {
    sanitizeObject(req.body);
  }

  next();
};

// Recursive function to sanitize objects
const sanitizeObject = (obj) => {
  for (let key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      if (typeof obj[key] === 'string') {
        // Trim whitespace
        obj[key] = validator.trim(obj[key]);

        // Escape HTML/XSS
        obj[key] = xss(obj[key]);

        // Validate and normalize email if it looks like an email
        if (validator.isEmail(obj[key])) {
          obj[key] = validator.normalizeEmail(obj[key]);
        }

        // Escape special characters for MongoDB
        obj[key] = escapeMongoSpecialChars(obj[key]);
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        sanitizeObject(obj[key]);
      }
    }
  }
};

// Escape MongoDB special characters to prevent NoSQL injection
const escapeMongoSpecialChars = (str) => {
  // Simple approach: escape $ and . characters which are commonly used in injection
  return str.replace(/\$/g, '\\$').replace(/\./g, '\\.');
};

// Validate and sanitize file uploads (if implemented later)
const sanitizeFileUpload = (req, res, next) => {
  if (req.file) {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (!allowedTypes.includes(req.file.mimetype)) {
      return res.status(400).json({ message: 'Invalid file type' });
    }

    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (req.file.size > maxSize) {
      return res.status(400).json({ message: 'File too large' });
    }

    // Sanitize filename
    req.file.originalname = validator.escape(req.file.originalname);
  }

  if (req.files) {
    req.files.forEach(file => {
      file.originalname = validator.escape(file.originalname);
    });
  }

  next();
};

// Rate limiting helper (complements express-rate-limit)
const createRateLimitKey = (req) => {
  // Create a unique key based on IP and user ID (if authenticated)
  const ip = req.ip || req.connection.remoteAddress;
  const userId = req.user ? req.user._id : 'anonymous';
  return `${ip}:${userId}`;
};

module.exports = {
  sanitizeInput,
  sanitizeFileUpload,
  createRateLimitKey
};