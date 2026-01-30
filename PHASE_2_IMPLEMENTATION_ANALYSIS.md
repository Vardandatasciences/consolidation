# Phase 2 Requirements - Detailed Implementation Analysis

## Executive Summary

This document provides a comprehensive analysis of the current system, Phase 2 requirements, their importance, and detailed implementation guidance.

---

## 1. CURRENT SYSTEM ANALYSIS

### 1.1 Database Schema Overview

#### Existing Tables:
1. **`users`** - User authentication and authorization
2. **`entity_master`** - Entity information
   - Fields: `ent_id`, `ent_name`, `ent_code`, `lcl_curr`, `city`, `country`
   - **MISSING**: Parent-child relationship fields
3. **`forex_master`** - Forex rates
   - Fields: `fx_id`, `currency`, `initial_rate`, `latest_rate`, `month`, `updated_at`
   - **LIMITATION**: No financial year association
4. **`final_structured`** - Processed financial data
   - Fields: `sl_no`, `entityCode`, `entityName`, `Year`, `Month`, `Particular`, `transactionAmount`, `localCurrencyCode`, `Avg_Fx_Rt`, `transactionAmountUSD`, `mainCategory`, `category1-5`
5. **`code_master`** - Account mapping
6. **`rawData`** - Raw uploaded data
7. **`upload_history`** - Upload tracking

### 1.2 Current Functionality

#### Backend Capabilities:
- ✅ Entity CRUD operations (`/entities`)
- ✅ Forex rate management (`/forex`) - but **NOT financial year specific**
- ✅ Data upload and processing (`/upload`)
- ✅ Structured data retrieval (`/structure/data`)
- ✅ Dashboard analytics (`/dashboard/overview`)
- ✅ Reports and comparisons (`/reports/comparison`)
- ✅ Multi-entity filtering by `entity_id` or `entity_code`
- ✅ Financial year filtering in queries

#### Frontend Capabilities:
- ✅ Dashboard with KPIs, charts, trends
- ✅ Entity management UI
- ✅ Reports page with cross-entity comparisons
- ✅ Data upload interface
- ✅ Structured data viewing

### 1.3 Current Limitations

1. **Forex Rates**: Not tied to financial years
   - Current: Single `initial_rate` and `latest_rate` per currency
   - Missing: Financial year-specific opening/closing rates

2. **Entity Relationships**: No parent-child structure
   - Current: Flat entity list
   - Missing: Parent company, child company relationships

3. **Consolidation**: No multi-entity consolidation logic
   - Current: Individual entity reports only
   - Missing: City/Country/Parent-Child/Manual selection consolidation

4. **Monthly Updates**: No explicit monthly update tracking
   - Current: Data can be uploaded monthly, but no structured tracking

5. **Category 5 Related Parties**: No special handling
   - Current: `category5` exists but no special reporting

---

## 2. PHASE 2 REQUIREMENTS ANALYSIS

### 2.1 Requirement 1: Financial Year-Based Forex Rates

**Requirement:**
> "There should be a financial year for each entity. Under which the forex rates should be considered. The rates should be independent for each financial year. Opening rate will be at the start of the financial year, and the closing rate will be a maximum 12 months from the financial year start. Next financial year, the rates will be updated for Opening and closing."

**Why It's Important:**
- **Accuracy**: Financial statements must use rates from the correct financial year
- **Compliance**: Accounting standards require period-specific exchange rates
- **Audit Trail**: Historical rate tracking for each FY ensures transparency
- **Multi-Year Analysis**: Enables accurate year-over-year comparisons

**Current Gap:**
- Forex rates are currency-based only, not financial year-based
- No mechanism to store opening/closing rates per financial year per entity

**Implementation Impact:**
- **Database**: New table or schema changes required
- **Backend**: Forex API needs financial year parameters
- **Frontend**: Forex management UI needs FY selection
- **Data Processing**: All forex calculations must use FY-specific rates

---

### 2.2 Requirement 2: Monthly Data Updates

**Requirement:**
> "The data may be updated each month from the trial balances. This will be as per the location, country, name, month and financial year."

**Why It's Important:**
- **Incremental Updates**: Allows monthly refresh without full re-upload
- **Data Freshness**: Keeps financial data current
- **Audit Compliance**: Tracks when data was last updated
- **Selective Updates**: Update specific entities/locations without affecting others

**Current Gap:**
- Upload process exists but no structured monthly update workflow
- No explicit tracking of "last updated" per entity/month/year/location

**Implementation Impact:**
- **Database**: May need update tracking fields
- **Backend**: Enhanced upload endpoint with update vs. insert logic
- **Frontend**: Monthly update interface/indicator

