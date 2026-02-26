# Financial Year Based Forex Rates - Implementation Guide

## Overview

This feature implements **Phase 2 Requirement 1**: Financial Year Based Forex Rates. Each entity can now have independent forex rates for each financial year, with opening rates at the start of the financial year and closing rates at the end (maximum 12 months from start).

## Database Changes

### 1. Entity Master Enhancement
- Added `financial_year_start_month` (INT, default: 4 for April)
- Added `financial_year_start_day` (INT, default: 1)

### 2. New Table: `entity_forex_rates`
```sql
CREATE TABLE entity_forex_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_year INT NOT NULL,
    opening_rate DECIMAL(18,6) NOT NULL,
    closing_rate DECIMAL(18,6) NOT NULL,
    fy_start_date DATE NOT NULL,
    fy_end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NULL,
    UNIQUE KEY uk_entity_currency_fy (entity_id, currency, financial_year)
);
```

## API Endpoints

### 1. Get Entity FY Forex Rates
```
GET /forex/entity/<entity_id>/financial-year/<financial_year>?currency=<currency>
```
**Response:**
```json
{
  "success": true,
  "data": {
    "entity_id": 1,
    "financial_year": 2024,
    "rates": [
      {
        "id": 1,
        "entity_id": 1,
        "currency": "USD",
        "financial_year": 2024,
        "opening_rate": 82.50,
        "closing_rate": 83.20,
        "fy_start_date": "2023-04-01",
        "fy_end_date": "2024-03-31"
      }
    ]
  }
}
```

### 2. Set Entity FY Forex Rates
```
POST /forex/entity/<entity_id>/financial-year/<financial_year>
PUT /forex/entity/<entity_id>/financial-year/<financial_year>
```
**Body:**
```json
{
  "currency": "USD",
  "opening_rate": 82.50,
  "closing_rate": 83.20
}
```

### 3. Get Financial Years for Entity
```
GET /forex/entity/<entity_id>/financial-years
```
**Response:**
```json
{
  "success": true,
  "data": {
    "entity_id": 1,
    "financial_years": [2024, 2023, 2022]
  }
}
```

## Financial Year Calculation

The system automatically calculates FY start and end dates based on:
- Entity's `financial_year_start_month` (default: 4 = April)
- Entity's `financial_year_start_day` (default: 1)

**Example:**
- Financial Year: 2024
- FY Start Month: 4 (April)
- FY Start Day: 1
- **FY Start Date**: 2023-04-01
- **FY End Date**: 2024-03-31 (12 months from start - 1 day)

## Usage in Code

### Get FY-Specific Rate for Entity
```python
from routes.forex import get_entity_fy_forex_rate

# Get rates for entity 1, USD currency, FY 2024
rates = get_entity_fy_forex_rate(entity_id=1, currency="USD", financial_year=2024)
if rates:
    opening_rate = rates['opening_rate']
    closing_rate = rates['closing_rate']
    # Use opening_rate for Balance Sheet items
    # Use average of opening_rate and closing_rate for P&L items
```

### Calculate Average Rate for P&L
```python
if rates:
    avg_rate_pl = (rates['opening_rate'] + rates['closing_rate']) / 2.0
```

## Migration

Run the migration script to:
1. Add new columns to `entity_master`
2. Create `entity_forex_rates` table
3. Migrate existing forex rates to latest financial year

```bash
mysql -u <user> -p balance_sheet < backend/migrations/001_fy_forex_rates.sql
```

## Next Steps

1. ✅ Database schema created
2. ✅ Backend API endpoints implemented
3. ⏳ Update forex calculation logic in `structure_data.py` to use FY-specific rates
4. ⏳ Create frontend UI for managing FY-specific rates
5. ⏳ Update existing reports to use FY-specific rates

## Notes

- The old `forex_master` table is still maintained for backward compatibility
- New code should prefer `entity_forex_rates` for entity-specific, FY-specific rates
- If FY-specific rate is not found, system can fall back to `forex_master` rates
- Each entity can have different financial year start dates (e.g., April 1, January 1, etc.)





