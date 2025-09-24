const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const auth = require('../middleware/auth');
const { validate, schemas } = require('../middleware/validation');
const emailService = require('../services/emailService');

const router = express.Router();

/**
 * @swagger
 * /api/auth/register:
 *   post:
 *     summary: Register a new user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - username
 *               - email
 *               - password
 *             properties:
 *               username:
 *                 type: string
 *                 minLength: 3
 *                 maxLength: 30
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *                 minLength: 6
 *     responses:
 *       201:
 *         description: User registered successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 token:
 *                   type: string
 *                 user:
 *                   $ref: '#/components/schemas/User'
 *       400:
 *         description: Validation error or user already exists
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/register', validate(schemas.register), async (req, res) => {
  try {
    const { username, email, password } = req.body;

    // Check if user exists
    const existingUser = await User.findOne({ $or: [{ email }, { username }] });
    if (existingUser) {
      return res.status(400).json({ message: 'User already exists' });
    }

    // Create user
    const user = new User({ username, email, password });
    await user.save();

    // Send welcome email (don't block registration if email fails)
    try {
      await emailService.sendWelcomeEmail(email, username);
    } catch (emailError) {
      console.error('Welcome email failed:', emailError);
      // Continue with registration even if email fails
    }

    // Generate token
    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '7d'
    });

    res.status(201).json({ token, user: { id: user._id, username, email } });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @swagger
 * /api/auth/login:
 *   post:
 *     summary: Login user
 *     tags: [Authentication]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               password:
 *                 type: string
 *     responses:
 *       200:
 *         description: Login successful
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 token:
 *                   type: string
 *                 user:
 *                   $ref: '#/components/schemas/User'
 *       400:
 *         description: Invalid credentials
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Error'
 */
router.post('/login', validate(schemas.login), async (req, res) => {
  try {
    const { email, password } = req.body;

    // Find user
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    // Check password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    // Generate token
    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, {
      expiresIn: process.env.JWT_EXPIRES_IN || '7d'
    });

    res.json({ token, user: { id: user._id, username: user.username, email } });
  } catch (error) {
    res.status(500).json({ message: 'Server error' });
  }
});

// Refresh token endpoint
router.post('/refresh', async (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(401).json({ message: 'No token provided' });
    }

    // Verify the token (this will throw if invalid/expired)
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Generate a new token with the same user data
    const newToken = jwt.sign(
      { userId: decoded.userId },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    res.json({ token: newToken });
  } catch (error) {
    res.status(401).json({ message: 'Invalid or expired token' });
  }
});

// Request password reset
router.post('/forgot-password', validate(schemas.forgotPassword), async (req, res) => {
  try {
    const { email } = req.body;

    const user = await User.findOne({ email });
    if (!user) {
      // Don't reveal if email exists for security
      return res.json({ message: 'If an account with that email exists, a password reset link has been sent.' });
    }

    // Generate reset token (expires in 1 hour)
    const resetToken = jwt.sign(
      { userId: user._id, type: 'password_reset' },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );

    // Send password reset email
    try {
      const resetLink = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/reset-password?token=${resetToken}`;
      await emailService.sendPasswordResetEmail(email, resetToken, resetLink);

      res.json({
        message: 'If an account with that email exists, a password reset link has been sent.',
        // Remove this in production - for development only
        resetToken: process.env.NODE_ENV === 'development' ? resetToken : undefined
      });
    } catch (emailError) {
      console.error('Password reset email failed:', emailError);
      // Still return success to prevent email enumeration attacks
      res.json({
        message: 'If an account with that email exists, a password reset link has been sent.',
        // Remove this in production - for development only
        resetToken: process.env.NODE_ENV === 'development' ? resetToken : undefined
      });
    }
  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Reset password with token
router.post('/reset-password', validate(schemas.resetPassword), async (req, res) => {
  try {
    const { token, newPassword } = req.body;

    if (!token || !newPassword) {
      return res.status(400).json({ message: 'Token and new password are required' });
    }

    // Verify reset token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    if (decoded.type !== 'password_reset') {
      return res.status(400).json({ message: 'Invalid reset token' });
    }

    // Find user and update password
    const user = await User.findById(decoded.userId);
    if (!user) {
      return res.status(400).json({ message: 'Invalid reset token' });
    }

    user.password = newPassword; // Will be hashed by pre-save middleware
    await user.save();

    res.json({ message: 'Password reset successfully' });
  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      return res.status(400).json({ message: 'Invalid or expired reset token' });
    }
    console.error('Reset password error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Get user profile
router.get('/profile', auth, async (req, res) => {
  try {
    const user = await User.findById(req.user._id).select('-password');
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    res.json(user);
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Update user profile
router.put('/profile', auth, validate(schemas.profileUpdate), async (req, res) => {
  try {
    const { username, email } = req.body;
    const userId = req.user._id;

    // Check if new email/username is already taken by another user
    const existingUser = await User.findOne({
      $or: [
        { email, _id: { $ne: userId } },
        { username, _id: { $ne: userId } }
      ]
    });

    if (existingUser) {
      return res.status(400).json({ message: 'Email or username already taken' });
    }

    const updatedUser = await User.findByIdAndUpdate(
      userId,
      { username, email },
      { new: true, runValidators: true }
    ).select('-password');

    res.json(updatedUser);
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

// Change password
router.put('/change-password', auth, validate(schemas.changePassword), async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    const user = await User.findById(req.user._id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Verify current password
    const isMatch = await user.comparePassword(currentPassword);
    if (!isMatch) {
      return res.status(400).json({ message: 'Current password is incorrect' });
    }

    // Update password (will be hashed by pre-save middleware)
    user.password = newPassword;
    await user.save();

    res.json({ message: 'Password changed successfully' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;