---

### 2.3 Requirement 3: Multi-Entity Consolidation

**Requirement:**
> "In general, each company will have either a parent company or a child company. The parent may be in a different country, and the child may be in another. But when the consolidation happens, the numbers should show by unit and total. Hence, there should be an option to generate a consolidation by:
> - City
> - Country
> - Parent and child option
> - Or selection of entities by choice"

**Why It's Important:**
- **Group Reporting**: Essential for multi-entity organizations
- **Regulatory Compliance**: Many jurisdictions require consolidated financial statements
- **Management Reporting**: Executives need consolidated views
- **Flexibility**: Different consolidation views for different purposes

**Current Gap:**
- No parent-child relationship in `entity_master`
- No consolidation logic
- Reports only show individual entities

**Implementation Impact:**
- **Database**: Add parent entity reference to `entity_master`
- **Backend**: New consolidation endpoint with multiple grouping options
- **Frontend**: Consolidation report UI with selection options
- **Business Logic**: Currency conversion, inter-entity elimination (if needed)

---

### 2.4 Requirement 4: Common Currency Consolidation

**Requirement:**
> "When the numbers are consolidated, the currency should be the common currency. It should show the data as per category, and by unit as well as total."

**Why It's Important:**
- **Comparability**: All entities in same currency for meaningful comparison
- **Standard Practice**: Consolidated statements use a single reporting currency
- **Decision Making**: Management can compare apples-to-apples
- **Regulatory**: Many jurisdictions mandate single-currency consolidation

**Current Gap:**
- Individual entities have `transactionAmountUSD` but no consolidation-level conversion
- No "common currency" selection mechanism
- No "by unit and total" breakdown in reports

**Implementation Impact:**
- **Backend**: Consolidation logic must convert all amounts to common currency
- **Frontend**: Currency selector in consolidation UI
- **Reports**: Show both individual entity amounts and totals

---

### 2.5 Requirement 5: Unrelated Entity Consolidation

**Requirement:**
> "If the selection is by city or country, even if the entities are not related but the consolidation should happen."

**Why It's Important:**
- **Geographic Analysis**: Compare performance by location
- **Market Analysis**: Understand regional trends
- **Flexibility**: Users may want ad-hoc groupings

**Current Gap:**
- No geographic-based consolidation
- Current system requires explicit entity selection

**Implementation Impact:**
- **Backend**: Consolidation endpoint must support geographic grouping
- **Frontend**: City/Country selection in consolidation UI

---

### 2.6 Requirement 6: Category 5 Related Parties Display

**Requirement:**
> "In Category 5, we will be marking some entities as related parties or so. Need that to be displayed as in the image as part of the report out, this is independent of the above consolidation."

**Why It's Important:**
- **Regulatory Compliance**: Related party transactions must be disclosed
- **Transparency**: Stakeholders need visibility into related party dealings
- **Audit Requirements**: Auditors review related party transactions separately

**Current Gap:**
- `category5` field exists but no special reporting
- No related party identification mechanism
- No dedicated related party report

**Implementation Impact:**
- **Backend**: New endpoint for related party transactions
- **Frontend**: Related party report page/section
- **Database**: May need to enhance `category5` usage or add related party flags

---

## 3. DETAILED IMPLEMENTATION PLAN

### 3.1 Database Schema Changes

#### 3.1.1 Entity Master Enhancement
```sql
ALTER TABLE entity_master
ADD COLUMN parent_entity_id INT NULL,
ADD COLUMN financial_year_start_month INT DEFAULT 4, -- April = 4
ADD COLUMN financial_year_start_day INT DEFAULT 1,
ADD INDEX idx_parent_entity (parent_entity_id),
ADD FOREIGN KEY (parent_entity_id) REFERENCES entity_master(ent_id) ON DELETE SET NULL;
```

#### 3.1.2 Forex Master Enhancement
```sql
-- Option 1: Add financial year to existing table
ALTER TABLE forex_master
ADD COLUMN financial_year INT NULL,
ADD COLUMN entity_id INT NULL,
ADD COLUMN opening_rate DECIMAL(18,6) NULL,
ADD COLUMN closing_rate DECIMAL(18,6) NULL,
ADD COLUMN fy_start_date DATE NULL,
ADD COLUMN fy_end_date DATE NULL,
ADD INDEX idx_fy_entity (financial_year, entity_id),
ADD INDEX idx_currency_fy (currency, financial_year);

-- OR Option 2: Create new table for FY-specific rates
CREATE TABLE entity_forex_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    financial_year INT NOT NULL,
    opening_rate DECIMAL(18,6) NOT NULL,
    closing_rate DECIMAL(18,6) NOT NULL,
    fy_start_date DATE NOT NULL,
    fy_end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id),
    UNIQUE KEY uk_entity_currency_fy (entity_id, currency, financial_year),
    INDEX idx_fy (financial_year),
    INDEX idx_currency (currency)
);
```

