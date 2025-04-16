# TimberHarvestBienville Shapefile Data Dictionary

| Field Name | Data Type | Description | Examples |
|------------|-----------|-------------|----------|
| ADMIN_FORE | String | Administrative Forest Name | "07" |
| ADMIN_REGI | String | Administrative Region | "08" |
| ADMIN_FO_1 | String | Administrative Forest Code (alternative) | "National Forests in Mississippi" |
| PROCLAIMED | String | Proclaimed Name | "0804" |
| ADMIN_DIST | String | Administrative District Name | "Bienville Ranger District" |
| ADMIN_DI_1 | String | Administrative District Code (alternative) | "01" |
| DISTRICTOR | String | District Identifier | "080701" |
| ACTIVITY_U | String | Activity Unit | "080701" |
| SUID | String | Subunit ID | "080701SPB18SS016018", "0807010720704000008", "080701SPB18SS023004" |
| FACTS_ID | String | Forest Service Activity Tracking System ID | "SPB18SS016", "0720704000", "4104279220" |
| SUBUNIT | String | Subunit Code | "018", "008", "039" |
| SUBUNIT_CN | String | Subunit Contract Number | "1323530010602", "1247717010602", "384212010602" |
| AU_NAME | String | Analysis Unit Name | "FY18SPB SALVAGE SALE 16", "LAA7 C70/71 COMMERCIAL HARVEST", "FY07 COMMERCIAL THIN/SHWD C279" |
| SUBUNIT_NA | String | Subunit Name | "FY18 SPB SALVAGE SALE 16", "LAA7 C70/71 COMMERCIAL HARVEST", "FY18 SPB SALVAGE SALE 23/24" |
| SUBUNIT_SI | Real | Subunit Size (likely in acres) | 0.0, 655.0, 20.0, 27.0 |
| SALE_NAME | String | Name of the Timber Sale | "BIENVILLE #16 SPB SALVAGE", "COMPARTMENT 70-71 DXP", "COON CREEK" |
| UNIT_ID | String | Unit Identifier | "01", "02", "03" |
| ACTIVITY_C | String | Activity Code | "6598915010602", "6147056010602", "5940236010602" |
| ACTIVITY_1 | String | Activity Description | "5947605010602", "6361472010602", "6013336010602" |
| ACTIVITY_2 | String | Secondary Activity Description | "4231", "4220", "4131" |
| ACTIVITY_N | String | Activity Name | "Salvage Cut (intermediate treatment, not regeneration)", "Commercial Thin" |
| TREATMENT_ | String | Treatment Type | "Salvage cut (interme", "Commercial Thinning" |
| NBR_UNITS_ | Real | Number of Units | 18.0, 20.0, 27.0 |
| UOM | String | Unit of Measure | "ACRES" |
| NBR_UNITS1 | Real | Alternative Number of Units | 0.0 |
| DATE_PLANN | Date | Date Planned | "2017/11/01", "2021/09/21", "2022/08/23" |
| DATE_AWARD | Date | Date Awarded | "2021/09/21" |
| DATE_COMPL | Date | Date Completed | "2021/09/21", "2022/08/23" |
| FY_PLANNED | String | Fiscal Year Planned | "2018", "2021" |
| FY_AWARDED | String | Fiscal Year Awarded | "2021" |
| FY_COMPLET | String | Fiscal Year Completed | "2021", "2022" |
| FUND_CODES | String | Funding Codes | "SPFH" |
| COST_PER_U | Real | Cost Per Unit | 0.0, 100.0 |
| NEPA_PROJE | String | NEPA Project | "NOT REQD", "26359" |
| NEPA_DOC_N | String | NEPA Document Name | "DEFAULT FOR NOT REQUIRED", "(PALS)CANEY CREEK LANDSCAPE ANALYSIS AREA 7 PROJECT" |
| NEPA_PRO_1 | String | NEPA Project Description | "101045510455", "36238" |
| METHOD_COD | String | Method Code | "200", "000" |
| METHOD_DES | String | Method Description | "Mechanical" |
| EQUIPMENT_ | String | Equipment Code | "000" |
| EQUIPMENT1 | String | Equipment Description | "NA" |
| IMPLEMENTA | String | Implementation Code | "C" |
| IMPLEMEN_1 | String | Implementation Description | "Contract" |
| IMPLEMEN_2 | String | Secondary Implementation Description | "Timber Sale" |
| WORK_AGENT | String | Work Agent | "Contractor" |
| LAND_SUITA | String | Land Suitability Code | "500" |
| LAND_SUI_1 | String | Land Suitability Description | "Timber Production Primary Emphasis" |
| PRODUCTIVI | String | Productivity Code | "3", "4" |
| PRODUCTI_1 | String | Productivity Description | "120-164 cubic feet per acre per year", "85-119 cubic feet per acre per year" |
| OWNERSHIP_ | String | Ownership Code | "FS" |
| OWNERSHIP1 | String | Ownership Description | "USDA FOREST SERVICE" |
| ASPECT | String | Aspect (cardinal direction the land faces) | "Flat", "SE", "SW" |
| ELEVATION | Integer | Elevation (likely in feet) | 0, 400, 450 |
| SLOPE | Integer | Slope (likely in percent) | 0, 5, 10 |
| STATE_ABBR | String | State Abbreviation | "MS" |
| WATERSHED_ | String | Watershed Code | "0317", "0304" |
| SUBUNIT_UO | String | Subunit Unit of Measure | "ACRES" |
| STAGE | Integer | Stage of Project | 3 |
| STAGE_DESC | String | Stage Description | "Accomplished" |
| DATA_SOURC | Integer | Data Source Code | 24, 2 |
| DATA_SOU_1 | String | Data Source Description | "GPS", "Digitized" |
| ACCURACY | Real | Accuracy of Data | 0.0 |
| CRC_VALUE | String | CRC Value | "C3F44FF87A37F3C0", "761FBC4B20E604A2" |
| UK | String | Unknown/Miscellaneous | "1", "2" |
| EDW_INSERT | Date | Date Inserted into Enterprise Data Warehouse | "2020/09/28", "2022/08/23" |
| ETL_MODIFI | Date | Date Modified in ETL Process | "2021/09/21", "2022/08/23" |
| REV_DATE | String | Revision Date | "2022/08/23", "2020/09/28" |
| GIS_ACRES | Real | GIS Calculated Acreage | 18.149, 655.0, 27.0 |
| SHAPE_Leng | Real | Length of Shape Perimeter | 0.014183916052500, 0.016240333549800 |
| SHAPE_Area | Real | Area of Shape | 0.000007018607995, 0.000007938054956 |
| FORESTORGC | String | Forest Organization Code | "0807" |

## Shapefile Information

- **Geometry Type**: Polygon
- **Feature Count**: 449
- **Geographic Extent**: (-89.683111, 32.047919) to (-89.227199, 32.531356)
- **Coordinate System**: NAD83 (North American Datum 1983)
- **Character Encoding**: UTF-8 