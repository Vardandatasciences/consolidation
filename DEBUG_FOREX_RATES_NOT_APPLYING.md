# Debug: Forex Rates Not Applying to Structured Data

## Issue
You have forex rates configured (Opening: 82.00, Closing: 79.00, Monthly rates set), but structured data still shows `Avg_Fx_Rt = 1.0000`.

## Root Cause Checks

### 1. Check Currency Code Match ⚠️

**Your Forex Rates are set for**: `USD`  
**Your Structured Data uses**: Check what's in `localCurrencyCode` column

**Action**: 
- Go to Structured Data page
- Look at the `localCurrencyCode` column
- It MUST match the currency you set in Forex Rates (USD)

**If Mismatch**:
- Either update Forex Rates to match your data's currency
- OR update your data's currency code

### 2. Check Entity Code Match ⚠️

**Your Forex Rates are for**: Test Company (TEST001)  
**Your Structured Data entity**: Check `entityCode` column

**Action**:
- Structured Data must have `entityCode = "TEST001"` (or matching entity code)
- The system joins on `entityCode` to get `entity_id`

### 3. Check Financial Year Match ⚠️

**Your Forex Rates are for**: FY 2024-25  
**Your Structured Data Year**: Check `Year` column

**Action**:
- Structured Data must have `Year = 2024` (or matching financial year)
- The system uses this to lookup rates

### 4. Check mainCategory is Set ⚠️ **CRITICAL**

**The system ONLY applies forex rates if `mainCategory` is set!**

**Action**:
```sql
-- Check if your data has mainCategory
SELECT COUNT(*) as total_rows,
       COUNT(mainCategory) as rows_with_maincategory,
       COUNT(*) - COUNT(mainCategory) as rows_without_maincategory
FROM final_structured 
WHERE entityCode = 'TEST001' AND Year = 2024;
```

**If rows_without_maincategory > 0**:
- You need to map your accounts to categories
- Go to Code Master page and create mappings
- OR the data needs to be processed with category mappings

### 5. Check Month Matching (For Monthly Rates)

**Your Monthly Rates**: October (79.00), November (83.00), December (85.00)  
**Your Structured Data Month**: Check `Month` or `selectedMonth` column

**Action**:
- For December data, the system will use December's monthly rate (85.00)
- Make sure the Month column matches exactly: "December" (case-insensitive)

## Quick Debug Query

Run this SQL to check if rates should match:

```sql
-- Check your data characteristics
SELECT 
    fs.entityCode,
    fs.Year,
    fs.Month,
    fs.localCurrencyCode,
    fs.mainCategory,
    COUNT(*) as row_count,
    MIN(fs.Avg_Fx_Rt) as min_rate,
    MAX(fs.Avg_Fx_Rt) as max_rate
FROM final_structured fs
LEFT JOIN entity_master em ON fs.entityCode = em.ent_code
WHERE fs.Year = 2024
GROUP BY fs.entityCode, fs.Year, fs.Month, fs.localCurrencyCode, fs.mainCategory;
```

Then check if rates exist:
```sql
-- Check if rates exist for this entity/year/currency
SELECT * FROM entity_forex_rates
WHERE entity_id = (SELECT ent_id FROM entity_master WHERE ent_code = 'TEST001')
  AND financial_year = 2024
  AND currency = 'USD';
```

## Most Likely Issues (In Order)

1. **mainCategory not set** - System requires this to apply rates
2. **Currency mismatch** - Data uses different currency than rates (e.g., INR vs USD)
3. **Entity code mismatch** - Data uses different entity code
4. **Financial year mismatch** - Data uses different year

## Solution Steps

1. ✅ **Verify mainCategory is set** for your data
   - If not, map accounts in Code Master page

2. ✅ **Verify currency matches**
   - Forex Rates: USD
   - Structured Data localCurrencyCode: USD

3. ✅ **Refresh Structured Data page**
   - The system applies rates automatically when viewing
   - No need to re-upload if rates are configured correctly

4. ✅ **Check browser console** (F12)
   - Look for any errors
   - Check network tab for API responses

## Expected Behavior

Once everything matches, when you view Structured Data:
- **December 2024 data** → Uses December monthly rate: **85.00** ✅
- **November 2024 data** → Uses November monthly rate: **83.00** ✅
- **October 2024 data** → Uses October monthly rate: **79.00** ✅
- **Other months or no monthly rate** → Uses opening/closing rates (Balance Sheet: 79.00, P&L: 80.50)




