"""
Dashboard analytics routes for finance demo dashboards.
Builds aggregated insights from final_structured and code_master tables.
"""
from flask import Blueprint, request, jsonify
import traceback

from database import Database

dashboard_bp = Blueprint('dashboard', __name__)


def _safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _resolve_entity_code(entity_id):
    """
    Resolve ent_code from entity_master using ent_id.
    Returns (entity_code or None).
    """
    if not entity_id:
        return None
    try:
        row = Database.execute_query(
            "SELECT ent_code FROM entity_master WHERE ent_id = %s",
            params=[entity_id],
            fetch_one=True
        )
        return row.get('ent_code') if row else None
    except Exception:
        return None


@dashboard_bp.route('/dashboard/overview', methods=['GET', 'OPTIONS'])
def dashboard_overview():
    """
    Return KPI + chart data for the dashboard using final_structured + code_master.
    Supports optional filters: entity_id, entity_code, financial_year.
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        entity_id = request.args.get('entity_id', type=int)
        financial_year = request.args.get('financial_year', type=int)
        entity_code = request.args.get('entity_code', type=str)

        # Resolve entity_code from entity_id if provided
        resolved_entity_code = entity_code or _resolve_entity_code(entity_id)

        where_clauses = ["1=1"]
        params = []

        if resolved_entity_code:
            where_clauses.append("entityCode = %s")
            params.append(resolved_entity_code)

        if financial_year:
            where_clauses.append("Year = %s")
            params.append(financial_year)

        where_sql = " AND ".join(where_clauses)

        # Total entities (no filters)
        total_entities_row = Database.execute_query(
            "SELECT COUNT(*) as total_entities FROM entity_master",
            fetch_one=True
        ) or {}
        total_entities = total_entities_row.get('total_entities', 0)

        # Totals & records (respect filters)
        totals_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd,
                MAX(Year) as latest_year
            FROM final_structured
            WHERE {where_sql}
        """
        totals_row = Database.execute_query(
            totals_query,
            params=params if params else None,
            fetch_one=True
        ) or {}

        total_records = totals_row.get('total_records', 0)
        total_amount = _safe_float(totals_row.get('total_amount'))
        total_amount_usd = _safe_float(totals_row.get('total_amount_usd'))
        latest_year = totals_row.get('latest_year')

        # Mapping coverage (mainCategory present)
        mapped_query = f"""
            SELECT 
                SUM(CASE WHEN mainCategory IS NOT NULL AND TRIM(mainCategory) != '' THEN 1 ELSE 0 END) as mapped_count,
                COUNT(*) as total_rows,
                SUM(CASE WHEN mainCategory IS NOT NULL AND TRIM(mainCategory) != '' AND Avg_Fx_Rt IS NOT NULL THEN 1 ELSE 0 END) as fx_covered
            FROM final_structured
            WHERE {where_sql}
        """
        mapped_row = Database.execute_query(
            mapped_query,
            params=params if params else None,
            fetch_one=True
        ) or {}

        mapped_count = mapped_row.get('mapped_count', 0) or 0
        total_rows = mapped_row.get('total_rows', 0) or 0
        fx_covered = mapped_row.get('fx_covered', 0) or 0
        mapped_ratio = round((mapped_count / total_rows) * 100, 2) if total_rows else 0
        # FX ratio: percentage of mapped records that have FX rates
        fx_ratio = round((fx_covered / mapped_count) * 100, 2) if mapped_count else 0

        # P&L vs Balance Sheet mix
        pl_bs_query = f"""
            SELECT 
                CASE 
                    WHEN LOWER(TRIM(category1)) = 'profit and loss' THEN 'Profit and Loss'
                    WHEN LOWER(TRIM(category1)) = 'profit & loss' THEN 'Profit and Loss'
                    WHEN LOWER(TRIM(category1)) = 'p&l' THEN 'Profit and Loss'
                    WHEN LOWER(TRIM(category1)) = 'balance sheet' THEN 'Balance Sheet'
                    ELSE 'Other'
                END as bucket,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql}
            GROUP BY bucket
        """
        pl_bs_mix = Database.execute_query(
            pl_bs_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Category breakdown (category1)
        category_query = f"""
            SELECT 
                COALESCE(category1, 'Unmapped') as category,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd
            FROM final_structured
            WHERE {where_sql}
            GROUP BY COALESCE(category1, 'Unmapped')
            ORDER BY total_amount DESC
            LIMIT 12
        """
        category_breakdown = Database.execute_query(
            category_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Sub-category breakdown (category2)
        subcategory_query = f"""
            SELECT 
                COALESCE(category2, 'Unmapped') as sub_category,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql}
            GROUP BY COALESCE(category2, 'Unmapped')
            ORDER BY total_amount DESC
            LIMIT 12
        """
        subcategory_breakdown = Database.execute_query(
            subcategory_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Entity totals
        entity_totals_query = f"""
            SELECT 
                COALESCE(entityCode, 'N/A') as entity_code,
                COALESCE(entityName, 'Unknown Entity') as entity_name,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd
            FROM final_structured
            WHERE {where_sql}
            GROUP BY entityCode, entityName
            ORDER BY total_amount DESC
            LIMIT 12
        """
        entity_totals = Database.execute_query(
            entity_totals_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Yearly trend
        yearly_query = f"""
            SELECT 
                Year as year,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql} AND Year IS NOT NULL
            GROUP BY Year
            ORDER BY Year
        """
        yearly_trend = Database.execute_query(
            yearly_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Monthly trend (Year + Month)
        monthly_query = f"""
            SELECT 
                Year as year,
                Month as month,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql} AND Month IS NOT NULL
            GROUP BY Year, Month
            ORDER BY Year, Month
        """
        monthly_trend = Database.execute_query(
            monthly_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Top accounts / Particulars
        top_accounts_query = f"""
            SELECT 
                Particular as account_name,
                mainCategory,
                category1,
                category2,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd
            FROM final_structured
            WHERE {where_sql}
            GROUP BY Particular, mainCategory, category1, category2
            ORDER BY total_amount DESC
            LIMIT 10
        """
        top_accounts = Database.execute_query(
            top_accounts_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Bottom accounts / Particulars
        bottom_accounts_query = f"""
            SELECT 
                Particular as account_name,
                mainCategory,
                category1,
                category2,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd
            FROM final_structured
            WHERE {where_sql}
            GROUP BY Particular, mainCategory, category1, category2
            HAVING total_amount IS NOT NULL
            ORDER BY total_amount ASC
            LIMIT 10
        """
        bottom_accounts = Database.execute_query(
            bottom_accounts_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Currency mix
        currency_mix_query = f"""
            SELECT 
                COALESCE(localCurrencyCode, 'N/A') as currency,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql}
            GROUP BY COALESCE(localCurrencyCode, 'N/A')
            ORDER BY total_amount DESC
        """
        currency_mix = Database.execute_query(
            currency_mix_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # FX gaps by currency
        fx_gap_query = f"""
            SELECT 
                COALESCE(localCurrencyCode, 'N/A') as currency,
                COUNT(*) as missing_fx_rows
            FROM final_structured
            WHERE {where_sql}
              AND (Avg_Fx_Rt IS NULL OR TRIM(Avg_Fx_Rt) = '')
            GROUP BY COALESCE(localCurrencyCode, 'N/A')
            ORDER BY missing_fx_rows DESC
        """
        fx_gaps = Database.execute_query(
            fx_gap_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Unmapped particulars
        unmapped_query = f"""
            SELECT 
                Particular as account_name,
                COALESCE(SUM(transactionAmount), 0) as total_amount
            FROM final_structured
            WHERE {where_sql}
              AND (mainCategory IS NULL OR TRIM(mainCategory) = '')
            GROUP BY Particular
            ORDER BY total_amount DESC
            LIMIT 15
        """
        unmapped = Database.execute_query(
            unmapped_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Code master coverage (distinct codes available)
        code_master_row = Database.execute_query(
            "SELECT COUNT(*) as code_master_count FROM code_master",
            fetch_one=True
        ) or {}
        code_master_count = code_master_row.get('code_master_count', 0)

        # Normalize numeric fields
        def normalize_amounts(rows, fields=('total_amount', 'total_amount_usd')):
            for row in rows:
                for field in fields:
                    if field in row:
                        row[field] = _safe_float(row.get(field))
            return rows

        category_breakdown = normalize_amounts(category_breakdown)
        subcategory_breakdown = normalize_amounts(subcategory_breakdown, fields=('total_amount',))
        entity_totals = normalize_amounts(entity_totals)
        yearly_trend = normalize_amounts(yearly_trend, fields=('total_amount',))
        monthly_trend = normalize_amounts(monthly_trend, fields=('total_amount',))
        top_accounts = normalize_amounts(top_accounts)
        bottom_accounts = normalize_amounts(bottom_accounts)
        currency_mix = normalize_amounts(currency_mix, fields=('total_amount',))
        fx_gaps = normalize_amounts(fx_gaps, fields=('missing_fx_rows',))
        unmapped = normalize_amounts(unmapped, fields=('total_amount',))
        pl_bs_mix = normalize_amounts(pl_bs_mix, fields=('total_amount',))

        # Concentration: top 5 vs others
        concentration_top5 = sorted(top_accounts, key=lambda r: r.get('total_amount', 0), reverse=True)[:5]
        total_all = sum([r.get('total_amount', 0) for r in top_accounts]) if top_accounts else 0
        top5_sum = sum([r.get('total_amount', 0) for r in concentration_top5]) if concentration_top5 else 0
        others_sum = max(total_all - top5_sum, 0)
        concentration = {
            'top5': concentration_top5,
            'others_total': others_sum
        }

        # Variance (YoY)
        variance_year = []
        if yearly_trend and len(yearly_trend) > 1:
            yearly_sorted = sorted(yearly_trend, key=lambda r: r.get('year'))
            prev = None
            for row in yearly_sorted:
                if prev is not None:
                    delta = row['total_amount'] - prev['total_amount']
                    pct = (delta / prev['total_amount'] * 100) if prev['total_amount'] else 0
                else:
                    delta, pct = 0, 0
                variance_year.append({
                    'year': row['year'],
                    'total_amount': row['total_amount'],
                    'delta_amount': delta,
                    'delta_percent': round(pct, 2)
                })
                prev = row

        # Variance (Month over previous month across returned order)
        variance_month = []
        if monthly_trend and len(monthly_trend) > 1:
            monthly_sorted = monthly_trend  # already ordered by Year, Month from SQL
            prev = None
            for row in monthly_sorted:
                if prev is not None:
                    delta = row['total_amount'] - prev['total_amount']
                    pct = (delta / prev['total_amount'] * 100) if prev['total_amount'] else 0
                else:
                    delta, pct = 0, 0
                variance_month.append({
                    'label': f"{row.get('year')}-{row.get('month')}",
                    'total_amount': row['total_amount'],
                    'delta_amount': delta,
                    'delta_percent': round(pct, 2)
                })
                prev = row

        # Alerts (simple heuristics)
        alerts = []
        # Large YoY change
        if variance_year:
            latest_var = variance_year[-1]
            if abs(latest_var.get('delta_percent', 0)) >= 15:
                alerts.append(f"Year {latest_var.get('year')} moved {latest_var.get('delta_percent', 0)}% vs prior year.")
        # FX gaps
        total_fx_gaps = sum([r.get('missing_fx_rows', 0) for r in fx_gaps]) if fx_gaps else 0
        if total_fx_gaps > 0:
            alerts.append(f"{total_fx_gaps} rows missing Avg_Fx_Rt.")
        # Unmapped
        if unmapped:
            alerts.append(f"{len(unmapped)} unmapped particulars shown.")

        response = {
            'success': True,
            'data': {
                'filters': {
                    'entity_id': entity_id,
                    'financial_year': financial_year,
                    'entity_code': resolved_entity_code
                },
                'kpis': {
                    'total_entities': total_entities,
                    'total_records': total_records,
                    'total_amount': total_amount,
                    'total_amount_usd': total_amount_usd,
                    'latest_year': latest_year,
                    'mapped_count': mapped_count,
                    'unmapped_count': max(total_rows - mapped_count, 0),
                    'mapped_ratio': mapped_ratio,
                    'fx_coverage_ratio': fx_ratio,
                    'code_master_count': code_master_count
                },
                'category_breakdown': category_breakdown,
                'subcategory_breakdown': subcategory_breakdown,
                'entity_totals': entity_totals,
                'yearly_trend': yearly_trend,
                'monthly_trend': monthly_trend,
                'top_accounts': top_accounts,
                'bottom_accounts': bottom_accounts,
                'currency_mix': currency_mix,
                'fx_gaps': fx_gaps,
                'unmapped': unmapped,
                'pl_bs_mix': pl_bs_mix,
                'concentration': concentration,
                'variance_year': variance_year,
                'variance_month': variance_month,
                'alerts': alerts
            }
        }

        return jsonify(response), 200
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ Error building dashboard overview: {error_type}: {error_msg}")
        traceback.print_exc()
        
        # In development/debug mode, include more details
        import os
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        response_data = {
            'success': False,
            'message': 'Failed to build dashboard data',
            'error_type': error_type
        }
        
        if debug_mode:
            response_data['error_details'] = error_msg
            response_data['traceback'] = traceback.format_exc()
        
        return jsonify(response_data), 500
