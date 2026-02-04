# Step-by-Step Implementation Plan
## Requirements 2 & 3 Implementation

---

## 📋 Overview

This document outlines the step-by-step implementation plan for:
- **Requirement 2**: Master Data Section for Financial Year
- **Requirement 3**: Strict Currency Calculations Based on Financial Year

---

## 🎯 REQUIREMENT 2: Master Data Section for Financial Year

### Goal
Create a master data management system where:
- Administrators can add/edit/delete financial year ranges
- System validates that data uploads are only allowed within configured financial year ranges
- Example: If FY 2024-25 (April 2024 to March 2025) is configured, data for April 2026 should be rejected

---

### Step 1: Database Migration - Create `financial_year_master` Table

**File to Create:** `backend/migrations/005_financial_year_master.sql`

**What it does:**
- Creates `financial_year_master` table to store valid financial year ranges
- Fields:
  - `id` (Primary Key)
  - `financial_year` (VARCHAR(10)) - Format: "2024-25"
  - `start_date` (DATE) - FY start date (e.g., 2024-04-01)
  - `end_date` (DATE) - FY end date (e.g., 2025-03-31)
  - `is_active` (BOOLEAN) - Whether this FY is active for data uploads
  - `description` (VARCHAR(255)) - Optional description
  - `created_at`, `updated_at`, `created_by`

**SQL Structure:**
```sql
CREATE TABLE financial_year_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    financial_year VARCHAR(10) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_financial_year (financial_year),
    INDEX idx_is_active (is_active),
    INDEX idx_dates (start_date, end_date)
);
```

**Why:** This table will be the source of truth for valid financial year ranges.

---

### Step 2: Backend API - Create Financial Year Master Routes

**File to Create:** `backend/routes/financial_year_master.py`

**Endpoints to Create:**

1. **GET `/financial-year-master`** - List all financial years
   - Returns all financial years with their date ranges
   - Can filter by `is_active` status

2. **GET `/financial-year-master/<id>`** - Get single financial year
   - Returns details of a specific financial year

3. **POST `/financial-year-master`** - Create new financial year
   - Body: `{ financial_year: "2024-25", start_date: "2024-04-01", end_date: "2025-03-31", is_active: true, description: "FY 2024-25" }`
   - Validates date ranges (end_date must be after start_date)
   - Validates no overlapping date ranges

4. **PUT `/financial-year-master/<id>`** - Update financial year
   - Updates existing financial year
   - Validates date ranges

5. **DELETE `/financial-year-master/<id>`** - Delete financial year
   - Soft delete (set is_active = 0) or hard delete
   - Check if any data exists for this FY before deletion

6. **GET `/financial-year-master/validate`** - Validate date against active FYs
   - Query params: `date=2024-04-15`
   - Returns: `{ valid: true, financial_year: "2024-25" }` or `{ valid: false, message: "Date falls outside configured financial years" }`

**Why:** These endpoints will allow frontend to manage financial years and backend to validate uploads.

---

### Step 3: Update Upload Validation - Check Against Master Data

**File to Modify:** `backend/routes/upload_data.py`

**Location:** In `upload_file()` function, after getting `month_name` and `financial_year`

**What to Add:**
```python
# After line ~1030 (after getting month_details)

# Validate that the month/year falls within an active financial year range
from routes.financial_year_master import validate_date_against_fy_master

# Convert month_name and year to a date
# Example: "April" + 2024 → "2024-04-01"
upload_date = convert_month_year_to_date(month_details['month_name'], month_details['year'])

# Validate against master data
validation_result = validate_date_against_fy_master(upload_date)
if not validation_result['valid']:
    return jsonify({
        'success': False,
        'message': f"Data upload not allowed: {validation_result['message']}",
        'error': 'FINANCIAL_YEAR_VALIDATION_FAILED'
    }), 400
```

**Helper Function to Create:**
```python
def convert_month_year_to_date(month_name, year):
    """Convert month name and year to first day of that month"""
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    month_num = month_map.get(month_name.lower(), 1)
    return datetime(year, month_num, 1).date()
```

**Why:** This ensures data can only be uploaded for months within configured financial year ranges.

---

### Step 4: Frontend API Client - Add Financial Year Master API

**File to Modify:** `entity-insights-hub/src/lib/api.ts`

