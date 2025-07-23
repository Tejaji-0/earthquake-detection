#!/usr/bin/env python3
"""
Production Seismic Data Fetcher for All Earthquakes
Fetches actual seismic waveform data for all earthquakes in the dataset
"""

import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNException
import warnings
warnings.filterwarnings('ignore')

class ProductionSeismicFetcher:
    def __init__(self, data_dir='seismic_station_data'):
        self.data_dir = data_dir
        
        # Initialize IRIS client (most reliable for global data)
        try:
            self.client = Client('IRIS')
            print("✓ IRIS client initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize IRIS client: {e}")
            self.client = None
        
        # Create main data directory
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Global station list (expanded for worldwide coverage)
        self.global_stations = [
            # Americas
            {'network': 'IU', 'station': 'ANMO', 'latitude': 34.9459, 'longitude': -106.4572, 'name': 'Albuquerque, NM'},
            {'network': 'IU', 'station': 'HRV', 'latitude': 42.5064, 'longitude': -71.5583, 'name': 'Harvard, MA'},
            {'network': 'IU', 'station': 'COLA', 'latitude': 64.8738, 'longitude': -147.8616, 'name': 'College, AK'},
            {'network': 'IU', 'station': 'CCM', 'latitude': 38.0557, 'longitude': -91.2446, 'name': 'Cathedral Cave, MO'},
            {'network': 'US', 'station': 'WMOK', 'latitude': 34.7367, 'longitude': -98.7707, 'name': 'Wichita Mountains, OK'},
            {'network': 'CI', 'station': 'PAS', 'latitude': 34.1484, 'longitude': -118.1717, 'name': 'Pasadena, CA'},
            {'network': 'BK', 'station': 'BRK', 'latitude': 37.8735, 'longitude': -122.2609, 'name': 'Berkeley, CA'},
            {'network': 'IU', 'station': 'SSPA', 'latitude': -40.3084, 'longitude': -70.8601, 'name': 'San Martin, Argentina'},
            {'network': 'GT', 'station': 'PLCA', 'latitude': -31.6729, 'longitude': -63.8792, 'name': 'Argentina'},
            
            # Europe & Middle East
            {'network': 'IU', 'station': 'KONO', 'latitude': 59.6491, 'longitude': 9.5982, 'name': 'Kongsberg, Norway'},
            {'network': 'IU', 'station': 'KEV', 'latitude': 69.7565, 'longitude': 27.0035, 'name': 'Kevo, Finland'},
            {'network': 'IU', 'station': 'KIEV', 'latitude': 50.7012, 'longitude': 29.2242, 'name': 'Kiev, Ukraine'},
            {'network': 'IU', 'station': 'PAB', 'latitude': 39.5446, 'longitude': 4.3499, 'name': 'San Pablo, Spain'},
            {'network': 'GE', 'station': 'WLF', 'latitude': 49.6555, 'longitude': 6.1508, 'name': 'Walferdange, Luxembourg'},
            {'network': 'GE', 'station': 'APE', 'latitude': 40.8204, 'longitude': 14.4297, 'name': 'Ape, Italy'},
            {'network': 'II', 'station': 'ANTO', 'latitude': 39.8683, 'longitude': 32.7934, 'name': 'Ankara, Turkey'},
            {'network': 'HL', 'station': 'JER', 'latitude': 31.7730, 'longitude': 35.2045, 'name': 'Jerusalem, Israel'},
            
            # Asia & Pacific
            {'network': 'IU', 'station': 'MAJO', 'latitude': 36.5457, 'longitude': 138.2041, 'name': 'Matsushiro, Japan'},
            {'network': 'IU', 'station': 'TATO', 'latitude': 24.9735, 'longitude': 121.4971, 'name': 'Taipei, Taiwan'},
            {'network': 'IU', 'station': 'ULN', 'latitude': 47.8651, 'longitude': 107.0532, 'name': 'Ulaanbaatar, Mongolia'},
            {'network': 'IU', 'station': 'MAKZ', 'latitude': 46.8080, 'longitude': 82.1283, 'name': 'Makanchi, Kazakhstan'},
            {'network': 'IU', 'station': 'TEIG', 'latitude': 20.2263, 'longitude': 92.7936, 'name': 'Teigaga, Myanmar'},
            {'network': 'II', 'station': 'NIL', 'latitude': 33.6506, 'longitude': 73.2686, 'name': 'Nilore, Pakistan'},
            {'network': 'IU', 'station': 'GUMO', 'latitude': 13.5893, 'longitude': 144.8684, 'name': 'Guam, Mariana Is'},
            {'network': 'IU', 'station': 'FUNA', 'latitude': -8.5259, 'longitude': 179.1966, 'name': 'Funafuti, Tuvalu'},
            {'network': 'GE', 'station': 'SUMG', 'latitude': -0.5527, 'longitude': 100.2381, 'name': 'Sumatra, Indonesia'},
            {'network': 'AU', 'station': 'ARMA', 'latitude': -30.6267, 'longitude': 151.9501, 'name': 'Armidale, Australia'},
            {'network': 'AU', 'station': 'EIDS', 'latitude': -26.3912, 'longitude': 116.7975, 'name': 'Emu Heights, Australia'},
            
            # Polar regions
            {'network': 'IU', 'station': 'PMSA', 'latitude': -64.7744, 'longitude': -64.0489, 'name': 'Palmer Station, Antarctica'},
            {'network': 'IU', 'station': 'QSPA', 'latitude': -89.9289, 'longitude': 144.4382, 'name': 'South Pole, Antarctica'},
        ]
    
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
    
    def get_nearest_stations(self, latitude, longitude, max_radius_km=3000, max_stations=5):
        """Get nearest stations from global list"""
        stations = []
        for station in self.global_stations:
            distance = self.calculate_distance(
                latitude, longitude,
                station['latitude'], station['longitude']
            )
            
            if distance <= max_radius_km:
                station_copy = station.copy()
                station_copy['distance_km'] = distance
                stations.append(station_copy)
        
        # Sort by distance and return top stations
        stations.sort(key=lambda x: x['distance_km'])
        return stations[:max_stations]
    
    def get_waveforms(self, network, station, start_time, end_time):
        """Get seismic waveforms"""
        if not self.client:
            return None, "No client available"
        
        # Convert to UTCDateTime
        starttime = UTCDateTime(start_time)
        endtime = UTCDateTime(end_time)
        
        # Try different channel combinations
        channel_sets = ['BH*', 'HH*', 'LH*', 'BHZ', 'HHZ']
        
        for channels in channel_sets:
            try:
                waveforms = self.client.get_waveforms(
                    network=network,
                    station=station,
                    location="*",
                    channel=channels,
                    starttime=starttime,
                    endtime=endtime
                )
                
                if waveforms and len(waveforms) > 0:
                    return waveforms, f"IRIS-{channels}"
                    
            except Exception:
                continue
            
            time.sleep(0.2)  # Small delay
        
        return None, "No data found"
    
    def process_earthquake(self, row, index, total):
        """Process a single earthquake"""
        try:
            # Extract earthquake information
            title = row['title']
            magnitude = row['magnitude']
            date_str = row['date_time']
            latitude = row['latitude']
            longitude = row['longitude']
            location = row['location']
            
            print(f"\\n[{index}/{total}] Processing: {title}")
            
            # Parse datetime
            try:
                event_time = pd.to_datetime(date_str, format='%d-%m-%Y %H:%M')
            except:
                try:
                    event_time = pd.to_datetime(date_str)
                except:
                    print(f"  ✗ Could not parse date: {date_str}")
                    return None
            
            # Create safe directory name
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:60]
            
            event_dir = os.path.join(
                self.data_dir,
                f"{event_time.strftime('%Y%m%d_%H%M')}_M{magnitude}_{safe_title}"
            )
            
            if os.path.exists(event_dir):
                print(f"  → Directory exists, skipping: {os.path.basename(event_dir)}")
                return event_dir
            
            os.makedirs(event_dir, exist_ok=True)
            
            # Create before/after directories
            before_dir = os.path.join(event_dir, 'before_event')
            after_dir = os.path.join(event_dir, 'after_event')
            os.makedirs(before_dir, exist_ok=True)
            os.makedirs(after_dir, exist_ok=True)
            
            # Define time periods (30 days before and after)
            before_start = event_time - timedelta(days=30)
            before_end = event_time - timedelta(hours=2)
            after_start = event_time + timedelta(hours=2)
            after_end = event_time + timedelta(days=30)
            
            # Find nearest stations
            stations = self.get_nearest_stations(latitude, longitude, max_radius_km=4000, max_stations=3)
            
            if not stations:
                print(f"  ✗ No stations found within 4000km")
                return None
            
            print(f"  → Found {len(stations)} stations:")
            for i, station in enumerate(stations, 1):
                print(f"    {i}. {station['network']}.{station['station']} ({station['distance_km']:.0f}km)")
            
            # Process stations
            station_results = []
            successful_retrievals = 0
            
            for i, station in enumerate(stations, 1):
                network = station['network']
                station_code = station['station']
                
                print(f"  [{i}/3] {network}.{station_code}:")
                
                station_info = {
                    'network': network,
                    'station': station_code,
                    'name': station['name'],
                    'distance_km': station['distance_km'],
                    'data_retrieved': {'before': False, 'after': False}
                }
                
                # Fetch before-event data
                before_waveforms, before_msg = self.get_waveforms(
                    network, station_code, before_start, before_end
                )
                
                if before_waveforms:
                    before_file = os.path.join(before_dir, f'{network}_{station_code}_before.mseed')
                    try:
                        before_waveforms.write(before_file, format='MSEED')
                        station_info['data_retrieved']['before'] = True
                        successful_retrievals += 1
                        file_size = os.path.getsize(before_file) / (1024*1024)
                        print(f"    ✓ Before: {len(before_waveforms)} traces ({file_size:.1f}MB)")
                    except Exception as e:
                        print(f"    ✗ Before: Save failed - {e}")
                else:
                    print(f"    ✗ Before: {before_msg}")
                
                time.sleep(1)
                
                # Fetch after-event data
                after_waveforms, after_msg = self.get_waveforms(
                    network, station_code, after_start, after_end
                )
                
                if after_waveforms:
                    after_file = os.path.join(after_dir, f'{network}_{station_code}_after.mseed')
                    try:
                        after_waveforms.write(after_file, format='MSEED')
                        station_info['data_retrieved']['after'] = True
                        successful_retrievals += 1
                        file_size = os.path.getsize(after_file) / (1024*1024)
                        print(f"    ✓ After: {len(after_waveforms)} traces ({file_size:.1f}MB)")
                    except Exception as e:
                        print(f"    ✗ After: Save failed - {e}")
                else:
                    print(f"    ✗ After: {after_msg}")
                
                station_results.append(station_info)
                time.sleep(2)  # Respectful delay
            
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
                    'before': {'start': before_start.isoformat(), 'end': before_end.isoformat()},
                    'after': {'start': after_start.isoformat(), 'end': after_end.isoformat()}
                },
                'processing_time': datetime.now().isoformat(),
                'successful_retrievals': successful_retrievals,
                'total_possible': len(stations) * 2,
                'status': 'completed'
            }
            
            with open(os.path.join(event_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"  ✓ Complete! Retrieved {successful_retrievals}/{len(stations)*2} datasets")
            return event_dir
            
        except Exception as e:
            print(f"  ✗ Error processing earthquake {index}: {e}")
            return None
    
    def process_all_earthquakes(self, csv_file, max_events=None, start_from=0):
        """Process all earthquakes in the CSV file"""
        if not self.client:
            print("Cannot proceed without IRIS client")
            return
        
        print("Loading earthquake data...")
        df = pd.read_csv(csv_file)
        df = df.dropna(subset=['latitude', 'longitude'])
        
        if max_events:
            df = df.iloc[start_from:start_from + max_events]
        else:
            df = df.iloc[start_from:]
        
        print(f"\\n{'='*60}")
        print(f"SEISMIC DATA FETCHER - PRODUCTION MODE")
        print(f"{'='*60}")
        print(f"Total earthquakes to process: {len(df)}")
        print(f"Data period: 30 days before and after each event")
        print(f"Max radius: 4000 km per event")
        print(f"Max stations: 3 per event")
        print(f"Data will be saved to: {os.path.abspath(self.data_dir)}")
        print(f"{'='*60}")
        
        successful = 0
        failed = 0
        start_time = datetime.now()
        
        for index, row in df.iterrows():
            result = self.process_earthquake(row, index - start_from + 1, len(df))
            
            if result:
                successful += 1
            else:
                failed += 1
            
            # Progress update every 10 events
            if (index - start_from + 1) % 10 == 0:
                elapsed = datetime.now() - start_time
                rate = (index - start_from + 1) / elapsed.total_seconds() * 3600  # events per hour
                
                print(f"\\n{'='*60}")
                print(f"PROGRESS UPDATE - {index - start_from + 1}/{len(df)} events processed")
                print(f"Successful: {successful} | Failed: {failed}")
                print(f"Rate: {rate:.1f} events/hour")
                print(f"Elapsed: {elapsed}")
                print(f"{'='*60}")
            
            # Respectful delay between events
            time.sleep(5)
        
        # Final summary
        total_time = datetime.now() - start_time
        print(f"\\n{'='*60}")
        print(f"PROCESSING COMPLETE!")
        print(f"{'='*60}")
        print(f"Total events processed: {len(df)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {successful/len(df)*100:.1f}%")
        print(f"Total time: {total_time}")
        print(f"Average time per event: {total_time.total_seconds()/len(df):.1f} seconds")
        print(f"Data saved to: {os.path.abspath(self.data_dir)}")
        print(f"{'='*60}")
        
        # Save processing summary
        summary = {
            'processing_date': datetime.now().isoformat(),
            'total_events': len(df),
            'successful': successful,
            'failed': failed,
            'success_rate': successful/len(df)*100,
            'total_time_seconds': total_time.total_seconds(),
            'average_time_per_event': total_time.total_seconds()/len(df),
            'data_directory': os.path.abspath(self.data_dir)
        }
        
        with open(os.path.join(self.data_dir, 'processing_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)

def main():
    """Main function"""
    fetcher = ProductionSeismicFetcher()
    
    csv_file = 'data\earthquake_1995-2023.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    print("SEISMIC DATA FETCHER - PRODUCTION VERSION")
    print("This will fetch actual seismic waveform data for earthquakes")
    print("Data source: IRIS Global Seismographic Network")
    print()
    
    # Processing options
    print("Processing options:")
    print("1. Test with 5 events")
    print("2. Process 25 events")
    print("3. Process 100 events")
    print("4. Process ALL events (1000+)")
    print("5. Custom range")
    
    try:
        choice = input("\\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print("\\nProcessing 5 test events...")
            fetcher.process_all_earthquakes(csv_file, max_events=5)
        elif choice == '2':
            print("\\nProcessing 25 events...")
            fetcher.process_all_earthquakes(csv_file, max_events=25)
        elif choice == '3':
            print("\\nProcessing 100 events...")
            fetcher.process_all_earthquakes(csv_file, max_events=100)
        elif choice == '4':
            confirm = input("This will process ALL events. This may take many hours. Continue? (y/n): ")
            if confirm.lower() == 'y':
                fetcher.process_all_earthquakes(csv_file)
            else:
                print("Cancelled.")
        elif choice == '5':
            start = int(input("Start from event number: ")) - 1
            count = int(input("Number of events to process: "))
            print(f"\\nProcessing {count} events starting from event {start + 1}...")
            fetcher.process_all_earthquakes(csv_file, max_events=count, start_from=start)
        else:
            print("Invalid choice.")
            
    except KeyboardInterrupt:
        print("\\nProcessing interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
