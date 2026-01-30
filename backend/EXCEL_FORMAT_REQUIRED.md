# Excel File Format for Upload

## ❌ PROBLEM: Your Current Excel Format

Your Excel file currently has **ONLY NUMBERS** without Dr/Cr indicators:

| Particular | Opening | Transaction | Closing |
|------------|---------|-------------|---------|
| Cash       | 322.18  | 322.00      | 0.18    |
| Bank       | 1365.00 | 102901.37   | -101536.37 |

**Result**: Everything defaults to Dr (positive) because there's no way to know if it's Cr!

## ✅ SOLUTION: Add Dr/Cr to Your Excel

You have **TWO OPTIONS**:

### Option 1: Add Dr/Cr Text to Amount Columns (RECOMMENDED)

| Particular | Opening    | Transaction  | Closing     |
|------------|------------|--------------|-------------|
| Cash       | 322.18 Dr  | 322.00 Cr    | 0.18 Dr     |
| Bank       | 1365.00 Dr | 102901.37 Cr | 101536.37 Cr|

**Format**: `<number> Dr` or `<number> Cr`

### Option 2: Add a Separate "Type" Column

| Particular | Opening  | Transaction | Closing     | Type |
|------------|----------|-------------|-------------|------|
| Cash       | 322.18   | 322.00      | 0.18        | Dr   |
| Bank       | 1365.00  | 102901.37   | 101536.37   | Cr   |

**Column names supported**: `Type`, `Dr/Cr`, or `DrCr`

## 📋 Complete Example (Option 1 - Recommended)

```
Particular                    | Opening      | Transaction   | Closing
------------------------------|--------------|---------------|-------------
Cash                          | 1365.00 Dr   | 322.00 Cr     | 1043.00 Dr
Bank - Current Account        | 5000.00 Cr   | 2000.00 Dr    | 3000.00 Cr
Consultancy Fees - Hafeez     |              | 3485.36 Dr    | 3485.36 Dr
Consultancy Fees - Sadiq      |              | 14775.42 Dr   | 14775.42 Dr
Dubai Islamic Bank AED A/c    | 2784.84 Dr   | 10379.67 Dr   | 13164.51 Dr
Dubai Islamic Bank USD        | 217686.33 Dr | 102901.37 Cr  | 114784.96 Dr
```

## 🔍 How It Works

### With Dr/Cr Indicators:
- `1365.00 Dr` → Saved as `+1365.00` in database ✅
- `322.00 Cr` → Saved as `-322.00` in database ✅
- `102901.37 Cr` → Saved as `-102901.37` in database ✅

### Without Dr/Cr (Your Current File):
- `1365.00` → Defaults to Dr → Saved as `+1365.00` ❌ (might be wrong!)
- `322.00` → Defaults to Dr → Saved as `+322.00` ❌ (should be Cr!)
- `102901.37` → Defaults to Dr → Saved as `+102901.37` ❌ (should be Cr!)

## 🚀 What to Do Now

### Step 1: Update Your Excel File
Add "Dr" or "Cr" text after each number in the Opening and Transaction columns.

**Example**:
- Change `322.00` to `322.00 Cr`
- Change `1365.00` to `1365.00 Dr`

### Step 2: Re-upload the File
1. Go to Upload page
2. Select your updated Excel file
3. Choose Entity, Month, and Financial Year
4. Click "Upload & Process File"

### Step 3: Verify in Console
You should now see in the backend console:
```
🔍 Calculating Amt_TB_lc for Dr: 1365.00
✅ Inserted Opening record for: Cash (Amount: 1365.00)
🔍 Calculating Amt_TB_lc for Cr: -322.00
✅ Inserted Transaction record for: Cash (Amount: -322.00)
```

Notice the **negative sign** for Cr entries!

### Step 4: Check Structured Data Page
- Cr entries will show: `₹-3,22.00`
- Dr entries will show: `₹1,365.00`

## 📝 Notes

1. **Closing column** is optional - it's not saved to database
2. **Dr/Cr is case-insensitive**: `Dr`, `dr`, `DR` all work
3. **Spacing doesn't matter**: `322.00Dr` and `322.00 Dr` both work
4. **Type column** (Option 2) applies the same type to both Opening and Transaction

## ❓ FAQ

**Q: Can I use just numbers without Dr/Cr?**
A: No, the system needs to know if each value is Debit or Credit. Without indicators, everything defaults to Dr.

**Q: What if I have mixed formats?**
A: The system will try to detect Dr/Cr from:
1. The amount cell itself (e.g., "322.00 Cr")
2. The Type column (if present)
3. The Closing column (as fallback)
4. Default to Dr if none found

**Q: Do I need Dr/Cr in the Closing column?**
A: No, Closing is not processed. But if Opening/Transaction are plain numbers, the system will try to use Closing's Dr/Cr as a hint.

