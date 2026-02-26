# Testing Monthly Forex Rates - Step-by-Step Guide

## Overview

This guide walks you through testing the monthly forex rate feature using your trial balance sheet data across multiple months.

---

## Prerequisites

✅ Database migration completed (002_monthly_forex_rates.sql)  
✅ Backend server running  
✅ Frontend running  
✅ One month's trial balance sheet data ready  

---

## Step 1: Set Up Entity and Financial Year

### 1.1 Create/Select Entity

1. Go to **Entities** page
2. Create a new entity or select an existing one
3. Note down:
   - **Entity ID**: (e.g., 1)
   - **Entity Code**: (e.g., "COMP001")
   - **Local Currency**: (e.g., "USD")
   - **Financial Year Start**: (e.g., April 1st)

### 1.2 Example Entity Setup

**Entity Details:**
- Entity Code: `TEST001`
- Entity Name: `Test Company`
- Local Currency: `USD`
- Financial Year Start: April 1st

---

## Step 2: Set Up Forex Rates for Multiple Months

### 2.1 Open Forex Rates Page

1. Go to **Forex Rates** page (`/forex`)
2. Select your entity: `TEST001`
3. Select Financial Year: `2024` (or your target FY)

### 2.2 Set Opening Rate (FY Start - April)

1. Click **"Add Forex Rate"** or edit existing
2. Enter:
   - **Currency**: `USD`
   - **Opening Rate**: `80.00` (rate at FY start - April)
   - **Closing Rate**: `80.00` (same as opening for now)
   - **Month Number**: `1`
   - **Month Name**: `April`
3. Click **Save**

**Result**: 
- Opening rate set: 80.00 ✅
- Monthly rate for April saved: 80.00 ✅

### 2.3 Update Closing Rate for May

