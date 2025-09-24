# HRM System Backend

A comprehensive Human Resource Management System backend built with FastAPI, SQLAlchemy, and SQLite.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **User Management**: User registration, login, profile management
- **Employee Management**: Complete employee lifecycle management
- **Leave Management**: Leave request, approval, and tracking system
- **Attendance Management**: Check-in/check-out functionality with tracking
- **Performance Management**: Performance review system
- **Role-Based Access**: Admin, HR, Team Lead, and Employee roles

## Database Schema

### Tables
- **users**: User authentication and basic profile
- **employees**: Detailed employee information
- **departments**: Department management
- **leaves**: Leave request management
- **attendance**: Daily attendance tracking
- **performance_reviews**: Performance evaluation records

### Relationships
- User (1:1) Employee
- Department (1:N) Employee
- Employee (1:N) Employee (Manager-Subordinate)
- User (1:N) Leave (Employee-Leaves)
- User (1:N) Attendance (Employee-Attendance)
- User (1:N) Performance (Employee-Reviews)

## API Endpoints

### Authentication
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `PUT /auth/profile/me` - Complete user profile

### Employees
- `GET /api/employees/` - List employees (Admin/HR)
- `GET /api/employees/me` - Get my profile
- `GET /api/employees/{id}` - Get employee by ID
- `POST /api/employees/` - Create employee (Admin/HR)
- `PUT /api/employees/{id}` - Update employee (Admin/HR)
- `DELETE /api/employees/{id}` - Delete employee (Admin)

### Leave Management
- `GET /api/leaves/` - List leave requests
- `GET /api/leaves/my-leaves` - Get my leave requests
- `POST /api/leaves/` - Create leave request
- `PUT /api/leaves/{id}/approve` - Approve leave
- `PUT /api/leaves/{id}/reject` - Reject leave
- `DELETE /api/leaves/{id}` - Cancel leave request

### Attendance
- `GET /api/attendance/` - List attendance records
- `GET /api/attendance/my-attendance` - Get my attendance
- `GET /api/attendance/today` - Get today's attendance
- `POST /api/attendance/check-in` - Check in
- `POST /api/attendance/check-out` - Check out
- `POST /api/attendance/` - Create attendance record (Admin/HR)

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   cd hrm-be
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   copy .env.example .env  # Windows
   # cp .env.example .env  # Linux/Mac
   ```
   
   Edit `.env` file with your configuration:
   ```
   DATABASE_URL=sqlite:///./hrm.db
   SECRET_KEY=your-secret-key-here-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`

### Default Users

After running `init_db.py`, the following users will be created:

- **Admin**: admin@hrm.com / admin123
- **HR Manager**: hr@hrm.com / hr123  
- **Employee**: employee@hrm.com / emp123

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Role-Based Access Control

### Admin
- Full system access
- Manage all users and employees
- View all data and reports
- System configuration

### HR
- Employee management access
- Leave approval and management
- Attendance management
- Performance review access

### Team Lead
- Team-specific access
- Approve team member leaves
- View team attendance and performance
- Limited employee management for team

### Employee
- Personal data access only
- Submit leave requests
- View own attendance and performance
- Update personal profile

## Security Features

- JWT token authentication
- Password hashing with bcrypt
- Role-based authorization
- Token refresh mechanism
- Input validation and sanitization
- SQL injection protection via SQLAlchemy ORM

## Development

### Project Structure
```
hrm-be/
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API route handlers
│   ├── auth.py          # Authentication utilities
│   ├── config.py        # Configuration settings
│   ├── database.py      # Database connection
│   └── main.py          # FastAPI application
├── requirements.txt     # Python dependencies
├── init_db.py          # Database initialization
├── run.py              # Application runner
└── README.md           # This file
```

### Adding New Features

1. Create database model in `app/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Create API routes in `app/routers/`
4. Update `app/main.py` to include new router
5. Run database migrations if needed

## Production Deployment

1. **Environment Setup**
   - Use PostgreSQL instead of SQLite for production
   - Set strong SECRET_KEY
   - Configure proper CORS origins
   - Set up SSL/HTTPS

2. **Security Considerations**
   - Use environment variables for sensitive data
   - Implement rate limiting
   - Add request logging
   - Set up monitoring and alerting

3. **Performance Optimization**
   - Add database indexes
   - Implement caching
   - Use connection pooling
   - Add pagination for large datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.