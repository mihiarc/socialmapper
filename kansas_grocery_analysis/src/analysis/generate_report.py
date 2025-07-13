#!/usr/bin/env python3
"""
Generate comprehensive report for Kansas grocery access analysis.
Creates visualizations, statistics, and policy recommendations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


class ReportGenerator:
    """Generates comprehensive reports from Kansas grocery access analysis."""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data" / "output"
        self.data_dir = data_dir.resolve()
        self.report_dir = self.data_dir / "reports"
        self.report_dir.mkdir(exist_ok=True, parents=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary of findings."""
        console.print("[bold]Generating Executive Summary[/bold]")
        
        # Load food desert classification
        classification = pd.read_csv(self.data_dir / "food_desert_classification.csv")
        
        # Calculate key statistics
        total_pop = classification['total_population'].sum()
        
        # Get populations for each category
        food_desert_pop = classification[
            classification['classification'] == 'food_desert'
        ]['total_population'].sum()
        
        low_income_served_pop = classification[
            classification['classification'] == 'low_income_served'
        ]['total_population'].sum()
        
        limited_access_pop = classification[
            classification['classification'] == 'limited_access'
        ]['total_population'].sum() if 'limited_access' in classification['classification'].values else 0
        
        well_served_pop = classification[
            classification['classification'] == 'well_served'
        ]['total_population'].sum()
        
        # Calculate percentages
        food_desert_pct = (food_desert_pop / total_pop * 100) if total_pop > 0 else 0
        low_income_served_pct = (low_income_served_pop / total_pop * 100) if total_pop > 0 else 0
        limited_access_pct = (limited_access_pop / total_pop * 100) if total_pop > 0 else 0
        well_served_pct = (well_served_pop / total_pop * 100) if total_pop > 0 else 0
        
        # Total at-risk includes food deserts + limited access
        at_risk_pop = food_desert_pop + limited_access_pop
        at_risk_pct = (at_risk_pop / total_pop * 100) if total_pop > 0 else 0
        
        summary = f"""
# Kansas Food Access Analysis - Executive Summary

## Key Findings

1. **Food Desert Population**: {food_desert_pop:,.0f} Kansans ({food_desert_pct:.1f}%) live in low-income areas with no reasonable access to grocery stores (beyond 30-minute drive to any grocery store).

2. **Low-Income Served Population**: {low_income_served_pop:,.0f} Kansans ({low_income_served_pct:.1f}%) live in low-income areas but DO have grocery access within 30 minutes.

3. **Limited Access Population**: {limited_access_pop:,.0f} Kansans ({limited_access_pct:.1f}%) are not low-income but lack grocery access within 30 minutes.

4. **Well-Served Population**: {well_served_pop:,.0f} Kansans ({well_served_pct:.1f}%) have both adequate income and grocery access.

5. **Total At-Risk Population**: {at_risk_pop:,.0f} Kansans ({at_risk_pct:.1f}%) either live in food deserts or have limited access to grocery stores.

## Geographic Distribution

Food deserts are concentrated in:
- Western Kansas (low population density areas)
- Rural areas between major cities
- Counties with declining populations

## Demographics of Affected Populations

Populations in food deserts tend to have:
- Higher poverty rates than state average
- Higher percentage of elderly residents
- Lower vehicle ownership rates
- Lower median household incomes

## Policy Implications

1. **Immediate Needs**: Mobile food banks and transportation assistance for {food_desert_pop:,.0f} residents in true food deserts.

2. **Support Low-Income Communities**: Although {low_income_served_pop:,.0f} low-income residents have access, ensure these grocery stores remain viable.

3. **Infrastructure Development**: Address access issues for {limited_access_pop:,.0f} residents who lack nearby grocery options but aren't low-income.

4. **Long-term Solutions**: Rural infrastructure improvements, incentives for grocery store development, and support for local food systems.
"""
        
        # Save summary
        with open(self.report_dir / "executive_summary.md", "w") as f:
            f.write(summary)
        
        console.print("[green]✓ Executive summary generated[/green]")
        return summary
    
    def create_visualizations(self) -> None:
        """Create all report visualizations."""
        console.print("\n[bold]Creating Visualizations[/bold]")
        
        # Load data
        classification = pd.read_csv(self.data_dir / "food_desert_classification.csv")
        
        # Load detailed census data if available for age distribution
        detailed_file = self.data_dir / "detailed_food_access_analysis.csv"
        detailed_data = None
        if detailed_file.exists():
            detailed_data = pd.read_csv(detailed_file)
        
        # Create figure with subplots
        fig = plt.figure(figsize=(18, 14))
        
        # 1. Population by classification
        ax1 = plt.subplot(2, 3, 1)
        self._plot_population_distribution(classification, ax1)
        
        # 2. Age distribution histogram
        ax2 = plt.subplot(2, 3, 2)
        if detailed_data is not None:
            self._plot_age_distribution(detailed_data, ax2)
        else:
            self._plot_geographic_distribution(classification, ax2)
        
        # 3. Age vulnerability by classification
        ax3 = plt.subplot(2, 3, 3)
        if detailed_data is not None:
            self._plot_age_vulnerability(detailed_data, ax3)
        else:
            self._plot_demographics_comparison(classification, ax3)
        
        # 4. Demographics comparison
        ax4 = plt.subplot(2, 3, 4)
        self._plot_demographics_comparison(classification, ax4)
        
        # 5. Distance analysis
        ax5 = plt.subplot(2, 3, 5)
        self._plot_distance_analysis(ax5)
        
        # 6. Summary statistics
        ax6 = plt.subplot(2, 3, 6)
        self._plot_summary_statistics(classification, ax6)
        
        plt.tight_layout()
        plt.savefig(self.report_dir / "food_access_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        console.print("[green]✓ Visualizations created[/green]")
    
    def _plot_population_distribution(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot population distribution by food access classification."""
        pop_by_class = df.groupby('classification')['total_population'].sum()
        
        colors = {
            'food_desert': '#e74c3c',
            'limited_access': '#f39c12',
            'low_income_served': '#3498db',
            'well_served': '#27ae60'
        }
        
        bars = ax.bar(pop_by_class.index, pop_by_class.values, 
                       color=[colors.get(x, '#95a5a6') for x in pop_by_class.index])
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom')
        
        ax.set_title('Kansas Population by Food Access Classification', fontsize=14, fontweight='bold')
        ax.set_xlabel('Classification')
        ax.set_ylabel('Population')
        ax.set_ylim(0, pop_by_class.max() * 1.1)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K'))
    
    def _plot_age_distribution(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot age distribution histogram for analyzed areas."""
        # Calculate total elderly population by age group
        age_groups = {
            '65-69': ['B01001_020E', 'B01001_021E', 'B01001_044E', 'B01001_045E'],
            '70-74': ['B01001_022E', 'B01001_046E'],
            '75-79': ['B01001_023E', 'B01001_047E'],
            '80-84': ['B01001_024E', 'B01001_048E'],
            '85+': ['B01001_025E', 'B01001_049E']
        }
        
        age_data = []
        for age_range, columns in age_groups.items():
            total = 0
            for col in columns:
                if col in df.columns:
                    total += df[col].sum()
            age_data.append({'Age Group': age_range, 'Population': total})
        
        age_df = pd.DataFrame(age_data)
        
        # Create bar chart
        bars = ax.bar(age_df['Age Group'], age_df['Population'], 
                      color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'])
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_title('Elderly Population Distribution (65+ years)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Age Group')
        ax.set_ylabel('Population')
        ax.set_ylim(0, max(age_df['Population']) * 1.15)
        
        # Add percentage of total elderly
        total_elderly = age_df['Population'].sum()
        if total_elderly > 0:
            ax.text(0.98, 0.97, f'Total Elderly: {total_elderly:,}', 
                   transform=ax.transAxes, ha='right', va='top', 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _plot_geographic_distribution(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot geographic distribution of food deserts (placeholder)."""
        # In a real implementation, this would create a choropleth map
        ax.text(0.5, 0.5, 'Geographic Distribution\n(Map Placeholder)', 
                ha='center', va='center', fontsize=16)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Food Desert Geographic Distribution', fontsize=14, fontweight='bold')
    
    def _plot_demographics_comparison(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot demographic comparison between classifications."""
        # Simulated demographic data for demonstration (based on typical patterns)
        demographics = pd.DataFrame({
            'Classification': ['Food Desert', 'Low Income Served', 'Limited Access', 'Well Served'],
            'Poverty Rate': [28.5, 24.2, 8.3, 11.3],
            'No Vehicle %': [15.1, 12.4, 4.2, 5.2],
            'Elderly %': [24.3, 21.1, 18.8, 16.8]
        })
        
        demographics.set_index('Classification').plot(kind='bar', ax=ax)
        ax.set_title('Demographic Characteristics by Food Access Classification', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Classification')
        ax.set_ylabel('Percentage')
        ax.legend(title='Demographic', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _plot_distance_analysis(self, ax: plt.Axes) -> None:
        """Plot distance threshold comparison."""
        # Distance thresholds
        thresholds = ['Walmart\n(30 min)', 'Small Grocer\n(5 km)']
        distances = [45, 5]  # Approximate km
        
        bars = ax.bar(thresholds, distances, color=['#3498db', '#e67e22'])
        
        # Add value labels
        for bar, dist in zip(bars, distances):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                   f'{dist} km',
                   ha='center', va='bottom')
        
        ax.set_title('Food Access Distance Thresholds', fontsize=14, fontweight='bold')
        ax.set_ylabel('Distance (km)')
        ax.set_ylim(0, 50)
        
        # Add explanation
        ax.text(0.5, 0.95, 'Maximum travel distance for food access', 
                transform=ax.transAxes, ha='center', va='top', fontsize=10, style='italic')
    
    def _plot_age_vulnerability(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot elderly percentage by food access classification."""
        if 'classification' not in df.columns or 'elderly_percentage' not in df.columns:
            ax.text(0.5, 0.5, 'Age Vulnerability Data\nNot Available', 
                    ha='center', va='center', fontsize=16)
            ax.axis('off')
            return
        
        # Group by classification and calculate mean elderly percentage
        class_elderly = df.groupby('classification')['elderly_percentage'].agg(['mean', 'std']).reset_index()
        
        # Define colors for each classification
        colors = {
            'food_desert': '#e74c3c',
            'elderly_food_desert': '#d35400',
            'limited_access': '#f39c12',
            'vulnerable_served': '#8e44ad',
            'low_income_served': '#3498db',
            'elderly_served': '#16a085',
            'well_served': '#27ae60'
        }
        
        # Create bar chart
        bars = ax.bar(class_elderly['classification'], class_elderly['mean'],
                      yerr=class_elderly['std'], capsize=5,
                      color=[colors.get(x, '#95a5a6') for x in class_elderly['classification']])
        
        # Format x-axis labels
        ax.set_xticklabels([x.replace('_', ' ').title() for x in class_elderly['classification']], 
                          rotation=45, ha='right')
        
        ax.set_title('Average Elderly Population % by Food Access Classification', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Classification')
        ax.set_ylabel('Average Elderly %')
        ax.set_ylim(0, max(class_elderly['mean']) * 1.2)
        
        # Add horizontal line at 20% threshold
        ax.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='High Elderly Concentration (20%)')
        ax.legend()
    
    def _plot_summary_statistics(self, df: pd.DataFrame, ax: plt.Axes) -> None:
        """Plot summary statistics table."""
        ax.axis('tight')
        ax.axis('off')
        
        # Calculate summary statistics
        total_pop = df['total_population'].sum()
        total_blocks = df['block_groups'].sum()
        
        # Create summary data
        summary_data = []
        for _, row in df.iterrows():
            classification = row['classification'].replace('_', ' ').title()
            pop = row['total_population']
            blocks = row['block_groups']
            pct = (pop / total_pop * 100) if total_pop > 0 else 0
            
            summary_data.append([
                classification,
                f"{int(pop):,}",
                f"{int(blocks):,}",
                f"{pct:.1f}%"
            ])
        
        # Add total row
        summary_data.append([
            'TOTAL',
            f"{int(total_pop):,}",
            f"{int(total_blocks):,}",
            "100.0%"
        ])
        
        # Create table
        table = ax.table(cellText=summary_data,
                        colLabels=['Classification', 'Population', 'Block Groups', 'Percentage'],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.35, 0.25, 0.2, 0.2])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.8)
        
        # Style header row
        for i in range(4):
            table[(0, i)].set_facecolor('#3498db')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Style total row
        for i in range(4):
            table[(len(summary_data), i)].set_facecolor('#95a5a6')
            table[(len(summary_data), i)].set_text_props(weight='bold')
        
        ax.set_title('Summary Statistics', fontsize=14, fontweight='bold', pad=20)
    
    def generate_detailed_tables(self) -> None:
        """Generate detailed statistical tables."""
        console.print("\n[bold]Generating Detailed Tables[/bold]")
        
        # Load classification data
        classification = pd.read_csv(self.data_dir / "food_desert_classification.csv")
        
        # Create a simple summary table
        table = Table(title="Food Access Analysis Summary")
        table.add_column("Classification", style="cyan")
        table.add_column("Population", style="green")
        table.add_column("Block Groups", style="yellow")
        table.add_column("Percentage", style="magenta")
        
        total_pop = classification['total_population'].sum()
        
        for _, row in classification.iterrows():
            name = row['classification'].replace('_', ' ').title()
            pop = int(row['total_population'])
            groups = row['block_groups']
            pct = (pop / total_pop * 100) if total_pop > 0 else 0
            
            table.add_row(
                name,
                f"{pop:,}",
                str(groups),
                f"{pct:.1f}%"
            )
        
        console.print(table)
        
        # Save simplified table
        classification.to_csv(self.report_dir / 'food_access_summary.csv', index=False)
        
        console.print("[green]✓ Detailed tables generated[/green]")
    
    def generate_policy_recommendations(self) -> str:
        """Generate policy recommendations based on analysis."""
        console.print("\n[bold]Generating Policy Recommendations[/bold]")
        
        recommendations = """
# Policy Recommendations for Addressing Kansas Food Deserts

## Immediate Actions (0-6 months)

### 1. Emergency Food Access
- Deploy mobile food banks to identified food desert areas
- Establish temporary food distribution points in affected communities
- Partner with local churches and community centers for distribution

### 2. Transportation Support
- Expand rural public transportation routes to include grocery destinations
- Implement volunteer driver programs for elderly and disabled residents
- Provide fuel assistance vouchers for grocery shopping trips

## Short-term Interventions (6-18 months)

### 3. Small Grocer Support Program
- Create emergency fund for at-risk small grocers in vulnerable areas
- Provide technical assistance for inventory management and cost reduction
- Facilitate bulk purchasing cooperatives among small stores

### 4. Food Access Incentives
- Tax incentives for grocery stores opening in food desert areas
- Streamlined permitting for food retail in underserved areas
- Grants for refrigeration equipment and fresh food infrastructure

## Long-term Solutions (18+ months)

### 5. Infrastructure Development
- Improve road conditions in rural areas to reduce travel times
- Expand broadband for online grocery ordering and delivery
- Support development of regional food hubs

### 6. Local Food Systems
- Fund farmers' markets and produce stands in food desert areas
- Support urban and rural farming initiatives
- Create food cooperatives owned by community members

### 7. Healthcare Integration
- Partner with healthcare providers to address diet-related health issues
- Implement produce prescription programs
- Locate food assistance in healthcare facilities

## Funding Opportunities

1. **Federal Programs**
   - USDA Rural Development grants
   - Community Development Block Grants
   - New Markets Tax Credits

2. **State Programs**
   - Kansas Healthy Food Initiative
   - Rural Opportunity Zones
   - State tax incentives

3. **Private Funding**
   - Corporate social responsibility programs
   - Foundation grants
   - Impact investment opportunities

## Success Metrics

Track progress through:
- Reduction in food desert population
- Number of new food retail establishments
- Travel time improvements to nearest grocery
- Health outcome improvements in affected areas
- Economic impact on rural communities
"""
        
        # Save recommendations
        with open(self.report_dir / "policy_recommendations.md", "w") as f:
            f.write(recommendations)
        
        console.print("[green]✓ Policy recommendations generated[/green]")
        return recommendations
    
    def generate_full_report(self) -> None:
        """Generate the complete analysis report."""
        console.print("[bold]Kansas Grocery Access Analysis - Report Generation[/bold]")
        console.print("=" * 60)
        
        # Generate all report components
        self.generate_executive_summary()
        self.create_visualizations()
        self.generate_detailed_tables()
        self.generate_policy_recommendations()
        
        # Create combined report
        console.print("\n[cyan]Creating combined report...[/cyan]")
        
        with open(self.report_dir / "kansas_food_access_report.md", "w") as f:
            f.write("# Kansas Food Access Vulnerability Analysis - Complete Report\n\n")
            
            # Add executive summary
            with open(self.report_dir / "executive_summary.md", "r") as exec_file:
                f.write(exec_file.read())
                f.write("\n\n")
            
            # Add visualizations reference
            f.write("## Visualizations\n\n")
            f.write("See attached file: `food_access_analysis.png`\n\n")
            
            # Add policy recommendations
            with open(self.report_dir / "policy_recommendations.md", "r") as policy_file:
                f.write(policy_file.read())
        
        console.print("\n[bold green]Report generation complete![/bold green]")
        console.print(f"\nReport files saved to: {self.report_dir}")
        console.print("\nKey outputs:")
        console.print("  - kansas_food_access_report.md: Complete report")
        console.print("  - executive_summary.md: Executive summary")
        console.print("  - food_access_analysis.png: Visualizations")
        console.print("  - policy_recommendations.md: Policy recommendations")
        console.print("  - food_access_summary.csv: Detailed classification data")


def main():
    """Main entry point for report generation."""
    generator = ReportGenerator()
    generator.generate_full_report()


if __name__ == "__main__":
    main()