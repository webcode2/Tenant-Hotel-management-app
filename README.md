# Hotel Management System - FastAPI

A production-ready, multi-tenant Hotel Management System built with FastAPI, featuring role-based access control (RBAC), JWT authentication, and async PostgreSQL database operations.

## Features

- **Multi-Tenant Architecture**: Each hotel operates as a separate tenant with isolated data access
- **Role-Based Access Control (RBAC)**: Flexible permission system with global and hotel-scoped roles
- **JWT Authentication**: Secure token-based authentication
- **Async Database Operations**: Using SQLAlchemy with async PostgreSQL support
- **Database Migrations**: Alembic for version-controlled schema changes
- **Comprehensive Testing**: pytest with async support and test fixtures
- **Type Safety**: Full type hints throughout the codebase
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Project Structure

```
app/
├── main.py                 # Application entry point
├── core/                   # Core configuration and dependencies
│   ├── config.py          # Settings and configuration
│   ├── database.py        # Database setup and session management
│   ├── security.py        # Password hashing and JWT utilities
│   └── dependencies.py    # FastAPI dependencies for auth
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── role.py
│   ├── hotel.py
│   └── user_role_assignment.py
├── schemas/                # Pydantic schemas
│   ├── user.py
│   ├── role.py
│   ├── hotel.py
│   ├── token.py
│   └── user_role_assignment.py
├── routers/                # API route handlers
│   ├── auth.py
│   ├── users.py
│   ├── roles.py
│   └── hotels.py
└── services/               # Business logic
    ├── auth_service.py
    ├── user_service.py
    ├── role_service.py
    └── hotel_service.py
alembic/                    # Database migrations
tests/                      # Test suite
```

## Data Models

### User
- `id`: Integer (primary key)
- `email`: String (unique)
- `password_hash`: String
- `is_active`: Boolean
- `created_at`: DateTime

### Role
- `id`: Integer (primary key)
- `name`: String (unique)
- `description`: Text

Default roles: Admin, Manager, Receptionist, Staff, Guest

### Hotel
- `id`: Integer (primary key)
- `name`: String
- `address`: Text
- `created_at`: DateTime

### UserRoleAssignment
- `id`: Integer (primary key)
- `user_id`: Integer (foreign key)
- `role_id`: Integer (foreign key)
- `hotel_id`: Integer (nullable foreign key)

When `hotel_id` is NULL, the role applies globally (system-wide).
When `hotel_id` is set, the role is scoped to that specific hotel.

## Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Copy `.env.example` to `.env` and update:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hotel_management
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Users
- `GET /users/me` - Get current user info
- `GET /users/` - Get all users (Admin only)
- `GET /users/{user_id}` - Get user by ID (Admin only)
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user (Admin only)

### Roles
- `POST /roles/` - Create new role (Admin only)
- `GET /roles/` - Get all roles (Admin only)
- `GET /roles/{role_id}` - Get role by ID (Admin only)
- `PUT /roles/{role_id}` - Update role (Admin only)
- `DELETE /roles/{role_id}` - Delete role (Admin only)
- `POST /roles/assignments` - Assign role to user (Admin only)
- `GET /roles/users/{user_id}/assignments` - Get user's role assignments (Admin only)

### Hotels
- `POST /hotels/` - Create new hotel (Admin only)
- `GET /hotels/` - Get all hotels (Admin/Manager)
- `GET /hotels/{hotel_id}` - Get hotel by ID (Admin/Manager)
- `PUT /hotels/{hotel_id}` - Update hotel (Admin only)
- `DELETE /hotels/{hotel_id}` - Delete hotel (Admin only)

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

## Authorization Examples

### Global Admin Role
```json
{
  "user_id": 1,
  "role_id": 1,
  "hotel_id": null
}
```
This user has Admin access across the entire system.

### Hotel-Scoped Manager Role
```json
{
  "user_id": 2,
  "role_id": 2,
  "hotel_id": 5
}
```
This user has Manager access only for hotel ID 5.

### Multiple Role Assignments
A user can have multiple role assignments:
- Global Admin role (hotel_id = null)
- Manager role for Hotel A (hotel_id = 1)
- Staff role for Hotel B (hotel_id = 2)

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Security Features

- **Password Hashing**: Using bcrypt via passlib
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access Control**: Fine-grained permissions
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **CORS Configuration**: Configurable cross-origin resource sharing

## Contributing

1. Follow the existing code structure and patterns
2. Write tests for new features
3. Use type hints throughout
4. Add docstrings to functions and classes
5. Run tests before committing

## License

MIT License
