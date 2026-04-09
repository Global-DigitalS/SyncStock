# Breaking Changes: Catalog-Based Competitor Monitoring

## Overview
The competitor price monitoring system has been updated to use catalog-based product selection with final prices (including margin rules) instead of direct product selection with base prices.

## Changes

### 1. Product Selection Source
**Before**: Products were selected directly from the `products` collection using the `is_selected` flag.
```javascript
// Old approach
products = await db.products.find(
  {"user_id": user_id, "is_selected": True},
  {"price": 1, ...}
)
```

**After**: Products are now fetched from the `catalog_items` collection with margins applied.
```javascript
// New approach
items = await db.catalog_items.aggregate([
  {$match: {catalog_id, active: True}},
  {$lookup: {from: "products", ...}},
  // Calculate final_price with margin rules
])
```

### 2. Price Comparison
**Before**: Used base product prices directly.
```
My Price: €100 (base price from products collection)
Competitor: €95
Gap: -€5 (-5%)
```

**After**: Uses final prices from the configured catalog (with margin rules applied).
```
My Price: €110 (base €100 + 10% margin rule)
Competitor: €95
Gap: -€15 (-13.6%)
```

### 3. Configuration
**Before**: Always used the default catalog (or first available).
**After**: Users must configure which catalog to use for monitoring.

**New Endpoints**:
- `GET /competitors/config/monitoring-catalog` - Get current configuration
- `PUT /competitors/config/monitoring-catalog` - Set monitoring catalog
- `GET /competitors/config/available-catalogs` - List available catalogs

**New Field in users collection**:
```
{
  id: "uuid",
  email: "user@example.com",
  competitor_monitoring_catalog_id: "catalog-uuid"  // NEW
}
```

## Migration Guide

### For Existing Users
1. **No automatic migration**: Existing users will need to configure their monitoring catalog.
2. **Default behavior**: If not configured, the system falls back to:
   - The default catalog (if one is marked as default)
   - The first available catalog (if no default exists)
   - Empty result (if no catalogs exist)

3. **Recommended action**:
   - Users should go to Competitors → Configuración
   - Select the catalog they want to use for price monitoring
   - This catalog should have their selling prices with appropriate margins

### For System Administrators
If you need to automatically configure monitoring catalogs for existing users:

```python
# Example: Set all users to their default catalog
from services.database import db

async def auto_configure_monitoring_catalogs():
    users = await db.users.find({}).to_list(None)

    for user in users:
        # Find user's default catalog
        default_catalog = await db.catalogs.find_one(
            {"user_id": user["id"], "is_default": True},
            {"_id": 0, "id": 1}
        )

        if default_catalog:
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"competitor_monitoring_catalog_id": default_catalog["id"]}}
            )
```

## Impact on Historical Data

### Price Snapshots
Existing `price_snapshots` documents remain unchanged. They still contain:
- Original competitor prices
- Match confidence scores
- Comparison with the product's base price at the time

However, new price_snapshots will be compared against final prices (with margins).

### Price History
Price history remains valid but may show different gap calculations:
- Old snapshots: Gap vs. base product price
- New snapshots: Gap vs. final price (base + margins)

This is acceptable as the intent is to track real selling price comparisons going forward.

## Frontend Changes

### New Configuration Tab
A new "Configuración" tab is available in the Competitors dashboard showing:
- Current monitoring catalog
- List of available catalogs to choose from
- Visual feedback (highlight) for selected catalog
- Status of default/non-default catalogs

### Dashboard Comparisons
The price comparison dashboard now uses final prices:
```javascript
// KPI: Competitors Cheaper (24h)
// Now shows: products where any competitor's price < our final_price
// Before: compared against base product price
```

## Testing Recommendations

1. **Test catalog selection**
   - Create multiple catalogs with different margin rules
   - Verify switching between catalogs updates comparisons correctly
   - Confirm fallback logic works when no catalog is configured

2. **Test price calculations**
   - Add products to catalog with custom margins
   - Verify price_snapshots compare against final price (not base)
   - Check that different margin rules produce correct comparisons

3. **Test for existing users**
   - Verify users without configured catalog still see data (with fallback)
   - Confirm prompts direct users to configure their monitoring catalog
   - Test that switching catalogs updates comparisons immediately

## Rollback Instructions

If you need to revert to the old product-selection method:

1. Revert the commits related to catalog-based selection
2. Restore the original `_get_user_products()` function
3. Remove the new configuration endpoints from `competitors.py`
4. Remove the configuration UI from `Competitors.jsx`

## See Also
- `CLAUDE.md` - Project guidelines and conventions
- `DATABASE.md` - Database schema documentation
- `/backend/routes/competitors.py` - Competitor monitoring routes
- `/backend/services/scrapers/orchestrator.py` - Scraping orchestration logic
