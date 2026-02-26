# Monthly Forex Rates Implementation

## Overview

The system now stores **monthly forex rates** to preserve historical accuracy when viewing previous month data. This ensures that when you view April's data, it uses April's rate (not the current closing rate).

---

## How It Works

### 1. Monthly Rate Storage

When you update the **closing rate** via the `/forex` page, the system can automatically save it as a **monthly rate** for that specific month.

**Table**: `entity_forex_monthly_rates`
- Stores one rate per month per entity/currency/financial year
- Rate is saved when you update closing_rate with month information

### 2. Using Monthly Rates

When viewing structured data:

1. **System checks for monthly rate first** (if month is available in the data)
   - Uses the monthly rate for that specific month
   - Ensures historical accuracy

2. **Falls back to FY-level rates** (opening/closing)
   - If no monthly rate exists, uses opening/closing rates as before

3. **Applies rate based on item type**:
   - **Balance Sheet items**: Use monthly rate (if available) or closing rate
   - **P&L items**: Use monthly rate (if available) or average of opening/closing

---

## Database Schema

### Table: `entity_forex_monthly_rates`

```sql
CREATE TABLE entity_forex_monthly_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_year INT NOT NULL,
    month_number INT NOT NULL,  -- 1-12 (April=1 if FY starts in April)
    month_name VARCHAR(20) NOT NULL,  -- "April", "May", etc.
    rate DECIMAL(18,6) NOT NULL,
    effective_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id),
    UNIQUE KEY uk_entity_currency_fy_month (entity_id, currency, financial_year, month_number)
);
```

---

## API Endpoints

### 1. Get Monthly Rates

**GET** `/api/forex/entity/<entity_id>/financial-year/<financial_year>/monthly?currency=USD`

Returns monthly rates for a specific entity, financial year, and currency.

**Example Response:**
```json
{
  "success": true,
  "data": {
    "entity_id": 1,
    "currency": "USD",
    "financial_year": 2024,
    "monthly_rates": [
      {
        "month_number": 1,
        "month_name": "April",
        "rate": 82.50,
        "effective_date": "2023-04-01",
        "created_at": "2023-04-01T10:00:00"
      },
      {
        "month_number": 2,
        "month_name": "May",
        "rate": 82.75,
        "effective_date": "2023-05-01",
        "created_at": "2023-05-01T10:00:00"
      }
    ]
  }
}
```

### 2. Update Closing Rate (with Monthly Rate Auto-Save)

**POST/PUT** `/api/forex/entity/<entity_id>/financial-year/<financial_year>`

**Request Body:**
```json
{
  "currency": "USD",
  "opening_rate": 82.00,
  "closing_rate": 82.75,
  "month_number": 2,        // Optional: 1-12
  "month_name": "May",      // Optional: "May", "June", etc.
  "save_monthly_rate": true // Optional: Default true
}
```

If `month_number` and `month_name` are provided, the system automatically saves the `closing_rate` as a monthly rate for that month.

---

## Usage Workflow

### Monthly Update Process

1. **Each month when uploading trial balance:**
   - Go to `/forex` page
   - Select: Entity, Financial Year
   - Enter current month's rate as `closing_rate`
   - Optionally provide `month_number` and `month_name`
   - System saves both:
     - Updates `closing_rate` in `entity_forex_rates`
     - Saves monthly rate in `entity_forex_monthly_rates`

2. **When viewing data:**
   - System automatically uses the monthly rate for that month's data
   - Ensures historical accuracy

---

## Example Timeline

**FY 2024 (April 2023 - March 2024):**

| Month | Action | Closing Rate Updated | Monthly Rate Saved | Viewing April Data Shows |
|-------|--------|---------------------|-------------------|-------------------------|
| April 2023 | Initial setup | 82.00 | 82.00 (April) | 82.00 ✅ |
| May 2023 | Update closing | 82.50 | 82.50 (May) | 82.00 ✅ (still accurate) |
| June 2023 | Update closing | 82.75 | 82.75 (June) | 82.00 ✅ (still accurate) |
| ... | ... | ... | ... | ... |
| March 2024 | Final update | 85.00 | 85.00 (March) | 82.00 ✅ (still accurate) |

**Key Point**: Each month's data uses its own rate, even if closing_rate changes later.

---

## Benefits

✅ **Historical Accuracy**: Previous month data always uses that month's rate  
✅ **Automatic Tracking**: Monthly rates saved automatically when updating closing_rate  
✅ **Backward Compatible**: Falls back to opening/closing rates if monthly rate not available  
✅ **No Breaking Changes**: Existing data continues to work  

---

## Migration

Run the migration script to create the table:

```bash
mysql -u your_user -p balance_sheet < backend/migrations/002_monthly_forex_rates.sql
```

---

## Notes

- Monthly rates are **optional** - if not provided, system uses opening/closing rates as before
- Monthly rates are saved automatically when `month_number` and `month_name` are provided
- Month numbers are 1-12 based on financial year (e.g., if FY starts in April, April = 1, May = 2, etc.)
- The system maps month names (case-insensitive) to numbers automatically





