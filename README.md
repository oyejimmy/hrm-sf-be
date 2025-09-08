# HRM System - Comprehensive Human Resource Management Platform

A full-stack Human Resource Management system built with FastAPI (backend) and React with TypeScript (frontend).

## 🚀 Features

### User Roles & Permissions
- **Admin**: Full system access and management
- **HR**: Employee management, attendance, leave, training, performance
- **Team Lead**: Team management and approvals
- **Employee**: Personal dashboard, leave requests, attendance, payslips

### Core Modules
- **Authentication & Authorization**: JWT-based with role-based access control
- **Employee Management**: Complete employee lifecycle management
- **Attendance Tracking**: Real-time attendance logging and monitoring
- **Leave Management**: Leave requests, approvals, and balance tracking
- **Performance Management**: Reviews, scoring, and analytics
- **Training Management**: Training programs and enrollment tracking
- **Document Management**: Secure document storage and sharing
- **Reports & Analytics**: Comprehensive reporting and dashboard analytics
- **Recruitment**: Job postings and application management
- **Communication**: Notifications and announcements

## 🛠 Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLite**: Lightweight SQL database with SQLAlchemy ORM
- **JWT**: Secure authentication with refresh tokens
- **Pydantic**: Data validation and serialization
- **Python-Jose**: JWT token handling
- **Passlib**: Password hashing with bcrypt
- **SQLAlchemy**: Modern Python SQL toolkit and ORM

### Frontend
- **React 19**: Latest React with TypeScript
- **Ant Design**: Comprehensive UI component library
- **Redux Toolkit**: State management
- **React Router**: Client-side routing
- **Styled Components**: CSS-in-JS styling
- **Axios**: HTTP client with interceptors
- **React Query**: Server state management

## 📁 Project Structure

```
HRM/
├── hrm-be/                 # Backend (FastAPI)
│   ├── app/
│   │   ├── core/          # Core configuration and utilities
│   │   ├── db/            # Database connection and setup
│   │   ├── models/        # Pydantic models
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # Business logic services
│   │   └── main.py        # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
├── hrm-fe/                # Frontend (React + TypeScript)
│   ├── app/
│   │   ├── components/    # Reusable UI components
│   │   ├── features/      # Feature-based modules
│   │   ├── store/         # Redux store and slices
│   │   ├── services/      # API services
│   │   ├── styles/        # Global styles and theme
│   │   └── App.tsx        # Main application component
│   └── package.json       # Node.js dependencies
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd hrm-be
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the `hrm-be` directory:
   ```env
   DATABASE_NAME=hrm_system
   SECRET_KEY=your-super-secret-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ENVIRONMENT=development
   DEBUG=True
   ```

5. **Initialize the database**:
   ```bash
   python init_db.py
   ```
   This will create the SQLite database and optionally create an admin user.

6. **Run the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd hrm-fe
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   Create a `.env` file in the `hrm-fe` directory:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

   The application will be available at `http://localhost:3000`

## 🔐 Authentication

The system uses JWT-based authentication with the following endpoints:

- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Get current user info
- `POST /auth/logout` - User logout

## 📊 API Endpoints

### Authentication
- `/auth/*` - Authentication and user management

### Employee Management
- `/employees/*` - Employee CRUD operations
- `/employees/profile/{user_id}` - Employee profile management

### Attendance
- `/attendance/log` - Log attendance
- `/attendance/today` - Get today's attendance
- `/attendance/user/{user_id}` - Get user attendance history
- `/attendance/summary/{user_id}` - Get attendance summary

### Leave Management
- `/leave/request` - Create leave request
- `/leave/my-requests` - Get user's leave requests
- `/leave/pending` - Get pending leave requests (HR)
- `/leave/approve/{request_id}` - Approve/reject leave request
- `/leave/balance/{user_id}` - Get leave balance

### Reports & Analytics
- `/reports/dashboard-stats` - Dashboard statistics
- `/reports/attendance-report` - Attendance reports
- `/reports/leave-report` - Leave reports
- `/reports/employee-summary/{user_id}` - Employee summary

### Additional Modules
- `/recruitment/*` - Recruitment management
- `/performance/*` - Performance management
- `/training/*` - Training management
- `/documents/*` - Document management
- `/notifications/*` - Notification system
- `/announcements/*` - Announcement management

## 🎨 UI/UX Features

- **Responsive Design**: Mobile-first approach with Ant Design
- **Dark/Light Theme**: Theme provider with styled-components
- **Role-based Navigation**: Dynamic sidebar based on user role
- **Real-time Updates**: Live data updates and notifications
- **Accessibility**: WCAG compliant components
- **Print Support**: Optimized for printing reports

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access Control**: Granular permissions system
- **Password Hashing**: Bcrypt password hashing
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic model validation
- **SQL Injection Protection**: MongoDB with parameterized queries

## 📈 Performance & Scalability

- **Async/Await**: Non-blocking I/O operations
- **Database Indexing**: Optimized MongoDB indexes
- **Caching**: Redis integration ready
- **Pagination**: Efficient data loading
- **Lazy Loading**: Component-based code splitting
- **API Rate Limiting**: Built-in rate limiting support

## 🧪 Testing

### Backend Testing
```bash
cd hrm-be
pytest tests/ -v
```

### Frontend Testing
```bash
cd hrm-fe
npm test
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Environment
1. Set `ENVIRONMENT=production` in backend `.env`
2. Update `SECRET_KEY` with a secure random key
3. Configure production MongoDB connection
4. Set up reverse proxy (nginx)
5. Enable HTTPS/SSL certificates

## 📝 Development Guidelines

### Backend Development
- Follow PEP 8 Python style guide
- Use type hints for all functions
- Write comprehensive docstrings
- Implement proper error handling
- Use async/await for I/O operations

### Frontend Development
- Use TypeScript for type safety
- Follow React best practices
- Implement proper error boundaries
- Use Redux Toolkit for state management
- Write unit tests for components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs` endpoint
- Review the code comments and docstrings

## 🔮 Future Enhancements

- **Payroll Automation**: Automated salary calculations
- **AI Analytics**: Machine learning for performance insights
- **Mobile App**: React Native mobile application
- **Chatbot Integration**: AI-powered HR assistant
- **Multi-language Support**: Internationalization
- **Advanced Reporting**: Custom report builder
- **Integration APIs**: Third-party service integrations
- **Workflow Automation**: Business process automation

---

**Built with ❤️ for modern HR management**
