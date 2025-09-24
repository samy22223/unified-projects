const Joi = require('joi');

// Validation middleware function
const validate = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body, { abortEarly: false });
    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));
      return res.status(400).json({
        message: 'Validation error',
        errors
      });
    }
    next();
  };
};

// Validation schemas
const schemas = {
  // Auth schemas
  register: Joi.object({
    username: Joi.string()
      .min(3)
      .max(30)
      .required()
      .messages({
        'string.empty': 'Username is required',
        'string.min': 'Username must be at least 3 characters long',
        'string.max': 'Username must be less than 30 characters long',
        'any.required': 'Username is required'
      }),
    email: Joi.string()
      .email()
      .required()
      .messages({
        'string.empty': 'Email is required',
        'string.email': 'Please provide a valid email address',
        'any.required': 'Email is required'
      }),
    password: Joi.string()
      .min(6)
      .required()
      .messages({
        'string.empty': 'Password is required',
        'string.min': 'Password must be at least 6 characters long',
        'any.required': 'Password is required'
      })
  }),

  login: Joi.object({
    email: Joi.string()
      .email()
      .required()
      .messages({
        'string.empty': 'Email is required',
        'string.email': 'Please provide a valid email address',
        'any.required': 'Email is required'
      }),
    password: Joi.string()
      .required()
      .messages({
        'string.empty': 'Password is required',
        'any.required': 'Password is required'
      })
  }),

  // Task schemas
  task: Joi.object({
    title: Joi.string()
      .min(1)
      .max(100)
      .required()
      .messages({
        'string.empty': 'Title is required',
        'string.min': 'Title cannot be empty',
        'string.max': 'Title must be less than 100 characters',
        'any.required': 'Title is required'
      }),
    description: Joi.string()
      .max(500)
      .allow('')
      .messages({
        'string.max': 'Description must be less than 500 characters'
      }),
    dueDate: Joi.date()
      .optional()
      .messages({
        'date.base': 'Due date must be a valid date'
      }),
    priority: Joi.string()
      .valid('Low', 'Medium', 'High')
      .default('Medium')
      .messages({
        'any.only': 'Priority must be Low, Medium, or High'
      }),
    status: Joi.string()
      .valid('Pending', 'In Progress', 'Completed')
      .default('Pending')
      .messages({
        'any.only': 'Status must be Pending, In Progress, or Completed'
      }),
    category: Joi.string()
      .optional()
      .allow('')
      .messages({
        'string.base': 'Category must be a valid string'
      })
  }),

  taskUpdate: Joi.object({
    title: Joi.string()
      .min(1)
      .max(100)
      .messages({
        'string.empty': 'Title cannot be empty',
        'string.min': 'Title cannot be empty',
        'string.max': 'Title must be less than 100 characters'
      }),
    description: Joi.string()
      .max(500)
      .allow('')
      .messages({
        'string.max': 'Description must be less than 500 characters'
      }),
    dueDate: Joi.date()
      .optional()
      .messages({
        'date.base': 'Due date must be a valid date'
      }),
    priority: Joi.string()
      .valid('Low', 'Medium', 'High')
      .messages({
        'any.only': 'Priority must be Low, Medium, or High'
      }),
    status: Joi.string()
      .valid('Pending', 'In Progress', 'Completed')
      .messages({
        'any.only': 'Status must be Pending, In Progress, or Completed'
      }),
    category: Joi.string()
      .optional()
      .allow('')
      .messages({
        'string.base': 'Category must be a valid string'
      })
  }),

  // Category schemas
  category: Joi.object({
    name: Joi.string()
      .min(1)
      .max(50)
      .required()
      .messages({
        'string.empty': 'Category name is required',
        'string.min': 'Category name cannot be empty',
        'string.max': 'Category name must be less than 50 characters',
        'any.required': 'Category name is required'
      })
  }),

  categoryUpdate: Joi.object({
    name: Joi.string()
      .min(1)
      .max(50)
      .messages({
        'string.empty': 'Category name cannot be empty',
        'string.min': 'Category name cannot be empty',
        'string.max': 'Category name must be less than 50 characters'
      })
  }),

  // Profile and password schemas
  profileUpdate: Joi.object({
    username: Joi.string()
      .min(3)
      .max(30)
      .messages({
        'string.min': 'Username must be at least 3 characters long',
        'string.max': 'Username must be less than 30 characters long'
      }),
    email: Joi.string()
      .email()
      .messages({
        'string.email': 'Please provide a valid email address'
      })
  }),

  changePassword: Joi.object({
    currentPassword: Joi.string()
      .required()
      .messages({
        'string.empty': 'Current password is required',
        'any.required': 'Current password is required'
      }),
    newPassword: Joi.string()
      .min(6)
      .required()
      .messages({
        'string.empty': 'New password is required',
        'string.min': 'New password must be at least 6 characters long',
        'any.required': 'New password is required'
      })
  }),

  forgotPassword: Joi.object({
    email: Joi.string()
      .email()
      .required()
      .messages({
        'string.empty': 'Email is required',
        'string.email': 'Please provide a valid email address',
        'any.required': 'Email is required'
      })
  }),

  resetPassword: Joi.object({
    token: Joi.string()
      .required()
      .messages({
        'string.empty': 'Reset token is required',
        'any.required': 'Reset token is required'
      }),
    newPassword: Joi.string()
      .min(6)
      .required()
      .messages({
        'string.empty': 'New password is required',
        'string.min': 'New password must be at least 6 characters long',
        'any.required': 'New password is required'
      })
  })
};

module.exports = {
  validate,
  schemas
};