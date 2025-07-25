#!/usr/bin/env python3
"""
Final comprehensive script to check database.csv and add accurate country information.
This script combines geographical rules with selective geocoding for optimal accuracy and speed.
"""

import pandas as pd
import numpy as np
import os
import logging
from tqdm import tqdm
import json
import argparse

# Optional imports with graceful fallback
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    import time
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveCountryDetector:
    """
    Comprehensive country detector using multiple strategies for accuracy and speed.
    """
    
    def __init__(self, use_geocoding=False, cache_file=None):
        self.use_geocoding = use_geocoding and GEOPY_AVAILABLE
        self.geolocator = None
        self.geocoding_cache = {}
        self.cache_file = cache_file
        
        # Load existing cache if available
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.geocoding_cache = json.load(f)
                logger.info(f"Loaded {len(self.geocoding_cache)} cached geocoding results")
            except Exception as e:
                logger.warning(f"Could not load cache file: {e}")
        
        if self.use_geocoding:
            self.geolocator = Nominatim(user_agent="comprehensive_earthquake_country_detector_v1.0")
            logger.info("Initialized with geocoding support")
        else:
            logger.info("Initialized without geocoding - using geographical rules only")
    
    def standardize_country_name(self, country_name):
        """
        Standardize country names using pycountry if available.
        """
        if not PYCOUNTRY_AVAILABLE or not country_name:
            return country_name
        
        try:
            # Try to find the country
            country_obj = pycountry.countries.lookup(country_name)
            return country_obj.name
        except LookupError:
            # If not found, return original name
            return country_name
    
    def get_country_from_coordinates(self, lat, lon):
        """
        Main method to get country from coordinates.
        Uses a hybrid approach: fast geographical rules first, geocoding for uncertain cases.
        """
        if pd.isna(lat) or pd.isna(lon):
            return 'Unknown'
        
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return 'Unknown'
        
        # First try high-confidence geographical rules
        country = self.get_high_confidence_country(lat, lon)
        if country != 'Uncertain':
            return country
        
        # For uncertain cases, try geocoding if available
        if self.use_geocoding:
            geocoded_country = self.get_country_with_geocoding(lat, lon)
            if geocoded_country:
                return self.standardize_country_name(geocoded_country)
        
        # Fallback to detailed geographical analysis
        return self.get_detailed_geographical_country(lat, lon)
    
    def get_high_confidence_country(self, lat, lon):
        """
        Get country using high-confidence geographical boundaries.
        Returns 'Uncertain' if the location is ambiguous.
        """
        
        # Very specific and high-confidence country boundaries
        
        # United States (clear boundaries)
        if ((25 <= lat <= 49 and -125 <= lon <= -66) or  # Continental US
            (55 <= lat <= 72 and -168 <= lon <= -141) or  # Alaska
            (18 <= lat <= 23 and -162 <= lon <= -154)):   # Hawaii
            return 'United States'
        
        # Canada (clear boundaries, excluding border areas)
        if 50 <= lat <= 84 and -141 <= lon <= -52:
            return 'Canada'
        
        # Russia (large, well-defined territory)
        if 50 <= lat <= 82 and 30 <= lon <= 180:
            return 'Russia'
        if 50 <= lat <= 82 and -180 <= lon <= -169:  # Far eastern Russia
            return 'Russia'
        
        # China (clear core territory)
        if 20 <= lat <= 50 and 80 <= lon <= 130:
            return 'China'
        
        # Australia (isolated continent)
        if -44 <= lat <= -10 and 112 <= lon <= 154:
            return 'Australia'
        
        # Japan (island nation, clear boundaries)
        if 24 <= lat <= 46 and 129 <= lon <= 146:
            return 'Japan'
        
        # Indonesia (archipelago, core areas)
        if -8 <= lat <= 6 and 95 <= lon <= 141:
            return 'Indonesia'
        
        # Brazil (large, clear territory)
        if -34 <= lat <= 6 and -75 <= lon <= -34:
            return 'Brazil'
        
        # Major ocean areas (high confidence)
        if self.is_definitely_ocean(lat, lon):
            return self.get_ocean_name(lat, lon)
        
        # If not in high-confidence areas, mark as uncertain for further analysis
        return 'Uncertain'
    
    def is_definitely_ocean(self, lat, lon):
        """
        Check if coordinates are definitely in ocean (not near coastlines).
        """
        # Central Pacific
        if -40 <= lat <= 40 and 140 <= lon <= -120:
            return True
        
        # Central Atlantic
        if -40 <= lat <= 40 and -50 <= lon <= -10:
            return True
        
        # Central Indian Ocean
        if -40 <= lat <= 20 and 60 <= lon <= 100:
            return True
        
        # Southern Ocean
        if lat <= -50:
            return True
        
        # Arctic Ocean
        if lat >= 75:
            return True
        
        return False
    
    def get_ocean_name(self, lat, lon):
        """
        Get specific ocean name.
        """
        if lat <= -50:
            return 'Southern Ocean'
        elif lat >= 75:
            return 'Arctic Ocean'
        elif 60 <= lon <= 100 and lat <= 20:
            return 'Indian Ocean'
        elif -50 <= lon <= -10:
            if lat >= 0:
                return 'North Atlantic Ocean'
            else:
                return 'South Atlantic Ocean'
        elif (140 <= lon <= 180) or (-180 <= lon <= -120):
            if lat >= 0:
                return 'North Pacific Ocean'
            else:
                return 'South Pacific Ocean'
        else:
            return 'Ocean'
    
    def get_country_with_geocoding(self, lat, lon, max_retries=2):
        """
        Get country using online geocoding service with caching.
        """
        cache_key = f"{lat:.2f},{lon:.2f}"  # Round to reduce cache size
        
        if cache_key in self.geocoding_cache:
            return self.geocoding_cache[cache_key]
        
        for attempt in range(max_retries):
            try:
                time.sleep(0.3)  # Be respectful to the service
                
                location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True, timeout=15)
                
                if location and location.raw.get('address'):
                    address = location.raw['address']
                    country = (address.get('country') or 
                              address.get('country_name') or 
                              address.get('country_code'))
                    
                    if country:
                        self.geocoding_cache[cache_key] = country
                        self.save_cache()  # Save cache periodically
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
    
    def save_cache(self):
        """
        Save geocoding cache to file.
        """
        if self.cache_file and len(self.geocoding_cache) % 10 == 0:  # Save every 10 entries
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.geocoding_cache, f)
            except Exception as e:
                logger.warning(f"Could not save cache: {e}")
    
    def get_detailed_geographical_country(self, lat, lon):
        """
        Detailed geographical analysis for remaining cases.
        """
        
        # Specific countries with more detailed boundaries
        
        # Mexico
        if 14 <= lat <= 33 and -118 <= lon <= -86:
            return 'Mexico'
        
        # Philippines
        if 5 <= lat <= 21 and 116 <= lon <= 127:
            return 'Philippines'
        
        # Chile
        if -56 <= lat <= -17 and -76 <= lon <= -66:
            return 'Chile'
        
        # Peru
        if -19 <= lat <= 0 and -82 <= lon <= -68:
            return 'Peru'
        
        # Argentina
        if -55 <= lat <= -21 and -74 <= lon <= -53:
            return 'Argentina'
        
        # Turkey
        if 36 <= lat <= 42 and 26 <= lon <= 45:
            return 'Turkey'
        
        # Iran
        if 25 <= lat <= 40 and 44 <= lon <= 64:
            return 'Iran'
        
        # India
        if 6 <= lat <= 38 and 68 <= lon <= 98:
            return 'India'
        
        # New Zealand
        if -47 <= lat <= -34 and 166 <= lon <= 179:
            return 'New Zealand'
        
        # Papua New Guinea
        if -12 <= lat <= -1 and 140 <= lon <= 160:
            return 'Papua New Guinea'
        
        # Italy
        if 36 <= lat <= 47 and 6 <= lon <= 19:
            return 'Italy'
        
        # Greece
        if 34 <= lat <= 42 and 19 <= lon <= 30:
            return 'Greece'
        
        # Regional classifications for remaining areas
        return self.get_regional_classification(lat, lon)
    
    def get_regional_classification(self, lat, lon):
        """
        Regional classification for areas not covered by specific countries.
        """
        
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
        
        # Europe regions
        if 35 <= lat <= 75 and -15 <= lon <= 45:
            if lat >= 55:
                return 'Northern Europe'
            elif 45 <= lat <= 55:
                return 'Central Europe'
            else:
                return 'Southern Europe'
        
        # Africa regions
        if -40 <= lat <= 40 and -20 <= lon <= 55:
            if lat >= 20:
                return 'Northern Africa'
            elif lat >= 0:
                return 'Central Africa'
            else:
                return 'Southern Africa'
        
        # Antarctica
        if lat <= -60:
            return 'Antarctica'
        
        # Arctic
        if lat >= 70:
            return 'Arctic Region'
        
        # Ocean fallback
        if abs(lon) > 90 or abs(lat) > 60:
            return self.get_ocean_name(lat, lon)
        
        return 'Unknown Region'

