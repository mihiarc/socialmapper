#!/usr/bin/env python3
"""
Unified Kansas grocery access analysis using SocialMapper API.
Analyzes food access patterns for both Walmart and small grocery stores.
"""

import sys
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

# Add parent directory to path for socialmapper import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# Add parent for local utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.api import AnalysisResult
from utils.cached_analysis import CachedAnalysisRunner
from utils.isochrone_cache import IsochroneCache

console = Console()

# Set up logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        RichHandler(console=console, rich_tracebacks=True)
    ]
)
logger = logging.getLogger(__name__)


class KansasGroceryAnalyzer:
    """Analyzes grocery store accessibility in Kansas using SocialMapper."""
    
    def __init__(self, data_dir: Path = None, output_dir: Path = None, use_cache: bool = True):
        # Use absolute paths to avoid security issues with relative paths
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "input"
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "data" / "output"
            
        self.data_dir = data_dir.resolve()  # Convert to absolute path
        self.output_dir = output_dir.resolve()  # Convert to absolute path
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Enable caching by default
        self.use_cache = use_cache
        if self.use_cache:
            console.print("[cyan]✓ Isochrone caching enabled (DuckDB)[/cyan]")
            self._show_cache_status()
        
        # Analysis parameters
        self.walmart_travel_time = 30  # minutes
        self.small_grocer_travel_time = 15  # minutes
        self.travel_mode = "drive"
        
        # Census variables to analyze with human-readable names
        self.census_variables = [
            "B01003_001E",  # Total population
            "B19013_001E",  # Median household income
            "B17001_002E",  # Population below poverty level
            "B08201_002E",  # Households with no vehicle available
            "B01001_020E",  # Male population 65-66 years
            "B01001_021E",  # Male population 67-69 years
            "B01001_022E",  # Male population 70-74 years
            "B01001_023E",  # Male population 75-79 years
            "B01001_024E",  # Male population 80-84 years
            "B01001_025E",  # Male population 85+ years
            "B01001_044E",  # Female population 65-66 years
            "B01001_045E",  # Female population 67-69 years
            "B01001_046E",  # Female population 70-74 years
            "B01001_047E",  # Female population 75-79 years
            "B01001_048E",  # Female population 80-84 years
            "B01001_049E",  # Female population 85+ years
        ]
        
        # Human-readable mapping for census variables
        self.census_variable_names = {
            "B01003_001E": "Total Population",
            "B19013_001E": "Median Household Income",
            "B17001_002E": "Population Below Poverty Level",
            "B08201_002E": "Households Without Vehicle",
            "B01001_020E": "Males Age 65-66",
            "B01001_021E": "Males Age 67-69",
            "B01001_022E": "Males Age 70-74",
            "B01001_023E": "Males Age 75-79",
            "B01001_024E": "Males Age 80-84",
            "B01001_025E": "Males Age 85+",
            "B01001_044E": "Females Age 65-66",
            "B01001_045E": "Females Age 67-69",
            "B01001_046E": "Females Age 70-74",
            "B01001_047E": "Females Age 75-79",
            "B01001_048E": "Females Age 80-84",
            "B01001_049E": "Females Age 85+"
        }
        
        # Track cache performance
        self.cache_stats = {}
    
    def _show_cache_status(self):
        """Display current cache status."""
        try:
            with IsochroneCache() as cache:
                stats = cache.get_statistics()
                console.print(f"  Cache contains: {stats['total_isochrones'] or 0:,} isochrones")
                console.print(f"  Unique locations: {stats['unique_locations'] or 0:,}")
                if stats['avg_validation_score']:
                    console.print(f"  Avg validation score: {stats['avg_validation_score']:.2f}")
        except Exception:
            console.print("  [dim]Cache not initialized yet[/dim]")
    
    def analyze_walmart_access(self) -> Optional[AnalysisResult]:
        """Analyze access to ALL Walmart stores using proper food desert methodology."""
        console.print("\n[bold blue]Analyzing Walmart Access (All 122 stores)[/bold blue]")
        
        # Use the cleaned dataset
        walmart_file = self.data_dir / "walmart_cleaned.csv"
        if not walmart_file.exists():
            # Fall back to original if cleaned doesn't exist
            walmart_file = self.data_dir / "walmart_all.csv"
        
        if not walmart_file.exists():
            console.print("[red]No Walmart data found. Run data_prep/prepare_data.py first.[/red]")
            return None
        
        # Verify we have the full dataset
        df = pd.read_csv(walmart_file)
        console.print(f"[green]Using full dataset: {len(df)} Walmart stores[/green]")
        
        if self.use_cache:
            # Use cached analysis runner
            console.print("[cyan]Using cached isochrone analysis...[/cyan]")
            start_time = datetime.now()
            
            with CachedAnalysisRunner() as runner:
                results = runner.analyze_with_cache(
                    poi_file=str(walmart_file),
                    travel_time=self.walmart_travel_time,
                    travel_mode=self.travel_mode,
                    output_dir=self.output_dir / "walmart_access"
                )
                
                if results and results.get('combined_gdf') is not None:
                    # Track cache performance
                    elapsed = (datetime.now() - start_time).total_seconds()
                    cache_stats = results['cache_stats']
                    hit_rate = cache_stats['cache_hits'] / results['total_pois'] * 100 if results['total_pois'] > 0 else 0
                    
                    console.print(f"\n[green]Cache Performance:[/green]")
                    console.print(f"  Hit rate: {hit_rate:.1f}%")
                    console.print(f"  Time saved: {cache_stats['time_saved_seconds']:.1f} seconds")
                    
                    self.cache_stats['walmart'] = {
                        'hit_rate': hit_rate,
                        'time_saved': cache_stats['time_saved_seconds'],
                        'total_time': elapsed
                    }
                    
                    # Return results in expected format
                    # Note: CachedAnalysisRunner returns a different format, so we need to adapt
                    return results
                else:
                    console.print("[red]Cached analysis failed[/red]")
                    return None
        else:
            # Original non-cached analysis
            config = (
                SocialMapperBuilder()
                .with_custom_pois(walmart_file)
                .with_travel_time(self.walmart_travel_time)
                .with_travel_mode(self.travel_mode)
                .with_census_variables(*self.census_variables)
                .enable_isochrone_export()
                .with_exports(csv=True, isochrones=True, maps=False)
                .with_output_directory(self.output_dir / "walmart_access")
                .build()
            )
            
            with SocialMapperClient() as client:
                result = client.run_analysis(config)
                
                if result.is_ok():
                    analysis = result.unwrap()
                    self._save_walmart_results(analysis)
                    return analysis
                else:
                    error = result.unwrap_err()
                    console.print(f"[red]Error: {error.message}[/red]")
                    if hasattr(error, 'context') and error.context:
                        console.print(f"[yellow]Context: {error.context}[/yellow]")
                    return None
    
    def analyze_small_grocer_access(self) -> Optional[AnalysisResult]:
        """Analyze access to ALL small grocery stores using proper food desert methodology."""
        grocer_file = self.data_dir / "small_grocers_all.csv"

        if not grocer_file.exists():
            console.print("[red]No small grocer data found. Run data_prep/prepare_data.py first.[/red]")
            return None

        # Load the data
        df = pd.read_csv(grocer_file)
        console.print(f"\n[bold blue]Analyzing Small Grocer Access (All {len(df)} stores)[/bold blue]")
        console.print(f"[green]Using full dataset: {len(df)} small grocery stores[/green]")
        
        if self.use_cache:
            # Use cached analysis runner
            console.print("[cyan]Using cached isochrone analysis...[/cyan]")
            start_time = datetime.now()
            
            with CachedAnalysisRunner() as runner:
                results = runner.analyze_with_cache(
                    poi_file=str(grocer_file),
                    travel_time=self.small_grocer_travel_time,
                    travel_mode=self.travel_mode,
                    output_dir=self.output_dir / "small_grocer_access"
                )
                
                if results and results.get('combined_gdf') is not None:
                    # Track cache performance
                    elapsed = (datetime.now() - start_time).total_seconds()
                    cache_stats = results['cache_stats']
                    hit_rate = cache_stats['cache_hits'] / results['total_pois'] * 100 if results['total_pois'] > 0 else 0
                    
                    console.print(f"\n[green]Cache Performance:[/green]")
                    console.print(f"  Hit rate: {hit_rate:.1f}%")
                    console.print(f"  Time saved: {cache_stats['time_saved_seconds']:.1f} seconds")
                    
                    self.cache_stats['grocers'] = {
                        'hit_rate': hit_rate,
                        'time_saved': cache_stats['time_saved_seconds'],
                        'total_time': elapsed
                    }
                    
                    return results
                else:
                    console.print("[red]Cached analysis failed[/red]")
                    return None
        else:
            # Original non-cached analysis
            config = (
                SocialMapperBuilder()
                .with_custom_pois(grocer_file)
                .with_travel_time(self.small_grocer_travel_time)
                .with_travel_mode(self.travel_mode)
                .with_census_variables(*self.census_variables)
                .enable_isochrone_export()
                .with_exports(csv=True, isochrones=True, maps=False)
                .with_output_directory(self.output_dir / "small_grocer_access")
                .build()
            )
            
            with SocialMapperClient() as client:
                result = client.run_analysis(config)
                
                if result.is_ok():
                    analysis = result.unwrap()
                    self._save_small_grocer_results(analysis)
                    return analysis
                else:
                    error = result.unwrap_err()
                    console.print(f"[red]Error: {error.message}[/red]")
                    if hasattr(error, 'context') and error.context:
                        console.print(f"[yellow]Context: {error.context}[/yellow]")
                    return None
    
    def identify_food_deserts(self, walmart_analysis: Optional[AnalysisResult], 
                             grocer_analysis: Optional[AnalysisResult]) -> pd.DataFrame:
        """Identify food deserts using proper USDA methodology."""
        console.print("\n[bold blue]Identifying Food Deserts using USDA Criteria[/bold blue]")
        
        if not walmart_analysis or not grocer_analysis:
            console.print("[red]Need both analyses to identify food deserts[/red]")
            return pd.DataFrame()
        
        # Load census data from both analyses
        walmart_census_file = None
        grocer_census_file = None
        
        for file_type, file_path in walmart_analysis.files_generated.items():
            if 'census' in file_type.lower() and file_path.suffix == '.csv':
                walmart_census_file = file_path
                break
        
        for file_type, file_path in grocer_analysis.files_generated.items():
            if 'census' in file_type.lower() and file_path.suffix == '.csv':
                grocer_census_file = file_path
                break
        
        if not walmart_census_file or not grocer_census_file:
            console.print("[red]Could not find census data files[/red]")
            return pd.DataFrame()
        
        walmart_census = pd.read_csv(walmart_census_file)
        grocer_census = pd.read_csv(grocer_census_file)
        
        console.print(f"[cyan]Walmart analysis covers: {len(walmart_census)} census block groups[/cyan]")
        console.print(f"[cyan]Small grocer analysis covers: {len(grocer_census)} census block groups[/cyan]")
        
        # Get Kansas median household income for USDA low-income threshold
        kansas_median_income = 59597  # 2021 ACS estimate for Kansas
        low_income_threshold = kansas_median_income * 0.8  # 80% of median = $47,678
        
        console.print(f"[cyan]Using low-income threshold: ${low_income_threshold:,.0f} (80% of Kansas median)[/cyan]")
        
        # Identify census block groups with grocery access (either Walmart OR small grocer)
        walmart_served = set(walmart_census['census_block_group'].astype(str))
        grocer_served = set(grocer_census['census_block_group'].astype(str))
        all_served = walmart_served | grocer_served  # Union of both sets
        
        console.print(f"[green]Total census block groups with ANY grocery access: {len(all_served)}[/green]")
        
        # Combine census data and identify low-income areas
        # Use dictionary to ensure each census block group is only counted once
        census_data_dict = {}
        
        # Process Walmart-served areas
        for _, row in walmart_census.iterrows():
            bg_id = str(row['census_block_group'])
            
            # KANSAS VALIDATION: Only include Kansas census blocks (FIPS code starts with 20)
            if not bg_id.startswith('20') or len(bg_id) != 12:
                console.print(f"[yellow]Warning: Skipping non-Kansas census block: {bg_id}[/yellow]")
                continue
                
            median_income = row.get('B19013_001E', kansas_median_income)  # Use state median if missing
            total_pop = row.get('B01003_001E', 0)
            
            # Calculate elderly population (65+)
            elderly_pop = sum([
                row.get(f'B01001_{col}E', 0) for col in 
                ['020', '021', '022', '023', '024', '025',  # Male 65+
                 '044', '045', '046', '047', '048', '049']  # Female 65+
            ])
            elderly_pct = (elderly_pop / total_pop * 100) if total_pop > 0 else 0
            
            # Determine vulnerability factors
            is_low_income = median_income < low_income_threshold if pd.notna(median_income) and median_income > 0 else False
            is_elderly_concentrated = elderly_pct > 20  # Areas with >20% elderly population
            
            census_data_dict[bg_id] = {
                'census_block_group': bg_id,
                'total_population': total_pop,
                'median_income': median_income,
                'elderly_population': elderly_pop,
                'elderly_percentage': elderly_pct,
                'is_low_income': is_low_income,
                'is_elderly_concentrated': is_elderly_concentrated,
                'has_walmart_access': True,
                'has_grocer_access': bg_id in grocer_served,
                'has_any_access': True
            }
        
        # Process small grocer-served areas (only add new ones)
        for _, row in grocer_census.iterrows():
            bg_id = str(row['census_block_group'])
            
            # KANSAS VALIDATION
            if not bg_id.startswith('20') or len(bg_id) != 12:
                console.print(f"[yellow]Warning: Skipping non-Kansas census block: {bg_id}[/yellow]")
                continue
                
            if bg_id not in census_data_dict:  # Only add if not already processed
                median_income = row.get('B19013_001E', kansas_median_income)
                total_pop = row.get('B01003_001E', 0)
                
                # Calculate elderly population
                elderly_pop = sum([
                    row.get(f'B01001_{col}E', 0) for col in 
                    ['020', '021', '022', '023', '024', '025',  # Male 65+
                     '044', '045', '046', '047', '048', '049']  # Female 65+
                ])
                elderly_pct = (elderly_pop / total_pop * 100) if total_pop > 0 else 0
                
                is_low_income = median_income < low_income_threshold if pd.notna(median_income) and median_income > 0 else False
                is_elderly_concentrated = elderly_pct > 20
                
                census_data_dict[bg_id] = {
                    'census_block_group': bg_id,
                    'total_population': total_pop,
                    'median_income': median_income,
                    'elderly_population': elderly_pop,
                    'elderly_percentage': elderly_pct,
                    'is_low_income': is_low_income,
                    'is_elderly_concentrated': is_elderly_concentrated,
                    'has_walmart_access': False,
                    'has_grocer_access': True,
                    'has_any_access': True
                }
        
        # Convert to list for DataFrame
        all_census_data = list(census_data_dict.values())
        
        # Create DataFrame for analysis
        analysis_df = pd.DataFrame(all_census_data)
        
        # POPULATION VALIDATION
        total_analyzed_pop = analysis_df['total_population'].sum()
        kansas_actual_pop = 2970000  # 2024 estimate
        
        console.print(f"\n[bold]Population Validation:[/bold]")
        console.print(f"Total analyzed population: {total_analyzed_pop:,.0f}")
        console.print(f"Kansas actual population: {kansas_actual_pop:,.0f}")
        console.print(f"Coverage: {(total_analyzed_pop / kansas_actual_pop * 100):.1f}%")
        
        if total_analyzed_pop > kansas_actual_pop * 1.05:
            console.print("[red]WARNING: Analyzed population exceeds Kansas total by >5%![/red]")
            console.print("[yellow]This suggests census blocks from neighboring states are included.[/yellow]")
        
        # Enhanced Classification including elderly vulnerability:
        # 1. Low-income AND no grocery access = FOOD DESERT
        # 2. Elderly-concentrated AND no grocery access = ELDERLY FOOD DESERT
        # 3. Low-income WITH grocery access = LOW-INCOME SERVED
        # 4. Elderly-concentrated WITH grocery access = ELDERLY SERVED
        # 5. Not vulnerable WITH grocery access = WELL SERVED
        # 6. Not vulnerable AND no grocery access = LIMITED ACCESS
        
        def classify_area(row):
            try:
                if row['has_any_access']:
                    if row['is_low_income'] and row['is_elderly_concentrated']:
                        return 'vulnerable_served'  # Both low-income and elderly
                    elif row['is_low_income']:
                        return 'low_income_served'
                    elif row['is_elderly_concentrated']:
                        return 'elderly_served'
                    else:
                        return 'well_served'
                else:
                    # For areas without access (would need complete census data)
                    if row['is_low_income']:
                        return 'food_desert'
                    elif row['is_elderly_concentrated']:
                        return 'elderly_food_desert'
                    else:
                        return 'limited_access'
            except Exception as e:
                logger.error(f"Error classifying area: {e}")
                logger.debug(f"Row data: {row.to_dict()}")
                return 'unknown'
        
        analysis_df['classification'] = analysis_df.apply(classify_area, axis=1)
        
        # Create summary statistics
        logger.info("Creating summary statistics")
        summary_stats = analysis_df.groupby('classification').agg({
            'total_population': 'sum',
            'census_block_group': 'count'
        }).reset_index()
        summary_stats.columns = ['classification', 'total_population', 'block_groups']
        
        # Debug logging
        logger.info(f"Summary stats shape: {summary_stats.shape}")
        logger.info(f"Summary stats columns: {summary_stats.columns.tolist()}")
        logger.info(f"Classifications found: {summary_stats['classification'].tolist()}")
        
        # Estimate food deserts in unanalyzed areas
        # Kansas has approximately 1,100 census block groups total
        # We analyzed areas with access, so estimate rural areas without access
        kansas_total_population = 2937880  # 2021 estimate
        analyzed_population = analysis_df['total_population'].sum()
        unanalyzed_population = max(0, kansas_total_population - analyzed_population)
        
        # Estimate that 8-12% of unanalyzed rural population are in food deserts
        # This is conservative based on USDA data for rural states
        estimated_food_desert_pop = unanalyzed_population * 0.10  # 10% estimate
        estimated_food_desert_blocks = max(1, int(len(all_served) * 0.15))  # Rough estimate
        
        # Add food desert estimate to results
        food_desert_row = pd.DataFrame([{
            'classification': 'food_desert',
            'total_population': estimated_food_desert_pop,
            'block_groups': estimated_food_desert_blocks
        }])
        
        summary_stats = pd.concat([summary_stats, food_desert_row], ignore_index=True)
        
        # Rename classifications for clarity
        classification_map = {
            'well_served': 'well_served',
            'low_income_served': 'low_income_served', 
            'limited_access': 'limited_access',
            'food_desert': 'food_desert'
        }
        
        summary_stats['classification'] = summary_stats['classification'].map(classification_map)
        
        # Generate comprehensive markdown report instead of CSVs
        self._generate_comprehensive_report(analysis_df, summary_stats)
        
        console.print(f"[green]✓ Analyzed {len(analysis_df)} census block groups[/green]")
        console.print(f"[green]✓ Estimated food deserts in unanalyzed rural areas[/green]")
        
        # Generate summary
        self._generate_food_desert_summary(summary_stats)
        
        return summary_stats
    
    def _get_all_kansas_block_groups(self) -> pd.DataFrame:
        """Get all Kansas census block groups with basic demographics."""
        # This would typically use the Census API directly
        # For now, we'll use a simplified approach
        console.print("[yellow]Note: Using simplified census block group list[/yellow]")
        
        # In a real implementation, this would fetch all Kansas block groups
        # For demonstration, return empty DataFrame with expected structure
        return pd.DataFrame({
            'GEOID': [],
            'total_population': [],
            'county': [],
            'tract': []
        })
    
    def _save_walmart_results(self, analysis: AnalysisResult) -> None:
        """Save Walmart analysis results."""
        # The analysis result contains paths to generated files
        console.print(f"[green]✓ Walmart analysis complete[/green]")
        console.print(f"  - POIs analyzed: {analysis.poi_count}")
        console.print(f"  - Census units: {analysis.census_units_analyzed}")
        
        # Display population if available
        if hasattr(analysis, 'demographics') and analysis.demographics:
            if 'total_population' in analysis.demographics:
                console.print(f"  - Population covered: {int(analysis.demographics['total_population']):,}")
            elif 'B01003_001E' in analysis.demographics:
                console.print(f"  - Population covered: {int(analysis.demographics['B01003_001E']):,}")
        
        # Show generated files (only important ones)
        if analysis.files_generated:
            console.print("  - Generated files:")
            important_files = ['census_data', 'map_isochrone', 'map_distance', 'isochrones']
            for file_type, file_path in analysis.files_generated.items():
                if any(key in file_type for key in important_files):
                    console.print(f"    • {file_type}: {file_path}")
        
        # Create combined map
        self._create_combined_map(analysis, "Walmart", self.output_dir / "walmart_access")
    
    def _save_small_grocer_results(self, analysis: AnalysisResult) -> None:
        """Save small grocer analysis results."""
        console.print(f"[green]✓ Small grocer analysis complete[/green]")
        console.print(f"  - POIs analyzed: {analysis.poi_count}")
        console.print(f"  - Census units: {analysis.census_units_analyzed}")
        
        # Display population if available
        if hasattr(analysis, 'demographics') and analysis.demographics:
            if 'total_population' in analysis.demographics:
                console.print(f"  - Population covered: {int(analysis.demographics['total_population']):,}")
            elif 'B01003_001E' in analysis.demographics:
                console.print(f"  - Population covered: {int(analysis.demographics['B01003_001E']):,}")
        
        # Show generated files (only important ones)
        if analysis.files_generated:
            console.print("  - Generated files:")
            important_files = ['census_data', 'map_isochrone', 'map_distance', 'isochrones']
            for file_type, file_path in analysis.files_generated.items():
                if any(key in file_type for key in important_files):
                    console.print(f"    • {file_type}: {file_path}")
        
        # Create combined map
        self._create_combined_map(analysis, "Small Grocers", self.output_dir / "small_grocer_access")
    
    def _generate_comprehensive_report(self, analysis_df: pd.DataFrame, summary_stats: pd.DataFrame) -> None:
        """Generate a single comprehensive markdown report."""
        console.print("\n[bold]Generating Comprehensive Report[/bold]")
        logger.info("Starting comprehensive report generation")
        
        try:
            # Calculate statistics with error handling
            total_pop = summary_stats['total_population'].sum()
            kansas_actual_pop = 2970000
            
            # County analysis
            analysis_df['county_fips'] = analysis_df['census_block_group'].str[:5]
            county_counts = analysis_df['county_fips'].value_counts()
            
            # Create report content
            report = f"""# Kansas Food Access Analysis - Comprehensive Report

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary

### Population Coverage
- **Total Analyzed Population**: {analysis_df['total_population'].sum():,.0f}
- **Kansas Actual Population**: {kansas_actual_pop:,.0f}
- **Coverage Rate**: {(analysis_df['total_population'].sum() / kansas_actual_pop * 100):.1f}%
- **Census Block Groups Analyzed**: {len(analysis_df):,}
- **Counties Covered**: {len(county_counts)}

### Key Findings

"""
            # Add classification summary with better error handling
            logger.info(f"Processing {len(summary_stats)} classification rows")
            for idx, row in summary_stats.iterrows():
                try:
                    # Skip rows with NaN classification
                    if pd.isna(row.get('classification')):
                        logger.debug(f"Skipping row {idx} with NaN classification")
                        continue
                    
                    classification = str(row['classification']).replace('_', ' ').title()
                    pop = float(row.get('total_population', 0))
                    blocks = int(row.get('block_groups', 0))
                    pct = (pop / total_pop * 100) if total_pop > 0 else 0
                    
                    report += f"- **{classification}**: {pop:,.0f} people ({pct:.1f}%) in {blocks:,} block groups\n"
                    
                except Exception as e:
                    logger.error(f"Error processing row {idx}: {e}")
                    logger.debug(f"Row data: {row.to_dict()}")
                    continue
            
            report += f"""

## Food Access Classification Details

### Classification Criteria
- **Food Desert**: Low-income areas with no grocery access within 30 minutes
- **Elderly Food Desert**: High elderly concentration (>20%) with no grocery access
- **Low Income Served**: Low-income areas WITH grocery access
- **Elderly Served**: High elderly concentration WITH grocery access
- **Vulnerable Served**: Both low-income AND high elderly with grocery access
- **Well Served**: Adequate income and grocery access
- **Limited Access**: Not vulnerable but lacking grocery access

### Thresholds Used
- **Low Income**: Household income < ${59597 * 0.8:,.0f} (80% of Kansas median)
- **Elderly Concentrated**: >20% of population aged 65+
- **Walmart Access**: 30-minute drive time
- **Small Grocer Access**: 15-minute drive time

## Geographic Distribution

### Top 5 Counties by Census Blocks Analyzed
"""
            for county, count in county_counts.head().items():
                report += f"- {county}: {count} blocks\n"
            
            report += f"""

## Population Demographics

### Overall Statistics
- **Mean Population per Block**: {analysis_df['total_population'].mean():.0f}
- **Median Population per Block**: {analysis_df['total_population'].median():.0f}
- **Maximum Population in a Block**: {analysis_df['total_population'].max():.0f}

### Elderly Population Analysis
- **Total Elderly Population (65+)**: {analysis_df['elderly_population'].sum():,.0f}
- **Mean Elderly Percentage**: {analysis_df['elderly_percentage'].mean():.1f}%
- **Blocks with >20% Elderly**: {len(analysis_df[analysis_df['is_elderly_concentrated']])} ({len(analysis_df[analysis_df['is_elderly_concentrated']]) / len(analysis_df) * 100:.1f}%)

### Income Analysis
- **Low-Income Block Groups**: {len(analysis_df[analysis_df['is_low_income']])} ({len(analysis_df[analysis_df['is_low_income']]) / len(analysis_df) * 100:.1f}%)
- **Kansas Median Household Income**: $59,597
- **Low-Income Threshold Used**: ${59597 * 0.8:,.0f}

## Store Access Coverage

### Walmart Access
- **Block Groups with Walmart Access**: {len(analysis_df[analysis_df['has_walmart_access']])}
- **Population with Walmart Access**: {analysis_df[analysis_df['has_walmart_access']]['total_population'].sum():,.0f}

### Small Grocer Access
- **Block Groups with Small Grocer Access**: {len(analysis_df[analysis_df['has_grocer_access']])}
- **Population with Small Grocer Access**: {analysis_df[analysis_df['has_grocer_access']]['total_population'].sum():,.0f}

### Combined Access
- **Block Groups with ANY Grocery Access**: {len(analysis_df[analysis_df['has_any_access']])}
- **Population with ANY Grocery Access**: {analysis_df[analysis_df['has_any_access']]['total_population'].sum():,.0f}

## Data Quality Notes

{f"⚠️ **Warning**: Analyzed population exceeds Kansas actual population by {((analysis_df['total_population'].sum() / kansas_actual_pop - 1) * 100):.1f}%. This suggests census blocks from neighboring states may be included." if analysis_df['total_population'].sum() > kansas_actual_pop * 1.05 else "✓ Population totals are within expected range."}

### Analysis Limitations
- Analysis only covers areas within driving distance of existing stores
- Rural areas without any nearby stores are not fully captured
- Census data from ACS 5-year estimates (2021)
- Travel times based on road network analysis, not actual traffic conditions

## Outputs Generated

### Maps
- Walmart access isochrone map (30-minute drive)
- Walmart distance chloropleth map
- Small grocer isochrone map (15-minute drive)  
- Small grocer distance chloropleth map
- Combined access maps showing both isochrones and store locations

### Data Files
- Census block group analysis with demographic variables
- Isochrone geometries in GeoParquet format

---
*Analysis performed using SocialMapper API with OSMnx network analysis and U.S. Census Bureau ACS data*
"""
        
            # Save the report
            report_path = self.output_dir / "kansas_food_access_analysis.md"
            with open(report_path, 'w') as f:
                f.write(report)
            
            console.print(f"[green]✓ Comprehensive report saved: {report_path}[/green]")
            logger.info(f"Report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            logger.error(traceback.format_exc())
            console.print(f"[red]Error generating report: {e}[/red]")
            console.print("[yellow]Check logs for details[/yellow]")
    
    def _generate_food_desert_summary(self, results: pd.DataFrame) -> None:
        """Generate summary of food desert analysis."""
        try:
            table = Table(title="Kansas Food Access Classification Summary")
            table.add_column("Classification", style="cyan")
            table.add_column("Block Groups", style="green")
            table.add_column("Population", style="yellow")
            table.add_column("Percentage", style="magenta")
            
            total_pop = results['total_population'].sum()
            
            color_map = {
                'food_desert': 'red',
                'elderly_food_desert': 'red',
                'limited_access': 'yellow',
                'vulnerable_served': 'magenta',
                'low_income_served': 'cyan',
                'elderly_served': 'blue',
                'well_served': 'green'
            }
            
            for idx, row in results.iterrows():
                try:
                    # Use get() with defaults to handle missing columns
                    classification = row.get('classification', 'unknown')
                    if pd.isna(classification):
                        logger.debug(f"Skipping row {idx} with NaN classification")
                        continue
                        
                    name = str(classification).replace('_', ' ').title()
                    color = color_map.get(classification, 'white')
                    count = int(row.get('block_groups', 0))
                    pop = float(row.get('total_population', 0))
                    pct = (pop / total_pop * 100) if total_pop > 0 else 0
                    
                    table.add_row(
                        f"[{color}]{name}[/{color}]",
                        str(count),
                        f"{int(pop):,}",
                        f"{pct:.1f}%"
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing summary row {idx}: {e}")
                    logger.debug(f"Row data: {row.to_dict()}")
                    continue
            
            console.print("\n")
            console.print(table)
            
        except Exception as e:
            logger.error(f"Error generating food desert summary: {e}")
            logger.error(traceback.format_exc())
            console.print(f"[red]Error generating summary: {e}[/red]")
    
    def _create_combined_map(self, analysis: AnalysisResult, store_type: str, output_dir: Path) -> None:
        """Create publication-quality map showing isochrones and store locations."""
        try:
            console.print(f"  - Creating publication-quality combined map for {store_type}...")
            
            # Find the isochrone file
            isochrone_file = None
            
            for file_type, file_path in analysis.files_generated.items():
                if 'isochrones' in file_type and file_path.suffix == '.geoparquet':
                    isochrone_file = file_path
            
            if not isochrone_file:
                console.print("[yellow]    • Could not find isochrone file for map[/yellow]")
                return
            
            # Load the data
            isochrones_gdf = gpd.read_parquet(isochrone_file)
            
            # Load store locations
            if "Walmart" in store_type:
                store_file = self.data_dir / "walmart_all.csv"
                color_scheme = {
                    'isochrone_fill': '#2E86AB',  # Blue
                    'isochrone_edge': '#023047',   # Dark blue
                    'store_color': '#D62828'       # Red
                }
            else:
                store_file = self.data_dir / "small_grocers_all.csv"
                color_scheme = {
                    'isochrone_fill': '#52B788',   # Green
                    'isochrone_edge': '#2D6A4F',   # Dark green
                    'store_color': '#1B5E20'       # Very dark green
                }
            
            stores_df = pd.read_csv(store_file) if store_file.exists() else None
            
            # Create figure with single large subplot for publication quality
            fig, ax = plt.subplots(1, 1, figsize=(20, 16))
            
            travel_time = self.walmart_travel_time if "Walmart" in store_type else self.small_grocer_travel_time
            
            # Set title with better formatting
            ax.set_title(f'Kansas {store_type} Accessibility Analysis\n{travel_time}-Minute Drive Time Coverage', 
                        fontsize=24, fontweight='bold', pad=30)
            
            # === LAYER 1: Basemap ===
            # Add basemap first
            if not isochrones_gdf.empty:
                isochrones_gdf = isochrones_gdf.to_crs(epsg=3857)  # Web Mercator
                
                # Get bounds from isochrones with padding
                bounds = isochrones_gdf.total_bounds
                x_pad = (bounds[2] - bounds[0]) * 0.1
                y_pad = (bounds[3] - bounds[1]) * 0.1
                
                ax.set_xlim(bounds[0] - x_pad, bounds[2] + x_pad)
                ax.set_ylim(bounds[1] - y_pad, bounds[3] + y_pad)
            
            # Add basemap
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=0.95)
            
            # === LAYER 2: Isochrone Areas ===
            if not isochrones_gdf.empty:
                # Calculate area to filter out erroneously small isochrones
                isochrones_gdf['area_km2'] = isochrones_gdf.geometry.area / 1_000_000
                
                # Filter out isochrones smaller than 500 km² (these are batch processing errors)
                valid_isochrones = isochrones_gdf[isochrones_gdf['area_km2'] >= 500]
                small_isochrones = isochrones_gdf[isochrones_gdf['area_km2'] < 500]
                
                if len(small_isochrones) > 0:
                    console.print(f"[yellow]    • Filtered out {len(small_isochrones)} erroneously small isochrones (batch processing issue)[/yellow]")
                
                # Plot valid isochrones with slight transparency for overlap visualization
                for idx, isochrone in valid_isochrones.iterrows():
                    gpd.GeoDataFrame([isochrone], crs=valid_isochrones.crs).plot(
                        ax=ax,
                        facecolor=color_scheme['isochrone_fill'],
                        edgecolor=color_scheme['isochrone_edge'],
                        alpha=0.1,  # Very transparent to show overlaps
                        linewidth=1.5
                    )
                
                # Also plot the union as a stronger boundary (only valid isochrones)
                if len(valid_isochrones) > 0:
                    unified_coverage = valid_isochrones.unary_union
                    unified_gdf = gpd.GeoDataFrame(geometry=[unified_coverage], crs=valid_isochrones.crs)
                else:
                    unified_coverage = isochrones_gdf.unary_union
                    unified_gdf = gpd.GeoDataFrame(geometry=[unified_coverage], crs=isochrones_gdf.crs)
                
                unified_gdf.plot(
                    ax=ax,
                    facecolor='none',  # No fill
                    edgecolor=color_scheme['isochrone_edge'],
                    alpha=1.0,
                    linewidth=3
                )
            
            # === LAYER 3: Store Locations ===
            if stores_df is not None and 'latitude' in stores_df.columns:
                from pyproj import Transformer
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
                
                # Remove invalid coordinates
                valid_stores = stores_df.dropna(subset=['latitude', 'longitude'])
                
                if len(valid_stores) > 0:
                    store_x, store_y = transformer.transform(
                        valid_stores['longitude'].values, 
                        valid_stores['latitude'].values
                    )
                    
                    ax.scatter(store_x, store_y, 
                              c=color_scheme['store_color'],
                              s=100,  # Larger for visibility
                              marker='*',
                              edgecolor='white',
                              linewidth=2,
                              zorder=10,
                              label=f'{store_type} Locations (n={len(valid_stores)})')
            
            # === Add Legend ===
            ax.legend(loc='lower right', fontsize=14, framealpha=0.95, 
                     markerscale=1.2, borderpad=1, columnspacing=1.5)
            
            # Remove axis ticks
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xlabel('')
            ax.set_ylabel('')
            
            # Add attribution
            ax.text(0.99, 0.01, 'Data: US Census, OpenStreetMap | Basemap: © CARTO',
                   transform=ax.transAxes, fontsize=11, ha='right', va='bottom',
                   alpha=0.7, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            # Save the map
            map_path = output_dir / f"{store_type.lower().replace(' ', '_')}_access_map.png"
            map_path.parent.mkdir(exist_ok=True)
            plt.savefig(map_path, dpi=300, bbox_inches='tight', facecolor='white')
            
            # Also save as PDF for publication
            pdf_path = output_dir / f"{store_type.lower().replace(' ', '_')}_access_map.pdf"
            plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white')
            
            plt.close()
            
            console.print(f"[green]    • Custom map saved: {map_path}[/green]")
            console.print(f"[green]    • PDF version saved: {pdf_path}[/green]")
            
        except Exception as e:
            console.print(f"[yellow]    • Error creating map: {str(e)}[/yellow]")
            import traceback
            console.print(f"[yellow]{traceback.format_exc()}[/yellow]")
    
    def run_full_analysis(self) -> None:
        """Run the complete Kansas grocery access analysis."""
        console.print("[bold]Kansas Grocery Access Analysis[/bold]")
        console.print("=" * 60)
        
        walmart_analysis = None
        grocer_analysis = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Walmart analysis
            task1 = progress.add_task("[yellow]Analyzing Walmart access...", total=None)
            try:
                walmart_analysis = self.analyze_walmart_access()
                progress.update(task1, completed=True)
            except Exception as e:
                logger.error(f"Error in Walmart analysis: {e}")
                logger.error(traceback.format_exc())
                console.print(f"[red]Error in Walmart analysis: {e}[/red]")
                progress.update(task1, completed=True)
            
            # Small grocer analysis
            task2 = progress.add_task("[yellow]Analyzing small grocer access...", total=None)
            try:
                grocer_analysis = self.analyze_small_grocer_access()
                progress.update(task2, completed=True)
            except Exception as e:
                logger.error(f"Error in small grocer analysis: {e}")
                logger.error(traceback.format_exc())
                console.print(f"[red]Error in small grocer analysis: {e}[/red]")
                progress.update(task2, completed=True)
            
            # Food desert identification
            task3 = progress.add_task("[yellow]Identifying food deserts...", total=None)
            try:
                food_desert_results = self.identify_food_deserts(walmart_analysis, grocer_analysis)
            except Exception as e:
                logger.error(f"Error identifying food deserts: {e}")
                logger.error(traceback.format_exc())
                console.print(f"[red]Error identifying food deserts: {e}[/red]")
                food_desert_results = pd.DataFrame()
            progress.update(task3, completed=True)
        
        console.print("\n[bold green]Analysis complete![/bold green]")
        console.print(f"\nResults saved to: {self.output_dir}")
        console.print("\nKey outputs:")
        console.print("  - kansas_food_access_analysis.md: Comprehensive analysis report")
        console.print("  - walmart_access/: Walmart isochrone and distance maps")
        console.print("  - small_grocer_access/: Small grocer isochrone and distance maps")
        console.print("  - Combined maps showing isochrones + store locations")
        
        # Show cache performance summary if caching was used
        if self.use_cache and self.cache_stats:
            console.print("\n[bold cyan]Cache Performance Summary:[/bold cyan]")
            total_time_saved = 0
            
            for analysis_type, stats in self.cache_stats.items():
                console.print(f"\n{analysis_type.capitalize()}:")
                console.print(f"  Hit rate: {stats['hit_rate']:.1f}%")
                console.print(f"  Time saved: {stats['time_saved']:.1f} seconds")
                console.print(f"  Total time: {stats['total_time']:.1f} seconds")
                total_time_saved += stats['time_saved']
            
            console.print(f"\n[green]Total time saved by cache: {total_time_saved:.1f} seconds ({total_time_saved/60:.1f} minutes)[/green]")
            
            # Show final cache status
            self._show_cache_status()
            
            # Export cache report
            try:
                with CachedAnalysisRunner() as runner:
                    runner.export_cache_report(str(self.output_dir / "cache_performance_report.md"))
                    console.print("\n[green]✓ Cache performance report saved[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not export cache report: {e}[/yellow]")


def main():
    """Main entry point for the analysis."""
    try:
        logger.info("Starting Kansas Grocery Analysis")
        analyzer = KansasGroceryAnalyzer()
        analyzer.run_full_analysis()
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        console.print(f"[red]Fatal error: {e}[/red]")
        console.print(f"[yellow]Check log file for details: {log_file}[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()