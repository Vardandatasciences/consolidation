# 🔌 Backend Connection Guide

This guide ensures your frontend is properly connected to the Flask backend.

## ✅ Connection Checklist

### 1. Backend Server Status
- [ ] Flask backend is running on `http://localhost:5000`
- [ ] Database connection is successful
- [ ] CORS is enabled for frontend origins

### 2. Frontend Configuration
- [ ] API base URL is set correctly (default: `http://localhost:5000/api`)
- [ ] Environment variable `VITE_API_URL` is set if needed
- [ ] Frontend is running on `http://localhost:5173` (or port 3000)

### 3. Database Setup
- [ ] MySQL database `balance_sheet` exists
- [ ] `users` table is created
- [ ] Test users are created (admin, demo, test)

## 🔧 Configuration Files

### Frontend API Configuration

**Location:** `entity-insights-hub/src/lib/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
```

### Environment Variables (Optional)

Create `entity-insights-hub/.env` if you need custom API URL:

```env
VITE_API_URL=http://localhost:5000/api
```

### Backend Configuration

**Location:** `backend/config.py`

```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
```

## 🧪 Testing Connection

### 1. Test Backend Directly

Open browser and visit:
- **Health Check:** `http://localhost:5000/api/health`
- **Test Endpoint:** `http://localhost:5000/api/test`

You should see JSON responses.

### 2. Test from Frontend

The login page automatically checks connection when loaded. Look for:
- ✅ **Green indicator:** "Backend connected" - Connection successful
- ❌ **Red indicator:** "Cannot connect to backend" - Connection failed

### 3. Check Browser Console

Open browser DevTools (F12) and check Console tab:
- `[API Config] Base URL: http://localhost:5000/api`
- `[API] POST http://localhost:5000/api/auth/login`
- `[API Success]` or `[API Error]` messages

## 🐛 Troubleshooting

### Error: "Cannot connect to server"

**Possible causes:**
1. Backend server is not running
   - **Solution:** Start Flask server: `python backend/app.py`
   
2. Wrong port number
   - **Solution:** Check backend is running on port 5000
   - **Solution:** Verify `VITE_API_URL` in frontend matches backend port

3. CORS issues
   - **Solution:** Ensure frontend URL is in `CORS_ORIGINS` in `backend/config.py`

### Error: "NetworkError when attempting to fetch resource"

**Possible causes:**
1. Backend server crashed
   - **Solution:** Check backend console for errors
   - **Solution:** Restart Flask server

2. Firewall blocking connection
   - **Solution:** Allow port 5000 in firewall settings

### Error: "Invalid credentials"

**This is normal** if:
- Wrong username/password entered
- User doesn't exist in database

**Solution:**
- Use test credentials: `admin` / `admin123`
- Create users: Run `python backend/create_test_user.py`

### Login Works but Redirect Fails

**Possible causes:**
1. Token not stored in localStorage
   - **Solution:** Check browser DevTools > Application > Local Storage
   - Should see `token` and `user` keys

2. Protected route not working
   - **Solution:** Verify `ProtectedRoute` component is working
   - Check browser console for navigation errors

## 📡 API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | Register user |
| GET | `/api/auth/verify` | Verify token |

### Test Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/test` | Test API connection |
| GET | `/api/health` | Health check with DB status |

## 🔍 Debugging Steps

1. **Check Backend is Running**
   ```bash
   # Terminal 1: Start Backend
   cd backend
   python app.py
   ```
   Should see:
   ```
   ✅ Server running on http://localhost:5000
   ✅ Database: balance_sheet
   ```

2. **Check Frontend is Running**
   ```bash
   # Terminal 2: Start Frontend
   cd entity-insights-hub
   npm run dev
   ```
   Should see:
   ```
   VITE ready in XXX ms
   ➜  Local:   http://localhost:5173/
   ```

3. **Test API in Browser**
   - Open: `http://localhost:5000/api/test`
   - Should see: `{"success": true, "message": "Backend API is working!"}`

4. **Check Browser Console**
   - Open DevTools (F12)
   - Go to Console tab
   - Look for API logs: `[API Config]`, `[API]`, `[Login]`

5. **Check Network Tab**
   - Open DevTools (F12)
   - Go to Network tab
   - Try logging in
   - Check if `POST /api/auth/login` request is sent
   - Check response status (200 = success, 401 = invalid credentials, etc.)

## ✅ Success Indicators

You'll know everything is connected when:

1. ✅ Backend console shows: "Server running on http://localhost:5000"
2. ✅ Login page shows: "✅ Backend connected" (green indicator)
3. ✅ Browser console shows: `[API Config] Base URL: http://localhost:5000/api`
4. ✅ Login with `admin` / `admin123` redirects to dashboard
5. ✅ LocalStorage contains `token` and `user` keys
6. ✅ No CORS errors in browser console
7. ✅ No network errors in browser DevTools

## 🆘 Still Having Issues?

1. **Verify all services are running:**
   - MySQL server
   - Flask backend (`python app.py`)
   - React frontend (`npm run dev`)

2. **Check ports are not in use:**
   - Backend: Port 5000
   - Frontend: Port 5173 (or 3000)

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Clear localStorage: DevTools > Application > Local Storage > Clear

4. **Check firewall/antivirus:**
   - Ensure port 5000 is not blocked

5. **Review logs:**
   - Backend console for database/API errors
   - Browser console for frontend/network errors

---

**Need Help?** Check the error messages in:
- Backend console (Flask server terminal)
- Browser console (F12 > Console)
- Network tab (F12 > Network)

