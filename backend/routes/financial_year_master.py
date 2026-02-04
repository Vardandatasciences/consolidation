"""
Financial Year Master routes for managing financial_year_master table
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback
from datetime import datetime, date

from database import Database

financial_year_master_bp = Blueprint('financial_year_master', __name__)


def validate_date_against_fy_master(check_date):
    """
    Validate if a date falls within any active financial year range.
    
    Args:
        check_date: date object or string in format 'YYYY-MM-DD'
    
    Returns:
        dict: {
            'valid': bool,
            'financial_year': str or None,
            'message': str
        }
    """
    try:
        # Convert string to date if needed
        if isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        elif isinstance(check_date, datetime):
            check_date = check_date.date()
        
        query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date
            FROM financial_year_master
            WHERE is_active = 1
              AND %s >= start_date
              AND %s <= end_date
            LIMIT 1
        """
        result = Database.execute_query(query, params=[check_date, check_date], fetch_one=True)
        
        if result:
            return {
                'valid': True,
                'financial_year': result.get('financial_year'),
                'id': result.get('id'),
                'message': f"Date falls within FY {result.get('financial_year')}"
            }
        else:
            return {
                'valid': False,
                'financial_year': None,
                'message': f"Date {check_date} falls outside configured financial year ranges"
            }
    except Exception as e:
        print(f"❌ Error validating date against FY master: {str(e)}")
        return {
            'valid': False,
            'financial_year': None,
            'message': f"Error validating date: {str(e)}"
        }


def check_if_previous_fy(check_date):
    """
    Check if a date falls before any configured active financial year.
    This helps identify when user tries to upload data for a previous FY that hasn't been configured.
    
    Args:
        check_date: date object or string in format 'YYYY-MM-DD'
    
    Returns:
        dict: {
            'is_previous': bool,
            'suggested_fy': str or None,  # Suggested FY format like "2024-25"
            'message': str
        }
    """
    try:
        # Convert string to date if needed
        if isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        elif isinstance(check_date, datetime):
            check_date = check_date.date()
        
        # Get the earliest active financial year
        query = """
            SELECT 
                financial_year,
                start_date,
                end_date
            FROM financial_year_master
            WHERE is_active = 1
            ORDER BY start_date ASC
            LIMIT 1
        """
        earliest_fy = Database.execute_query(query, fetch_one=True)
        
        if not earliest_fy:
            # No financial years configured at all
            # Calculate suggested FY from the check_date
            year = check_date.year
            month = check_date.month
            # If month is Jan-Mar, FY is previous year
            if month <= 3:
                ending_year = year
                suggested_fy = f"{year-1}-{str(year)[-2:]}"
            else:
                ending_year = year + 1
                suggested_fy = f"{year}-{str(year+1)[-2:]}"
            
            return {
                'is_previous': True,
                'suggested_fy': suggested_fy,
                'message': f'No financial years configured. Please configure FY {suggested_fy} first.'
            }
        
        earliest_start = earliest_fy.get('start_date')
        if isinstance(earliest_start, str):
            earliest_start = datetime.strptime(earliest_start, '%Y-%m-%d').date()
        
        # Check if check_date is before the earliest configured FY
        if check_date < earliest_start:
            # Calculate suggested FY from the check_date
            year = check_date.year
            month = check_date.month
            # If month is Jan-Mar, FY is previous year
            if month <= 3:
                ending_year = year
                suggested_fy = f"{year-1}-{str(year)[-2:]}"
            else:
                ending_year = year + 1
                suggested_fy = f"{year}-{str(year+1)[-2:]}"
            
            return {
                'is_previous': True,
                'suggested_fy': suggested_fy,
                'message': f'Date {check_date} is before any configured financial year. Please configure FY {suggested_fy} first.'
            }
        else:
            return {
                'is_previous': False,
                'suggested_fy': None,
                'message': 'Date is not before configured financial years'
            }
    except Exception as e:
        print(f"❌ Error checking if previous FY: {str(e)}")
        return {
            'is_previous': False,
            'suggested_fy': None,
            'message': f"Error checking: {str(e)}"
        }


