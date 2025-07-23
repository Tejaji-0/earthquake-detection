#!/usr/bin/env python3
"""
Simple seismic data fetcher focusing on proven global stations
"""

import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNException
import warnings
warnings.filterwarnings('ignore')

class SimpleSeismicFetcher:
    def __init__(self, data_dir='seismic_station_data'):
        self.data_dir = data_dir
        
        # Initialize only IRIS client (most reliable)
        try:
            self.client = Client('IRIS')
            print("✓ IRIS client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize IRIS client: {e}")
            self.client = None
        
        # Create main data directory
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_global_stations(self, latitude, longitude, max_radius_km=1000):
        """
        Get reliable global seismic stations
        """
        # Well-known, reliable global stations
        global_stations = [
            # Global Seismographic Network (GSN) - most reliable
            {'network': 'IU', 'station': 'ANMO', 'latitude': 34.9459, 'longitude': -106.4572, 'name': 'Albuquerque, NM'},
            {'network': 'IU', 'station': 'HRV', 'latitude': 42.5064, 'longitude': -71.5583, 'name': 'Harvard, MA'},
            {'network': 'IU', 'station': 'COLA', 'latitude': 64.8738, 'longitude': -147.8616, 'name': 'College, AK'},
            {'network': 'IU', 'station': 'CCM', 'latitude': 38.0557, 'longitude': -91.2446, 'name': 'Cathedral Cave, MO'},
            {'network': 'IU', 'station': 'FUNA', 'latitude': -8.5259, 'longitude': 179.1966, 'name': 'Funafuti, Tuvalu'},
            {'network': 'IU', 'station': 'GUMO', 'latitude': 13.5893, 'longitude': 144.8684, 'name': 'Guam, Mariana Is'},
            {'network': 'IU', 'station': 'MAJO', 'latitude': 36.5457, 'longitude': 138.2041, 'name': 'Matsushiro, Japan'},
            {'network': 'IU', 'station': 'PAB', 'latitude': 39.5446, 'longitude': 4.3499, 'name': 'San Pablo, Spain'},
            {'network': 'IU', 'station': 'PMSA', 'latitude': -64.7744, 'longitude': -64.0489, 'name': 'Palmer Station, Antarctica'},
            {'network': 'IU', 'station': 'QSPA', 'latitude': -89.9289, 'longitude': 144.4382, 'name': 'South Pole, Antarctica'},
            {'network': 'IU', 'station': 'SSPA', 'latitude': -40.3084, 'longitude': -70.8601, 'name': 'San Martin, Argentina'},
            {'network': 'IU', 'station': 'TATO', 'latitude': 24.9735, 'longitude': 121.4971, 'name': 'Taipei, Taiwan'},
            {'network': 'IU', 'station': 'KONO', 'latitude': 59.6491, 'longitude': 9.5982, 'name': 'Kongsberg, Norway'},
            {'network': 'IU', 'station': 'KEV', 'latitude': 69.7565, 'longitude': 27.0035, 'name': 'Kevo, Finland'},
            {'network': 'IU', 'station': 'KIEV', 'latitude': 50.7012, 'longitude': 29.2242, 'name': 'Kiev, Ukraine'},
            {'network': 'IU', 'station': 'MAKZ', 'latitude': 46.8080, 'longitude': 82.1283, 'name': 'Makanchi, Kazakhstan'},
            {'network': 'IU', 'station': 'TEIG', 'latitude': 20.2263, 'longitude': 92.7936, 'name': 'Teigaga, Myanmar'},
            {'network': 'IU', 'station': 'ULN', 'latitude': 47.8651, 'longitude': 107.0532, 'name': 'Ulaanbaatar, Mongolia'},
            
            # European stations
            {'network': 'GE', 'station': 'SNAA', 'latitude': 67.0180, 'longitude': -2.0199, 'name': 'Snartemo, Norway'},
            {'network': 'GE', 'station': 'WLF', 'latitude': 49.6555, 'longitude': 6.1508, 'name': 'Walferdange, Luxembourg'},
            {'network': 'GE', 'station': 'SUMG', 'latitude': -0.5527, 'longitude': 100.2381, 'name': 'Sumatra, Indonesia'},
            {'network': 'GE', 'station': 'APE', 'latitude': 40.8204, 'longitude': 14.4297, 'name': 'Ape, Italy'},
            
            # Additional reliable stations
            {'network': 'US', 'station': 'WMOK', 'latitude': 34.7367, 'longitude': -98.7707, 'name': 'Wichita Mountains, OK'},
            {'network': 'CI', 'station': 'PAS', 'latitude': 34.1484, 'longitude': -118.1717, 'name': 'Pasadena, CA'},
            {'network': 'BK', 'station': 'BRK', 'latitude': 37.8735, 'longitude': -122.2609, 'name': 'Berkeley, CA'},
            
            # Middle East and Turkey region
            {'network': 'TU', 'station': 'ISK', 'latitude': 41.0618, 'longitude': 29.0608, 'name': 'Istanbul, Turkey'},
            {'network': 'KO', 'station': 'KONS', 'latitude': 39.8467, 'longitude': 32.8627, 'name': 'Ankara, Turkey'},
            {'network': 'HL', 'station': 'JER', 'latitude': 31.7730, 'longitude': 35.2045, 'name': 'Jerusalem, Israel'},
            {'network': 'II', 'station': 'ANTO', 'latitude': 39.8683, 'longitude': 32.7934, 'name': 'Ankara, Turkey'},
            {'network': 'II', 'station': 'NIL', 'latitude': 33.6506, 'longitude': 73.2686, 'name': 'Nilore, Pakistan'},
            
            # Australian and Pacific
            {'network': 'AU', 'station': 'ARMA', 'latitude': -30.6267, 'longitude': 151.9501, 'name': 'Armidale, Australia'},
            {'network': 'AU', 'station': 'EIDS', 'latitude': -26.3912, 'longitude': 116.7975, 'name': 'Emu Heights, Australia'},
        ]
        
        # Calculate distances and filter
        stations = []
        for station in global_stations:
            distance = self.calculate_distance(
                latitude, longitude,
                station['latitude'], station['longitude']
            )
            
            if distance <= max_radius_km:
                station['distance_km'] = distance
                stations.append(station)
        
        # Sort by distance
        stations.sort(key=lambda x: x['distance_km'])
        return stations
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance using Haversine formula"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        return c * r
    
    def get_waveforms(self, network, station, start_time, end_time):
        """
        Get seismic waveforms for a station
        """
        if not self.client:
            return None, "No client available"
        
        # Convert to UTCDateTime
        starttime = UTCDateTime(start_time)
        endtime = UTCDateTime(end_time)
        
        # Try different channel priorities
        channel_priorities = [
            ['BH*'],  # Broadband high-gain
            ['HH*'],  # High broadband  
            ['LH*'],  # Long period
            ['BH1', 'BH2', 'BHZ'],  # Individual components
            ['HH1', 'HH2', 'HHZ'],
        ]
        
        for channels in channel_priorities:
            for channel in channels:
                try:
                    print(f"        Trying {network}.{station}.{channel}...")
                    
                    waveforms = self.client.get_waveforms(
                        network=network,
                        station=station,
                        location="*",
                        channel=channel,
                        starttime=starttime,
                        endtime=endtime
                    )
                    
                    if waveforms and len(waveforms) > 0:
                        print(f"        ✓ Got {len(waveforms)} traces")
                        return waveforms, "IRIS"
                        
                except FDSNException as e:
                    if "No data available" in str(e):
                        continue
                    else:
                        print(f"        FDSN error: {e}")
                except Exception as e:
                    print(f"        Error: {e}")
                
                time.sleep(0.3)  # Small delay
        
        return None, "No data found"
    
    def save_waveforms(self, waveforms, filepath):
        """Save waveforms to file"""
        try:
            waveforms.write(filepath, format='MSEED')
            return True
        except Exception as e:
            print(f"Error saving waveforms: {e}")
            return False
    
    def process_single_earthquake(self, title, magnitude, event_time, latitude, longitude, location):
        """
        Process a single earthquake and fetch seismic data
        """
        print(f"\n{'='*60}")
        print(f"Processing: {title}")
        print(f"Location: {location}")
        print(f"Time: {event_time}")
        print(f"Magnitude: {magnitude}")
        print(f"{'='*60}")
        
        # Create event directory
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:80]
        
        event_dir = os.path.join(
            self.data_dir, 
            f"{event_time.strftime('%Y%m%d_%H%M')}_M{magnitude}_{safe_title}"
        )
        
        if os.path.exists(event_dir):
            print(f"Directory already exists: {event_dir}")
            return event_dir
        
        os.makedirs(event_dir, exist_ok=True)
        
        # Create before/after directories
        before_dir = os.path.join(event_dir, 'before_event')
        after_dir = os.path.join(event_dir, 'after_event')
        os.makedirs(before_dir, exist_ok=True)
        os.makedirs(after_dir, exist_ok=True)
        
        # Define time periods (30 days before and after)
        before_start = event_time - timedelta(days=30)
        before_end = event_time - timedelta(hours=1)
        after_start = event_time + timedelta(hours=1)
        after_end = event_time + timedelta(days=30)
        
        print(f"\nTime periods:")
        print(f"  Before: {before_start} to {before_end}")
        print(f"  After:  {after_start} to {after_end}")
        
        # Find nearest stations
        print(f"\nFinding nearest stations...")
        stations = self.get_global_stations(latitude, longitude, max_radius_km=2000)
        
        if not stations:
            print("No stations found within 2000 km!")
            return None
        
        print(f"Found {len(stations)} stations within range:")
        for i, station in enumerate(stations[:5], 1):  # Show top 5
            print(f"  {i}. {station['network']}.{station['station']} - {station['name']} ({station['distance_km']:.0f} km)")
        
        # Process top 3 stations
        station_results = []
        successful_stations = 0
        
        for i, station in enumerate(stations[:3], 1):
            network = station['network']
            station_code = station['station']
            distance = station['distance_km']
            name = station['name']
            
            print(f"\n--- Station {i}: {network}.{station_code} ({name}) ---")
            print(f"Distance: {distance:.1f} km")
            
            station_info = {
                'network': network,
                'station': station_code,
                'name': name,
                'latitude': station['latitude'],
                'longitude': station['longitude'],
                'distance_km': distance,
                'data_retrieved': {'before': False, 'after': False}
            }
            
            # Fetch before-event data
            print(f"  Fetching before-event data...")
            before_waveforms, before_msg = self.get_waveforms(
                network, station_code, before_start, before_end
            )
            
            if before_waveforms:
                before_file = os.path.join(before_dir, f'{network}_{station_code}_before.mseed')
                if self.save_waveforms(before_waveforms, before_file):
                    station_info['data_retrieved']['before'] = True
                    file_size = os.path.getsize(before_file) / (1024*1024)
                    print(f"    ✓ Saved before-event data ({file_size:.1f} MB)")
                    successful_stations += 0.5
            else:
                print(f"    ✗ No before-event data: {before_msg}")
            
            time.sleep(2)  # Respectful delay
            
            # Fetch after-event data
            print(f"  Fetching after-event data...")
            after_waveforms, after_msg = self.get_waveforms(
                network, station_code, after_start, after_end
            )
            
            if after_waveforms:
                after_file = os.path.join(after_dir, f'{network}_{station_code}_after.mseed')
                if self.save_waveforms(after_waveforms, after_file):
                    station_info['data_retrieved']['after'] = True
                    file_size = os.path.getsize(after_file) / (1024*1024)
                    print(f"    ✓ Saved after-event data ({file_size:.1f} MB)")
                    successful_stations += 0.5
            else:
                print(f"    ✗ No after-event data: {after_msg}")
            
            station_results.append(station_info)
            time.sleep(3)  # Longer delay between stations
        
        # Save metadata
        metadata = {
            'event_info': {
                'title': title,
                'magnitude': magnitude,
                'datetime': event_time.isoformat(),
                'latitude': latitude,
                'longitude': longitude,
                'location': location
            },
            'stations': station_results,
            'data_periods': {
                'before': {
                    'start': before_start.isoformat(),
                    'end': before_end.isoformat(),
                    'duration_days': 30
                },
                'after': {
                    'start': after_start.isoformat(),
                    'end': after_end.isoformat(),
                    'duration_days': 30
                }
            },
            'processing_time': datetime.now().isoformat(),
            'successful_retrievals': successful_stations,
            'status': 'completed'
        }
        
        with open(os.path.join(event_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Processing complete!")
        print(f"  Successful data retrievals: {successful_stations}/6")
        print(f"  Data saved to: {event_dir}")
        
        return event_dir

def main():
    """Test with a single recent earthquake"""
    fetcher = SimpleSeismicFetcher()
    
    if not fetcher.client:
        print("Cannot proceed without IRIS client")
        return
    
    # Test with a recent significant earthquake
    # Using the 2023 Turkey earthquake as an example
    test_earthquake = {
        'title': 'M 7.8 - Central Turkey',
        'magnitude': 7.8,
        'datetime': datetime(2023, 2, 6, 1, 17, 35),
        'latitude': 37.166,
        'longitude': 37.042,
        'location': 'Central Turkey'
    }
    
    print("=== Simple Seismic Data Fetcher Test ===")
    print(f"Testing with: {test_earthquake['title']}")
    
    result = fetcher.process_single_earthquake(
        test_earthquake['title'],
        test_earthquake['magnitude'],
        test_earthquake['datetime'],
        test_earthquake['latitude'],
        test_earthquake['longitude'],
        test_earthquake['location']
    )
    
    if result:
        print(f"\n🎉 Test completed successfully!")
        print(f"Check the results in: {result}")
    else:
        print(f"\n❌ Test failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
