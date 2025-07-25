#!/usr/bin/env python3
"""
Simple script to add a 'Country' column to database.csv based on latitude and longitude coordinates.
Uses basic geographical rules for major regions as a fallback when geocoding is not available.
"""

import pandas as pd
import numpy as np
import os
import logging
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_country_from_coordinates_simple(lat, lon):
    """
    Simple country/region detection based on latitude and longitude coordinates.
    This is a basic implementation using geographical boundaries.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        str: Country/region name or 'Unknown' if not determinable
    """
    if pd.isna(lat) or pd.isna(lon):
        return 'Unknown'
    
    # Convert to float for comparison
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return 'Unknown'
    
    # Basic country/region mapping based on coordinate ranges
    # This is a simplified approach - real-world boundaries are more complex
    
    # Major ocean regions
    if is_likely_ocean(lat, lon):
        return get_ocean_region(lat, lon)
    
    # Continental regions (simplified)
    
    # North America
    if 25 <= lat <= 85 and -170 <= lon <= -50:
        if lat >= 60:
            return 'Canada/Alaska'
        elif lat >= 49 and lon <= -95:
            return 'Canada'
        elif lat >= 25 and -125 <= lon <= -66:
            if lon >= -95:
                return 'United States (Eastern)'
            else:
                return 'United States (Western)'
        elif 15 <= lat <= 32 and -118 <= lon <= -86:
            return 'Mexico'
        else:
            return 'North America'
    
    # South America
    elif -60 <= lat <= 15 and -85 <= lon <= -30:
        if lat >= 5:
            return 'Northern South America'
        elif -20 <= lat <= 5:
            return 'Central South America'
        else:
            return 'Southern South America'
    
    # Europe
    elif 35 <= lat <= 75 and -15 <= lon <= 45:
        if lat >= 60:
            return 'Northern Europe'
        elif 45 <= lat <= 60:
            return 'Central Europe'
        else:
            return 'Southern Europe'
    
    # Asia
    elif 5 <= lat <= 80 and 25 <= lon <= 180:
        if lat >= 55:
            return 'Northern Asia/Russia'
        elif 35 <= lat <= 55 and 70 <= lon <= 140:
            return 'Central Asia'
        elif 20 <= lat <= 50 and 100 <= lon <= 145:
            return 'East Asia'
        elif 5 <= lat <= 35 and 65 <= lon <= 100:
            return 'South Asia'
        elif 10 <= lat <= 40 and 25 <= lon <= 65:
            return 'Middle East'
        else:
            return 'Asia'
    
    # Africa
    elif -40 <= lat <= 40 and -20 <= lon <= 55:
        if lat >= 20:
            return 'Northern Africa'
        elif 0 <= lat <= 20:
            return 'Central Africa'
        else:
            return 'Southern Africa'
    
    # Australia and Oceania
    elif -50 <= lat <= 5 and 110 <= lon <= 180:
        if -30 <= lat <= -10 and 110 <= lon <= 155:
            return 'Australia'
        else:
            return 'Oceania/Pacific Islands'
    
    # Pacific region
    elif -60 <= lat <= 60 and 130 <= lon <= 180:
        return 'Pacific Ocean Region'
    elif -60 <= lat <= 60 and -180 <= lon <= -120:
        return 'Pacific Ocean Region'
    
    # Antarctica
    elif lat <= -60:
        return 'Antarctica'
    
    # Arctic
    elif lat >= 75:
        return 'Arctic'
    
    return 'Unknown Region'

def is_likely_ocean(lat, lon):
    """
    Simple check to determine if coordinates are likely in ocean based on major land masses.
    """
    # This is a very basic implementation
    # Most areas not covered by major continental boundaries are likely ocean
    
    # Major continental boundaries (simplified)
    continental_regions = [
        # North America
        (25, 85, -170, -50),
        # South America  
        (-60, 15, -85, -30),
        # Europe
        (35, 75, -15, 45),
        # Asia
        (5, 80, 25, 180),
        # Africa
        (-40, 40, -20, 55),
        # Australia/Oceania
        (-50, 5, 110, 180)
    ]
    
    for lat_min, lat_max, lon_min, lon_max in continental_regions:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return False
    
    return True