def get_current_financial_year():
    """
    Get the current active financial year based on today's date.
    Returns the financial year that today's date falls within.
    
    Returns:
        dict: {
            'financial_year': str or None,  # e.g., "2025-26"
            'id': int or None,
            'start_date': date or None,
            'end_date': date or None,
            'found': bool
        }
    """
    try:
        today = date.today()
        
        query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date
            FROM financial_year_master
            WHERE is_active = 1
              AND %s >= start_date
              AND %s <= end_date
            LIMIT 1
        """
        result = Database.execute_query(query, params=[today, today], fetch_one=True)
        
        if result:
            return {
                'financial_year': result.get('financial_year'),
                'id': result.get('id'),
                'start_date': result.get('start_date'),
                'end_date': result.get('end_date'),
                'found': True
            }
        else:
            return {
                'financial_year': None,
                'id': None,
                'start_date': None,
                'end_date': None,
                'found': False
            }
    except Exception as e:
        print(f"❌ Error getting current financial year: {str(e)}")
        return {
            'financial_year': None,
            'id': None,
            'start_date': None,
            'end_date': None,
            'found': False
        }


def check_overlapping_dates(start_date, end_date, exclude_id=None):
    """
    Check if date range overlaps with any existing active financial year.
    
    Args:
        start_date: date object
        end_date: date object
        exclude_id: int or None - ID to exclude from check (for updates)
    
    Returns:
        dict: {
            'overlaps': bool,
            'overlapping_fy': str or None,
            'message': str
        }
    """
    try:
        # Convert strings to dates if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Validate end_date > start_date
        if end_date <= start_date:
            return {
                'overlaps': True,
                'overlapping_fy': None,
                'message': 'End date must be after start date'
            }
        
        query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date
            FROM financial_year_master
            WHERE is_active = 1
              AND id != COALESCE(%s, 0)
              AND (
                (%s BETWEEN start_date AND end_date)
                OR (%s BETWEEN start_date AND end_date)
                OR (start_date BETWEEN %s AND %s)
                OR (end_date BETWEEN %s AND %s)
              )
            LIMIT 1
        """
        result = Database.execute_query(
            query,
            params=[exclude_id, start_date, end_date, start_date, end_date, start_date, end_date],
            fetch_one=True
        )
        
        if result:
            return {
                'overlaps': True,
                'overlapping_fy': result.get('financial_year'),
                'message': f"Date range overlaps with existing FY {result.get('financial_year')}"
            }
        else:
            return {
                'overlaps': False,
                'overlapping_fy': None,
                'message': 'No overlap found'
            }
    except Exception as e:
        print(f"❌ Error checking overlapping dates: {str(e)}")
        return {
            'overlaps': True,
            'overlapping_fy': None,
            'message': f"Error checking overlaps: {str(e)}"
        }


