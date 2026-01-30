# Fix: Forex Rates Showing 1.0000

## Problem
The structured data is showing `Avg_Fx_Rt = 1.0000` for all rows, which means the system isn't finding or applying the correct forex rates from the new `entity_forex_rates` and `entity_forex_monthly_rates` tables.

## Root Cause
1. The database already has `1.0000` stored in `Avg_Fx_Rt` column
2. The in-memory rate calculation is working, but the rates need to be:
   - First configured in the Forex Rates page
   - Then recalculated and saved to the database

## Solution Steps

### Step 1: Set Up Forex Rates
1. Go to **Forex Rates** page (`/forex`)
2. Select your entity and financial year (2024)
3. Add forex rates:
   - Currency: INR (or your currency)
   - Opening Rate: 80.00 (or your actual rate)
   - Closing Rate: 82.00 (or your actual rate)
   - Month: December (month 12)
   - Check "Save as monthly rate"
4. Click **Save**

### Step 2: Recalculate All Rates
The system needs to recalculate all existing data with the new rates. You can do this by:

**Option A: Use the Recalculate Endpoint (Recommended)**
```bash
POST /api/structure/recalculate-all-forex-rates
```

**Option B: Re-upload Data**
- Re-upload your trial balance data, which will trigger recalculation

### Step 3: Verify
1. Go to Structured Data page
2. Check that `Avg_Fx_Rt` now shows the correct rates (not 1.0000)
3. For December data, it should use the December monthly rate if set

## Expected Behavior
- **December 2024 data** should use the December monthly rate (if configured)
- If no monthly rate, it uses opening/closing rates based on item type:
  - Balance Sheet: Closing rate
  - P&L: Average of opening + closing rates

## Debugging

### Check if Rates Are Configured
```sql
-- Check entity forex rates
SELECT * FROM entity_forex_rates 
WHERE entity_id = <your_entity_id> AND financial_year = 2024;

-- Check monthly rates
SELECT * FROM entity_forex_monthly_rates 
WHERE entity_id = <your_entity_id> AND financial_year = 2024 
ORDER BY month_number;
```

### Check Current Data
```sql
-- Check what rates are currently stored
SELECT entityCode, Month, Year, localCurrencyCode, Avg_Fx_Rt, COUNT(*) 
FROM final_structured 
WHERE Year = 2024 AND Month = 'December'
GROUP BY entityCode, Month, Year, localCurrencyCode, Avg_Fx_Rt;
```

If you see 1.0000, the rates need to be recalculated.




