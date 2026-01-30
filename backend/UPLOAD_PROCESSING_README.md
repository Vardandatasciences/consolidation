# Excel Upload Processing Documentation

## Overview
This document describes the Excel file upload and processing functionality for financial data.

## Excel File Format

### Required Columns
The Excel file must have the following columns (case-sensitive):
- **Particular**: Account name/description
- **Opening**: Opening balance with Dr/Cr indicator
- **Transaction**: Transaction amount with Dr/Cr indicator
- **Closing**: Closing balance (not processed, for reference only)

### Data Format Examples
**Simple Format (Recommended):**
- Opening: `5000.00` or `-21190.88`
- Transaction: `-46468.07` or `29597.50`

**Legacy Format (Still Supported):**
- Opening: `5000.00 Dr` or `21190.88 Cr`
- Transaction: `46468.07 Cr` or `29597.50 Cr`

## Processing Logic

### 1. Entity Information
When uploading, the user selects:
- **Entity**: The organization/company
- **Financial Year**: The fiscal year
- **Month**: The specific month

The system automatically retrieves:
- Entity Name
- Entity Code
- Local Currency (lcl_curr) from entity_master table

### 2. COA (Chart of Accounts) Mapping
For each row, the system:
1. Takes the "Particular" value from Excel
2. Matches it with "nomenclature" column in `coa_master` table
3. Retrieves the following columns:
   - std_code
   - brd_cls
   - brd_cls2
   - ctg_code
   - cafl_fnfl
   - cat5

If no match is found, these fields are set to NULL but processing continues.

### 3. Amount Processing

#### Scenario 1: Opening Balance
If the "Opening" column has a value:
- **Positive number**: Stored as positive (Debit)
  - Example: `5000.00` → `5000.00`
  - Example: `5000.00 Dr` → `5000.00`
- **Negative number**: Stored as negative (Credit)
  - Example: `-21190.88` → `-21190.88`
  - Example: `21190.88 Cr` → `-21190.88`
- **Month field**: Set to "Opening"

#### Scenario 2: Transaction Amount
If the "Transaction" column has a value:
- **Positive number**: Stored as positive (Debit)
  - Example: `29597.50` → `29597.50`
  - Example: `29597.50 Dr` → `29597.50`
- **Negative number**: Stored as negative (Credit)
  - Example: `-46468.07` → `-46468.07`
  - Example: `46468.07 Cr` → `-46468.07`
- **Month field**: Set to the selected month name (e.g., "April", "May")

#### Scenario 3: Both Opening and Transaction
If BOTH "Opening" and "Transaction" columns have values:
- **TWO separate rows** are inserted into the database
- First row: Opening balance with month = "Opening"
- Second row: Transaction amount with month = selected month

## Database Table: final_structured

### Columns Populated
```sql
Brd_Cls              -- From coa_master
Brd_Cls_2            -- From coa_master
particular           -- From Excel "Particular" column
Std_Code             -- From coa_master
Amt_TB_lc            -- Calculated amount (positive for Dr, negative for Cr)
Ent_Name             -- From entity_master
Ent_Code             -- From entity_master
Local_Currency_code  -- From entity_master (lcl_curr)
Year                 -- From month_master
Month                -- "Opening" or month name
Qtr                  -- From month_master
Half                 -- From month_master
Ctg_Code             -- From coa_master
Cafl_Fnfl            -- From coa_master
Cat5                 -- From coa_master
```

## API Endpoint

### POST /api/upload/upload
**Authentication**: Required (JWT token)

**Request Format**: multipart/form-data
- `file`: Excel file (.xlsx, .xls, or .csv)
- `ent_id`: Entity ID (integer)
- `month_id`: Month ID (integer)
- `financial_year`: Financial year (integer)

**Response Format**:
```json
{
  "success": true,
  "message": "File processed successfully. 10 records inserted, 2 rows skipped.",
  "data": {
    "filename": "balance_sheet.xlsx",
    "records_inserted": 10,
    "records_skipped": 2,
    "total_rows": 12,
    "entity": "Risk Analytics & Data Solutions INC",
    "month": "April",
    "year": 2024
  },
  "warnings": []  // Optional: any errors encountered during processing
}
```

## Error Handling

### File-Level Errors
- Invalid file format
- Missing required columns
- Unable to read Excel file

### Row-Level Errors
- Missing "Particular" value → Row skipped
- No matching COA record → Processing continues with NULL COA fields
- Invalid amount format → Row skipped with warning
- Database insertion error → Row skipped with warning

## Helper Functions

### parse_amount_and_type(cell_value)
Extracts amount and Dr/Cr type from cell value.
- Supports formats: "123.45 Dr", "1,234.56 Cr"
- Returns: (amount, type) tuple

### calculate_amt_tb_lc(amount, amount_type)
Calculates the final amount for database:
- Dr (Debit) → positive value
- Cr (Credit) → negative value
- Type is determined from sign or explicit Dr/Cr text

### get_entity_details(ent_id)
Retrieves entity information from entity_master table.

### get_month_details(month_id)
Retrieves month information from month_master table.

### get_coa_mapping(particular_name)
Matches particular name with COA master table.

### insert_structured_data(data)
Inserts a single record into final_structured table.

## Testing

To test the upload functionality:
1. Ensure backend server is running
2. Log in to get JWT token
3. Navigate to Upload page
4. Select Entity, Financial Year, and Month
5. Upload Excel file with correct format
6. Check response for success/errors
7. Verify data in final_structured table

## Example Excel File Structure

| Particular | Opening | Transaction | Closing |
|-----------|---------|-------------|---------|
| 100 Equity Shares of Risk Analytics & Data Solutions INC | 5000.00 Dr | | 5000.00 Dr |
| 28461 Of Eq Sh in Vardaan Software Services Ltd UK | | 62291.18 Dr | 62291.18 Dr |
| ADIB Bank AED A/c | 67658.95 Dr | 46468.07 Cr | 21190.88 Dr |
| ADIB Bank USD A/c | 49606.25 Dr | 29597.50 Cr | 20008.75 Dr |
| All-S Technology Private Limited | | 9276.84 Cr | 9276.84 Cr |

## Notes
- All amounts are processed as floating-point numbers
- Commas in numbers are automatically removed
- Case-insensitive Dr/Cr detection (Dr, dr, DR all work)
- Spaces and extra whitespace are trimmed
- Empty rows or rows without "Particular" are skipped





