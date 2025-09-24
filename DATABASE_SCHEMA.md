# HRM System Database Schema

## Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Users      │    │   Departments   │    │   Employees     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ email (UNIQUE)  │    │ name (UNIQUE)   │    │ user_id (FK)    │
│ hashed_password │    │ description     │    │ employee_id     │
│ first_name      │    │ head_id         │    │ department_id   │
│ last_name       │    │ created_at      │    │ position        │
│ phone           │    │ updated_at      │    │ employment_status│
│ role            │    └─────────────────┘    │ hire_date       │
│ status          │                           │ salary          │
│ is_profile_complete                        │ manager_id (FK) │
│ profile_picture │                           │ work_location   │
│ created_at      │                           │ gender          │
│ updated_at      │                           │ date_of_birth   │
│ last_login      │                           │ marital_status  │
└─────────────────┘                           │ address         │
         │                                    │ emergency_contact_name
         │                                    │ emergency_contact_phone
         │                                    │ created_at      │
         │                                    │ updated_at      │
         │                                    └─────────────────┘
         │                                             │
         │                                             │
         │    ┌─────────────────┐                     │
         │    │     Leaves      │                     │
         │    ├─────────────────┤                     │
         │    │ id (PK)         │                     │
         └────┤ employee_id (FK)│                     │
              │ leave_type      │                     │
              │ start_date      │                     │
              │ end_date        │                     │
              │ days_requested  │                     │
              │ reason          │                     │
              │ status          │                     │
              │ approved_by (FK)│                     │
              │ approved_at     │                     │
              │ rejection_reason│                     │
              │ created_at      │                     │
              │ updated_at      │                     │
              └─────────────────┘                     │
                                                      │
         ┌─────────────────┐                         │
         │   Attendance    │                         │
         ├─────────────────┤                         │
         │ id (PK)         │                         │
         │ employee_id (FK)├─────────────────────────┘
         │ date            │
         │ check_in        │
         │ check_out       │
         │ status          │
         │ hours_worked    │
         │ notes           │
         │ created_at      │
         │ updated_at      │
         └─────────────────┘
                  
         ┌─────────────────┐
         │ Performance     │
         │   Reviews       │
         ├─────────────────┤
         │ id (PK)         │
         │ employee_id (FK)├─────────────────────────┐
         │ reviewer_id (FK)├─────────────────────────┘
         │ review_period_start
         │ review_period_end
         │ overall_rating  │
         │ goals_achievement
         │ strengths       │
         │ areas_for_improvement
         │ goals_next_period
         │ comments        │
         │ status          │
         │ created_at      │
         │ updated_at      │
         └─────────────────┘