**What to Add:**
```typescript
/**
 * Financial Year Master API calls
 */
export const financialYearMasterApi = {
  list: async (isActive?: boolean) => {
    const params = new URLSearchParams();
    if (isActive !== undefined) params.append('is_active', isActive.toString());
    const queryString = params.toString();
    const endpoint = queryString ? `/financial-year-master?${queryString}` : '/financial-year-master';
    return apiCall<{ financial_years: Array<{...}> }>(endpoint, { method: 'GET' });
  },
  
  get: async (id: number) => {
    return apiCall(`/financial-year-master/${id}`, { method: 'GET' });
  },
  
  create: async (payload: {
    financial_year: string;
    start_date: string;
    end_date: string;
    is_active?: boolean;
    description?: string;
  }) => {
    return apiCall('/financial-year-master', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  
  update: async (id: number, payload: {...}) => {
    return apiCall(`/financial-year-master/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  
  delete: async (id: number) => {
    return apiCall(`/financial-year-master/${id}`, { method: 'DELETE' });
  },
  
  validate: async (date: string) => {
    return apiCall<{ valid: boolean; financial_year?: string; message?: string }>(
      `/financial-year-master/validate?date=${date}`,
      { method: 'GET' }
    );
  },
};
```

**Why:** Frontend needs API methods to interact with the master data.

---

### Step 5: Frontend UI - Add Master Data Section in Settings

**File to Modify:** `entity-insights-hub/src/pages/Settings.tsx`

**What to Add:**
- New tab: "Master Data" (after "Data Processing" tab)
- Table showing all financial years with:
  - Financial Year (e.g., "2024-25")
  - Start Date
  - End Date
  - Status (Active/Inactive)
  - Actions (Edit, Delete)
- "Add Financial Year" button
- Dialog/Modal for Add/Edit form with:
  - Financial Year (text input, format: "2024-25")
  - Start Date (date picker)
  - End Date (date picker)
  - Active toggle
  - Description (optional)

**UI Structure:**
```tsx
<TabsTrigger value="master-data">Master Data</TabsTrigger>
<TabsContent value="master-data">
  <Card>
    <CardHeader>
      <CardTitle>Financial Year Master Data</CardTitle>
      <CardDescription>Manage valid financial year ranges</CardDescription>
    </CardHeader>
    <CardContent>
      {/* Table with financial years */}
      {/* Add/Edit Dialog */}
    </CardContent>
  </Card>
</TabsContent>
```

**Why:** Administrators need a UI to manage financial year master data.

---

### Step 6: Register Backend Routes

**File to Modify:** `backend/app.py`

**What to Add:**
```python
from routes.financial_year_master import financial_year_master_bp

# Register blueprint
app.register_blueprint(financial_year_master_bp, url_prefix='')
```

**Why:** Flask needs to know about the new routes.

---

## 🎯 REQUIREMENT 3: Strict Currency Calculations Based on Financial Year

### Goal
Ensure currency calculations use rates from the **exact same financial year** as the data:
- Remove adjacent year fallback logic
- Only use rates from the same FY as the data
- Show clear errors if rates are missing for a specific FY

---

### Step 7: Update Forex Rate Lookup - Remove Adjacent Year Fallback

**File to Modify:** `backend/routes/structure_data.py`

**Location:** `_apply_forex_rates()` function (lines 185-204)

**Current Code (to remove):**
```python
# If not found, try adjacent years
if not fx:
    try_next_fy = financial_year + 1
    cache_key = f"{entity_id}_{curr}_{try_next_fy}"
    fx = forex_cache.get(cache_key)
    if fx:
        print(f"✅ Using FY rate from adjacent year...")

if not fx:
    try_prev_fy = financial_year - 1
    cache_key = f"{entity_id}_{curr}_{try_prev_fy}"
    fx = forex_cache.get(cache_key)
    if fx:
        print(f"✅ Using FY rate from previous year...")
```

**New Code (strict matching):**
```python
# Try FY-specific cache - STRICT MATCHING ONLY
fx = None
if entity_id and financial_year:
    cache_key = f"{entity_id}_{curr}_{financial_year}"
    fx = forex_cache.get(cache_key)
    
    # If not found, log warning and skip (don't use fallback)
    if not fx:
        print(f"⚠️ WARNING: No forex rates found for Entity {entity_id}, Currency {curr}, FY {financial_year}. Skipping calculation.")
        # Optionally: Set a flag in the row to indicate missing rates
        row["_forex_rate_missing"] = True
        continue  # Skip this row
