# Monthly Forex Rate Update Workflow

## Current System Design

The system uses **Opening Rate** and **Closing Rate** per financial year:

- **Opening Rate**: Fixed at FY start (e.g., April 1 rate = 80.00)
- **Closing Rate**: Updated monthly as FY progresses (current month's rate)

---

## How Monthly Updates Work

### Monthly Workflow (Simple Approach)

**Every month when you upload trial balance:**

1. **Get current month's forex rate** (e.g., May rate = 81.50)
2. **Go to `/forex` page**
3. **Select**: Entity, Financial Year
4. **Update**: Closing Rate = Current month's rate (81.50)
5. **Upload**: Trial balance for May
6. **System uses**: Updated closing_rate (81.50) for all calculations

### Example Timeline:

**FY 2024 (April 2023 - March 2024):**

| Month | Action | Opening Rate | Closing Rate (Updated) | Used For Calculations |
|-------|--------|--------------|------------------------|----------------------|
| April 2023 | Set initial rates | 80.00 | 80.50 | Closing: 80.50, P&L Avg: 80.25 |
| May 2023 | Update closing | 80.00 (fixed) | 81.00 | Closing: 81.00, P&L Avg: 80.50 |
| June 2023 | Update closing | 80.00 (fixed) | 81.50 | Closing: 81.50, P&L Avg: 80.75 |
| ... | ... | ... | ... | ... |
| March 2024 | Final update | 80.00 (fixed) | 85.00 | Closing: 85.00, P&L Avg: 82.50 |

**Result**:
- Opening rate stays fixed (80.00) ✅
- Closing rate reflects current month (updated monthly) ✅
- Balance Sheet uses current closing rate ✅
- P&L uses average of opening + current closing ✅

---

## Implementation: Simple Monthly Update

**This is already supported!** You just need to:

1. **Update closing_rate monthly** via `/forex` page
2. **System automatically uses** updated closing_rate for calculations

**No code changes needed!**

---

## Optional: Monthly Rate History (If Needed)

If you want to **track monthly rate history** (see what rate was used in each month), I can add:

### New Table: `entity_forex_monthly_rates`
```sql
CREATE TABLE entity_forex_monthly_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_year INT NOT NULL,
    month_number INT NOT NULL,  -- 1-12
    month_name VARCHAR(20) NOT NULL,  -- "April", "May", etc.
    rate DECIMAL(18,6) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id),
    UNIQUE KEY uk_entity_currency_fy_month (entity_id, currency, financial_year, month_number)
);
```

**Benefits**:
- ✅ See historical monthly rates
- ✅ Track rate changes over time
- ✅ Audit trail of when rates changed
- ✅ Can analyze rate trends

**Would you like me to implement this?** Or is simple monthly update of closing_rate sufficient?

---

## Recommended Approach

### For Most Users: **Simple Monthly Update** ✅

**Workflow**:
1. Each month, update `closing_rate` in `/forex` page
2. Upload trial balance
3. System uses updated closing_rate

**Pros**:
- ✅ Simple - no additional tables
- ✅ Matches Phase 2 requirements
- ✅ Easy to use
- ✅ Already implemented!

**Cons**:
- ⚠️ Can't see historical monthly rates (only current closing)
- ⚠️ Previous months' closing rates are overwritten

---

## If You Need Monthly History

I can implement monthly rate tracking which would:
1. Auto-save monthly rates when you update closing_rate
2. Add API to view monthly rate history
3. Add UI to see rate trends
4. Keep calculations using opening/closing (simple logic)

**Should I implement monthly rate history, or is simple monthly update enough?**

---

## Current Behavior (What You Have Now)

✅ **Opening Rate**: Set once at FY start, stays fixed  
✅ **Closing Rate**: Can be updated monthly via `/forex` page  
✅ **Calculations**: Use closing_rate (Balance Sheet) or average (P&L)  
✅ **Monthly Updates**: Just update closing_rate before/after uploading trial balance  

**This works for monthly updates!** You just update the closing_rate each month. 🎉





