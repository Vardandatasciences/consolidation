"""
Migration script to fix existing transactionAmount signs in final_structured table.
This script reads from rawData to determine Dr/Cr and updates final_structured accordingly.

Dr -> Positive value
Cr -> Negative value
"""
import re
from database import Database

def parse_amount_and_type(cell_value):
    """Parse cell value to extract Dr/Cr type"""
    if cell_value is None:
        return None, None
    
    cell_str = str(cell_value).strip()
    
    if cell_str == '' or cell_str.lower() in ['nan', 'none', 'null', '']:
        return None, None
    
    # Check if it contains Dr or Cr
    if 'Dr' in cell_str or 'dr' in cell_str or 'DR' in cell_str:
        amount_type = 'Dr'
    elif 'Cr' in cell_str or 'cr' in cell_str or 'CR' in cell_str:
        amount_type = 'Cr'
    else:
        return None, None
    
    # Extract numeric value
    amount_match = re.search(r'[\d,]+\.?\d*', cell_str)
    if amount_match:
        amount_str = amount_match.group().replace(',', '')
        try:
            amount = float(amount_str)
            return amount, amount_type
        except ValueError:
            return None, None
    
    return None, None


def fix_existing_data():
    """Fix signs in final_structured based on rawData"""
    print("🔧 Starting sign correction for existing data...")
    
    # Get all records from final_structured
    query = """
        SELECT 
            fs.sl_no,
            fs.Particular,
            fs.transactionAmount,
            fs.Month,
            fs.entityName,
            fs.Year,
            rd.EntityID,
            rd.PeriodID,
            rd.OpeningBalance,
            rd.Transactions,
            rd.Particular as raw_particular
        FROM final_structured fs
        LEFT JOIN rawData rd ON 
            fs.Particular = rd.Particular 
            AND fs.entityName = (SELECT ent_name FROM entity_master WHERE ent_id = rd.EntityID)
            AND fs.Year = (SELECT year FROM month_master WHERE mnt_id = rd.PeriodID)
        WHERE fs.transactionAmount IS NOT NULL
        ORDER BY fs.sl_no
    """
    
    records = Database.execute_query(query, fetch_all=True)
    
    if not records:
        print("❌ No records found in final_structured")
        return
    
    print(f"📊 Found {len(records)} records to check")
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for record in records:
        try:
            sl_no = record['sl_no']
            particular = record['Particular']
            current_amount = float(record['transactionAmount'])
            month = record['Month']
            
            # Determine which raw column to check based on Month field
            if month and month.lower() == 'opening':
                raw_value = record.get('OpeningBalance')
            else:
                raw_value = record.get('Transactions')
            
            if not raw_value:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"⏭️ Skipped sl_no={sl_no}, {particular}: No raw data found")
                continue
            
            # Parse the raw value to get Dr/Cr type
            amount, amount_type = parse_amount_and_type(raw_value)
            
            if not amount_type:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"⏭️ Skipped sl_no={sl_no}, {particular}: Could not determine Dr/Cr from '{raw_value}'")
                continue
            
            # Calculate correct signed amount
            if amount_type == 'Dr':
                correct_amount = abs(current_amount)  # Should be positive
            else:  # Cr
                correct_amount = -abs(current_amount)  # Should be negative
            
            # Only update if the sign is wrong
            if current_amount != correct_amount:
                update_query = """
                    UPDATE final_structured
                    SET transactionAmount = %s
                    WHERE sl_no = %s
                """
                Database.execute_query(update_query, params=[correct_amount, sl_no])
                updated_count += 1
                
                if updated_count <= 10:
                    print(f"✅ Updated sl_no={sl_no}, {particular}: {current_amount} → {correct_amount} ({amount_type})")
            
        except Exception as e:
            error_count += 1
            if error_count <= 5:
                print(f"❌ Error processing sl_no={sl_no}: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print(f"🎉 Sign Correction Complete!")
    print(f"{'='*60}")
    print(f"✅ Updated: {updated_count} records")
    print(f"⏭️ Skipped: {skipped_count} records (no raw data or couldn't parse)")
    print(f"❌ Errors: {error_count} records")
    print(f"📊 Total processed: {len(records)} records")
    print(f"{'='*60}\n")
    
    # Also update transactionAmountUSD if Avg_Fx_Rt exists
    if updated_count > 0:
        print("🔄 Recalculating transactionAmountUSD...")
        usd_query = """
            UPDATE final_structured
            SET transactionAmountUSD = CASE 
                WHEN Avg_Fx_Rt IS NOT NULL AND transactionAmount IS NOT NULL 
                THEN transactionAmount * Avg_Fx_Rt
                ELSE NULL
            END
            WHERE transactionAmount IS NOT NULL
        """
        Database.execute_query(usd_query)
        print("✅ transactionAmountUSD recalculated")


if __name__ == '__main__':
    try:
        fix_existing_data()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()

