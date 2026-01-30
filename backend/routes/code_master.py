"""
Code Master routes for managing code_master table
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request, get_jwt_identity
import traceback
import uuid
from threading import Lock
import pandas as pd
import os
import tempfile
from datetime import datetime

from database import Database

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

code_master_bp = Blueprint('code_master', __name__)


@code_master_bp.route('/code-master', methods=['GET', 'OPTIONS'])
def list_codes():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        query = """
            SELECT 
                code_id,
                RawParticulars,
                mainCategory,
                category1,
                category2,
                category3,
                category4,
                category5
            FROM code_master
            ORDER BY code_id DESC
        """
        rows = Database.execute_query(query, fetch_all=True)
        return jsonify({'success': True, 'data': {'codes': rows or []}}), 200
    except Exception as e:
        print(f"❌ Error fetching code master: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch code master'}), 500


@code_master_bp.route('/code-master', methods=['POST'])
def create_code():
    """Create a new code master entry with manual JWT verification"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Manual JWT verification with better error handling
        auth_header = request.headers.get('Authorization', 'NOT SET')
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED for code-master POST")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            print(f"   Authorization header present: {auth_header != 'NOT SET'}")
            if auth_header != 'NOT SET':
                print(f"   Authorization header preview: {auth_header[:50]}...")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type
            }), 401
        
        payload = request.get_json(silent=True) or {}
        print(f"📥 Received payload: {payload}")
        
        RawParticulars = (payload.get('RawParticulars') or '').strip()
        mainCategory = (payload.get('mainCategory') or payload.get('standardizedCode') or '').strip()  # Support both for backward compatibility
        category1 = (payload.get('category1') or '').strip()
        category2 = (payload.get('category2') or '').strip()
        category3 = (payload.get('category3') or '').strip()
        category4 = (payload.get('category4') or '').strip()
        category5 = (payload.get('category5') or '').strip()

        if not RawParticulars or not mainCategory:
            return jsonify({'success': False, 'message': 'RawParticulars and mainCategory are required'}), 400

        print(f"📝 Attempting to upsert code: RawParticulars={RawParticulars}, mainCategory={mainCategory}, category1={category1}")

        # Use INSERT ... ON DUPLICATE KEY UPDATE to update existing records instead of creating duplicates
        upsert = """
            INSERT INTO code_master
            (RawParticulars, mainCategory, category1, category2, category3, category4, category5)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                mainCategory = VALUES(mainCategory),
                category1 = VALUES(category1),
                category2 = VALUES(category2),
                category3 = VALUES(category3),
                category4 = VALUES(category4),
                category5 = VALUES(category5)
        """
        params = [RawParticulars, mainCategory, category1 or None, category2 or None, category3 or None, category4 or None, category5 or None]
        result_id = Database.execute_query(upsert, params=params)
        print(f"✅ Upsert successful, result_id={result_id}")

        # Get the record (either newly inserted or updated)
        get_q = """
            SELECT code_id, RawParticulars, mainCategory, category1, category2, category3, category4, category5
            FROM code_master WHERE RawParticulars = %s
        """
        created = Database.execute_query(get_q, params=[RawParticulars], fetch_one=True)

        print(f"✅ Code saved successfully: {created}")
        return jsonify({'success': True, 'message': 'Code saved successfully', 'data': created}), 200
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error creating code: {error_type}: {error_msg}")
        traceback.print_exc()
        # Return more detailed error message
        return jsonify({
            'success': False, 
            'message': f'Failed to create code: {error_msg}',
            'error_type': error_type
        }), 500