#### 3.1.3 Monthly Update Tracking
```sql
CREATE TABLE monthly_data_updates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    financial_year INT NOT NULL,
    month VARCHAR(20) NOT NULL,
    location VARCHAR(100) NULL,
    country VARCHAR(100) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INT NULL,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id),
    FOREIGN KEY (updated_by) REFERENCES users(id),
    UNIQUE KEY uk_entity_fy_month (entity_id, financial_year, month),
    INDEX idx_fy_month (financial_year, month),
    INDEX idx_location (location, country)
);
```

#### 3.1.4 Related Party Tracking
```sql
-- Add to code_master or create separate table
CREATE TABLE related_parties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entity_id INT NOT NULL,
    related_entity_id INT NULL, -- If related to another entity
    related_party_name VARCHAR(200) NOT NULL,
    relationship_type VARCHAR(100) NULL, -- e.g., 'Subsidiary', 'Associate', 'Key Management'
    category5_value VARCHAR(100) NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entity_master(ent_id),
    FOREIGN KEY (related_entity_id) REFERENCES entity_master(ent_id),
    INDEX idx_entity (entity_id),
    INDEX idx_category5 (category5_value)
);
```

---

### 3.2 Backend Implementation

#### 3.2.1 Forex Routes Enhancement (`backend/routes/forex.py`)

**New Endpoints:**
```python
# Get forex rates for entity and financial year
GET /forex/entity/<int:entity_id>/financial-year/<int:fy>
# Returns: opening_rate, closing_rate, fy_start_date, fy_end_date

# Create/Update forex rates for entity and financial year
POST /forex/entity/<int:entity_id>/financial-year/<int:fy>
PUT /forex/entity/<int:entity_id>/financial-year/<int:fy>
# Body: { currency, opening_rate, closing_rate, fy_start_date, fy_end_date }

# List all financial years with forex rates for an entity
GET /forex/entity/<int:entity_id>/financial-years
```

**Modified Logic:**
- All forex calculations must use FY-specific rates
- Opening rate = rate at FY start
- Closing rate = rate at FY end (max 12 months from start)
- When calculating `Avg_Fx_Rt`, use FY-specific rates

---

#### 3.2.2 Entity Routes Enhancement (`backend/routes/entity.py`)

**New Endpoints:**
```python
# Get entity hierarchy (parent and children)
GET /entities/<int:ent_id>/hierarchy
# Returns: parent entity, children entities

# Set parent entity
PUT /entities/<int:ent_id>/parent
# Body: { parent_entity_id }

# Get entities by city
GET /entities/by-city?city=<city_name>

# Get entities by country
GET /entities/by-country?country=<country_name>

# Get all parent entities
GET /entities/parents

# Get children of a parent
GET /entities/<int:ent_id>/children
```

---

#### 3.2.3 New Consolidation Routes (`backend/routes/consolidation.py`)

**New File: `backend/routes/consolidation.py`**

```python
"""
Consolidation routes for multi-entity financial consolidation
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from database import Database

consolidation_bp = Blueprint('consolidation', __name__)

@consolidation_bp.route('/consolidation/by-city', methods=['GET'])
def consolidate_by_city():
    """
    Consolidate financial data by city.
    Query params: city, financial_year, common_currency
    """
    # Implementation: Group entities by city, convert to common currency, aggregate
    
@consolidation_bp.route('/consolidation/by-country', methods=['GET'])
def consolidate_by_country():
    """
    Consolidate financial data by country.
    Query params: country, financial_year, common_currency
    """
    
@consolidation_bp.route('/consolidation/by-parent-child', methods=['GET'])
def consolidate_by_parent_child():
    """
    Consolidate parent and all child entities.
    Query params: parent_entity_id, financial_year, common_currency
    """
    
@consolidation_bp.route('/consolidation/by-selection', methods=['POST'])
def consolidate_by_selection():
    """
    Consolidate selected entities.
    Body: { entity_ids: [1, 2, 3], financial_year, common_currency }
    """
    
@consolidation_bp.route('/consolidation/details', methods=['GET'])
def get_consolidation_details():
    """
    Get detailed consolidation with unit-wise breakdown.
    Query params: consolidation_type, consolidation_value, financial_year
    Returns: { units: [...], total: {...}, by_category: [...] }
    """
```

