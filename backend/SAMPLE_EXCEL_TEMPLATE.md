# Sample Excel Template for Upload Testing

## How to Create Test Excel File

Create an Excel file (.xlsx) with the following structure:

### Column Headers (Row 1)
| Particular | Opening | Transaction | Closing |

### Sample Data (Starting from Row 2)

| Particular | Opening | Transaction | Closing |
|-----------|---------|-------------|---------|
| 100 Equity Shares of Risk Analytics & Data Solutions INC | 5000.00 Dr | | 5000.00 Dr |
| 28461 Of Eq Sh in Vardaan Software Services Ltd UK | | 62291.18 Dr | 62291.18 Dr |
| ADIB Bank AED A/c | 67658.95 Dr | 46468.07 Cr | 21190.88 Dr |
| ADIB Bank USD A/c | 49606.25 Dr | 29597.50 Cr | 20008.75 Dr |
| All-S Technology Private Limited | | 9276.84 Cr | 9276.84 Cr |
| Bank Charges | | 4521.38 Dr | 4521.38 Dr |
| Beyond Exalio Technology LLC | 5604.29 Dr | | 5604.29 Dr |
| Beyond Exhalio Technology L L C- Others | | 59076.92 Dr | 59076.92 Dr |

## Important Notes

1. **Column Names**: Must be exactly as shown (case-sensitive):
   - Particular
   - Opening
   - Transaction
   - Closing

2. **Data Format**:
   - Amounts must be followed by space and either "Dr" or "Cr"
   - Examples: "5000.00 Dr", "46468.07 Cr"
   - Commas in numbers are supported: "62,291.18 Dr"

3. **Required Data**:
   - "Particular" column must have a value for each row
   - At least one of "Opening" or "Transaction" should have data
   - "Closing" is optional (not processed by system)

4. **Empty Rows**:
   - Rows without "Particular" value will be skipped
   - Empty rows are ignored

## Processing Rules

### Single Column Data
If only Opening has data:
- Creates 1 row in database
- Month = "Opening"
- Amount = negative (Dr) or positive (Cr)

If only Transaction has data:
- Creates 1 row in database
- Month = selected month name
- Amount = negative (Dr) or positive (Cr)

### Both Columns Have Data
If both Opening and Transaction have data:
- Creates 2 rows in database
- First row: Opening data with month = "Opening"
- Second row: Transaction data with month = selected month

## Example Excel File

You can create a test file with:
1. Open Excel or Google Sheets
2. Create the headers in first row
3. Add sample data from the table above
4. Save as .xlsx format
5. Upload through the application

## Testing Scenarios

### Test Case 1: Opening Only
- Particular: "Test Account 1"
- Opening: "1000.00 Dr"
- Transaction: (empty)
- Expected: 1 record with month="Opening", amt_tb_lc=-1000.00

### Test Case 2: Transaction Only
- Particular: "Test Account 2"
- Opening: (empty)
- Transaction: "2000.00 Cr"
- Expected: 1 record with month=(selected month), amt_tb_lc=2000.00

### Test Case 3: Both Opening and Transaction
- Particular: "Test Account 3"
- Opening: "3000.00 Dr"
- Transaction: "500.00 Cr"
- Expected: 2 records
  - Record 1: month="Opening", amt_tb_lc=-3000.00
  - Record 2: month=(selected month), amt_tb_lc=500.00

### Test Case 4: Missing Particular
- Particular: (empty)
- Opening: "1000.00 Dr"
- Expected: Row skipped

## Database Prerequisites

Before testing, ensure:
1. `entity_master` table has test entities
2. `month_master` table has month data
3. `coa_master` table has nomenclature mappings for your particular names
4. `final_structured` table exists with correct schema

## Upload Steps

1. Log in to the application
2. Navigate to Upload page
3. Select Entity from dropdown
4. Select Financial Year
5. Select Month
6. Drag and drop or click to select Excel file
7. Click "Upload & Process File"
8. Check success message with records count
9. Verify data in `final_structured` table






