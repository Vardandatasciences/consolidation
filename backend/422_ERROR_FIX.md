# 422 Error Fix - Upload Endpoint

## Problem
Getting 422 (Unprocessable Entity) error when uploading files to `/api/upload/upload` endpoint.

## Root Causes
The 422 error can occur due to:

1. **JWT Token Issues**
   - Missing or invalid JWT token
   - Expired token
   - Malformed token format
   - Token not in Authorization header

2. **Request Format Issues**
   - Missing required form fields
   - File not properly attached
   - Content-Type header conflicts

3. **Flask-JWT-Extended Validation**
   - Token validation fails before endpoint code runs
   - Returns 422 automatically

## Solutions Implemented

### 1. Enhanced Error Handling
- Added 422 error handler in `app.py`
- Added 401 error handler for authentication issues
- Better error messages with debugging info

### 2. Improved Logging
- Added detailed request logging
- Logs Authorization header (first 50 chars)
- Logs all form keys and file keys
- Logs JWT validation errors

### 3. OPTIONS Request Handling
- Explicitly handles OPTIONS preflight requests
- Returns 200 OK for OPTIONS

### 4. Better JWT Error Handling
- Wraps JWT validation in try-catch
- Returns 401 with detailed error message
- Logs error type for debugging

## Debugging Steps

### Check Backend Logs
When you see a 422 error, check the backend console for:
```
🔍 Request method: POST
🔍 Content-Type: multipart/form-data
🔍 Authorization header: Bearer eyJ...
🔍 Has files: True/False
🔍 Form keys: ['ent_id', 'month_id', 'financial_year']
🔍 Files keys: ['file']
```

### Common Issues and Fixes

#### Issue 1: Missing Authorization Header
**Symptoms:**
- `Authorization header: NOT SET`
- 422 or 401 error

**Fix:**
- Ensure user is logged in
- Check if token exists in localStorage
- Verify token is being sent in request

#### Issue 2: Invalid Token
**Symptoms:**
- `❌ JWT Error: ...`
- 401 error

**Fix:**
- User needs to login again
- Token may have expired
- Check token format

#### Issue 3: Missing Form Fields
**Symptoms:**
- `Missing required fields: Entity, Month, Financial Year`
- 400 error

**Fix:**
- Ensure all dropdowns are selected
- Check frontend form validation

#### Issue 4: File Not Attached
**Symptoms:**
- `No 'file' key in request.files`
- 400 error

**Fix:**
- Ensure file is selected
- Check file input is working
- Verify FormData is created correctly

## Testing

### Test 1: Check Authentication
```bash
# Should return 401 if not authenticated
curl -X POST http://localhost:5000/api/upload/upload
```

### Test 2: Check with Valid Token
```bash
# Replace YOUR_TOKEN with actual JWT token
curl -X POST http://localhost:5000/api/upload/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.xlsx" \
  -F "ent_id=1" \
  -F "month_id=1" \
  -F "financial_year=2024"
```

### Test 3: Check Frontend
1. Open browser DevTools → Network tab
2. Try uploading a file
3. Check the request:
   - Headers → Authorization should have "Bearer ..."
   - Payload → Should have file and form fields
   - Response → Check error message

## Expected Behavior

### Successful Request
```
🔍 Request method: POST
🔍 Content-Type: multipart/form-data; boundary=...
🔍 Authorization header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
✅ User authenticated: 1
📄 File received: balance_sheet.xlsx, Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
📋 Form data - ent_id: 1, month_id: 1, financial_year: 2024
```

### Failed Request (Missing Token)
```
🔍 Request method: POST
🔍 Authorization header: NOT SET
❌ 422 Error: Missing Authorization Header
```

### Failed Request (Invalid Token)
```
🔍 Request method: POST
🔍 Authorization header: Bearer invalid_token...
❌ JWT Error: Not enough segments
❌ 401 Error: Not enough segments
```

## Frontend Checklist

1. ✅ User is logged in
2. ✅ Token exists in localStorage
3. ✅ Token is sent in Authorization header
4. ✅ File is selected
5. ✅ Entity is selected
6. ✅ Month is selected
7. ✅ Financial Year is selected
8. ✅ FormData is created correctly
9. ✅ Content-Type is NOT manually set (browser handles it)

## Backend Checklist

1. ✅ JWT_SECRET_KEY is configured
2. ✅ CORS is properly configured
3. ✅ Error handlers are in place
4. ✅ Logging is enabled
5. ✅ Database connection is working

## Next Steps

If you still see 422 errors:

1. **Check Backend Logs**
   - Look for the debug messages starting with 🔍
   - Identify which step is failing

2. **Check Frontend Console**
   - Look for network errors
   - Check if token is being sent

3. **Verify Token**
   - Try logging in again
   - Check if token is valid

4. **Test with Postman/curl**
   - Isolate if issue is frontend or backend
   - Test with known good token

## Code Changes Made

### app.py
- Added 422 error handler
- Added 401 error handler
- Better error logging

### upload_data.py
- Added OPTIONS handler
- Enhanced request logging
- Better JWT error handling
- More detailed error messages

## Contact

If issues persist, check:
1. Backend console logs
2. Browser DevTools Network tab
3. Browser DevTools Console
4. Token expiration time