**Key Logic:**
1. **Entity Selection**: Based on consolidation type (city/country/parent-child/manual)
2. **Currency Conversion**: Convert all amounts to common currency using FY-specific rates
3. **Aggregation**: Sum by category, show by unit and total
4. **Data Structure**: Return both unit-level and total-level data

---

#### 3.2.4 Related Parties Routes (`backend/routes/related_parties.py`)

**New File: `backend/routes/related_parties.py`**

```python
"""
Related parties routes for Category 5 related party transactions
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from database import Database

related_parties_bp = Blueprint('related_parties', __name__)

@related_parties_bp.route('/related-parties/transactions', methods=['GET'])
def get_related_party_transactions():
    """
    Get all transactions marked as related parties (category5).
    Query params: entity_id, financial_year, related_party_name
    """
    
@related_parties_bp.route('/related-parties/summary', methods=['GET'])
def get_related_party_summary():
    """
    Get summary of related party transactions.
    Query params: entity_id, financial_year
    Returns: Grouped by related party, category, amount
    """
```

---

#### 3.2.5 Monthly Updates Routes (`backend/routes/monthly_updates.py`)

**New File: `backend/routes/monthly_updates.py`**

```python
"""
Monthly data update tracking routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import Database

monthly_updates_bp = Blueprint('monthly_updates', __name__)

@monthly_updates_bp.route('/monthly-updates', methods=['GET'])
def list_monthly_updates():
    """
    List monthly updates for entities.
    Query params: entity_id, financial_year, month, location, country
    """
    
@monthly_updates_bp.route('/monthly-updates', methods=['POST'])
@jwt_required()
def record_monthly_update():
    """
    Record a monthly data update.
    Body: { entity_id, financial_year, month, location, country }
    """
```

---

### 3.3 Frontend Implementation

#### 3.3.1 New Pages/Components

1. **Consolidation Page** (`entity-insights-hub/src/pages/Consolidation.tsx`)
   - Consolidation type selector (City/Country/Parent-Child/Manual)
   - Entity selection interface
   - Common currency selector
   - Financial year selector
   - Results display: Unit-wise breakdown + Total
   - Export functionality

2. **Forex Management Enhancement** (`entity-insights-hub/src/pages/Forex.tsx` or new component)
   - Entity selector
   - Financial year selector
   - Opening/Closing rate inputs
   - FY start/end date inputs
   - Rate history view

3. **Related Parties Page** (`entity-insights-hub/src/pages/RelatedParties.tsx`)
   - Entity selector
   - Financial year selector
   - Related party transaction table
   - Summary by related party
   - Export functionality

4. **Entity Management Enhancement**
   - Add parent entity selector
   - Show entity hierarchy
   - Financial year start configuration

---

#### 3.3.2 API Integration (`entity-insights-hub/src/lib/api.ts`)

Add new API methods:
```typescript
// Consolidation APIs
consolidationApi: {
  byCity: (city: string, fy: number, currency: string) => Promise<...>,
  byCountry: (country: string, fy: number, currency: string) => Promise<...>,
  byParentChild: (parentId: number, fy: number, currency: string) => Promise<...>,
  bySelection: (entityIds: number[], fy: number, currency: string) => Promise<...>,
  getDetails: (type: string, value: string, fy: number) => Promise<...>,
}

// Forex APIs (enhanced)
forexApi: {
  getEntityFYRates: (entityId: number, fy: number) => Promise<...>,
  setEntityFYRates: (entityId: number, fy: number, rates: {...}) => Promise<...>,
  getEntityFinancialYears: (entityId: number) => Promise<...>,
}

// Related Parties APIs
relatedPartiesApi: {
  getTransactions: (entityId?: number, fy?: number) => Promise<...>,
  getSummary: (entityId?: number, fy?: number) => Promise<...>,
}
```

---

## 4. IMPLEMENTATION PRIORITY & PHASES

### Phase 2.1: Foundation (Week 1-2)
1. ✅ Database schema changes
   - Entity parent-child relationships
   - Forex FY-specific rates table
   - Monthly update tracking
2. ✅ Backend: Entity hierarchy endpoints
3. ✅ Backend: Forex FY-specific endpoints

### Phase 2.2: Core Consolidation (Week 3-4)
1. ✅ Backend: Consolidation logic (all 4 types)
2. ✅ Backend: Currency conversion in consolidation
3. ✅ Frontend: Consolidation page UI
4. ✅ Testing: Consolidation accuracy

