# Testing Guide - Requirements 2 & 3 Implementation

## 🎯 How to Verify Implementation

This guide provides step-by-step instructions to verify that Requirements 2 and 3 are properly implemented.

---

## ✅ REQUIREMENT 2: Master Data Section for Financial Year

### Test 1: Check Database Table Exists

**Run in MySQL:**
```sql
USE balance_sheet;

-- Check if table exists
SHOW TABLES LIKE 'financial_year_master';

-- Check table structure
DESCRIBE financial_year_master;

-- Should show columns: id, financial_year, start_date, end_date, is_active, description, created_at, updated_at, created_by
```

**Expected Result:** ✅ Table exists with all columns

---

### Test 2: Check Backend API Endpoints

**Test in browser or Postman:**

1. **List Financial Years:**
   ```
   GET http://localhost:5000/financial-year-master
   ```
   **Expected:** Returns JSON with `success: true` and `financial_years` array

2. **Validate Date:**
   ```
   GET http://localhost:5000/financial-year-master/validate?date=2024-04-15
   ```
   **Expected:** Returns validation result

**Or use curl:**
```bash
# List all financial years
curl http://localhost:5000/financial-year-master

# Validate a date
curl "http://localhost:5000/financial-year-master/validate?date=2024-04-15"
```

**Expected Result:** ✅ API endpoints respond correctly

---

### Test 3: Check Frontend UI

**Steps:**
1. Start frontend: `cd entity-insights-hub && npm run dev`
2. Login to the application
3. Navigate to **Settings** page
4. Look for **"Master Data"** tab

**Expected Result:** ✅ "Master Data" tab is visible in Settings

---

### Test 4: Create Financial Year via UI

**Steps:**
1. Go to Settings → Master Data tab
2. Click **"Add Financial Year"** button
3. Fill in the form:
   - Financial Year: `2024-25`
   - Start Date: `2024-04-01`
   - End Date: `2025-03-31`
   - Active: ✅ (checked)
   - Description: `Financial Year 2024-25` (optional)
4. Click **"Create"**

**Expected Result:** ✅ 
- Financial year appears in the table
- Success toast message shown
- Table shows: Financial Year, Start Date, End Date, Status (Active), Description

---

### Test 5: Upload Validation - Data WITHIN Active FY Range

**Steps:**
1. Ensure FY 2024-25 is active (created in Test 4)
2. Go to **Upload** page
3. Select:
   - Entity: Any entity
   - Financial Year: `2024` (ending year)
   - Month: `April` (or any month between April 2024 - March 2025)
4. Upload a test Excel file

**Expected Result:** ✅ 
- Upload proceeds successfully
- No validation error
- Data is processed

**Check Backend Logs:**
```
✅ Financial year validation passed: 2024-25
```

---

### Test 6: Upload Validation - Data OUTSIDE Active FY Range

**Steps:**
1. Go to **Upload** page
2. Select:
   - Entity: Any entity
   - Financial Year: `2026` (ending year)
   - Month: `April` (April 2026 - outside configured FY ranges)
3. Try to upload a test Excel file

**Expected Result:** ❌ 
- Upload is **REJECTED**
- Error message: `"Data upload not allowed: Date 2026-04-01 falls outside configured financial year ranges. Please configure the financial year in Master Data settings."`
- Error code: `FINANCIAL_YEAR_VALIDATION_FAILED`

**Check Backend Logs:**
```
⚠️ Financial year validation failed: Date 2026-04-01 falls outside configured financial year ranges
```

---

### Test 7: Upload Validation - Inactive Financial Year

**Steps:**
1. In Settings → Master Data:
   - Edit FY 2024-25
   - Uncheck "Active" toggle
   - Save
2. Go to **Upload** page
3. Select:
   - Financial Year: `2024`
   - Month: `April`
4. Try to upload

**Expected Result:** ❌ 
- Upload is **REJECTED**
- Error: Data falls outside active financial year ranges

---

### Test 8: Edit Financial Year

**Steps:**
1. In Settings → Master Data tab
2. Click **Edit** icon (pencil) on any financial year
3. Change:
   - End Date: `2025-03-31` → `2025-04-30`
   - Description: Update description
4. Click **"Update"**

**Expected Result:** ✅ 
- Changes saved
- Table shows updated values
- Success toast message

---

### Test 9: Delete/Deactivate Financial Year

**Steps:**
1. In Settings → Master Data tab
2. Click **Delete** icon (trash) on a financial year
3. Confirm deletion

**Expected Result:** ✅ 
- Financial year status changes to "Inactive" (soft delete)
- Or shows error if data exists for that FY
- Success message shown