@code_master_bp.route('/code-master/<int:code_id>', methods=['GET', 'OPTIONS'])
def get_code_by_id(code_id):
    """Get code master entry by code_id"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT 
                code_id,
                RawParticulars,
                mainCategory,
                category1,
                category2,
                category3,
                category4,
                category5
            FROM code_master
            WHERE code_id = %s
        """
        result = Database.execute_query(query, params=[code_id], fetch_one=True)
        
        if result:
            return jsonify({'success': True, 'data': result}), 200
        else:
            return jsonify({'success': False, 'message': 'Code not found'}), 404
    except Exception as e:
        print(f"❌ Error fetching code by id: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch code'}), 500


@code_master_bp.route('/code-master/<int:code_id>', methods=['PUT', 'OPTIONS'])
def update_code(code_id):
    """Update an existing code master entry"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Manual JWT verification
        auth_header = request.headers.get('Authorization', 'NOT SET')
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED for code-master PUT")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type
            }), 401
        
        payload = request.get_json(silent=True) or {}
        print(f"📥 Received update payload for code_id={code_id}: {payload}")
        
        # Check if code exists
        check_query = "SELECT code_id FROM code_master WHERE code_id = %s"
        existing = Database.execute_query(check_query, params=[code_id], fetch_one=True)
        if not existing:
            return jsonify({'success': False, 'message': 'Code not found'}), 404
        
        RawParticulars = (payload.get('RawParticulars') or '').strip()
        mainCategory = (payload.get('mainCategory') or '').strip()
        category1 = (payload.get('category1') or '').strip() or None
        category2 = (payload.get('category2') or '').strip() or None
        category3 = (payload.get('category3') or '').strip() or None
        category4 = (payload.get('category4') or '').strip() or None
        category5 = (payload.get('category5') or '').strip() or None

        if not RawParticulars or not mainCategory:
            return jsonify({'success': False, 'message': 'RawParticulars and mainCategory are required'}), 400

        print(f"📝 Updating code_id={code_id}: RawParticulars={RawParticulars}, mainCategory={mainCategory}")

        # Update the record
        update_query = """
            UPDATE code_master
            SET RawParticulars = %s,
                mainCategory = %s,
                category1 = %s,
                category2 = %s,
                category3 = %s,
                category4 = %s,
                category5 = %s
            WHERE code_id = %s
        """
        params = [RawParticulars, mainCategory, category1, category2, category3, category4, category5, code_id]
        Database.execute_query(update_query, params=params)

        # Get the updated record
        get_q = """
            SELECT code_id, RawParticulars, mainCategory, category1, category2, category3, category4, category5
            FROM code_master WHERE code_id = %s
        """
        updated = Database.execute_query(get_q, params=[code_id], fetch_one=True)

        print(f"✅ Code updated successfully: {updated}")
        return jsonify({'success': True, 'message': 'Code updated successfully', 'data': updated}), 200
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error updating code: {error_type}: {error_msg}")
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Failed to update code: {error_msg}',
            'error_type': error_type
        }), 500


@code_master_bp.route('/code-master/<int:code_id>', methods=['DELETE', 'OPTIONS'])
def delete_code(code_id):
    """Delete a code master entry"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Manual JWT verification
        auth_header = request.headers.get('Authorization', 'NOT SET')
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED for code-master DELETE")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type
            }), 401
        
        # Check if code exists
        check_query = "SELECT code_id, RawParticulars FROM code_master WHERE code_id = %s"
        existing = Database.execute_query(check_query, params=[code_id], fetch_one=True)
        if not existing:
            return jsonify({'success': False, 'message': 'Code not found'}), 404
        
        print(f"🗑️ Deleting code_id={code_id}: {existing.get('RawParticulars')}")

        # Delete the record
        delete_query = "DELETE FROM code_master WHERE code_id = %s"
        Database.execute_query(delete_query, params=[code_id])

        print(f"✅ Code deleted successfully: code_id={code_id}")
        return jsonify({'success': True, 'message': 'Code deleted successfully'}), 200
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error deleting code: {error_type}: {error_msg}")
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Failed to delete code: {error_msg}',
            'error_type': error_type
        }), 500


