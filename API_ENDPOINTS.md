# HRM System API Endpoints

This document provides a comprehensive list of all API endpoints available in the HRM System.

## Base URL
```
http://localhost:8000
```

## Authentication Endpoints
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `PUT /auth/profile/me` - Complete user profile

## Employee Management
- `GET /api/employees/` - List employees (Admin/HR)
- `GET /api/employees/me` - Get my profile
- `GET /api/employees/{id}` - Get employee by ID
- `POST /api/employees/` - Create employee (Admin/HR)
- `PUT /api/employees/{id}` - Update employee (Admin/HR)
- `DELETE /api/employees/{id}` - Delete employee (Admin)

## Leave Management
- `GET /api/leaves/` - List leave requests
- `GET /api/leaves/my-leaves` - Get my leave requests
- `POST /api/leaves/` - Create leave request
- `PUT /api/leaves/{id}/approve` - Approve leave
- `PUT /api/leaves/{id}/reject` - Reject leave
- `DELETE /api/leaves/{id}` - Cancel leave request

## Attendance Management
- `GET /api/attendance/` - List attendance records
- `GET /api/attendance/my-attendance` - Get my attendance
- `GET /api/attendance/today` - Get today's attendance
- `POST /api/attendance/check-in` - Check in
- `POST /api/attendance/check-out` - Check out
- `POST /api/attendance/` - Create attendance record (Admin/HR)

## Asset Management
- `GET /api/assets/` - List assets
- `GET /api/assets/{id}` - Get asset by ID
- `POST /api/assets/` - Create asset (Admin/HR)
- `PUT /api/assets/{id}` - Update asset (Admin/HR)
- `DELETE /api/assets/{id}` - Delete asset (Admin)
- `GET /api/assets/requests/` - List asset requests
- `POST /api/assets/requests/` - Create asset request
- `PUT /api/assets/requests/{id}/approve` - Approve asset request
- `PUT /api/assets/requests/{id}/reject` - Reject asset request

## Complaint Management
- `GET /api/complaints/` - List complaints
- `GET /api/complaints/{id}` - Get complaint by ID
- `POST /api/complaints/` - Create complaint
- `PUT /api/complaints/{id}` - Update complaint
- `DELETE /api/complaints/{id}` - Delete complaint
- `GET /api/complaints/{id}/comments` - Get complaint comments
- `POST /api/complaints/{id}/comments` - Add complaint comment
- `PUT /api/complaints/{id}/assign` - Assign complaint
- `PUT /api/complaints/{id}/resolve` - Resolve complaint

## Document Management
- `GET /api/documents/` - List documents
- `GET /api/documents/{id}` - Get document by ID
- `POST /api/documents/` - Create document
- `PUT /api/documents/{id}` - Update document
- `DELETE /api/documents/{id}` - Delete document
- `POST /api/documents/upload` - Upload document
- `PUT /api/documents/{id}/approve` - Approve document
- `PUT /api/documents/{id}/reject` - Reject document
- `GET /api/documents/types/` - Get document types
- `POST /api/documents/types/` - Create document type
- `GET /api/documents/{id}/versions` - Get document versions

## Notification Management
- `GET /api/notifications/` - List notifications
- `GET /api/notifications/{id}` - Get notification by ID
- `POST /api/notifications/` - Create notification
- `PUT /api/notifications/{id}` - Update notification
- `DELETE /api/notifications/{id}` - Delete notification
- `PUT /api/notifications/{id}/read` - Mark notification as read
- `GET /api/notifications/announcements/` - List announcements
- `POST /api/notifications/announcements/` - Create announcement
- `PUT /api/notifications/announcements/{id}/read` - Mark announcement as read
- `GET /api/notifications/holidays/` - List holidays
- `POST /api/notifications/holidays/` - Create holiday
- `GET /api/notifications/tasks/` - List tasks
- `POST /api/notifications/tasks/` - Create task
- `PUT /api/notifications/tasks/{id}/complete` - Complete task

## Performance Management
- `GET /api/performance/` - List performance reviews
- `GET /api/performance/{id}` - Get performance review by ID
- `POST /api/performance/` - Create performance review
- `PUT /api/performance/{id}` - Update performance review
- `DELETE /api/performance/{id}` - Delete performance review
- `PUT /api/performance/{id}/submit` - Submit performance review
- `PUT /api/performance/{id}/approve` - Approve performance review
- `PUT /api/performance/{id}/complete` - Complete performance review
- `GET /api/performance/employee/{id}/history` - Get employee performance history
- `GET /api/performance/stats/overview` - Get performance statistics

## Recruitment Management
- `GET /api/recruitment/jobs/` - List job postings
- `GET /api/recruitment/jobs/{id}` - Get job posting by ID
- `POST /api/recruitment/jobs/` - Create job posting
- `PUT /api/recruitment/jobs/{id}` - Update job posting
- `DELETE /api/recruitment/jobs/{id}` - Delete job posting
- `PUT /api/recruitment/jobs/{id}/activate` - Activate job posting
- `PUT /api/recruitment/jobs/{id}/deactivate` - Deactivate job posting
- `GET /api/recruitment/candidates/` - List candidates
- `GET /api/recruitment/candidates/{id}` - Get candidate by ID
- `POST /api/recruitment/candidates/` - Create candidate
- `GET /api/recruitment/applications/` - List job applications
- `PUT /api/recruitment/applications/{id}/status` - Update application status
- `GET /api/recruitment/interviews/` - List interviews
- `POST /api/recruitment/interviews/` - Schedule interview
- `PUT /api/recruitment/interviews/{id}/complete` - Complete interview
- `GET /api/recruitment/stats/overview` - Get recruitment statistics