1. **Keep the same entity and FY selected**
2. Edit the forex rate
3. Update:
   - **Opening Rate**: `80.00` (stays fixed)
   - **Closing Rate**: `81.00` (May's rate)
   - **Month Number**: `2`
   - **Month Name**: `May`
4. Click **Save**

**Result**: 
- Closing rate updated: 81.00 ✅
- Monthly rate for May saved: 81.00 ✅
- April's rate still stored: 80.00 ✅

### 2.4 Continue for June, July, etc.

Repeat for each month you want to test:

**June:**
- Closing Rate: `81.50`
- Month Number: `3`
- Month Name: `June`

**July:**
- Closing Rate: `82.00`
- Month Number: `4`
- Month Name: `July`

**August:**
- Closing Rate: `82.50`
- Month Number: `5`
- Month Name: `August`

**Example Timeline:**

| Month | Closing Rate | Month Number | Monthly Rate Saved |
|-------|-------------|--------------|-------------------|
| April | 80.00 | 1 | 80.00 ✅ |
| May | 81.00 | 2 | 81.00 ✅ |
| June | 81.50 | 3 | 81.50 ✅ |
| July | 82.00 | 4 | 82.00 ✅ |
| August | 82.50 | 5 | 82.50 ✅ |

---

## Step 3: Upload Trial Balance Data for Multiple Months

### 3.1 Prepare Your Excel Files

You have one month's data. You'll upload it multiple times, changing only the **Month** column.

**Option A: Create Separate Excel Files**

Create files:
- `trial_balance_april.xlsx` - Month column = "April"
- `trial_balance_may.xlsx` - Month column = "May"
- `trial_balance_june.xlsx` - Month column = "June"
- etc.

**Option B: Modify One File Multiple Times**

Use the same Excel file but change the **Month** column value before each upload.

### 3.2 Upload April Data

1. Go to **Upload** page
2. Select Entity: `TEST001`
3. Select Month: `April`
4. Select Year: `2024` (or your FY)
5. Upload `trial_balance_april.xlsx`
6. Verify upload success

**Expected Result:**
- Data uploaded for April ✅
- System will use April's forex rate (80.00) for calculations

### 3.3 Upload May Data

1. **Same Upload page**
2. Select Entity: `TEST001`
3. Select Month: `May`
4. Select Year: `2024`
5. Upload `trial_balance_may.xlsx` (or same file with Month="May")
6. Verify upload success

**Expected Result:**
- Data uploaded for May ✅
- System will use May's forex rate (81.00) for calculations

### 3.4 Upload Remaining Months

Repeat for June, July, August, etc., changing only the **Month** selection.

---

## Step 4: Verify Monthly Rates Are Applied Correctly

### 4.1 View Structured Data

1. Go to **Structured Data** page
2. Filter by:
   - Entity: `TEST001`
   - Financial Year: `2024`
   - **Month**: `April`

### 4.2 Check Forex Rate Used

For April data, you should see:
- **Avg_Fx_Rt**: `80.00` (April's rate) ✅
- **transactionAmountUSD**: `transactionAmount × 80.00`

### 4.3 Check May Data

1. Change filter: **Month**: `May`
2. For May data, you should see:
   - **Avg_Fx_Rt**: `81.00` (May's rate) ✅
   - **transactionAmountUSD**: `transactionAmount × 81.00`

### 4.4 Check June Data

1. Change filter: **Month**: `June`
2. For June data, you should see:
   - **Avg_Fx_Rt**: `81.50` (June's rate) ✅
   - **transactionAmountUSD**: `transactionAmount × 81.50`

### 4.5 Verify Historical Accuracy

**Key Test**: Even if you update closing_rate later, previous month's data should still use their original rates!

1. Go back to Forex Rates page
2. Update closing_rate for August to `83.00` (Month 6)
3. Go back to Structured Data
4. Filter by **April**
5. **April's data should still show**: Avg_Fx_Rt = 80.00 ✅

---

## Step 5: Detailed Verification Checklist

### ✅ Test 1: Monthly Rates Stored

1. Go to Forex Rates page
2. Select entity and FY
3. Check that rates are displayed
4. **Verify**: Can see opening_rate and closing_rate

**API Test:**
```bash
GET /api/forex/entity/1/financial-year/2024/monthly?currency=USD
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "entity_id": 1,
    "currency": "USD",
    "financial_year": 2024,
    "monthly_rates": [
      {"month_number": 1, "month_name": "April", "rate": 80.00},
      {"month_number": 2, "month_name": "May", "rate": 81.00},
      {"month_number": 3, "month_name": "June", "rate": 81.50}
    ]
  }
}
```

### ✅ Test 2: April Data Uses April Rate

1. Upload data for April
2. View Structured Data filtered by April
3. **Verify**: Avg_Fx_Rt = 80.00 for all rows
4. **Verify**: transactionAmountUSD = transactionAmount × 80.00

### ✅ Test 3: May Data Uses May Rate

1. Upload data for May
2. View Structured Data filtered by May
3. **Verify**: Avg_Fx_Rt = 81.00 for all rows
4. **Verify**: transactionAmountUSD = transactionAmount × 81.00

### ✅ Test 4: Historical Data Preserved

1. Update closing_rate to 85.00 (September)
2. View April data again
3. **Verify**: April still shows 80.00 (not 85.00) ✅

### ✅ Test 5: Balance Sheet vs P&L Items

**Balance Sheet Items:**
- Should use monthly rate directly (e.g., 80.00 for April)

**P&L Items:**
- Should use monthly rate directly (e.g., 80.00 for April)

**Note**: For monthly rates, both BS and P&L use the monthly rate (not average)

---

## Step 6: Testing with API (Optional)

### 6.1 Set Forex Rate via API

```bash
POST /api/forex/entity/1/financial-year/2024
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "currency": "USD",
  "opening_rate": 80.00,
  "closing_rate": 81.00,
  "month_number": 2,
  "month_name": "May",
  "save_monthly_rate": true
}
```

### 6.2 Get Monthly Rates

```bash
GET /api/forex/entity/1/financial-year/2024/monthly?currency=USD
```

### 6.3 Get Structured Data with Month Filter

```bash
GET /api/structure/data?entity_id=1&financial_year=2024&month=May
```

**Expected**: All rows should have Avg_Fx_Rt = 81.00

---

## Step 7: Troubleshooting

### Issue: Monthly rates not being saved

**Solution:**
- Check that `month_number` and `month_name` are provided when updating closing_rate
- Check backend logs for errors

### Issue: Wrong rate used for month data

**Solution:**
- Verify month name matches exactly (case-insensitive but spelling must match)
- Check that monthly rate exists in database:
  ```sql
  SELECT * FROM entity_forex_monthly_rates 
  WHERE entity_id = 1 AND currency = 'USD' AND financial_year = 2024;
  ```

### Issue: Previous month data shows wrong rate

**Solution:**
- Verify monthly rate was saved when you updated closing_rate
- Check that month filter is correctly applied when viewing data
- Check backend logs to see which rate is being used

---

## Quick Test Summary

1. ✅ **Set up entity** with FY start month
2. ✅ **Set opening rate** for April (month 1)
3. ✅ **Update closing rate** for each month (May, June, July...)
4. ✅ **Upload trial balance** for each month
5. ✅ **Verify** each month's data uses that month's rate
6. ✅ **Verify** historical data remains accurate after updating later months

---

## Expected Behavior Summary

| Month | Closing Rate Set | Monthly Rate Saved | Viewing Data Shows |
|-------|-----------------|-------------------|-------------------|
| April | 80.00 | 80.00 | Avg_Fx_Rt = 80.00 ✅ |
| May | 81.00 | 81.00 | Avg_Fx_Rt = 81.00 ✅ |
| June | 81.50 | 81.50 | Avg_Fx_Rt = 81.50 ✅ |
| July | 82.00 | 82.00 | Avg_Fx_Rt = 82.00 ✅ |
| August | 82.50 | 82.50 | Avg_Fx_Rt = 82.50 ✅ |

**Key Point**: Each month's data uses its own stored rate, ensuring historical accuracy! 🎯





