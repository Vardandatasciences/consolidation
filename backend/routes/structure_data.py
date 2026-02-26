"""
Structured data routes for fetching balance sheet data from final_structured table
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import traceback
import pandas as pd
import io
from datetime import datetime

from database import Database


def _build_forex_cache(rows):
    """
    Build a cache of forex rates keyed by (entity_id, currency, financial_year).
    Prioritizes entity_forex_rates (FY-specific) over forex_master (legacy).
    Falls back to legacy forex_master if FY-specific rates not found.
    """
    from routes.forex import _get_latest_row_for_currency, get_entity_fy_forex_rate, parse_financial_year  # lazy import to avoid cycles

    # Build set of (entity_id, currency, financial_year) tuples
    entity_currency_fy = set()
    currencies = set()
    
    for row in rows or []:
        curr = (row.get("localCurrencyCode") or "").strip()
        if curr:
            currencies.add(curr.upper())
        
        # Try to get entity_id and financial_year from row
        entity_id = row.get("entity_id") or row.get("EntityID")
        entity_code = row.get("entityCode") or row.get("entity_code")
        # Try financial_year column first (new format "2024-25"), then Year column (ending year int)
        financial_year_str = row.get("financial_year")
        financial_year = None
        if financial_year_str:
            # Parse "2024-25" format to get ending year (2024)
            financial_year = parse_financial_year(financial_year_str)
        # Fallback to Year column if financial_year not available
        if not financial_year:
            financial_year = row.get("Year") or row.get("year")
        
        # If we have entity_code but not entity_id, resolve it
        if entity_code and not entity_id:
            try:
                entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s LIMIT 1"
                entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
                if entity_result:
                    entity_id = entity_result.get('ent_id')
            except Exception:
                pass
        
        if entity_id and financial_year and curr:
            entity_currency_fy.add((entity_id, curr.upper(), financial_year))

    cache = {}
    found_entity_rates = set()  # Track which currencies have entity-specific rates
    
    # First, try to get FY-specific rates from entity_forex_rates
    print(f"🔍 Building forex cache: Checking {len(entity_currency_fy)} entity+currency+FY combinations")
    for entity_id, curr, fy in entity_currency_fy:
        cache_key = f"{entity_id}_{curr}_{fy}"
        fy_rates = get_entity_fy_forex_rate(entity_id, curr, fy)
        
        # If not found for exact FY, try adjacent year (FY 2024-25 might be stored as 2025)
        # Also try year-1 in case data has ending year but rates stored with starting year
        if not fy_rates:
            # Try next year (e.g., if data has 2024, try 2025 for FY 2024-25)
            try_next_fy = fy + 1
            print(f"⚠️ No FY-specific rate found: Entity {entity_id}, Currency {curr}, FY {fy}, trying adjacent year {try_next_fy}")
            fy_rates = get_entity_fy_forex_rate(entity_id, curr, try_next_fy)
            if fy_rates:
                print(f"✅ Found FY-specific rate in adjacent year: Entity {entity_id}, Currency {curr}, FY {try_next_fy} (data has {fy})")
                # Use the found FY for cache key to ensure consistency
                cache_key = f"{entity_id}_{curr}_{try_next_fy}"
                fy = try_next_fy  # Update fy for monthly rate lookup
        
        # If still not found, try previous year (e.g., if data has 2025, try 2024 for FY 2023-2024)
        if not fy_rates:
            try_prev_fy = fy - 1
            print(f"⚠️ No FY-specific rate found: Entity {entity_id}, Currency {curr}, FY {fy}, trying previous year {try_prev_fy}")
            fy_rates = get_entity_fy_forex_rate(entity_id, curr, try_prev_fy)
            if fy_rates:
                print(f"✅ Found FY-specific rate in previous year: Entity {entity_id}, Currency {curr}, FY {try_prev_fy} (data has {fy})")
                cache_key = f"{entity_id}_{curr}_{try_prev_fy}"
                fy = try_prev_fy  # Update fy for monthly rate lookup
        
        if fy_rates:
            found_entity_rates.add(curr.upper())
            cache[cache_key] = {
                "source": "entity_forex_rates",
                "entity_id": entity_id,
                "currency": curr,
                "financial_year": fy,
                "opening_rate": fy_rates.get("opening_rate"),
                "closing_rate": fy_rates.get("closing_rate"),
                "initial_rate": fy_rates.get("opening_rate"),  # For backward compatibility
                "latest_rate": fy_rates.get("closing_rate"),   # For backward compatibility
            }
            print(f"✅ Found FY-specific rate: Entity {entity_id}, Currency {curr}, FY {fy} - Opening: {fy_rates.get('opening_rate')}, Closing: {fy_rates.get('closing_rate')}")
        else:
            print(f"⚠️ No FY-specific rate found: Entity {entity_id}, Currency {curr}, FY {fy}")
    
    # Fallback to legacy forex_master ONLY for currencies that don't have entity-specific rates
    # AND only if we have rows that need those currencies
    currencies_needing_fallback = currencies - found_entity_rates
    
    if currencies_needing_fallback:
        print(f"🔄 Falling back to legacy forex_master for currencies: {currencies_needing_fallback}")
    
    for curr in currencies_needing_fallback:
        variants = [curr]
        if len(curr) == 3:
            variants.append(f"{curr}IN")
        variants.extend(["USDIN", "USD"])

        seen = set()
        for code in variants:
            if code in seen:
                continue
            seen.add(code)
            fx_row = _get_latest_row_for_currency(code)
            if fx_row:
                # Use a generic key for legacy rates
                cache[f"legacy_{curr}"] = {
                    "source": "forex_master",
                    "currency": curr,
                    "currency_used": code,
                    "initial_rate": fx_row.get("initial_rate"),
                    "latest_rate": fx_row.get("latest_rate"),
                    "opening_rate": fx_row.get("initial_rate"),  # Map initial to opening
                    "closing_rate": fx_row.get("latest_rate"),   # Map latest to closing
                }
                print(f"📦 Using legacy rate for {curr}: {fx_row.get('initial_rate')} / {fx_row.get('latest_rate')}")
                break

    print(f"💱 Forex cache built: {len(cache)} entries ({len([k for k in cache.keys() if not k.startswith('legacy_')])} entity-specific, {len([k for k in cache.keys() if k.startswith('legacy_')])} legacy)")
    return cache


def _apply_forex_rates(rows, forex_cache):
    """
    Enrich rows with Avg_Fx_Rt and transactionAmountUSD using the provided
    forex_cache. 
    - For FY-specific rates: Balance Sheet uses closing_rate, P&L uses average of opening_rate and closing_rate
    - For legacy rates: Balance Sheet uses latest_rate, P&L uses average of initial_rate and latest_rate
    
    Applies to ALL rows with mainCategory (regardless of category1).
    """
    from routes.forex import parse_financial_year  # lazy import to avoid cycles
    
    updated = 0
    for row in rows or []:
        # Check if mainCategory exists - THIS IS THE KEY REQUIREMENT
        main_category = (row.get("mainCategory") or "").strip()
        if not main_category:
            continue
        
        curr = (row.get("localCurrencyCode") or "").strip().upper()
        
        # Try to get entity_id and financial_year for FY-specific lookup
        entity_id = row.get("entity_id") or row.get("EntityID")
        entity_code = row.get("entityCode") or row.get("entity_code")
        # Try financial_year column first (new format "2024-25"), then Year column (ending year int)
        financial_year_str = row.get("financial_year")
        financial_year = None
        if financial_year_str:
            # Parse "2024-25" format to get ending year (2024)
            financial_year = parse_financial_year(financial_year_str)
        # Fallback to Year column if financial_year not available
        if not financial_year:
            financial_year = row.get("Year") or row.get("year")
        
        # Resolve entity_id from entity_code if needed
        if entity_code and not entity_id:
            try:
                entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s LIMIT 1"
                entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
                if entity_result:
                    entity_id = entity_result.get('ent_id')
            except Exception:
                pass
        
        # Try FY-specific cache first
        fx = None
        if entity_id and financial_year:
            cache_key = f"{entity_id}_{curr}_{financial_year}"
            fx = forex_cache.get(cache_key)
            
            # If not found, try adjacent years
            if not fx:
                try_next_fy = financial_year + 1
                cache_key = f"{entity_id}_{curr}_{try_next_fy}"
                fx = forex_cache.get(cache_key)
                if fx:
                    print(f"✅ Using FY rate from adjacent year: Entity {entity_id}, Currency {curr}, FY {try_next_fy} (data has {financial_year})")
            
            if not fx:
                try_prev_fy = financial_year - 1
                cache_key = f"{entity_id}_{curr}_{try_prev_fy}"
                fx = forex_cache.get(cache_key)
                if fx:
                    print(f"✅ Using FY rate from previous year: Entity {entity_id}, Currency {curr}, FY {try_prev_fy} (data has {financial_year})")
        
        # Fallback to legacy cache
        if not fx:
            fx = forex_cache.get(f"legacy_{curr}")
            # Also try direct currency key for backward compatibility
            if not fx:
                fx = forex_cache.get(curr)
        
        if not fx:
            continue
        
        # Determine calculation method using either category1 or mainCategory labels
        brd_cls = (row.get("category1") or "").strip().lower()
        main_category_lower = main_category.lower()
        is_balance_sheet = (
            "balance sheet" in brd_cls
            or "balance sheet" in main_category_lower
        )
        is_pl = (
            "profit and loss" in brd_cls
            or "profit & loss" in brd_cls
            or "p&l" in brd_cls
            or "profit and loss" in main_category_lower
            or "profit & loss" in main_category_lower
            or "p&l" in main_category_lower
        )
        
        # Use FY-specific rates if available, otherwise use legacy rates
        opening_rate = fx.get("opening_rate") or fx.get("initial_rate")
        closing_rate = fx.get("closing_rate") or fx.get("latest_rate")
        
        rate = None
        try:
            if is_pl:
                # P&L uses average of opening and closing rates
                if opening_rate is not None and closing_rate is not None:
                    rate = (float(opening_rate) + float(closing_rate)) / 2.0
                elif closing_rate is not None:
                    rate = float(closing_rate)
                else:
                    continue
            else:
                # Balance Sheet uses closing rate (FY end rate or monthly rate)
                if closing_rate is not None:
                    rate = float(closing_rate)
                else:
                    continue
        except Exception:
            continue

        if rate is None:
            continue

        row["Avg_Fx_Rt"] = rate

        # Pick transactionAmount (preferred) or the alias "amount" if present
        amt = row.get("transactionAmount", row.get("amount"))
        try:
            if amt is not None:
                row["transactionAmountUSD"] = float(amt) * rate
        except Exception:
            pass

        updated += 1

    return updated


def _calculate_and_save_forex_rates(rows, forex_cache, save_to_db=True):
    """
    Calculate and save Avg_Fx_Rt and transactionAmountUSD to database when mainCategory exists.
    Calculates for ALL rows with mainCategory (regardless of category1).
    Uses category1 only to determine rate calculation method (P&L average vs Balance Sheet latest).
    
    Args:
        rows: List of row dictionaries from database
        forex_cache: Dictionary of forex rates by currency
        save_to_db: If True, save calculated rates to database
    
    Returns:
        Number of rows updated
    """
    from routes.forex import parse_financial_year  # lazy import to avoid cycles
    
    updated_count = 0
    updates_to_save = []
    
    for row in rows or []:
        # Check if mainCategory exists - THIS IS THE KEY REQUIREMENT
        main_category = (row.get("mainCategory") or "").strip()
        if not main_category:
            continue
        
        curr = (row.get("localCurrencyCode") or "").strip().upper()
        
        # Try to get entity_id and financial_year for FY-specific lookup
        entity_id = row.get("entity_id") or row.get("EntityID")
        entity_code = row.get("entityCode") or row.get("entity_code")
        # Try financial_year column first (new format "2024-25"), then Year column (ending year int)
        financial_year_str = row.get("financial_year")
        financial_year = None
        if financial_year_str:
            # Parse "2024-25" format to get ending year (2024)
            financial_year = parse_financial_year(financial_year_str)
        # Fallback to Year column if financial_year not available
        if not financial_year:
            financial_year = row.get("Year") or row.get("year")
        
        # Resolve entity_id from entity_code if needed
        if entity_code and not entity_id:
            try:
                entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s LIMIT 1"
                entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
                if entity_result:
                    entity_id = entity_result.get('ent_id')
            except Exception:
                pass
        
        # Try FY-specific cache first
        fx = None
        if entity_id and financial_year:
            cache_key = f"{entity_id}_{curr}_{financial_year}"
            fx = forex_cache.get(cache_key)
            
            # If not found, try adjacent years
            if not fx:
                try_next_fy = financial_year + 1
                cache_key = f"{entity_id}_{curr}_{try_next_fy}"
                fx = forex_cache.get(cache_key)
            
            if not fx:
                try_prev_fy = financial_year - 1
                cache_key = f"{entity_id}_{curr}_{try_prev_fy}"
                fx = forex_cache.get(cache_key)
        
        # Fallback to legacy cache
        if not fx:
            fx = forex_cache.get(f"legacy_{curr}")
            if not fx:
                fx = forex_cache.get(curr)
        
        if not fx:
            # Debug: Log why forex wasn't found (only log first few to avoid spam)
            if updated_count < 3:
                print(f"⚠️ No forex cache found for currency: {curr}, entity: {entity_id}, FY: {financial_year} (row mainCategory: {main_category})")
            continue
        
        # Determine calculation method using either category1 or mainCategory labels
        brd_cls = (row.get("category1") or "").strip().lower()
        main_category_lower = main_category.lower()
        is_balance_sheet = (
            "balance sheet" in brd_cls
            or "balance sheet" in main_category_lower
        )
        is_pl = (
            "profit and loss" in brd_cls
            or "profit & loss" in brd_cls
            or "p&l" in brd_cls
            or "profit and loss" in main_category_lower
            or "profit & loss" in main_category_lower
            or "p&l" in main_category_lower
        )
        
        # Use FY-specific rates if available, otherwise use legacy rates
        opening_rate = fx.get("opening_rate") or fx.get("initial_rate")
        closing_rate = fx.get("closing_rate") or fx.get("latest_rate")

        rate = None
        try:
            if is_pl:
                # P&L uses average of opening and closing rates
                if opening_rate is not None and closing_rate is not None:
                    rate = (float(opening_rate) + float(closing_rate)) / 2.0
                elif closing_rate is not None:
                    rate = float(closing_rate)
                else:
                    continue
            else:
                # Default (Balance Sheet / anything else) uses closing_rate (FY end rate)
                if closing_rate is not None:
                    rate = float(closing_rate)
                else:
                    continue
        except Exception:
            rate = None

        if rate is None:
            continue

        # Get transaction amount
        amt = row.get("transactionAmount")
        transaction_amount_usd = None
        if amt is not None:
            try:
                transaction_amount_usd = float(amt) * rate
            except Exception:
                pass

        # Update row in memory
        row["Avg_Fx_Rt"] = rate
        if transaction_amount_usd is not None:
            row["transactionAmountUSD"] = transaction_amount_usd

        # Save to database if requested
        if save_to_db:
            sl_no = row.get("sl_no")
            if sl_no:
                updates_to_save.append({
                    'sl_no': sl_no,
                    'avg_fx_rt': rate,
                    'transaction_amount_usd': transaction_amount_usd
                })

        updated_count += 1

    # Batch update database
    if save_to_db and updates_to_save:
        try:
            for update in updates_to_save:
                update_query = """
                    UPDATE final_structured
                    SET Avg_Fx_Rt = %s,
                        transactionAmountUSD = %s
                    WHERE sl_no = %s
                """
                Database.execute_query(
                    update_query,
                    params=[update['avg_fx_rt'], update['transaction_amount_usd'], update['sl_no']]
                )
            print(f"💾 Saved {len(updates_to_save)} forex rate calculations to database")
        except Exception as db_error:
            print(f"⚠️ Error saving forex rates to database: {str(db_error)}")
            traceback.print_exc()

    return updated_count

def _sync_final_structured_with_code_master():
    """
    Ensure final_structured has main/category columns filled wherever a matching
    code_master entry exists for the same Particular/RawParticulars.

    This will:
      - Match rows case-insensitively on trimmed Particular vs RawParticulars
      - Only update rows where at least one of the mapping columns is NULL/blank
    """
    try:
        # Use a single UPDATE with JOIN so it is efficient even for many rows.
        # MySQL style syntax is assumed here.
        update_query = """
            UPDATE final_structured fs
            JOIN code_master cm
              ON LOWER(TRIM(fs.Particular)) = LOWER(TRIM(cm.RawParticulars))
            SET
              fs.mainCategory = cm.mainCategory,
              fs.category1   = cm.category1,
              fs.category2   = cm.category2,
              fs.category3   = cm.category3,
              fs.category4   = cm.category4,
              fs.category5   = cm.category5
            WHERE
              (
                fs.mainCategory IS NULL OR TRIM(fs.mainCategory) = '' OR
                fs.category1   IS NULL OR TRIM(fs.category1)   = '' OR
                fs.category2   IS NULL OR TRIM(fs.category2)   = '' OR
                fs.category3   IS NULL OR TRIM(fs.category3)   = '' OR
                fs.category4   IS NULL OR TRIM(fs.category4)   = '' OR
                fs.category5   IS NULL OR TRIM(fs.category5)   = ''
              )
        """
        Database.execute_query(update_query)
        print("✅ Synced final_structured with code_master for matching particulars")
    except Exception as sync_err:
        # Do not block main request if sync fails; just log it.
        print(f"⚠️ Error syncing final_structured with code_master: {str(sync_err)}")
        traceback.print_exc()


# Create blueprint for structured data routes
structure_bp = Blueprint('structure', __name__)


def _get_all_descendant_entity_ids(entity_id):
    """
    Recursively get all descendant entity IDs (children, grandchildren, etc.)
    Returns: list of entity IDs including the parent entity itself
    """
    descendant_ids = [entity_id]  # Include the entity itself
    
    children_query = "SELECT ent_id FROM entity_master WHERE parent_entity_id = %s"
    children = Database.execute_query(children_query, params=[entity_id], fetch_all=True) or []
    
    for child in children:
        child_id = child.get('ent_id')
        if child_id:
            # Recursively get descendants of this child (includes child_id)
            child_descendants = _get_all_descendant_entity_ids(child_id)
            descendant_ids.extend(child_descendants)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for eid in descendant_ids:
        if eid not in seen:
            seen.add(eid)
            unique_ids.append(eid)
    
    return unique_ids


def _get_all_descendant_entity_codes(entity_id):
    """
    Get all descendant entity codes (including the entity itself)
    Returns: list of entity codes
    """
    descendant_ids = _get_all_descendant_entity_ids(entity_id)
    
    if not descendant_ids:
        return []
    
    # Get entity codes for all descendant IDs
    placeholders = ','.join(['%s'] * len(descendant_ids))
    query = f"""
        SELECT ent_code
        FROM entity_master
        WHERE ent_id IN ({placeholders})
    """
    results = Database.execute_query(query, params=descendant_ids, fetch_all=True) or []
    return [r.get('ent_code') for r in results if r.get('ent_code')]


@structure_bp.route('/data', methods=['GET', 'OPTIONS'])
def get_structured_data():
    """Get all structured data from final_structured table"""
    try:
        from routes.forex import parse_financial_year, format_financial_year  # lazy import to avoid cycles
        
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # First, ensure final_structured is in sync with code_master mappings.
        # This will auto-fill mainCategory/category1-5 wherever a matching
        # RawParticulars exists in code_master for the same Particular.
        _sync_final_structured_with_code_master()

        # Get optional query parameters for filtering
        entity_id = request.args.get('entity_id', type=int)
        financial_year_param = request.args.get('financial_year', type=str)  # Can be "2024-25" or "2024"
        entity_code = request.args.get('entity_code', type=str)
        
        # Check if financial_year column exists (for backward compatibility)
        try:
            check_col_query = """
                SELECT COUNT(*) as col_exists
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'final_structured'
                AND COLUMN_NAME = 'financial_year'
            """
            col_check = Database.execute_query(check_col_query, fetch_one=True)
            has_financial_year_col = col_check and col_check.get('col_exists', 0) > 0
        except Exception:
            has_financial_year_col = False
        
        # Build query with full set of columns; keep aliases for UI while exposing all fields
        # Also join with entity_master to get ent_id for forex lookup
        financial_year_select = "fs.financial_year" if has_financial_year_col else "CONCAT(fs.Year, '-', SUBSTRING(CAST(fs.Year + 1 AS CHAR), -2)) AS financial_year"
        
        query = f"""
            SELECT 
                -- Aliases used by UI
                fs.category1 AS category,
                fs.category2 AS sub_category,
                fs.Particular AS account_name,
                fs.mainCategory AS code,
                fs.transactionAmount AS amount,
                -- Full original columns for complete visibility
                fs.sl_no,
                fs.Particular,
                fs.entityName,
                fs.entityCode,
                fs.localCurrencyCode,
                fs.transactionAmount,
                fs.Month,
                fs.selectedMonth,
                fs.mainCategory,
                fs.category1,
                fs.category2,
                fs.category3,
                fs.category4,
                fs.category5,
                fs.Avg_Fx_Rt,
                fs.transactionAmountUSD,
                fs.Year,
                {financial_year_select},
                fs.Qtr,
                fs.Half,
                -- Get entity_id from entity_master for forex lookup
                em.ent_id AS entity_id
            FROM final_structured fs
            LEFT JOIN entity_master em ON fs.entityCode = em.ent_code
            WHERE 1=1
        """
        params = []
        
        # If entity_id is provided, filter by ent_id and all its descendants
        if entity_id:
            # Get all descendant entity IDs (including the entity itself)
            descendant_ids = _get_all_descendant_entity_ids(entity_id)
            if descendant_ids:
                placeholders = ','.join(['%s'] * len(descendant_ids))
                query += f" AND em.ent_id IN ({placeholders})"
                params.extend(descendant_ids)
                print(f"🔍 Filtering by entity_id {entity_id} and {len(descendant_ids) - 1} descendant(s)")
        
        # Also support filtering by entity_code directly (with descendants)
        elif entity_code:
            # First, get entity_id from entity_code
            entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s"
            entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
            if entity_result and entity_result.get('ent_id'):
                entity_id_from_code = entity_result.get('ent_id')
                # Get all descendant entity IDs (including the entity itself)
                descendant_ids = _get_all_descendant_entity_ids(entity_id_from_code)
                if descendant_ids:
                    placeholders = ','.join(['%s'] * len(descendant_ids))
                    query += f" AND em.ent_id IN ({placeholders})"
                    params.extend(descendant_ids)
                    print(f"🔍 Filtering by entity_code {entity_code} (id: {entity_id_from_code}) and {len(descendant_ids) - 1} descendant(s)")
            else:
                # If entity not found, still filter by code (backward compatibility)
                query += " AND fs.entityCode = %s"
                params.append(entity_code)
        
        if financial_year_param:
            # Support both "2024-25" format and integer format
            financial_year_str = financial_year_param if '-' in str(financial_year_param) else format_financial_year(int(financial_year_param))
            # Also try to match by Year column if financial_year is integer
            try:
                year_int = int(financial_year_param) if '-' not in str(financial_year_param) else parse_financial_year(financial_year_param)
                if has_financial_year_col:
                    query += " AND (fs.financial_year = %s OR fs.Year = %s)"
                    params.append(financial_year_str)
                    params.append(year_int)
                else:
                    # If column doesn't exist, only filter by Year
                    query += " AND fs.Year = %s"
                    params.append(year_int)
            except (ValueError, TypeError):
                if has_financial_year_col:
                    query += " AND fs.financial_year = %s"
                    params.append(financial_year_str)
                # If column doesn't exist and can't parse, skip filter
        
        query += " ORDER BY category1, category2, Particular"
        
        data = Database.execute_query(query, params=params if params else None, fetch_all=True)
        
        # Apply forex rates only in memory for display.
        # Heavy "recalculate & save to DB" is moved to the dedicated endpoint
        # /structure/recalculate-avg-fx-rate so this list API stays fast.
        if data:
            forex_cache = _build_forex_cache(data)
            print(f"🔍 Building forex cache: {len(forex_cache)} currencies found")
            applied_count = _apply_forex_rates(data, forex_cache)
            if applied_count > 0:
                print(
                    f"✅ Applied forex rates in memory for {applied_count} row(s) "
                    f"using {len(forex_cache)} cached currency code(s)"
                )

        # Calculate total assets if data exists
        total_assets = 0
        if data:
            for row in data:
                try:
                    # Get amount from transactionAmount (it's a decimal, so should be numeric)
                    amount = row.get('amount', 0)
                    if amount is not None:
                        total_assets += float(amount)
                except (ValueError, TypeError):
                    continue
        
        print(f"✅ Fetched {len(data) if data else 0} structured data records")
        
        return jsonify({
            'success': True,
            'data': {
                'records': data or [],
                'total_assets': total_assets,
                'count': len(data) if data else 0
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching structured data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching structured data'
        }), 500


@structure_bp.route('/summary', methods=['GET', 'OPTIONS'])
def get_summary():
    """Get summary statistics from final_structured table"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        entity_id = request.args.get('entity_id', type=int)
        financial_year = request.args.get('financial_year', type=int)
        entity_code = request.args.get('entity_code', type=str)
        
        # Build query for summary with actual column names
        query = """
            SELECT 
                category1 as category,
                SUM(transactionAmount) as total_amount
            FROM final_structured
            WHERE 1=1
        """
        params = []
        
        # If entity_id is provided, include all descendants
        if entity_id:
            # Get all descendant entity codes (including the entity itself)
            descendant_codes = _get_all_descendant_entity_codes(entity_id)
            if descendant_codes:
                placeholders = ','.join(['%s'] * len(descendant_codes))
                query += f" AND entityCode IN ({placeholders})"
                params.extend(descendant_codes)
                print(f"🔍 Summary: Filtering by entity_id {entity_id} and {len(descendant_codes) - 1} descendant(s)")
        
        # Also support filtering by entity_code directly (with descendants)
        elif entity_code:
            # First, get entity_id from entity_code
            entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s"
            entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
            if entity_result and entity_result.get('ent_id'):
                entity_id_from_code = entity_result.get('ent_id')
                # Get all descendant entity codes (including the entity itself)
                descendant_codes = _get_all_descendant_entity_codes(entity_id_from_code)
                if descendant_codes:
                    placeholders = ','.join(['%s'] * len(descendant_codes))
                    query += f" AND entityCode IN ({placeholders})"
                    params.extend(descendant_codes)
                    print(f"🔍 Summary: Filtering by entity_code {entity_code} (id: {entity_id_from_code}) and {len(descendant_codes) - 1} descendant(s)")
            else:
                # If entity not found, still filter by code (backward compatibility)
                query += " AND entityCode = %s"
                params.append(entity_code)
        
        if financial_year:
            query += " AND Year = %s"
            params.append(financial_year)
        
        query += " GROUP BY category1"
        
        summary = Database.execute_query(query, params=params if params else None, fetch_all=True)
        
        print(f"✅ Fetched summary data")
        
        return jsonify({
            'success': True,
            'data': {
                'summary': summary or []
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching summary: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching summary'
        }), 500


@structure_bp.route('/update-by-particular', methods=['PUT', 'OPTIONS'])
@jwt_required()
def update_by_particular():
    """Update final_structured table rows by matching particular field with code master data"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        payload = request.get_json(silent=True) or {}
        particular = (payload.get('particular') or '').strip()
        
        if not particular:
            return jsonify({'success': False, 'message': 'particular is required'}), 400
        
        # Get code master data by RawParticulars (case-insensitive match)
        code_query = """
            SELECT 
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
        code_result = Database.execute_query(code_query, params=[particular], fetch_one=True)
        
        if not code_result:
            return jsonify({'success': False, 'message': f'No code master found for particular: {particular}'}), 404
        
        # Update all rows in final_structured with matching Particular (case-insensitive)
        update_query = """
            UPDATE final_structured
            SET 
                mainCategory = %s,
                category1 = %s,
                category2 = %s,
                category3 = %s,
                category4 = %s,
                category5 = %s
            WHERE LOWER(TRIM(Particular)) = LOWER(TRIM(%s))
        """
        update_params = [
            code_result.get('mainCategory') or None,
            code_result.get('category1') or None,
            code_result.get('category2') or None,
            code_result.get('category3') or None,
            code_result.get('category4') or None,
            code_result.get('category5') or None,
            particular
        ]
        
        Database.execute_query(update_query, params=update_params)
        
        # Get count of updated rows and fetch updated rows to check for Avg_Fx_Rt calculation
        count_query = """
            SELECT COUNT(*) as count
            FROM final_structured
            WHERE LOWER(TRIM(Particular)) = LOWER(TRIM(%s))
        """
        count_result = Database.execute_query(count_query, params=[particular], fetch_one=True)
        updated_count = count_result.get('count', 0) if count_result else 0
        
        # After updating, calculate and save Avg_Fx_Rt for rows with mainCategory
        rows_query = """
            SELECT sl_no, Particular, mainCategory, category1, localCurrencyCode, Avg_Fx_Rt, transactionAmount
            FROM final_structured
            WHERE LOWER(TRIM(Particular)) = LOWER(TRIM(%s))
        """
        updated_rows = Database.execute_query(rows_query, params=[particular], fetch_all=True)
        
        fx_calculated_count = 0
        if updated_rows:
            # Check if mainCategory exists - if yes, calculate and save forex rates
            rows_with_main_category = [
                row for row in updated_rows 
                if (row.get("mainCategory") or "").strip()
            ]
            
            if rows_with_main_category:
                # Build forex cache for these rows
                forex_cache = _build_forex_cache(rows_with_main_category)
                # Calculate and save forex rates
                fx_calculated_count = _calculate_and_save_forex_rates(
                    rows_with_main_category, 
                    forex_cache, 
                    save_to_db=True
                )
                print(f"   ✅ Calculated and saved Avg_Fx_Rt for {fx_calculated_count} row(s) with mainCategory")
        
        print(f"✅ Updated {updated_count} rows in final_structured for particular: {particular}")
        if fx_calculated_count > 0:
            print(f"✅ Auto-calculated Avg_Fx_Rt for {fx_calculated_count} updated row(s)")
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {updated_count} row(s) in final_structured',
            'data': {
                'particular': particular,
                'updated_count': updated_count,
                'fx_calculated_count': fx_calculated_count,
                'code_data': {
                    'mainCategory': code_result.get('mainCategory'),
                    'category1': code_result.get('category1'),
                    'category2': code_result.get('category2'),
                    'category3': code_result.get('category3'),
                    'category4': code_result.get('category4'),
                    'category5': code_result.get('category5'),
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating structured data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating structured data'
        }), 500


@structure_bp.route('/recalculate-avg-fx-rate', methods=['POST', 'OPTIONS'])
@jwt_required()
def recalculate_avg_fx_rate():
    """Recalculate Avg_Fx_Rt for all rows in final_structured based on Brd_Cls and forex rates"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get currency from request (default to USDIN)
        payload = request.get_json(silent=True) or {}
        currency = (payload.get('currency') or 'USDIN').upper().strip()
        
        # Import forex helper functions
        from routes.forex import _get_latest_row_for_currency
        
        # Get latest forex rates
        forex_row = _get_latest_row_for_currency(currency)
        
        if not forex_row:
            return jsonify({
                'success': False,
                'message': f'No forex data found for currency: {currency}'
            }), 404
        
        initial_rate = forex_row.get('initial_rate')
        latest_rate = forex_row.get('latest_rate')
        
        if initial_rate is None and latest_rate is None:
            return jsonify({
                'success': False,
                'message': f'No forex rates available for currency: {currency}'
            }), 400
        
        # Get average rate for P&L calculation (if both rates exist)
        avg_rate_pl = None
        if initial_rate is not None and latest_rate is not None:
            avg_rate_pl = (float(initial_rate) + float(latest_rate)) / 2.0
        
        # Determine which localCurrencyCode values match this forex currency
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
        
        # Update rows based on classification
        updated_count = 0
        
        # Update ALL rows with mainCategory matching currency
        # Use latest_rate for Balance Sheet / unknown rows
        # Use average rate for P&L rows (category1 or mainCategory marked as P&L)
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
            # Get count
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
            # Get count
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
        
        print(f"✅ Recalculated Avg_Fx_Rt for {updated_count} rows using currency {currency}")
        print(f"   Initial Rate: {initial_rate}, Latest Rate: {latest_rate}, P&L Avg: {avg_rate_pl}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully recalculated Avg_Fx_Rt for {updated_count} row(s)',
            'data': {
                'currency': currency,
                'updated_count': updated_count,
                'rates': {
                    'initial_rate': float(initial_rate) if initial_rate else None,
                    'latest_rate': float(latest_rate) if latest_rate else None,
                    'profit_loss_avg_rate': float(avg_rate_pl) if avg_rate_pl else None
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error recalculating avg fx rate: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while recalculating avg fx rate'
        }), 500


@structure_bp.route('/export-excel', methods=['GET', 'OPTIONS'])
def export_to_excel():
    """Export structured data to Excel file and download directly"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get optional query parameters for filtering
        entity_id = request.args.get('entity_id', type=int)
        financial_year = request.args.get('financial_year', type=int)
        entity_code = request.args.get('entity_code', type=str)
        
        # Build query with all columns
        query = """
            SELECT 
                sl_no,
                Particular,
                transactionAmount,
                entityName,
                localCurrencyCode,
                mainCategory,
                category1,
                category2,
                category3,
                category4,
                category5,
                Avg_Fx_Rt,
                transactionAmountUSD,
                Month,
                selectedMonth,
                Year
            FROM final_structured
            WHERE 1=1
        """
        params = []
        
        # If entity_id is provided, include all descendants
        if entity_id:
            # Get all descendant entity codes (including the entity itself)
            descendant_codes = _get_all_descendant_entity_codes(entity_id)
            if descendant_codes:
                placeholders = ','.join(['%s'] * len(descendant_codes))
                query += f" AND entityCode IN ({placeholders})"
                params.extend(descendant_codes)
                print(f"🔍 Export: Filtering by entity_id {entity_id} and {len(descendant_codes) - 1} descendant(s)")
        
        # Also support filtering by entity_code directly (with descendants)
        elif entity_code:
            # First, get entity_id from entity_code
            entity_query = "SELECT ent_id FROM entity_master WHERE ent_code = %s"
            entity_result = Database.execute_query(entity_query, params=[entity_code], fetch_one=True)
            if entity_result and entity_result.get('ent_id'):
                entity_id_from_code = entity_result.get('ent_id')
                # Get all descendant entity codes (including the entity itself)
                descendant_codes = _get_all_descendant_entity_codes(entity_id_from_code)
                if descendant_codes:
                    placeholders = ','.join(['%s'] * len(descendant_codes))
                    query += f" AND entityCode IN ({placeholders})"
                    params.extend(descendant_codes)
                    print(f"🔍 Export: Filtering by entity_code {entity_code} (id: {entity_id_from_code}) and {len(descendant_codes) - 1} descendant(s)")
            else:
                # If entity not found, still filter by code (backward compatibility)
                query += " AND entityCode = %s"
                params.append(entity_code)
        
        if financial_year:
            query += " AND Year = %s"
            params.append(financial_year)
        
        query += " ORDER BY sl_no"
        
        # Fetch data
        data = Database.execute_query(query, params=params if params else None, fetch_all=True)

        # Apply forex rates for export so Excel matches on-screen values
        if data:
            forex_cache = _build_forex_cache(data)
            applied_count = _apply_forex_rates(data, forex_cache)
            print(
                f"✅ Applied forex rates for export: {applied_count} row(s) "
                f"using {len(forex_cache)} cached currency code(s)"
            )
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data found to export'
            }), 404
        
        # Convert to DataFrame with human-readable column names
        df_data = []
        for row in data:
            df_data.append({
                'Sl No': row.get('sl_no', ''),
                'Particular': row.get('Particular', ''),
                'Transaction Amount': row.get('transactionAmount', ''),
                'Entity Name': row.get('entityName', ''),
                'Local Currency Code': row.get('localCurrencyCode', ''),
                'Main Category': row.get('mainCategory', ''),
                'Category 1': row.get('category1', ''),
                'Category 2': row.get('category2', ''),
                'Category 3': row.get('category3', ''),
                'Category 4': row.get('category4', ''),
                'Category 5': row.get('category5', ''),
                'Avg Fx Rt': row.get('Avg_Fx_Rt', ''),
                'Transaction Amount USD': row.get('transactionAmountUSD', ''),
                'Month': row.get('Month', ''),
                'Selected Month': row.get('selectedMonth', ''),
                'Year': row.get('Year', '')
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Structured Data', index=False)
            
            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets['Structured Data']
            
            # Auto-adjust column widths
            from openpyxl.utils import get_column_letter
            for idx, col in enumerate(df.columns, start=1):
                max_length = max(
                    df[col].astype(str).apply(len).max() if len(df) > 0 else 0,
                    len(str(col))
                ) + 2
                column_letter = get_column_letter(idx)
                worksheet.column_dimensions[column_letter].width = min(max_length, 50)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'structured_data_export_{timestamp}.xlsx'
        
        print(f"✅ Excel export successful: {len(data)} records, filename: {filename}")
        
        # Return file for download
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Error exporting to Excel: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'An error occurred while exporting to Excel: {str(e)}'
        }), 500


