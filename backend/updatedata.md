# Complete Explanation of `upload_data.py`

## 📋 **OVERVIEW**
This file handles Excel file uploads for financial data. It processes balance sheet/transaction data, stores it in two database tables (`rawData` and `final_structured`), uploads files to S3, and tracks progress.

---

## 🏗️ **FILE STRUCTURE**

### **1. IMPORTS & SETUP (Lines 1-27)**

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
```

**What it does:**
- Creates Flask routes for file uploads
- Handles JWT authentication
- Imports pandas for Excel processing
- Sets up S3 client (optional, for cloud storage)
- Creates a progress tracker dictionary with thread-safe locking

**Key Variables:**
- `UPLOAD_PROGRESS`: In-memory dictionary tracking upload progress by `operation_id`
- `progress_lock`: Thread lock to prevent race conditions when multiple uploads happen simultaneously
- `S3_CLIENT_AVAILABLE`: Boolean flag indicating if S3 upload is possible

---

## 🔧 **HELPER FUNCTIONS**

### **2. PROGRESS TRACKING FUNCTIONS (Lines 30-52)**

#### `init_progress(operation_id, meta=None)`
**Purpose:** Initialize progress tracking for a new upload operation

**What it does:**
- Creates a new entry in `UPLOAD_PROGRESS` dictionary
- Sets initial status: `'starting'`, progress: `0`, processed_rows: `0`
- Stores metadata (filename, entity info, etc.)
- Uses thread lock to prevent concurrent access issues

**When called:** At the start of every upload

---

#### `update_progress(operation_id, **kwargs)`
**Purpose:** Update progress information during upload

**What it does:**
- Updates any field in the progress dictionary (status, progress %, processed_rows, message, etc.)
- Only updates if operation_id exists (safety check)
- Thread-safe using lock

**Example updates:**
- `update_progress(id, status='processing', progress=50, processed_rows=100)`

---

#### `get_progress(operation_id)`
**Purpose:** Retrieve current progress for an upload

**What it does:**
- Returns the progress dictionary for a given operation_id
- Used by frontend to poll upload status
- Returns `None` if operation not found

---

### **3. DATA PARSING FUNCTIONS**

#### `parse_amount_and_type(cell_value)` (Lines 58-111)
**Purpose:** Extract amount and Dr/Cr type from Excel cell values

**Input Examples:**
- `"-123.45"` → Returns: `(123.45, 'Cr')`
- `"123.45"` → Returns: `(123.45, 'Dr')`
- `"5000 Dr"` → Returns: `(5000.0, 'Dr')`
- `"-5000 Cr"` → Returns: `(5000.0, 'Cr')`
- `"62,291.18"` → Returns: `(62291.18, 'Dr')`

**Logic Flow:**
1. **Check for None/Empty:** Returns `(None, None)` if cell is empty, None, or NaN
2. **Convert to String:** Converts cell value to string and strips whitespace
3. **Check Explicit Type:** Looks for "Dr", "Cr", "DR", "CR" text in the string
4. **Extract Number:** Uses regex `r'-?[\d,]+\.?\d*'` to find numeric value (handles commas, decimals, negative sign)
5. **Determine Type:**
   - If explicit Dr/Cr text found → Use that type, store absolute value
   - If no explicit text → Use sign: negative = Cr, positive = Dr, zero = Dr (default)
6. **Return:** `(amount, type)` tuple

**Edge Cases Handled:**
- Empty cells → `(None, None)`
- NaN values → `(None, None)`
- Numbers with commas → Removes commas
- Negative numbers → Extracts sign, determines type
- Text with numbers → Extracts only numeric part

---

#### `calculate_amt_tb_lc(amount, amount_type)` (Lines 114-127)
**Purpose:** Calculate transaction amount for database storage

**Business Rule:**
- **Dr (Debit)** → Positive value: `+amount`
- **Cr (Credit)** → Negative value: `-amount`

**Examples:**
- `calculate_amt_tb_lc(5000, 'Dr')` → Returns: `5000`
- `calculate_amt_tb_lc(5000, 'Cr')` → Returns: `-5000`

**Why:** This standardizes how debits/credits are stored in the database (Dr = positive, Cr = negative)

---

#### `parse_plain_number(cell_value)` (Lines 130-147)
**Purpose:** Extract just the numeric value (no Dr/Cr parsing)

**Use Case:** For raw data storage where we just need the number

**Logic:**
1. Check for None/empty → Return None
2. Extract number using regex (handles commas, decimals, signs)
3. Convert to float
4. Return float or None

**Example:**
- `"5,000.50"` → Returns: `5000.50`
- `"-123.45"` → Returns: `-123.45`
- `"abc"` → Returns: `None`

---

### **4. DATABASE OPERATIONS**

#### `insert_raw_data(...)` (Lines 150-216)
**Purpose:** Insert raw Excel row into `rawData` table (unprocessed data)

**Parameters:**
- `entity_id`: Which company/entity
- `month_name`: Month name (e.g., "January")
- `year`: Financial year
- `particular`: Account name/description
- `opening_value`: Opening balance
- `transaction_value`: Transaction amount
- `closing_value`: Closing balance
- `new_company`: 1 if starting month balance sheet, 0 otherwise

**What it does:**
1. Builds SQL INSERT query with backticks (handles case-sensitive column names)
2. Parses numeric values using `parse_plain_number()` (converts to decimal or NULL)
3. Inserts into `rawData` table
4. Returns insert result (record ID) or None on error

**Table Structure:**
- `RecordID` (auto-increment primary key)
- `EntityID`, `Month`, `Year`, `Particular`
- `OpeningBalance`, `Transactions`, `ClosingBalance` (decimal fields)
- `newCompany` (0 or 1)
- `created_at` (timestamp)

**Error Handling:**
- Catches database errors, logs them, returns None
- Continues processing even if one row fails

---

#### `delete_existing_data_for_entity_month_year(...)` (Lines 219-341)
**Purpose:** Delete existing data before inserting new data (prevents duplicates)

**Why:** When re-uploading the same entity/month/year, we delete old data first

**What it does:**
1. **Delete from `rawData` table:**
   - Finds records matching: EntityID + Month + Year (case-insensitive)
   - Counts records before deletion
   - Executes DELETE query
   - **VERIFIES deletion** (counts again to ensure all deleted)
   - If records remain → Tries deletion again (safety mechanism)
   - Logs success/failure

2. **Delete from `final_structured` table:**
   - Finds records matching: entityCode + selectedMonth + Year (case-insensitive)
   - Counts before deletion
   - Executes DELETE
   - Verifies deletion completed

3. **Returns summary:**
   ```python
   {
       'success': True/False,
       'raw_data_deleted': count,
       'structured_data_deleted': count,
       'total_deleted': count
   }
   ```

**Safety Features:**
- Case-insensitive matching (handles "January" vs "january")
- Verification after deletion
- Retry mechanism if first deletion fails
- Continues even if deletion fails (logs warning)

---

#### `get_entity_details(ent_id)` (Lines 344-354)
**Purpose:** Fetch entity information from `entity_master` table

**Returns:**
```python
{
    'ent_name': 'Company Name',
    'ent_code': 'COMP001',
    'lcl_curr': 'USD'
}
```

**Use Case:** Get entity name, code, and local currency for data processing

---

#### `get_month_details(month_id)` (Lines 357-367)
**Purpose:** Fetch month information from `month_master` table

**Returns:**
```python
{
    'month_short': 'Jan',
    'month_name': 'January',
    'year': 2024,
    'qtr': 1,
    'half': 1
}
```

**Use Case:** Get quarter and half-year information for financial reporting

---

#### `get_coa_mapping(particular_name)` (Lines 370-421)
**Purpose:** Look up Chart of Accounts (COA) mapping for a particular name

**What is COA Mapping?**
- Maps account names (e.g., "Cash") to standardized categories
- Categories: mainCategory, category1, category2, category3, category4, category5
- Used for financial reporting and classification

**Logic:**
1. Normalizes input (strips whitespace, case-insensitive)
2. Queries `code_master` table where `RawParticulars` matches
3. Maps database columns to expected keys:
   - `mainCategory` → `std_code`
   - `category1` → `brd_cls`
   - `category2` → `brd_cls_2`
   - `category3` → `ctg_code`
   - `category4` → `cafl_fnfl`
   - `category5` → `cat_5`
4. Returns mapping dictionary or None if not found

**Why None is OK:**
- New accounts may not have COA mapping yet
- System continues processing without COA (fills with NULL)

---

#### `insert_structured_data(data, inserted_keys_set=None)` (Lines 424-585)
**Purpose:** Insert processed data into `final_structured` table (main data table)

**This is the MOST IMPORTANT function** - it handles duplicate prevention and data insertion.

**Parameters:**
- `data`: Dictionary with all record fields
- `inserted_keys_set`: Set tracking records inserted in current batch (prevents duplicates within same upload)

**Duplicate Prevention (3 Layers):**

**Layer 1: In-Memory Check (Lines 456-463)**
- Creates unique key: `(particular, entity_code, selectedMonth, year, month, amount)`
- Checks if key exists in `inserted_keys_set`
- If duplicate → Skip insertion, return None
- If new → Add to set, continue

**Layer 2: Database Check (Lines 465-504)**
- Queries database for existing record with same:
  - Particular (case-insensitive)
  - entityCode (case-insensitive)
  - selectedMonth (case-insensitive)
  - Year
  - Month (case-insensitive)
  - transactionAmount (with 0.01 tolerance for floating point)
- If found → Skip insertion, return None
- If not found → Continue

**Layer 3: Final Check + INSERT IGNORE (Lines 506-585)**
- Double-checks database one more time (in case another process inserted between checks)
- Uses `INSERT IGNORE` SQL statement (database-level safety net)
- If duplicate key error → Returns None
- If successful → Returns record ID

**Data Inserted:**
- `Particular`, `entityName`, `entityCode`, `localCurrencyCode`
- `transactionAmount` (calculated with Dr/Cr sign)
- `Month` (e.g., "Opening", "January")
- `selectedMonth` (month selected during upload)
- `mainCategory`, `category1-5` (COA mapping)
- `Year`, `Qtr`, `Half`

**Why So Many Checks?**
- Prevents duplicate transactions
- Handles concurrent uploads
- Ensures data integrity

---

### **5. UPLOAD HISTORY FUNCTIONS**

#### `create_upload_history_table()` (Lines 588-610)
**Purpose:** Create `upload_history` table if it doesn't exist

**Table Structure:**
- `slno`: Auto-increment primary key
- `ent_code`, `year`, `month`: Upload metadata
- `doc_link`: S3 URL of uploaded file
- `uploaded_at`: Timestamp

**Use Case:** Track which files were uploaded, when, and where they're stored

---

#### `save_upload_history(...)` (Lines 613-649)
**Purpose:** Save upload record to history table

**What it does:**
1. Ensures table exists (calls `create_upload_history_table()`)
2. Inserts record with entity code, year, month, S3 URL, timestamp
3. Returns operation_id (record ID) or None on error

---

## 🌐 **API ENDPOINTS**

### **6. GET ENDPOINTS (Helper Routes)**

#### `/entities` (Lines 652-682)
**Purpose:** Get list of all entities from database

**Request:** `GET /upload/entities`

**Response:**
```json
{
    "success": true,
    "data": {
        "entities": [
            {
                "ent_id": 1,
                "ent_name": "Company A",
                "ent_code": "COMP001",
                "lcl_curr": "USD",
                "city": "New York",
                "country": "USA"
            },
            ...
        ]
    }
}
```

**Use Case:** Frontend dropdown to select entity during upload

---

#### `/months` (Lines 685-715)
**Purpose:** Get list of all months from database

**Request:** `GET /upload/months`

**Response:**
```json
{
    "success": true,
    "data": {
        "months": [
            {
                "mnt_id": 1,
                "month_short": "Jan",
                "month_name": "January",
                "year": 2024,
                "qtr": 1,
                "half": 1
            },
            ...
        ]
    }
}
```

**Use Case:** Frontend dropdown to select month during upload

---

#### `/financial-years` (Lines 718-765)
**Purpose:** Get distinct financial years

**Request:** `GET /upload/financial-years`

**Response:**
```json
{
    "success": true,
    "data": {
        "years": [2024, 2023, 2022, ...]
    }
}
```

**Use Case:** Frontend dropdown to select financial year

---

#### `/progress/<operation_id>` (Lines 768-785)
**Purpose:** Get upload progress status

**Request:** `GET /upload/progress/abc123`

**Response:**
```json
{
    "success": true,
    "data": {
        "status": "processing",
        "progress": 50,
        "processed_rows": 100,
        "total_rows": 200,
        "message": "Processing rows",
        "meta": {
            "filename": "data.xlsx",
            "entity": "Company A"
        }
    }
}
```

**Use Case:** Frontend polls this endpoint to show progress bar

---

## 🚀 **MAIN UPLOAD ENDPOINT**

### **7. `/upload` - POST Endpoint (Lines 788-1542)**

**This is the HEART of the file** - handles the entire upload process.

---

### **PHASE 1: REQUEST VALIDATION (Lines 799-840)**

#### **Step 1.1: Log Request Details**
- Logs request method, headers, content-type
- Logs authorization header (for debugging)
- Logs form keys and file keys

#### **Step 1.2: JWT Authentication**
```python
verify_jwt_in_request()
current_user_id = get_jwt_identity()
```

**What happens:**
- Verifies JWT token from Authorization header
- Extracts user ID from token
- If invalid/expired → Returns 401 error with detailed message
- If valid → Continues with user_id

**Error Response:**
```json
{
    "success": false,
    "message": "Authentication failed. Please login again.",
    "error": "Token expired",
    "error_type": "JWTDecodeError"
}
```

---

### **PHASE 2: INITIALIZATION (Lines 841-846)**

#### **Step 2.1: Generate Operation ID**
- Gets `operation_id` from form data OR generates new UUID
- This ID tracks the entire upload operation

#### **Step 2.2: Initialize Progress Tracker**
- Calls `init_progress(operation_id)`
- Sets status to 'validating'
- Frontend can now poll `/progress/<operation_id>` to see status

---

### **PHASE 3: FILE VALIDATION (Lines 848-869)**

#### **Step 3.1: Check File Exists**
```python
if 'file' not in request.files:
    return error 400
