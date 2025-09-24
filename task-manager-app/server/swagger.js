const swaggerJSDoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Task Manager API',
      version: '1.0.0',
      description: 'A comprehensive task management API with user authentication, categories, and analytics'
    },
    servers: [
      {
        url: 'http://localhost:5000',
        description: 'Development server'
      }
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT'
        }
      },
      schemas: {
        User: {
          type: 'object',
          properties: {
            _id: { type: 'string' },
            username: { type: 'string' },
            email: { type: 'string', format: 'email' },
            createdAt: { type: 'string', format: 'date-time' }
          }
        },
        Task: {
          type: 'object',
          properties: {
            _id: { type: 'string' },
            title: { type: 'string' },
            description: { type: 'string' },
            dueDate: { type: 'string', format: 'date' },
            priority: { type: 'string', enum: ['Low', 'Medium', 'High'] },
            status: { type: 'string', enum: ['Pending', 'In Progress', 'Completed'] },
            category: { $ref: '#/components/schemas/Category' },
            user: { type: 'string' },
            createdAt: { type: 'string', format: 'date-time' },
            updatedAt: { type: 'string', format: 'date-time' }
          }
        },
        Category: {
          type: 'object',
          properties: {
            _id: { type: 'string' },
            name: { type: 'string' },
            user: { type: 'string' }
          }
        },
        Error: {
          type: 'object',
          properties: {
            message: { type: 'string' },
            errors: { type: 'array', items: { type: 'object' } }
          }
        }
      }
    },
    security: [
      {
        bearerAuth: []
      }
    ]
  },
  apis: ['./routes/*.js'] // Path to the API routes
};

const specs = swaggerJSDoc(options);

module.exports = { swaggerUi, specs };