## Training Management
- `GET /api/training/programs/` - List training programs
- `GET /api/training/programs/{id}` - Get training program by ID
- `POST /api/training/programs/` - Create training program
- `PUT /api/training/programs/{id}` - Update training program
- `DELETE /api/training/programs/{id}` - Delete training program
- `GET /api/training/sessions/` - List training sessions
- `POST /api/training/sessions/` - Create training session
- `GET /api/training/enrollments/` - List training enrollments
- `POST /api/training/enrollments/` - Enroll in training
- `PUT /api/training/enrollments/{id}/progress` - Update training progress
- `PUT /api/training/enrollments/{id}/complete` - Complete training
- `GET /api/training/roadmaps/` - List training roadmaps
- `GET /api/training/roadmaps/{id}` - Get training roadmap by ID
- `POST /api/training/roadmaps/` - Create training roadmap
- `GET /api/training/my-trainings/` - Get my trainings
- `GET /api/training/stats/overview` - Get training statistics

## Health Insurance Management
- `GET /api/health-insurance/policies/` - List health insurance policies
- `GET /api/health-insurance/policies/{id}` - Get policy by ID
- `GET /api/health-insurance/my-policy/` - Get my policy
- `GET /api/health-insurance/dependents/` - List dependents
- `GET /api/health-insurance/my-dependents/` - Get my dependents
- `POST /api/health-insurance/dependents/` - Add dependent
- `PUT /api/health-insurance/dependents/{id}/deactivate` - Deactivate dependent
- `GET /api/health-insurance/claims/` - List insurance claims
- `GET /api/health-insurance/my-claims/` - Get my claims
- `POST /api/health-insurance/claims/` - Submit insurance claim
- `GET /api/health-insurance/claims/{id}` - Get claim by ID
- `PUT /api/health-insurance/claims/{id}/approve` - Approve claim
- `PUT /api/health-insurance/claims/{id}/reject` - Reject claim
- `GET /api/health-insurance/panel-hospitals/` - List panel hospitals
- `POST /api/health-insurance/panel-hospitals/` - Add panel hospital
- `GET /api/health-insurance/coverage/` - Get coverage details
- `GET /api/health-insurance/my-coverage/` - Get my coverage
- `GET /api/health-insurance/stats/overview` - Get insurance statistics

## Payroll Management
- `GET /api/payroll/payslips/` - List payslips
- `GET /api/payroll/payslips/{id}` - Get payslip by ID
- `GET /api/payroll/my-payslips/` - Get my payslips
- `POST /api/payroll/payslips/` - Create payslip
- `PUT /api/payroll/payslips/{id}/finalize` - Finalize payslip
- `DELETE /api/payroll/payslips/{id}` - Delete payslip
- `GET /api/payroll/salary-structures/` - List salary structures
- `GET /api/payroll/my-salary-structure/` - Get my salary structure
- `POST /api/payroll/salary-structures/` - Create salary structure
- `GET /api/payroll/bonuses/` - List bonuses
- `GET /api/payroll/my-bonuses/` - Get my bonuses
- `POST /api/payroll/bonuses/` - Create bonus
- `PUT /api/payroll/bonuses/{id}/approve` - Approve bonus
- `GET /api/payroll/stats/overview` - Get payroll statistics
- `GET /api/payroll/generate-payslips/{pay_period}` - Generate monthly payslips

## Employee Requests
- `GET /api/requests/` - List employee requests
- `GET /api/requests/{id}` - Get request by ID
- `GET /api/requests/my-requests/` - Get my requests
- `POST /api/requests/` - Create employee request
- `PUT /api/requests/{id}` - Update employee request
- `DELETE /api/requests/{id}` - Delete employee request
- `PUT /api/requests/{id}/approve` - Approve request
- `PUT /api/requests/{id}/reject` - Reject request
- `PUT /api/requests/{id}/in-progress` - Mark request as in progress
- `GET /api/requests/{id}/logs` - Get request logs
- `GET /api/requests/hr-documents/` - List HR documents
- `POST /api/requests/hr-documents/` - Upload HR document
- `GET /api/requests/stats/overview` - Get request statistics
- `GET /api/requests/stats/my-requests` - Get my request statistics

## Reports & Analytics
- `GET /api/reports/dashboard/admin` - Get admin dashboard statistics
- `GET /api/reports/dashboard/employee` - Get employee dashboard statistics
- `GET /api/reports/attendance/monthly` - Get monthly attendance report
- `GET /api/reports/leave/summary` - Get leave summary report
- `GET /api/reports/payroll/summary` - Get payroll summary report
- `GET /api/reports/performance/summary` - Get performance summary report
- `GET /api/reports/training/progress` - Get training progress report
- `GET /api/reports/assets/utilization` - Get asset utilization report
- `GET /api/reports/complaints/analysis` - Get complaints analysis report
- `GET /api/reports/export/attendance` - Export attendance data

## System Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/modules` - Get available modules
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Authentication
Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Role-Based Access Control
- **Admin**: Full system access
- **HR**: Employee management, leave approval, attendance management, performance reviews
- **Team Lead**: Team-specific access, approve team member leaves, view team data
- **Employee**: Personal data access only, submit requests, view own data

## Query Parameters
Many endpoints support filtering via query parameters:
- `skip`: Number of records to skip (pagination)
- `limit`: Maximum number of records to return
- `status`: Filter by status
- `department`: Filter by department
- `employee_id`: Filter by employee ID
- `year`: Filter by year
- `month`: Filter by month

## Response Format
All endpoints return JSON responses with consistent structure:
```json
{
  "data": [...],
  "message": "Success message",
  "status": 200
}
```

Error responses:
```json
{
  "detail": "Error message",
  "status": 400
}
```