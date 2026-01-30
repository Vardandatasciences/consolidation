# Financial Year Format Update: "2024-25" Format

## Overview
Updated the system to store financial years in the format **"2024-25"** (ending year format) instead of just the ending year integer (2024).

## Changes Made

### 1. Database Schema Updates

**Migration File**: `backend/migrations/003_financial_year_format.sql`

- Added `financial_year VARCHAR(10)` column to `final_structured` table
- Added `financial_year VARCHAR(10)` column to `rawData` table  
- Updated `entity_forex_rates.financial_year` to `VARCHAR(10)` to support "2024-25" format
- Created indexes for better query performance

### 2. Helper Functions Added

**In `backend/routes/upload_data.py` and `backend/routes/forex.py`:**

```python
def format_financial_year(ending_year: int) -> str:
    """
    Format financial year as "2024-25" from ending year.
    - ending_year = 2024 → returns "2024-25"
    - ending_year = 2025 → returns "2025-26"
    """
    if ending_year is None:
        return None
    next_year = ending_year + 1
    return f"{ending_year}-{str(next_year)[-2:]}"


def parse_financial_year(fy_string: str) -> int:
    """
    Parse financial year string "2024-25" to ending year integer (2024).
    Also handles integer input for backward compatibility.
    """
    if fy_string is None:
        return None
    if isinstance(fy_string, int):
        return fy_string
    # Try to parse "2024-25" format
    if '-' in str(fy_string):
        parts = str(fy_string).split('-')
        if len(parts) == 2:
            try:
                return int(parts[0])
            except ValueError:
                pass
    # Try to parse as integer
    try:
        return int(fy_string)
    except ValueError:
        return None
```

### 3. Code Updates

#### `backend/routes/upload_data.py`
- **`insert_raw_data()`**: Now saves `financial_year` in "2024-25" format to `rawData` table
- **`insert_structured_data()`**: Now saves `financial_year` in "2024-25" format to `final_structured` table
- **Duplicate checks**: Updated to check both `Year` (int) and `financial_year` (string) for backward compatibility

#### `backend/routes/forex.py`
- **`set_entity_fy_forex()`**: Now saves `financial_year` in "2024-25" format to `entity_forex_rates` table
- **`get_entity_fy_forex()`**: Updated to check both formats for backward compatibility
- **`get_entity_fy_forex_rate()`**: Updated to handle both "2024-25" format and integer format
- **`get_entity_financial_years()`**: Updated ORDER BY to handle both formats

#### `backend/routes/structure_data.py`
- **`_build_forex_cache()`**: Updated to parse `financial_year` column (new format) or fallback to `Year` column
- **`_apply_forex_rates()`**: Updated to parse `financial_year` column (new format) or fallback to `Year` column
- **`_calculate_and_save_forex_rates()`**: Updated to parse `financial_year` column (new format) or fallback to `Year` column
- **`get_structured_data()`**: Updated query to include `financial_year` column and support filtering by both formats

### 4. Format Convention

**Financial Year Format**: "YYYY-YY" (ending year format)
- User selects **"2024"** → Stored as **"2024-25"** (FY 2023-2024)
- User selects **"2025"** → Stored as **"2025-26"** (FY 2024-2025)

**Examples**:
- Ending year 2024 → "2024-25"
- Ending year 2025 → "2025-26"
- Ending year 2023 → "2023-24"

### 5. Backward Compatibility

The system maintains backward compatibility:
- **Reading**: Checks both `financial_year` (new format) and `Year` (old format)
- **Writing**: Always writes in new format "2024-25"
- **Lookups**: Tries both formats when searching

### 6. Database Migration

**To apply the migration**, run:
```sql
-- Run the migration script
SOURCE backend/migrations/003_financial_year_format.sql;
```

Or manually execute:
```sql
-- Add financial_year column to final_structured
ALTER TABLE final_structured 
ADD COLUMN IF NOT EXISTS financial_year VARCHAR(10) NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Add financial_year column to rawData
ALTER TABLE `rawData` 
ADD COLUMN IF NOT EXISTS `financial_year` VARCHAR(10) NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Update entity_forex_rates.financial_year to VARCHAR
ALTER TABLE entity_forex_rates 
MODIFY COLUMN financial_year VARCHAR(10) NOT NULL COMMENT 'Financial year in format "2024-25" (ending year format)';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_final_structured_financial_year ON final_structured(financial_year);
CREATE INDEX IF NOT EXISTS idx_rawData_financial_year ON `rawData`(`financial_year`);
```

### 7. Data Migration (Optional)

To convert existing data to new format:
```sql
-- Update existing final_structured records
UPDATE final_structured 
SET financial_year = CONCAT(Year, '-', SUBSTRING(CAST(Year + 1 AS CHAR), -2))
WHERE financial_year IS NULL AND Year IS NOT NULL;

-- Update existing rawData records
UPDATE `rawData` 
SET `financial_year` = CONCAT(`Year`, '-', SUBSTRING(CAST(`Year` + 1 AS CHAR), -2))
WHERE `financial_year` IS NULL AND `Year` IS NOT NULL;

-- Update existing entity_forex_rates records
UPDATE entity_forex_rates 
SET financial_year = CONCAT(CAST(financial_year AS UNSIGNED), '-', SUBSTRING(CAST(CAST(financial_year AS UNSIGNED) + 1 AS CHAR), -2))
WHERE financial_year NOT LIKE '%-%';
```

## Testing

1. **Upload new data**: Verify `financial_year` is saved as "2024-25" format
2. **Check rawData**: Verify `financial_year` column has "2024-25" format
3. **Check final_structured**: Verify `financial_year` column has "2024-25" format
4. **Check entity_forex_rates**: Verify `financial_year` is stored as "2024-25" format
5. **Forex lookup**: Verify rates are found correctly using new format

## Notes

- The `Year` column is still maintained for backward compatibility
- All new data will use the "2024-25" format
- The system can read both formats (backward compatible)
- Forex rate lookups work with both formats