def analyze_and_update_database(input_file, output_file=None, use_geocoding=False, 
                               sample_size=None, force_update=False):
    """
    Comprehensive function to analyze and update the earthquake database.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        use_geocoding (bool): Whether to use online geocoding
        sample_size (int): Process only a sample of records
        force_update (bool): Force update even if country column exists
    """
    
    if output_file is None:
        if use_geocoding:
            output_file = input_file.replace('.csv', '_with_comprehensive_countries.csv')
        else:
            output_file = input_file.replace('.csv', '_with_countries_fast.csv')
    
    cache_file = output_file.replace('.csv', '_geocoding_cache.json') if use_geocoding else None
    
    logger.info(f"Reading earthquake data from: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Successfully loaded {len(df)} earthquake records")
    except Exception as e:
        logger.error(f"Failed to read {input_file}: {e}")
        return None
    
    # Database analysis
    logger.info("\n=== Database Analysis ===")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    
    if 'Magnitude' in df.columns:
        mag_stats = df['Magnitude'].describe()
        logger.info(f"Magnitude range: {mag_stats['min']:.1f} to {mag_stats['max']:.1f}")
        logger.info(f"Average magnitude: {mag_stats['mean']:.1f}")
    
    # Sample data if requested
    if sample_size and sample_size < len(df):
        logger.info(f"Processing sample of {sample_size} records")
        df = df.head(sample_size)
    
    # Initialize detector
    detector = ComprehensiveCountryDetector(use_geocoding=use_geocoding, cache_file=cache_file)
    
    # Determine which records to process
    if 'Country' in df.columns and not force_update:
        logger.info("Country column exists")
        missing_mask = df['Country'].isna() | (df['Country'] == 'Unknown') | (df['Country'] == 'Unknown Region')
        rows_to_process = df[missing_mask].index
        logger.info(f"Found {len(rows_to_process)} records with missing/unknown country information")
    else:
        logger.info("Adding new Country column" if 'Country' not in df.columns else "Force updating all country information")
        df['Country'] = 'Unknown'
        rows_to_process = df.index
    
    if len(rows_to_process) == 0:
        logger.info("No records need country information update")
        return df
    
    logger.info(f"Processing {len(rows_to_process)} records...")
    
    # Process records with progress tracking
    start_time = time.time()
    processed_count = 0
    
    try:
        for idx in tqdm(rows_to_process, desc="Adding country information"):
            lat = df.loc[idx, 'Latitude']
            lon = df.loc[idx, 'Longitude']
            
            country = detector.get_country_from_coordinates(lat, lon)
            df.loc[idx, 'Country'] = country
            
            processed_count += 1
            
            # Save progress for large geocoding jobs
            if use_geocoding and processed_count % 100 == 0:
                df.to_csv(output_file, index=False)
                elapsed = time.time() - start_time
                rate = processed_count / elapsed
                eta = (len(rows_to_process) - processed_count) / rate / 60  # minutes
                logger.info(f"Processed {processed_count}/{len(rows_to_process)} records. ETA: {eta:.1f} minutes")
                
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Saving current progress...")
    
    # Final save
    logger.info(f"Saving final results to: {output_file}")
    df.to_csv(output_file, index=False)
    
    # Final cache save
    if use_geocoding:
        detector.save_cache()
        logger.info(f"Saved {len(detector.geocoding_cache)} geocoding results to cache")
    
    # Results summary
    logger.info("\n=== Results Summary ===")
    country_counts = df['Country'].value_counts()
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Unique countries/regions: {len(country_counts)}")
    logger.info(f"Records processed: {processed_count}")
    
    if processed_count > 0:
        elapsed = time.time() - start_time
        logger.info(f"Processing time: {elapsed/60:.1f} minutes")
        logger.info(f"Average rate: {processed_count/elapsed:.1f} records/second")
    
    logger.info("\nTop 20 countries/regions by earthquake count:")
    print(country_counts.head(20))
    
    # Quality metrics
    unknown_count = df['Country'].isin(['Unknown', 'Unknown Region']).sum()
    quality_score = (len(df) - unknown_count) / len(df) * 100
    logger.info(f"\nData quality: {quality_score:.1f}% of records have identified countries/regions")
    
    if unknown_count > 0:
        logger.warning(f"Warning: {unknown_count} records still have unknown country/region")
    
    return df