---

## ✅ REQUIREMENT 3: Strict Currency Calculations Based on Financial Year

### Test 10: Check Forex Rates Configuration

**Steps:**
1. Go to **Forex** page
2. Select an entity
3. Check if forex rates exist for different financial years

**Expected Result:** ✅ 
- Can see forex rates per financial year
- Each rate has: Opening Rate, Closing Rate, Financial Year

---

### Test 11: Verify Strict FY Matching - Rates from Same FY

**Steps:**
1. Configure forex rates:
   - Entity: Test Entity
   - Financial Year: `2024-25` (ending year 2024)
   - Currency: `USD`
   - Opening Rate: `82.00`
   - Closing Rate: `85.00`
2. Upload data:
   - Same Entity
   - Financial Year: `2024`
   - Month: `May` (within FY 2024-25)
3. Check structured data:
   - Go to **Structured Data** page
   - Filter by Entity and FY 2024-25
   - Check `Avg_Fx_Rt` column

**Expected Result:** ✅ 
- P&L items: `Avg_Fx_Rt = (82.00 + 85.00) / 2 = 83.50`
- Balance Sheet items: `Avg_Fx_Rt = 85.00` (closing rate)
- Rates used are from FY 2024-25

**Check Backend Logs:**
```
✅ Using FY-specific rate: Entity X, Currency USD, FY 2024
```

---

### Test 12: Verify No Adjacent Year Fallback

**Steps:**
1. Configure forex rates:
   - Entity: Test Entity
   - Financial Year: `2025-26` (ending year 2025)
   - Currency: `USD`
   - Opening Rate: `86.00`
   - Closing Rate: `88.00`
2. **DO NOT** configure rates for FY 2024-25
3. Upload data:
   - Same Entity
   - Financial Year: `2024` (FY 2024-25)
   - Month: `May`
4. Check structured data

**Expected Result:** ⚠️ 
- **NO rates applied** (calculation skipped)
- `Avg_Fx_Rt` is NULL or not calculated
- Warning in logs: `"⚠️ WARNING: No forex rates found for Entity X, Currency USD, FY 2024. Skipping calculation for this row."`

**Check Backend Logs:**
```
⚠️ WARNING: No forex rates found for Entity X, Currency USD, FY 2024. Skipping calculation for this row.
```

**Key Point:** System should **NOT** use rates from FY 2025-26 (adjacent year) for FY 2024-25 data.

---

### Test 13: Verify P&L Calculation Uses Average Rate

**Steps:**
1. Ensure data has rows classified as P&L (Profit & Loss)
2. Configure forex rates:
   - Opening Rate: `80.00`
   - Closing Rate: `90.00`
3. Upload data for that FY
4. Check structured data for P&L rows

**Expected Result:** ✅ 
- P&L rows: `Avg_Fx_Rt = (80.00 + 90.00) / 2 = 85.00`
- Formula: `(opening_rate + closing_rate) / 2`

**SQL Query to Verify:**
```sql
SELECT 
    Particular,
    mainCategory,
    category1,
    transactionAmount,
    Avg_Fx_Rt,
    transactionAmountUSD,
    financial_year
FROM final_structured
WHERE mainCategory IS NOT NULL
  AND (category1 LIKE '%profit%loss%' OR category1 LIKE '%p&l%')
  AND financial_year = '2024-25'
LIMIT 10;
```

**Check:** `Avg_Fx_Rt` should equal `(opening_rate + closing_rate) / 2`

---

### Test 14: Verify Balance Sheet Uses Closing Rate

**Steps:**
1. Ensure data has rows classified as Balance Sheet
2. Configure forex rates:
   - Opening Rate: `80.00`
   - Closing Rate: `90.00`
3. Upload data for that FY
4. Check structured data for Balance Sheet rows

**Expected Result:** ✅ 
- Balance Sheet rows: `Avg_Fx_Rt = 90.00` (closing rate)
- Formula: `closing_rate`

**SQL Query to Verify:**
```sql
SELECT 
    Particular,
    mainCategory,
    category1,
    transactionAmount,
    Avg_Fx_Rt,
    transactionAmountUSD,
    financial_year
FROM final_structured
WHERE mainCategory IS NOT NULL
  AND (category1 LIKE '%balance%sheet%' OR category1 NOT LIKE '%profit%loss%' AND category1 NOT LIKE '%p&l%')
  AND financial_year = '2024-25'
LIMIT 10;
```

**Check:** `Avg_Fx_Rt` should equal `closing_rate` (not average)

---

### Test 15: Check Code Changes - No Adjacent Year Fallback