```

## Table Definitions

### Users Table
Primary table for user authentication and basic profile information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique user identifier |
| email | STRING | UNIQUE, NOT NULL | User email address |
| hashed_password | STRING | NOT NULL | Bcrypt hashed password |
| first_name | STRING | NULLABLE | User's first name |
| last_name | STRING | NULLABLE | User's last name |
| phone | STRING | NULLABLE | Phone number |
| role | STRING | DEFAULT 'employee' | User role (admin, hr, team_lead, employee) |
| status | STRING | DEFAULT 'active' | Account status (active, inactive, suspended) |
| is_profile_complete | BOOLEAN | DEFAULT FALSE | Profile completion status |
| profile_picture | STRING | NULLABLE | Profile picture URL |
| created_at | DATETIME | AUTO | Account creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |
| last_login | DATETIME | NULLABLE | Last login timestamp |

### Employees Table
Detailed employee information and employment details.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique employee identifier |
| user_id | INTEGER | FOREIGN KEY, UNIQUE | Reference to users table |
| employee_id | STRING | UNIQUE, NOT NULL | Employee ID (e.g., EMP0001) |
| department_id | INTEGER | FOREIGN KEY | Reference to departments table |
| position | STRING | NULLABLE | Job position/title |
| employment_status | STRING | DEFAULT 'full_time' | Employment type |
| hire_date | DATE | NULLABLE | Date of joining |
| salary | FLOAT | NULLABLE | Employee salary |
| manager_id | INTEGER | FOREIGN KEY | Reference to manager (employees.id) |
| work_location | STRING | DEFAULT 'office' | Work location type |
| gender | STRING | NULLABLE | Gender |
| date_of_birth | DATE | NULLABLE | Date of birth |
| marital_status | STRING | NULLABLE | Marital status |
| address | TEXT | NULLABLE | Home address |
| emergency_contact_name | STRING | NULLABLE | Emergency contact name |
| emergency_contact_phone | STRING | NULLABLE | Emergency contact phone |
| created_at | DATETIME | AUTO | Record creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |

### Departments Table
Department/team organization structure.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique department identifier |
| name | STRING | UNIQUE, NOT NULL | Department name |
| description | TEXT | NULLABLE | Department description |
| head_id | INTEGER | NULLABLE | Department head user ID |
| created_at | DATETIME | AUTO | Record creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |

### Leaves Table
Leave request and approval management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique leave request identifier |
| employee_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to users table |
| leave_type | STRING | NOT NULL | Type of leave |
| start_date | DATE | NOT NULL | Leave start date |
| end_date | DATE | NOT NULL | Leave end date |
| days_requested | FLOAT | NOT NULL | Number of days requested |
| reason | TEXT | NULLABLE | Reason for leave |
| status | STRING | DEFAULT 'pending' | Leave status |
| approved_by | INTEGER | FOREIGN KEY | Approver user ID |
| approved_at | DATETIME | NULLABLE | Approval timestamp |
| rejection_reason | TEXT | NULLABLE | Reason for rejection |
| created_at | DATETIME | AUTO | Request creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |

### Attendance Table
Daily attendance tracking and time management.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique attendance record identifier |
| employee_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to users table |
| date | DATE | NOT NULL | Attendance date |
| check_in | TIME | NULLABLE | Check-in time |
| check_out | TIME | NULLABLE | Check-out time |
| status | STRING | NOT NULL | Attendance status |
| hours_worked | STRING | NULLABLE | Total hours worked |
| notes | TEXT | NULLABLE | Additional notes |
| created_at | DATETIME | AUTO | Record creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |

### Performance Reviews Table
Employee performance evaluation and review system.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique review identifier |
| employee_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to users table |
| reviewer_id | INTEGER | FOREIGN KEY, NOT NULL | Reviewer user ID |
| review_period_start | DATE | NOT NULL | Review period start date |
| review_period_end | DATE | NOT NULL | Review period end date |
| overall_rating | STRING | NOT NULL | Overall performance rating |
| goals_achievement | FLOAT | NULLABLE | Goals achievement percentage |
| strengths | TEXT | NULLABLE | Employee strengths |
| areas_for_improvement | TEXT | NULLABLE | Areas needing improvement |
| goals_next_period | TEXT | NULLABLE | Goals for next period |
| comments | TEXT | NULLABLE | Additional comments |
| status | STRING | DEFAULT 'draft' | Review status |
| created_at | DATETIME | AUTO | Review creation timestamp |
| updated_at | DATETIME | AUTO | Last update timestamp |

## Relationships

### One-to-One Relationships
- **User ↔ Employee**: Each user has one employee profile
- **Department ↔ Department Head**: Each department has one head

### One-to-Many Relationships
- **Department → Employees**: One department has many employees
- **Employee → Subordinates**: One manager has many subordinates
- **User → Leave Requests**: One user can have many leave requests
- **User → Attendance Records**: One user can have many attendance records
- **User → Performance Reviews**: One user can have many performance reviews

### Many-to-One Relationships
- **Employees → Manager**: Many employees report to one manager
- **Leave Requests → Approver**: Many leaves approved by one user
- **Performance Reviews → Reviewer**: Many reviews by one reviewer

## Indexes

### Primary Indexes
- All primary keys are automatically indexed

### Secondary Indexes
- `users.email` - Unique index for fast email lookups
- `employees.employee_id` - Unique index for employee ID lookups
- `employees.user_id` - Index for user-employee relationship
- `employees.department_id` - Index for department queries
- `employees.manager_id` - Index for manager-subordinate queries
- `leaves.employee_id` - Index for employee leave queries
- `attendance.employee_id` - Index for employee attendance queries
- `attendance.date` - Index for date-based queries
- `performance_reviews.employee_id` - Index for employee review queries

## Constraints

### Foreign Key Constraints
- `employees.user_id` → `users.id`
- `employees.department_id` → `departments.id`
- `employees.manager_id` → `employees.id`
- `leaves.employee_id` → `users.id`
- `leaves.approved_by` → `users.id`
- `attendance.employee_id` → `users.id`
- `performance_reviews.employee_id` → `users.id`
- `performance_reviews.reviewer_id` → `users.id`

### Unique Constraints
- `users.email` - Unique email addresses
- `employees.employee_id` - Unique employee IDs
- `employees.user_id` - One employee profile per user
- `departments.name` - Unique department names

### Check Constraints
- `users.role` IN ('admin', 'hr', 'team_lead', 'employee')
- `users.status` IN ('active', 'inactive', 'suspended')
- `employees.employment_status` IN ('full_time', 'part_time', 'contract', 'intern')
- `employees.work_location` IN ('office', 'remote', 'hybrid', 'field')
- `leaves.status` IN ('pending', 'approved', 'rejected', 'cancelled')
- `attendance.status` IN ('present', 'absent', 'late', 'half_day', 'on_leave')
- `performance_reviews.overall_rating` IN ('excellent', 'good', 'satisfactory', 'needs_improvement', 'unsatisfactory')
- `performance_reviews.status` IN ('draft', 'submitted', 'approved')

## Data Integrity Rules

1. **User Creation**: Every user must have a unique email
2. **Employee Profile**: Employee profile is created after user profile completion
3. **Department Assignment**: Employees must be assigned to valid departments
4. **Manager Hierarchy**: Managers must be existing employees
5. **Leave Dates**: End date must be after or equal to start date
6. **Attendance**: One attendance record per employee per date
7. **Performance Reviews**: Review period end must be after start date