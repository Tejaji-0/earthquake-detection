#!/usr/bin/env python3
"""
Test script for ObsPy-based seismic data fetcher
"""

import sys
import os
sys.path.append('.')

from backup.fetch_seismic_data import SeismicDataFetcher
from datetime import datetime, timedelta

def test_waveform_fetching():
    """Test the waveform fetching functionality"""
    
    print("=== Testing ObsPy Seismic Data Fetcher ===\n")
    
    # Initialize fetcher
    fetcher = SeismicDataFetcher()
    
    if not fetcher.clients:
        print("No FDSN clients available. Please check ObsPy installation.")
        return
    
    # Test location: San Francisco (known to have good station coverage)
    test_lat, test_lon = 37.7749, -122.4194
    location_name = "San Francisco, CA"
    
    print(f"Testing location: {location_name} ({test_lat}, {test_lon})")
    print("-" * 60)
    
    # Find stations
    print("Finding nearest stations...")
    stations = fetcher.get_nearest_stations(test_lat, test_lon, max_radius_km=200, max_stations=3)
    
    if not stations:
        print("No stations found!")
        return
    
    print(f"Found {len(stations)} stations:")
    for i, station in enumerate(stations, 1):
        print(f"  {i}. {station['network']}.{station['station']} - {station['distance_km']:.1f} km")
        print(f"      Location: ({station['latitude']:.3f}, {station['longitude']:.3f})")
        print(f"      Client: {station.get('client', 'Unknown')}")
        print(f"      Site: {station.get('site_name', 'Unknown')}")
    
    print()
    
    # Test waveform fetching for the closest station
    if stations:
        station = stations[0]
        network = station['network']
        station_code = station['station']
        
        print(f"Testing waveform fetching for {network}.{station_code}...")
        
        # Use a recent time period (last week)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)  # 1 day of data
        
        print(f"Time period: {start_time} to {end_time}")
        
        waveforms, client_name = fetcher.get_seismic_waveforms(
            network, station_code, start_time, end_time
        )
        
        if waveforms:
            print(f"SUCCESS! Retrieved {len(waveforms)} traces from {client_name}")
            
            # Show waveform details
            summary = fetcher.create_waveform_summary(waveforms)
            print(f"Channels: {summary['channels']}")
            print(f"Sampling rates: {summary['unique_sampling_rates']} Hz")
            print(f"Total duration: {sum(t['duration_hours'] for t in summary['traces']):.2f} hours")
            
            # Try to save the data
            test_file = "test_waveforms.mseed"
            if fetcher.save_waveform_data(waveforms, test_file):
                print(f"Saved waveform data to {test_file}")
                
                # Check file size
                file_size = os.path.getsize(test_file) / (1024 * 1024)  # MB
                print(f"File size: {file_size:.2f} MB")
                
                # Clean up test file
                os.remove(test_file)
                print("Test file cleaned up")
            else:
                print("Failed to save waveform data")
        else:
            print("No waveform data retrieved")
            print("This might be due to:")
            print("  - No data available for this time period")
            print("  - Network/station not active")
            print("  - Data access restrictions")
            print("  - Server issues")

if __name__ == "__main__":
    try:
        test_waveform_fetching()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