**Verify in Code:**

**File:** `backend/routes/structure_data.py`

**Search for:** `try_next_fy` or `try_prev_fy` or `adjacent year`

**Expected Result:** ✅ 
- **NO** code that tries `financial_year + 1` or `financial_year - 1`
- Only exact FY matching: `f"{entity_id}_{curr}_{financial_year}"`

**Check these functions:**
1. `_build_forex_cache()` - Should NOT have adjacent year logic
2. `_apply_forex_rates()` - Should NOT have adjacent year logic
3. `_calculate_and_save_forex_rates()` - Should NOT have adjacent year logic

**Search Command:**
```bash
# In backend/routes/structure_data.py
grep -n "try_next_fy\|try_prev_fy\|adjacent" structure_data.py
```

**Expected:** No results (or only in comments)

---

## 📋 Quick Verification Checklist

### Requirement 2 Checklist:
- [ ] `financial_year_master` table exists in database
- [ ] Backend API `/financial-year-master` endpoints work
- [ ] Frontend Settings page has "Master Data" tab
- [ ] Can create financial year via UI
- [ ] Can edit financial year via UI
- [ ] Can delete/deactivate financial year via UI
- [ ] Upload WITHIN active FY range → ✅ Allowed
- [ ] Upload OUTSIDE active FY range → ❌ Rejected
- [ ] Upload for inactive FY → ❌ Rejected
- [ ] Error messages are clear and actionable

### Requirement 3 Checklist:
- [ ] Forex rates configured per financial year
- [ ] Data uses rates from **exact same FY** (not adjacent years)
- [ ] P&L items use average: `(opening_rate + closing_rate) / 2`
- [ ] Balance Sheet items use: `closing_rate`
- [ ] If rates missing for FY → Calculation skipped (no fallback)
- [ ] Warnings logged when rates are missing
- [ ] No adjacent year fallback code in `structure_data.py`

---

## 🔍 SQL Queries for Verification

### Check Financial Year Master Data:
```sql
SELECT * FROM financial_year_master ORDER BY start_date DESC;
```

### Check Upload Validation:
```sql
-- Check if data exists outside configured FY ranges
SELECT 
    entityCode,
    financial_year,
    Month,
    Year,
    COUNT(*) as record_count
FROM final_structured
WHERE financial_year NOT IN (
    SELECT financial_year 
    FROM financial_year_master 
    WHERE is_active = 1
)
GROUP BY entityCode, financial_year, Month, Year;
```

### Check Forex Rate Usage:
```sql
-- Check which FY rates are being used
SELECT 
    entityCode,
    financial_year,
    localCurrencyCode,
    COUNT(*) as rows_with_rates,
    AVG(Avg_Fx_Rt) as avg_rate_used
FROM final_structured
WHERE mainCategory IS NOT NULL
  AND Avg_Fx_Rt IS NOT NULL
GROUP BY entityCode, financial_year, localCurrencyCode;
```

### Check Missing Rates:
```sql
-- Find rows that should have rates but don't
SELECT 
    entityCode,
    financial_year,
    localCurrencyCode,
    COUNT(*) as rows_without_rates
FROM final_structured
WHERE mainCategory IS NOT NULL
  AND Avg_Fx_Rt IS NULL
  AND localCurrencyCode IS NOT NULL
GROUP BY entityCode, financial_year, localCurrencyCode;
```

---

## 🐛 Troubleshooting

### Issue: Foreign Key Error
**Solution:** Use the simple SQL version without foreign key (provided earlier)

### Issue: Upload Not Validating
**Check:**
1. Is `financial_year_master` table populated?
2. Are financial years marked as `is_active = 1`?
3. Check backend logs for validation messages

### Issue: Rates Not Applied
**Check:**
1. Are forex rates configured for the exact FY?
2. Check backend logs for warnings
3. Verify entity_id matches between data and rates

### Issue: Adjacent Year Fallback Still Happening
**Check:**
1. Search code for `try_next_fy` or `try_prev_fy`
2. Should return no results
3. Verify strict matching in `_apply_forex_rates()`

---

## ✅ Success Criteria

**Requirement 2 is working if:**
- ✅ Can manage financial years in UI
- ✅ Uploads outside FY ranges are rejected
- ✅ Clear error messages guide users

**Requirement 3 is working if:**
- ✅ Calculations use rates from exact same FY
- ✅ No fallback to adjacent years
- ✅ P&L uses average, Balance Sheet uses closing rate
- ✅ Missing rates result in skipped calculations (not fallback)

---

**Run through these tests to verify your implementation!** 🚀
