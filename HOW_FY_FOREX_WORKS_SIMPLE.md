# How FY-Specific Forex Rates Work - Simple Explanation

## 🎯 The Main Idea

**Before**: One exchange rate for everyone, all the time  
**After**: Each company gets its own exchange rate for each financial year

---

## 📊 Visual Example

### Scenario:
You have **Entity A** with transactions in **INR** (Indian Rupees)

### OLD SYSTEM (Wrong):
```
All Years, All Entities:
USD Rate = 82.50 (same for everyone)

FY 2023 Transaction: ₹10,00,000 → $12,121
FY 2024 Transaction: ₹10,00,000 → $12,121  ❌ Same rate!
```

### NEW SYSTEM (Correct):
```
Entity A, FY 2023:
Opening Rate: 80.00
Closing Rate: 82.00
→ Uses 82.00 for Balance Sheet
→ Uses 81.00 (average) for P&L

FY 2023 Transaction: ₹10,00,000 → $12,195 ✅

Entity A, FY 2024:
Opening Rate: 82.00
Closing Rate: 85.00
→ Uses 85.00 for Balance Sheet
→ Uses 83.50 (average) for P&L

FY 2024 Transaction: ₹10,00,000 → $11,765 ✅ Different!
```

---

## 🔍 Where You See the Change

### 1. In Structured Data Page

**Go to**: `/structured-data`

**What you'll see**:
```
| Particular        | Amount (INR) | Avg_Fx_Rt | Amount (USD) |
|-------------------|--------------|-----------|--------------|
| Assets            | 10,00,000    | 82.00     | 12,195       | ← Uses closing rate
| Revenue           | 5,00,000     | 81.00     | 6,173        | ← Uses average rate
```

**Before (Old System)**:
```
| Particular        | Amount (INR) | Avg_Fx_Rt | Amount (USD) |
|-------------------|--------------|-----------|--------------|
| Assets            | 10,00,000    | 82.50     | 12,121       | ← Same for all
| Revenue           | 5,00,000     | 82.50     | 6,061        | ← Same for all
```

### 2. How It's Calculated

When you view structured data:

1. **System looks at each row**:
   - Entity: Entity A
   - Year: 2023
   - Currency: INR
   - Category: Balance Sheet or P&L

2. **System checks forex rates**:
   ```
   SELECT opening_rate, closing_rate 
   FROM entity_forex_rates
   WHERE entity_id = 1 
     AND currency = 'USD' 
     AND financial_year = 2023
   ```

3. **System applies correct rate**:
   - **Balance Sheet item** → Uses `closing_rate` (82.00)
   - **P&L item** → Uses `(opening_rate + closing_rate) / 2` (81.00)

4. **System calculates USD amount**:
   ```
   transactionAmountUSD = transactionAmount / Avg_Fx_Rt
   ```

---

## 🧪 Test It Yourself

### Step 1: Set Different Rates
1. Go to `/forex`
2. Select Entity A, FY 2023
3. Set: Opening = 80.00, Closing = 82.00
4. Select Entity A, FY 2024
5. Set: Opening = 82.00, Closing = 85.00

### Step 2: View Structured Data
1. Go to `/structured-data`
2. Select Entity A, FY 2023
3. Look at `Avg_Fx_Rt` column
4. You should see: 82.00 (for Balance Sheet) or 81.00 (for P&L)

### Step 3: Compare Years
1. Change to FY 2024
2. Look at `Avg_Fx_Rt` column again
3. You should see: 85.00 (for Balance Sheet) or 83.50 (for P&L)
4. **Different rates = Different USD amounts!**

---

## 💡 Why This Matters

### Real-World Example:

**Company in India**:
- FY 2023: Bought equipment for ₹10,00,000 when USD = ₹80
- FY 2024: Bought equipment for ₹10,00,000 when USD = ₹85

**Old System Says**:
- Both items = $12,121 (wrong - uses same rate)

**New System Says**:
- FY 2023 item = $12,195 (correct - uses 82.00)
- FY 2024 item = $11,765 (correct - uses 85.00)

**Result**: Your financial statements are now **accurate**! ✅

---

## 📈 Impact on Reports

### Dashboard Totals:
- **Before**: All years show same USD totals (wrong)
- **After**: Each year shows correct USD totals based on that year's rates

### Year-over-Year Comparison:
- **Before**: Can't compare accurately (rates are wrong)
- **After**: Accurate comparisons because each year uses correct rates

### Multi-Entity Reports:
- **Before**: All entities use same rate (wrong if they're in different countries)
- **After**: Each entity uses its own rates (correct!)

---

## 🔄 Automatic Calculation

**You don't need to do anything!**

When you:
1. Set rates in `/forex` page
2. View data in `/structured-data`

The system **automatically**:
- Finds the correct rate for that entity + year
- Applies it based on Balance Sheet vs P&L
- Calculates USD amounts
- Updates the display

**It happens in the background!** 🎉

---

## ❓ Common Questions

**Q: Do I need to recalculate existing data?**  
A: No! The system automatically uses new rates when you view data.

**Q: What if I don't set FY-specific rates?**  
A: System falls back to old rates (backward compatible).

**Q: Can different entities have different rates?**  
A: Yes! That's the whole point - each entity, each year, gets its own rates.

**Q: How do I know which rate was used?**  
A: Check the `Avg_Fx_Rt` column in structured data - it shows the exact rate used.

---

## 🎓 Summary

**Think of it like this:**

Imagine you're buying things in different years:
- 2023: $1 = ₹80
- 2024: $1 = ₹85

If you spent ₹10,000 in 2023, it's worth $125 (10,000/80)  
If you spent ₹10,000 in 2024, it's worth $118 (10,000/85)

**The old system would say both are worth the same** ❌  
**The new system says they're different** ✅

That's why FY-specific rates matter!




