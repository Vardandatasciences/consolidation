# Testing Guide: Financial Year Based Forex Rate Calculations

## ✅ Feature Status: **IMPLEMENTED**

The system **already implements** the requirement:
> "The calculations of the common currency should be based on the rates within the financial year and the data pertaining to the same financial year. Example: The Average rate application to P&L for the months April 2024 to March 2025 should be the average of (Opening rate and Closing rates) for financial year 2024-25."

---

## 📋 How It Works

### Calculation Logic:
1. **P&L Items** (Profit & Loss):
   - Uses: **Average of (Opening Rate + Closing Rate) / 2**
   - Example: If Opening Rate = 80.00 and Closing Rate = 85.00
   - Average Rate = (80.00 + 85.00) / 2 = **82.50**

2. **Balance Sheet Items**:
   - Uses: **Closing Rate** (FY end rate)
   - Example: If Closing Rate = 85.00
   - Rate Used = **85.00**

3. **Strict FY Matching**:
   - Data for FY 2024-25 → Must use rates from FY 2024-25 only
   - No fallback to adjacent years
   - If rates missing for specific FY → Calculation skipped with warning

---

## 🧪 Step-by-Step Testing Guide

### Prerequisites:
1. **Entity Master Data**: At least one entity configured
2. **Financial Year Master**: FY 2024-25 configured (or your test FY)
3. **Forex Rates**: Opening and Closing rates for the test FY

---

### Test Case 1: Verify P&L Uses Average Rate

#### Step 1: Configure Forex Rates for FY 2024-25
1. Go to **Forex** page (`/forex`)
2. Select:
   - **Entity**: Your test entity (e.g., "IRMS")
   - **Financial Year**: 2024-25
   - **Currency**: USD (or your test currency)
3. Enter:
   - **Opening Rate**: `80.00` (rate at April 1, 2024)
   - **Closing Rate**: `85.00` (rate at March 31, 2025)
4. Click **Save**

**Expected Result:**
- Average Rate for P&L = (80.00 + 85.00) / 2 = **82.50**

---

#### Step 2: Upload P&L Data for FY 2024-25
1. Go to **Upload** page (`/upload`)
2. Select:
   - **Entity**: Same entity as Step 1
   - **Financial Year**: 2024-25 (ending year: 2024)
   - **Month**: Any month from April 2024 to March 2025 (e.g., "June 2024")
3. Upload Excel file with **P&L items** (Revenue, Expenses, etc.)
4. Ensure data has:
   - `mainCategory` = "Profit and Loss" or "P&L"
   - `localCurrencyCode` = "USD" (or your test currency)
   - `transactionAmount` = Some amount (e.g., 100,000)

**Expected Result:**
- System should apply **Avg_Fx_Rt = 82.50** to P&L rows
- `transactionAmountUSD` = `transactionAmount` × 82.50

---

#### Step 3: Verify in Database
Run this SQL query:
```sql
SELECT 
    entityCode,
    financial_year,
    mainCategory,
    category1,
    localCurrencyCode,
    transactionAmount,
    Avg_Fx_Rt,
    transactionAmountUSD,
    Month,
    Year
FROM final_structured
WHERE financial_year = '2024-25'
  AND mainCategory LIKE '%Profit%Loss%'
  AND localCurrencyCode = 'USD'
ORDER BY Month;
```

**Expected Results:**
- `Avg_Fx_Rt` = **82.50** (average of 80.00 and 85.00)
- `transactionAmountUSD` = `transactionAmount` × 82.50
- All months (April 2024 to March 2025) should use the same average rate

---

### Test Case 2: Verify Balance Sheet Uses Closing Rate

#### Step 1: Use Same Forex Rates (from Test Case 1)
- Opening Rate: 80.00
- Closing Rate: 85.00

#### Step 2: Upload Balance Sheet Data
1. Upload Excel file with **Balance Sheet items** (Assets, Liabilities, etc.)
2. Ensure data has:
   - `mainCategory` = "Balance Sheet"
   - `localCurrencyCode` = "USD"
   - `transactionAmount` = Some amount (e.g., 500,000)

**Expected Result:**
- System should apply **Avg_Fx_Rt = 85.00** (closing rate, not average)
- `transactionAmountUSD` = `transactionAmount` × 85.00

#### Step 3: Verify in Database
```sql
SELECT 
    entityCode,
    financial_year,
    mainCategory,
    localCurrencyCode,
    transactionAmount,
    Avg_Fx_Rt,
    transactionAmountUSD
FROM final_structured
WHERE financial_year = '2024-25'
  AND mainCategory LIKE '%Balance Sheet%'
  AND localCurrencyCode = 'USD'
LIMIT 10;
```

**Expected Results:**
- `Avg_Fx_Rt` = **85.00** (closing rate)
- `transactionAmountUSD` = `transactionAmount` × 85.00

---

### Test Case 3: Verify Strict FY Matching

#### Step 1: Configure Rates for Different FYs
1. **FY 2024-25**: Opening = 80.00, Closing = 85.00
2. **FY 2025-26**: Opening = 85.00, Closing = 90.00

#### Step 2: Upload Data for FY 2024-25
- Upload data for FY 2024-25