### Phase 2.3: Related Parties (Week 5)
1. ✅ Backend: Related parties endpoints
2. ✅ Frontend: Related parties page
3. ✅ Integration with existing reports

### Phase 2.4: Monthly Updates & Polish (Week 6)
1. ✅ Monthly update tracking UI
2. ✅ Enhanced forex management UI
3. ✅ Documentation
4. ✅ User acceptance testing

---

## 5. TECHNICAL CONSIDERATIONS

### 5.1 Currency Conversion Logic

**For Consolidation:**
1. Identify all entities in consolidation group
2. For each entity, get its local currency
3. Get FY-specific forex rates for each currency → common currency
4. Convert `transactionAmount` using appropriate rate:
   - Balance Sheet items: Use closing rate (FY end)
   - P&L items: Use average of opening and closing rates
5. Sum converted amounts by category
6. Return both unit-level (per entity) and total-level data

### 5.2 Financial Year Calculation

**Per Entity:**
- Each entity may have different FY start (e.g., April 1, January 1)
- Store `financial_year_start_month` and `financial_year_start_day` in `entity_master`
- Calculate FY end = FY start + 12 months - 1 day
- Opening rate = Rate on FY start date
- Closing rate = Rate on FY end date (max 12 months from start)

### 5.3 Consolidation Data Structure

**Response Format:**
```json
{
  "consolidation_type": "by-country",
  "consolidation_value": "India",
  "financial_year": 2024,
  "common_currency": "USD",
  "units": [
    {
      "entity_id": 1,
      "entity_name": "Entity A",
      "entity_code": "ENT001",
      "local_currency": "INR",
      "by_category": [
        { "category": "Assets", "amount": 1000000, "amount_usd": 12000 }
      ],
      "total_amount": 5000000,
      "total_amount_usd": 60000
    }
  ],
  "total": {
    "by_category": [
      { "category": "Assets", "amount_usd": 50000 }
    ],
    "total_amount_usd": 250000
  }
}
```

---

## 6. TESTING STRATEGY

### 6.1 Unit Tests
- Forex FY-specific rate calculations
- Currency conversion logic
- Consolidation aggregation
- Entity hierarchy traversal

### 6.2 Integration Tests
- End-to-end consolidation workflows
- Multi-entity data upload and consolidation
- Related party transaction filtering

### 6.3 Data Validation
- Verify consolidation totals match sum of units
- Verify currency conversion accuracy
- Verify FY-specific rate application

---

## 7. MIGRATION STRATEGY

### 7.1 Data Migration
1. **Existing Forex Rates**: Map to default financial year (latest year in system)
2. **Entity Relationships**: Manual input or import via CSV
3. **Historical Data**: Assign to appropriate financial years based on `Year` field

### 7.2 Backward Compatibility
- Keep existing forex endpoints working (default to latest FY)
- Gradual migration to FY-specific rates
- Support both old and new consolidation methods during transition

---

## 8. DOCUMENTATION REQUIREMENTS

1. **API Documentation**: Swagger/OpenAPI for all new endpoints
2. **User Guide**: How to set up parent-child relationships, configure FY rates
3. **Consolidation Guide**: Step-by-step consolidation process
4. **Related Parties Guide**: How to mark and report related party transactions

---

## 9. SUCCESS CRITERIA

✅ **Requirement 1**: Forex rates are FY-specific and entity-specific  
✅ **Requirement 2**: Monthly updates are tracked by location/country/entity/month/FY  
✅ **Requirement 3**: Consolidation works by City, Country, Parent-Child, and Manual selection  
✅ **Requirement 4**: Consolidation shows data in common currency, by unit and total  
✅ **Requirement 5**: City/Country consolidation works for unrelated entities  
✅ **Requirement 6**: Related parties (Category 5) are displayed in dedicated reports  

---

## 10. RISKS & MITIGATION

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance degradation with large consolidations | High | Implement pagination, caching, async processing |
| Currency conversion accuracy | High | Thorough testing, audit logs, validation |
| Data inconsistency during migration | Medium | Phased rollout, data validation scripts |
| Complex parent-child hierarchies | Medium | Limit hierarchy depth, clear UI indicators |

---

## CONCLUSION

Phase 2 requirements significantly enhance the system's consolidation and reporting capabilities. The implementation requires careful database design, robust backend logic, and intuitive frontend interfaces. The phased approach ensures manageable delivery while maintaining system stability.

**Estimated Total Effort**: 6 weeks (1 developer) or 3 weeks (2 developers)

**Key Dependencies**:
- Database schema changes must be completed first
- Forex FY-specific rates must be implemented before consolidation
- Entity hierarchy must be established before parent-child consolidation




