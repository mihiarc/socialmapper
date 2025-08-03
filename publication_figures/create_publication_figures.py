#!/usr/bin/env python3
"""Create publication-quality figures for travel mode analysis using seaborn."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import ticker

# Set publication quality defaults
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['savefig.pad_inches'] = 0.1

# Set seaborn style for publication
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)

# Define consistent color palette
COLORS = {
    'walk': '#2E86AB',    # Professional blue
    'bike': '#E63946',    # Professional red
    'drive': '#2A9D8F'    # Professional teal
}

def load_test_data():
    """Load the test data from our analysis."""
    # This would normally load from the JSON file, but for demo we'll use the values from our test
    data = {
        'walk': {
            'poi_count': 5,
            'census_units': 17,
            'total_population': 27884,
            'median_income': 52969,
            'population_density': 1640
        },
        'bike': {
            'poi_count': 5,
            'census_units': 59,
            'total_population': 77057,
            'median_income': 82115,
            'population_density': 1306
        },
        'drive': {
            'poi_count': 5,
            'census_units': 66,
            'total_population': 85137,
            'median_income': 97917,
            'population_density': 1289
        }
    }
    return data


def create_figure_1_population_access():
    """Create Figure 1: Population Access by Travel Mode."""
    data = load_test_data()

    # Prepare data for plotting
    modes = ['Walk', 'Bike', 'Drive']
    populations = [data['walk']['total_population'],
                   data['bike']['total_population'],
                   data['drive']['total_population']]

    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Panel A: Absolute population served
    bars1 = ax1.bar(modes, populations,
                     color=[COLORS['walk'], COLORS['bike'], COLORS['drive']],
                     edgecolor='black', linewidth=0.5)

    ax1.set_ylabel('Population Served', fontweight='bold')
    ax1.set_xlabel('Travel Mode', fontweight='bold')
    ax1.set_title('A. Total Population with Library Access', fontweight='bold', pad=10)

    # Add value labels on bars
    for bar, pop in zip(bars1, populations, strict=False):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1000,
                f'{int(pop):,}', ha='center', va='bottom', fontsize=9)

    # Format y-axis
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax1.set_ylim(0, max(populations) * 1.15)

    # Panel B: Incremental population access
    walk_pop = populations[0]
    incremental = [walk_pop,
                   populations[1] - walk_pop,
                   populations[2] - populations[1]]

    # Create stacked bar chart
    bottom = 0
    labels = ['Walking distance', 'Requires bicycle', 'Requires car']
    colors_stack = [COLORS['walk'], COLORS['bike'], COLORS['drive']]

    for i, (inc, label, color) in enumerate(zip(incremental, labels, colors_stack, strict=False)):
        ax2.bar(['Population Distribution'], inc, bottom=bottom,
                color=color, edgecolor='black', linewidth=0.5,
                label=f'{label}\n({inc:,} people, {inc/populations[2]*100:.1f}%)')
        bottom += inc

    ax2.set_ylabel('Population', fontweight='bold')
    ax2.set_title('B. Incremental Access by Mode', fontweight='bold', pad=10)
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=True,
               fancybox=False, shadow=False)
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax2.set_ylim(0, populations[2] * 1.05)

    # Remove top and right spines
    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save figure
    output_dir = Path("publication_figures")
    output_dir.mkdir(exist_ok=True)
    fig.savefig(output_dir / "figure1_population_access.pdf", format='pdf')
    fig.savefig(output_dir / "figure1_population_access.png", format='png')
    plt.close()


def create_figure_2_demographic_analysis():
    """Create Figure 2: Demographic Characteristics by Access Mode."""
    data = load_test_data()

    # Prepare data
    df = pd.DataFrame({
        'Mode': ['Walk', 'Bike', 'Drive'],
        'Median Income': [data['walk']['median_income'],
                          data['bike']['median_income'],
                          data['drive']['median_income']],
        'Population Density': [data['walk']['population_density'],
                               data['bike']['population_density'],
                               data['drive']['population_density']],
        'Census Units': [data['walk']['census_units'],
                         data['bike']['census_units'],
                         data['drive']['census_units']]
    })

    # Create figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

    # Panel A: Median Income
    sns.barplot(data=df, x='Mode', y='Median Income', ax=ax1,
                palette=[COLORS['walk'], COLORS['bike'], COLORS['drive']],
                edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('Median Household Income ($)', fontweight='bold')
    ax1.set_xlabel('Travel Mode', fontweight='bold')
    ax1.set_title('A. Median Household Income', fontweight='bold', pad=10)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${int(x):,}'))

    # Add value labels
    for i, (mode, income) in enumerate(zip(df['Mode'], df['Median Income'], strict=False)):
        ax1.text(i, income + 2000, f'${int(income):,}', ha='center', va='bottom', fontsize=9)

    # Panel B: Population Density
    sns.barplot(data=df, x='Mode', y='Population Density', ax=ax2,
                palette=[COLORS['walk'], COLORS['bike'], COLORS['drive']],
                edgecolor='black', linewidth=0.5)
    ax2.set_ylabel('People per Census Unit', fontweight='bold')
    ax2.set_xlabel('Travel Mode', fontweight='bold')
    ax2.set_title('B. Population Density', fontweight='bold', pad=10)

    # Add value labels
    for i, (mode, density) in enumerate(zip(df['Mode'], df['Population Density'], strict=False)):
        ax2.text(i, density + 20, f'{int(density):,}', ha='center', va='bottom', fontsize=9)

    # Panel C: Geographic Coverage
    sns.barplot(data=df, x='Mode', y='Census Units', ax=ax3,
                palette=[COLORS['walk'], COLORS['bike'], COLORS['drive']],
                edgecolor='black', linewidth=0.5)
    ax3.set_ylabel('Census Block Groups', fontweight='bold')
    ax3.set_xlabel('Travel Mode', fontweight='bold')
    ax3.set_title('C. Geographic Coverage', fontweight='bold', pad=10)

    # Add value labels
    for i, (mode, units) in enumerate(zip(df['Mode'], df['Census Units'], strict=False)):
        ax3.text(i, units + 1, f'{int(units)}', ha='center', va='bottom', fontsize=9)

    # Panel D: Income Distribution Box Plot (simulated data for demonstration)
    # In real analysis, this would use the actual income distribution data
    np.random.seed(42)
    income_data = []
    for mode, median in zip(['Walk', 'Bike', 'Drive'], df['Median Income'], strict=False):
        # Simulate income distribution around median
        incomes = np.random.normal(median, median * 0.3, 100)
        incomes = np.clip(incomes, 10000, 250000)  # Realistic bounds
        income_data.extend([(mode, inc) for inc in incomes])

    income_df = pd.DataFrame(income_data, columns=['Mode', 'Income'])

    sns.violinplot(data=income_df, x='Mode', y='Income', ax=ax4,
                   palette=[COLORS['walk'], COLORS['bike'], COLORS['drive']],
                   inner='box', linewidth=0.5)
    ax4.set_ylabel('Household Income ($)', fontweight='bold')
    ax4.set_xlabel('Travel Mode', fontweight='bold')
    ax4.set_title('D. Income Distribution (Simulated)', fontweight='bold', pad=10)
    ax4.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${int(x/1000)}k'))

    # Remove top and right spines for all subplots
    for ax in [ax1, ax2, ax3, ax4]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save figure
    output_dir = Path("publication_figures")
    fig.savefig(output_dir / "figure2_demographic_analysis.pdf", format='pdf')
    fig.savefig(output_dir / "figure2_demographic_analysis.png", format='png')
    plt.close()


def create_figure_3_equity_analysis():
    """Create Figure 3: Transit Equity Analysis."""
    data = load_test_data()

    # Calculate equity metrics
    walk_pop = data['walk']['total_population']
    bike_pop = data['bike']['total_population']
    drive_pop = data['drive']['total_population']

    # Population that needs each mode
    walk_only = walk_pop
    needs_bike = bike_pop - walk_pop
    needs_car = drive_pop - bike_pop

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: Population by minimum required mode (donut chart)
    sizes = [walk_only, needs_bike, needs_car]
    labels = ['Walking\nDistance', 'Requires\nBicycle', 'Requires\nCar']
    colors = [COLORS['walk'], COLORS['bike'], COLORS['drive']]

    # Create donut chart
    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors,
                                        autopct='%1.1f%%', startangle=90,
                                        wedgeprops=dict(width=0.5, edgecolor='black', linewidth=0.5),
                                        textprops={'fontsize': 10})

    # Add center text
    ax1.text(0, 0, f'Total Population\n{drive_pop:,}',
             ha='center', va='center', fontsize=12, fontweight='bold')

    ax1.set_title('A. Population Distribution by\nMinimum Required Travel Mode',
                  fontweight='bold', pad=20)

    # Panel B: Accessibility ratios
    modes = ['Walk', 'Bike', 'Drive']
    pop_ratios = [1.0, bike_pop/walk_pop, drive_pop/walk_pop]
    income_ratios = [1.0,
                     data['bike']['median_income']/data['walk']['median_income'],
                     data['drive']['median_income']/data['walk']['median_income']]

    x = np.arange(len(modes))
    width = 0.35

    bars1 = ax2.bar(x - width/2, pop_ratios, width,
                     label='Population Ratio',
                     color='#457B9D', edgecolor='black', linewidth=0.5)
    bars2 = ax2.bar(x + width/2, income_ratios, width,
                     label='Income Ratio',
                     color='#F1FAEE', edgecolor='black', linewidth=0.5)

    ax2.set_ylabel('Ratio (vs Walking)', fontweight='bold')
    ax2.set_xlabel('Travel Mode', fontweight='bold')
    ax2.set_title('B. Relative Access and Income', fontweight='bold', pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(modes)
    ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5, linewidth=0.5)
    ax2.legend(frameon=True, fancybox=False, shadow=False)

    # Add value labels
    for bar, ratio in zip(bars1, pop_ratios, strict=False):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{ratio:.1f}x', ha='center', va='bottom', fontsize=9)

    for bar, ratio in zip(bars2, income_ratios, strict=False):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{ratio:.2f}x', ha='center', va='bottom', fontsize=9)

    # Remove top and right spines
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add text annotation about equity gap
    fig.text(0.5, 0.02,
             f'Transit Equity Gap: {needs_bike + needs_car:,} people ({(needs_bike + needs_car)/drive_pop*100:.0f}%) cannot access libraries by walking',
             ha='center', fontsize=11, style='italic', wrap=True)

    plt.tight_layout()

    # Save figure
    output_dir = Path("publication_figures")
    fig.savefig(output_dir / "figure3_equity_analysis.pdf", format='pdf')
    fig.savefig(output_dir / "figure3_equity_analysis.png", format='png')
    plt.close()


def create_summary_table():
    """Create a summary table of key findings."""
    data = load_test_data()

    # Create summary dataframe
    summary_data = {
        'Metric': ['POIs Analyzed', 'Census Units', 'Total Population',
                   'Median Income', 'Population Density', 'Coverage Ratio'],
        'Walking': [
            data['walk']['poi_count'],
            data['walk']['census_units'],
            f"{data['walk']['total_population']:,}",
            f"${data['walk']['median_income']:,}",
            f"{data['walk']['population_density']:,}",
            "1.0x"
        ],
        'Bicycling': [
            data['bike']['poi_count'],
            data['bike']['census_units'],
            f"{data['bike']['total_population']:,}",
            f"${data['bike']['median_income']:,}",
            f"{data['bike']['population_density']:,}",
            f"{data['bike']['total_population']/data['walk']['total_population']:.1f}x"
        ],
        'Driving': [
            data['drive']['poi_count'],
            data['drive']['census_units'],
            f"{data['drive']['total_population']:,}",
            f"${data['drive']['median_income']:,}",
            f"{data['drive']['population_density']:,}",
            f"{data['drive']['total_population']/data['walk']['total_population']:.1f}x"
        ]
    }

    df = pd.DataFrame(summary_data)

    # Create figure for table
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')

    # Create table
    table = ax.table(cellText=df.values,
                     colLabels=df.columns,
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.3, 0.23, 0.23, 0.23])

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Header styling
    for i in range(len(df.columns)):
        table[(0, i)].set_facecolor('#E8E8E8')
        table[(0, i)].set_text_props(weight='bold')

    # Row styling
    for i in range(1, len(df) + 1):
        table[(i, 0)].set_facecolor('#F5F5F5')
        table[(i, 0)].set_text_props(weight='bold')

    plt.title('Table 1: Library Accessibility by Travel Mode in Chapel Hill, NC',
              fontsize=14, fontweight='bold', pad=20)

    # Save table
    output_dir = Path("publication_figures")
    fig.savefig(output_dir / "table1_summary.pdf", format='pdf')
    fig.savefig(output_dir / "table1_summary.png", format='png')
    plt.close()


def main():
    """Generate all publication figures."""
    print("Creating publication-quality figures...")

    # Create output directory
    output_dir = Path("publication_figures")
    output_dir.mkdir(exist_ok=True)

    # Generate figures
    create_figure_1_population_access()
    print("✓ Created Figure 1: Population Access")

    create_figure_2_demographic_analysis()
    print("✓ Created Figure 2: Demographic Analysis")

    create_figure_3_equity_analysis()
    print("✓ Created Figure 3: Equity Analysis")

    create_summary_table()
    print("✓ Created Table 1: Summary Statistics")

    print(f"\nAll figures saved to {output_dir}/")
    print("Available in both PDF and PNG formats")


if __name__ == "__main__":
    main()
