"""
Entity routes for managing entity_master
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback

from database import Database

entity_bp = Blueprint('entity', __name__)


def _get_all_descendants(entity_id):
    """
    Recursively get all descendant entity IDs (children, grandchildren, etc.)
    Returns: list of entity IDs
    """
    descendants = []
    children_query = "SELECT ent_id FROM entity_master WHERE parent_entity_id = %s"
    children = Database.execute_query(children_query, params=[entity_id], fetch_all=True) or []
    
    for child in children:
        child_id = child.get('ent_id')
        descendants.append(child_id)
        # Recursively get descendants of this child
        descendants.extend(_get_all_descendants(child_id))
    
    return descendants


def _would_create_circular_reference(child_id, parent_id):
    """
    Check if setting parent_id for child_id would create a circular reference.
    Returns: True if circular reference would occur, False otherwise
    """
    if child_id == parent_id:
        return True
    
    # Get all descendants of child_id
    descendants = _get_all_descendants(child_id)
    
    # If parent_id is in the descendants, it would create a cycle
    return parent_id in descendants


@entity_bp.route('/entities', methods=['GET', 'OPTIONS'])
def list_entities():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        query = """
            SELECT 
                e.ent_id,
                e.ent_name,
                e.ent_code,
                e.lcl_curr,
                e.city,
                e.country,
                e.financial_year_start_month,
                e.financial_year_start_day,
                e.parent_entity_id,
                p.ent_name as parent_name,
                p.ent_code as parent_code
            FROM entity_master e
            LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
            ORDER BY e.ent_name ASC
        """
        rows = Database.execute_query(query, fetch_all=True)
        return jsonify({
            'success': True,
            'data': {
                'entities': rows or []
            }
        }), 200
    except Exception as e:
        print(f"❌ Error listing entities: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch entities'}), 500


@entity_bp.route('/entities', methods=['POST'])
@jwt_required()
def create_entity():
    try:
        payload = request.get_json(silent=True) or {}
        ent_name = (payload.get('ent_name') or '').strip()
        ent_code = (payload.get('ent_code') or '').strip()
        lcl_curr = (payload.get('lcl_curr') or '').strip().upper()
        city = (payload.get('city') or '').strip()
        country = (payload.get('country') or '').strip()
        financial_year_start_month = payload.get('financial_year_start_month', 4)  # Default to April
        financial_year_start_day = payload.get('financial_year_start_day', 1)  # Default to 1st
        parent_entity_id = payload.get('parent_entity_id')  # Can be None or int

        if not ent_name or not ent_code or not lcl_curr:
            return jsonify({
                'success': False,
                'message': 'ent_name, ent_code and lcl_curr are required'
            }), 400

        # Validate FY start month (1-12)
        if financial_year_start_month and (financial_year_start_month < 1 or financial_year_start_month > 12):
            return jsonify({
                'success': False,
                'message': 'financial_year_start_month must be between 1 and 12'
            }), 400

        # Validate FY start day (1-31)
        if financial_year_start_day and (financial_year_start_day < 1 or financial_year_start_day > 31):
            return jsonify({
                'success': False,
                'message': 'financial_year_start_day must be between 1 and 31'
            }), 400

        # Validate parent_entity_id if provided
        if parent_entity_id is not None:
            if parent_entity_id == 0:
                parent_entity_id = None  # Convert 0 to None
            elif isinstance(parent_entity_id, int) and parent_entity_id > 0:
                # Check if parent exists
                parent_check = "SELECT ent_id FROM entity_master WHERE ent_id = %s"
                parent_exists = Database.execute_query(parent_check, params=[parent_entity_id], fetch_one=True)
                if not parent_exists:
                    return jsonify({
                        'success': False,
                        'message': f'Parent entity with id {parent_entity_id} does not exist'
                    }), 400

        insert = """
            INSERT INTO entity_master (ent_name, ent_code, lcl_curr, city, country, financial_year_start_month, financial_year_start_day, parent_entity_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [ent_name, ent_code, lcl_curr, city or None, country or None, financial_year_start_month, financial_year_start_day, parent_entity_id]
        new_id = Database.execute_query(insert, params=params)

        # Add currency to forex_master if it doesn't exist
        try:
            check_forex = """
                SELECT fx_id FROM forex_master WHERE currency = %s LIMIT 1
            """
            existing_forex = Database.execute_query(check_forex, params=[lcl_curr], fetch_one=True)
            
            if not existing_forex:
                # Insert new row with currency and null values
                insert_forex = """
                    INSERT INTO forex_master (currency, initial_rate, latest_rate, month, updated_at)
                    VALUES (%s, NULL, NULL, NULL, CURDATE())
                """
                Database.execute_query(insert_forex, params=[lcl_curr])
                print(f"✅ Added new currency {lcl_curr} to forex_master")
        except Exception as forex_error:
            # Don't fail entity creation if forex insert fails
            print(f"⚠️ Failed to add currency to forex_master: {str(forex_error)}")

        # return the created entity
        get_q = """
            SELECT 
                e.ent_id, 
                e.ent_name, 
                e.ent_code, 
                e.lcl_curr, 
                e.city, 
                e.country, 
                e.financial_year_start_month, 
                e.financial_year_start_day,
                e.parent_entity_id,
                p.ent_name as parent_name,
                p.ent_code as parent_code
            FROM entity_master e
            LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
            WHERE e.ent_id = %s
        """
        created = Database.execute_query(get_q, params=[new_id], fetch_one=True)

        return jsonify({
            'success': True,
            'message': 'Entity created successfully',
            'data': created
        }), 201
    except Exception as e:
        print(f"❌ Error creating entity: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to create entity'}), 500


@entity_bp.route('/entities/<int:ent_id>', methods=['PUT', 'OPTIONS'])
@jwt_required()
def update_entity(ent_id):
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        payload = request.get_json(silent=True) or {}
        ent_name = (payload.get('ent_name') or '').strip()
        ent_code = (payload.get('ent_code') or '').strip()
        lcl_curr = (payload.get('lcl_curr') or '').strip().upper()
        city = (payload.get('city') or '').strip()
        country = (payload.get('country') or '').strip()
        financial_year_start_month = payload.get('financial_year_start_month')
        financial_year_start_day = payload.get('financial_year_start_day')
        parent_entity_id = payload.get('parent_entity_id')  # Can be None, 0, or int

        if not ent_name or not ent_code or not lcl_curr:
            return jsonify({
                'success': False,
                'message': 'ent_name, ent_code and lcl_curr are required'
            }), 400

        # Validate FY start month if provided
        if financial_year_start_month is not None and (financial_year_start_month < 1 or financial_year_start_month > 12):
            return jsonify({
                'success': False,
                'message': 'financial_year_start_month must be between 1 and 12'
            }), 400

        # Validate FY start day if provided
        if financial_year_start_day is not None and (financial_year_start_day < 1 or financial_year_start_day > 31):
            return jsonify({
                'success': False,
                'message': 'financial_year_start_day must be between 1 and 31'
            }), 400

        # Check if entity exists
        check_query = "SELECT ent_id, lcl_curr FROM entity_master WHERE ent_id = %s"
        existing = Database.execute_query(check_query, params=[ent_id], fetch_one=True)
        if not existing:
            return jsonify({'success': False, 'message': 'Entity not found'}), 404

        old_currency = existing.get('lcl_curr')
        
        # Validate parent_entity_id if provided
        if parent_entity_id is not None:
            if parent_entity_id == 0:
                parent_entity_id = None  # Convert 0 to None
            elif isinstance(parent_entity_id, int) and parent_entity_id > 0:
                # Prevent entity from being its own parent
                if parent_entity_id == ent_id:
                    return jsonify({
                        'success': False,
                        'message': 'Entity cannot be its own parent'
                    }), 400
                
                # Check if parent exists
                parent_check = "SELECT ent_id FROM entity_master WHERE ent_id = %s"
                parent_exists = Database.execute_query(parent_check, params=[parent_entity_id], fetch_one=True)
                if not parent_exists:
                    return jsonify({
                        'success': False,
                        'message': f'Parent entity with id {parent_entity_id} does not exist'
                    }), 400
                
                # Check for circular reference (prevent descendant from being parent)
                if _would_create_circular_reference(ent_id, parent_entity_id):
                    return jsonify({
                        'success': False,
                        'message': 'Cannot set parent: it would create a circular reference'
                    }), 400
        
        # Build update query dynamically based on provided fields
        update_fields = [
            "ent_name = %s",
            "ent_code = %s",
            "lcl_curr = %s",
            "city = %s",
            "country = %s"
        ]
        params = [ent_name, ent_code, lcl_curr, city or None, country or None]
        
        if financial_year_start_month is not None:
            update_fields.append("financial_year_start_month = %s")
            params.append(financial_year_start_month)
        
        if financial_year_start_day is not None:
            update_fields.append("financial_year_start_day = %s")
            params.append(financial_year_start_day)
        
        # Handle parent_entity_id (can be explicitly set to None)
        if 'parent_entity_id' in payload:
            update_fields.append("parent_entity_id = %s")
            params.append(parent_entity_id)
        
        params.append(ent_id)  # For WHERE clause
        
        update_query = f"""
            UPDATE entity_master
            SET {', '.join(update_fields)}
            WHERE ent_id = %s
        """
        Database.execute_query(update_query, params=params)

        # If currency changed, add new currency to forex_master if it doesn't exist
        if lcl_curr != old_currency:
            try:
                check_forex = """
                    SELECT fx_id FROM forex_master WHERE currency = %s LIMIT 1
                """
                existing_forex = Database.execute_query(check_forex, params=[lcl_curr], fetch_one=True)
                
                if not existing_forex:
                    insert_forex = """
                        INSERT INTO forex_master (currency, initial_rate, latest_rate, month, updated_at)
                        VALUES (%s, NULL, NULL, NULL, CURDATE())
                    """
                    Database.execute_query(insert_forex, params=[lcl_curr])
                    print(f"✅ Added new currency {lcl_curr} to forex_master")
            except Exception as forex_error:
                print(f"⚠️ Failed to add currency to forex_master: {str(forex_error)}")

        # Get the updated entity
        get_q = """
            SELECT 
                e.ent_id, 
                e.ent_name, 
                e.ent_code, 
                e.lcl_curr, 
                e.city, 
                e.country, 
                e.financial_year_start_month, 
                e.financial_year_start_day,
                e.parent_entity_id,
                p.ent_name as parent_name,
                p.ent_code as parent_code
            FROM entity_master e
            LEFT JOIN entity_master p ON e.parent_entity_id = p.ent_id
            WHERE e.ent_id = %s
        """
        updated = Database.execute_query(get_q, params=[ent_id], fetch_one=True)

        return jsonify({
            'success': True,
            'message': 'Entity updated successfully',
            'data': updated
        }), 200
    except Exception as e:
        print(f"❌ Error updating entity: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to update entity'}), 500


@entity_bp.route('/entities/<int:ent_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_entity(ent_id):
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        # Check if entity exists
        check_query = "SELECT ent_id, ent_name, ent_code FROM entity_master WHERE ent_id = %s"
        existing = Database.execute_query(check_query, params=[ent_id], fetch_one=True)
        if not existing:
            return jsonify({'success': False, 'message': 'Entity not found'}), 404

        print(f"🗑️ Deleting entity ent_id={ent_id}: {existing.get('ent_name')} ({existing.get('ent_code')})")

        # Delete the entity
        delete_query = "DELETE FROM entity_master WHERE ent_id = %s"
        Database.execute_query(delete_query, params=[ent_id])

        print(f"✅ Entity deleted successfully: ent_id={ent_id}")
        return jsonify({
            'success': True,
            'message': 'Entity deleted successfully'
        }), 200
    except Exception as e:
        print(f"❌ Error deleting entity: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to delete entity'}), 500


@entity_bp.route('/entities/<int:ent_id>/children', methods=['GET', 'OPTIONS'])
def get_children(ent_id):
    """Get direct children of an entity"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Check if entity exists
        check_query = "SELECT ent_id, ent_name FROM entity_master WHERE ent_id = %s"
        entity = Database.execute_query(check_query, params=[ent_id], fetch_one=True)
        if not entity:
            return jsonify({'success': False, 'message': 'Entity not found'}), 404
        
        query = """
            SELECT 
                ent_id,
                ent_name,
                ent_code,
                lcl_curr,
                city,
                country,
                financial_year_start_month,
                financial_year_start_day,
                parent_entity_id
            FROM entity_master
            WHERE parent_entity_id = %s
            ORDER BY ent_name ASC
        """
        children = Database.execute_query(query, params=[ent_id], fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': ent_id,
                'entity_name': entity.get('ent_name'),
                'children': children
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching children: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch children'}), 500


@entity_bp.route('/entities/<int:ent_id>/parent', methods=['GET', 'OPTIONS'])
def get_parent(ent_id):
    """Get parent entity of an entity"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT 
                p.ent_id,
                p.ent_name,
                p.ent_code,
                p.lcl_curr,
                p.city,
                p.country,
                p.financial_year_start_month,
                p.financial_year_start_day,
                p.parent_entity_id
            FROM entity_master e
            INNER JOIN entity_master p ON e.parent_entity_id = p.ent_id
            WHERE e.ent_id = %s
        """
        parent = Database.execute_query(query, params=[ent_id], fetch_one=True)
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': ent_id,
                'parent': parent
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching parent: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch parent'}), 500


@entity_bp.route('/entities/<int:ent_id>/descendants', methods=['GET', 'OPTIONS'])
def get_descendants(ent_id):
    """Get all descendants (children, grandchildren, etc.) of an entity"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Check if entity exists
        check_query = "SELECT ent_id, ent_name FROM entity_master WHERE ent_id = %s"
        entity = Database.execute_query(check_query, params=[ent_id], fetch_one=True)
        if not entity:
            return jsonify({'success': False, 'message': 'Entity not found'}), 404
        
        # Get all descendant IDs recursively
        descendant_ids = _get_all_descendants(ent_id)
        
        if not descendant_ids:
            return jsonify({
                'success': True,
                'data': {
                    'entity_id': ent_id,
                    'entity_name': entity.get('ent_name'),
                    'descendants': []
                }
            }), 200
        
        # Get full details of all descendants
        placeholders = ','.join(['%s'] * len(descendant_ids))
        query = f"""
            SELECT 
                ent_id,
                ent_name,
                ent_code,
                lcl_curr,
                city,
                country,
                financial_year_start_month,
                financial_year_start_day,
                parent_entity_id
            FROM entity_master
            WHERE ent_id IN ({placeholders})
            ORDER BY ent_name ASC
        """
        descendants = Database.execute_query(query, params=descendant_ids, fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entity_id': ent_id,
                'entity_name': entity.get('ent_name'),
                'descendants': descendants
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching descendants: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch descendants'}), 500


@entity_bp.route('/entities/<int:ent_id>/hierarchy', methods=['GET', 'OPTIONS'])
def get_hierarchy(ent_id):
    """Get full hierarchy: entity, parent, children, and grandchildren"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get entity itself
        entity_query = """
            SELECT 
                e.ent_id,
                e.ent_name,
                e.ent_code,
                e.lcl_curr,
                e.city,
                e.country,
                e.financial_year_start_month,
                e.financial_year_start_day,
                e.parent_entity_id
            FROM entity_master e
            WHERE e.ent_id = %s
        """
        entity = Database.execute_query(entity_query, params=[ent_id], fetch_one=True)
        if not entity:
            return jsonify({'success': False, 'message': 'Entity not found'}), 404
        
        # Get parent
        parent = None
        if entity.get('parent_entity_id'):
            parent_query = """
                SELECT 
                    ent_id,
                    ent_name,
                    ent_code,
                    lcl_curr,
                    city,
                    country,
                    financial_year_start_month,
                    financial_year_start_day,
                    parent_entity_id
                FROM entity_master
                WHERE ent_id = %s
            """
            parent = Database.execute_query(parent_query, params=[entity.get('parent_entity_id')], fetch_one=True)
        
        # Get direct children
        children_query = """
            SELECT 
                ent_id,
                ent_name,
                ent_code,
                lcl_curr,
                city,
                country,
                financial_year_start_month,
                financial_year_start_day,
                parent_entity_id
            FROM entity_master
            WHERE parent_entity_id = %s
            ORDER BY ent_name ASC
        """
        children = Database.execute_query(children_query, params=[ent_id], fetch_all=True) or []
        
        # Get grandchildren (children of children)
        grandchildren = []
        if children:
            child_ids = [c.get('ent_id') for c in children]
            placeholders = ','.join(['%s'] * len(child_ids))
            grandchildren_query = f"""
                SELECT 
                    ent_id,
                    ent_name,
                    ent_code,
                    lcl_curr,
                    city,
                    country,
                    financial_year_start_month,
                    financial_year_start_day,
                    parent_entity_id
                FROM entity_master
                WHERE parent_entity_id IN ({placeholders})
                ORDER BY ent_name ASC
            """
            grandchildren = Database.execute_query(grandchildren_query, params=child_ids, fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entity': entity,
                'parent': parent,
                'children': children,
                'grandchildren': grandchildren
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching hierarchy: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch hierarchy'}), 500


@entity_bp.route('/entities/roots', methods=['GET', 'OPTIONS'])
def get_root_entities():
    """Get all root entities (entities with no parent)"""
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        query = """
            SELECT 
                e.ent_id,
                e.ent_name,
                e.ent_code,
                e.lcl_curr,
                e.city,
                e.country,
                e.financial_year_start_month,
                e.financial_year_start_day,
                e.parent_entity_id
            FROM entity_master e
            WHERE e.parent_entity_id IS NULL
            ORDER BY e.ent_name ASC
        """
        roots = Database.execute_query(query, fetch_all=True) or []
        
        return jsonify({
            'success': True,
            'data': {
                'entities': roots
            }
        }), 200
    except Exception as e:
        print(f"❌ Error fetching root entities: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch root entities'}), 500






