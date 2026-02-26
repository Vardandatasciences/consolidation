# Quick Fix: Avg_Fx_Rt Showing 1.0000

## Problem
Your structured data shows `Avg_Fx_Rt = 1.0000` because:
1. The database already has `1.0000` stored
2. **You haven't set up forex rates yet** in the new system

## Solution: Set Up Forex Rates First

### Step 1: Go to Forex Rates Page
1. Navigate to **Forex Rates** page (`/forex`)
2. Select your **Entity** (the one with December 2024 data)
3. Select **Financial Year**: `2024`

### Step 2: Add Forex Rates
Click **"Add Rate"** button and fill in:
- **Currency**: `INR` (or your currency code)
- **Opening Rate**: `80.00` (your actual rate at FY start)
- **Closing Rate**: `82.00` (your actual rate for December)
- **Month Number**: `12`
- **Month Name**: `December`
- ✅ Check **"Save as monthly rate"**
- Click **Save**

### Step 3: Refresh Structured Data
1. Go back to **Structured Data** page
2. The system will automatically use the new rates
3. You should now see correct rates (not 1.0000)

## How It Works Now

The system **automatically applies rates in memory** when you view the data. It:
1. Looks for monthly rates first (for December → uses December's rate)
2. Falls back to opening/closing rates if no monthly rate found
3. Applies the correct rate based on item type:
   - Balance Sheet: Uses closing/monthly rate
   - P&L: Uses average of opening + closing

## If Rates Still Show 1.0000

**Check:**
1. Did you set up rates in Forex Rates page? ✅
2. Is the entity and financial year correct? ✅
3. Is the currency code matching? (e.g., `INR` in rates = `INR` in data)

**Debug Query:**
```sql
-- Check if rates are configured
SELECT * FROM entity_forex_rates 
WHERE entity_id = <your_entity_id> AND financial_year = 2024;

-- Check monthly rates
SELECT * FROM entity_forex_monthly_rates 
WHERE entity_id = <your_entity_id> AND financial_year = 2024;
```

If these queries return empty, you need to set up the rates first!

## Important Notes

- The system **does NOT use** the old `forex_master` table anymore for entity-specific rates
- You **MUST** set up rates in the Forex Rates page using the new system
- Once rates are configured, the data will automatically use them (no need to re-upload)





