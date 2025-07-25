#!/usr/bin/env python3
"""
Test script for the earthquake seismic data fetcher
"""

import sys
import os
from datetime import datetime

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_earthquake_seismic_data import EarthquakeSeismicFetcher

def test_fetcher_initialization():
    """Test that the fetcher initializes correctly"""
    print("=== Testing Fetcher Initialization ===")
    
    fetcher = EarthquakeSeismicFetcher()
    
    if fetcher.client is None:
        print("✗ Failed to initialize IRIS client")
        return False
    
    if len(fetcher.earthquakes) == 0:
        print("✗ No earthquake data loaded")
        return False
    
    print(f"✓ Successfully loaded {len(fetcher.earthquakes)} significant earthquakes")
    print(f"✓ IRIS client initialized successfully")
    
    return True

def test_database_loading():
    """Test database loading and filtering"""
    print("\n=== Testing Database Loading ===")
    
    fetcher = EarthquakeSeismicFetcher()
    
    if len(fetcher.earthquakes) == 0:
        print("✗ No earthquakes loaded")
        return False
    
    # Check that we have the expected columns
    required_columns = ['Date', 'Time', 'Magnitude', 'Latitude', 'Longitude', 'ID', 'datetime']
    missing_columns = [col for col in required_columns if col not in fetcher.earthquakes.columns]
    
    if missing_columns:
        print(f"✗ Missing required columns: {missing_columns}")
        return False
    
    # Check date range
    min_date = fetcher.earthquakes['datetime'].min()
    max_date = fetcher.earthquakes['datetime'].max()
    print(f"✓ Date range: {min_date} to {max_date}")
    
    # Check magnitude range
    min_mag = fetcher.earthquakes['Magnitude'].min()
    max_mag = fetcher.earthquakes['Magnitude'].max()
    print(f"✓ Magnitude range: {min_mag} to {max_mag}")
    
    # Show some sample data
    print("\n✓ Sample earthquakes:")
    sample = fetcher.earthquakes.head(3)[['datetime', 'Magnitude', 'ID']]
    for idx, row in sample.iterrows():
        print(f"  - {row['datetime']}: M{row['Magnitude']} (ID: {row['ID']})")
    
    return True

def test_station_list():
    """Test that global stations are available"""
    print("\n=== Testing Station List ===")
    
    fetcher = EarthquakeSeismicFetcher()
    stations = fetcher.get_global_stations()
    
    if len(stations) == 0:
        print("✗ No global stations available")
        return False
    
    print(f"✓ {len(stations)} global stations available:")
    for station in stations[:5]:  # Show first 5
        print(f"  - {station['network']}.{station['station']}: {station['name']}")
    
    return True

def test_earthquake_selection():
    """Test earthquake selection for data fetching"""
    print("\n=== Testing Earthquake Selection ===")
    
    fetcher = EarthquakeSeismicFetcher()
    
    # Get major earthquakes
    major_earthquakes = fetcher.earthquakes[
        fetcher.earthquakes['Magnitude'] >= 8.0
    ].sort_values('Magnitude', ascending=False).head(5)
    
    if len(major_earthquakes) == 0:
        print("✗ No major earthquakes (M >= 8.0) found")
        return False
    
    print(f"✓ Found {len(major_earthquakes)} major earthquakes (M >= 8.0):")
    for idx, eq in major_earthquakes.iterrows():
        print(f"  - M{eq['Magnitude']}: {eq['datetime']} (ID: {eq['ID']})")
    
    return True

def main():
    """Run all tests"""
    print("Testing Earthquake Seismic Data Fetcher")
    print("=" * 50)
    
    tests = [
        test_fetcher_initialization,
        test_database_loading,
        test_station_list,
        test_earthquake_selection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ PASSED\n")
            else:
                failed += 1
                print("✗ FAILED\n")
        except Exception as e:
            print(f"✗ ERROR: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed! The seismic data fetcher is ready to use.")
        print("\nTo fetch seismic data for earthquakes, run:")
        print("  python fetch_earthquake_seismic_data.py")
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())