```

**Conditions:**
- If no 'file' key in request → Error 400
- If filename is empty → Error 400
- If file exists → Continue

**Error Response:**
```json
{
    "success": false,
    "message": "No file provided. Please select a file to upload."
}
```

---

### **PHASE 4: FORM DATA VALIDATION (Lines 873-940)**

#### **Step 4.1: Extract Form Data**
- `ent_id`: Entity ID (required)
- `month_name`: Month name (optional, can use month_id instead)
- `month_id`: Month ID (optional, can use month_name instead)
- `financial_year`: Financial year (required)
- `newCompany`: 0 or 1 (default: 0)

#### **Step 4.2: Validate Required Fields**
**Conditions:**
- If `ent_id` missing → Error 400
- If `financial_year` missing → Error 400
- If both `month_name` AND `month_id` missing → Error 400
- If all present → Continue

#### **Step 4.3: Get Entity Details**
- Calls `get_entity_details(ent_id)`
- If entity not found → Error 400
- If found → Store entity name, code, currency

#### **Step 4.4: Get Month Details**
**Two Paths:**

**Path A: month_name provided**
- Uses month_name directly
- Sets year from financial_year
- qtr and half set to None (can be calculated later)

**Path B: month_id provided**
- Calls `get_month_details(month_id)`
- If not found → Error 400
- If found → Uses month_name, year, qtr, half from database

---

### **PHASE 5: DELETE EXISTING DATA (Lines 957-972)**

#### **Step 5.1: Delete Old Records**
- Calls `delete_existing_data_for_entity_month_year(...)`
- Deletes from `rawData` table
- Deletes from `final_structured` table
- Verifies deletion completed

**Why:** Prevents duplicates when re-uploading same data

**If deletion fails:**
- Logs warning
- Continues anyway (better to have duplicate than miss data)

---

### **PHASE 6: FILE STORAGE (Lines 974-1033)**

#### **Step 6.1: Save Temporary File**
- Creates temp file in system temp directory
- Filename: `upload_YYYYMMDD_HHMMSS_originalname.xlsx`
- Saves uploaded file to temp location
- If save fails → Error 500

#### **Step 6.2: Upload to S3 (Optional)**
**Conditions:**
- If S3_CLIENT_AVAILABLE == True:
  1. Create S3 client
  2. Upload file to S3 with user_id and module='financial_data'
  3. Get S3 URL from response
  4. Save upload history with S3 URL
  5. If upload fails → Log warning, continue (doesn't stop processing)

- If S3_CLIENT_AVAILABLE == False:
  - Skip S3 upload, log warning
  - Continue processing

**Why Optional:** System works even without S3 (for local development)

---

### **PHASE 7: EXCEL PROCESSING (Lines 1035-1068)**

#### **Step 7.1: Read Excel File**
```python
df = pd.read_excel(file, engine='openpyxl', dtype=str, keep_default_na=False)
```

**Settings:**
- `dtype=str`: Preserves text format (important for Dr/Cr parsing)
- `keep_default_na=False`: Doesn't convert empty cells to NaN
- Reads entire Excel into pandas DataFrame

**Expected Columns:**
- `Particular`: Account name
- `Opening`: Opening balance
- `Transaction`: Transaction amount
- `Closing`: Closing balance
- `Type` or `Dr/Cr` or `DrCr`: Optional type column

#### **Step 7.2: Update Progress**
- Sets status to 'processing'
- Sets total_rows = number of rows in Excel
- Sets processed_rows = 0

---

### **PHASE 8: ROW-BY-ROW PROCESSING (Lines 1070-1338)**

**This is the CORE processing loop** - processes each Excel row.

#### **Step 8.1: Initialize Counters**
```python
records_inserted = 0
records_skipped = 0
records_without_coa = 0
records_duplicate_skipped = 0
raw_data_inserted = 0
final_structured_inserted = 0
errors = []
inserted_keys_set = set()  # Track duplicates in current batch
```

#### **Step 8.2: Loop Through Each Row**

**For each row in Excel:**

##### **A. Validate Particular (Lines 1088-1095)**
- Gets 'Particular' column value
- If None or empty → Skip row, increment `records_skipped`
- If valid → Strip whitespace, continue

##### **B. Insert Raw Data (Lines 1097-1137)**
**Conditions:**
- Check if rawData record already exists (duplicate check)
- If exists → Skip insertion
- If not exists:
  - If `newCompany == 1`: Save opening balance
  - If `newCompany == 0`: Don't save opening balance (set to None)
  - Call `insert_raw_data()` with all values
  - If successful → Increment `raw_data_inserted`

**Why Check Duplicates:** Even though we deleted old data, this prevents duplicates within the same upload

##### **C. Get COA Mapping (Lines 1139-1151)**
- Calls `get_coa_mapping(particular)`
- If found → Use mapping
- If not found → Set all categories to None, increment `records_without_coa`

**Why None is OK:** New accounts may not have COA mapping yet

##### **D. Parse Amounts and Types (Lines 1153-1236)**

**This is COMPLEX - handles multiple scenarios:**

**D.1: Parse Opening Column**
- Calls `parse_amount_and_type(opening_value)`
- Returns: `(opening_amount, opening_type)` or `(None, None)`

**D.2: Parse Transaction Column**
- Calls `parse_amount_and_type(transaction_value)`
- Returns: `(transaction_amount, transaction_type)` or `(None, None)`

**D.3: Parse Closing Column**
- Calls `parse_amount_and_type(closing_value)`
- Returns: `(closing_amount, closing_type)` or `(None, None)`

**D.4: Check for Type Column**
- Looks for 'Type', 'Dr/Cr', or 'DrCr' column
- If found:
  - Extracts Dr or Cr from value
  - If Opening has amount but no type → Apply type from Type column
  - If Transaction has amount but no type → Apply type from Type column

**D.5: Fallback Logic (If types still missing)**
- If Opening missing type but Closing has type → Use Closing's type
- If Transaction missing type but Closing has type → Use Closing's type

**D.6: Final Fallback (If still no type)**
- If Opening has number but no type → Default to 'Dr'
- If Transaction has number but no type → Default to 'Dr'

**Why So Many Fallbacks:** Excel files come in different formats, this handles all variations

##### **E. Create Base Data Structure (Lines 1245-1261)**
```python
base_data = {
    'particular': particular,
    'ent_name': entity_details['ent_name'],
    'ent_code': entity_details['ent_code'],
    'local_currency_code': entity_details['lcl_curr'],
    'year': month_details['year'],
    'qtr': month_details.get('qtr'),
    'half': month_details.get('half'),
    'selectedMonth': month_details['month_name'],
    'std_code': coa_mapping.get('std_code'),
    'brd_cls': coa_mapping.get('brd_cls'),
    ...
}
```

##### **F. Process Opening Balance (Lines 1266-1290)**
**Conditions:**
- If `opening_amount` is not None AND `opening_type` is not None:
  - If `newCompany == 1`:
    1. Copy base_data
    2. Calculate `amt_tb_lc` using `calculate_amt_tb_lc(opening_amount, opening_type)`
    3. Set `month = 'Opening'`
    4. Call `insert_structured_data(opening_data, inserted_keys_set)`
    5. If inserted (not duplicate) → Increment counters
  - If `newCompany == 0`:
    - Skip opening balance (not a starting month balance sheet)

**Why newCompany Check:** Opening balances only saved for starting month balance sheets

##### **G. Process Transaction (Lines 1292-1313)**
**Conditions:**
- If `transaction_amount` is not None AND `transaction_type` is not None:
  1. Copy base_data
  2. Calculate `amt_tb_lc` using `calculate_amt_tb_lc(transaction_amount, transaction_type)`
  3. Set `month = month_details['month_name']` (e.g., "January")
  4. Call `insert_structured_data(transaction_data, inserted_keys_set)`
  5. If inserted (not duplicate) → Increment counters
  6. If duplicate → Increment `records_duplicate_skipped`

##### **H. Handle Empty Rows (Lines 1315-1319)**
- If neither Opening nor Transaction has data → Skip row
- Increment `records_skipped`

##### **I. Update Progress (Lines 1321-1331)**
- Calculate progress percentage: `(processed_rows / total_rows) * 100`
- Update progress tracker
- Frontend can poll to show progress bar

##### **J. Error Handling (Lines 1333-1338)**
- If any error occurs processing a row:
  - Log error message
  - Add to errors list
  - Continue processing next row (don't stop entire upload)

---

### **PHASE 9: POST-PROCESSING (Lines 1340-1378)**

#### **Step 9.1: Calculate Forex Rates**
**Conditions:**
- If `records_inserted > 0`:
  1. Query database for newly inserted rows with `mainCategory` but no `Avg_Fx_Rt`
  2. Import forex calculation functions
  3. Build forex cache
  4. Calculate and save forex rates for each row
  5. Log success count

**Why:** Some financial data needs currency conversion rates calculated

**If fails:** Logs warning, doesn't stop upload

---

### **PHASE 10: RESPONSE PREPARATION (Lines 1380-1516)**

#### **Step 10.1: Build Response Message**
- Creates success message with counts
- Includes: records inserted, skipped, duplicates, without COA

#### **Step 10.2: Build Response Data**
```json
{
    "success": true,
    "message": "File processed successfully...",
    "data": {
        "filename": "data.xlsx",
        "operation_id": "abc123",
        "records_inserted": 100,
        "records_skipped": 5,
        "records_duplicate_skipped": 2,
        "records_without_coa": 10,
        "total_rows": 105,
        "entity": "Company A",
        "month": "January",
        "year": 2024,
        "s3_url": "https://s3.../file.xlsx",
        "uploaded_to_s3": true
    }
}
```

#### **Step 10.3: Verify Database Counts**
- Counts actual records in `rawData` table
- Counts actual records in `final_structured` table
- Compares with insertion counts
- If mismatch → Logs warning, checks for duplicates
- Prints detailed summary

#### **Step 10.4: Update Final Progress**
- Sets status to 'completed'
- Sets progress to 100%
- Includes final metadata

#### **Step 10.5: Return Response**
- Returns JSON response with 200 status code

---

### **PHASE 11: ERROR HANDLING (Lines 1520-1532)**

**If any exception occurs during upload:**
- Logs error with traceback
- Updates progress to 'failed'
- Returns error response:
```json
{
    "success": false,
    "message": "An error occurred while uploading file: ...",
    "operation_id": "abc123"
}
```

---

### **PHASE 12: CLEANUP (Lines 1534-1541)**

**Finally block (always executes):**
- Deletes temporary file from disk
- Logs cleanup success/failure

**Why:** Prevents disk space issues from accumulating temp files

---

## 📊 **DATA FLOW SUMMARY**

```
1. User uploads Excel file
   ↓
