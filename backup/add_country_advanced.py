#!/usr/bin/env python3
"""
Advanced script to add a 'Country' column to database.csv based on latitude and longitude coordinates.
Uses multiple approaches: offline country boundaries, reverse geocoding, and geographical rules.
"""

import pandas as pd
import numpy as np
import os
import logging
from tqdm import tqdm
import json

# Optional imports - will fallback gracefully if not available
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    import time
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("geopy not available - will use simplified geographical mapping")

try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False
    print("pycountry not available - will use basic country names")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CountryDetector:
    """
    Class to detect countries from coordinates using multiple methods.
    """
    
    def __init__(self, use_geocoding=True):
        self.use_geocoding = use_geocoding and GEOPY_AVAILABLE
        self.geolocator = None
        self.geocoding_cache = {}
        
        if self.use_geocoding:
            self.geolocator = Nominatim(user_agent="earthquake_country_detector_v2.0")
            logger.info("Initialized with geocoding support")
        else:
            logger.info("Initialized without geocoding - using geographical rules only")
    
    def get_country_with_geocoding(self, lat, lon, max_retries=3):
        """
        Get country using online geocoding service.
        """
        cache_key = f"{lat:.3f},{lon:.3f}"  # Round to reduce cache size
        
        if cache_key in self.geocoding_cache:
            return self.geocoding_cache[cache_key]
        
        for attempt in range(max_retries):
            try:
                time.sleep(0.2)  # Be respectful to the service
                
                location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=10)
                
                if location and location.raw.get('address'):
                    address = location.raw['address']
                    country = (address.get('country') or 
                              address.get('country_name') or 
                              address.get('country_code'))
                    
                    if country:
                        # Standardize country name if pycountry is available
                        if PYCOUNTRY_AVAILABLE:
                            try:
                                country_obj = pycountry.countries.lookup(country)
                                country = country_obj.name
                            except LookupError:
                                pass
                        
                        self.geocoding_cache[cache_key] = country
                        return country
                
                break  # If no country found, don't retry
                
            except (GeocoderTimedOut, GeocoderServiceError):
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    break
            except Exception:
                break
        
        # Cache the failure to avoid repeated attempts
        self.geocoding_cache[cache_key] = None
        return None
    
    def get_country_from_coordinates(self, lat, lon):
        """
        Main method to get country from coordinates using available methods.
        """
        if pd.isna(lat) or pd.isna(lon):
            return 'Unknown'
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return 'Unknown'
        
        # Try geocoding first if available
        if self.use_geocoding:
            country = self.get_country_with_geocoding(lat, lon)
            if country:
                return country
        
        # Fallback to geographical rules
        return self.get_country_from_geography(lat, lon)
    
    def get_country_from_geography(self, lat, lon):
        """
        Get country/region using geographical boundaries and rules.
        More detailed than the simple version.
        """
        
        # Specific country boundaries (simplified but more accurate)
        
        # United States (including Alaska and Hawaii)
        if ((25 <= lat <= 49 and -125 <= lon <= -66) or  # Continental US
            (55 <= lat <= 72 and -168 <= lon <= -141) or  # Alaska
            (18 <= lat <= 23 and -162 <= lon <= -154)):   # Hawaii
            return 'United States'
        
        # Canada
        if 42 <= lat <= 84 and -141 <= lon <= -52:
            return 'Canada'
        
        # Mexico
        if 14 <= lat <= 33 and -118 <= lon <= -86:
            return 'Mexico'
        
        # Japan
        if 24 <= lat <= 46 and 122 <= lon <= 146:
            return 'Japan'
        
        # Indonesia
        if -11 <= lat <= 6 and 95 <= lon <= 141:
            return 'Indonesia'
        
        # Philippines
        if 5 <= lat <= 21 and 116 <= lon <= 127:
            return 'Philippines'
        
        # Chile
        if -56 <= lat <= -17 and -76 <= lon <= -66:
            return 'Chile'
        
        # New Zealand
        if -47 <= lat <= -34 and 166 <= lon <= 179:
            return 'New Zealand'
        
        # Turkey
        if 36 <= lat <= 42 and 26 <= lon <= 45:
            return 'Turkey'
        
        # Italy
        if 36 <= lat <= 47 and 6 <= lon <= 19:
            return 'Italy'
        
        # Greece
        if 34 <= lat <= 42 and 19 <= lon <= 30:
            return 'Greece'
        
        # Iran
        if 25 <= lat <= 40 and 44 <= lon <= 64:
            return 'Iran'
        
        # China
        if 18 <= lat <= 54 and 73 <= lon <= 135:
            return 'China'
        
        # Russia
        if 41 <= lat <= 82 and 19 <= lon <= 180:
            return 'Russia'
        
        # India
        if 6 <= lat <= 38 and 68 <= lon <= 98:
            return 'India'
        
        # Australia
        if -44 <= lat <= -10 and 112 <= lon <= 154:
            return 'Australia'
        
        # Papua New Guinea
        if -12 <= lat <= -1 and 140 <= lon <= 160:
            return 'Papua New Guinea'
        
        # Peru
        if -19 <= lat <= 0 and -82 <= lon <= -68:
            return 'Peru'
        
        # Ecuador
        if -5 <= lat <= 2 and -82 <= lon <= -75:
            return 'Ecuador'
        
        # Colombia
        if -5 <= lat <= 13 and -80 <= lon <= -66:
            return 'Colombia'
        
        # Venezuela
        if 0 <= lat <= 13 and -74 <= lon <= -59:
            return 'Venezuela'
        
        # Brazil
        if -34 <= lat <= 6 and -75 <= lon <= -30:
            return 'Brazil'
        
        # Argentina
        if -55 <= lat <= -21 and -74 <= lon <= -53:
            return 'Argentina'
        
        # Ocean regions with more specific names
        if self.is_in_ocean(lat, lon):
            return self.get_specific_ocean_region(lat, lon)
        
        # Regional fallbacks
        return self.get_regional_fallback(lat, lon)
    
    def is_in_ocean(self, lat, lon):
        """
        Check if coordinates are in ocean using land boundaries.
        """
        # Major land regions (more comprehensive)
        land_regions = [
            # North America
            (10, 85, -170, -50),
            # South America  
            (-60, 15, -85, -30),
            # Europe
            (35, 75, -15, 45),
            # Asia
            (-15, 80, 25, 180),
            # Africa
            (-40, 40, -20, 55),
            # Australia/Oceania main landmasses
            (-50, -10, 110, 180)
        ]
        
        for lat_min, lat_max, lon_min, lon_max in land_regions:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                # Additional checks for major water bodies within these regions
                if self.is_major_sea_or_lake(lat, lon):
                    return True
                return False
        
        return True
    
    def is_major_sea_or_lake(self, lat, lon):
        """
        Check if coordinates are in major seas or lakes within continental regions.
        """
        # Mediterranean Sea
        if 30 <= lat <= 46 and -6 <= lon <= 37:
            return True
        
        # Black Sea
        if 40 <= lat <= 48 and 27 <= lon <= 42:
            return True
        
        # Caspian Sea
        if 36 <= lat <= 47 and 46 <= lon <= 55:
            return True
        
        # Great Lakes region
        if 41 <= lat <= 49 and -93 <= lon <= -76:
            return True
        
        return False
    
    def get_specific_ocean_region(self, lat, lon):
        """
        Get specific ocean/sea region names.
        """
        # Mediterranean Sea
        if 30 <= lat <= 46 and -6 <= lon <= 37:
            return 'Mediterranean Sea'
        
        # Black Sea
        if 40 <= lat <= 48 and 27 <= lon <= 42:
            return 'Black Sea'
        
        # Caspian Sea
        if 36 <= lat <= 47 and 46 <= lon <= 55:
            return 'Caspian Sea'
        
        # Pacific Ocean regions
        if (120 <= lon <= 180) or (-180 <= lon <= -100):
            if lat >= 40:
                return 'North Pacific Ocean'
            elif lat <= -40:
                return 'South Pacific Ocean'
            elif -10 <= lat <= 10:
                return 'Equatorial Pacific Ocean'
            else:
                return 'Pacific Ocean'
        
        # Atlantic Ocean regions
        if -80 <= lon <= 20:
            if lat >= 40:
                return 'North Atlantic Ocean'
            elif lat <= -40:
                return 'South Atlantic Ocean'
            elif -10 <= lat <= 10:
                return 'Equatorial Atlantic Ocean'
            else:
                return 'Atlantic Ocean'
        
        # Indian Ocean
        if 20 <= lon <= 120 and -50 <= lat <= 30:
            return 'Indian Ocean'
        
        # Arctic Ocean
        if lat >= 70:
            return 'Arctic Ocean'
        
        # Southern Ocean
        if lat <= -50:
            return 'Southern Ocean'
        
        return 'Ocean'
    
    def get_regional_fallback(self, lat, lon):
        """
        Regional fallback for areas not specifically identified.
        """
        # Regional classifications
        
        # Caribbean
        if 10 <= lat <= 25 and -85 <= lon <= -60:
            return 'Caribbean Region'
        
        # Central America
        if 7 <= lat <= 18 and -92 <= lon <= -77:
            return 'Central America'
        
        # Middle East
        if 12 <= lat <= 42 and 25 <= lon <= 65:
            return 'Middle East'
        
        # Southeast Asia
        if -15 <= lat <= 25 and 90 <= lon <= 145:
            return 'Southeast Asia'
        
        # Northern Europe
        if 55 <= lat <= 75 and -15 <= lon <= 45:
            return 'Northern Europe'
        
        # Eastern Europe
        if 45 <= lat <= 70 and 15 <= lon <= 50:
            return 'Eastern Europe'
        
        # Western Europe
        if 40 <= lat <= 60 and -15 <= lon <= 20:
            return 'Western Europe'
        
        # North Africa
        if 15 <= lat <= 40 and -20 <= lon <= 40:
            return 'North Africa'
        
        # East Africa
        if -15 <= lat <= 20 and 25 <= lon <= 55:
            return 'East Africa'
        
        # West Africa
        if 0 <= lat <= 25 and -25 <= lon <= 20:
            return 'West Africa'
        
        # Southern Africa
        if -40 <= lat <= -15 and 10 <= lon <= 40:
            return 'Southern Africa'
        
        # Central Asia
        if 35 <= lat <= 55 and 45 <= lon <= 85:
            return 'Central Asia'
        
        # Antarctica
        if lat <= -60:
            return 'Antarctica'
        
        # Arctic regions
        if lat >= 75:
            return 'Arctic Region'
        
        return 'Unknown Region'