@code_master_bp.route('/code-master/by-particular', methods=['GET', 'OPTIONS'])
def get_code_by_particular():
    """Get code master entry by RawParticulars (case-insensitive match)"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        particular = request.args.get('particular', '').strip()
        if not particular:
            return jsonify({'success': False, 'message': 'particular parameter is required'}), 400
        
        query = """
            SELECT 
                code_id,
                RawParticulars,
                mainCategory,
                category1,
                category2,
                category3,
                category4,
                category5
            FROM code_master
            WHERE LOWER(TRIM(RawParticulars)) = LOWER(TRIM(%s))
            ORDER BY code_id DESC
            LIMIT 1
        """
        result = Database.execute_query(query, params=[particular], fetch_one=True)
        
        if result:
            return jsonify({'success': True, 'data': result}), 200
        else:
            return jsonify({'success': True, 'data': None}), 200
    except Exception as e:
        print(f"❌ Error fetching code by particular: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch code'}), 500


@code_master_bp.route('/code-master/test-categories', methods=['GET', 'OPTIONS'])
def test_categories():
    """Test endpoint to check what category data exists in final_structured"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Try to get sample data from final_structured to see what columns exist
        query = """
            SELECT 
                category1,
                category2,
                category3,
                category4,
                category5,
                Particular
            FROM final_structured
            WHERE category1 IS NOT NULL 
            LIMIT 10
        """
        results = Database.execute_query(query, fetch_all=True)
        
        # Also get distinct values for category1
        distinct_query = """
            SELECT DISTINCT category1
            FROM final_structured
            WHERE category1 IS NOT NULL 
            AND TRIM(category1) != ''
        """
        distinct_results = Database.execute_query(distinct_query, fetch_all=True)
        
        print(f"✅ Test query results: {len(results) if results else 0} rows, {len(distinct_results) if distinct_results else 0} distinct category1 values")
        
        return jsonify({
            'success': True,
            'data': {
                'sample_rows': results or [],
                'distinct_category1': distinct_results or [],
                'count': len(results) if results else 0
            }
        }), 200
    except Exception as e:
        print(f"❌ Error in test query: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@code_master_bp.route('/code-master/unique-values', methods=['GET', 'OPTIONS'])
def get_unique_values():
    """Get unique values for mainCategory and all category fields from both code_master and final_structured tables"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        field = request.args.get('field', '').strip().lower()
        
        print(f"📊 Fetching unique values for field: '{field}'")
        
        if not field:
            return jsonify({'success': False, 'message': 'field parameter is required'}), 400
        
        # Map field names to column names in code_master and corresponding columns in final_structured
        field_map = {
            'maincategory': {
                'code_master': 'mainCategory',
                'final_structured': 'mainCategory'
            },
            'standardizedcode': {  # Support old name for backward compatibility
                'code_master': 'mainCategory',
                'final_structured': 'mainCategory'
            },
            'category1': {
                'code_master': 'category1',
                'final_structured': 'category1'
            },
            'category2': {
                'code_master': 'category2',
                'final_structured': 'category2'
            },
            'category3': {
                'code_master': 'category3',
                'final_structured': 'category3'
            },
            'category4': {
                'code_master': 'category4',
                'final_structured': 'category4'
            },
            'category5': {
                'code_master': 'category5',
                'final_structured': 'category5'
            },
        }
        
        column_map = field_map.get(field)
        if not column_map:
            print(f"⚠️ Invalid field '{field}' - not found in field_map")
            return jsonify({'success': False, 'message': f'Invalid field: {field}'}), 400
        
        code_master_col = column_map.get('code_master')
        final_structured_col = column_map.get('final_structured')
        
        print(f"   Mapped to: code_master.{code_master_col}, final_structured.{final_structured_col}")
        
        # Validate column names against whitelist to prevent SQL injection
        allowed_code_master_cols = ['mainCategory', 'category1', 'category2', 'category3', 'category4', 'category5']
        allowed_final_structured_cols = ['mainCategory', 'category1', 'category2', 'category3', 'category4', 'category5']
        
        if code_master_col not in allowed_code_master_cols or final_structured_col not in allowed_final_structured_cols:
            print(f"⚠️ Column validation failed")
            return jsonify({'success': False, 'message': f'Invalid field: {field}'}), 400
        
        values_set = set()
        
        # Get values from code_master table
        try:
            query_cm = f"""
                SELECT DISTINCT TRIM({code_master_col}) as value
                FROM code_master
                WHERE {code_master_col} IS NOT NULL 
                AND TRIM({code_master_col}) != ''
                AND {code_master_col} != ''
            """
            print(f"   Executing code_master query: {query_cm}")
            results_cm = Database.execute_query(query_cm, fetch_all=True)
            print(f"   Found {len(results_cm) if results_cm else 0} unique values from code_master")
            if results_cm:
                for row in results_cm:
                    val = row.get('value')
                    if val and str(val).strip():
                        values_set.add(str(val).strip())
        except Exception as cm_error:
            print(f"⚠️ Error querying code_master: {str(cm_error)}")
            # Continue to try final_structured even if code_master fails
        
        # Get values from final_structured table
        try:
            query_fs = f"""
                SELECT DISTINCT TRIM({final_structured_col}) as value
                FROM final_structured
                WHERE {final_structured_col} IS NOT NULL 
                AND TRIM({final_structured_col}) != ''
                AND {final_structured_col} != ''
            """
            print(f"   Executing final_structured query: {query_fs}")
            results_fs = Database.execute_query(query_fs, fetch_all=True)
            print(f"   Found {len(results_fs) if results_fs else 0} unique values from final_structured")
            if results_fs:
                for row in results_fs:
                    val = row.get('value')
                    if val and str(val).strip():
                        clean_val = str(val).strip()
                        values_set.add(clean_val)
                        print(f"      -> Added value: '{clean_val}'")
        except Exception as fs_error:
            print(f"⚠️ Error querying final_structured: {str(fs_error)}")
            traceback.print_exc()
        
        # Convert set to sorted list
        values = sorted(list(values_set))
        
        print(f"✅ Fetched {len(values)} total unique values for field '{field}'")
        print(f"   Values: {values}")
        
        return jsonify({'success': True, 'data': {'values': values}}), 200
    except Exception as e:
        print(f"❌ Error fetching unique values: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Failed to fetch unique values: {str(e)}'}), 500


@code_master_bp.route('/code-master/upload', methods=['POST', 'OPTIONS'])
def upload_code_master_file():
    """Handle file upload and process Excel data to insert into code_master table"""
    temp_file_path = None
    operation_id = None
    
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        # Debug: Log request details
        print(f"\n{'='*60}")
        print(f"🔍 CODE MASTER UPLOAD REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"🔍 Request method: {request.method}")
        print(f"🔍 Content-Type: {request.content_type}")
        auth_header = request.headers.get('Authorization', 'NOT SET')
        print(f"🔍 Authorization header: {auth_header[:100] if auth_header != 'NOT SET' else 'NOT SET'}")
        print(f"🔍 Has files: {'file' in request.files}")
        print(f"{'='*60}\n")
        
        # Manual JWT verification
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED for code-master upload")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type
            }), 401
        
        # Accept optional client-provided operation id for progress tracking
        operation_id = request.form.get('operation_id') or str(uuid.uuid4())
        
        # Initialize progress tracker
        init_progress(operation_id, meta={'filename': None})
        update_progress(operation_id, status='validating', message='Validating request')
        
        # Check if file is in request
        if 'file' not in request.files:
            print(f"❌ No 'file' key in request.files")
            return jsonify({
                'success': False,
                'message': 'No file provided. Please select a file to upload.'
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
        
        # Save file temporarily
        try:
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"code_master_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file.save(temp_file_path)
            print(f"💾 Saved file temporarily: {temp_file_path}")
        except Exception as e:
            print(f"❌ Error saving temporary file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error saving file: {str(e)}'
            }), 500
        
        # Read Excel file
        file.seek(0)  # Reset file pointer to beginning
        try:
            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(file, engine='openpyxl', dtype=str, keep_default_na=False)
            print(f"📊 Read {len(df)} rows from Excel")
            
            # Display column names for debugging
            print(f"📋 Columns: {list(df.columns)}")
            
            # Expected columns (case-insensitive matching)
            expected_columns = {
                'RawParticulars': ['RawParticulars', 'Raw Particulars', 'Particular', 'particular'],
                'mainCategory': ['mainCategory', 'Main Category', 'main_category', 'MainCategory', 'standardizedCode', 'Standardized Code', 'standardized_code', 'StandardizedCode'],
                'category1': ['category1', 'Category 1', 'Category1'],
                'category2': ['category2', 'Category 2', 'Category2'],
                'category3': ['category3', 'Category 3', 'Category3'],
                'category4': ['category4', 'Category 4', 'Category4'],
                'category5': ['category5', 'Category 5', 'Category5']
            }
            
            # Map actual column names to expected names
            column_mapping = {}
            for expected_name, possible_names in expected_columns.items():
                for col in df.columns:
                    if col.strip() in possible_names or col.strip().lower() == expected_name.lower():
                        column_mapping[expected_name] = col
                        break
            
            print(f"📋 Column mapping: {column_mapping}")
            
            # Check required columns
            if 'RawParticulars' not in column_mapping:
                return jsonify({
                    'success': False,
                    'message': 'Required column "RawParticulars" not found in Excel file. Please ensure the file has this column.'
                }), 400
            
            if 'mainCategory' not in column_mapping:
                return jsonify({
                    'success': False,
                    'message': 'Required column "mainCategory" (or "standardizedCode") not found in Excel file. Please ensure the file has this column.'
                }), 400
            
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
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error reading Excel file: {str(e)}'
            }), 400
        
        # Process each row
        records_inserted = 0
        records_updated = 0
        records_skipped = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Get values from mapped columns
                raw_particulars = str(row[column_mapping['RawParticulars']]).strip() if column_mapping.get('RawParticulars') else None
                main_category = str(row[column_mapping['mainCategory']]).strip() if column_mapping.get('mainCategory') else None
                
                # Skip if required fields are empty
                if not raw_particulars or not main_category or raw_particulars == '' or main_category == '':
                    records_skipped += 1
                    if index < 3:
                        print(f"⏭️ Skipped row {index + 1} - Missing required fields")
                    continue
                
                # Get optional category fields
                category1 = str(row[column_mapping['category1']]).strip() if column_mapping.get('category1') and pd.notna(row.get(column_mapping['category1'])) else None
                category2 = str(row[column_mapping['category2']]).strip() if column_mapping.get('category2') and pd.notna(row.get(column_mapping['category2'])) else None
                category3 = str(row[column_mapping['category3']]).strip() if column_mapping.get('category3') and pd.notna(row.get(column_mapping['category3'])) else None
                category4 = str(row[column_mapping['category4']]).strip() if column_mapping.get('category4') and pd.notna(row.get(column_mapping['category4'])) else None
                category5 = str(row[column_mapping['category5']]).strip() if column_mapping.get('category5') and pd.notna(row.get(column_mapping['category5'])) else None
                
                # Clean empty strings to None
                category1 = category1 if category1 and category1 != '' else None
                category2 = category2 if category2 and category2 != '' else None
                category3 = category3 if category3 and category3 != '' else None
                category4 = category4 if category4 and category4 != '' else None
                category5 = category5 if category5 and category5 != '' else None
                
                # Check if record already exists
                check_query = """
                    SELECT code_id FROM code_master 
                    WHERE RawParticulars = %s
                """
                existing = Database.execute_query(check_query, params=[raw_particulars], fetch_one=True)
                is_update = existing is not None
                
                # Insert/update code master record
                try:
                    upsert = """
                        INSERT INTO code_master
                        (RawParticulars, mainCategory, category1, category2, category3, category4, category5)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            mainCategory = VALUES(mainCategory),
                            category1 = VALUES(category1),
                            category2 = VALUES(category2),
                            category3 = VALUES(category3),
                            category4 = VALUES(category4),
                            category5 = VALUES(category5)
                    """
                    params = [raw_particulars, main_category, category1, category2, category3, category4, category5]
                    Database.execute_query(upsert, params=params)
                    
                    if is_update:
                        records_updated += 1
                        if index < 5:
                            print(f"✅ Updated code: {raw_particulars} -> {main_category}")
                    else:
                        records_inserted += 1
                        if index < 5:
                            print(f"✅ Inserted code: {raw_particulars} -> {main_category}")
                            
                except Exception as db_error:
                    error_msg = f"Error inserting/updating code for '{raw_particulars}': {str(db_error)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    records_skipped += 1
                
                # Update progress
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
                error_msg = f"Error processing row {index + 1}: {str(row_error)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                traceback.print_exc()
                records_skipped += 1
                continue
        
        # Prepare response
        message = f'File processed successfully. {records_inserted} records inserted, {records_updated} records updated, {records_skipped} rows skipped.'
        
        response_data = {
            'success': True,
            'message': message,
            'data': {
                'filename': file.filename,
                'operation_id': operation_id,
                'records_inserted': records_inserted,
                'records_updated': records_updated,
                'records_skipped': records_skipped,
                'total_rows': len(df)
            }
        }
        
        if errors:
            response_data['warnings'] = errors[:10]  # Limit warnings to first 10
        
        print(f"\n✅ Processing Summary:")
        print(f"   Total rows: {len(df)}")
        print(f"   Records inserted: {records_inserted}")
        print(f"   Records updated: {records_updated}")
        print(f"   Rows skipped: {records_skipped}")
        print(f"   Errors: {len(errors)}")
        
        update_progress(
            operation_id,
            status='completed',
            progress=100,
            message='Processing complete',
            processed_rows=len(df),
            total_rows=len(df),
            meta={**(get_progress(operation_id).get('meta', {}) if get_progress(operation_id) else {}), 
                  'records_inserted': records_inserted, 'records_updated': records_updated}
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


@code_master_bp.route('/code-master/upload/progress/<operation_id>', methods=['GET', 'OPTIONS'])
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


@code_master_bp.route('/code-master/delete-all', methods=['DELETE', 'OPTIONS'])
def delete_all_codes():
    """Delete all records from code_master table"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Manual JWT verification
        auth_header = request.headers.get('Authorization', 'NOT SET')
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user_id = str(current_user_id) if current_user_id else 'default-user'
            print(f"✅ User authenticated: {user_id}")
        except Exception as jwt_error:
            error_type = type(jwt_error).__name__
            error_msg = str(jwt_error)
            print(f"\n❌ JWT VALIDATION FAILED for code-master DELETE ALL")
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg}")
            traceback.print_exc()
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': False,
                'message': 'Authentication failed. Please login again.',
                'error': error_msg,
                'error_type': error_type
            }), 401
        
        # Get count before deletion
        count_query = "SELECT COUNT(*) as count FROM code_master"
        count_result = Database.execute_query(count_query, fetch_one=True)
        total_count = count_result.get('count', 0) if count_result else 0
        
        if total_count == 0:
            return jsonify({
                'success': True,
                'message': 'No records to delete',
                'data': {'deleted_count': 0}
            }), 200
        
        # Delete all records
        delete_query = "DELETE FROM code_master"
        Database.execute_query(delete_query)
        
        print(f"✅ Deleted all {total_count} records from code_master table")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted all {total_count} record(s) from code_master',
            'data': {'deleted_count': total_count}
        }), 200
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error deleting all codes: {error_type}: {error_msg}")
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Failed to delete all codes: {error_msg}',
            'error_type': error_type
        }), 500