@structure_bp.route('/delete-all', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_all_structured_data():
    """Delete all records from rawdata and final_structured tables"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get counts before deletion (use correct camel-case table name `rawData`)
        rawdata_count_query = "SELECT COUNT(*) as count FROM `rawData`"
        rawdata_count_result = Database.execute_query(rawdata_count_query, fetch_one=True)
        rawdata_count = rawdata_count_result.get('count', 0) if rawdata_count_result else 0
        
        final_structured_count_query = "SELECT COUNT(*) as count FROM final_structured"
        final_structured_count_result = Database.execute_query(final_structured_count_query, fetch_one=True)
        final_structured_count = final_structured_count_result.get('count', 0) if final_structured_count_result else 0
        
        total_count = rawdata_count + final_structured_count
        
        if total_count == 0:
            return jsonify({
                'success': True,
                'message': 'No records to delete',
                'data': {
                    'deleted_count': 0,
                    'rawdata_count': 0,
                    'final_structured_count': 0
                }
            }), 200
        
        # Delete all records from final_structured first (due to potential foreign key constraints)
        if final_structured_count > 0:
            delete_final_structured_query = "DELETE FROM final_structured"
            Database.execute_query(delete_final_structured_query)
            print(f"✅ Deleted all {final_structured_count} records from final_structured table")
        
        # Delete all records from rawData
        if rawdata_count > 0:
            delete_rawdata_query = "DELETE FROM `rawData`"
            Database.execute_query(delete_rawdata_query)
            print(f"✅ Deleted all {rawdata_count} records from rawData table")
        
        print(f"✅ Deleted all records: {rawdata_count} from rawData, {final_structured_count} from final_structured")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted all records: {rawdata_count} from rawData, {final_structured_count} from final_structured',
            'data': {
                'deleted_count': total_count,
                'rawdata_count': rawdata_count,
                'final_structured_count': final_structured_count
            }
        }), 200
    except Exception as e:
        print(f"❌ Error deleting all structured data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'An error occurred while deleting all structured data: {str(e)}'
        }), 500


@structure_bp.route('/consolidation', methods=['GET', 'OPTIONS'])
def get_consolidation_data():
    """Get consolidated financial data grouped by mainCategory, category1, category2, and entity"""
    try:
        # Handle preflight
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get query parameters
        entity_id = request.args.get('entity_id', type=int)
        financial_year_param = request.args.get('financial_year', type=str)
        
        if not entity_id:
            return jsonify({
                'success': False,
                'message': 'entity_id is required'
            }), 400
        
        # Get all descendant entity IDs (including the entity itself)
        descendant_ids = _get_all_descendant_entity_ids(entity_id)
        if not descendant_ids:
            return jsonify({
                'success': False,
                'message': 'Entity not found'
            }), 404
        
        # Check if financial_year column exists
        try:
            check_col_query = """
                SELECT COUNT(*) as col_exists
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'final_structured'
                AND COLUMN_NAME = 'financial_year'
            """
            col_check = Database.execute_query(check_col_query, fetch_one=True)
            has_financial_year_col = col_check and col_check.get('col_exists', 0) > 0
        except Exception:
            has_financial_year_col = False
        
        financial_year_select = "fs.financial_year" if has_financial_year_col else "CONCAT(fs.Year, '-', SUBSTRING(CAST(fs.Year + 1 AS CHAR), -2)) AS financial_year"
        
        # Build query to get aggregated data
        placeholders = ','.join(['%s'] * len(descendant_ids))
        query = f"""
            SELECT 
                fs.mainCategory,
                fs.category1,
                fs.category2,
                fs.entityName,
                fs.entityCode,
                em.ent_id AS entity_id,
                SUM(fs.transactionAmountUSD) AS total_amount_usd,
                {financial_year_select} AS financial_year
            FROM final_structured fs
            LEFT JOIN entity_master em ON fs.entityCode = em.ent_code
            WHERE em.ent_id IN ({placeholders})
        """
        params = list(descendant_ids)
        
        # Add financial year filter if provided
        if financial_year_param:
            from routes.forex import parse_financial_year, format_financial_year
            financial_year_str = financial_year_param if '-' in str(financial_year_param) else format_financial_year(int(financial_year_param))
            try:
                year_int = int(financial_year_param) if '-' not in str(financial_year_param) else parse_financial_year(financial_year_param)
                if has_financial_year_col:
                    query += " AND (fs.financial_year = %s OR fs.Year = %s)"
                    params.append(financial_year_str)
                    params.append(year_int)
                else:
                    query += " AND fs.Year = %s"
                    params.append(year_int)
            except (ValueError, TypeError):
                if has_financial_year_col:
                    query += " AND fs.financial_year = %s"
                    params.append(financial_year_str)
        
        query += """
            GROUP BY fs.mainCategory, fs.category1, fs.category2, fs.entityName, fs.entityCode, em.ent_id
            ORDER BY fs.mainCategory, fs.category1, fs.category2, fs.entityName
        """
        
        data = Database.execute_query(query, params=params, fetch_all=True)
        
        # Get entity information for all descendants
        entity_query = f"""
            SELECT ent_id, ent_name, ent_code
            FROM entity_master
            WHERE ent_id IN ({placeholders})
            ORDER BY ent_name
        """
        entities = Database.execute_query(entity_query, params=list(descendant_ids), fetch_all=True) or []
        
        # Structure the data similar to the pivot table
        # Group by mainCategory -> category1 -> category2 -> entity
        result = {
            'balance_sheet': {},
            'profit_loss': {},
            'entities': [{'ent_id': e['ent_id'], 'ent_name': e['ent_name'], 'ent_code': e['ent_code']} for e in entities]
        }
        
        for row in data or []:
            main_category = (row.get('mainCategory') or '').strip()
            category1 = (row.get('category1') or '').strip()
            category2 = (row.get('category2') or '').strip()
            entity_id_val = row.get('entity_id')
            amount = float(row.get('total_amount_usd') or 0)
            
            # Determine which main category
            if not main_category:
                continue
            
            # Normalize mainCategory to determine if it's Balance Sheet or Profit & Loss
            main_cat_lower = main_category.lower()
            is_balance_sheet = any(term in main_cat_lower for term in ['balance sheet', 'balance', 'bs', 'assets', 'liabilities', 'equity'])
            is_profit_loss = any(term in main_cat_lower for term in ['profit', 'loss', 'p&l', 'pl', 'income', 'revenue', 'expense', 'cost'])
            
            # Also check category1 for better categorization
            category1_lower = category1.lower() if category1 else ''
            if not is_balance_sheet and not is_profit_loss:
                # Use category1 to determine
                is_balance_sheet = any(term in category1_lower for term in ['asset', 'liabilit', 'equity', 'intercompany'])
                is_profit_loss = any(term in category1_lower for term in ['revenue', 'expense', 'cost', 'income'])
            
            # Default to Balance Sheet if still unclear
            target_dict = result['balance_sheet'] if is_balance_sheet or not is_profit_loss else result['profit_loss']
            
            # Initialize category1 if not exists
            if category1 not in target_dict:
                target_dict[category1] = {}
            
            # Initialize category2 if not exists
            if category2 not in target_dict[category1]:
                target_dict[category1][category2] = {}
            
            # Store amount by entity_id
            target_dict[category1][category2][entity_id_val] = amount
        
        print(f"✅ Generated consolidation data for entity {entity_id} with {len(descendant_ids)} entities")
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching consolidation data: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'An error occurred while fetching consolidation data'
        }), 500

