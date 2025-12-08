# SKU Standardization Plan

## Current State Analysis

### Data Overview
- **Total rows**: 339,652
- **Rows with existing SKU**: 99,342 (29%)
- **Rows without SKU**: 240,310 (71%)
- **Unique product combinations**: 877 (vendor + title + variant)
- **Unique existing SKUs**: 221

### Existing SKU Patterns
1. **Numeric only**: `10013`, `10043`, `10020`, `10024`
2. **Alphanumeric with suffixes**: `100059-TP-21`, `100025-TR`, `100051-WH`
3. **With size/color codes**: `100056-SI-23`, `100078-BE-26`, `100039-FS-1`

### Key Observations
- Many products have no SKU (71% of rows)
- Existing SKUs are inconsistent in format
- Same product variant appears multiple times across dates
- Need unique SKU per product combination (vendor + title + variant)

## Standardization Strategy

### Option 1: Preserve Existing SKUs + Generate New Ones
**Approach:**
- Use existing SKU if present and valid
- Generate standardized SKU for missing ones
- Format: `MB-{VENDOR_CODE}-{PRODUCT_ID}-{VARIANT_ID}`

**Pros:**
- Preserves existing SKU data
- Backward compatible
- Can map old to new SKUs

**Cons:**
- Mixed formats in same column
- May have duplicates if existing SKUs aren't unique

### Option 2: Generate All New Standardized SKUs (Recommended)
**Approach:**
- Generate new standardized SKU for ALL products
- Format: `MB-{VENDOR_CODE}-{PRODUCT_HASH}-{VARIANT_HASH}`
- Example: `MB-SNUGI-A3F2B1-EU20`

**Pros:**
- Consistent format
- Guaranteed uniqueness
- Easy to parse and validate
- Scalable

**Cons:**
- Loses connection to existing SKUs (can be preserved in mapping)

### Option 3: Hybrid - Normalize Existing + Generate Missing
**Approach:**
- Normalize existing SKUs to standard format
- Generate new SKUs for missing ones
- Format: `MB-{VENDOR_CODE}-{NORMALIZED_SKU}`

**Pros:**
- Uses existing data when available
- Standardized format

**Cons:**
- Complex normalization logic needed
- May have conflicts

## Recommended Solution: Option 2

### SKU Format Specification
```
MB-{VENDOR_CODE}-{PRODUCT_HASH}-{VARIANT_HASH}
```

**Components:**
1. **Prefix**: `MB` (Minibambini)
2. **Vendor Code**: 3-6 uppercase letters from vendor name
   - Snugi → `SNUGI`
   - Dobavitelj M → `DOBAV`
   - Small Foot → `SMALL`
   - Just kiddin baby → `JKBABY`
3. **Product Hash**: 6-character hash from product title
   - Use first 6 chars of MD5 hash (uppercase)
   - Example: `A3F2B1`
4. **Variant Hash**: 4-character hash from variant title
   - Use first 4 chars of MD5 hash (uppercase)
   - Example: `EU20`

**Example SKUs:**
- `MB-SNUGI-A3F2B1-EU20` (Snugi, Papuče Snugi - Daisy, EU 20)
- `MB-DOBAV-B7C3D2-DEF` (Dobavitelj M, Product, Default Title)
- `MB-SMALL-C9E4F1-DEF` (Small Foot, Product, Default Title)

### Implementation Steps

#### Step 1: Create Vendor Code Mapping
- Extract unique vendors
- Generate consistent vendor codes (3-6 chars, uppercase)
- Handle special characters and spaces

#### Step 2: Generate Product Hashes
- For each unique (vendor, title) combination
- Generate 6-char hash from normalized title
- Normalize: lowercase, remove special chars, trim spaces

#### Step 3: Generate Variant Hashes
- For each unique (vendor, title, variant) combination
- Generate 4-char hash from normalized variant
- Handle "Default Title" specially → `DEF`

#### Step 4: Create SKU Mapping
- Build dictionary: `(vendor, title, variant) → SKU`
- Ensure uniqueness (handle collisions if any)

#### Step 5: Add SKU Column
- Add new `sku` column to CSV
- Populate using mapping
- Preserve existing `Product variant SKU` column for reference

#### Step 6: Validation
- Verify all rows have SKU
- Check for duplicates
- Validate format consistency