def process_earthquake_database(input_file, output_file=None, use_geocoding=False, sample_size=None):
    """
    Process the earthquake database and add country information.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        use_geocoding (bool): Whether to use online geocoding service
        sample_size (int): Process only a sample of records (for testing)
    """
    if output_file is None:
        output_file = input_file.replace('.csv', '_with_countries.csv')
    
    logger.info(f"Reading data from {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Successfully loaded {len(df)} records")
    except Exception as e:
        logger.error(f"Failed to read {input_file}: {e}")
        return None
    
    # Sample data if requested
    if sample_size and sample_size < len(df):
        logger.info(f"Processing sample of {sample_size} records")
        df = df.head(sample_size)
    
    # Initialize country detector
    detector = CountryDetector(use_geocoding=use_geocoding)
    
    # Check existing Country column
    if 'Country' in df.columns:
        logger.info("Country column exists - updating missing values")
        mask = df['Country'].isna() | (df['Country'] == 'Unknown')
        rows_to_process = df[mask].index
    else:
        logger.info("Adding new Country column")
        df['Country'] = 'Unknown'
        rows_to_process = df.index
    
    logger.info(f"Processing {len(rows_to_process)} records...")
    
    # Process records
    processed_count = 0
    for idx in tqdm(rows_to_process, desc="Adding country information"):
        lat = df.loc[idx, 'Latitude']
        lon = df.loc[idx, 'Longitude']
        
        country = detector.get_country_from_coordinates(lat, lon)
        df.loc[idx, 'Country'] = country
        
        processed_count += 1
        
        # Save progress periodically for large datasets
        if processed_count % 1000 == 0 and use_geocoding:
            logger.info(f"Processed {processed_count} records, saving progress...")
            df.to_csv(output_file, index=False)
    
    # Final save
    logger.info(f"Saving final results to {output_file}")
    df.to_csv(output_file, index=False)
    
    # Print summary
    logger.info("\n=== Processing Summary ===")
    country_counts = df['Country'].value_counts()
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Unique countries/regions: {len(country_counts)}")
    
    logger.info("\nTop 20 countries/regions by earthquake count:")
    print(country_counts.head(20))
    
    # Save geocoding cache if used
    if use_geocoding and detector.geocoding_cache:
        cache_file = output_file.replace('.csv', '_geocoding_cache.json')
        with open(cache_file, 'w') as f:
            json.dump(detector.geocoding_cache, f)
        logger.info(f"Saved geocoding cache to {cache_file}")
    
    return df

def main():
    """Main function with command-line-like options."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'data', 'database.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    logger.info("=== Earthquake Database Country Enrichment ===")
    logger.info(f"Input file: {input_file}")
    
    # Process with geographical rules only (fast)
    logger.info("\nProcessing with geographical rules...")
    output_file = os.path.join(script_dir, 'data', 'database_with_countries.csv')
    
    process_earthquake_database(
        input_file=input_file,
        output_file=output_file,
        use_geocoding=False  # Set to True to enable online geocoding
    )
    
    logger.info("Process completed!")

if __name__ == "__main__":
    main()
