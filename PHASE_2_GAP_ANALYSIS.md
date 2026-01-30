# Phase 2 Gap Analysis - Quick Reference

## Current State vs. Required State

### 1. FOREX RATES

| Aspect | Current State | Required State | Gap |
|--------|--------------|----------------|-----|
| **Scope** | Currency-based only | Entity + Financial Year + Currency | ❌ Missing entity and FY association |
| **Rates** | `initial_rate`, `latest_rate` | `opening_rate` (FY start), `closing_rate` (FY end) | ❌ Not FY-specific |
| **Storage** | Single row per currency | Multiple rows per currency (one per entity per FY) | ❌ Schema limitation |
| **Calculation** | Uses latest rates globally | Uses FY-specific rates per entity | ❌ Logic needs update |

**Impact**: All forex calculations currently use the same rates regardless of financial year or entity.

---

### 2. ENTITY RELATIONSHIPS

| Aspect | Current State | Required State | Gap |
|--------|--------------|----------------|-----|
| **Structure** | Flat list of entities | Hierarchical (parent-child) | ❌ No parent-child fields |
| **Fields** | `ent_id`, `ent_name`, `ent_code`, `lcl_curr`, `city`, `country` | + `parent_entity_id`, `financial_year_start_month` | ❌ Missing relationship fields |
| **Queries** | Individual entity only | Can query by parent, children, hierarchy | ❌ No hierarchy queries |

**Impact**: Cannot identify or consolidate parent-child company groups.

---

### 3. CONSOLIDATION

| Aspect | Current State | Required State | Gap |
|--------|--------------|----------------|-----|
| **Type** | Individual entity reports only | Multi-entity consolidation | ❌ No consolidation logic |
| **Grouping** | N/A | By City, Country, Parent-Child, Manual selection | ❌ No grouping mechanisms |
| **Currency** | Each entity in its own currency | Common currency for all entities | ❌ No currency unification |
| **Display** | Single entity totals | Unit-wise breakdown + Total | ❌ No unit-level detail in consolidation |
| **Unrelated Entities** | N/A | Can consolidate unrelated entities by location | ❌ No geographic grouping |

**Impact**: Cannot generate consolidated financial statements for groups of entities.

---

### 4. MONTHLY UPDATES

| Aspect | Current State | Required State | Gap |
|--------|--------------|----------------|-----|
| **Tracking** | Upload history exists | Track updates by location, country, entity, month, FY | ⚠️ Partial - has upload history but not structured by location |
| **Granularity** | Entity + Year + Month | + Location + Country | ❌ Missing location/country tracking |
| **Update Workflow** | Full upload process | Monthly update workflow | ⚠️ Can upload monthly but no dedicated update flow |

**Impact**: Cannot track when specific locations/countries were last updated.

---

### 5. RELATED PARTIES (Category 5)

| Aspect | Current State | Required State | Gap |
|--------|--------------|----------------|-----|
| **Storage** | `category5` field exists | `category5` used for related party marking | ✅ Field exists |
| **Reporting** | No special handling | Dedicated related party reports | ❌ No related party reporting |
| **Identification** | N/A | Entities marked as related parties | ❌ No related party identification mechanism |
| **Display** | Included in general reports | Separate report section | ❌ No dedicated UI |

**Impact**: Related party transactions are not separately reported as required for compliance.

---

## Implementation Checklist

### Database Changes
- [ ] Add `parent_entity_id` to `entity_master`
- [ ] Add `financial_year_start_month` to `entity_master`
- [ ] Create `entity_forex_rates` table (or enhance `forex_master`)
- [ ] Create `monthly_data_updates` table
- [ ] Create `related_parties` table (optional, or use `category5`)

### Backend Changes
- [ ] Enhance `/forex` endpoints to support entity + FY
- [ ] Add entity hierarchy endpoints (`/entities/<id>/hierarchy`)
- [ ] Create `/consolidation` routes (4 types)
- [ ] Create `/related-parties` routes
- [ ] Create `/monthly-updates` routes
- [ ] Update forex calculation logic to use FY-specific rates
- [ ] Implement currency conversion for consolidation

### Frontend Changes
- [ ] Create Consolidation page
- [ ] Enhance Forex management UI (add entity + FY selection)
- [ ] Enhance Entity management (add parent selector)
- [ ] Create Related Parties page
- [ ] Add monthly update indicators
- [ ] Update API client with new endpoints

### Testing
- [ ] Test FY-specific forex rate calculations
- [ ] Test parent-child entity relationships
- [ ] Test all 4 consolidation types
- [ ] Test currency conversion accuracy
- [ ] Test related party filtering
- [ ] Test monthly update tracking

---

## Priority Matrix

| Feature | Business Value | Technical Complexity | Priority |
|---------|--------------|---------------------|----------|
| FY-Specific Forex Rates | High | Medium | **P0 - Critical** |
| Entity Parent-Child | High | Low | **P0 - Critical** |
| Consolidation (All Types) | Very High | High | **P0 - Critical** |
| Common Currency Conversion | Very High | Medium | **P0 - Critical** |
| Related Parties Reporting | Medium | Low | **P1 - High** |
| Monthly Update Tracking | Medium | Low | **P1 - High** |

---

## Quick Wins (Can Implement First)

1. ✅ **Entity Parent-Child** - Simple schema change, quick to implement
2. ✅ **Related Parties Reporting** - `category5` already exists, just need filtering/reporting
3. ✅ **Monthly Update Tracking** - Add tracking table, minimal code changes

## Complex Features (Require More Planning)

1. ⚠️ **Consolidation Logic** - Complex aggregation, currency conversion, multiple grouping types
2. ⚠️ **FY-Specific Forex** - Requires careful migration of existing rates, affects all calculations

---

## Migration Path

### Step 1: Foundation (Week 1)
- Add parent-child to entities
- Create forex FY table
- Migrate existing forex rates to latest FY

### Step 2: Consolidation Core (Week 2-3)
- Implement consolidation endpoints
- Add currency conversion
- Build consolidation UI

### Step 3: Enhancements (Week 4)
- Related parties reporting
- Monthly update tracking
- Polish and testing

---

## Key Files to Modify

### Backend
- `backend/routes/forex.py` - Add FY-specific endpoints
- `backend/routes/entity.py` - Add hierarchy endpoints
- `backend/routes/consolidation.py` - **NEW FILE**
- `backend/routes/related_parties.py` - **NEW FILE**
- `backend/routes/monthly_updates.py` - **NEW FILE**
- `backend/routes/structure_data.py` - Update forex calculation logic

### Frontend
- `entity-insights-hub/src/pages/Consolidation.tsx` - **NEW FILE**
- `entity-insights-hub/src/pages/RelatedParties.tsx` - **NEW FILE**
- `entity-insights-hub/src/pages/Entities.tsx` - Add parent selector
- `entity-insights-hub/src/lib/api.ts` - Add new API methods

### Database
- `backend/schema.sql` - Add new tables and columns
- Migration scripts for existing data




