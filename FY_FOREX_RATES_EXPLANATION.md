# Why Financial Year Based Forex Rates Matter

## The Problem Before (Legacy System)

### Old Way:
- **One rate per currency** for ALL entities and ALL financial years
- Example: USD rate = 82.50 for everyone, always
- **Problem**: If USD was 80.00 in FY 2023 and 85.00 in FY 2024, system used the same rate for both years
- **Result**: Incorrect currency conversions in financial statements

### Example of the Problem:
```
Entity A - FY 2023:
- Transaction: ₹10,00,000 (INR)
- USD Rate Used: 82.50 (wrong - should be 80.00)
- Converted: $12,121 (incorrect)

Entity A - FY 2024:
- Transaction: ₹10,00,000 (INR)
- USD Rate Used: 82.50 (wrong - should be 85.00)
- Converted: $12,121 (incorrect - should be $11,765)
```

---

## The Solution Now (FY-Specific Rates)

### New Way:
- **Different rates per entity, per financial year**
- Example:
  - Entity A, FY 2023: USD opening = 80.00, closing = 82.00
  - Entity A, FY 2024: USD opening = 82.00, closing = 85.00
  - Entity B, FY 2023: USD opening = 79.50, closing = 81.50 (different entity, different rates!)

### How It Works:

#### 1. **Opening Rate** (FY Start)
- Exchange rate at the **beginning** of the financial year
- Used for: Balance Sheet items (assets, liabilities at year start)

#### 2. **Closing Rate** (FY End)
- Exchange rate at the **end** of the financial year (max 12 months from start)
- Used for: Balance Sheet items (assets, liabilities at year end)

#### 3. **Average Rate** (for P&L)
- Average of opening + closing rates
- Used for: Profit & Loss items (revenue, expenses throughout the year)

---

## How It Changes Structured Data

### Before (Legacy):
```sql
-- All entities, all years use same rate
SELECT 
  entityCode,
  Year,
  transactionAmount,
  localCurrencyCode,
  Avg_Fx_Rt,  -- Always 82.50 (from forex_master)
  transactionAmountUSD
FROM final_structured
WHERE entityCode = 'ENT001' AND Year = 2023
```

**Result:**
```
Entity: ENT001, Year: 2023
Transaction: ₹10,00,000 (INR)
Avg_Fx_Rt: 82.50 (same for everyone)
USD Amount: $12,121
```

### After (FY-Specific):
```sql
-- System looks up entity_forex_rates first
SELECT 
  entityCode,
  Year,
  transactionAmount,
  localCurrencyCode,
  Avg_Fx_Rt,  -- From entity_forex_rates: 80.00 (opening) or 81.00 (avg) or 82.00 (closing)
  transactionAmountUSD
FROM final_structured
WHERE entityCode = 'ENT001' AND Year = 2023
```

**Result:**
```
Entity: ENT001, Year: 2023
Transaction: ₹10,00,000 (INR)
- If Balance Sheet: Avg_Fx_Rt = 82.00 (closing rate for FY 2023)
- If P&L: Avg_Fx_Rt = 81.00 (average of 80.00 + 82.00)
USD Amount: $12,195 (Balance Sheet) or $12,346 (P&L)
```

---

## Real-World Example

### Scenario:
- **Entity A** (India) has transactions in INR
- **FY 2023**: USD/INR was 80.00 (start) → 82.00 (end)
- **FY 2024**: USD/INR was 82.00 (start) → 85.00 (end)

### Transaction:
- **Asset Purchase** (Balance Sheet): ₹10,00,000 in FY 2023
- **Revenue** (P&L): ₹5,00,000 in FY 2023

### Calculation:

#### FY 2023 - Balance Sheet Item:
```
Opening Rate: 80.00
Closing Rate: 82.00
Used Rate: 82.00 (closing rate for Balance Sheet)
USD Amount: ₹10,00,000 / 82.00 = $12,195.12
```

#### FY 2023 - P&L Item:
```
Opening Rate: 80.00
Closing Rate: 82.00
Average Rate: (80.00 + 82.00) / 2 = 81.00
USD Amount: ₹5,00,000 / 81.00 = $6,172.84
```

#### FY 2024 - Same Transaction:
```
Opening Rate: 82.00
Closing Rate: 85.00
Used Rate: 85.00 (for Balance Sheet) or 83.50 (for P&L)
USD Amount: Different from FY 2023!
```

---

## Where You See the Change

### 1. **Structured Data Page** (`/structured-data`)
- When you view financial data, `Avg_Fx_Rt` column now shows FY-specific rates
- `transactionAmountUSD` is calculated using correct rates per entity/FY

### 2. **Dashboard** (`/dashboard`)
- All USD totals are now accurate per financial year
- Year-over-year comparisons are correct

### 3. **Reports** (`/reports`)
- Cross-entity comparisons use correct rates
- Financial year filters show accurate conversions

### 4. **Excel Exports**
- Exported data includes correct `Avg_Fx_Rt` and `transactionAmountUSD`

---

## How to Verify It's Working

### Step 1: Check Structured Data
1. Go to `/structured-data`
2. Select an entity and financial year
3. Look at `Avg_Fx_Rt` column - should match rates you set in `/forex`

### Step 2: Compare Different Years
1. View same entity for FY 2023 and FY 2024
2. `Avg_Fx_Rt` should be different if you set different rates
3. `transactionAmountUSD` should reflect the difference

### Step 3: Check Balance Sheet vs P&L
1. Find a Balance Sheet item (e.g., "Assets")
2. Find a P&L item (e.g., "Revenue")
3. Balance Sheet should use closing rate
4. P&L should use average rate

---

## Benefits Summary

✅ **Accuracy**: Each entity and financial year uses correct exchange rates  
✅ **Compliance**: Meets accounting standards (IAS 21, IFRS)  
✅ **Audit Trail**: Historical rates preserved per FY  
✅ **Multi-Entity**: Different entities can have different rates  
✅ **Multi-Year**: Same entity can have different rates per year  
✅ **Correct Reporting**: Financial statements show accurate USD conversions  

---

## Technical Flow

```
1. User uploads data → final_structured table
   ↓
2. System checks: entityCode, Year, localCurrencyCode
   ↓
3. Looks up entity_forex_rates table:
   - entity_id = X
   - currency = "USD"
   - financial_year = 2023
   ↓
4. Gets: opening_rate = 80.00, closing_rate = 82.00
   ↓
5. Determines item type:
   - Balance Sheet → uses closing_rate (82.00)
   - P&L → uses average (81.00)
   ↓
6. Calculates:
   - Avg_Fx_Rt = selected rate
   - transactionAmountUSD = transactionAmount × Avg_Fx_Rt
   ↓
7. Saves to final_structured table
```

---

## Still Confused?

**Think of it like this:**
- **Before**: Everyone uses the same exchange rate, regardless of when the transaction happened
- **After**: Each company, each year, gets its own exchange rate - just like in real life!

**Example:**
- If you bought something in 2023 when USD = ₹80, it should be converted at ₹80
- If you bought something in 2024 when USD = ₹85, it should be converted at ₹85
- The old system would use the same rate for both - **wrong!**
- The new system uses the correct rate for each year - **correct!**





