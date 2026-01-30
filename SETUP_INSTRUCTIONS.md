# 🚀 Setup Instructions - Financial Analyzer Application

Complete setup guide for connecting the React frontend with Flask backend and MySQL database.

## 📋 Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- MySQL Server (v8.0 or higher)
- Git

## 🗄️ Step 1: Database Setup

### 1.1 Create Database

Open MySQL command line or MySQL Workbench and run:

```sql
CREATE DATABASE balance_sheet;
USE balance_sheet;
```

### 1.2 Create Users Table

Run the schema file from the backend folder:

```bash
# Navigate to backend folder
cd backend

# Run schema (Windows Command Prompt)
mysql -u root -p balance_sheet < schema.sql

# OR using MySQL Workbench: Open schema.sql and execute it
```

### 1.3 Verify Tables Created

```sql
USE balance_sheet;
SHOW TABLES;
DESCRIBE users;
```

You should see the following tables:
- `users`
- `entity_master`
- `coa_master` (from your existing database)
- `forex_master`
- `month_master`

## 🐍 Step 2: Backend (Flask) Setup

### 2.1 Navigate to Backend Folder

```bash
cd backend
```

### 2.2 Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 2.3 Configure Database Connection

Edit `backend/.env` file and update with your MySQL credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD_HERE
DB_NAME=balance_sheet
DB_PORT=3306
```

### 2.4 Create Test Users

Run the script to create test users in the database:

```bash
python create_test_user.py
```

This will create three test users:
- **Admin**: username: `admin`, password: `admin123`
- **Demo**: username: `demo`, password: `demo123`
- **Test**: username: `test`, password: `test123`

### 2.5 Start Flask Server

```bash
python app.py
```

You should see:
```
==================================================
🚀 Starting Flask Backend Server
==================================================
✅ Database connection pool created successfully
✅ Database connection test successful
✅ Server running on http://localhost:5000
✅ Database: balance_sheet
==================================================
```

## ⚛️ Step 3: Frontend (React) Setup

### 3.1 Open New Terminal

Keep the Flask server running and open a new terminal window.

### 3.2 Navigate to Frontend Folder

```bash
cd entity-insights-hub
```

### 3.3 Install Dependencies

```bash
npm install
```

### 3.4 Start Development Server

```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

## ✅ Step 4: Test the Application

### 4.1 Test Backend API

Open your browser or Postman and test:

**Health Check:**
```
GET http://localhost:5000/api/health
```

**Test Endpoint:**
```
GET http://localhost:5000/api/test
```

### 4.2 Test Login

1. Open browser and go to `http://localhost:5173/login`
2. Enter credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Click "Login"
4. You should be redirected to the dashboard with a success message

## 🔧 Troubleshooting

### Issue: Database Connection Failed

**Solution:**
1. Check if MySQL is running
2. Verify credentials in `backend/.env`
3. Make sure the `balance_sheet` database exists
4. Check if port 3306 is available

### Issue: CORS Error

**Solution:**
- Make sure Flask server is running on port 5000
- Check if `VITE_API_URL` in frontend matches the backend URL
- Verify CORS is enabled in `backend/app.py`

### Issue: Module Not Found

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
npm install
```

### Issue: Port Already in Use

**Backend (Port 5000):**
- Change port in `backend/.env`:
```env
PORT=5001
```

**Frontend (Port 5173):**
- Vite will automatically try the next available port

## 📁 Project Structure

```
srini/
├── backend/                    # Flask Backend
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration
│   ├── database.py            # Database handler
│   ├── schema.sql             # Database schema
│   ├── create_test_user.py    # User creation script
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables
│
└── entity-insights-hub/       # React Frontend
    ├── src/
    │   ├── components/        # UI Components
    │   ├── pages/             # Page Components
    │   ├── lib/
    │   │   └── api.ts         # API Service
    │   ├── App.tsx            # Main App
    │   └── main.tsx           # Entry Point
    └── package.json           # Node dependencies
```

## 🔐 Test Credentials

| Username | Password | Role   |
|----------|----------|--------|
| admin    | admin123 | admin  |
| demo     | demo123  | user   |
| test     | test123  | user   |

## 📝 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/verify` | Verify token |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/test` | Test endpoint |

## 🎯 Next Steps

1. ✅ Login functionality - **COMPLETED**
2. 📊 Connect Dashboard to backend
3. 🏢 Implement Entity Management APIs
4. 📤 Implement File Upload functionality
5. 📈 Add Reports and Analytics
6. ⚙️ Settings and User Management

## 📞 Support

If you encounter any issues, check:
1. Both servers are running (Flask on 5000, React on 5173)
2. MySQL is running
3. Database credentials are correct
4. All dependencies are installed

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Backend shows "Server running on http://localhost:5000"
- ✅ Frontend loads at http://localhost:5173
- ✅ Login redirects to dashboard
- ✅ Toast notifications appear on login
- ✅ No console errors in browser

---

**Created for Vardaan Data Sciences**
*Multi-Entity Financial Platform*

