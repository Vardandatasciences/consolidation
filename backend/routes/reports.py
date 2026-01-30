"""
Reports and Analytics routes for financial reports and cross-entity comparisons.
"""
from flask import Blueprint, request, jsonify
import traceback
from datetime import datetime

from database import Database

reports_bp = Blueprint('reports', __name__)


def _safe_float(val):
    """Safely convert value to float."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _resolve_entity_code(entity_id):
    """Resolve ent_code from entity_master using ent_id."""
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


@reports_bp.route('/reports/metrics', methods=['GET', 'OPTIONS'])
def get_available_metrics():
    """Get list of available metrics for reports."""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        metrics = [
            {'value': 'total-assets', 'label': 'Total Assets', 'category': 'balance-sheet'},
            {'value': 'total-liabilities', 'label': 'Total Liabilities', 'category': 'balance-sheet'},
            {'value': 'total-equity', 'label': 'Total Equity', 'category': 'balance-sheet'},
            {'value': 'total-revenue', 'label': 'Total Revenue', 'category': 'profit-loss'},
            {'value': 'total-expenses', 'label': 'Total Expenses', 'category': 'profit-loss'},
            {'value': 'net-profit', 'label': 'Net Profit', 'category': 'profit-loss'},
            {'value': 'total-amount', 'label': 'Total Amount', 'category': 'general'},
            {'value': 'mapped-ratio', 'label': 'Mapping Coverage Ratio', 'category': 'quality'},
            {'value': 'fx-coverage', 'label': 'FX Coverage Ratio', 'category': 'quality'},
        ]

        return jsonify({
            'success': True,
            'data': {'metrics': metrics}
        }), 200
    except Exception as e:
        print(f"❌ Error fetching metrics: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to fetch metrics'
        }), 500


@reports_bp.route('/reports/financial-years', methods=['GET', 'OPTIONS'])
def get_financial_years():
    """Get list of available financial years."""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        years_query = """
            SELECT DISTINCT Year as year
            FROM final_structured
            WHERE Year IS NOT NULL
            ORDER BY Year DESC
        """
        years_rows = Database.execute_query(years_query, fetch_all=True) or []

        years = []
        for row in years_rows:
            year = row.get('year')
            if year:
                # Format as FY YYYY-YY
                fy_label = f"FY {year-1}-{str(year)[-2:]}"
                years.append({
                    'value': f'fy-{year}',
                    'label': fy_label,
                    'year': year
                })

        return jsonify({
            'success': True,
            'data': {'years': years}
        }), 200
    except Exception as e:
        print(f"❌ Error fetching financial years: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to fetch financial years'
        }), 500


@reports_bp.route('/reports/entities', methods=['GET', 'OPTIONS'])
def get_entities_for_reports():
    """Get list of entities for report selection."""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        entities_query = """
            SELECT ent_id, ent_name, ent_code
            FROM entity_master
            ORDER BY ent_name
        """
        entities = Database.execute_query(entities_query, fetch_all=True) or []

        return jsonify({
            'success': True,
            'data': {'entities': entities}
        }), 200
    except Exception as e:
        print(f"❌ Error fetching entities: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to fetch entities'
        }), 500


@reports_bp.route('/reports/comparison', methods=['GET', 'OPTIONS'])
def get_comparison_data():
    """
    Get cross-entity comparison data based on metric, period, and entities.
    Query params:
    - metric: total-assets, total-liabilities, etc.
    - financial_year: year number (e.g., 2024)
    - entity_ids: comma-separated list of entity IDs (optional, if not provided, all entities)
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        metric = request.args.get('metric', 'total-amount')
        financial_year = request.args.get('financial_year', type=int)
        entity_ids_str = request.args.get('entity_ids', type=str)

        # Build where clause
        where_clauses = ["1=1"]
        params = []

        if financial_year:
            where_clauses.append("Year = %s")
            params.append(financial_year)

        # Handle entity filter
        entity_codes = []
        if entity_ids_str:
            entity_ids = [int(eid.strip()) for eid in entity_ids_str.split(',') if eid.strip().isdigit()]
            if entity_ids:
                placeholders = ','.join(['%s'] * len(entity_ids))
                entity_query = f"""
                    SELECT ent_code FROM entity_master
                    WHERE ent_id IN ({placeholders})
                """
                entity_rows = Database.execute_query(entity_query, params=entity_ids, fetch_all=True) or []
                entity_codes = [row.get('ent_code') for row in entity_rows if row.get('ent_code')]

        if entity_codes:
            placeholders = ','.join(['%s'] * len(entity_codes))
            where_clauses.append(f"entityCode IN ({placeholders})")
            params.extend(entity_codes)

        where_sql = " AND ".join(where_clauses)

        # Determine metric calculation based on metric type
        metric_field = "transactionAmount"
        category_filter = None

        if metric == 'total-assets':
            category_filter = "LOWER(TRIM(category1)) IN ('assets', 'asset', 'balance sheet')"
        elif metric == 'total-liabilities':
            category_filter = "LOWER(TRIM(category1)) IN ('liabilities', 'liability', 'balance sheet')"
        elif metric == 'total-equity':
            category_filter = "LOWER(TRIM(category1)) IN ('equity', 'balance sheet')"
        elif metric == 'total-revenue':
            category_filter = "LOWER(TRIM(category1)) IN ('revenue', 'income', 'profit and loss', 'profit & loss', 'p&l')"
        elif metric == 'total-expenses':
            category_filter = "LOWER(TRIM(category1)) IN ('expenses', 'expense', 'profit and loss', 'profit & loss', 'p&l')"
        elif metric == 'net-profit':
            # Revenue - Expenses
            category_filter = "LOWER(TRIM(category1)) IN ('revenue', 'income', 'expenses', 'expense', 'profit and loss', 'profit & loss', 'p&l')"

        if category_filter:
            where_sql += f" AND {category_filter}"

        # Build comparison query
        comparison_query = f"""
            SELECT 
                COALESCE(entityCode, 'N/A') as entity_code,
                COALESCE(entityName, 'Unknown Entity') as entity_name,
                COALESCE(SUM(transactionAmount), 0) as total_amount,
                COALESCE(SUM(transactionAmountUSD), 0) as total_amount_usd,
                COUNT(*) as record_count
            FROM final_structured
            WHERE {where_sql}
            GROUP BY COALESCE(entityCode, 'N/A'), COALESCE(entityName, 'Unknown Entity')
            ORDER BY total_amount DESC
        """

        comparison_data = Database.execute_query(
            comparison_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        # Normalize amounts
        for row in comparison_data:
            row['total_amount'] = _safe_float(row.get('total_amount'))
            row['total_amount_usd'] = _safe_float(row.get('total_amount_usd'))

        # Calculate totals and averages
        total_amount = sum([r.get('total_amount', 0) for r in comparison_data])
        total_amount_usd = sum([r.get('total_amount_usd', 0) for r in comparison_data])
        avg_amount = total_amount / len(comparison_data) if comparison_data else 0
        entity_count = len(comparison_data)

        return jsonify({
            'success': True,
            'data': {
                'metric': metric,
                'financial_year': financial_year,
                'comparison_data': comparison_data,
                'summary': {
                    'entity_count': entity_count,
                    'total_amount': total_amount,
                    'total_amount_usd': total_amount_usd,
                    'average_amount': avg_amount
                }
            }
        }), 200
    except Exception as e:
        print(f"❌ Error building comparison: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to build comparison data'
        }), 500