## Alternative: Simpler Sequential Format

If hash-based approach is too complex, use sequential:

```
MB-{VENDOR_CODE}-{SEQUENTIAL_ID}
```

**Example:**
- `MB-SNUGI-001`
- `MB-SNUGI-002`
- `MB-DOBAV-001`

**Pros:**
- Simpler to implement
- Human-readable
- Sequential numbering

**Cons:**
- Less descriptive
- Requires maintaining sequence counter

## Implementation Code Structure

```python
1. Read CSV
2. Extract unique product combinations
3. Generate vendor codes
4. Generate SKUs (hash-based or sequential)
5. Create mapping dictionary
6. Add 'sku' column to all rows
7. Write updated CSV
8. Generate SKU mapping report (optional)
```

## Output

### New CSV Structure
```
Day,Product vendor,Product title,Product variant title,Product variant SKU,sku,Net items sold,Ending inventory units
```

### Deliverables
1. Updated CSV with `sku` column
2. SKU mapping file (CSV/JSON) - product combination → SKU
3. Validation report

## Questions to Consider

1. **Should we preserve existing SKUs?**
   - Yes: Keep in separate column, use for reference
   - No: Replace entirely with standardized format

2. **SKU format preference?**
   - Hash-based (more unique, less readable)
   - Sequential (more readable, requires counter)

3. **Handle special cases?**
   - Empty variants → use "DEF" or hash?
   - Duplicate product names → how to differentiate?

4. **Case sensitivity?**
   - Uppercase only (recommended)
   - Mixed case

## Next Steps

1. Review and approve plan
2. Choose SKU format (hash vs sequential)
3. Implement SKU generation
4. Add column to CSV
5. Validate results

---

## Implementation Results

### Final Implementation: Normalized Pattern-Based SKUs

**Decision:** Implemented a hybrid approach using normalized variant codes with hash-based product IDs, following existing SKU patterns in the data.

### Final SKU Format

```
{BASE_ID}-{VARIANT_CODE}
```

Where:
- **BASE_ID**: 6-digit number (100000-999999) generated from product hash
- **VARIANT_CODE**: Normalized variant identifier (or empty for Default Title)

**Key Normalization Rules:**
- EU sizes normalized: `EU 20` → `20`, `EU 23-24` → `23-24`
- Plain numbers preserved: `22` → `22`
- Size codes: `L`, `M`, `S`, `XL` → `L`, `M`, `S`, `XL`
- Color/name codes: `Starry Mint` → `SM`, `Bledo roze` → `BLED`
- Default Title → no variant code (just base number)

### Implementation Statistics

- **Total rows processed**: 339,652
- **Unique product combinations**: 877
- **Unique SKUs generated**: 877 (one per product+variant combination)
- **Rows with SKU**: 339,652 (100%)
- **Rows without SKU**: 0

### SKU Assignment Summary

#### Generated New SKUs
- **Count**: 877 unique SKUs
- **Reason**: All products received new standardized SKUs following the pattern
- **Format**: `{6-digit-base}-{variant-code}` or `{6-digit-base}` (for Default Title)

**Examples:**
- `494798-20` - Snugi, Papuče Snugi - Daisy, EU 20
- `160569` - Dobavitelj M, Product, Default Title (no variant code)
- `433502-SM` - Dobavitelj M, Product, Starry Mint
- `373177-30-31` - Snugi, Product, EU 30-31
- `664852-L` - Dobavitelj M, Product, L

#### Preserved Existing SKUs
- **Count**: 0
- **Reason**: All existing SKUs were either duplicates or needed regeneration for consistency
- **Note**: The `Product variant SKU` column is preserved in the CSV for reference

#### Duplicate SKUs Fixed

**1 Duplicate SKU Found and Fixed:**

**SKU: `10041`**
- **Issue**: This existing SKU was incorrectly assigned to 3 different variants of the same product
- **Product**: Just kiddin baby - "Muslin prekrivač - više boja"
- **Affected Variants**:
  1. `Bledo roze` → New SKU: `897556-BLED`
  2. `Bež` → New SKU: `897556-BEŽ`
  3. `Bebi plava` → New SKU: `897556-BEBI`

**Action Taken**: Each variant now has a unique SKU with proper variant code identification.

### Vendor Distribution

