#!/usr/bin/env python3
"""
Seismic Wave Data Fetcher for Earthquake Detection
This script fetches seismic wave data one week before and after earthquakes using APIs.
"""

import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import time
import warnings
warnings.filterwarnings('ignore')

class SeismicWaveFetcher:
    def __init__(self, output_dir='seismic_waves_data'):
        """Initialize the seismic wave fetcher."""
        self.output_dir = output_dir
        self.ensure_output_directory()
        
        # Initialize seismic data clients
        self.clients = {}
        self.available_networks = [
            'IRIS',  # Incorporated Research Institutions for Seismology
            'USGS',  # United States Geological Survey
            'ORFEUS', # Observatories and Research Facilities for European Seismology
            'GFZ',   # GeoForschungsZentrum Potsdam
        ]
        
        self.initialize_clients()
        
        # Define time windows
        self.time_window_days = 7  # One week before and after
        
    def ensure_output_directory(self):
        """Create output directory structure."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Create subdirectories for different types of data
        subdirs = ['before_events', 'after_events', 'station_metadata', 'logs']
        for subdir in subdirs:
            subdir_path = os.path.join(self.output_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
    
    def initialize_clients(self):
        """Initialize FDSN clients for different seismic networks."""
        for network in self.available_networks:
            try:
                client = Client(network)
                # Test if client is working
                client.get_stations(level='network', maxlatitude=1, maxlongitude=1, 
                                  minlatitude=0, minlongitude=0, starttime=UTCDateTime()-86400)
                self.clients[network] = client
                print(f"✓ Initialized {network} client")
            except Exception as e:
                print(f"✗ Failed to initialize {network} client: {e}")
    
    def get_nearby_stations(self, latitude, longitude, radius_km=500, max_stations=10):
        """Find seismic stations near the earthquake location."""
        stations = []
        
        for network_name, client in self.clients.items():
            try:
                # Convert radius to degrees (rough approximation)
                radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km
                
                # Get stations within radius
                inventory = client.get_stations(
                    latitude=latitude,
                    longitude=longitude,
                    maxradius=radius_deg,
                    level='station',
                    starttime=UTCDateTime() - 365*24*3600,  # Last year
                    endtime=UTCDateTime()
                )
                
                for network in inventory:
                    for station in network:
                        station_info = {
                            'network': network.code,
                            'station': station.code,
                            'latitude': station.latitude,
                            'longitude': station.longitude,
                            'elevation': station.elevation,
                            'distance_km': self.calculate_distance(
                                latitude, longitude,
                                station.latitude, station.longitude
                            ),
                            'client': network_name
                        }
                        stations.append(station_info)
                
            except Exception as e:
                print(f"Error getting stations from {network_name}: {e}")
        
        # Sort by distance and return closest stations
        stations.sort(key=lambda x: x['distance_km'])
        return stations[:max_stations]
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points on Earth using Haversine formula."""
        # Convert latitude and longitude to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    def fetch_seismic_data(self, station_info, start_time, end_time, event_id):
        """Fetch seismic waveform data for a specific station and time period."""
        network = station_info['network']
        station = station_info['station']
        client_name = station_info['client']
        
        if client_name not in self.clients:
            return None
        
        client = self.clients[client_name]
        
        try:
            # Request waveform data
            # Common channels: BHZ (vertical), BHN (north), BHE (east)
            channels = ['BHZ', 'BHN', 'BHE', 'HHZ', 'HHN', 'HHE']
            
            for channel in channels:
                try:
                    stream = client.get_waveforms(
                        network=network,
                        station=station,
                        location='*',
                        channel=channel,
                        starttime=UTCDateTime(start_time),
                        endtime=UTCDateTime(end_time)
                    )
                    
                    if len(stream) > 0:
                        # Process and save the data
                        waveform_data = self.process_waveform_data(stream, station_info, event_id)
                        return waveform_data
                        
                except Exception as e:
                    print(f"Error fetching {channel} data from {network}.{station}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error fetching data from {network}.{station}: {e}")
            return None
    
    def process_waveform_data(self, stream, station_info, event_id):
        """Process seismic waveform data and extract features."""
        try:
            # Merge traces if multiple
            stream.merge(fill_value=0)
            
            waveform_data = {
                'event_id': event_id,
                'network': station_info['network'],
                'station': station_info['station'],
                'latitude': station_info['latitude'],
                'longitude': station_info['longitude'],
                'distance_km': station_info['distance_km'],
                'channels': [],
                'sampling_rate': None,
                'start_time': None,
                'end_time': None,
                'duration_seconds': None,
                'statistics': {}
            }
            
            for trace in stream:
                channel_data = {
                    'channel': trace.stats.channel,
                    'sampling_rate': trace.stats.sampling_rate,
                    'npts': trace.stats.npts,
                    'start_time': str(trace.stats.starttime),
                    'end_time': str(trace.stats.endtime),
                    'data_samples': len(trace.data),
                    'statistics': {
                        'max': float(np.max(trace.data)),
                        'min': float(np.min(trace.data)),
                        'mean': float(np.mean(trace.data)),
                        'std': float(np.std(trace.data)),
                        'rms': float(np.sqrt(np.mean(trace.data**2))),
                    }
                }
                
                # Calculate frequency domain features
                try:
                    from scipy import signal
                    freqs, psd = signal.welch(trace.data, trace.stats.sampling_rate)
                    dominant_freq = freqs[np.argmax(psd)]
                    channel_data['statistics']['dominant_frequency'] = float(dominant_freq)
                    channel_data['statistics']['frequency_content'] = {
                        'low_freq_energy': float(np.sum(psd[freqs < 1])),
                        'mid_freq_energy': float(np.sum(psd[(freqs >= 1) & (freqs < 10)])),
                        'high_freq_energy': float(np.sum(psd[freqs >= 10]))
                    }
                except ImportError:
                    print("scipy not available for frequency analysis")
                
                waveform_data['channels'].append(channel_data)
            
            # Set overall metadata
            if waveform_data['channels']:
                first_channel = waveform_data['channels'][0]
                waveform_data['sampling_rate'] = first_channel['sampling_rate']
                waveform_data['start_time'] = first_channel['start_time']
                waveform_data['end_time'] = first_channel['end_time']
                
                # Calculate duration
                start = UTCDateTime(first_channel['start_time'])
                end = UTCDateTime(first_channel['end_time'])
                waveform_data['duration_seconds'] = float(end - start)
                
                # Calculate overall statistics
                all_data = []
                for channel in waveform_data['channels']:
                    all_data.extend([
                        channel['statistics']['max'],
                        channel['statistics']['min'],
                        channel['statistics']['mean'],
                        channel['statistics']['std']
                    ])
                
                waveform_data['statistics'] = {
                    'overall_max': max([ch['statistics']['max'] for ch in waveform_data['channels']]),
                    'overall_min': min([ch['statistics']['min'] for ch in waveform_data['channels']]),
                    'overall_mean': np.mean([ch['statistics']['mean'] for ch in waveform_data['channels']]),
                    'overall_std': np.mean([ch['statistics']['std'] for ch in waveform_data['channels']]),
                    'num_channels': len(waveform_data['channels'])
                }
            
            return waveform_data
            
        except Exception as e:
            print(f"Error processing waveform data: {e}")
            return None
    
    def fetch_earthquake_seismic_data(self, earthquake_data):
        """Fetch seismic data for one week before and after an earthquake."""
        try:
            # Parse earthquake information
            if isinstance(earthquake_data, dict):
                event_id = earthquake_data.get('event_id', f"eq_{int(time.time())}")
                latitude = earthquake_data['latitude']
                longitude = earthquake_data['longitude']
                earthquake_time = pd.to_datetime(earthquake_data['date_time'])
                magnitude = earthquake_data['magnitude']
                location = earthquake_data.get('location', 'Unknown')
            else:
                # Assume it's a pandas Series
                event_id = getattr(earthquake_data, 'event_id', f"eq_{int(time.time())}")
                latitude = earthquake_data['latitude']
                longitude = earthquake_data['longitude']
                earthquake_time = pd.to_datetime(earthquake_data['date_time'])
                magnitude = earthquake_data['magnitude']
                location = getattr(earthquake_data, 'location', 'Unknown')
            
            print(f"\nFetching seismic data for Event {event_id}: M{magnitude} - {location}")
            print(f"Location: {latitude:.3f}, {longitude:.3f}")
            print(f"Time: {earthquake_time}")
            
            # Define time windows
            before_start = earthquake_time - timedelta(days=self.time_window_days)
            before_end = earthquake_time
            after_start = earthquake_time
            after_end = earthquake_time + timedelta(days=self.time_window_days)
            
            # Find nearby seismic stations
            print("Finding nearby seismic stations...")
            stations = self.get_nearby_stations(latitude, longitude)
            
            if not stations:
                print("No nearby seismic stations found")
                return None
            
            print(f"Found {len(stations)} nearby stations")
            
            # Create event directory
            event_dir = os.path.join(self.output_dir, f"event_{event_id}")
            if not os.path.exists(event_dir):
                os.makedirs(event_dir)
            
            # Save earthquake metadata
            earthquake_metadata = {
                'event_id': event_id,
                'earthquake_time': str(earthquake_time),
                'latitude': latitude,
                'longitude': longitude,
                'magnitude': magnitude,
                'location': location,
                'time_windows': {
                    'before': {'start': str(before_start), 'end': str(before_end)},
                    'after': {'start': str(after_start), 'end': str(after_end)}
                },
                'stations': stations,
                'data_fetched': {
                    'before': [],
                    'after': []
                }
            }
            
            # Fetch data for each station
            for i, station in enumerate(stations[:5]):  # Limit to 5 stations to avoid overload
                print(f"Fetching data from station {i+1}/{min(len(stations), 5)}: "
                      f"{station['network']}.{station['station']} "
                      f"({station['distance_km']:.1f} km)")
                
                try:
                    # Fetch before-event data
                    print("  Fetching before-event data...")
                    before_data = self.fetch_seismic_data(station, before_start, before_end, event_id)
                    if before_data:
                        before_file = os.path.join(event_dir, 
                                                 f"before_{station['network']}_{station['station']}.json")
                        with open(before_file, 'w') as f:
                            json.dump(before_data, f, indent=2)
                        earthquake_metadata['data_fetched']['before'].append(before_file)
                        print("    ✓ Before-event data saved")
                    else:
                        print("    ✗ No before-event data available")
                    
                    # Small delay to avoid overwhelming servers
                    time.sleep(1)
                    
                    # Fetch after-event data
                    print("  Fetching after-event data...")
                    after_data = self.fetch_seismic_data(station, after_start, after_end, event_id)
                    if after_data:
                        after_file = os.path.join(event_dir, 
                                                f"after_{station['network']}_{station['station']}.json")
                        with open(after_file, 'w') as f:
                            json.dump(after_data, f, indent=2)
                        earthquake_metadata['data_fetched']['after'].append(after_file)
                        print("    ✓ After-event data saved")
                    else:
                        print("    ✗ No after-event data available")
                    
                    # Small delay between stations
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    ✗ Error fetching data from station: {e}")
            
            # Save earthquake metadata
            metadata_file = os.path.join(event_dir, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(earthquake_metadata, f, indent=2, default=str)
            
            print(f"✓ Earthquake seismic data collection completed for Event {event_id}")
            print(f"  Data saved in: {event_dir}")
            
            return earthquake_metadata
            
        except Exception as e:
            print(f"Error fetching earthquake seismic data: {e}")
            return None
    
    def process_earthquake_batch(self, earthquake_csv_file, max_events=5):
        """Process a batch of earthquakes from CSV file."""
        print(f"=== Seismic Wave Data Batch Processing ===")
        print(f"Processing earthquakes from: {earthquake_csv_file}")
        print(f"Maximum events to process: {max_events}")
        
        try:
            # Load earthquake data
            if not os.path.exists(earthquake_csv_file):
                print(f"Error: CSV file not found: {earthquake_csv_file}")
                return
            
            df = pd.read_csv(earthquake_csv_file)
            print(f"Loaded {len(df)} earthquakes from CSV")
            
            # Convert date_time column
            if 'date_time' in df.columns:
                df['date_time'] = pd.to_datetime(df['date_time'], format='%d-%m-%Y %H:%M')
            
            # Sort by magnitude (process largest earthquakes first)
            df = df.sort_values('magnitude', ascending=False)
            
            # Process top earthquakes
            processed_events = []
            for i, (idx, earthquake) in enumerate(df.head(max_events).iterrows()):
                print(f"\n{'='*60}")
                print(f"Processing earthquake {i+1}/{max_events}")
                print(f"{'='*60}")
                
                # Fetch seismic data for this earthquake
                result = self.fetch_earthquake_seismic_data(earthquake)
                if result:
                    processed_events.append(result)
                    print(f"✓ Successfully processed event {result['event_id']}")
                else:
                    print(f"✗ Failed to process earthquake {idx}")
                
                # Progress update
                if i < max_events - 1:
                    print(f"\nWaiting before processing next earthquake...")
                    time.sleep(5)  # Wait between earthquakes
            
            # Save batch processing summary
            summary = {
                'batch_processing_time': str(datetime.now()),
                'source_file': earthquake_csv_file,
                'total_earthquakes_in_file': len(df),
                'processed_earthquakes': len(processed_events),
                'max_events_limit': max_events,
                'processed_events': processed_events
            }
            
            summary_file = os.path.join(self.output_dir, 
                                       f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            print(f"\n{'='*60}")
            print(f"BATCH PROCESSING COMPLETED")
            print(f"{'='*60}")
            print(f"Processed: {len(processed_events)}/{max_events} earthquakes")
            print(f"Summary saved: {summary_file}")
            print(f"Data directory: {os.path.abspath(self.output_dir)}")
            
            return processed_events
            
        except Exception as e:
            print(f"Error in batch processing: {e}")
            return []

def main():
    """Main function for seismic wave data fetching."""
    fetcher = SeismicWaveFetcher()
    
    print("=== Seismic Wave Data Fetcher ===")
    print("Choose an option:")
    print("1. Process earthquake batch from CSV")
    print("2. Process single earthquake")
    print("3. Test station connectivity")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            # Batch processing
            csv_file = input("Enter CSV file path (default: data/database.csv): ") or "data/database.csv"
            max_events = int(input("Maximum events to process (default: 5): ") or 5)
            
            if os.path.exists(csv_file):
                fetcher.process_earthquake_batch(csv_file, max_events)
            else:
                print(f"CSV file not found: {csv_file}")
        
        elif choice == '2':
            # Single earthquake
            print("Enter earthquake details:")
            latitude = float(input("Latitude: "))
            longitude = float(input("Longitude: "))
            magnitude = float(input("Magnitude: "))
            date_time = input("Date/time (YYYY-MM-DD HH:MM): ")
            location = input("Location: ")
            
            earthquake_data = {
                'event_id': f"manual_{int(time.time())}",
                'latitude': latitude,
                'longitude': longitude,
                'magnitude': magnitude,
                'date_time': date_time,
                'location': location
            }
            
            fetcher.fetch_earthquake_seismic_data(earthquake_data)
        
        elif choice == '3':
            # Test station connectivity
            print("Testing seismic data client connectivity...")
            for network_name, client in fetcher.clients.items():
                try:
                    # Test with a simple station query
                    inventory = client.get_stations(
                        maxlatitude=1, maxlongitude=1, 
                        minlatitude=0, minlongitude=0,
                        level='network',
                        starttime=UTCDateTime()-86400
                    )
                    print(f"✓ {network_name}: {len(inventory)} networks available")
                except Exception as e:
                    print(f"✗ {network_name}: {e}")
        
        else:
            print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()