**Expected Result:**
- Should use rates from FY 2024-25 only (80.00/85.00)
- Should NOT use rates from FY 2025-26 (85.00/90.00)

#### Step 3: Check Backend Logs
Look for messages like:
```
✅ Found FY-specific rate: Entity 1, Currency USD, FY 2024 - Opening: 80.00, Closing: 85.00
```

If rates are missing:
```
⚠️ WARNING: No forex rates found for Entity 1, Currency USD, FY 2024. Skipping calculation for this row.
```

---

### Test Case 4: Verify Different Months Use Same FY Rates

#### Scenario:
- Upload data for **April 2024** (FY 2024-25)
- Upload data for **June 2024** (FY 2024-25)
- Upload data for **March 2025** (FY 2024-25)

**Expected Result:**
- All months should use the **same rates** from FY 2024-25:
  - P&L: Average = 82.50 (same for all months)
  - Balance Sheet: Closing = 85.00 (same for all months)

**Why?** Because they all belong to the same financial year (2024-25).

---

## 🔍 Verification Queries

### Query 1: Check Applied Rates by Category
```sql
SELECT 
    mainCategory,
    COUNT(*) as row_count,
    AVG(Avg_Fx_Rt) as avg_rate_applied,
    MIN(Avg_Fx_Rt) as min_rate,
    MAX(Avg_Fx_Rt) as max_rate
FROM final_structured
WHERE financial_year = '2024-25'
  AND localCurrencyCode = 'USD'
  AND Avg_Fx_Rt IS NOT NULL
GROUP BY mainCategory;
```

**Expected:**
- P&L items: `avg_rate_applied` ≈ 82.50 (average of opening + closing)
- Balance Sheet items: `avg_rate_applied` = 85.00 (closing rate)

---

### Query 2: Verify Rate Consistency Across Months
```sql
SELECT 
    Month,
    mainCategory,
    AVG(Avg_Fx_Rt) as avg_rate,
    COUNT(*) as count
FROM final_structured
WHERE financial_year = '2024-25'
  AND localCurrencyCode = 'USD'
  AND mainCategory LIKE '%Profit%Loss%'
GROUP BY Month, mainCategory
ORDER BY Month;
```

**Expected:**
- All months should show the same `avg_rate` (82.50 for P&L)

---

### Query 3: Check for Missing Rates
```sql
SELECT 
    entityCode,
    financial_year,
    localCurrencyCode,
    COUNT(*) as rows_without_rate
FROM final_structured
WHERE financial_year = '2024-25'
  AND localCurrencyCode IS NOT NULL
  AND Avg_Fx_Rt IS NULL
  AND mainCategory IS NOT NULL
GROUP BY entityCode, financial_year, localCurrencyCode;
```

**Expected:**
- Should return 0 rows (or only rows where rates weren't configured)

---

## 🐛 Troubleshooting

### Issue: Rates Not Applied
**Check:**
1. Are forex rates configured for the exact same FY?
   ```sql
   SELECT * FROM entity_forex_rates 
   WHERE entity_id = <your_entity_id>
     AND currency = 'USD'
     AND financial_year = 2024;
   ```

2. Does data have `mainCategory` field?
   ```sql
   SELECT COUNT(*) FROM final_structured 
   WHERE financial_year = '2024-25' 
     AND mainCategory IS NULL;
   ```

3. Check backend logs for warnings:
   - Look for: `⚠️ WARNING: No forex rates found`

---

### Issue: Wrong Rate Applied
**Check:**
1. Verify which rates are in cache:
   - Check backend console logs when processing data
   - Look for: `✅ Found FY-specific rate: Entity X, Currency Y, FY Z`

2. Verify data's financial_year matches rates' financial_year:
   ```sql
   SELECT DISTINCT financial_year FROM final_structured WHERE entityCode = '<your_entity>';
   SELECT DISTINCT financial_year FROM entity_forex_rates WHERE entity_id = <your_entity_id>;
   ```

---

## 📊 Example Test Data

### Forex Rates Setup:
```
Entity: IRMS
Financial Year: 2024-25
Currency: USD
Opening Rate: 80.00
Closing Rate: 85.00
```

### Expected Calculations:
- **P&L Average Rate**: (80.00 + 85.00) / 2 = **82.50**
- **Balance Sheet Rate**: **85.00**

### Test Transaction:
```
Transaction Amount: 100,000 (local currency)
Category: Profit and Loss
```

### Expected Results:
- **Avg_Fx_Rt**: 82.50
- **transactionAmountUSD**: 100,000 × 82.50 = **8,250,000**

---

## ✅ Success Criteria

Your test is successful if:
1. ✅ P&L items use average of (opening + closing) / 2
2. ✅ Balance Sheet items use closing rate
3. ✅ Rates are from the exact same FY as data
4. ✅ All months in the same FY use the same rates
5. ✅ No fallback to adjacent years or legacy rates

---

## 📝 Notes

- The system enforces **strict FY matching** - no fallbacks
- If rates are missing for a specific FY, calculations are skipped (not calculated with wrong rates)
- Rates are applied during data upload/processing, not at query time
- To recalculate rates, use the "Recalculate" function in the Forex page
