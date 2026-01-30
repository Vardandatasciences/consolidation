# Excel File Format - Simple Sign-Based Approach

## ✅ SIMPLE FORMAT: Use Positive/Negative Numbers

Just enter your numbers with their signs directly in Excel:

| Particular | Opening   | Transaction | Closing    |
|------------|-----------|-------------|------------|
| Cash       | 322.18    | -322.00     | 0.18       |
| Bank       | 1365.00   | -102901.37  | -101536.37 |
| Revenue    | -400000.00| 400000.00   | 0.00       |

## 🔍 How It Works

### Sign-Based Logic:
- **Positive number** (`1365.00`) → Saved as **positive** in database → Debit
- **Negative number** (`-322.00`) → Saved as **negative** in database → Credit

**That's it! No need for "Dr" or "Cr" text.**

## 📊 Complete Example

```
Particular                    | Opening      | Transaction   | Closing
------------------------------|--------------|---------------|-------------
Cash                          | 1365.00      | -322.00       | 1043.00
Bank - Current Account        | -5000.00     | 2000.00       | -3000.00
Consultancy Fees - Hafeez     | 0            | 3485.36       | 3485.36
Consultancy Fees - Sadiq      | 0            | 14775.42      | 14775.42
Dubai Islamic Bank AED A/c    | 2784.84      | 10379.67      | 13164.51
Dubai Islamic Bank USD        | 217686.33    | -102901.37    | 114784.96
Revenue                       | -400000.00   | 400000.00     | 0.00
Expenses                      | 50000.00     | -25000.00     | 25000.00
```

## 💾 Database Storage

The values are stored **exactly as entered**:

| Excel Value | Database Value | Type   |
|-------------|----------------|--------|
| 1365.00     | +1365.00       | Debit  |
| -322.00     | -322.00        | Credit |
| -102901.37  | -102901.37     | Credit |
| 400000.00   | +400000.00     | Debit  |
| -400000.00  | -400000.00     | Credit |

## 🎯 Key Points

1. ✅ **Positive numbers** = Debit (stored as positive)
2. ✅ **Negative numbers** = Credit (stored as negative)
3. ✅ **No Dr/Cr text needed** (but still supported for backward compatibility)
4. ✅ **Commas are handled**: `-1,02,901.37` works fine
5. ✅ **Decimals supported**: `-322.18`, `1365.00`, etc.

## 🔄 Backward Compatibility

If your Excel still has "Dr" or "Cr" text, it will still work:
- `1365.00 Dr` → Saved as `+1365.00`
- `322.00 Cr` → Saved as `-322.00`

But you don't need them anymore!

## 🚀 What to Do Now

### Step 1: Update Your Excel File
Simply enter numbers with their signs:
- Credits (losses, liabilities): Use negative sign (`-322.00`)
- Debits (assets, income): Use positive number (`1365.00`)

### Step 2: Upload the File
1. Go to Upload page
2. Select your Excel file
3. Choose Entity, Month, and Financial Year
4. Click "Upload & Process File"

### Step 3: Verify in Console
Backend console will show:
```
🔍 Calculating Amt_TB_lc for Dr: 1365.00
✅ Inserted Opening record for: Cash (Amount: 1365.00)
🔍 Calculating Amt_TB_lc for Cr: -322.00
✅ Inserted Transaction record for: Cash (Amount: -322.00)
```

### Step 4: Check Structured Data Page
- Negative values will show: `₹-3,22.00`
- Positive values will show: `₹1,365.00`

## 📝 Notes

1. **Zero values** (`0` or `0.00`) are treated as Debit (positive)
2. **Closing column** is optional - not saved to database
3. **Sign is preserved** - if you enter `-322.00`, it's saved as `-322.00`
4. **No conversion needed** - the sign you enter is the sign that's stored

## ✅ Summary

**OLD WAY (Still works):**
```
Cash | 322.00 Cr | 1365.00 Dr
```

**NEW WAY (Simpler):**
```
Cash | -322.00 | 1365.00
```

Both produce the same result in the database!

