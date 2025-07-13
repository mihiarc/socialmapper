# OpenStreetMap Grocery Store Identification Guide

This guide documents how to identify grocery stores and food retailers in OpenStreetMap (OSM) based on the official OSM Wiki documentation.

## Primary Grocery Store Tags

### 1. `shop=supermarket`
- **Definition**: A large shop for groceries and other goods, including meat and fresh produce
- **Characteristics**:
  - Large enough to use shopping trolleys/carts
  - Sells full range of groceries including fresh produce
  - Often sells non-food products
  - Typically part of a chain (e.g., Kroger, Safeway, Walmart Supercenter)
- **Required Tags**:
  - `name=*` (store name)
- **Recommended Additional Tags**:
  - `opening_hours=*`
  - `operator=*` (parent company)
  - `wheelchair=*`
  - `phone=*`
  - `website=*`

### 2. `shop=convenience`
- **Definition**: A small local shop carrying a subset of supermarket items
- **Characteristics**:
  - Limited selection compared to supermarket
  - Often open extended hours
  - Examples: 7-Eleven, Circle K, local corner stores
- **Use Case**: Small stores where quick grocery purchases can be made

### 3. `shop=grocery`
- **Definition**: A traditional grocery shop specializing in non-perishable foods
- **Important Notes**:
  - NOT the same as U.S./Canadian "grocery stores" (those are typically `shop=supermarket`)
  - More specialized than supermarkets
  - Often found alongside other specialist shops
  - May specialize in imported foods
- **Use Case**: Specialized food stores focusing on dry goods

## Related Food Retail Tags

### Fresh Produce Specialists
- `shop=greengrocer` - Vegetables and fruits
- `shop=farm` - Farm produce, roadside stands
- `shop=butcher` - Fresh meat
- `shop=bakery` - Bread and baked goods
- `shop=dairy` - Dairy products

### Other Food Retailers
- `shop=deli` - Prepared foods, specialty items
- `shop=frozen_food` - Frozen food specialists
- `shop=health_food` - Health and organic foods
- `shop=food` - Generic food shop (use more specific tag if possible)

## Additional Useful Tags for Grocery Stores

### Store Characteristics
- `organic=yes/only` - Indicates organic food availability
- `fair_trade=*` - Fair trade product availability
- `bulk_purchase=yes` - Bulk buying options
- `membership=yes` - Membership-required stores (e.g., Costco, Sam's Club)

### Payment and Services
- `payment:cash=yes/no`
- `payment:credit_cards=yes/no`
- `payment:debit_cards=yes/no`
- `payment:ebt=yes/no` (SNAP/Food stamps)
- `delivery=yes/no`
- `wheelchair=yes/no/limited`

## Query Strategy for Kansas Grocery Analysis

To comprehensively identify grocery stores in Kansas, query for:

1. **Primary grocery locations**:
   - `shop=supermarket`
   - `shop=grocery`
   - `shop=convenience`

2. **Supplementary food sources**:
   - `shop=greengrocer`
   - `shop=farm`
   - `shop=deli`

3. **Large retail with grocery sections**:
   - `shop=department_store` + `name~"Walmart|Target"`
   - `shop=wholesale` + `name~"Costco|Sam's Club"`

## Mapping Considerations

- Stores can be mapped as either:
  - **Node**: Single point for the store location
  - **Area**: Building outline or property boundary
- Always include `name=*` tag for identification
- Consider adding accessibility information (`wheelchair=*`)
- Include operating hours when known (`opening_hours=*`)

## Data Quality Notes

- Tag usage may vary by region and mapper preferences
- Some stores may be tagged generically as `shop=yes` or `building=retail`
- Chain stores often have consistent tagging patterns
- Rural areas may have less complete tagging than urban areas