def main():
    """
    Main function with command-line argument support.
    """
    parser = argparse.ArgumentParser(description='Add country information to earthquake database')
    parser.add_argument('--input', default='data/database.csv', help='Input CSV file path')
    parser.add_argument('--output', help='Output CSV file path (auto-generated if not specified)')
    parser.add_argument('--geocoding', action='store_true', help='Enable online geocoding (slower but more accurate)')
    parser.add_argument('--sample', type=int, help='Process only a sample of records')
    parser.add_argument('--force', action='store_true', help='Force update all records even if country column exists')
    
    args = parser.parse_args()
    
    # Set up file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, args.input)
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.info(f"Please ensure the database.csv file exists at: {input_file}")
        return
    
    output_file = args.output
    if output_file:
        output_file = os.path.join(script_dir, output_file)
    
    logger.info("=== Comprehensive Earthquake Database Country Enrichment ===")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Geocoding enabled: {args.geocoding}")
    
    if args.geocoding and not GEOPY_AVAILABLE:
        logger.warning("Geocoding requested but geopy not available. Install with: pip install geopy")
        logger.info("Continuing with geographical rules only...")
        args.geocoding = False
    
    # Process the database
    result_df = analyze_and_update_database(
        input_file=input_file,
        output_file=output_file,
        use_geocoding=args.geocoding,
        sample_size=args.sample,
        force_update=args.force
    )
    
    if result_df is not None:
        logger.info("✅ Process completed successfully!")
        logger.info(f"Updated database saved with country information")
    else:
        logger.error("❌ Process failed!")

if __name__ == "__main__":
    # If run without arguments, use default settings
    import sys
    if len(sys.argv) == 1:
        # Default run without geocoding for speed
        sys.argv.extend(['--input', 'data/database.csv'])
    
    main()
