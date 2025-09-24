# Task Manager App

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-blue.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)

A comprehensive MERN stack task management application with analytics dashboard, user authentication, and advanced task organization features.

## 🚀 Features

- **User Authentication**: Secure registration and login with JWT tokens
- **Task Management**: Full CRUD operations for tasks with categories and priorities
- **Advanced Filtering**: Search, filter, and sort tasks by various criteria
- **Statistics Dashboard**: Visual analytics and insights on task completion
- **Responsive Design**: Mobile-friendly interface built with React
- **Real-time Updates**: Live task status updates
- **Category Management**: Organize tasks into custom categories
- **Priority Levels**: Set task priorities (Low, Medium, High)
- **Due Date Tracking**: Set and track task deadlines

## 📋 Prerequisites

- **Node.js** (v18 or higher)
- **MongoDB** (v4.4 or higher)
- **npm** or **yarn**

## 🛠 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/task-manager-app.git
cd task-manager-app
```

### 2. Environment Configuration
Copy the example environment file and configure your settings:
```bash
cp server/.env.example server/.env
```

Edit `server/.env` with your actual values:
```env
MONGODB_URI=mongodb://localhost:27017/taskmanager
JWT_SECRET=your_super_secret_jwt_key_here
PORT=5000
```

### 3. Database Setup

**Option 1: Docker (Recommended)**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Option 2: MongoDB Atlas**
- Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
- Get connection string and update `MONGODB_URI`

**Option 3: Local Installation**
```bash
# macOS with Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### 4. Install Dependencies

**Server:**
```bash
cd server
npm install
```

**Client:**
```bash
cd ../client
npm install
```

### 5. Start the Application

**Development Mode:**
```bash
# Terminal 1: Start server
cd server
npm run dev

# Terminal 2: Start client
cd ../client
npm start
```

**Production Mode:**
```bash
# Server
cd server
npm start

# Client (after building)
cd client
npm run build
npm run serve
```

Visit `http://localhost:3000` for the client and `http://localhost:5000` for the API.

### Docker Development Setup (Recommended)
For easier development with all services running together:
```bash
# From the project root directory
docker-compose up -d
```
This will start:
- MongoDB on port 27017
- Backend API on port 5000
- Frontend on port 3000
- Analytics service on port 8001
- Compliance service on port 8002

### Firefox Extension
Install the browser extension for quick task creation:
1. Open Firefox and go to `about:debugging`
2. Click "This Firefox" → "Load Temporary Add-on"
3. Select `firefox-extension/manifest.json`
4. Configure the extension with your API URL and auth token

## 🔧 Configuration

### Environment Variables
See `server/.env.example` for all available configuration options.

### Database
The application uses MongoDB with the following collections:
- `users`: User accounts and authentication
- `tasks`: Task data with relationships
- `categories`: Task categories

## 📖 Usage

### Basic Operations
1. **Register**: Create a new account
2. **Login**: Authenticate with email/password
3. **Create Tasks**: Add new tasks with title, description, category, priority, and due date
4. **Manage Categories**: Create and organize task categories
5. **View Dashboard**: Monitor task statistics and progress

### API Usage
The REST API is available at `http://localhost:5000/api`

#### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

#### Task Endpoints
- `GET /api/tasks` - Get all user tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task

#### Category Endpoints
- `GET /api/categories` - Get all categories
- `POST /api/categories` - Create category
- `PUT /api/categories/:id` - Update category
- `DELETE /api/categories/:id` - Delete category

## 🧪 Testing

Run the test suite:
```bash
cd server
npm test
```

## 🚀 Deployment

### Backend Deployment (Heroku)
1. Create Heroku app
2. Set environment variables in Heroku dashboard
3. Deploy server directory

### Frontend Deployment (Vercel/Netlify)
1. Build the client: `cd client && npm run build`
2. Deploy `client/build` folder to Vercel or Netlify
3. Configure API base URL to point to deployed backend

### Database
Use MongoDB Atlas for production deployments.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add some feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Development Guidelines
- Follow ESLint configuration
- Write tests for new features
- Update documentation as needed
- Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with the MERN stack
- UI components inspired by modern design principles
- Thanks to the open-source community for amazing tools and libraries

## 📞 Support

If you have any questions or issues, please open an issue on GitHub or contact the maintainers.