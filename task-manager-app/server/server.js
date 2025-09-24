const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { createRateLimitKey } = require('./middleware/sanitization');
const morgan = require('morgan');
const dotenv = require('dotenv');
const { swaggerUi, specs } = require('./swagger');
const logger = require('./logger');
const { sanitizeInput } = require('./middleware/sanitization');
const { errorHandler, notFound } = require('./middleware/errorHandler');
const monitoringService = require('./services/monitoringService');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Security middleware
app.use(helmet({
  contentSecurityPolicy: NODE_ENV === 'production' ? undefined : false
}));

// CORS configuration
const corsOptions = {
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
};
app.use(cors(corsOptions));

// HTTP request logging
app.use(morgan('combined', {
  stream: {
    write: (message) => {
      logger.http(message.trim());
    }
  }
}));

// Rate limiting configurations
const generalLimiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: createRateLimitKey
});

// Stricter rate limiting for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // limit each IP to 5 auth requests per windowMs
  message: {
    error: 'Too many authentication attempts, please try again later.'
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: createRateLimitKey
});

// Apply rate limiting
app.use('/api/auth', authLimiter);
app.use('/api', generalLimiter);

// Input sanitization
app.use(sanitizeInput);

// Request tracking for monitoring
app.use(monitoringService.requestTracker.bind(monitoringService));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Connect to MongoDB (skip in test environment)
if (process.env.NODE_ENV !== 'test') {
  mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/taskmanager', {
    useNewUrlParser: true,
    useUnifiedTopology: true
  })
    .then(() => {
      logger.info('MongoDB connected successfully');
    })
    .catch(err => {
      logger.error('MongoDB connection error:', err);
    });
}

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/tasks', require('./routes/tasks'));
app.use('/api/categories', require('./routes/categories'));
app.use('/api/statistics', require('./routes/statistics'));

// API Documentation
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs));

app.get('/', (req, res) => {
  res.send('Task Management API');
});

// Error handling
app.use(notFound);
app.use(errorHandler);

// Health check endpoint for load balancer monitoring
app.get('/health', async (req, res) => {
  try {
    // Check database connectivity
    await mongoose.connection.db.admin().ping();

    const healthCheck = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      database: {
        status: 'connected',
        name: mongoose.connection.db.databaseName
      },
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0'
    };

    res.status(200).json(healthCheck);
  } catch (error) {
    console.error('Health check failed:', error);
    const healthCheck = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message,
      database: {
        status: 'disconnected'
      }
    };

    res.status(503).json(healthCheck);
  }
});

// Start server (skip in test environment)
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    logger.info(`Server running on port ${PORT} in ${NODE_ENV} mode`);
    logger.info(`API Documentation available at http://localhost:${PORT}/api-docs`);
    logger.info(`Health check available at http://localhost:${PORT}/health`);
  });
}

module.exports = app;
