#!/usr/bin/env python3
"""
Script to extract earthquake data before and after significant events.
This script identifies major earthquakes and extracts data from specified time periods
before and after these events for analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

def load_earthquake_data(file_path):
    """Load earthquake data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        # Convert date_time to datetime
        df['date_time'] = pd.to_datetime(df['date_time'], format='%d-%m-%Y %H:%M')
        # Sort by date_time
        df = df.sort_values('date_time').reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def identify_major_events(df, magnitude_threshold=7.0, significance_threshold=800):
    """
    Identify major earthquake events based on magnitude and significance.
    
    Args:
        df: DataFrame with earthquake data
        magnitude_threshold: Minimum magnitude to consider as major event
        significance_threshold: Minimum significance score to consider
    
    Returns:
        DataFrame with major events
    """
    major_events = df[
        (df['magnitude'] >= magnitude_threshold) | 
        (df['sig'] >= significance_threshold)
    ].copy()
    
    return major_events.sort_values('date_time')

def extract_before_after_data(df, event_date, days_before=30, days_after=30, 
                            radius_km=500, event_lat=None, event_lon=None):
    """
    Extract earthquake data before and after a specific event.
    
    Args:
        df: Full earthquake dataset
        event_date: Date of the main event
        days_before: Number of days before the event to include
        days_after: Number of days after the event to include
        radius_km: Radius in km around the event location (if coordinates provided)
        event_lat: Latitude of the main event
        event_lon: Longitude of the main event
    
    Returns:
        Dictionary with before and after data
    """
    start_date = event_date - timedelta(days=days_before)
    end_date = event_date + timedelta(days=days_after)
    
    # Filter by date range
    period_data = df[
        (df['date_time'] >= start_date) & 
        (df['date_time'] <= end_date)
    ].copy()
    
    # If coordinates are provided, filter by geographic proximity
    if event_lat is not None and event_lon is not None:
        # Simple distance calculation (approximation)
        # Convert radius from km to degrees (rough approximation: 1 degree ≈ 111 km)
        radius_deg = radius_km / 111.0
        
        period_data = period_data[
            (abs(period_data['latitude'] - event_lat) <= radius_deg) &
            (abs(period_data['longitude'] - event_lon) <= radius_deg)
        ]
    
    # Split into before and after
    before_data = period_data[period_data['date_time'] < event_date]
    after_data = period_data[period_data['date_time'] > event_date]
    
    return {
        'before': before_data,
        'after': after_data,
        'event_date': event_date,
        'total_before': len(before_data),
        'total_after': len(after_data)
    }

def save_event_data(event_data, event_info, output_dir):
    """Save before/after data for a specific event."""
    # Create event-specific directory
    event_date_str = event_info['date_time'].strftime('%Y%m%d_%H%M')
    magnitude = event_info['magnitude']
    # Clean location name for valid directory name
    location_raw = event_info['location'] if pd.notna(event_info['location']) else 'Unknown_Location'
    location = str(location_raw).replace(',', '_').replace(' ', '_').replace('?', '').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')[:50]
    
    event_dir = os.path.join(output_dir, f"event_{event_date_str}_M{magnitude}_{location}")
    os.makedirs(event_dir, exist_ok=True)
    
    # Save before data
    if not event_data['before'].empty:
        before_file = os.path.join(event_dir, 'before_event.csv')
        event_data['before'].to_csv(before_file, index=False)
        print(f"Saved {len(event_data['before'])} records before event to: {before_file}")
    
    # Save after data
    if not event_data['after'].empty:
        after_file = os.path.join(event_dir, 'after_event.csv')
        event_data['after'].to_csv(after_file, index=False)
        print(f"Saved {len(event_data['after'])} records after event to: {after_file}")
    
    # Save event metadata
    metadata = {
        'main_event': {
            'title': event_info['title'] if pd.notna(event_info['title']) else 'Unknown',
            'magnitude': float(event_info['magnitude']) if pd.notna(event_info['magnitude']) else 0.0,
            'date_time': event_info['date_time'].isoformat(),
            'latitude': float(event_info['latitude']) if pd.notna(event_info['latitude']) else None,
            'longitude': float(event_info['longitude']) if pd.notna(event_info['longitude']) else None,
            'location': str(event_info['location']) if pd.notna(event_info['location']) else 'Unknown Location',
            'depth': float(event_info['depth']) if pd.notna(event_info['depth']) else None,
            'significance': int(event_info['sig']) if pd.notna(event_info['sig']) else None
        },
        'analysis_parameters': {
            'days_before': 30,
            'days_after': 30,
            'radius_km': 500
        },
        'data_summary': {
            'events_before': int(event_data['total_before']),
            'events_after': int(event_data['total_after'])
        }
    }
    
    metadata_file = os.path.join(event_dir, 'event_metadata.json')
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return event_dir

def main():
    """Main function to process earthquake data."""
    # File paths
    input_file = 'earthquake_1995-2023.csv'
    output_dir = 'event_analysis'
    
    print("Loading earthquake data...")
    df = load_earthquake_data(input_file)
    
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    print(f"Loaded {len(df)} earthquake records from {df['date_time'].min()} to {df['date_time'].max()}")
    
    # Identify major events
    print("\nIdentifying major earthquake events...")
    major_events = identify_major_events(df, magnitude_threshold=7.0, significance_threshold=800)
    print(f"Found {len(major_events)} major events")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each major event
    processed_events = []
    
    for idx, event in major_events.iterrows():
        print(f"\nProcessing event: {event['title']}")
        print(f"Date: {event['date_time']}, Magnitude: {event['magnitude']}")
        
        # Extract before/after data
        event_data = extract_before_after_data(
            df, 
            event['date_time'],
            days_before=30,
            days_after=30,
            radius_km=500,
            event_lat=event['latitude'],
            event_lon=event['longitude']
        )
        
        # Save the data
        event_dir = save_event_data(event_data, event, output_dir)
        processed_events.append({
            'event': event['title'],
            'directory': event_dir,
            'before_count': event_data['total_before'],
            'after_count': event_data['total_after']
        })
    
    # Create summary report
    summary_file = os.path.join(output_dir, 'processing_summary.json')
    summary = {
        'processing_date': datetime.now().isoformat(),
        'total_events_processed': len(processed_events),
        'events': processed_events
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n=== Processing Complete ===")
    print(f"Processed {len(processed_events)} major events")
    print(f"Data saved to: {output_dir}")
    print(f"Summary saved to: {summary_file}")
    
    # Display summary
    print("\nEvent Summary:")
    for event in processed_events:
        print(f"- {event['event'][:60]}...")
        print(f"  Before: {event['before_count']} events, After: {event['after_count']} events")

if __name__ == "__main__":
    main()