2. Authenticate user (JWT)
   ↓
3. Validate file and form data
   ↓
4. Delete existing data for entity/month/year
   ↓
5. Save file temporarily
   ↓
6. Upload to S3 (optional)
   ↓
7. Read Excel into DataFrame
   ↓
8. For each row:
   a. Insert into rawData table
   b. Parse amounts and Dr/Cr types
   c. Get COA mapping
   d. Insert Opening balance (if newCompany=1)
   e. Insert Transaction
   ↓
9. Calculate forex rates (if needed)
   ↓
10. Return success response with counts
```

---

## 🔑 **KEY CONCEPTS**

### **1. Duplicate Prevention**
- **3 layers:** In-memory set, database check, INSERT IGNORE
- **Why:** Prevents duplicate transactions from multiple uploads or errors

### **2. Dr/Cr Handling**
- **Dr (Debit)** = Positive amount in database
- **Cr (Credit)** = Negative amount in database
- **Parsing:** Handles multiple formats (sign, text, separate column)

### **3. Two-Table Storage**
- **rawData:** Unprocessed Excel data (for audit trail)
- **final_structured:** Processed data with COA mapping (for reporting)

### **4. Progress Tracking**
- In-memory dictionary (per operation_id)
- Frontend polls `/progress/<operation_id>` endpoint
- Updates in real-time during processing

### **5. Error Resilience**
- Continues processing even if one row fails
- Logs all errors but doesn't stop upload
- Returns summary of successes and failures

---

## 🎯 **CONDITIONS SUMMARY**

### **When Opening Balance is Saved:**
- ✅ `newCompany == 1` AND `opening_amount` is not None AND `opening_type` is not None

### **When Transaction is Saved:**
- ✅ `transaction_amount` is not None AND `transaction_type` is not None

### **When Row is Skipped:**
- ❌ `particular` is empty/None
- ❌ Both Opening and Transaction are empty
- ❌ Duplicate record found

### **When COA Mapping is Missing:**
- ⚠️ Account not in `code_master` table
- ⚠️ System continues with NULL categories (expected for new accounts)

### **When S3 Upload is Skipped:**
- ⚠️ S3 client not available
- ⚠️ S3 upload fails (but processing continues)

---

## 📝 **END OF EXPLANATION**

This file is a comprehensive financial data upload system that handles:
- ✅ Authentication
- ✅ File validation
- ✅ Excel parsing
- ✅ Data transformation
- ✅ Duplicate prevention
- ✅ Error handling
- ✅ Progress tracking
- ✅ Cloud storage
- ✅ Database operations

Every condition and edge case is handled to ensure robust, reliable data processing.
