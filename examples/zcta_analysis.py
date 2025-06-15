#!/usr/bin/env python3
"""
ZCTA Analysis Example

A practical example of ZIP Code Tabulation Area (ZCTA) analysis using SocialMapper.
This example demonstrates:
- Fetching ZCTA boundaries for a state
- Getting census demographics for ZCTAs
- Combining boundary and demographic data
- Basic analysis and visualization

ZCTAs are ideal for:
- Business intelligence and market analysis
- Regional demographic studies
- ZIP code-level reporting
- Faster processing than block groups

Prerequisites:
- SocialMapper installed: uv add socialmapper
- Optional: Census API key in environment (CENSUS_API_KEY)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import get_census_system


def main():
    """Run ZCTA analysis example."""
    print("🗺️  ZCTA Analysis Example")
    print("=" * 50)
    
    # Get the census system
    census_system = get_census_system()
    
    # Configuration
    state_fips = "37"  # North Carolina
    test_zctas = ["27601", "27605", "27609", "28202", "28204"]  # Raleigh & Charlotte areas
    variables = [
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25003_002E",  # Owner-occupied housing units
    ]
    
    print(f"\n📍 Analyzing ZCTAs in North Carolina")
    print(f"   Target ZCTAs: {', '.join(test_zctas)}")
    print(f"   Variables: Population, Income, Housing")
    
    try:
        # Step 1: Get ZCTA boundaries
        print(f"\n🗺️  Step 1: Fetching ZCTA boundaries...")
        zctas = census_system._zcta_service.get_zctas_for_state(state_fips)
        
        if zctas.empty:
            print("❌ No ZCTA boundaries found")
            return 1
        
        print(f"   ✅ Retrieved {len(zctas)} ZCTA boundaries")
        
        # Filter to our test ZCTAs
        if 'GEOID' in zctas.columns:
            test_zctas_available = [z for z in test_zctas if z in zctas['GEOID'].values]
            zctas_filtered = zctas[zctas['GEOID'].isin(test_zctas_available)]
            print(f"   🎯 Filtered to {len(zctas_filtered)} target ZCTAs")
        else:
            print("   ⚠️  No GEOID column found, using all ZCTAs")
            zctas_filtered = zctas.head(5)  # Just take first 5 for demo
            test_zctas_available = zctas_filtered['ZCTA5CE'].tolist() if 'ZCTA5CE' in zctas_filtered.columns else []
        
        # Step 2: Get census data
        print(f"\n📊 Step 2: Fetching census demographics...")
        if test_zctas_available:
            census_data = census_system._zcta_service.get_census_data(
                geoids=test_zctas_available,
                variables=variables
            )
            
            if not census_data.empty:
                print(f"   ✅ Retrieved {len(census_data)} data points")
                
                # Step 3: Combine and analyze
                print(f"\n🔗 Step 3: Combining data and analysis...")
                
                # Pivot census data for easier analysis
                census_pivot = census_data.pivot(
                    index='GEOID', 
                    columns='variable_code', 
                    values='value'
                ).reset_index()
                
                # Merge with boundaries
                combined = zctas_filtered.merge(census_pivot, on='GEOID', how='left')
                
                print(f"   ✅ Combined dataset ready: {len(combined)} ZCTAs")
                
                # Display results
                print(f"\n📋 ZCTA Analysis Results:")
                print("-" * 80)
                print(f"{'ZCTA':<8} {'Population':<12} {'Med Income':<15} {'Owner Occ':<12} {'Area (sq mi)':<12}")
                print("-" * 80)
                
                for _, row in combined.iterrows():
                    zcta = row.get('GEOID', 'N/A')
                    pop = row.get('B01003_001E', 0)
                    income = row.get('B19013_001E', 0)
                    housing = row.get('B25003_002E', 0)
                    
                    # Calculate area if available
                    area_sqmi = "N/A"
                    if 'AREALAND' in row and row['AREALAND']:
                        try:
                            area_sqm = float(row['AREALAND'])
                            area_sqmi = f"{area_sqm / 2589988:.1f}"  # Convert to square miles
                        except:
                            pass
                    
                    pop_str = f"{pop:,.0f}" if pop and pop > 0 else "N/A"
                    income_str = f"${income:,.0f}" if income and income > 0 else "N/A"
                    housing_str = f"{housing:,.0f}" if housing and housing > 0 else "N/A"
                    
                    print(f"{zcta:<8} {pop_str:<12} {income_str:<15} {housing_str:<12} {area_sqmi:<12}")
                
                print("-" * 80)
                
                # Summary statistics
                valid_pop = combined['B01003_001E'].dropna()
                valid_income = combined['B19013_001E'].dropna()
                
                if len(valid_pop) > 0:
                    print(f"\n📈 Summary Statistics:")
                    print(f"   Total Population: {valid_pop.sum():,.0f}")
                    print(f"   Average Population per ZCTA: {valid_pop.mean():,.0f}")
                    
                if len(valid_income) > 0:
                    print(f"   Average Median Income: ${valid_income.mean():,.0f}")
                    print(f"   Income Range: ${valid_income.min():,.0f} - ${valid_income.max():,.0f}")
                
                # Optional: Save results
                output_file = "zcta_analysis_results.csv"
                try:
                    combined.to_csv(output_file, index=False)
                    print(f"\n💾 Results saved to: {output_file}")
                except Exception as e:
                    print(f"\n⚠️  Could not save results: {e}")
                
                print(f"\n✅ ZCTA analysis complete!")
                return 0
                
            else:
                print("   ❌ No census data retrieved")
                return 1
        else:
            print("   ❌ No target ZCTAs found in boundaries")
            return 1
            
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        print("\n💡 Tips:")
        print("   • Check your internet connection")
        print("   • Verify state FIPS code is correct")
        print("   • Consider setting CENSUS_API_KEY environment variable")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 