def get_ocean_region(lat, lon):
    """
    Get ocean region name based on coordinates.
    """
    # Pacific Ocean
    if (lon >= 120 or lon <= -120):
        if lat >= 0:
            return 'North Pacific Ocean'
        else:
            return 'South Pacific Ocean'
    
    # Atlantic Ocean
    elif -70 <= lon <= 20:
        if lat >= 0:
            return 'North Atlantic Ocean'
        else:
            return 'South Atlantic Ocean'
    
    # Indian Ocean
    elif 20 <= lon <= 120 and lat <= 30:
        return 'Indian Ocean'
    
    # Arctic Ocean
    elif lat >= 70:
        return 'Arctic Ocean'
    
    # Southern Ocean
    elif lat <= -50:
        return 'Southern Ocean'
    
    return 'Ocean'

def analyze_database_structure(df):
    """
    Analyze the structure and content of the database.
    """
    logger.info("\n=== Database Analysis ===")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    
    # Check for missing coordinates
    missing_lat = df['Latitude'].isna().sum()
    missing_lon = df['Longitude'].isna().sum()
    logger.info(f"Missing latitude values: {missing_lat}")
    logger.info(f"Missing longitude values: {missing_lon}")
    
    # Coordinate ranges
    if len(df) > 0:
        lat_range = (df['Latitude'].min(), df['Latitude'].max())
        lon_range = (df['Longitude'].min(), df['Longitude'].max())
        logger.info(f"Latitude range: {lat_range}")
        logger.info(f"Longitude range: {lon_range}")
    
    # Sample of data
    logger.info("\nSample records:")
    print(df[['Date', 'Latitude', 'Longitude', 'Magnitude']].head())

def process_earthquake_data_simple(input_file, output_file=None):
    """
    Process the earthquake database and add country/region information using simple rules.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (optional)
    """
    if output_file is None:
        output_file = input_file.replace('.csv', '_with_countries.csv')
    
    logger.info(f"Reading data from {input_file}")
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Successfully loaded {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to read {input_file}: {e}")
        return None
    
    # Analyze the database structure
    analyze_database_structure(df)
    
    # Check if Country column already exists
    if 'Country' in df.columns:
        logger.info("Country column already exists. Will update missing values.")
        rows_to_process = df[df['Country'].isna() | (df['Country'] == 'Unknown')].index
    else:
        logger.info("Adding new Country column")
        df['Country'] = 'Unknown'
        rows_to_process = df.index
    
    logger.info(f"Processing {len(rows_to_process)} records...")
    
    # Process each row
    for idx in tqdm(rows_to_process, desc="Adding country/region information"):
        lat = df.loc[idx, 'Latitude']
        lon = df.loc[idx, 'Longitude']
        
        country = get_country_from_coordinates_simple(lat, lon)
        df.loc[idx, 'Country'] = country
    
    # Save the updated data
    logger.info(f"Saving results to {output_file}")
    df.to_csv(output_file, index=False)
    
    # Generate summary statistics
    logger.info("\n=== Results Summary ===")
    country_counts = df['Country'].value_counts()
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Unique countries/regions found: {len(country_counts)}")
    
    logger.info(f"\nTop 15 countries/regions by earthquake count:")
    print(country_counts.head(15))
    
    # Show records with unknown regions
    unknown_count = (df['Country'] == 'Unknown Region').sum() + (df['Country'] == 'Unknown').sum()
    if unknown_count > 0:
        logger.warning(f"Warning: {unknown_count} records still have 'Unknown' region")
        
    logger.info(f"\nResults saved to: {output_file}")
    
    return df

def main():
    """Main function to run the country addition process."""
    
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'data', 'database.csv')
    output_file = os.path.join(script_dir, 'data', 'database_with_countries.csv')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please ensure the database.csv file exists in the data/ directory")
        logger.info(f"Expected path: {input_file}")
        return
    
    logger.info("Starting earthquake database country/region enrichment process...")
    logger.info("Using simplified geographical rules for country/region detection...")
    
    # Process the data
    result_df = process_earthquake_data_simple(input_file, output_file)
    
    if result_df is not None:
        logger.info("Process completed successfully!")
    else:
        logger.error("Process failed!")

if __name__ == "__main__":
    main()
