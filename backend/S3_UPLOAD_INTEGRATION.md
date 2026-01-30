# S3 Upload Integration with Upload History

## Overview
The Excel upload functionality has been enhanced to automatically upload files to S3 and save upload history to the database.

## Features Implemented

### 1. S3 Upload Integration
- Automatically uploads Excel files to S3 after validation
- Uses the `RenderS3Client` from `s3_fucntions.py`
- Handles upload errors gracefully (continues processing even if S3 upload fails)

### 2. Upload History Tracking
- Creates `upload_history` table automatically if it doesn't exist
- Saves upload details: entity code, year, month, S3 document link, and upload timestamp
- Tracks all successful uploads for audit and reference

## Database Table: upload_history

### Schema
```sql
CREATE TABLE IF NOT EXISTS upload_history (
    slno BIGINT AUTO_INCREMENT PRIMARY KEY,
    ent_code VARCHAR(50) NOT NULL,
    year INT NOT NULL,
    month VARCHAR(20) NOT NULL,
    doc_link VARCHAR(500) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ent_code (ent_code),
    INDEX idx_year (year),
    INDEX idx_month (month),
    INDEX idx_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
```

### Columns
- **slno**: Auto-increment primary key
- **ent_code**: Entity code from entity_master
- **year**: Financial year
- **month**: Month name (e.g., "April", "May")
- **doc_link**: S3 URL where the document is stored
- **uploaded_at**: Timestamp of upload

## Upload Flow

1. **File Validation**
   - Validates file exists and is not empty
   - Validates entity, month, and financial year are provided

2. **Entity & Month Details**
   - Fetches entity details (name, code, local currency)
   - Fetches month details (name, year, quarter, half)

3. **Temporary File Storage**
   - Saves uploaded file to temporary directory
   - Uses timestamped filename to avoid conflicts

4. **S3 Upload** (if S3 client available)
   - Creates S3 client using `create_direct_mysql_client()`
   - Uploads file to S3 with module name 'financial_data'
   - Retrieves S3 URL from upload response

5. **Upload History Save**
   - Saves upload record to `upload_history` table
   - Includes entity code, year, month, and S3 document link

6. **Excel Processing**
   - Reads Excel file and processes row by row
   - Inserts data into `final_structured` table
   - Handles Opening and Transaction scenarios

7. **Cleanup**
   - Removes temporary file after processing
   - Returns success response with S3 URL

## API Response

### Success Response
```json
{
  "success": true,
  "message": "File processed successfully. 10 records inserted, 2 rows skipped.",
  "data": {
    "filename": "balance_sheet.xlsx",
    "records_inserted": 10,
    "records_skipped": 2,
    "total_rows": 12,
    "entity": "Risk Analytics & Data Solutions INC",
    "month": "April",
    "year": 2024,
    "s3_url": "https://s3.amazonaws.com/bucket/file.xlsx",
    "uploaded_to_s3": true
  },
  "warnings": []
}
```

### New Fields in Response
- **s3_url**: S3 URL where the document is stored (null if S3 upload failed)
- **uploaded_to_s3**: Boolean indicating if file was successfully uploaded to S3

## Error Handling

### S3 Upload Errors
- If S3 upload fails, processing continues
- Warning is logged but doesn't stop Excel processing
- Response includes `uploaded_to_s3: false` if upload failed

### Upload History Errors
- If history save fails, warning is logged
- Processing continues normally
- S3 URL is still returned in response

### Temporary File Cleanup
- Temporary files are always cleaned up in `finally` block
- Errors during cleanup are logged but don't affect response

## Dependencies

### Required
- `routes.s3_fucntions` - S3 client module
- `tempfile` - Python standard library for temporary files
- `os` - File operations

### Optional
- If S3 client is not available, upload continues without S3 storage
- Upload history is only saved if S3 upload succeeds

## Usage Example

```python
# Upload endpoint automatically:
# 1. Validates file and form data
# 2. Uploads to S3
# 3. Saves to upload_history
# 4. Processes Excel data
# 5. Returns response with S3 URL

POST /api/upload/upload
Headers: Authorization: Bearer <token>
Form Data:
  - file: Excel file
  - ent_id: Entity ID
  - month_id: Month ID
  - financial_year: Financial year
```

## Query Upload History

```sql
-- Get all uploads for an entity
SELECT * FROM upload_history 
WHERE ent_code = 'ENTITY_CODE' 
ORDER BY uploaded_at DESC;

-- Get uploads for a specific year
SELECT * FROM upload_history 
WHERE year = 2024 
ORDER BY uploaded_at DESC;

-- Get uploads for a specific month
SELECT * FROM upload_history 
WHERE ent_code = 'ENTITY_CODE' 
  AND year = 2024 
  AND month = 'April'
ORDER BY uploaded_at DESC;
```

## Configuration

### S3 Client Configuration
The S3 client uses configuration from:
1. Django settings (if available)
2. Environment variables (fallback)
3. Default values (last resort)

### Module Name
All financial data uploads use module name: `'financial_data'`

This can be changed in the upload function if needed.

## Notes

- Temporary files are stored in system temp directory
- Files are automatically cleaned up after processing
- S3 upload is non-blocking (errors don't stop processing)
- Upload history is only saved if S3 upload succeeds
- All uploads are tracked with timestamps for audit purposes






