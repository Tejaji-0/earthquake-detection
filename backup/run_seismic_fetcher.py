#!/usr/bin/env python3
"""
Simplified Seismic Data Fetcher - processes earthquakes in batches
"""

import sys
import os
sys.path.append('.')

from backup.fetch_seismic_data import SeismicDataFetcher
import pandas as pd

def main():
    """Main function to run the seismic data fetcher with options"""
    
    print("=== Seismic Data Fetcher ===")
    print("This script will fetch seismic station data for earthquakes")
    print("Data period: 30 days before and after each event")
    print("APIs used: IRIS and USGS web services")
    print()
    
    # Initialize fetcher
    fetcher = SeismicDataFetcher()
    
    # CSV file path
    csv_file = 'earthquake_1995-2023.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return
    
    # Load and show basic info about the data
    df = pd.read_csv(csv_file)
    df = df.dropna(subset=['latitude', 'longitude'])
    
    print(f"Total earthquakes in dataset: {len(df)}")
    print(f"Magnitude range: {df['magnitude'].min():.1f} - {df['magnitude'].max():.1f}")
    print(f"Date range: {df['date_time'].min()} to {df['date_time'].max()}")
    print()
    
    # Processing options
    print("Processing options:")
    print("1. Test with 3 events")
    print("2. Process 10 events")
    print("3. Process 50 events")
    print("4. Process all events")
    print("5. Process specific range")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == '1':
        print("Processing 3 test events...")
        fetcher.fetch_all_earthquake_data(csv_file, max_events=3)
    elif choice == '2':
        print("Processing 10 events...")
        fetcher.fetch_all_earthquake_data(csv_file, max_events=10)
    elif choice == '3':
        print("Processing 50 events...")
        fetcher.fetch_all_earthquake_data(csv_file, max_events=50)
    elif choice == '4':
        confirm = input(f"This will process all {len(df)} events. Continue? (y/n): ")
        if confirm.lower() == 'y':
            fetcher.fetch_all_earthquake_data(csv_file)
        else:
            print("Cancelled.")
    elif choice == '5':
        try:
            start = int(input("Start from event number: ")) - 1
            count = int(input("Number of events to process: "))
            print(f"Processing {count} events starting from event {start + 1}...")
            fetcher.fetch_all_earthquake_data(csv_file, max_events=count, start_from=start)
        except ValueError:
            print("Invalid input. Please enter numbers.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