@financial_year_master_bp.route('/financial-year-master', methods=['GET', 'OPTIONS'])
def list_financial_years():
    """List all financial years, optionally filtered by is_active"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        is_active = request.args.get('is_active', type=str)
        
        # Build query
        where_clause = ""
        params = []
        
        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            where_clause = "WHERE is_active = %s"
            params.append(1 if is_active_bool else 0)
        
        query = f"""
            SELECT 
                id,
                financial_year,
                start_date,
                end_date,
                is_active,
                description,
                created_at,
                updated_at,
                created_by
            FROM financial_year_master
            {where_clause}
            ORDER BY start_date DESC
        """
        
        rows = Database.execute_query(query, params=params, fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'financial_years': rows
            }
        }), 200
    except Exception as e:
        print(f"❌ Error listing financial years: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch financial years'}), 500


@financial_year_master_bp.route('/financial-year-master/<int:fy_id>', methods=['GET', 'OPTIONS'])
def get_financial_year(fy_id):
    """Get a single financial year by ID"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date,
                is_active,
                description,
                created_at,
                updated_at,
                created_by
            FROM financial_year_master
            WHERE id = %s
        """
        result = Database.execute_query(query, params=[fy_id], fetch_one=True)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Financial year not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        print(f"❌ Error fetching financial year: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch financial year'}), 500


@financial_year_master_bp.route('/financial-year-master', methods=['POST'])
@jwt_required()
def create_financial_year():
    """Create a new financial year"""
    try:
        payload = request.get_json(silent=True) or {}
        financial_year = (payload.get('financial_year') or '').strip()
        start_date_str = payload.get('start_date')
        end_date_str = payload.get('end_date')
        is_active = payload.get('is_active', True)
        description = (payload.get('description') or '').strip()
        
        # Validate required fields
        if not financial_year or not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'message': 'financial_year, start_date, and end_date are required'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate end_date > start_date
        if end_date <= start_date:
            return jsonify({
                'success': False,
                'message': 'End date must be after start date'
            }), 400
        
        # Check for overlapping dates
        overlap_check = check_overlapping_dates(start_date, end_date)
        if overlap_check['overlaps']:
            return jsonify({
                'success': False,
                'message': overlap_check['message']
            }), 400
        
        # Check if financial_year already exists
        check_query = "SELECT id FROM financial_year_master WHERE financial_year = %s"
        existing = Database.execute_query(check_query, params=[financial_year], fetch_one=True)
        if existing:
            return jsonify({
                'success': False,
                'message': f'Financial year {financial_year} already exists'
            }), 400
        
        # Insert new record
        user_id = get_jwt_identity()
        insert_query = """
            INSERT INTO financial_year_master 
                (financial_year, start_date, end_date, is_active, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        Database.execute_query(insert_query, params=[
            financial_year, start_date, end_date, 1 if is_active else 0, 
            description if description else None, user_id
        ])
        
        # Fetch and return the created record
        get_query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date,
                is_active,
                description,
                created_at,
                updated_at,
                created_by
            FROM financial_year_master
            WHERE financial_year = %s
        """
        result = Database.execute_query(get_query, params=[financial_year], fetch_one=True)
        
        return jsonify({
            'success': True,
            'message': 'Financial year created successfully',
            'data': result
        }), 201
    except Exception as e:
        print(f"❌ Error creating financial year: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to create financial year'}), 500


@financial_year_master_bp.route('/financial-year-master/<int:fy_id>', methods=['PUT'])
@jwt_required()
def update_financial_year(fy_id):
    """Update an existing financial year"""
    try:
        payload = request.get_json(silent=True) or {}
        
        # Check if record exists
        check_query = "SELECT id FROM financial_year_master WHERE id = %s"
        existing = Database.execute_query(check_query, params=[fy_id], fetch_one=True)
        if not existing:
            return jsonify({
                'success': False,
                'message': 'Financial year not found'
            }), 404
        
        # Get current values
        current_query = """
            SELECT financial_year, start_date, end_date, is_active
            FROM financial_year_master
            WHERE id = %s
        """
        current = Database.execute_query(current_query, params=[fy_id], fetch_one=True)
        
        # Use provided values or keep current values
        financial_year = payload.get('financial_year', current.get('financial_year'))
        start_date_str = payload.get('start_date')
        end_date_str = payload.get('end_date')
        is_active = payload.get('is_active', current.get('is_active'))
        description = payload.get('description')
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        def parse_date(date_value):
            """Helper to parse date from various formats"""
            if not date_value:
                return None
            if isinstance(date_value, date):
                return date_value
            if isinstance(date_value, datetime):
                return date_value.date()
            if isinstance(date_value, str):
                # Try YYYY-MM-DD format first
                try:
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(date_value, fmt).date()
                        except ValueError:
                            continue
                    raise ValueError(f"Invalid date format: {date_value}. Use YYYY-MM-DD")
            return None
        
        if start_date_str:
            try:
                start_date = parse_date(start_date_str)
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid start_date format: {str(e)}'
                }), 400
        else:
            start_date = current.get('start_date')
            if start_date:
                start_date = parse_date(start_date)
        
        if end_date_str:
            try:
                end_date = parse_date(end_date_str)
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid end_date format: {str(e)}'
                }), 400
        else:
            end_date = current.get('end_date')
            if end_date:
                end_date = parse_date(end_date)
        
        # Validate end_date > start_date
        if end_date <= start_date:
            return jsonify({
                'success': False,
                'message': 'End date must be after start date'
            }), 400
        
        # Check for overlapping dates (exclude current record)
        overlap_check = check_overlapping_dates(start_date, end_date, exclude_id=fy_id)
        if overlap_check['overlaps']:
            return jsonify({
                'success': False,
                'message': overlap_check['message']
            }), 400
        
        # Update record
        update_query = """
            UPDATE financial_year_master
            SET financial_year = %s,
                start_date = %s,
                end_date = %s,
                is_active = %s,
                description = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        Database.execute_query(update_query, params=[
            financial_year, start_date, end_date, 1 if is_active else 0,
            description if description else None, fy_id
        ])
        
        # Fetch and return updated record
        get_query = """
            SELECT 
                id,
                financial_year,
                start_date,
                end_date,
                is_active,
                description,
                created_at,
                updated_at,
                created_by
            FROM financial_year_master
            WHERE id = %s
        """
        result = Database.execute_query(get_query, params=[fy_id], fetch_one=True)
        
        return jsonify({
            'success': True,
            'message': 'Financial year updated successfully',
            'data': result
        }), 200
    except Exception as e:
        print(f"❌ Error updating financial year: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to update financial year'}), 500


@financial_year_master_bp.route('/financial-year-master/<int:fy_id>', methods=['DELETE'])
@jwt_required()
def delete_financial_year(fy_id):
    """Delete a financial year (soft delete by setting is_active = 0)"""
    try:
        # Check if record exists
        check_query = "SELECT id, financial_year FROM financial_year_master WHERE id = %s"
        existing = Database.execute_query(check_query, params=[fy_id], fetch_one=True)
        if not existing:
            return jsonify({
                'success': False,
                'message': 'Financial year not found'
            }), 404
        
        financial_year = existing.get('financial_year')
        print(f"🗑️ Attempting to soft delete financial year ID {fy_id} ({financial_year})")
        
        # Optional: Check if any data exists for this financial year
        # This check is optional - we'll allow soft delete even if data exists
        # (soft delete just sets is_active=0, which is safe)
        structured_count = 0
        raw_count = 0
        try:
            # Try to check for data, but don't fail if tables/columns don't exist
            # Extract ending year from financial_year string (e.g., "2024-25" -> 2024)
            ending_year = None
            if financial_year and '-' in str(financial_year):
                try:
                    ending_year = int(str(financial_year).split('-')[0])
                except ValueError:
                    pass
            
            if ending_year:
                # Check using Year column (more likely to exist)
                check_data_query = """
                    SELECT 
                        COALESCE((SELECT COUNT(*) FROM final_structured WHERE Year = %s), 0) as structured_count,
                        COALESCE((SELECT COUNT(*) FROM `rawData` WHERE Year = %s), 0) as raw_count
                """
                try:
                    data_check = Database.execute_query(check_data_query, params=[ending_year, ending_year], fetch_one=True)
                    if data_check:
                        structured_count = data_check.get('structured_count', 0) or 0
                        raw_count = data_check.get('raw_count', 0) or 0
                        print(f"📊 Found {structured_count} structured records and {raw_count} raw records for FY {financial_year}")
                except Exception as query_error:
                    # If query fails, just continue (allow deletion)
                    print(f"⚠️ Could not check for existing data (non-blocking): {str(query_error)}")
                    pass
        except Exception as check_error:
            # If check fails, log but don't block deletion (allow soft delete)
            print(f"⚠️ Warning: Could not check for existing data: {str(check_error)}")
            pass
        
        # Note: We allow soft delete even if data exists, as it's just setting is_active=0
        # If you want to prevent deletion when data exists, uncomment the following:
        # if structured_count > 0 or raw_count > 0:
        #     return jsonify({
        #         'success': False,
        #         'message': f'Cannot delete financial year {financial_year}. Data exists: {structured_count} structured records, {raw_count} raw records.',
        #         'data_exists': True,
        #         'structured_count': structured_count,
        #         'raw_count': raw_count
        #     }), 400
        
        # Soft delete (set is_active = 0) instead of hard delete
        # This preserves historical reference
        update_query = """
            UPDATE financial_year_master
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        print(f"🔄 Executing soft delete query for ID {fy_id}")
        Database.execute_query(update_query, params=[fy_id])
        print(f"✅ Successfully soft deleted financial year ID {fy_id}")
        
        return jsonify({
            'success': True,
            'message': 'Financial year deactivated successfully'
        }), 200
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error deleting financial year ID {fy_id}: {error_msg}")
        print(f"   Error type: {type(e).__name__}")
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Failed to delete financial year: {error_msg}',
            'error_type': type(e).__name__
        }), 500


@financial_year_master_bp.route('/financial-year-master/validate', methods=['GET', 'OPTIONS'])
def validate_date():
    """Validate if a date falls within any active financial year range"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        date_str = request.args.get('date', type=str)
        if not date_str:
            return jsonify({
                'success': False,
                'message': 'date parameter is required (format: YYYY-MM-DD)'
            }), 400
        
        # Parse date
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate against master data
        validation_result = validate_date_against_fy_master(check_date)
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
    except Exception as e:
        print(f"❌ Error validating date: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to validate date'}), 500


@financial_year_master_bp.route('/financial-year-master/current', methods=['GET', 'OPTIONS'])
def get_current_financial_year_endpoint():
    """Get the current active financial year based on today's date"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        current_fy = get_current_financial_year()
        
        if current_fy['found']:
            return jsonify({
                'success': True,
                'data': {
                    'financial_year': current_fy['financial_year'],
                    'id': current_fy['id'],
                    'start_date': str(current_fy['start_date']) if current_fy['start_date'] else None,
                    'end_date': str(current_fy['end_date']) if current_fy['end_date'] else None
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No active financial year found for today\'s date. Please configure a financial year in Master Data settings.',
                'data': None
            }), 404
    except Exception as e:
        print(f"❌ Error getting current financial year: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to get current financial year'}), 500
