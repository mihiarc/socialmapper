# TIM (no bids) Bienville CSV Data Dictionary

| Field Name | Data Type | Description | Examples |
|------------|-----------|-------------|----------|
| (First Column) | Integer | ID or Row Number | 79, 1692, 5009, 15668, 28476, 34543 |
| FORESTORGC | String | Forest Organization Code (0807 = Bienville National Forest) | "0807" |
| DISTRICTOR | String | District Identifier (080701 = District 1 in Bienville) | "080701" |
| volume_mbf | Float | Volume in Thousand Board Feet | 599.0, 3077.0, 5093.5, 48.0, 10.5 |
| volume_ccf | Float | Volume in Hundred Cubic Feet | 76.0, 1198.0, 6154.0, 10489.0 |
| total_bid_value | Float | Total Value of Bids (in dollars) | 111160.0, 236276.1875, 30918.279296875, 576613.1875, 734494.625 |
| total_quantity | Float | Total Quantity of Timber | 128.0, 31171.0, 173131.0, 8506.0, 85480.0 |
| sale_volume_mbf | Float | Sale Volume in Thousand Board Feet | 64.0, 4694.35253906525, 1968.44995117187, 21561.62890625, 5066.73486328125 |
| sale_volume_ccf | Float | Sale Volume in Hundred Cubic Feet | 128.0, 9388.705078125, 3579.0, 39538.87890625, 10489.0 |
| gross_sale_area | Float | Gross Area of Sale (likely in acres) | 25.0, 3800.0, 570.0, 9143.0, 635.0 |
| composite_rate_ssf | Float | Composite Rate per Square Foot | 41.0, 98.80000305175781, 76.0, 39.0, 13.0 |
| neversold_bin | Integer | Binary Indicator if Never Sold (0=sold, 1=never sold) | 0, 1 |
| region_code | String | Forest Service Region Code (08 = Southern Region) | "08" |
| forest_code | String | Forest Code (07 = Bienville) | "07" |
| district_code | String | District Code (01 = District 1) | "01" |
| sale_name | String | Name of the Timber Sale | "GA Sale 1 NWTF Stewardship Agreement", "Bienville #18/19 SPB Salvage", "Hail Damage C-14", "NWTF Stewardship Agreement", "Caney South" |
| planned_gate_6_date | DateTime | Planned Date for Gate 6 (final approval) | "2018-01-17 00:00", "2006-04-03 00:00", "2003-11-10 00:00", "2019-09-30 00:00", "2022-09-30 00:00" |
| actual_gate_6_date | DateTime | Actual Date for Gate 6 (final approval) | "2018-02-12 00:00", "2006-04-04 00:00", "2002-09-25 00:00", "2019-09-19 00:00", "2022-09-21 00:00" |

## Dataset Information

- **Number of Rows**: 277
- **File Size**: 36KB
- **Content**: Records of timber sales in Bienville National Forest that received no bids
- **Date Range**: Records span from approximately 2002 to 2024
- **Types of Sales**: Includes regular timber sales, salvage operations (often for Southern Pine Beetle damage), and stewardship agreements 