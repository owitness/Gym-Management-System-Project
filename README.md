# Gym Management System

A comprehensive web-based gym management system built with Flask that handles memberships, class scheduling, equipment management, and more.

## Features

- 🔐 Secure Authentication System
- 👥 Multi-role Support (Members, Trainers, Admins)
- 📅 Class Scheduling and Booking
- 💳 Membership Management
- 💰 Payment Processing
- 📊 Attendance Tracking
- 🏋️ Equipment Management
- 📱 Responsive Dashboard
- 📈 Analytics and Reporting

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQL
- **Authentication**: JWT (JSON Web Tokens)
- **Security**: CSRF Protection, CORS, Rate Limiting
- **Frontend**: HTML, CSS, JavaScript
- **Templates**: Flask Templates

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQL Database
- Virtual Environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd Gym-Management-System-Project
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python init_db.py
```

5. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
```

## Project Structure

```
Gym-Management-System-Project/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── db_connection.py      # Database connection management
├── middleware.py         # Authentication and security middleware
├── requirements.txt      # Project dependencies
├── schema.sql           # Database schema
├── init_db.py           # Database initialization
├── routes/              # API routes
│   ├── auth.py         # Authentication routes
│   ├── users.py        # User management
│   ├── memberships.py  # Membership management
│   ├── classes.py      # Class management
│   ├── trainer.py      # Trainer management
│   ├── admin.py        # Admin operations
│   ├── payments.py     # Payment processing
│   ├── equipment.py    # Equipment management
│   └── attendance.py   # Attendance tracking
├── templates/           # HTML templates
├── static/             # Static assets
├── utils/              # Utility functions
├── tests/              # Test files
└── logs/               # Application logs
```

## Running the Application

1. Start the development server:
```bash
python app.py
```

2. Access the application:
- Frontend: http://localhost:5001
- API: http://localhost:5001/api

## API Documentation

### Authentication Endpoints
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - User login
- POST `/api/auth/refresh-token` - Refresh JWT token

### User Management
- GET `/api/users/profile` - Get user profile
- PUT `/api/users/profile` - Update user profile

### Membership Management
- GET `/api/memberships` - List available memberships
- POST `/api/memberships/subscribe` - Subscribe to membership

### Class Management
- GET `/api/classes` - List available classes
- POST `/api/classes/book` - Book a class
- GET `/api/classes/schedule` - Get class schedule

## Security Features

- JWT-based authentication
- CSRF protection
- CORS configuration
- Rate limiting
- Secure session management
- Content Security Policy
- Secure cookie settings

## Error Handling

The system includes comprehensive error handling for:
- 401 (Unauthorized)
- 403 (Forbidden)
- 404 (Not Found)
- 429 (Too Many Requests)
- 500 (Internal Server Error)

## Logging

- Rotating file handler
- Log file size limit: 10KB
- Backup count: 10 files
- Log level: WARNING
- Detailed logging format

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Flask Documentation
- JWT Documentation
- All contributors who have helped shape this project 