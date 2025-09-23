# System Architecture

## Overview
The task management web app follows a client-server architecture with a React frontend, Node.js/Express backend, and MongoDB database.

## Frontend
- **Framework**: React.js
- **Key Components**:
  - App: Main application component
  - TaskList: Displays list of tasks
  - TaskItem: Individual task display
  - AddTaskForm: Form for creating new tasks
  - EditTaskForm: Form for editing tasks
  - LoginForm/RegisterForm: Authentication forms
  - Dashboard: Overview of tasks
- **State Management**: React Context API for global state
- **Routing**: React Router for navigation
- **Styling**: CSS modules or styled-components

## Backend
- **Runtime**: Node.js
- **Framework**: Express.js
- **API Endpoints**:
  - `POST /api/auth/register` - User registration
  - `POST /api/auth/login` - User login
  - `GET /api/tasks` - Get all user tasks
  - `POST /api/tasks` - Create new task
  - `PUT /api/tasks/:id` - Update task
  - `DELETE /api/tasks/:id` - Delete task
  - `GET /api/categories` - Get task categories
- **Middleware**:
  - Authentication middleware for protected routes
  - CORS for cross-origin requests
  - Body parsing for JSON

## Database
- **Database**: MongoDB
- **ODM**: Mongoose
- **Collections**:
  - Users: { username, email, passwordHash, createdAt }
  - Tasks: { title, description, dueDate, priority, status, category, userId, createdAt, updatedAt }
  - Categories: { name, userId }

## Authentication
- **Method**: JSON Web Tokens (JWT)
- **Storage**: Tokens stored in browser localStorage
- **Security**: Passwords hashed with bcrypt
- **Session Management**: Token expiration and refresh

## Data Flow
1. User logs in → JWT token generated and sent to client
2. Client includes token in Authorization header for API requests
3. Server validates token and processes request
4. Data retrieved from/sent to MongoDB
5. Response sent back to client

## Deployment
- **Frontend**: Deployed as static files to Netlify or Vercel
- **Backend**: Deployed to Heroku or AWS
- **Database**: MongoDB Atlas cloud database
- **Environment Variables**: Used for sensitive data (DB URI, JWT secret)