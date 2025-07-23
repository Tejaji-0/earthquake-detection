#!/usr/bin/env python3
"""
Test script for seismic station finder
"""

import sys
import os
sys.path.append('.')

from backup.fetch_seismic_data import SeismicDataFetcher

def test_station_finder():
    """Test the station finding functionality"""
    
    fetcher = SeismicDataFetcher()
    
    # Test locations (latitude, longitude, location name)
    test_locations = [
        (34.0522, -118.2437, "Los Angeles, CA"),
        (37.7749, -122.4194, "San Francisco, CA"),
        (40.7128, -74.0060, "New York, NY"),
        (35.6762, 139.6503, "Tokyo, Japan"),
        (-33.8688, 151.2093, "Sydney, Australia")
    ]
    
    print("=== Testing Station Finder ===\n")
    
    for lat, lon, location in test_locations:
        print(f"Testing location: {location} ({lat}, {lon})")
        print("-" * 50)
        
        stations = fetcher.get_nearest_stations(lat, lon, max_radius_km=1000, max_stations=5)
        
        if stations:
            print(f"Found {len(stations)} stations:")
            for i, station in enumerate(stations, 1):
                print(f"  {i}. {station['network']}.{station['station']} - {station['distance_km']:.1f} km")
                print(f"      Location: ({station['latitude']:.3f}, {station['longitude']:.3f})")
        else:
            print("No stations found!")
        
        print("\n")

if __name__ == "__main__":
    test_station_finder()
