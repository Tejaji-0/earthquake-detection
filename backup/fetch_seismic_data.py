#!/usr/bin/env python3
"""
Seismic Data Fetcher for Earthquake Events
This script fetches actual seismic waveform data from the nearest stations for all earthquakes
using ObsPy and FDSN web services.
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

class SeismicDataFetcher:
    def __init__(self, data_dir='seismic_station_data'):
        self.data_dir = data_dir
        self.clients = {}
        
        # Initialize FDSN clients for different data centers
        self.init_clients()
        
        # Create main data directory
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def init_clients(self):
        """Initialize FDSN clients for different seismic data centers"""
        client_urls = {
            'IRIS': 'IRIS',
            'USGS': 'USGS', 
            'SCEDC': 'SCEDC',  # Southern California
            'NCEDC': 'NCEDC',  # Northern California
            'GEONET': 'GEONET',  # New Zealand
            'BGR': 'BGR',      # Germany
            'INGV': 'INGV',    # Italy
            'EMSC': 'EMSC',    # Europe
            'KOERI': 'KOERI',  # Turkey
            'JMA': 'JMA'       # Japan
        }
        
        for name, url in client_urls.items():
            try:
                self.clients[name] = Client(url)
                print(f"Initialized {name} client")
            except Exception as e:
                print(f"Failed to initialize {name} client: {e}")
        
        if not self.clients:
            print("Warning: No FDSN clients could be initialized!")
        else:
            print(f"Successfully initialized {len(self.clients)} FDSN clients")
    
    def get_nearest_stations(self, latitude, longitude, max_radius_km=500, max_stations=5):
        """
        Find nearest seismic stations using ObsPy FDSN clients
        """
        all_stations = []
        
        # Try each client to get station inventory
        for client_name, client in self.clients.items():
            try:
                print(f"  Querying {client_name} for stations...")
                
                # Get station inventory
                inventory = client.get_stations(
                    latitude=latitude, 
                    longitude=longitude,
                    maxradius=max_radius_km / 111.32,  # Convert km to degrees
                    level="station",
                    starttime=UTCDateTime("2010-01-01"),
                    endtime=UTCDateTime("2024-01-01")
                )
                
                # Extract station information
                for network in inventory:
                    for station in network:
                        distance = self.calculate_distance(
                            latitude, longitude,
                            station.latitude, station.longitude
                        )
                        
                        all_stations.append({
                            'network': network.code,
                            'station': station.code,
                            'latitude': station.latitude,
                            'longitude': station.longitude,
                            'distance_km': distance,
                            'client': client_name,
                            'site_name': station.site.name if station.site else 'Unknown',
                            'elevation': station.elevation
                        })
                        
            except Exception as e:
                print(f"    Error querying {client_name}: {e}")
                continue
        
        # If no stations found from clients, use fallback
        if not all_stations:
            print("  No stations found from FDSN clients, using fallback stations...")
            all_stations = self.get_fallback_stations(latitude, longitude, max_radius_km)
        
        # Remove duplicates and sort by distance
        unique_stations = []
        seen = set()
        for station in all_stations:
            key = f"{station['network']}.{station['station']}"
            if key not in seen:
                seen.add(key)
                unique_stations.append(station)
        
        unique_stations.sort(key=lambda x: x['distance_km'])
        return unique_stations[:max_stations]
    
    def get_stations_iris_text(self, latitude, longitude, max_radius_km):
        """
        Get stations from IRIS using text format
        """
        try:
            url = f"{self.base_url_iris}/fdsnws/station/1/query"
            params = {
                'format': 'text',
                'level': 'station',
                'latitude': latitude,
                'longitude': longitude,
                'maxradius': max_radius_km / 111.32,  # Convert km to degrees
                'starttime': '1990-01-01',
                'endtime': '2024-01-01'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return self.parse_station_text(response.text, latitude, longitude)
            else:
                print(f"IRIS text station query failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting IRIS stations (text): {e}")
            return []
    
    def get_stations_usgs(self, latitude, longitude, max_radius_km):
        """
        Get stations from USGS earthquake catalog (alternative approach)
        """
        try:
            # Use a broader time range to find events with station data
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                'format': 'geojson',
                'latitude': latitude,
                'longitude': longitude,
                'maxradius': max_radius_km / 111.32,
                'starttime': '2020-01-01',
                'endtime': '2024-01-01',
                'minmagnitude': 5.0,
                'limit': 50
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Extract station information from event data
                return self.extract_stations_from_events(data, latitude, longitude)
            else:
                print(f"USGS station query failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting USGS stations: {e}")
            return []
    
    def get_fallback_stations(self, latitude, longitude, max_radius_km):
        """
        Use predefined major global seismic stations as fallback
        """
        # Major global seismic stations with known coordinates
        global_stations = [
            # Global Seismographic Network (GSN)
            {'network': 'IU', 'station': 'ANMO', 'latitude': 34.9459, 'longitude': -106.4572},  # Albuquerque
            {'network': 'IU', 'station': 'COLA', 'latitude': 64.8738, 'longitude': -147.8616}, # College, Alaska
            {'network': 'IU', 'station': 'HRV', 'latitude': 42.5064, 'longitude': -71.5583},   # Harvard
            {'network': 'IU', 'station': 'KONO', 'latitude': 59.6491, 'longitude': 9.5982},    # Norway
            {'network': 'IU', 'station': 'MAJO', 'latitude': 36.5457, 'longitude': 138.2041},  # Japan
            {'network': 'IU', 'station': 'RAO', 'latitude': 46.0407, 'longitude': 14.5148},    # Slovenia
            {'network': 'IU', 'station': 'TATO', 'latitude': 24.9735, 'longitude': 121.4971},  # Taiwan
            {'network': 'IU', 'station': 'ULN', 'latitude': 47.8651, 'longitude': 107.0532},   # Mongolia
            {'network': 'GT', 'station': 'PLCA', 'latitude': -31.6729, 'longitude': -63.8792}, # Argentina
            {'network': 'GT', 'station': 'DBIC', 'latitude': -7.9333, 'longitude': 115.2333},  # Indonesia
            
            # Regional networks
            {'network': 'US', 'station': 'ECSD', 'latitude': 44.0648, 'longitude': -121.4058}, # Oregon
            {'network': 'US', 'station': 'LKWY', 'latitude': 44.5664, 'longitude': -110.4016}, # Yellowstone
            {'network': 'CI', 'station': 'PAS', 'latitude': 34.1484, 'longitude': -118.1717},  # Pasadena
            {'network': 'BK', 'station': 'BRK', 'latitude': 37.8735, 'longitude': -122.2609},  # Berkeley
            {'network': 'HV', 'station': 'KIP', 'latitude': 21.4233, 'longitude': -158.0095},  # Hawaii
            
            # International stations
            {'network': 'GE', 'station': 'APE', 'latitude': 40.8204, 'longitude': 14.4297},    # Italy
            {'network': 'GE', 'station': 'SUMG', 'latitude': -0.5527, 'longitude': 100.2381},  # Sumatra
            {'network': 'AU', 'station': 'ARMA', 'latitude': -30.6267, 'longitude': 151.9501}, # Australia
            {'network': 'AU', 'station': 'EIDS', 'latitude': -26.3912, 'longitude': 116.7975}, # Australia
        ]
        
        stations = []
        for station in global_stations:
            distance = self.calculate_distance(
                latitude, longitude, 
                station['latitude'], station['longitude']
            )
            
            if distance <= max_radius_km:
                station['distance_km'] = distance
                station['client'] = 'IRIS'  # Default client
                station['site_name'] = 'Global Station'
                station['elevation'] = 0.0
                stations.append(station)
        
        return stations
    
    def parse_station_text(self, text_content, event_lat, event_lon):
        """
        Parse IRIS station text response
        """
        stations = []
        try:
            lines = text_content.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip() and not line.startswith('#'):
                    parts = line.split('|')
                    if len(parts) >= 5:
                        network = parts[0].strip()
                        station = parts[1].strip()
                        lat = float(parts[2].strip())
                        lon = float(parts[3].strip())
                        
                        distance = self.calculate_distance(event_lat, event_lon, lat, lon)
                        
                        stations.append({
                            'network': network,
                            'station': station,
                            'latitude': lat,
                            'longitude': lon,
                            'distance_km': distance
                        })
        except Exception as e:
            print(f"Error parsing station text: {e}")
        
        return stations
    
    def extract_stations_from_events(self, geojson_data, event_lat, event_lon):
        """
        Extract station information from USGS event data
        """
        stations = []
        try:
            for feature in geojson_data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]
                    distance = self.calculate_distance(event_lat, event_lon, lat, lon)
                    
                    # Create pseudo-station from event location
                    # This is a fallback approach using event reporting stations
                    net = props.get('net', 'US')
                    code = props.get('code', '')[:4] or 'UNK'
                    
                    stations.append({
                        'network': net,
                        'station': code,
                        'latitude': lat,
                        'longitude': lon,
                        'distance_km': distance
                    })
        except Exception as e:
            print(f"Error extracting stations from events: {e}")
        
        return stations
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points using Haversine formula
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        return c * r
    
    def get_seismic_waveforms(self, network, station, start_time, end_time, channels=['BHZ', 'HHZ', 'BHN', 'BHE']):
        """
        Fetch actual seismic waveform data using ObsPy
        """
        waveforms = None
        
        # Convert to UTCDateTime
        starttime = UTCDateTime(start_time)
        endtime = UTCDateTime(end_time)
        
        # Try different clients and channels
        for client_name, client in self.clients.items():
            for channel in channels:
                try:
                    print(f"        Trying {client_name} for {network}.{station}.{channel}...")
                    
                    # Get waveform data
                    waveforms = client.get_waveforms(
                        network=network,
                        station=station,
                        location="*",  # Try all locations
                        channel=channel,
                        starttime=starttime,
                        endtime=endtime
                    )
                    
                    if waveforms and len(waveforms) > 0:
                        print(f"        Success! Got {len(waveforms)} traces from {client_name}")
                        return waveforms, client_name
                        
                except FDSNException as e:
                    if "No data available" not in str(e):
                        print(f"        FDSN error: {e}")
                except Exception as e:
                    print(f"        Error: {e}")
                
                # Small delay between requests
                time.sleep(0.5)
        
        return None, None
    
    def save_waveform_data(self, waveforms, filepath, format='MSEED'):
        """
        Save waveform data to file
        """
        try:
            waveforms.write(filepath, format=format)
            return True
        except Exception as e:
            print(f"Error saving waveforms: {e}")
            return False
    
    def create_waveform_summary(self, waveforms):
        """
        Create summary information about waveforms
        """
        summary = {
            'traces': [],
            'total_traces': len(waveforms),
            'sampling_rates': [],
            'channels': set(),
            'start_times': [],
            'end_times': []
        }
        
        for trace in waveforms:
            trace_info = {
                'network': trace.stats.network,
                'station': trace.stats.station,
                'location': trace.stats.location,
                'channel': trace.stats.channel,
                'sampling_rate': trace.stats.sampling_rate,
                'npts': trace.stats.npts,
                'starttime': str(trace.stats.starttime),
                'endtime': str(trace.stats.endtime),
                'duration_hours': (trace.stats.endtime - trace.stats.starttime) / 3600.0
            }
            
            summary['traces'].append(trace_info)
            summary['sampling_rates'].append(trace.stats.sampling_rate)
            summary['channels'].add(trace.stats.channel)
            summary['start_times'].append(str(trace.stats.starttime))
            summary['end_times'].append(str(trace.stats.endtime))
        
        # Convert sets to lists for JSON serialization
        summary['channels'] = list(summary['channels'])
        summary['unique_sampling_rates'] = list(set(summary['sampling_rates']))
        
        return summary
    
    def get_earthquake_catalog_data(self, latitude, longitude, start_time, end_time, radius_km=200):
        """
        Get earthquake catalog data from USGS for the region
        """
        try:
            url = f"{self.base_url_usgs}/event/1/query"
            params = {
                'format': 'geojson',
                'latitude': latitude,
                'longitude': longitude,
                'maxradius': radius_km / 111.32,  # Convert to degrees
                'starttime': start_time.strftime('%Y-%m-%d'),
                'endtime': end_time.strftime('%Y-%m-%d'),
                'minmagnitude': 3.0,  # Only get M3+ events
                'orderby': 'time'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Catalog data request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching catalog data: {e}")
            return None
    
    def process_earthquake(self, row, index, total):
        """
        Process a single earthquake event and fetch seismic data
        """
        try:
            # Extract earthquake information
            title = row['title']
            magnitude = row['magnitude']
            date_str = row['date_time']
            latitude = row['latitude']
            longitude = row['longitude']
            location = row['location']
            
            print(f"Processing {index}/{total}: {title}")
            
            # Parse datetime
            try:
                event_time = pd.to_datetime(date_str, format='%d-%m-%Y %H:%M')
            except:
                try:
                    event_time = pd.to_datetime(date_str)
                except:
                    print(f"Could not parse date: {date_str}")
                    return None
            
            # Create safe directory name
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:100]  # Limit length
            
            event_dir = os.path.join(self.data_dir, f"{event_time.strftime('%Y%m%d_%H%M')}_M{magnitude}_{safe_title}")
            
            if os.path.exists(event_dir):
                print(f"Directory already exists, skipping: {safe_title}")
                return event_dir
            
            os.makedirs(event_dir, exist_ok=True)
            
            # Define time periods (1 month before and after)
            before_start = event_time - timedelta(days=30)
            before_end = event_time - timedelta(hours=1)  # Stop 1 hour before event
            after_start = event_time + timedelta(hours=1)  # Start 1 hour after event
            after_end = event_time + timedelta(days=30)
            
            # Find nearest stations
            print(f"  Finding nearest stations...")
            stations = self.get_nearest_stations(latitude, longitude)
            
            if not stations:
                print(f"  No stations found near {location}")
                # Save metadata anyway
                metadata = {
                    'event_info': {
                        'title': title,
                        'magnitude': magnitude,
                        'datetime': event_time.isoformat(),
                        'latitude': latitude,
                        'longitude': longitude,
                        'location': location
                    },
                    'stations': [],
                    'data_periods': {
                        'before': {
                            'start': before_start.isoformat(),
                            'end': before_end.isoformat()
                        },
                        'after': {
                            'start': after_start.isoformat(),
                            'end': after_end.isoformat()
                        }
                    },
                    'processing_time': datetime.now().isoformat(),
                    'status': 'no_stations_found'
                }
                
                with open(os.path.join(event_dir, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return event_dir
            
            print(f"  Found {len(stations)} stations")
            
            # Create subdirectories
            before_dir = os.path.join(event_dir, 'before_event')
            after_dir = os.path.join(event_dir, 'after_event')
            os.makedirs(before_dir, exist_ok=True)
            os.makedirs(after_dir, exist_ok=True)
            
            # Fetch seismic waveform data from stations
            station_data = []
            for i, station in enumerate(stations[:3]):  # Limit to top 3 stations to avoid overwhelming
                network = station['network']
                station_code = station['station']
                distance = station['distance_km']
                client_name = station.get('client', 'Unknown')
                
                print(f"    Station {i+1}: {network}.{station_code} ({distance:.1f} km) via {client_name}")
                
                station_info = {
                    'network': network,
                    'station': station_code,
                    'latitude': station['latitude'],
                    'longitude': station['longitude'],
                    'distance_km': distance,
                    'client': client_name,
                    'site_name': station.get('site_name', 'Unknown'),
                    'elevation': station.get('elevation', 0.0),
                    'data_available': {'before': False, 'after': False},
                    'waveform_summary': {'before': None, 'after': None}
                }
                
                # Fetch before event waveform data
                print(f"      Fetching before-event waveforms...")
                before_waveforms, before_client = self.get_seismic_waveforms(
                    network, station_code, before_start, before_end
                )
                if before_waveforms:
                    before_file = os.path.join(before_dir, f'{network}_{station_code}_before.mseed')
                    if self.save_waveform_data(before_waveforms, before_file):
                        station_info['data_available']['before'] = True
                        station_info['waveform_summary']['before'] = self.create_waveform_summary(before_waveforms)
                        print(f"        Saved {len(before_waveforms)} traces from {before_client}")
                
                # Small delay to be respectful to servers
                time.sleep(2)
                
                # Fetch after event waveform data
                print(f"      Fetching after-event waveforms...")
                after_waveforms, after_client = self.get_seismic_waveforms(
                    network, station_code, after_start, after_end
                )
                if after_waveforms:
                    after_file = os.path.join(after_dir, f'{network}_{station_code}_after.mseed')
                    if self.save_waveform_data(after_waveforms, after_file):
                        station_info['data_available']['after'] = True
                        station_info['waveform_summary']['after'] = self.create_waveform_summary(after_waveforms)
                        print(f"        Saved {len(after_waveforms)} traces from {after_client}")
                
                station_data.append(station_info)
                
                # Longer delay between stations
                time.sleep(3)
            
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
                'stations': station_data,
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
                'status': 'completed'
            }
            
            with open(os.path.join(event_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  Completed processing: {safe_title}")
            return event_dir
            
        except Exception as e:
            print(f"Error processing earthquake {index}: {e}")
            return None
    
    def fetch_all_earthquake_data(self, csv_file, max_events=None, start_from=0):
        """
        Fetch seismic data for all earthquakes in the CSV file
        """
        print("Loading earthquake data...")
        df = pd.read_csv(csv_file)
        
        # Filter out events with missing coordinates
        df = df.dropna(subset=['latitude', 'longitude'])
        
        if max_events:
            df = df.iloc[start_from:start_from + max_events]
        else:
            df = df.iloc[start_from:]
        
        print(f"Processing {len(df)} earthquake events...")
        print(f"Data will be saved to: {os.path.abspath(self.data_dir)}")
        
        successful = 0
        failed = 0
        
        # Process earthquakes sequentially to be respectful to APIs
        for index, row in df.iterrows():
            result = self.process_earthquake(row, index - start_from + 1, len(df))
            
            if result:
                successful += 1
            else:
                failed += 1
            
            # Progress update
            if (index - start_from + 1) % 10 == 0:
                print(f"\nProgress: {index - start_from + 1}/{len(df)} events processed")
                print(f"Successful: {successful}, Failed: {failed}")
                print("-" * 50)
            
            # Respectful delay between events
            time.sleep(3)
        
        print(f"\n=== Processing Complete ===")
        print(f"Total events processed: {len(df)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Data saved to: {os.path.abspath(self.data_dir)}")
        
        # Create summary file
        summary = {
            'processing_date': datetime.now().isoformat(),
            'total_events': len(df),
            'successful': successful,
            'failed': failed,
            'data_directory': os.path.abspath(self.data_dir),
            'data_period': '30 days before and after each event',
            'apis_used': ['IRIS FDSN', 'USGS FDSN']
        }
        
        with open(os.path.join(self.data_dir, 'processing_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)

def main():
    """Main function to run the seismic data fetcher"""
    # Initialize fetcher
    fetcher = SeismicDataFetcher()
    
    # CSV file path
    csv_file = 'earthquake_1995-2023.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    print("=== Seismic Data Fetcher ===")
    print("This script will fetch seismic station data for all earthquakes")
    print("Data period: 30 days before and after each event")
    print("APIs used: IRIS and USGS web services")
    print()
    
    # Ask user for processing options
    try:
        choice = input("Process all events? (y/n) or enter number to process: ").strip().lower()
        
        if choice == 'y':
            fetcher.fetch_all_earthquake_data(csv_file)
        elif choice == 'n':
            print("Processing cancelled.")
        else:
            try:
                num_events = int(choice)
                print(f"Processing first {num_events} events...")
                fetcher.fetch_all_earthquake_data(csv_file, max_events=num_events)
            except ValueError:
                print("Invalid input. Processing first 10 events as test...")
                fetcher.fetch_all_earthquake_data(csv_file, max_events=10)
                
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
