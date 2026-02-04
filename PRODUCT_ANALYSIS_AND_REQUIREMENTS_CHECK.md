# Product Analysis and Requirements Check

## Product Overview

This is a **Multi-Entity Financial Platform** that allows:
- Entity management (hierarchical structure)
- Excel file uploads for financial data
- Forex rate management (both legacy and FY-specific)
- Structured data processing and consolidation
- Reports and dashboards
- Code master mapping for account classification

**Tech Stack:**
- Frontend: React + TypeScript + Vite + shadcn-ui + Tailwind CSS
- Backend: Flask + MySQL + JWT Authentication

---

## Requirements Analysis

### ✅ Requirement 1: Edit Option for Forex Data Entry

**Status: IMPLEMENTED**

**Location:**
- Frontend: `entity-insights-hub/src/pages/Forex.tsx` (lines 172-203, 446-568)
- Backend: `backend/routes/forex.py` (lines 747-756)

**Implementation Details:**
- The Forex page has **inline editing** functionality
- Users can click on `opening_rate` or `closing_rate` values in the table to edit them
- Changes are saved via PUT request to `/forex/entity/<entity_id>/financial-year/<financial_year>`
- The backend endpoint `updateEntityFYRates` handles the updates

**Evidence:**
```typescript
// Forex.tsx - Inline editing
const handleUpdate = async (rate: ForexRate, field: "opening_rate" | "closing_rate", value: string) => {
  // ... validation and API call
  const res = await forexApi.updateEntityFYRates(rate.entity_id, rate.financial_year, payload);
}
```

**Conclusion:** ✅ This requirement is **PRESENT** and working.

---

### ❌ Requirement 2: Master Data Section for Financial Year

**Status: NOT IMPLEMENTED**

**Current State:**
- Financial years are fetched dynamically from `month_master` table
- No master data management interface for financial years
- No validation that data can only be uploaded within configured financial year ranges
- No master table that defines valid financial year ranges with start/end dates

**What's Missing:**
1. **Master Data Table:** A `financial_year_master` table with:
   - `financial_year` (e.g., "2024-25")
   - `start_date` (e.g., "2024-04-01")
   - `end_date` (e.g., "2025-03-31")
   - `is_active` (boolean)
   - `created_at`, `updated_at`

2. **Master Data UI:** A section in Settings or a dedicated page to:
   - Add new financial years
   - Edit existing financial year ranges
   - Activate/deactivate financial years
   - View all configured financial years

3. **Validation Logic:** During data upload:
   - Check if the selected month/year falls within any active financial year range
   - Reject uploads if data is outside configured ranges
   - Example: Data for April 2026 should be rejected if no FY 2026-27 is configured

**Current Implementation:**
```python
# backend/routes/upload_data.py - Line 804-851
@upload_bp.route('/financial-years', methods=['GET', 'OPTIONS'])
def get_financial_years():
    """Get distinct financial years from month_master"""
    query = """
        SELECT DISTINCT year 
        FROM month_master 
        ORDER BY year DESC
    """
    # No validation against master data
```

**Conclusion:** ❌ This requirement is **NOT PRESENT**. It needs to be implemented.

---

### ⚠️ Requirement 3: Currency Calculations Based on Financial Year

**Status: PARTIALLY IMPLEMENTED**

**Current Implementation:**
- The system has FY-specific forex rates in `entity_forex_rates` table
- Calculations use `opening_rate` and `closing_rate` for the financial year
- P&L items use average of (opening_rate + closing_rate) / 2
- Balance Sheet items use closing_rate

**What's Working:**
```python
# backend/routes/structure_data.py - Lines 142-270
def _apply_forex_rates(rows, forex_cache):
    # Tries to get FY-specific rates
    if entity_id and financial_year:
        cache_key = f"{entity_id}_{curr}_{financial_year}"
        fx = forex_cache.get(cache_key)
        
        # Uses opening_rate and closing_rate for calculations
        if fx.get('opening_rate') and fx.get('closing_rate'):
            avg_rate_pl = (fx['opening_rate'] + fx['closing_rate']) / 2.0
```

**Issues/Concerns:**
1. **Adjacent Year Fallback:** The system tries adjacent years if exact match fails:
   ```python
   # If not found, try adjacent years
   if not fx:
       try_next_fy = financial_year + 1
       cache_key = f"{entity_id}_{curr}_{try_next_fy}"
       fx = forex_cache.get(cache_key)
   ```
   This may not align with the requirement that calculations should use rates **within the same financial year**.

2. **No Strict Enforcement:** The requirement states:
   > "The calculations of the common currency should be basis the rates within the financial year and the data pertaining to the same financial year."
   
   Currently, the system:
   - Tries to match FY rates
   - Falls back to adjacent years
   - Falls back to legacy rates
   
   This doesn't strictly enforce that data and rates must be from the **same** financial year.

3. **Example Issue:**
   - Data for FY 2024-25 (April 2024 to March 2025)
   - If rates for FY 2024-25 are not found, system may use rates from FY 2023-24 or FY 2025-26
   - This violates the requirement

**What Needs to be Fixed:**
1. **Strict Matching:** Only use rates from the exact same financial year as the data
2. **Validation:** Ensure data and rates are from the same FY before calculation
3. **Error Handling:** If rates for a specific FY are missing, show an error instead of using fallback rates

**Conclusion:** ⚠️ This requirement is **PARTIALLY IMPLEMENTED** but needs refinement to strictly enforce same-FY matching.

---

## Summary Table

| Requirement | Status | Notes |
|------------|--------|-------|
| 1. Edit Option for Forex Data | ✅ **PRESENT** | Inline editing works in Forex.tsx |
| 2. Master Data Section for Financial Year | ❌ **NOT PRESENT** | Needs implementation: table, UI, and validation |
| 3. Currency Calculations Based on FY | ⚠️ **PARTIAL** | Works but needs strict same-FY enforcement |

---

## Recommendations

### For Requirement 2 (Master Data Section):
1. Create `financial_year_master` table
2. Add UI in Settings page or create dedicated "Master Data" section
3. Implement validation in upload endpoint to check against master data
4. Add API endpoints for CRUD operations on financial year master

### For Requirement 3 (Currency Calculations):
1. Remove adjacent year fallback logic
2. Add strict validation: data and rates must be from same FY
3. Show clear error messages if rates are missing for a specific FY
4. Ensure P&L calculations use average of opening_rate and closing_rate from the same FY as the data

---

## Files to Review

**Forex Editing (Requirement 1):**
- `entity-insights-hub/src/pages/Forex.tsx`
- `backend/routes/forex.py` (updateEntityFYRates endpoint)

**Master Data (Requirement 2):**
- Need to create: `financial_year_master` table
- Need to create: Master data management UI
- Need to update: `backend/routes/upload_data.py` (add validation)

**Currency Calculations (Requirement 3):**
- `backend/routes/structure_data.py` (_apply_forex_rates, _calculate_and_save_forex_rates)
- `backend/routes/forex.py` (get_entity_fy_forex_rate)