```

**Why:** This enforces that rates must be from the exact same FY as the data.

---

### Step 8: Update Database Save Logic - Same Strict Matching

**File to Modify:** `backend/routes/structure_data.py`

**Location:** `_calculate_and_save_forex_rates()` function (similar logic)

**What to Change:**
- Remove adjacent year fallback
- Only use rates from exact FY match
- Log warnings for missing rates
- Optionally: Store a flag in database indicating which rows have missing rates

**Why:** Consistency - both in-memory and database calculations should use same logic.

---

### Step 9: Add Validation - Check Rates Exist Before Processing

**File to Modify:** `backend/routes/structure_data.py`

**Location:** In `get_structured_data()` or before processing

**What to Add:**
```python
def validate_forex_rates_for_fy(entity_id, financial_year, currency):
    """
    Validate that forex rates exist for the given entity, FY, and currency.
    Returns: { valid: bool, message: str }
    """
    from routes.forex import get_entity_fy_forex_rate
    
    rate = get_entity_fy_forex_rate(entity_id, currency, financial_year)
    if not rate:
        return {
            'valid': False,
            'message': f'Forex rates not configured for Entity {entity_id}, Currency {currency}, FY {financial_year}'
        }
    return { 'valid': True, 'message': 'OK' }
```

**Why:** Proactive validation can prevent processing data without rates.

---

### Step 10: Update Frontend - Show Warnings for Missing Rates

**File to Modify:** `entity-insights-hub/src/pages/StructuredData.tsx` (or relevant page)

**What to Add:**
- Check if any rows have `_forex_rate_missing` flag
- Display warning banner: "Some rows could not be converted due to missing forex rates"
- Show which entities/FYs/currencies are missing rates

**Why:** Users need visibility when rates are missing.

---

## 📝 Implementation Order

1. ✅ **Step 1**: Create database migration for `financial_year_master` table
2. ✅ **Step 2**: Create backend API routes for financial year master
3. ✅ **Step 6**: Register routes in `app.py`
4. ✅ **Step 4**: Add frontend API client methods
5. ✅ **Step 5**: Create frontend UI in Settings page
6. ✅ **Step 3**: Add upload validation against master data
7. ✅ **Step 7**: Remove adjacent year fallback in `_apply_forex_rates()`
8. ✅ **Step 8**: Remove adjacent year fallback in `_calculate_and_save_forex_rates()`
9. ✅ **Step 9**: Add validation for forex rates before processing
10. ✅ **Step 10**: Update frontend to show warnings

---

## 🧪 Testing Checklist

### Requirement 2 Testing:
- [ ] Can create new financial year in master data
- [ ] Can edit existing financial year
- [ ] Can activate/deactivate financial year
- [ ] Upload for date within active FY range → ✅ Allowed
- [ ] Upload for date outside active FY range → ❌ Rejected with clear error
- [ ] Upload for date in inactive FY → ❌ Rejected

### Requirement 3 Testing:
- [ ] Data for FY 2024-25 uses rates from FY 2024-25 only
- [ ] If rates missing for FY 2024-25, calculation skipped (not using adjacent years)
- [ ] Warning shown when rates are missing
- [ ] P&L items use average of (opening_rate + closing_rate) from same FY
- [ ] Balance Sheet items use closing_rate from same FY

---

## ⚠️ Important Notes

1. **Backward Compatibility**: Existing data should continue to work. We'll add validation but not break existing functionality.

2. **Migration Safety**: The migration will create new tables/columns without affecting existing data.

3. **Error Messages**: All error messages should be clear and actionable.

4. **Performance**: Add indexes on date ranges for fast validation queries.

5. **Data Integrity**: Before deleting a financial year, check if any data exists for that FY.

---

## 📦 Files to Create/Modify

### New Files:
- `backend/migrations/005_financial_year_master.sql`
- `backend/routes/financial_year_master.py`

### Modified Files:
- `backend/app.py` (register routes)
- `backend/routes/upload_data.py` (add validation)
- `backend/routes/structure_data.py` (remove fallback, strict matching)
- `entity-insights-hub/src/lib/api.ts` (add API methods)
- `entity-insights-hub/src/pages/Settings.tsx` (add master data UI)

---

## ✅ Confirmation Required

Please confirm:
1. ✅ The approach looks correct
2. ✅ The database structure is acceptable
3. ✅ The validation logic matches your requirements
4. ✅ The UI placement (Settings page) is appropriate
5. ✅ The strict FY matching (no fallbacks) is what you want

Once confirmed, I'll proceed with implementation step by step! 🚀
