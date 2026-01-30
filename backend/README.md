# Flask Backend API - Financial Analyzer

Backend API for the Multi-Entity Financial Platform built with Flask and MySQL.

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Database Setup

Make sure MySQL is running and create the database:

```sql
CREATE DATABASE balance_sheet;
```

Then run the schema file:

```bash
mysql -u root -p balance_sheet < schema.sql
```

### 3. Configure Environment

Edit the `.env` file with your database credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=balance_sheet
DB_PORT=3306
```

### 4. Create Test Users

Run the script to create test users:

```bash
python create_test_user.py
```

This will create:
- **Admin User**: username: `admin`, password: `admin123`
- **Demo User**: username: `demo`, password: `demo123`
- **Test User**: username: `test`, password: `test123`

### 5. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📡 API Endpoints

### Authentication

#### POST `/api/auth/login`
Login with username/email and password

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@vardaan.com",
      "full_name": "System Administrator",
      "role": "admin"
    }
  }
}
```

#### POST `/api/auth/register`
Register a new user

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "full_name": "New User"
}
```

#### GET `/api/auth/verify`
Verify JWT token (requires Authorization header)

**Headers:**
```
Authorization: Bearer <token>
```

### Utility

#### GET `/api/health`
Health check endpoint

#### GET `/api/test`
Test endpoint to verify API is running

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. After logging in, include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## 📁 Project Structure

```
backend/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── database.py         # Database connection handler
├── schema.sql          # Database schema
├── create_test_user.py # Script to create test users
├── requirements.txt    # Python dependencies
├── .env                # Environment variables
└── README.md           # This file
```

## 🛠️ Technologies Used

- **Flask**: Web framework
- **MySQL**: Database
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-JWT-Extended**: JWT authentication
- **mysql-connector-python**: MySQL database connector
- **werkzeug**: Password hashing

## 📝 Notes

- Make sure MySQL server is running before starting the Flask server
- Update the `.env` file with your actual database credentials
- The default port is 5000, you can change it in the `.env` file
- CORS is configured to allow requests from `http://localhost:5173` (Vite default)

