"""
Upload data routes for file uploads and entity/month data
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import traceback
import uuid
from threading import Lock
import pandas as pd
import re
from datetime import datetime
import os
import tempfile

from database import Database


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


# Import S3 client
try:
    from routes.s3_fucntions import create_direct_mysql_client
    S3_CLIENT_AVAILABLE = True
except ImportError:
    S3_CLIENT_AVAILABLE = False
    print("⚠️ S3 client not available. Install required dependencies.")

# Simple in-memory progress tracker (per operation_id)
UPLOAD_PROGRESS = {}
progress_lock = Lock()


def init_progress(operation_id, meta=None):
    with progress_lock:
        UPLOAD_PROGRESS[operation_id] = {
            'status': 'starting',
            'progress': 0,
            'processed_rows': 0,
            'total_rows': 0,
            'message': 'Initializing upload',
            'meta': meta or {}
        }


def update_progress(operation_id, **kwargs):
    with progress_lock:
        if operation_id not in UPLOAD_PROGRESS:
            return
        UPLOAD_PROGRESS[operation_id].update(kwargs)


def get_progress(operation_id):
    with progress_lock:
        return UPLOAD_PROGRESS.get(operation_id)


# Create blueprint for upload routes
upload_bp = Blueprint('upload', __name__)


def parse_amount_and_type(cell_value):
    """
    Parse cell value to extract amount with sign.
    Returns: (amount, type) where type is 'Dr' or 'Cr' based on sign only.
    Example: "-123.45" -> (123.45, 'Cr'), "123.45" -> (123.45, 'Dr')
    Only checks the sign of the number, ignores any text.
    """
    # Handle None, empty string, or NaN
    if cell_value is None:
        return None, None
    
    # Convert to string and clean
    cell_str = str(cell_value).strip()
    
    # Check for empty or NaN string representations
    if cell_str == '' or cell_str.lower() in ['nan', 'none', 'null', '']:
        return None, None
    
    # Extract numeric value using regex (including negative sign)
    # Pattern: matches numbers like -5000, 5000, -5000.00, 62,291.18, -62,291.18
    amount_match = re.search(r'-?[\d,]+\.?\d*', cell_str)
    if amount_match:
        # Remove commas and convert to float
        amount_str = amount_match.group().replace(',', '')
        try:
            amount = float(amount_str)
            
            # Determine type based on sign only
            if amount < 0:
                amount_type = 'Cr'
                amount = abs(amount)  # Store absolute value, type indicates sign
            elif amount > 0:
                amount_type = 'Dr'
            else:  # amount == 0
                amount_type = 'Dr'  # Default zero to Dr
            
            return amount, amount_type
        except ValueError:
            return None, None
    
    return None, None


def calculate_amt_tb_lc(amount, amount_type):
    """
    Calculate Amt_TB_lc based on amount and type (Dr/Cr).
    Dr -> positive, Cr -> negative
    """
    if amount is None or amount_type is None:
        return None
    
    if amount_type == 'Dr':
        return abs(amount)
    else:  # Cr
        return -abs(amount)


def parse_plain_number(cell_value):
    """
    Extract a plain numeric value from a cell including sign.
    Returns float or None.
    """
    if cell_value is None:
        return None
    cell_str = str(cell_value).strip()
    if cell_str == '' or cell_str.lower() in ['nan', 'none', 'null']:
        return None
    # Extract number with sign, ignoring commas and any trailing text (e.g., Dr/Cr)
    match = re.search(r'-?[\d,]+\.?\d*', cell_str)
    if not match:
        return None
    try:
        return float(match.group().replace(',', ''))
    except ValueError:
        return None


def insert_raw_data(entity_id, month_name, year, particular, opening_value, transaction_value, closing_value, new_company=0):
    """
    Insert raw row from Excel into rawData table.
    Converts provided values to decimals if possible, else stores NULL.
    Expected table structure:
    - RecordID (bigint AI PK) - auto-generated, not included in INSERT
    - EntityID (int)
    - Month (varchar(45))
    - Year (int)
    - financial_year (varchar(10)) - Financial year in format "2024-25"
    - Particular (varchar(255))
    - OpeningBalance (decimal(18,2))
    - Transactions (decimal(18,2))
    - ClosingBalance (decimal(18,2))
    - newCompany (int) - 1 if starting month balance sheet, 0 otherwise
    - created_at (datetime)
    """
    # Format financial year as "2024-25"
    financial_year_str = format_financial_year(year) if year else None
    
    # Insert with backticks to handle case sensitivity
    query = """
        INSERT INTO `rawData` (
            `EntityID`,
            `Month`,
            `Year`,
            `financial_year`,
            `Particular`,
            `OpeningBalance`,
            `Transactions`,
            `ClosingBalance`,
            `newCompany`,
            `created_at`
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = [
        entity_id,
        month_name,
        year,
        financial_year_str,
        particular,
        parse_plain_number(opening_value),
        parse_plain_number(transaction_value),
        parse_plain_number(closing_value),
        new_company,
        datetime.now()
    ]
    try:
        result = Database.execute_query(query, params=params)
        return result  # Return the insert result
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Database error: {error_msg}")
        print(f"⚠️ Failed to insert rawData for '{particular}': {error_msg}")
        return None
        # Get actual column names for debugging
        try:
            debug_query = "SHOW COLUMNS FROM `rawData`"
            columns = Database.execute_query(debug_query, fetch_all=True)
            if columns:
                actual_cols = [col.get('Field', col) for col in columns]
                print(f"🔍 Actual columns in rawData table: {actual_cols}")
                print(f"🔍 Expected columns: ['RecordID', 'EntityID', 'Month', 'Year', 'Particular', 'OpeningBalance', 'Transactions', 'ClosingBalance', 'created_at']")
                # Check if Month and Year exist
                if 'Month' not in actual_cols:
                    print(f"⚠️ WARNING: 'Month' column not found in rawData table!")
                    print(f"   Check for case variations: {[col for col in actual_cols if 'month' in col.lower()]}")
                if 'Year' not in actual_cols:
                    print(f"⚠️ WARNING: 'Year' column not found in rawData table!")
                    print(f"   Check for case variations: {[col for col in actual_cols if 'year' in col.lower()]}")
        except Exception as debug_err:
            print(f"⚠️ Could not fetch column info: {debug_err}")
        # Do not interrupt processing; continue


def delete_existing_data_for_entity_month_year(entity_id, entity_code, month_name, year):
    """
    Delete all existing records from rawData and final_structured tables
    for the given entity, month, and year combination.
    
    Args:
        entity_id: Entity ID (for rawData table)
        entity_code: Entity code (for final_structured table)
        month_name: Month name (e.g., 'January', 'Feb', etc.)
        year: Year (integer)
    
    Returns:
        dict with deletion counts and status
    """
    try:
        print(f"\n🔍 Checking for existing data: Entity ID={entity_id}, Entity Code={entity_code}, Month={month_name}, Year={year}")
        
        # Delete from rawData table (case-insensitive for month matching)
        raw_delete_query = """
            DELETE FROM `rawData`
            WHERE `EntityID` = %s AND LOWER(TRIM(`Month`)) = LOWER(TRIM(%s)) AND `Year` = %s
        """
        raw_delete_params = [entity_id, month_name, year]
        
        raw_deleted_count = 0
        try:
            # Get count before deletion (case-insensitive)
            count_query = """
                SELECT COUNT(*) as count
                FROM `rawData`
                WHERE `EntityID` = %s AND LOWER(TRIM(`Month`)) = LOWER(TRIM(%s)) AND `Year` = %s
            """
            count_result = Database.execute_query(count_query, params=raw_delete_params, fetch_one=True)
            raw_deleted_count = count_result.get('count', 0) if count_result else 0
            
            if raw_deleted_count > 0:
                print(f"🗑️ Found {raw_deleted_count} existing rawData record(s) to delete")
                Database.execute_query(raw_delete_query, params=raw_delete_params)
                
                # CRITICAL: Verify deletion completed
                verify_count = Database.execute_query(count_query, params=raw_delete_params, fetch_one=True)
                remaining = verify_count.get('count', 0) if verify_count else 0
                
                if remaining == 0:
                    print(f"✅ Deleted {raw_deleted_count} record(s) from rawData table (VERIFIED - {remaining} remaining)")
                else:
                    print(f"❌ ERROR: Deleted {raw_deleted_count} record(s) from rawData table, but {remaining} STILL REMAIN!")
                    print(f"   This will cause duplicates! Attempting to delete again...")
                    # Try one more time
                    Database.execute_query(raw_delete_query, params=raw_delete_params)
                    verify_count2 = Database.execute_query(count_query, params=raw_delete_params, fetch_one=True)
                    remaining2 = verify_count2.get('count', 0) if verify_count2 else 0
                    if remaining2 == 0:
                        print(f"✅ Second deletion attempt successful - all records removed")
                    else:
                        print(f"❌ CRITICAL: {remaining2} records still remain after second deletion attempt!")
            else:
                print(f"ℹ️ No existing records found in rawData table (clean start)")
        except Exception as raw_err:
            print(f"⚠️ Error deleting from rawData: {str(raw_err)}")
            traceback.print_exc()
            # Continue even if rawData deletion fails
        
        # Delete from final_structured table (case-insensitive for month matching)
        structured_delete_query = """
            DELETE FROM `final_structured`
            WHERE LOWER(TRIM(`entityCode`)) = LOWER(TRIM(%s)) 
              AND LOWER(TRIM(`selectedMonth`)) = LOWER(TRIM(%s)) 
              AND `Year` = %s
        """
        structured_delete_params = [entity_code, month_name, year]
        
        structured_deleted_count = 0
        try:
            # Get count before deletion (case-insensitive)
            count_query = """
                SELECT COUNT(*) as count
                FROM `final_structured`
                WHERE LOWER(TRIM(`entityCode`)) = LOWER(TRIM(%s)) 
                  AND LOWER(TRIM(`selectedMonth`)) = LOWER(TRIM(%s)) 
                  AND `Year` = %s
            """
            count_result = Database.execute_query(count_query, params=structured_delete_params, fetch_one=True)
            structured_deleted_count = count_result.get('count', 0) if count_result else 0
            
            if structured_deleted_count > 0:
                Database.execute_query(structured_delete_query, params=structured_delete_params)
                
                # Verify deletion
                verify_count = Database.execute_query(count_query, params=structured_delete_params, fetch_one=True)
                remaining = verify_count.get('count', 0) if verify_count else 0
                
                if remaining == 0:
                    print(f"✅ Deleted {structured_deleted_count} record(s) from final_structured table (verified)")
                else:
                    print(f"⚠️ Deleted {structured_deleted_count} record(s) from final_structured table, but {remaining} still remain")
            else:
                print(f"ℹ️ No existing records found in final_structured table")
        except Exception as structured_err:
            print(f"⚠️ Error deleting from final_structured: {str(structured_err)}")
            traceback.print_exc()
            # Continue even if final_structured deletion fails
        
        total_deleted = raw_deleted_count + structured_deleted_count
        print(f"📊 Total records deleted: {total_deleted} (rawData: {raw_deleted_count}, final_structured: {structured_deleted_count})")
        
        return {
            'success': True,
            'raw_data_deleted': raw_deleted_count,
            'structured_data_deleted': structured_deleted_count,
            'total_deleted': total_deleted
        }
        
    except Exception as e:
        print(f"❌ Error in delete_existing_data_for_entity_month_year: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'raw_data_deleted': 0,
            'structured_data_deleted': 0,
            'total_deleted': 0
        }


def deduplicate_final_structured_for_entity_month_year(entity_code, month_name, year):
    """
    Hard de‑duplicate final_structured for a given entity + month + year.
    Keeps the oldest row (smallest sl_no) for each unique combination of:
      Particular, entityCode, selectedMonth, Year, Month, transactionAmount
    and deletes any additional duplicates.
    """
    try:
        print(f"\n🔍 Running hard de-duplication for final_structured: "
              f"entityCode={entity_code}, month={month_name}, year={year}")

        # Delete any duplicates, keeping the lowest sl_no in each duplicate group
        dedupe_query = """
            DELETE fs1
            FROM final_structured fs1
            JOIN final_structured fs2
              ON LOWER(TRIM(fs1.Particular)) = LOWER(TRIM(fs2.Particular))
             AND LOWER(TRIM(fs1.entityCode))  = LOWER(TRIM(fs2.entityCode))
             AND LOWER(TRIM(fs1.selectedMonth)) = LOWER(TRIM(fs2.selectedMonth))
             AND fs1.Year = fs2.Year
             AND LOWER(TRIM(fs1.Month)) = LOWER(TRIM(fs2.Month))
             AND ABS(fs1.transactionAmount - fs2.transactionAmount) < 0.01
             AND fs1.sl_no > fs2.sl_no
            WHERE LOWER(TRIM(fs1.entityCode)) = LOWER(TRIM(%s))
              AND LOWER(TRIM(fs1.selectedMonth)) = LOWER(TRIM(%s))
              AND fs1.Year = %s
        """
        params = [entity_code, month_name, year]
        deleted = Database.execute_query(dedupe_query, params=params)

        print(f"✅ De-duplication completed for final_structured. "
              f"Duplicate rows deleted: {deleted}")

        return {
            'success': True,
            'deleted': deleted or 0
        }
    except Exception as e:
        print(f"⚠️ Error during de-duplication in final_structured: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'deleted': 0
        }


def get_entity_details(ent_id):
    """
    Get entity details including name, code, and local currency.
    """
    query = """
        SELECT ent_name, ent_code, lcl_curr
        FROM entity_master
        WHERE ent_id = %s
    """
    result = Database.execute_query(query, params=[ent_id], fetch_one=True)
    return result


def get_month_details(month_id):
    """
    Get month details including month name, year, quarter, and half.
    """
    query = """
        SELECT month_short, month_name, year, qtr, half
        FROM month_master
        WHERE mnt_id = %s
    """
    result = Database.execute_query(query, params=[month_id], fetch_one=True)
    return result


def get_coa_mapping(particular_name):
    """
    Get COA mapping details from code_master based on RawParticulars.
    Maps new schema columns to expected keys:
      mainCategory -> std_code
      category1 -> brd_cls
      category2 -> brd_cls_2
      category3 -> ctg_code
      category4 -> cafl_fnfl
      category5 -> cat_5
    """
    # Normalize input: strip whitespace so trailing/leading spaces don't break matches
    clean_particular = (particular_name or "").strip()

    # Use case-insensitive, trimmed comparison to be robust against extra spaces
    query = """
        SELECT 
            mainCategory,
            category1,
            category2,
            category3,
            category4,
            category5
        FROM code_master
        WHERE LOWER(TRIM(RawParticulars)) = LOWER(TRIM(%s))
    """
    
    try:
        result = Database.execute_query(query, params=[clean_particular], fetch_one=True)
        
        if not result:
            return None
        
        # Map new schema fields to the expected keys used elsewhere
        normalized = {
            'std_code': result.get('mainCategory'),
            'brd_cls': result.get('category1'),
            'brd_cls_2': result.get('category2'),
            'ctg_code': result.get('category3'),
            'cafl_fnfl': result.get('category4'),
            'cat_5': result.get('category5')
        }
        return normalized
        
    except Exception as e:
        # Silently continue if COA mapping fails - this is expected for entries not in code_master
        # Only log actual errors (not just missing entries)
        if 'Unknown column' in str(e) or 'does not exist' in str(e):
            # Database schema issue - log it
            print(f"⚠️ Database schema issue in COA mapping (code_master): {str(e)}")
        # Return None to continue processing without COA data
        return None


def insert_structured_data(data, inserted_keys_set=None):
    """
    Insert a record into final_structured table.
    Column names must match exactly: category1, category2, category3, category4, category5
    Now includes selectedMonth column (the month selected during upload)
    Checks for duplicates before inserting to prevent duplicate transactions.
    
    Args:
        data: Dictionary containing record data
        inserted_keys_set: Optional set to track inserted records in current batch (prevents duplicates within same upload)
    """
    # Normalize transaction amount for comparison (round to 2 decimal places to handle floating point precision)
    amt_tb_lc = data.get('amt_tb_lc')
    if amt_tb_lc is not None:
        try:
            amt_tb_lc_rounded = round(float(amt_tb_lc), 2)
        except (ValueError, TypeError):
            amt_tb_lc_rounded = amt_tb_lc
    else:
        amt_tb_lc_rounded = None
    
    # Create a unique key for this record (normalized for comparison)
    record_key = (
        str(data.get('particular', '')).strip().lower(),
        str(data.get('ent_code', '')).strip().lower(),
        str(data.get('selectedMonth', '')).strip().lower(),
        int(data.get('year', 0)) if data.get('year') else 0,
        str(data.get('month', '')).strip().lower(),
        amt_tb_lc_rounded
    )
    
    # First check in-memory set (for duplicates within same batch/upload)
    if inserted_keys_set is not None:
        if record_key in inserted_keys_set:
            print(f"⏭️ Skipping duplicate record (in batch): {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
            print(f"   Record key: {record_key}")
            return None
        inserted_keys_set.add(record_key)
        if len(inserted_keys_set) % 50 == 0:  # Log every 50 records for debugging
            print(f"📊 Tracking {len(inserted_keys_set)} unique records in current batch")
    
    # Format financial year for comparison
    year_value = data.get('year')
    financial_year_str = format_financial_year(year_value) if year_value else None
    
    # Also check database for existing records (case-insensitive, with floating point tolerance)
    # Check both financial_year (new format) and Year (old format) for backward compatibility
    check_query = """
        SELECT COUNT(*) as count
        FROM final_structured
        WHERE LOWER(TRIM(Particular)) = LOWER(TRIM(%s))
          AND LOWER(TRIM(entityCode)) = LOWER(TRIM(%s))
          AND LOWER(TRIM(selectedMonth)) = LOWER(TRIM(%s))
          AND (Year = %s OR financial_year = %s)
          AND LOWER(TRIM(Month)) = LOWER(TRIM(%s))
          AND ABS(transactionAmount - %s) < 0.01
    """
    check_params = [
        data.get('particular'),
        data.get('ent_code'),
        data.get('selectedMonth'),
        year_value,
        financial_year_str,
        data.get('month'),
        amt_tb_lc_rounded if amt_tb_lc_rounded is not None else 0
    ]
    
    try:
        existing = Database.execute_query(check_query, params=check_params, fetch_one=True)
        existing_count = existing.get('count', 0) if existing else 0
        if existing_count > 0:
            # Duplicate record exists in database, skip insertion
            print(f"⏭️ Skipping duplicate record (in DB): {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
            print(f"   Found {existing_count} existing record(s) matching this data")
            print(f"   Check params: Particular='{check_params[0]}', entityCode='{check_params[1]}', selectedMonth='{check_params[2]}', Year={check_params[3]}, Month='{check_params[4]}', Amount={check_params[5]}")
            # Remove from set if we added it
            if inserted_keys_set is not None and record_key in inserted_keys_set:
                inserted_keys_set.discard(record_key)
            return None
        else:
            # Log when no duplicate found (for first few records for debugging)
            if len(inserted_keys_set or []) < 5:
                print(f"✅ No duplicate found, proceeding with insert: {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
    except Exception as check_err:
        # If check fails, log but continue with insert (better to have duplicate than miss data)
        print(f"⚠️ Error checking for duplicate: {str(check_err)}")
        traceback.print_exc()
    
    # Final safety check: Double-check database one more time right before insert
    # (in case a record was inserted between our first check and now)
    try:
        final_check = Database.execute_query(check_query, params=check_params, fetch_one=True)
        final_count = final_check.get('count', 0) if final_check else 0
        if final_count > 0:
            final_ids = final_check.get('ids', '')
            print(f"⏭️ Final check: Duplicate found right before insert - skipping: {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
            print(f"   Found {final_count} existing record(s) with IDs: {final_ids}")
            if inserted_keys_set is not None and record_key in inserted_keys_set:
                inserted_keys_set.discard(record_key)
            return None
    except Exception as final_check_err:
        print(f"⚠️ Error in final duplicate check: {str(final_check_err)}")
    
    # Format financial year as "2024-25" (calculated earlier in function)
    # financial_year_str is already calculated above
    
    # Use INSERT IGNORE to prevent duplicates at database level (safety net)
    # This will silently skip if a duplicate exists based on any unique constraint
    query = """
        INSERT IGNORE INTO final_structured (
            Particular, 
            entityName, 
            entityCode, 
            localCurrencyCode, 
            transactionAmount, 
            Month, 
            selectedMonth,
            mainCategory, 
            category1, 
            category2, 
            category3, 
            category4, 
            category5, 
            Year, 
            financial_year,
            Qtr, 
            Half
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = [
        data.get('particular'),
        data.get('ent_name'),
        data.get('ent_code'),
        data.get('local_currency_code'),
        data.get('amt_tb_lc'),
        data.get('month'),  # Original Month column (e.g., 'Opening', 'January', etc.)
        data.get('selectedMonth'),  # New selectedMonth column (month selected during upload)
        data.get('std_code'),
        data.get('brd_cls'),
        data.get('brd_cls_2'),
        data.get('ctg_code'),
        data.get('cafl_fnfl'),
        data.get('cat_5'),
        data.get('year'),
        financial_year_str,  # Financial year in "2024-25" format
        data.get('qtr'),
        data.get('half')
    ]
    
    try:
        result = Database.execute_query(query, params=params)
        # INSERT IGNORE returns 0 if duplicate was ignored, or lastrowid if inserted
        # Note: INSERT IGNORE only works if there's a unique constraint, which we may not have
        # So we rely on our duplicate check above
        if result == 0:
            print(f"⏭️ INSERT IGNORE prevented duplicate: {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
            return None
        # Log successful insert for debugging
        if len(inserted_keys_set or []) < 10:  # Log first 10 inserts
            print(f"✅ Successfully inserted: {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')} (ID: {result})")
        return result
    except Exception as e:
        # Check if it's a duplicate key error (in case INSERT IGNORE doesn't work)
        error_str = str(e).lower()
        if 'duplicate' in error_str or 'unique' in error_str:
            print(f"⏭️ Database prevented duplicate (unique constraint): {data.get('particular')} - {data.get('month')} - Amount: {data.get('amt_tb_lc')}")
            return None
        print(f"❌ Database insert error: {str(e)}")
        print(f"   Particular: {data.get('particular')}, Amount: {data.get('amt_tb_lc')}, Month: {data.get('month')}")
        traceback.print_exc()
        raise  # Re-raise to be caught by calling function


def create_upload_history_table():
    """
    Create upload_history table if it doesn't exist.
    """
    query = """
        CREATE TABLE IF NOT EXISTS upload_history (
            slno BIGINT AUTO_INCREMENT PRIMARY KEY,
            ent_code VARCHAR(50) NOT NULL,
            year INT NOT NULL,
            month VARCHAR(20) NOT NULL,
            doc_link VARCHAR(500) NOT NULL,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_ent_code (ent_code),
            INDEX idx_year (year),
            INDEX idx_month (month),
            INDEX idx_uploaded_at (uploaded_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    try:
        Database.execute_query(query)
        print("✅ upload_history table verified/created")
    except Exception as e:
        print(f"⚠️ Error creating upload_history table: {str(e)}")


def save_upload_history(ent_code, year, month, doc_link):
    """
    Save upload history to database.
    
    Args:
        ent_code: Entity code
        year: Financial year
        month: Month name
        doc_link: S3 document link
    
    Returns:
        operation_id if successful, None otherwise
    """
    try:
        # Ensure table exists
        create_upload_history_table()
        
        query = """
            INSERT INTO upload_history (ent_code, year, month, doc_link, uploaded_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = [
            ent_code,
            year,
            month,
            doc_link,
            datetime.now()
        ]
        
        operation_id = Database.execute_query(query, params=params)
        print(f"✅ Upload history saved: ID {operation_id}")
        return operation_id
        
    except Exception as e:
        print(f"❌ Error saving upload history: {str(e)}")
        traceback.print_exc()
        return None


@upload_bp.route('/entities', methods=['GET', 'OPTIONS'])
def get_entities():
    """Get all entities from entity_master"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT ent_id, ent_name, ent_code, lcl_curr, city, country 
            FROM entity_master 
            ORDER BY ent_name ASC
        """
        entities = Database.execute_query(query, fetch_all=True)
        
        print(f"✅ Fetched {len(entities) if entities else 0} entities")
        
        return jsonify({
            'success': True,
            'data': {
                'entities': entities or []
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching entities: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching entities'
        }), 500


@upload_bp.route('/months', methods=['GET', 'OPTIONS'])
def get_months():
    """Get all months from month_master"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT mnt_id, month_short, month_name, year, qtr, half 
            FROM month_master 
            ORDER BY year DESC, mnt_id ASC
        """
        months = Database.execute_query(query, fetch_all=True)
        
        print(f"✅ Fetched {len(months) if months else 0} months")
        
        return jsonify({
            'success': True,
            'data': {
                'months': months or []
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching months: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching months'
        }), 500


@upload_bp.route('/financial-years', methods=['GET', 'OPTIONS'])
def get_financial_years():
    """Get distinct financial years from month_master"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT DISTINCT year 
            FROM month_master 
            ORDER BY year DESC
        """
        years = Database.execute_query(query, fetch_all=True)
        
        # Extract just the year values
        year_list = [year['year'] for year in years] if years else []
        
        print(f"✅ Fetched {len(year_list)} financial years")
        
        return jsonify({
            'success': True,
            'data': {
                'years': year_list
            }
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error fetching financial years: {error_type}: {error_msg}")
        traceback.print_exc()
        
        # In development/debug mode, include more details
        import os
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        response_data = {
            'success': False,
            'message': 'An error occurred while fetching financial years',
            'error_type': error_type
        }
        
        if debug_mode:
            response_data['error_details'] = error_msg
            response_data['traceback'] = traceback.format_exc()
        
        return jsonify(response_data), 500


@upload_bp.route('/progress/<operation_id>', methods=['GET', 'OPTIONS'])
def get_upload_progress(operation_id):
    """Poll current upload processing progress by operation_id."""
    # Handle preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    progress = get_progress(operation_id)
    if not progress:
        return jsonify({
            'success': False,
            'message': 'Operation not found'
        }), 404

    return jsonify({
        'success': True,
        'data': progress
    }), 200


@upload_bp.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    """Handle file upload, save to S3, and process Excel data"""
    temp_file_path = None
    s3_doc_link = None
    operation_id = None
    
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Debug: Log request details FIRST (before JWT validation)
        print(f"\n{'='*60}")
        print(f"🔍 UPLOAD REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"🔍 Request method: {request.method}")
        print(f"🔍 Content-Type: {request.content_type}")
        print(f"🔍 All headers: {dict(request.headers)}")
        auth_header = request.headers.get('Authorization', 'NOT SET')
        print(f"🔍 Authorization header: {auth_header[:100] if auth_header != 'NOT SET' else 'NOT SET'}")
        print(f"🔍 Has files: {'file' in request.files}")
        print(f"🔍 Form keys: {list(request.form.keys())}")
        print(f"🔍 Files keys: {list(request.files.keys())}")
        print(f"{'='*60}\n")
        
        # Manual JWT verification with better error handling
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            print(f"   Authorization header present: {auth_header != 'NOT SET'}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type,
                'debug': {
                    'auth_header_present': auth_header != 'NOT SET',
                    'auth_header_preview': auth_header[:50] if auth_header != 'NOT SET' else None
                }
            }), 401
        
        # Accept optional client-provided operation id for progress tracking
        operation_id = request.form.get('operation_id') or str(uuid.uuid4())

        # Initialize progress tracker early
        init_progress(operation_id, meta={'filename': None})
        update_progress(operation_id, status='validating', message='Validating request')

        # Check if file is in request
        if 'file' not in request.files:
            print(f"❌ No 'file' key in request.files")
            print(f"   Available keys: {list(request.files.keys())}")
            return jsonify({
                'success': False,
                'message': 'No file provided. Please select a file to upload.',
                'debug': {
                    'available_files': list(request.files.keys()),
                    'content_type': request.content_type
                }
            }), 400
        
        file = request.files['file']
        update_progress(operation_id, meta={'filename': file.filename})
        
        if file.filename == '':
            print(f"❌ File filename is empty")
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        print(f"📄 File received: {file.filename}, Content-Type: {file.content_type}")
        
        # Get other form data
        ent_id = request.form.get('ent_id')
        month_name = request.form.get('month_name')  # Month name directly from form
        month_id = request.form.get('month_id')  # Month ID (optional, if month_name not provided)
        financial_year = request.form.get('financial_year')
        # Financial Year Convention:
        # - User selects "2024" → means FY 2023-2024 → store as 2024 (ending year)
        # - User selects "2025" → means FY 2024-2025 → store as 2025 (ending year)
        # The financial_year from UI is the ENDING year and is stored as-is in DB
        new_company = request.form.get('newCompany', '0')  # Default to 0 if not provided
        
        # Convert newCompany to int (1 for yes, 0 for no)
        try:
            new_company = int(new_company)
        except (ValueError, TypeError):
            new_company = 0
        
        print(f"📋 Form data - ent_id: {ent_id}, month_name: {month_name}, month_id: {month_id}, financial_year: {financial_year}, newCompany: {new_company}")
        
        # Validate required fields - need either month_name or month_id
        if not ent_id or not financial_year:
            missing = []
            if not ent_id:
                missing.append('Entity')
            if not financial_year:
                missing.append('Financial Year')
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing)}',
                'missing_fields': missing
            }), 400
        
        # Validate month - need either month_name or month_id
        if not month_name and not month_id:
            return jsonify({
                'success': False,
                'message': 'Missing required field: Month (month_name or month_id)',
                'missing_fields': ['Month']
            }), 400
        
        # Get entity details
        entity_details = get_entity_details(ent_id)
        if not entity_details:
            return jsonify({
                'success': False,
                'message': 'Invalid entity ID'
            }), 400
        
        # Get month details - use month_name if provided, otherwise lookup by month_id
        if month_name:
            # Use month_name directly
            month_details = {
                'month_name': month_name,
                'year': int(financial_year),
                'qtr': None,  # Can be calculated if needed
                'half': None  # Can be calculated if needed
            }
        else:
            # Lookup by month_id
            month_details_result = get_month_details(month_id)
            if not month_details_result:
                return jsonify({
                    'success': False,
                    'message': 'Invalid month ID'
                }), 400
            month_details = {
                'month_name': month_details_result.get('month_name', month_name),
                'year': month_details_result.get('year', int(financial_year)),
                'qtr': month_details_result.get('qtr'),
                'half': month_details_result.get('half')
            }
        
        # Validate that the month/year falls within an active financial year range
        from routes.financial_year_master import validate_date_against_fy_master, get_current_financial_year
        
        # Convert month_name and year to a date (first day of that month)
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        month_name_lower = (month_details['month_name'] or '').lower().strip()
        month_num = month_map.get(month_name_lower, 1)
        upload_date = datetime(month_details['year'], month_num, 1).date()
        
        # Validate against master data
        validation_result = validate_date_against_fy_master(upload_date)
        if not validation_result['valid']:
            # Check if this is a previous financial year (before any configured FY)
            from routes.financial_year_master import check_if_previous_fy
            
            previous_fy_check = check_if_previous_fy(upload_date)
            if previous_fy_check['is_previous']:
                return jsonify({
                    'success': False,
                    'message': f"Cannot upload data for previous financial years. The selected date ({upload_date}) falls before any configured financial year. Please configure FY {previous_fy_check.get('suggested_fy', '')} in Master Data settings first.",
                    'error': 'PREVIOUS_FINANCIAL_YEAR_NOT_CONFIGURED',
                    'upload_date': str(upload_date),
                    'month': month_details['month_name'],
                    'year': month_details['year'],
                    'suggested_fy': previous_fy_check.get('suggested_fy', '')
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': f"Data upload not allowed: {validation_result['message']}. Please configure the financial year in Master Data settings.",
                    'error': 'FINANCIAL_YEAR_VALIDATION_FAILED',
                    'upload_date': str(upload_date),
                    'month': month_details['month_name'],
                    'year': month_details['year']
                }), 400
        
        print(f"✅ Financial year validation passed: {validation_result['financial_year']}")
        
        # Validate that the selected financial year is the CURRENT financial year
        current_fy_result = get_current_financial_year()
        if current_fy_result['found']:
            selected_fy = validation_result.get('financial_year')
            current_fy = current_fy_result.get('financial_year')
            
            if selected_fy != current_fy:
                return jsonify({
                    'success': False,
                    'message': f"You can only upload data for the current financial year (FY {current_fy}). Selected FY {selected_fy} is not the current financial year.",
                    'error': 'NOT_CURRENT_FINANCIAL_YEAR',
                    'selected_fy': selected_fy,
                    'current_fy': current_fy,
                    'upload_date': str(upload_date)
                }), 400
            print(f"✅ Current financial year validation passed: {current_fy}")
        else:
            print(f"⚠️ Warning: No current financial year found. Skipping current FY validation.")
        
        print(f"📄 Processing file: {file.filename}")
        print(f"🏢 Entity: {entity_details['ent_name']} ({entity_details['ent_code']})")
        print(f"📅 Month: {month_details['month_name']} {month_details['year']}")
        print(f"👤 User ID: {user_id}")
        update_progress(
            operation_id,
            status='preparing',
            message='Preparing upload',
            meta={
                'filename': file.filename,
                'entity': entity_details['ent_name'],
                'month': month_details['month_name'],
                'year': month_details['year']
            }
        )
        
        # Delete existing data for this entity + month + year combination before inserting new data
        print(f"\n{'='*60}")
        print(f"🗑️ Checking and deleting existing data for Entity {entity_details['ent_name']}, {month_details['month_name']} {month_details['year']}")
        print(f"{'='*60}")
        deletion_result = delete_existing_data_for_entity_month_year(
            entity_id=int(ent_id),
            entity_code=entity_details['ent_code'],
            month_name=month_details['month_name'],
            year=month_details['year']
        )
        print(f"🗑️ Deletion result: {deletion_result}")
        print(f"{'='*60}\n")
        
        # Verify deletion completed before proceeding
        if not deletion_result.get('success', False):
            print(f"⚠️ Warning: Deletion may have failed, but continuing with upload...")
        
        # Save file temporarily for S3 upload
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file.save(temp_file_path)
            print(f"💾 Saved file temporarily: {temp_file_path}")
        except Exception as e:
            print(f"❌ Error saving temporary file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error saving file: {str(e)}'
            }), 500
        
        # Upload to S3 if S3 client is available
        if S3_CLIENT_AVAILABLE:
            try:
                print(f"☁️ Uploading to S3...")
                s3_client = create_direct_mysql_client()
                
                # Upload file to S3
                upload_result = s3_client.upload(
                    file_path=temp_file_path,
                    user_id=user_id,
                    module='financial_data'  # Module name for financial data uploads
                )
                
                if upload_result.get('success'):
                    # Get S3 URL from response
                    file_info = upload_result.get('file_info', {})
                    s3_doc_link = file_info.get('url', '')
                    
                    if s3_doc_link:
                        print(f"✅ File uploaded to S3: {s3_doc_link}")
                        
                        # Save upload history
                        history_id = save_upload_history(
                            ent_code=entity_details['ent_code'],
                            year=month_details['year'],
                            month=month_details['month_name'],
                            doc_link=s3_doc_link
                        )
                        
                        if history_id:
                            print(f"✅ Upload history saved with ID: {history_id}")
                        else:
                            print(f"⚠️ Upload history save failed, but continuing...")
                    else:
                        print(f"⚠️ S3 upload successful but no URL returned")
                else:
                    error_msg = upload_result.get('error', 'Unknown S3 upload error')
                    print(f"⚠️ S3 upload failed: {error_msg}")
                    # Continue processing even if S3 upload fails
                    
            except Exception as s3_error:
                print(f"⚠️ S3 upload error: {str(s3_error)}")
                traceback.print_exc()
                # Continue processing even if S3 upload fails
        else:
            print(f"⚠️ S3 client not available, skipping S3 upload")
        
        # Read Excel file (reset file pointer)
        file.seek(0)  # Reset file pointer to beginning
        try:
            # Read the Excel file into a pandas DataFrame
            # Use dtype=str to preserve text format including Dr/Cr
            df = pd.read_excel(file, engine='openpyxl', dtype=str, keep_default_na=False)
            print(f"📊 Read {len(df)} rows from Excel")
            
            # Display column names for debugging
            print(f"📋 Columns: {list(df.columns)}")
            
            # Show sample of first row data to debug format
            if len(df) > 0:
                print(f"🔍 Sample row 1 data:")
                print(f"   Particular: {df.iloc[0].get('Particular', 'N/A')}")
                print(f"   Opening: '{df.iloc[0].get('Opening', 'N/A')}' (type: {type(df.iloc[0].get('Opening', None))})")
                print(f"   Transaction: '{df.iloc[0].get('Transaction', 'N/A')}' (type: {type(df.iloc[0].get('Transaction', None))})")
                print(f"   Closing: '{df.iloc[0].get('Closing', 'N/A')}' (type: {type(df.iloc[0].get('Closing', None))})")
            
            update_progress(
                operation_id,
                status='processing',
                message='Processing rows',
                total_rows=len(df),
                processed_rows=0,
                progress=0
            )
            
        except Exception as e:
            print(f"❌ Error reading Excel file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error reading Excel file: {str(e)}'
            }), 400
        
        # Process each row
        records_inserted = 0
        records_skipped = 0
        records_without_coa = 0
        records_duplicate_skipped = 0
        raw_data_inserted = 0
        final_structured_inserted = 0
        errors = []
        
        # Track inserted records in this batch to prevent duplicates within the same upload
        inserted_keys_set = set()
        
        print(f"\n{'='*60}")
        print(f"📊 Starting to process {len(df)} rows from Excel file")
        print(f"{'='*60}\n")
        
        for index, row in df.iterrows():
            try:
                # Get particular name
                particular = row.get('Particular', None)
                if pd.isna(particular) or particular == '':
                    records_skipped += 1
                    continue
                
                # Clean particular name
                particular = str(particular).strip()
                
                # Store raw data row before transformations
                # If newCompany is 0, don't save opening balance data
                # IMPORTANT: Check for duplicates BEFORE inserting to prevent double insertion
                try:
                    # Check if this rawData record already exists (case-insensitive)
                    raw_check_query = """
                        SELECT COUNT(*) as count, RecordID
                        FROM `rawData`
                        WHERE `EntityID` = %s 
                          AND LOWER(TRIM(`Month`)) = LOWER(TRIM(%s))
                          AND `Year` = %s
                          AND LOWER(TRIM(`Particular`)) = LOWER(TRIM(%s))
                        LIMIT 1
                    """
                    raw_check_params = [int(ent_id), month_details['month_name'], month_details['year'], particular]
                    raw_exists = Database.execute_query(raw_check_query, params=raw_check_params, fetch_one=True)
                    raw_exists_count = raw_exists.get('count', 0) if raw_exists else 0
                    
                    if raw_exists_count > 0:
                        existing_id = raw_exists.get('RecordID', 'unknown')
                        if index < 3:
                            print(f"⏭️ SKIPPING rawData insert - DUPLICATE EXISTS: {particular} (Existing ID: {existing_id})")
                    else:
                        opening_value_for_raw = row.get('Opening', None) if new_company == 1 else None
                        raw_result = insert_raw_data(
                            entity_id=int(ent_id),
                            month_name=month_details['month_name'],
                            year=month_details['year'],
                            particular=particular,
                            opening_value=opening_value_for_raw,
                            transaction_value=row.get('Transaction', None),
                            closing_value=row.get('Closing', None),
                            new_company=new_company
                        )
                        if raw_result is not None:
                            raw_data_inserted += 1
                        if index < 3:
                            print(f"🗃️ Saved rawData for: {particular} (newCompany: {new_company}, Opening: {'saved' if new_company == 1 else 'skipped'}, ID: {raw_result})")
                except Exception as raw_err:
                    print(f"⚠️ rawData insert warning for '{particular}': {str(raw_err)}")
                    traceback.print_exc()
                
                # Get COA mapping
                coa_mapping = get_coa_mapping(particular)
                if not coa_mapping:
                    # No COA mapping found - continue with None values (this is expected for new entries)
                    records_without_coa += 1
                    coa_mapping = {
                        'std_code': None,
                        'brd_cls': None,
                        'brd_cls_2': None,
                        'ctg_code': None,
                        'cafl_fnfl': None,
                        'cat_5': None
                    }
                
                # Parse Opening column
                opening_value = row.get('Opening', None)
                opening_amount, opening_type = parse_amount_and_type(opening_value)
                
                # Parse Transaction column
                transaction_value = row.get('Transaction', None)
                transaction_amount, transaction_type = parse_amount_and_type(transaction_value)
                
                # Parse Closing column (for rawData storage only, not used for type inference)
                closing_value = row.get('Closing', None)
                closing_amount, closing_type = parse_amount_and_type(closing_value)
                
                # Debug first few rows to see what's being parsed
                if index < 3:
                    print(f"🔍 Row {index + 1} - Particular: {particular}")
                    print(f"   Opening: '{opening_value}' → Amount: {opening_amount}, Type: {opening_type}")
                    print(f"   Transaction: '{transaction_value}' → Amount: {transaction_amount}, Type: {transaction_type}")
                    print(f"   Closing: '{closing_value}' → Amount: {closing_amount}, Type: {closing_type}")
                
                # Base data structure
                base_data = {
                    'particular': particular,
                    'ent_name': entity_details['ent_name'],
                    'ent_code': entity_details['ent_code'],
                    'local_currency_code': entity_details['lcl_curr'],
                    'year': month_details['year'],
                    'qtr': month_details.get('qtr'),
                    'half': month_details.get('half'),
                    'selectedMonth': month_details['month_name'],  # Month selected during upload
                    'std_code': coa_mapping.get('std_code'),
                    'brd_cls': coa_mapping.get('brd_cls'),
                    'brd_cls_2': coa_mapping.get('brd_cls_2'),
                    'ctg_code': coa_mapping.get('ctg_code'),
                    'cafl_fnfl': coa_mapping.get('cafl_fnfl'),
                    'cat_5': coa_mapping.get('cat_5')
                }
                
                # Track if any record was inserted for this row
                row_inserted = False
                
                # If user selected "Yes" (newCompany == 1), also push Opening column into final_structured
                # as a separate row with month = 'Opening'
                if new_company == 1 and opening_amount is not None and opening_type is not None:
                    try:
                        opening_data = base_data.copy()
                        opening_data['amt_tb_lc'] = calculate_amt_tb_lc(opening_amount, opening_type)
                        opening_data['month'] = 'Opening'
                        
                        result = insert_structured_data(opening_data, inserted_keys_set)
                        if result is not None:
                            records_inserted += 1
                            final_structured_inserted += 1
                            row_inserted = True
                            if index < 5:
                                print(f"✅ Inserted Opening record for: {particular} (Amount: {opening_data['amt_tb_lc']}, ID: {result})")
                    except Exception as insert_error:
                        error_msg = f"Error inserting Opening record for {particular}: {str(insert_error)}"
                        print(f"❌ {error_msg}")
                        errors.append(error_msg)
                
                # Always insert Transaction data (if present) as the main month row
                if transaction_amount is not None and transaction_type is not None:
                    try:
                        transaction_data = base_data.copy()
                        transaction_data['amt_tb_lc'] = calculate_amt_tb_lc(transaction_amount, transaction_type)
                        transaction_data['month'] = month_details['month_name']
                        
                        result = insert_structured_data(transaction_data, inserted_keys_set)
                        if result is not None:  # Only increment if actually inserted (not duplicate)
                            records_inserted += 1
                            final_structured_inserted += 1
                            row_inserted = True
                            if index < 5:  # Only log first few for debugging
                                print(f"✅ Inserted Transaction record for: {particular} (Amount: {transaction_data['amt_tb_lc']}, ID: {result})")
                        else:
                            records_duplicate_skipped += 1
                            if index < 5:
                                print(f"⚠️ Transaction record was NOT inserted (duplicate or error): {particular} (Amount: {transaction_data['amt_tb_lc']})")
                    except Exception as insert_error:
                        error_msg = f"Error inserting Transaction record for {particular}: {str(insert_error)}"
                        print(f"❌ {error_msg}")
                        errors.append(error_msg)
                
                # If neither Opening (for new company) nor Transaction has data, skip this row
                if not row_inserted and transaction_amount is None and (new_company != 1 or opening_amount is None):
                    records_skipped += 1
                    if index < 3:
                        print(f"⏭️ Skipped row {index + 1} - No Opening/Transaction data to insert")
                    
                # Update progress tracker
                processed_rows = index + 1
                total_rows = len(df) if len(df) > 0 else 1
                progress_pct = int((processed_rows / total_rows) * 100)
                update_progress(
                    operation_id,
                    processed_rows=processed_rows,
                    total_rows=total_rows,
                    progress=progress_pct,
                    message=f'Processed {processed_rows}/{total_rows} rows'
                )
                    
            except Exception as row_error:
                error_msg = f"Error processing row {index + 1} ({particular if 'particular' in locals() else 'unknown'}): {str(row_error)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                traceback.print_exc()
                continue
        
        # After all inserts, first run a hard de-duplication for this entity/month/year
        dedupe_result = deduplicate_final_structured_for_entity_month_year(
            entity_code=entity_details['ent_code'],
            month_name=month_details['month_name'],
            year=month_details['year']
        )
        print(f"📊 De-duplication result: {dedupe_result}")

        # Then calculate and save forex rates for rows with mainCategory
        if records_inserted > 0:
            try:
                print(f"\n{'='*60}")
                print(f"💱 Calculating forex rates for newly inserted rows with mainCategory...")
                print(f"{'='*60}")
                
                # Get all rows for this entity/month/year that have mainCategory (after de-duplication)
                new_rows_query = """
                    SELECT sl_no, Particular, mainCategory, category1, localCurrencyCode, Avg_Fx_Rt, transactionAmount
                    FROM final_structured
                    WHERE entityCode = %s AND selectedMonth = %s AND Year = %s
                    AND mainCategory IS NOT NULL AND TRIM(mainCategory) != ''
                    AND (Avg_Fx_Rt IS NULL OR Avg_Fx_Rt = '')
                """
                new_rows = Database.execute_query(
                    new_rows_query,
                    params=[entity_details['ent_code'], month_details['month_name'], month_details['year']],
                    fetch_all=True
                )
                
                if new_rows:
                    # Import forex calculation function
                    from routes.structure_data import _build_forex_cache, _calculate_and_save_forex_rates
                    
                    # Build forex cache
                    forex_cache = _build_forex_cache(new_rows)
                    
                    # Calculate and save forex rates
                    fx_calculated_count = _calculate_and_save_forex_rates(new_rows, forex_cache, save_to_db=True)
                    print(f"✅ Calculated and saved forex rates for {fx_calculated_count} row(s) with mainCategory (after de-duplication)")
                else:
                    print(f"ℹ️ No rows found needing forex calculation (all may already have rates or no mainCategory)")
                
                print(f"{'='*60}\n")
            except Exception as fx_error:
                print(f"⚠️ Error calculating forex rates after upload: {str(fx_error)}")
                traceback.print_exc()
                # Don't fail the upload if forex calculation fails
        
        # Prepare response
        message = f'File processed successfully. {records_inserted} records inserted, {records_skipped} rows skipped.'
        if records_duplicate_skipped > 0:
            message += f' {records_duplicate_skipped} duplicate records skipped.'
        if records_without_coa > 0:
            message += f' {records_without_coa} records processed without COA mapping (this is normal for new entries).'
        
        response_data = {
            'success': True,
            'message': message,
            'data': {
                'filename': file.filename,
                'operation_id': operation_id,
                'records_inserted': records_inserted,
                'records_skipped': records_skipped,
                'records_duplicate_skipped': records_duplicate_skipped,
                'records_without_coa': records_without_coa,
                'total_rows': len(df),
                'entity': entity_details['ent_name'],
                'month': month_details['month_name'],
                'year': month_details['year'],
                's3_url': s3_doc_link if s3_doc_link else None,
                'uploaded_to_s3': bool(s3_doc_link)
            }
        }
        
        # Verify actual counts in database and log summary
        try:
            # Count rawData records
            raw_data_count_query = """
                SELECT COUNT(*) as count
                FROM `rawData`
                WHERE `EntityID` = %s AND `Month` = %s AND `Year` = %s
            """
            raw_data_count_result = Database.execute_query(
                raw_data_count_query,
                params=[int(ent_id), month_details['month_name'], month_details['year']],
                fetch_one=True
            )
            actual_raw_data_count = raw_data_count_result.get('count', 0) if raw_data_count_result else 0
            
            # Count final_structured records
            final_structured_count_query = """
                SELECT COUNT(*) as count
                FROM `final_structured`
                WHERE LOWER(TRIM(`entityCode`)) = LOWER(TRIM(%s))
                  AND LOWER(TRIM(`selectedMonth`)) = LOWER(TRIM(%s))
                  AND `Year` = %s
            """
            final_structured_count_result = Database.execute_query(
                final_structured_count_query,
                params=[entity_details['ent_code'], month_details['month_name'], month_details['year']],
                fetch_one=True
            )
            actual_final_structured_count = final_structured_count_result.get('count', 0) if final_structured_count_result else 0
            
            print(f"\n{'='*60}")
            print(f"📊 UPLOAD SUMMARY")
            print(f"{'='*60}")
            print(f"   Total rows in Excel: {len(df)}")
            print(f"   Records inserted (counted): {records_inserted}")
            print(f"   Rows skipped (no data): {records_skipped}")
            print(f"   Duplicates skipped: {records_duplicate_skipped}")
            print(f"   Records without COA: {records_without_coa}")
            print(f"   Errors: {len(errors)}")
            print(f"   Unique records tracked in batch: {len(inserted_keys_set)}")
            print(f"\n   📊 DATABASE ACTUAL COUNTS:")
            print(f"   rawData table: {actual_raw_data_count} records (we inserted: {raw_data_inserted})")
            print(f"   final_structured table: {actual_final_structured_count} records (we inserted: {final_structured_inserted})")
            
            # Check for duplicates in final_structured
            if actual_final_structured_count > final_structured_inserted:
                print(f"\n   ⚠️ WARNING: More records in DB than we inserted!")
                print(f"   Difference: {actual_final_structured_count - final_structured_inserted} extra records")
                
                # Find duplicate records
                duplicate_check_query = """
                    SELECT 
                        Particular,
                        entityCode,
                        selectedMonth,
                        Year,
                        Month,
                        transactionAmount,
                        COUNT(*) as duplicate_count
                    FROM final_structured
                    WHERE LOWER(TRIM(`entityCode`)) = LOWER(TRIM(%s))
                      AND LOWER(TRIM(`selectedMonth`)) = LOWER(TRIM(%s))
                      AND `Year` = %s
                    GROUP BY 
                        LOWER(TRIM(Particular)),
                        LOWER(TRIM(entityCode)),
                        LOWER(TRIM(selectedMonth)),
                        Year,
                        LOWER(TRIM(Month)),
                        transactionAmount
                    HAVING COUNT(*) > 1
                    LIMIT 10
                """
                duplicates = Database.execute_query(
                    duplicate_check_query,
                    params=[entity_details['ent_code'], month_details['month_name'], month_details['year']],
                    fetch_all=True
                )
                if duplicates:
                    print(f"\n   🔍 Found {len(duplicates)} sets of duplicate records:")
                    for dup in duplicates:
                        print(f"      - {dup.get('Particular')} | {dup.get('Month')} | Amount: {dup.get('transactionAmount')} | Count: {dup.get('duplicate_count')}")
            
            print(f"{'='*60}\n")
        except Exception as count_err:
            print(f"⚠️ Error counting database records: {str(count_err)}")
            traceback.print_exc()
            # Still print basic summary
            print(f"\n{'='*60}")
            print(f"📊 UPLOAD SUMMARY (basic)")
            print(f"{'='*60}")
            print(f"   Total rows in Excel: {len(df)}")
            print(f"   Records inserted: {records_inserted}")
            print(f"   Rows skipped: {records_skipped}")
            print(f"   Duplicates skipped: {records_duplicate_skipped}")
            print(f"   rawData inserted: {raw_data_inserted}")
            print(f"   final_structured inserted: {final_structured_inserted}")
            print(f"{'='*60}\n")
        
        if errors:
            response_data['warnings'] = errors
        
        update_progress(
            operation_id,
            status='completed',
            progress=100,
            message='Processing complete',
            processed_rows=len(df),
            total_rows=len(df),
            meta={**(get_progress(operation_id).get('meta', {}) if get_progress(operation_id) else {}), 'records_inserted': records_inserted}
        )

        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error uploading file: {str(e)}")
        traceback.print_exc()
        update_progress(
            operation_id or 'unknown',
            status='failed',
            message=str(e)
        )
        return jsonify({
            'success': False,
            'message': f'An error occurred while uploading file: {str(e)}',
            'operation_id': operation_id
        }), 500
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"🧹 Cleaned up temporary file: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Error cleaning up temporary file: {str(cleanup_error)}")

