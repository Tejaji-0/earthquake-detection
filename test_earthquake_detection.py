#!/usr/bin/env python3
"""
Test script for earthquake detection models
"""

from realtime_earthquake_detector import RealTimeEarthquakeDetector
import pandas as pd
import json

def test_models():
    """Test the trained earthquake detection models."""
    print("=== Testing Earthquake Detection Models ===")
    
    # Initialize detector
    detector = RealTimeEarthquakeDetector()
    
    # Load all models
    tasks = ['major_earthquake', 'significant_earthquake', 'tsunami_generating']
    loaded_tasks = []
    
    for task in tasks:
        if detector.load_trained_models(task):
            loaded_tasks.append(task)
            print(f"✓ Loaded {task} model")
        else:
            print(f"✗ Failed to load {task} model")
    
    if not loaded_tasks:
        print("No models loaded. Please train models first.")
        return
    
    # Load some sample data
    print("\nLoading sample earthquake data...")
    df = pd.read_csv('data/earthquake_1995-2023.csv')
    df['date_time'] = pd.to_datetime(df['date_time'], format='%d-%m-%Y %H:%M')
    
    # Test on first 10 earthquakes
    print(f"\nTesting on first 10 earthquakes from dataset:")
    print("-" * 80)
    
    predictions_summary = {task: {'positive': 0, 'total': 0} for task in loaded_tasks}
    
    for i, row in df.head(10).iterrows():
        earthquake_data = row.to_dict()
        print(f"\nEarthquake {i+1}: {earthquake_data['title']}")
        print(f"  Magnitude: {earthquake_data['magnitude']}")
        print(f"  Location: {earthquake_data['location']}")
        print(f"  Date: {earthquake_data['date_time']}")
        
        # Apply ML models
        for task in loaded_tasks:
            prediction = detector.predict_earthquake_class(earthquake_data, task)
            if prediction:
                pred_label = "POSITIVE" if prediction['prediction'] == 1 else "negative"
                confidence = prediction['confidence']
                print(f"  {task}: {pred_label} (confidence: {confidence:.3f})")
                
                predictions_summary[task]['total'] += 1
                if prediction['prediction'] == 1:
                    predictions_summary[task]['positive'] += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("PREDICTION SUMMARY:")
    for task, stats in predictions_summary.items():
        pct = (stats['positive'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {task}: {stats['positive']}/{stats['total']} positive predictions ({pct:.1f}%)")
    
    print("\n✓ Model testing completed successfully!")

def test_real_time_api():
    """Test real-time earthquake API fetching."""
    print("\n=== Testing Real-time API Fetching ===")
    
    detector = RealTimeEarthquakeDetector()
    
    # Fetch latest earthquakes
    print("Fetching latest earthquakes from USGS...")
    earthquakes = detector.fetch_latest_earthquakes('usgs_latest')
    
    if earthquakes:
        print(f"✓ Successfully fetched {len(earthquakes)} recent earthquakes")
        
        # Display first few
        for i, eq in enumerate(earthquakes[:3]):
            print(f"\nEarthquake {i+1}:")
            print(f"  Title: {eq['title']}")
            print(f"  Magnitude: {eq['magnitude']}")
            print(f"  Location: {eq['location']}")
            print(f"  Time: {eq['date_time']}")
    else:
        print("✗ No earthquakes fetched (may be normal if no recent activity)")

if __name__ == "__main__":
    test_models()
    test_real_time_api()
