"""
Forex routes for managing forex_master
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database import Database

forex_bp = Blueprint('forex', __name__)


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

@forex_bp.route('/forex', methods=['GET', 'OPTIONS'])
def list_forex():
    """List distinct currencies with their initial(first row) and latest(last row) values"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get distinct currencies
        currencies = Database.execute_query(
            "SELECT DISTINCT currency FROM forex_master ORDER BY currency ASC",
            fetch_all=True
        ) or []
        
        result = []
        for row in currencies:
            curr = (row.get('currency') or '').upper()
            if not curr:
                continue
            first_row = _get_first_row_for_currency(curr)
            last_row = _get_latest_row_for_currency(curr)
            # Prefer first row's initial_rate, otherwise fall back to the latest row's initial_rate
            initial_rate = None
            initial_updated_at = None
            if first_row and first_row.get('initial_rate') is not None:
                initial_rate = first_row.get('initial_rate')
                initial_updated_at = first_row.get('updated_at')
            elif last_row and last_row.get('initial_rate') is not None:
                initial_rate = last_row.get('initial_rate')
                initial_updated_at = last_row.get('updated_at')
            result.append({
                'currency': curr,
                'initial': {
                    'fx_id': first_row['fx_id'] if first_row else None,
                    'rate': initial_rate,
                    'updated_at': initial_updated_at
                },
                'latest': {
                    'fx_id': last_row['fx_id'] if last_row else None,
                    'rate': last_row['latest_rate'] if last_row else None,
                    'month': last_row['month'] if last_row else None,
                    'updated_at': last_row['updated_at'] if last_row else None
                }
            })
        
        return jsonify({'success': True, 'data': {'items': result}}), 200
    except Exception as e:
        print(f"❌ Error listing forex: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to list forex'}), 500

def _get_latest_row_for_currency(currency: str):
    """Fetch latest row by updated_at then fx_id for a currency"""
    query = """
        SELECT 
            fx_id,
            currency,
            initial_rate,
            latest_rate,
            month,
            updated_at
        FROM forex_master
        WHERE currency = %s
        ORDER BY 
            COALESCE(updated_at, '1900-01-01') DESC,
            fx_id DESC
        LIMIT 1
    """
    return Database.execute_query(query, params=[currency], fetch_one=True)

def _get_second_latest_row_for_currency(currency: str):
    """Fetch second latest row (previous latest) by updated_at then fx_id for a currency"""
    query = """
        SELECT 
            fx_id,
            currency,
            initial_rate,
            latest_rate,
            month,
            updated_at
        FROM forex_master
        WHERE currency = %s
        ORDER BY 
            COALESCE(updated_at, '1900-01-01') DESC,
            fx_id DESC
        LIMIT 1 OFFSET 1
    """
    return Database.execute_query(query, params=[currency], fetch_one=True)

def _get_first_row_for_currency(currency: str):
    """Fetch first/oldest row for a currency"""
    query = """
        SELECT 
            fx_id,
            currency,
            initial_rate,
            latest_rate,
            month,
            updated_at
        FROM forex_master
        WHERE currency = %s
        ORDER BY 
            COALESCE(updated_at, '9999-12-31') ASC,
            fx_id ASC
        LIMIT 1
    """
    return Database.execute_query(query, params=[currency], fetch_one=True)

@forex_bp.route('/forex/<string:currency>', methods=['GET', 'OPTIONS'])
def get_forex(currency: str):
    """Get initial and latest forex for a currency - both from latest row"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        currency = (currency or '').upper().strip()
        if not currency:
            return jsonify({'success': False, 'message': 'currency is required'}), 400

        last_row = _get_latest_row_for_currency(currency)

        if not last_row:
            return jsonify({
                'success': True,
                'data': {
                    'currency': currency,
                    'initial': {'fx_id': None, 'rate': None, 'updated_at': None},
                    'latest': {'fx_id': None, 'rate': None, 'month': None, 'updated_at': None},
                }
            }), 200

        # Display latest row's initial_rate in initial field, and latest_rate in latest field
        data = {
            'currency': currency,
            'initial': {
                'fx_id': last_row['fx_id'],
                'rate': last_row['initial_rate'],
                'updated_at': last_row['updated_at']
            },
            'latest': {
                'fx_id': last_row['fx_id'],
                'rate': last_row['latest_rate'],
                'month': last_row['month'],
                'updated_at': last_row['updated_at']
            }
        }
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        print(f"❌ Error fetching forex for {currency}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch forex'}), 500


@forex_bp.route('/forex', methods=['POST'])
@jwt_required()
def create_forex():
    """
    Create a new forex_master row.
    - currency: required
    - latest_rate requires month
    - at least one of initial_rate or latest_rate must be provided
    """
    try:
        payload = request.get_json(silent=True) or {}
        currency = (payload.get('currency') or '').upper().strip()
        if not currency:
            return jsonify({'success': False, 'message': 'currency is required'}), 400

        initial_rate = payload.get('initial_rate', None)
        latest_rate = payload.get('latest_rate', None)
        month = payload.get('month', None)

        def _to_decimal(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except Exception:
                raise ValueError('Rate must be a number')

        try:
            initial_rate_dec = _to_decimal(initial_rate)
            latest_rate_dec = _to_decimal(latest_rate)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400

        if initial_rate_dec is None and latest_rate_dec is None:
            return jsonify({'success': False, 'message': 'initial_rate or latest_rate is required'}), 400

        if latest_rate_dec is not None:
            if not month or not str(month).strip():
                return jsonify({'success': False, 'message': 'month is required when providing latest_rate'}), 400
            month = str(month).strip()

        insert_sql = """
            INSERT INTO forex_master (currency, initial_rate, latest_rate, month, updated_at)
            VALUES (%s, %s, %s, %s, CURDATE())
        """
        Database.execute_query(insert_sql, params=[currency, initial_rate_dec, latest_rate_dec, month])

        last_row = _get_latest_row_for_currency(currency)
        data = {
            'currency': currency,
            'initial': {
                'fx_id': last_row['fx_id'] if last_row else None,
                'rate': last_row['initial_rate'] if last_row else None,
                'updated_at': last_row['updated_at'] if last_row else None
            },
            'latest': {
                'fx_id': last_row['fx_id'] if last_row else None,
                'rate': last_row['latest_rate'] if last_row else None,
                'month': last_row['month'] if last_row else None,
                'updated_at': last_row['updated_at'] if last_row else None
            }
        }

        try:
            recalc_result = recalculate_avg_fx_rate_internal(currency)
            if recalc_result.get('success'):
                print(f"✅ Triggered Avg_Fx_Rt recalculation after create: {recalc_result.get('updated_count', 0)} rows updated")
            else:
                print("⚠️ Avg_Fx_Rt recalculation completed with issues after create")
        except Exception as recalc_error:
            print(f"⚠️ Failed to recalculate Avg_Fx_Rt after forex create: {str(recalc_error)}")

        return jsonify({'success': True, 'message': 'Forex row created', 'data': data}), 200
    except Exception as e:
        print(f"❌ Error creating forex: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to create forex'}), 500


@forex_bp.route('/forex/<string:currency>', methods=['PUT'])
@jwt_required()
def upsert_forex(currency: str):
    """
    Update or insert forex for a currency.
    Rules:
    - latest_rate update requires month (mandatory)
    - initial_rate update does not require month
    - If no row exists, insert one
    """
    try:
        payload = request.get_json(silent=True) or {}
        currency = (currency or '').upper().strip()
        if not currency:
            return jsonify({'success': False, 'message': 'currency is required'}), 400

        initial_rate = payload.get('initial_rate', None)
        latest_rate = payload.get('latest_rate', None)
        month = payload.get('month', None)

        # Validate numbers if present
        def _to_decimal(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except Exception:
                raise ValueError('Rate must be a number')

        try:
            initial_rate_dec = _to_decimal(initial_rate)
            latest_rate_dec = _to_decimal(latest_rate)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400

        # If updating latest_rate, month is mandatory (non-empty)
        if latest_rate_dec is not None:
            if not month or not str(month).strip():
                return jsonify({'success': False, 'message': 'month is required when updating latest_rate'}), 400
            month = str(month).strip()

        did_anything = False

        # ALWAYS INSERT NEW ROWS - never update existing rows
        # This maintains history and ensures no NULL values
        
        # When adding initial_rate ONLY (not latest_rate)
        if initial_rate_dec is not None and latest_rate_dec is None:
            # Get latest_rate and month from current latest row to copy them
            current_latest = _get_latest_row_for_currency(currency)
            copy_latest_rate = None
            copy_month = None
            
            if current_latest:
                copy_latest_rate = current_latest.get('latest_rate')
                copy_month = current_latest.get('month')
            
            # Insert new row with initial_rate + copied latest_rate and month
            if copy_latest_rate is not None and copy_month is not None:
                insert_sql = """
                    INSERT INTO forex_master (currency, initial_rate, latest_rate, month, updated_at)
                    VALUES (%s, %s, %s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, initial_rate_dec, copy_latest_rate, copy_month])
            elif copy_latest_rate is not None:
                insert_sql = """
                    INSERT INTO forex_master (currency, initial_rate, latest_rate, updated_at)
                    VALUES (%s, %s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, initial_rate_dec, copy_latest_rate])
            elif copy_month is not None:
                insert_sql = """
                    INSERT INTO forex_master (currency, initial_rate, month, updated_at)
                    VALUES (%s, %s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, initial_rate_dec, copy_month])
            else:
                # No previous data to copy, just insert initial_rate
                insert_sql = """
                    INSERT INTO forex_master (currency, initial_rate, updated_at)
                    VALUES (%s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, initial_rate_dec])
            did_anything = True
        
        # When adding latest_rate (with or without initial_rate)
        if latest_rate_dec is not None:
            # Determine initial_rate to use
            final_initial_rate = None
            if initial_rate_dec is not None:
                # Use the provided initial_rate
                final_initial_rate = initial_rate_dec
            else:
                # Copy initial_rate from current latest row
                current_latest = _get_latest_row_for_currency(currency)
                if current_latest:
                    final_initial_rate = current_latest.get('initial_rate')
            
            # Insert new row with latest_rate, month, and initial_rate
            if final_initial_rate is not None:
                insert_sql = """
                    INSERT INTO forex_master (currency, initial_rate, latest_rate, month, updated_at)
                    VALUES (%s, %s, %s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, final_initial_rate, latest_rate_dec, month])
            else:
                # No initial_rate to copy, just insert latest_rate and month
                insert_sql = """
                    INSERT INTO forex_master (currency, latest_rate, month, updated_at)
                    VALUES (%s, %s, %s, CURDATE())
                """
                Database.execute_query(insert_sql, params=[currency, latest_rate_dec, month])
            did_anything = True

        if not did_anything:
            return jsonify({'success': False, 'message': 'Nothing to update'}), 400

        # Return both initial and latest after change - both from latest row
        last_row = _get_latest_row_for_currency(currency)
        data = {
            'currency': currency,
            'initial': {
                'fx_id': last_row['fx_id'] if last_row else None,
                'rate': last_row['initial_rate'] if last_row else None,
                'updated_at': last_row['updated_at'] if last_row else None
            },
            'latest': {
                'fx_id': last_row['fx_id'] if last_row else None,
                'rate': last_row['latest_rate'] if last_row else None,
                'month': last_row['month'] if last_row else None,
                'updated_at': last_row['updated_at'] if last_row else None
            }
        }
        
        # Trigger recalculation of Avg_Fx_Rt in final_structured table
        try:
            recalc_result = recalculate_avg_fx_rate_internal(currency)
            if recalc_result.get('success'):
                print(f"✅ Triggered Avg_Fx_Rt recalculation: {recalc_result.get('updated_count', 0)} rows updated")
            else:
                print(f"⚠️ Avg_Fx_Rt recalculation completed with issues")
        except Exception as recalc_error:
            # Don't fail the forex update if recalculation fails
            print(f"⚠️ Failed to recalculate Avg_Fx_Rt after forex update: {str(recalc_error)}")
        
        return jsonify({'success': True, 'message': 'Forex updated', 'data': data}), 200
    except Exception as e:
        print(f"❌ Error updating forex for {currency}: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to update forex'}), 500


def recalculate_avg_fx_rate_internal(currency: str):
    """
    Internal function to recalculate Avg_Fx_Rt for ALL rows with mainCategory 
    that match the changed currency. Matches localCurrencyCode to the forex currency.
    """
    try:
        currency = (currency or 'USDIN').upper().strip()
        
        # Get latest forex rates
        forex_row = _get_latest_row_for_currency(currency)
        
        if not forex_row:
            return {'success': False, 'updated_count': 0}
        
        initial_rate = forex_row.get('initial_rate')
        latest_rate = forex_row.get('latest_rate')
        
        if initial_rate is None and latest_rate is None:
            return {'success': False, 'updated_count': 0}
        
        # Get average rate for P&L calculation
        avg_rate_pl = None
        if initial_rate is not None and latest_rate is not None:
            avg_rate_pl = (float(initial_rate) + float(latest_rate)) / 2.0
        
        # Determine which localCurrencyCode values match this forex currency
        # e.g., if currency is "USDIN", match rows with localCurrencyCode = "USD" or "USDIN"
        # if currency is "EURIN", match rows with localCurrencyCode = "EUR" or "EURIN"
        matching_currencies = []
        if currency.endswith('IN'):
            base_currency = currency[:-2]  # Remove "IN" suffix
            matching_currencies = [base_currency, currency]
        else:
            matching_currencies = [currency]
            if len(currency) == 3:
                matching_currencies.append(f"{currency}IN")
        
        # Build WHERE clause for currency matching
        currency_conditions = " OR ".join([f"UPPER(TRIM(localCurrencyCode)) = %s" for _ in matching_currencies])
        currency_params = [curr.upper() for curr in matching_currencies]
        
        updated_count = 0
        
        # Update ALL rows with mainCategory matching currency
        # Use latest_rate for Balance Sheet / unknown rows
        # Use average rate for rows classified as P&L (by category1 or mainCategory)
        if latest_rate is not None:
            # First, update Balance Sheet rows and rows without P&L classification (use latest_rate)
            update_bs_query = f"""
                UPDATE final_structured
                SET Avg_Fx_Rt = %s,
                    transactionAmountUSD = transactionAmount * %s
                WHERE mainCategory IS NOT NULL 
                AND TRIM(mainCategory) != ''
                AND transactionAmount IS NOT NULL
                AND ({currency_conditions})
                AND NOT (
                    (category1 IS NOT NULL AND (
                        LOWER(TRIM(category1)) = 'profit and loss' 
                        OR LOWER(TRIM(category1)) = 'profit & loss' 
                        OR LOWER(TRIM(category1)) = 'p&l'))
                    OR (mainCategory IS NOT NULL AND (
                        LOWER(TRIM(mainCategory)) = 'profit and loss' 
                        OR LOWER(TRIM(mainCategory)) = 'profit & loss' 
                        OR LOWER(TRIM(mainCategory)) = 'p&l'))
                )
            """
            params = [latest_rate, latest_rate] + currency_params
            Database.execute_query(update_bs_query, params=params)
            count_query = f"""
                SELECT COUNT(*) as count
                FROM final_structured
                WHERE mainCategory IS NOT NULL 
                AND TRIM(mainCategory) != ''
                AND transactionAmount IS NOT NULL
                AND ({currency_conditions})
                AND NOT (
                    (category1 IS NOT NULL AND (
                        LOWER(TRIM(category1)) = 'profit and loss' 
                        OR LOWER(TRIM(category1)) = 'profit & loss' 
                        OR LOWER(TRIM(category1)) = 'p&l'))
                    OR (mainCategory IS NOT NULL AND (
                        LOWER(TRIM(mainCategory)) = 'profit and loss' 
                        OR LOWER(TRIM(mainCategory)) = 'profit & loss' 
                        OR LOWER(TRIM(mainCategory)) = 'p&l'))
                )
            """
            count_result = Database.execute_query(count_query, params=currency_params, fetch_one=True)
            updated_count += count_result.get('count', 0) if count_result else 0
        
        # Update Profit and Loss rows: use (initial_rate + latest_rate) / 2 (rows classified as P&L by category1 or mainCategory)
        if avg_rate_pl is not None:
            update_pl_query = f"""
                UPDATE final_structured
                SET Avg_Fx_Rt = %s,
                    transactionAmountUSD = transactionAmount * %s
                WHERE mainCategory IS NOT NULL 
                AND TRIM(mainCategory) != ''
                AND transactionAmount IS NOT NULL
                AND ({currency_conditions})
                AND (
                    (category1 IS NOT NULL AND (
                        LOWER(TRIM(category1)) = 'profit and loss' 
                        OR LOWER(TRIM(category1)) = 'profit & loss' 
                        OR LOWER(TRIM(category1)) = 'p&l'))
                    OR (mainCategory IS NOT NULL AND (
                        LOWER(TRIM(mainCategory)) = 'profit and loss' 
                        OR LOWER(TRIM(mainCategory)) = 'profit & loss' 
                        OR LOWER(TRIM(mainCategory)) = 'p&l'))
                )
            """
            params = [avg_rate_pl, avg_rate_pl] + currency_params
            Database.execute_query(update_pl_query, params=params)
            count_query = f"""
                SELECT COUNT(*) as count
                FROM final_structured
                WHERE mainCategory IS NOT NULL 
                AND TRIM(mainCategory) != ''
                AND transactionAmount IS NOT NULL
                AND ({currency_conditions})
                AND (
                    (category1 IS NOT NULL AND (
                        LOWER(TRIM(category1)) = 'profit and loss' 
                        OR LOWER(TRIM(category1)) = 'profit & loss' 
                        OR LOWER(TRIM(category1)) = 'p&l'))
                    OR (mainCategory IS NOT NULL AND (
                        LOWER(TRIM(mainCategory)) = 'profit and loss' 
                        OR LOWER(TRIM(mainCategory)) = 'profit & loss' 
                        OR LOWER(TRIM(mainCategory)) = 'p&l'))
                )
            """
            count_result = Database.execute_query(count_query, params=currency_params, fetch_one=True)
            updated_count += count_result.get('count', 0) if count_result else 0
        
        print(f"💱 Recalculated forex rates for {updated_count} row(s) with mainCategory matching currency {currency}")
        return {'success': True, 'updated_count': updated_count}
    except Exception as e:
        print(f"❌ Error in internal recalculation: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'updated_count': 0}


# ========================================
# Financial Year Based Forex Rates (Phase 2 - Requirement 1)
# ========================================

def _calculate_fy_dates(entity_id: int, financial_year: int):
    """
    Calculate financial year start and end dates for an entity.
    
    Financial Year Convention:
    - financial_year is the ENDING year (e.g., 2024 means FY 2023-2024)
    - If financial_year = 2024, then FY starts in 2023 and ends in 2024
    - If financial_year = 2025, then FY starts in 2024 and ends in 2025
    
    Returns: (fy_start_date, fy_end_date) as date strings
    """
    try:
        # Get entity's FY start month and day
        entity_query = """
            SELECT financial_year_start_month, financial_year_start_day
            FROM entity_master
            WHERE ent_id = %s
        """
        entity = Database.execute_query(entity_query, params=[entity_id], fetch_one=True)
        
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        fy_start_month = entity.get('financial_year_start_month') or 4  # Default to April
        fy_start_day = entity.get('financial_year_start_day') or 1  # Default to 1st
        
        # Calculate FY start date (previous year if FY starts before current date)
        # e.g., if FY is 2024 and starts April 1, then start date is 2023-04-01
        fy_start_date = datetime(financial_year - 1, fy_start_month, fy_start_day).date()
        
        # Calculate FY end date (12 months from start - 1 day)
        # e.g., 2023-04-01 + 12 months - 1 day = 2024-03-31
        fy_end_date = (datetime(financial_year - 1, fy_start_month, fy_start_day) + relativedelta(months=12) - relativedelta(days=1)).date()
        
        return fy_start_date, fy_end_date
    except Exception as e:
        print(f"❌ Error calculating FY dates: {str(e)}")
        # Fallback to standard April 1 - March 31
        fy_start_date = datetime(financial_year - 1, 4, 1).date()
        fy_end_date = datetime(financial_year, 3, 31).date()
        return fy_start_date, fy_end_date


@forex_bp.route('/forex/entity/<int:entity_id>/financial-year/<int:financial_year>', methods=['GET', 'OPTIONS'])
def get_entity_fy_forex(entity_id: int, financial_year: int):
    """
    Get forex rates for a specific entity and financial year.
    Returns opening_rate, closing_rate, and FY dates.
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        currency = request.args.get('currency', type=str)
        
        # Build query
        where_clauses = ["entity_id = %s", "financial_year = %s"]
        params = [entity_id, financial_year]
        
        if currency:
            where_clauses.append("currency = %s")
            params.append(currency.upper().strip())
        
        query = f"""
            SELECT 
                id,
                entity_id,
                currency,
                financial_year,
                opening_rate,
                closing_rate,
                fy_start_date,
                fy_end_date,
                created_at,
                updated_at
            FROM entity_forex_rates
            WHERE {' AND '.join(where_clauses)}
            ORDER BY currency ASC
        """
        
        rows = Database.execute_query(query, params=params, fetch_all=True) or []
        
        # If no results and currency specified, try to get from entity's local currency
        if not rows and currency:
            entity_query = "SELECT lcl_curr FROM entity_master WHERE ent_id = %s"
            entity = Database.execute_query(entity_query, params=[entity_id], fetch_one=True)
            if entity and entity.get('lcl_curr'):
                # Try with entity's local currency
                params_alt = [entity_id, financial_year, entity.get('lcl_curr').upper()]
                rows = Database.execute_query(query, params=params_alt, fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': entity_id,
                'financial_year': financial_year,
                'rates': rows
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching entity FY forex: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch entity FY forex rates'}), 500


@forex_bp.route('/forex/entity/<int:entity_id>/financial-year/<int:financial_year>', methods=['POST', 'PUT'])
@jwt_required()
def set_entity_fy_forex(entity_id: int, financial_year: int):
    """
    Create or update forex rates for a specific entity and financial year.
    Body: {
        "currency": "USD",
        "opening_rate": 82.50,
        "closing_rate": 83.20
    }
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        payload = request.get_json(silent=True) or {}
        currency = (payload.get('currency') or '').upper().strip()
        opening_rate = payload.get('opening_rate')
        closing_rate = payload.get('closing_rate')
        
        if not currency:
            return jsonify({'success': False, 'message': 'currency is required'}), 400
        
        if opening_rate is None and closing_rate is None:
            return jsonify({'success': False, 'message': 'At least one of opening_rate or closing_rate is required'}), 400
        
        # Validate rates
        def _to_decimal(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except Exception:
                raise ValueError('Rate must be a number')
        
        try:
            opening_rate_dec = _to_decimal(opening_rate) if opening_rate is not None else None
            closing_rate_dec = _to_decimal(closing_rate) if closing_rate is not None else None
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
        
        # If both rates are provided, use them; otherwise get existing rates
        if opening_rate_dec is None or closing_rate_dec is None:
            existing_query = """
                SELECT opening_rate, closing_rate
                FROM entity_forex_rates
                WHERE entity_id = %s AND currency = %s AND financial_year = %s
                LIMIT 1
            """
            existing = Database.execute_query(existing_query, params=[entity_id, currency, financial_year], fetch_one=True)
            
            if existing:
                opening_rate_dec = opening_rate_dec if opening_rate_dec is not None else existing.get('opening_rate')
                closing_rate_dec = closing_rate_dec if closing_rate_dec is not None else existing.get('closing_rate')
        
        if opening_rate_dec is None or closing_rate_dec is None:
            return jsonify({'success': False, 'message': 'Both opening_rate and closing_rate are required'}), 400
        
        # Format financial year as "2024-25" for storage
        financial_year_str = format_financial_year(financial_year)
        
        # Calculate FY dates (using integer ending year)
        fy_start_date, fy_end_date = _calculate_fy_dates(entity_id, financial_year)
        
        # Check if record exists (check both formats for backward compatibility)
        check_query = """
            SELECT id FROM entity_forex_rates
            WHERE entity_id = %s AND currency = %s AND (financial_year = %s OR financial_year = %s)
            LIMIT 1
        """
        existing_record = Database.execute_query(check_query, params=[entity_id, currency, financial_year_str, str(financial_year)], fetch_one=True)
        
        if existing_record:
            # Update existing record
            update_query = """
                UPDATE entity_forex_rates
                SET opening_rate = %s,
                    closing_rate = %s,
                    fy_start_date = %s,
                    fy_end_date = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            # Update financial_year to new format if it was in old format
            update_query = """
                UPDATE entity_forex_rates
                SET opening_rate = %s,
                    closing_rate = %s,
                    fy_start_date = %s,
                    fy_end_date = %s,
                    financial_year = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            Database.execute_query(update_query, params=[
                opening_rate_dec, closing_rate_dec, fy_start_date, fy_end_date, financial_year_str, existing_record['id']
            ])
            message = 'Forex rates updated'
        else:
            # Insert new record
            insert_query = """
                INSERT INTO entity_forex_rates 
                    (entity_id, currency, financial_year, opening_rate, closing_rate, fy_start_date, fy_end_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            user_id = get_jwt_identity()
            Database.execute_query(insert_query, params=[
                entity_id, currency, financial_year_str, opening_rate_dec, closing_rate_dec, 
                fy_start_date, fy_end_date, user_id
            ])
            message = 'Forex rates created'
        
        # Fetch and return the updated/created record (check both formats)
        get_query = """
            SELECT 
                id,
                entity_id,
                currency,
                financial_year,
                opening_rate,
                closing_rate,
                fy_start_date,
                fy_end_date,
                created_at,
                updated_at
            FROM entity_forex_rates
            WHERE entity_id = %s AND currency = %s AND (financial_year = %s OR financial_year = %s)
        """
        result = Database.execute_query(get_query, params=[entity_id, currency, financial_year_str, str(financial_year)], fetch_one=True)
        
        return jsonify({
            'success': True,
            'message': message,
            'data': result
        }), 200
    except Exception as e:
        print(f"❌ Error setting entity FY forex: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to set entity FY forex rates'}), 500


@forex_bp.route('/forex/entity/<int:entity_id>/financial-years', methods=['GET', 'OPTIONS'])
def get_entity_financial_years(entity_id: int):
    """
    Get list of financial years that have forex rates configured for an entity.
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT DISTINCT financial_year
            FROM entity_forex_rates
            WHERE entity_id = %s
            ORDER BY financial_year DESC
        """
        rows = Database.execute_query(query, params=[entity_id], fetch_all=True) or []
        
        financial_years = [row.get('financial_year') for row in rows if row.get('financial_year')]
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': entity_id,
                'financial_years': financial_years
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching entity financial years: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch entity financial years'}), 500


@forex_bp.route('/forex/entity/<int:entity_id>/rates', methods=['GET', 'OPTIONS'])
def get_entity_all_forex_rates(entity_id: int):
    """
    Get all forex rates for an entity across all financial years.
    Returns all rates grouped by financial year.
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT 
                id,
                entity_id,
                currency,
                financial_year,
                opening_rate,
                closing_rate,
                fy_start_date,
                fy_end_date,
                created_at,
                updated_at
            FROM entity_forex_rates
            WHERE entity_id = %s
            ORDER BY financial_year DESC, currency ASC
        """
        rows = Database.execute_query(query, params=[entity_id], fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': entity_id,
                'rates': rows
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching all entity forex rates: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch entity forex rates'}), 500


def get_entity_fy_forex_rate(entity_id: int, currency: str, financial_year):
    """
    Internal helper function to get FY-specific forex rate for an entity.
    financial_year can be int (ending year like 2024) or str ("2024-25" format).
    Returns: {'opening_rate': float, 'closing_rate': float} or None
    """
    try:
        # Handle both int and string formats
        if isinstance(financial_year, int):
            financial_year_str = format_financial_year(financial_year)
            # Check both formats for backward compatibility
            query = """
                SELECT opening_rate, closing_rate
                FROM entity_forex_rates
                WHERE entity_id = %s AND currency = %s AND (financial_year = %s OR financial_year = %s)
                LIMIT 1
            """
            result = Database.execute_query(query, params=[entity_id, currency.upper(), financial_year_str, str(financial_year)], fetch_one=True)
        else:
            # Already in string format
            query = """
                SELECT opening_rate, closing_rate
                FROM entity_forex_rates
                WHERE entity_id = %s AND currency = %s AND financial_year = %s
                LIMIT 1
            """
            result = Database.execute_query(query, params=[entity_id, currency.upper(), str(financial_year)], fetch_one=True)
        return result if result else None
    except Exception as e:
        print(f"⚠️ Error getting entity FY forex rate: {str(e)}")
        return None

