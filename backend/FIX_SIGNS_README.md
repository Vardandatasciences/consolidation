# Fix Existing Transaction Amount Signs

## Problem
All existing records in `final_structured` table have positive values, even for Credit (Cr) entries. This is because they were uploaded before the sign correction logic was implemented.

## Solution
Run the migration script to fix existing data by reading the original Dr/Cr indicators from `rawData` table.

## How to Run

### Step 1: Navigate to backend directory
```bash
cd backend
```

### Step 2: Run the migration script
```bash
python fix_existing_signs.py
```

## What the Script Does

1. **Reads all records** from `final_structured` table
2. **Matches with rawData** to find original Dr/Cr indicators
3. **Updates signs**:
   - Dr (Debit) → **Positive** value (e.g., `1365.00`)
   - Cr (Credit) → **Negative** value (e.g., `-102901.37`)
4. **Recalculates** `transactionAmountUSD` based on new signs

## Expected Output

```
🔧 Starting sign correction for existing data...
📊 Found 150 records to check
✅ Updated sl_no=1, Cash: 102901.37 → -102901.37 (Cr)
✅ Updated sl_no=2, Bank: 1365.00 → 1365.00 (Dr)
...
🎉 Sign Correction Complete!
✅ Updated: 75 records
⏭️ Skipped: 10 records (no raw data or couldn't parse)
❌ Errors: 0 records
📊 Total processed: 150 records
```

## After Running

1. **Restart your backend** server to pick up changes
2. **Refresh Structured Data page** - you'll now see negative values for Cr entries
3. **New uploads** will automatically use correct signs

## Verification

To verify the fix worked, run this SQL query:

```sql
SELECT 
    Particular,
    transactionAmount,
    Month
FROM final_structured
WHERE transactionAmount < 0
LIMIT 10;
```

You should see records with negative amounts (these are Cr entries).

## Important Notes

- ⚠️ **Backup your database** before running migration (optional but recommended)
- ✅ Script is **safe to run multiple times** - it only updates records with wrong signs
- ✅ Script **preserves absolute values** - only changes the sign based on Dr/Cr
- ✅ **No data loss** - original raw data is preserved in `rawData` table