Top vendors by row count:
- **Snugi**: 112,153 rows (33%)
- **Dobavitelj M**: 109,339 rows (32%)
- **Froddo**: 50,401 rows (15%)
- **FILIBABBA**: 34,540 rows (10%)
- **Tip Toey Joey**: 9,389 rows (3%)
- **Small Foot**: 9,144 rows (3%)
- **Just kiddin baby**: 6,858 rows (2%)
- **Jungle**: 3,966 rows (1%)
- **Babymoov**: 2,229 rows (<1%)
- **Mini Bambini**: 1,625 rows (<1%)

### CSV Structure

**Final Column Order:**
```
Day, Product vendor, Product title, Product variant title, Product variant SKU, sku, Net items sold, Ending inventory units
```

**Columns:**
- `Day`: Date of the record
- `Product vendor`: Vendor name
- `Product title`: Product name
- `Product variant title`: Variant (size, color, etc.)
- `Product variant SKU`: Original SKU (preserved for reference)
- `sku`: **New standardized SKU** (use this for Shopify)
- `Net items sold`: Sales quantity
- `Ending inventory units`: Inventory level

---

## Shopify Management Guide

### Importing SKUs to Shopify

1. **Use the `sku` column** for Shopify product imports
   - This is the standardized, unique SKU for each product+variant combination
   - All SKUs are guaranteed unique

2. **Keep `Product variant SKU` for reference**
   - This column contains the original SKU data
   - Useful for mapping/validation but don't use for Shopify import

### Handling Duplicate SKU Issues

**If you encounter SKU conflicts in Shopify:**

1. **Check the duplicate SKU list above**
   - SKU `10041` was split into multiple SKUs
   - If Shopify has products with old SKU `10041`, update them to the new SKUs:
     - `897556-BLED` for "Bledo roze" variant
     - `897556-BEŽ` for "Bež" variant
     - `897556-BEBI` for "Bebi plava" variant

2. **Verify product+variant combinations**
   - Each unique combination (vendor + title + variant) has exactly one SKU
   - Use the CSV to verify correct SKU assignment

### SKU Format Reference

**Pattern Examples:**
- **EU Sizes**: `494798-20`, `373177-30-31` (normalized from "EU 20", "EU 30-31")
- **Plain Numbers**: `668449-22` (from variant "22")
- **Size Codes**: `664852-L`, `857285-M` (from variants "L", "M")
- **Color Codes**: `897556-BLED`, `433502-SM` (from "Bledo roze", "Starry Mint")
- **Default Variants**: `160569`, `625612` (no variant code for "Default Title")
- **Age Ranges**: `{base}-0-6M` (from "0-6 mjeseci")

### Best Practices for Shopify

1. **Bulk Import**
   - Use the `sku` column as the primary SKU identifier
   - Map `Product vendor` → Shopify Vendor
   - Map `Product title` → Shopify Product Title
   - Map `Product variant title` → Shopify Variant Title
   - Map `sku` → Shopify Variant SKU

2. **SKU Uniqueness**
   - All SKUs in the `sku` column are unique
   - No two products/variants share the same SKU
   - Safe to use as primary key for product matching

3. **Updating Existing Products**
   - If products already exist in Shopify with old SKUs:
     - Use the CSV to find the new SKU for each product+variant
     - Update Shopify product variants with new SKUs
     - Keep old SKU in notes/metafields for reference if needed

4. **Validation**
   - Before import, verify SKU format matches expected pattern
   - Check that all variants of the same product have different SKUs
   - Ensure no SKU conflicts exist in Shopify

### Troubleshooting

**Issue: SKU already exists in Shopify**
- Check if it's from the old `Product variant SKU` column
- Use the new `sku` column instead
- If conflict persists, verify product+variant combination matches

**Issue: Missing SKU for a product**
- All rows should have a SKU in the `sku` column
- If missing, check CSV for data quality issues
- Re-run SKU generation if needed

**Issue: Same SKU for different variants**
- This should not happen with the new system
- If found, report as a bug - all 877 unique combinations have unique SKUs

---

## Files Generated

1. **updated_vendors.csv** - Main file with new `sku` column
   - Location: `data/minibambini/updated_vendors.csv`
   - Contains all 339,652 rows with standardized SKUs

2. **SKU_STANDARDIZATION_PLAN.md** - This documentation file
   - Contains implementation details, patterns, and Shopify management guide










