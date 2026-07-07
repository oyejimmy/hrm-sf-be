# Employee Attendance System Implementation

## Overview
This document describes the implementation of the Employee Attendance System with proper database relationships between `attendance` and `break_records` tables.

## Database Schema

### Attendance Table
- **Primary Key**: `id`
- **Foreign Key**: `employee_id` → `users.id`
- **Unique Constraint**: `(employee_id, date)` - Prevents duplicate attendance records
- **Cascade**: Break records are deleted when attendance record is deleted

### Break Records Table
- **Primary Key**: `id`
- **Foreign Key**: `attendance_id` → `attendance.id`
- **Relationship**: Many break records can belong to one attendance record

## API Endpoints

### Check-in: `POST /api/attendance/check-in`
- Creates or updates attendance record for today
- Sets `check_in` time and status to "present"
- Returns attendance ID for reference

### Check-out: `POST /api/attendance/check-out`
- Updates attendance record with `check_out` time
- Calculates and stores `hours_worked`
- Returns attendance ID for reference

### Start Break: `POST /api/attendance/break/start`
- Creates new break record linked to today's attendance
- Prevents multiple active breaks
- Returns break ID for reference

### End Break: `POST /api/attendance/break/end`
- Updates active break record with `end_time`
- Calculates and stores `duration_minutes`
- Returns break ID and duration

## Data Flow

1. **Check-in** → Creates/updates attendance record
2. **Start Break** → Creates break record linked to attendance
3. **End Break** → Updates break record with end time and duration
4. **Check-out** → Updates attendance record with checkout time and calculates hours

## Frontend Integration

### TanStack Query Hooks
- `useCheckIn()` - Handles check-in mutation
- `useCheckOut()` - Handles check-out mutation  
- `useStartBreak()` - Handles break start mutation
- `useEndBreak()` - Handles break end mutation

### Data Synchronization
- All mutations automatically invalidate attendance queries
- Real-time updates via React Query's cache invalidation
- Proper error handling with user feedback

## Key Features

### Database Integrity
- Foreign key constraints ensure data consistency
- Unique constraints prevent duplicate records
- Cascade deletes maintain referential integrity

### Error Handling
- Proper HTTP status codes
- Descriptive error messages
- Graceful fallbacks for edge cases

### Real-time Updates
- Automatic query invalidation after mutations
- Live clock updates in UI
- Instant feedback on user actions

## Testing

Run the test script to verify functionality:
```bash
python test_attendance_flow.py
```

## Migration

Run the migration script to ensure proper database schema:
```bash
python migrate_attendance.py
```

## Production Considerations

1. **Database Indexes**: Added on foreign keys for performance
2. **Constraints**: Unique constraints prevent data duplication
3. **Validation**: Input validation on both frontend and backend
4. **Error Handling**: Comprehensive error handling throughout
5. **Security**: Role-based access control for admin endpoints