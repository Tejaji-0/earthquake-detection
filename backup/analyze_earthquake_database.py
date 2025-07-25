#!/usr/bin/env python3
"""
Analysis script to validate and analyze the country-enriched earthquake database.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import Counter

def analyze_earthquake_database(csv_file):
    """
    Comprehensive analysis of the earthquake database with country information.
    """
    
    print("=" * 80)
    print("EARTHQUAKE DATABASE COUNTRY ANALYSIS")
    print("=" * 80)
    
    # Load data
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Successfully loaded {len(df)} earthquake records")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS")
    print("-" * 50)
    print(f"Total earthquakes: {len(df):,}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    if 'Magnitude' in df.columns:
        mag_stats = df['Magnitude'].describe()
        print(f"Magnitude range: {mag_stats['min']:.1f} to {mag_stats['max']:.1f}")
        print(f"Average magnitude: {mag_stats['mean']:.2f}")
        print(f"Major earthquakes (≥7.0): {len(df[df['Magnitude'] >= 7.0]):,}")
        print(f"Great earthquakes (≥8.0): {len(df[df['Magnitude'] >= 8.0]):,}")
    
    # Country analysis
    print(f"\n🌍 COUNTRY/REGION ANALYSIS")
    print("-" * 50)
    
    if 'Country' not in df.columns:
        print("❌ No Country column found in the database")
        return
    
    country_counts = df['Country'].value_counts()
    print(f"Unique countries/regions identified: {len(country_counts)}")
    
    # Data quality assessment
    unknown_variants = ['Unknown', 'Unknown Region', 'Uncertain']
    unknown_count = df['Country'].isin(unknown_variants).sum()
    quality_percentage = (len(df) - unknown_count) / len(df) * 100
    print(f"Data quality: {quality_percentage:.1f}% have identified countries/regions")
    print(f"Unknown locations: {unknown_count:,} records")
    
    # Top countries by earthquake count
    print(f"\n🔥 TOP 20 MOST SEISMICALLY ACTIVE COUNTRIES/REGIONS")
    print("-" * 50)
    for i, (country, count) in enumerate(country_counts.head(20).items(), 1):
        percentage = count / len(df) * 100
        print(f"{i:2d}. {country:<25} {count:>6,} ({percentage:5.1f}%)")
    
    # Continental analysis
    print(f"\n🌏 ANALYSIS BY MAJOR REGIONS")
    print("-" * 50)
    
    # Group countries into major regions
    pacific_ring = ['Japan', 'Indonesia', 'Philippines', 'Chile', 'Peru', 'Mexico', 
                   'Papua New Guinea', 'New Zealand', 'Russia', 'United States']
    
    oceanic_regions = ['North Pacific Ocean', 'South Pacific Ocean', 'North Atlantic Ocean',
                      'South Atlantic Ocean', 'Indian Ocean', 'Southern Ocean', 'Arctic Ocean', 'Ocean']
    
    asian_countries = ['China', 'Japan', 'Indonesia', 'Philippines', 'India', 'Iran', 'Turkey']
    
    americas = ['United States', 'Canada', 'Mexico', 'Chile', 'Peru', 'Brazil', 'Argentina',
               'Central America', 'Caribbean Region']
    
    # Calculate regional statistics
    def count_regional_earthquakes(countries_list, region_name):
        region_count = df[df['Country'].isin(countries_list)]['Country'].value_counts().sum()
        print(f"{region_name:<25} {region_count:>6,} ({region_count/len(df)*100:5.1f}%)")
        return region_count
    
    pacific_count = count_regional_earthquakes(pacific_ring, "Pacific Ring of Fire")
    oceanic_count = count_regional_earthquakes(oceanic_regions, "Oceanic Regions")
    asian_count = count_regional_earthquakes(asian_countries, "Asian Countries")
    americas_count = count_regional_earthquakes(americas, "Americas")
    
    # Magnitude analysis by region
    print(f"\n⚡ MAGNITUDE ANALYSIS BY TOP COUNTRIES")
    print("-" * 50)
    
    top_countries = country_counts.head(10).index
    
    for country in top_countries:
        country_data = df[df['Country'] == country]
        if len(country_data) > 0 and 'Magnitude' in df.columns:
            avg_mag = country_data['Magnitude'].mean()
            max_mag = country_data['Magnitude'].max()
            major_quakes = len(country_data[country_data['Magnitude'] >= 7.0])
            print(f"{country:<25} Avg: {avg_mag:.2f}, Max: {max_mag:.1f}, Major (≥7.0): {major_quakes}")
    
    # Time analysis
    print(f"\n📅 TEMPORAL ANALYSIS")
    print("-" * 50)
    
    # Convert dates and analyze by decade
    try:
        # Handle different date formats
        df['Date_clean'] = pd.to_datetime(df['Date'], errors='coerce')
        df_with_dates = df.dropna(subset=['Date_clean'])
        
        if len(df_with_dates) > 0:
            df_with_dates['Year'] = df_with_dates['Date_clean'].dt.year
            df_with_dates['Decade'] = (df_with_dates['Year'] // 10) * 10
            
            decade_counts = df_with_dates['Decade'].value_counts().sort_index()
            print("Earthquakes by decade:")
            for decade, count in decade_counts.items():
                print(f"{decade}s: {count:,} earthquakes")
        else:
            print("Could not parse date information for temporal analysis")
            
    except Exception as e:
        print(f"Error in temporal analysis: {e}")
    
    # Coordinate validation
    print(f"\n🗺️  COORDINATE VALIDATION")
    print("-" * 50)
    
    # Check for invalid coordinates
    invalid_lat = df[(df['Latitude'] < -90) | (df['Latitude'] > 90)]
    invalid_lon = df[(df['Longitude'] < -180) | (df['Longitude'] > 180)]
    
    print(f"Records with invalid latitude: {len(invalid_lat)}")
    print(f"Records with invalid longitude: {len(invalid_lon)}")
    
    # Geographic distribution
    hemisphere_analysis = {
        'Northern Hemisphere': len(df[df['Latitude'] >= 0]),
        'Southern Hemisphere': len(df[df['Latitude'] < 0]),
        'Eastern Hemisphere': len(df[df['Longitude'] >= 0]),
        'Western Hemisphere': len(df[df['Longitude'] < 0])
    }
    
    print("\nGeographic distribution:")
    for hemisphere, count in hemisphere_analysis.items():
        percentage = count / len(df) * 100
        print(f"{hemisphere:<20} {count:>6,} ({percentage:5.1f}%)")
    
    # Data completeness
    print(f"\n✅ DATA COMPLETENESS")
    print("-" * 50)
    
    for column in ['Date', 'Latitude', 'Longitude', 'Magnitude', 'Depth', 'Country']:
        if column in df.columns:
            missing = df[column].isna().sum()
            complete_pct = (len(df) - missing) / len(df) * 100
            print(f"{column:<15} {complete_pct:6.1f}% complete ({len(df)-missing:,}/{len(df):,})")
    
    print(f"\n🎯 SUMMARY")
    print("-" * 50)
    print(f"✅ Successfully processed {len(df):,} earthquake records")
    print(f"✅ Identified {len(country_counts)} unique countries/regions")
    print(f"✅ {quality_percentage:.1f}% data quality for country identification")
    print(f"✅ Database covers {df['Date'].nunique()} unique dates")
    
    if 'Magnitude' in df.columns:
        print(f"✅ Magnitude range: {df['Magnitude'].min():.1f} - {df['Magnitude'].max():.1f}")
    
    return df

def create_visualization_summary(df, output_dir="."):
    """
    Create simple visualization summaries.
    """
    
    try:
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Earthquake Database Analysis Summary', fontsize=16, fontweight='bold')
        
        # 1. Top countries bar chart
        top_countries = df['Country'].value_counts().head(15)
        axes[0, 0].barh(range(len(top_countries)), top_countries.values)
        axes[0, 0].set_yticks(range(len(top_countries)))
        axes[0, 0].set_yticklabels(top_countries.index, fontsize=8)
        axes[0, 0].set_xlabel('Number of Earthquakes')
        axes[0, 0].set_title('Top 15 Countries/Regions by Earthquake Count')
        axes[0, 0].invert_yaxis()
        
        # 2. Magnitude distribution
        if 'Magnitude' in df.columns:
            axes[0, 1].hist(df['Magnitude'].dropna(), bins=30, alpha=0.7, color='orange')
            axes[0, 1].axvline(df['Magnitude'].mean(), color='red', linestyle='--', 
                              label=f'Mean: {df["Magnitude"].mean():.2f}')
            axes[0, 1].set_xlabel('Magnitude')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].set_title('Earthquake Magnitude Distribution')
            axes[0, 1].legend()
        
        # 3. Geographic distribution
        valid_coords = df[(df['Latitude'].between(-90, 90)) & (df['Longitude'].between(-180, 180))]
        scatter = axes[1, 0].scatter(valid_coords['Longitude'], valid_coords['Latitude'], 
                                   s=1, alpha=0.5, c='blue')
        axes[1, 0].set_xlabel('Longitude')
        axes[1, 0].set_ylabel('Latitude')
        axes[1, 0].set_title('Global Distribution of Earthquakes')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Data quality pie chart
        quality_data = {
            'Identified': len(df[~df['Country'].isin(['Unknown', 'Unknown Region'])]),
            'Unknown': len(df[df['Country'].isin(['Unknown', 'Unknown Region'])])
        }
        
        axes[1, 1].pie(quality_data.values(), labels=quality_data.keys(), 
                      autopct='%1.1f%%', startangle=90)
        axes[1, 1].set_title('Country Identification Success Rate')
        
        plt.tight_layout()
        
        # Save the plot
        output_file = os.path.join(output_dir, 'earthquake_analysis_summary.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n📊 Visualization saved to: {output_file}")
        
        plt.show()
        
    except Exception as e:
        print(f"Error creating visualizations: {e}")

def main():
    """
    Main analysis function.
    """
    
    # Set up file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for available files
    files_to_check = [
        'data/database_with_countries_fast.csv',
        'data/database_with_countries.csv',
        'data/database.csv'
    ]
    
    input_file = None
    for file_path in files_to_check:
        full_path = os.path.join(script_dir, file_path)
        if os.path.exists(full_path):
            input_file = full_path
            break
    
    if not input_file:
        print("❌ No earthquake database file found!")
        print("Expected files:")
        for file_path in files_to_check:
            print(f"  - {file_path}")
        return
    
    print(f"📁 Analyzing file: {os.path.basename(input_file)}")
    
    # Run analysis
    df = analyze_earthquake_database(input_file)
    
    if df is not None:
        # Create visualizations
        create_visualization_summary(df, output_dir=os.path.dirname(input_file))
        
        print(f"\n✅ Analysis complete!")
        print(f"📁 Database file: {input_file}")
    else:
        print("❌ Analysis failed!")

if __name__ == "__main__":
    main()
