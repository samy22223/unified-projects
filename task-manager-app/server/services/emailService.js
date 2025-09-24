const nodemailer = require('nodemailer');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: process.env.SMTP_PORT || 587,
      secure: false, // true for 465, false for other ports
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });
  }

  async sendPasswordResetEmail(email, resetToken, resetLink) {
    const mailOptions = {
      from: `"Task Manager" <${process.env.SMTP_USER}>`,
      to: email,
      subject: 'Password Reset Request',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">Password Reset Request</h2>
          <p>You requested a password reset for your Task Manager account.</p>
          <p>Click the link below to reset your password:</p>
          <a href="${resetLink}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">Reset Password</a>
          <p><strong>This link will expire in 1 hour.</strong></p>
          <p>If you didn't request this password reset, please ignore this email.</p>
          <hr>
          <p style="color: #666; font-size: 12px;">If the button doesn't work, copy and paste this link into your browser:<br>${resetLink}</p>
        </div>
      `,
      text: `
        Password Reset Request

        You requested a password reset for your Task Manager account.

        Reset your password: ${resetLink}

        This link will expire in 1 hour.

        If you didn't request this password reset, please ignore this email.
      `
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      console.log('Password reset email sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('Error sending password reset email:', error);
      throw new Error('Failed to send password reset email');
    }
  }

  async sendWelcomeEmail(email, username) {
    const mailOptions = {
      from: `"Task Manager" <${process.env.SMTP_USER}>`,
      to: email,
      subject: 'Welcome to Task Manager!',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">Welcome to Task Manager, ${username}!</h2>
          <p>Thank you for joining Task Manager. We're excited to help you stay organized and productive.</p>
          <p>Get started by:</p>
          <ul>
            <li>Creating your first task</li>
            <li>Setting up categories for better organization</li>
            <li>Exploring the statistics dashboard</li>
          </ul>
          <a href="${process.env.FRONTEND_URL || 'http://localhost:3000'}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">Get Started</a>
          <p>Happy task managing!</p>
        </div>
      `,
      text: `
        Welcome to Task Manager, ${username}!

        Thank you for joining Task Manager. We're excited to help you stay organized and productive.

        Get started by visiting: ${process.env.FRONTEND_URL || 'http://localhost:3000'}

        Happy task managing!
      `
    };

    try {
      const info = await this.transporter.sendMail(mailOptions);
      console.log('Welcome email sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('Error sending welcome email:', error);
      // Don't throw error for welcome emails - they're not critical
      return { success: false, error: error.message };
    }
  }

  async verifyConnection() {
    try {
      await this.transporter.verify();
      return true;
    } catch (error) {
      console.error('Email service connection failed:', error);
      return false;
    }
  }
}

module.exports = new EmailService();