@reports_bp.route('/reports/alerts', methods=['GET', 'OPTIONS'])
def get_alerts():
    """
    Get red flags and alerts based on financial data analysis.
    Query params:
    - financial_year: year number (optional)
    - entity_id: entity ID (optional)
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        financial_year = request.args.get('financial_year', type=int)
        entity_id = request.args.get('entity_id', type=int)
        entity_code = request.args.get('entity_code', type=str)

        # Resolve entity_code
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

        alerts = []

        # 1. Check for high leverage (Debt-Equity ratio)
        leverage_query = f"""
            SELECT 
                COALESCE(entityCode, 'N/A') as entity_code,
                COALESCE(entityName, 'Unknown Entity') as entity_name,
                COALESCE(SUM(CASE 
                    WHEN LOWER(TRIM(category1)) LIKE '%liabilit%' 
                    OR LOWER(TRIM(category2)) LIKE '%debt%'
                    OR LOWER(TRIM(category2)) LIKE '%loan%'
                    THEN transactionAmount ELSE 0 END), 0) as total_debt,
                COALESCE(SUM(CASE 
                    WHEN LOWER(TRIM(category1)) LIKE '%equity%'
                    THEN transactionAmount ELSE 0 END), 0) as total_equity
            FROM final_structured
            WHERE {where_sql}
            GROUP BY COALESCE(entityCode, 'N/A'), COALESCE(entityName, 'Unknown Entity')
            HAVING total_equity > 0
        """
        leverage_data = Database.execute_query(
            leverage_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        for row in leverage_data:
            debt = _safe_float(row.get('total_debt', 0))
            equity = _safe_float(row.get('total_equity', 0))
            if equity > 0:
                debt_equity_ratio = abs(debt / equity)
                if debt_equity_ratio > 2.0:  # Threshold: 2:1
                    alerts.append({
                        'type': 'warning',
                        'severity': 'high',
                        'entity_code': row.get('entity_code'),
                        'entity_name': row.get('entity_name'),
                        'title': 'High Leverage',
                        'message': f"Debt-Equity ratio ({debt_equity_ratio:.2f}) above threshold (2.0)",
                        'metric': 'debt-equity-ratio',
                        'value': round(debt_equity_ratio, 2)
                    })

        # 2. Check for declining assets (YoY comparison)
        if financial_year:
            prev_year = financial_year - 1
            # Build where clause for both years - rebuild from scratch to avoid parameter issues
            assets_where_clauses = []
            assets_params = []
            
            if resolved_entity_code:
                assets_where_clauses.append("entityCode = %s")
                assets_params.append(resolved_entity_code)
            
            # Always include both years for comparison
            assets_where_clauses.append("Year IN (%s, %s)")
            assets_params.extend([financial_year, prev_year])
            
            assets_where_sql = " AND ".join(assets_where_clauses)
            
            assets_query = f"""
                SELECT 
                    COALESCE(entityCode, 'N/A') as entity_code,
                    COALESCE(entityName, 'Unknown Entity') as entity_name,
                    Year as year,
                    COALESCE(SUM(CASE 
                        WHEN LOWER(TRIM(category1)) IN ('assets', 'asset', 'balance sheet')
                        THEN transactionAmount ELSE 0 END), 0) as total_assets
                FROM final_structured
                WHERE {assets_where_sql}
                  AND LOWER(TRIM(category1)) IN ('assets', 'asset', 'balance sheet')
                GROUP BY COALESCE(entityCode, 'N/A'), COALESCE(entityName, 'Unknown Entity'), Year
                ORDER BY entity_code, Year
            """

            assets_data = Database.execute_query(
                assets_query,
                params=assets_params,
                fetch_all=True
            ) or []

            # Group by entity and compare years
            entity_assets = {}
            entity_names = {}
            for row in assets_data:
                ec = row.get('entity_code')
                if ec not in entity_assets:
                    entity_assets[ec] = {}
                    entity_names[ec] = row.get('entity_name', ec)
                entity_assets[ec][row.get('year')] = _safe_float(row.get('total_assets', 0))

            for entity_code, years_data in entity_assets.items():
                current = years_data.get(financial_year, 0)
                previous = years_data.get(prev_year, 0)
                if previous > 0 and current > 0:
                    decline_pct = ((previous - current) / previous) * 100
                    if decline_pct >= 15:  # 15% decline threshold
                        entity_name = entity_names.get(entity_code, entity_code)
                        alerts.append({
                            'type': 'error',
                            'severity': 'high',
                            'entity_code': entity_code,
                            'entity_name': entity_name,
                            'title': 'Declining Assets',
                            'message': f"{decline_pct:.1f}% drop YoY (from {prev_year} to {financial_year})",
                            'metric': 'asset-decline',
                            'value': round(decline_pct, 1)
                        })

        # 3. Check for unmapped accounts with high amounts
        unmapped_query = f"""
            SELECT 
                COALESCE(entityCode, 'N/A') as entity_code,
                COALESCE(entityName, 'Unknown Entity') as entity_name,
                COALESCE(SUM(transactionAmount), 0) as unmapped_amount,
                COUNT(*) as unmapped_count
            FROM final_structured
            WHERE {where_sql}
              AND (mainCategory IS NULL OR TRIM(mainCategory) = '')
            GROUP BY COALESCE(entityCode, 'N/A'), COALESCE(entityName, 'Unknown Entity')
            HAVING unmapped_amount > 1000000  -- Threshold: 1M
        """
        unmapped_data = Database.execute_query(
            unmapped_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        for row in unmapped_data:
            unmapped_amount = _safe_float(row.get('unmapped_amount', 0))
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'entity_code': row.get('entity_code'),
                'entity_name': row.get('entity_name'),
                'title': 'High Unmapped Amount',
                'message': f"{row.get('unmapped_count')} unmapped accounts totaling {unmapped_amount:,.0f}",
                'metric': 'unmapped-amount',
                'value': unmapped_amount
            })

        # 4. Check for FX gaps
        fx_gap_query = f"""
            SELECT 
                COALESCE(entityCode, 'N/A') as entity_code,
                COALESCE(entityName, 'Unknown Entity') as entity_name,
                COUNT(*) as missing_fx_count
            FROM final_structured
            WHERE {where_sql}
              AND (Avg_Fx_Rt IS NULL OR TRIM(Avg_Fx_Rt) = '')
              AND localCurrencyCode IS NOT NULL
              AND localCurrencyCode != 'INR'
            GROUP BY COALESCE(entityCode, 'N/A'), COALESCE(entityName, 'Unknown Entity')
            HAVING missing_fx_count > 10  -- Threshold: 10 rows
        """
        fx_gap_data = Database.execute_query(
            fx_gap_query,
            params=params if params else None,
            fetch_all=True
        ) or []

        for row in fx_gap_data:
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'entity_code': row.get('entity_code'),
                'entity_name': row.get('entity_name'),
                'title': 'Missing FX Rates',
                'message': f"{row.get('missing_fx_count')} rows missing foreign exchange rates",
                'metric': 'fx-gaps',
                'value': row.get('missing_fx_count')
            })

        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'count': len(alerts)
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching alerts: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to fetch alerts'
        }), 500


@reports_bp.route('/reports/export', methods=['GET', 'OPTIONS'])
def export_report():
    """
    Export report data to Excel/CSV format.
    Query params: same as comparison endpoint
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        # For now, return JSON data that can be exported
        # Full Excel export can be implemented later with openpyxl
        metric = request.args.get('metric', 'total-amount')
        financial_year = request.args.get('financial_year', type=int)
        entity_ids_str = request.args.get('entity_ids', type=str)

        # Reuse comparison logic
        # This is a simplified version - full implementation would generate Excel file
        return jsonify({
            'success': True,
            'message': 'Export functionality - use comparison endpoint data',
            'data': {
                'metric': metric,
                'financial_year': financial_year,
                'export_url': f'/reports/comparison?metric={metric}&financial_year={financial_year}'
            }
        }), 200
    except Exception as e:
        print(f"❌ Error exporting report: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Failed to export report'
        }), 500

