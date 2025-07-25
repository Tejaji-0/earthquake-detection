#!/usr/bin/env python3
"""
Script to add a 'Country' column to database.csv based on latitude and longitude coordinates.
Uses reverse geocoding to determine the country for each earthquake location.
"""

import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import os
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_country_from_coordinates(lat, lon, geolocator, max_retries=3):
    """
    Get country name from latitude and longitude coordinates.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        geolocator: Geopy geolocator instance
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Country name or 'Unknown' if not found
    """
    if pd.isna(lat) or pd.isna(lon):
        return 'Unknown'
    
    for attempt in range(max_retries):
        try:
            # Add a small delay between requests to be respectful to the service
            time.sleep(0.1)
            
            location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10)
            
            if location and location.raw.get('address'):
                address = location.raw['address']
                # Try different keys for country information
                country = (address.get('country') or 
                          address.get('country_name') or 
                          address.get('country_code'))
                
                if country:
                    return country
                    
            # If no country found in address, try to determine from coordinates
            # Simple ocean/land classification based on major water bodies
            if is_in_ocean(lat, lon):
                return get_ocean_name(lat, lon)
                
            return 'Unknown'
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding attempt {attempt + 1} failed for ({lat}, {lon}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to geocode ({lat}, {lon}) after {max_retries} attempts")
                return 'Unknown'
        except Exception as e:
            logger.error(f"Unexpected error geocoding ({lat}, {lon}): {e}")
            return 'Unknown'

def is_in_ocean(lat, lon):
    """
    Simple check to determine if coordinates are likely in ocean.
    This is a basic implementation and could be improved with more sophisticated methods.
    """
    # Very basic ocean detection - could be enhanced with coastline data
    # For now, just handle obvious ocean areas
    return False  # We'll rely on the geocoder for now

def get_ocean_name(lat, lon):
    """
    Get ocean name based on coordinates.
    """
    if lat > 0:
        if -180 <= lon <= -30:
            return 'North Atlantic Ocean'
        elif -30 < lon <= 60:
            return 'Indian Ocean' if lat < 30 else 'Arctic Ocean'
        elif 60 < lon <= 180:
            return 'North Pacific Ocean'
    else:
        if -180 <= lon <= -30:
            return 'South Atlantic Ocean'
        elif -30 < lon <= 60:
            return 'Indian Ocean'
        elif 60 < lon <= 180:
            return 'South Pacific Ocean'
    
    return 'Unknown Ocean'

def process_earthquake_data(input_file, output_file=None, batch_size=100):
    """
    Process the earthquake database and add country information.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (optional)
        batch_size (int): Number of rows to process before saving progress
    """
    if output_file is None:
        output_file = input_file.replace('.csv', '_with_countries.csv')
    
    logger.info(f"Reading data from {input_file}")
    
    # Read the CSV file
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to read {input_file}: {e}")
        return
    
    # Check if Country column already exists
    if 'Country' in df.columns:
        logger.info("Country column already exists. Checking for missing values...")
        missing_countries = df['Country'].isna().sum()
        if missing_countries == 0:
            logger.info("All records already have country information.")
            return
        else:
            logger.info(f"Found {missing_countries} records missing country information.")
    else:
        logger.info("Adding new Country column")
        df['Country'] = 'Unknown'
    
    # Initialize geocoder
    geolocator = Nominatim(user_agent="earthquake_country_detector_v1.0")
    
    # Process data in batches
    total_rows = len(df)
    processed_count = 0
    
    # Only process rows that don't have country information
    rows_to_process = df[df['Country'].isna() | (df['Country'] == 'Unknown')].index
    
    logger.info(f"Processing {len(rows_to_process)} records that need country information...")
    
    try:
        for idx in tqdm(rows_to_process, desc="Adding country information"):
            lat = df.loc[idx, 'Latitude']
            lon = df.loc[idx, 'Longitude']
            
            country = get_country_from_coordinates(lat, lon, geolocator)
            df.loc[idx, 'Country'] = country
            
            processed_count += 1
            
            # Save progress every batch_size records
            if processed_count % batch_size == 0:
                logger.info(f"Processed {processed_count}/{len(rows_to_process)} records. Saving progress...")
                df.to_csv(output_file, index=False)
                
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Saving current progress...")
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
    
    # Final save
    logger.info(f"Saving final results to {output_file}")
    df.to_csv(output_file, index=False)
    
    # Print summary statistics
    country_counts = df['Country'].value_counts()
    logger.info(f"\nProcessing complete! Summary:")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Records processed: {processed_count}")
    logger.info(f"Unique countries found: {len(country_counts)}")
    logger.info(f"Top 10 countries by earthquake count:")
    print(country_counts.head(10))
    
    # Show records with unknown countries
    unknown_count = (df['Country'] == 'Unknown').sum()
    if unknown_count > 0:
        logger.warning(f"Warning: {unknown_count} records still have 'Unknown' country")
        
    logger.info(f"Results saved to: {output_file}")

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
        return
    
    logger.info("Starting earthquake database country enrichment process...")
    logger.info("This process may take a while due to API rate limits for geocoding...")
    
    # Process the data
    process_earthquake_data(input_file, output_file)
    
    logger.info("Process completed!")

if __name__ == "__main__":
    main()
