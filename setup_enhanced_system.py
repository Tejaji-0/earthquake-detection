#!/usr/bin/env python3
"""
Setup and Integration Test Script for Earthquake Detection System
This script initializes the enhanced earthquake detection system with database integration.
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, status=""):
    """Print a step with status."""
    if status:
        print(f"  ✓ {step}: {status}")
    else:
        print(f"  {step}")

def check_file_exists(filepath, description=""):
    """Check if a file exists and print status."""
    if os.path.exists(filepath):
        print_step(f"{description or filepath} exists")
        return True
    else:
        print(f"  ✗ {description or filepath} missing")
        return False

def run_command(command, description=""):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_step(f"{description or command} completed successfully")
            return True
        else:
            print(f"  ✗ {description or command} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ {description or command} error: {e}")
        return False

def test_database_integration():
    """Test database.csv integration."""
    print_header("Testing Database Integration")
    
    # Check if database.csv exists
    if not check_file_exists("data/database.csv", "Enhanced database.csv"):
        print("  Creating database.csv from earthquake data...")
        try:
            import pandas as pd
            import numpy as np
            
            # Load original data
            df = pd.read_csv('data/earthquake_1995-2023.csv')
            
            # Add database fields
            database_df = df.copy()
            database_df['event_id'] = range(1, len(database_df) + 1)
            database_df['date_time_parsed'] = pd.to_datetime(database_df['date_time'], format='%d-%m-%Y %H:%M')
            database_df['year'] = database_df['date_time_parsed'].dt.year
            database_df['month'] = database_df['date_time_parsed'].dt.month
            database_df['day'] = database_df['date_time_parsed'].dt.day
            database_df['hour'] = database_df['date_time_parsed'].dt.hour
            
            # Add magnitude categories
            def get_magnitude_category(mag):
                if mag >= 8.0:
                    return 'Major'
                elif mag >= 7.0:
                    return 'Strong'
                elif mag >= 6.5:
                    return 'Moderate'
                else:
                    return 'Light'
            
            database_df['magnitude_category'] = database_df['magnitude'].apply(get_magnitude_category)
            database_df['tsunami_risk'] = database_df['tsunami'].apply(lambda x: 'Yes' if x == 1 else 'No')
            
            def get_alert_description(alert):
                if pd.isna(alert) or alert == '':
                    return 'None'
                elif alert == 'green':
                    return 'Low'
                elif alert == 'yellow':
                    return 'Moderate'
                elif alert == 'orange':
                    return 'High'
                elif alert == 'red':
                    return 'Critical'
                else:
                    return 'Unknown'
            
            database_df['alert_description'] = database_df['alert'].apply(get_alert_description)
            
            # Drop temporary column
            database_df = database_df.drop('date_time_parsed', axis=1)
            
            # Reorder columns
            column_order = [
                'event_id', 'title', 'magnitude', 'magnitude_category', 'date_time', 
                'year', 'month', 'day', 'hour', 'latitude', 'longitude', 'depth',
                'location', 'country', 'continent', 'alert', 'alert_description',
                'tsunami', 'tsunami_risk', 'sig', 'cdi', 'mmi', 'net', 'nst', 'dmin', 'gap', 'magType'
            ]
            
            available_columns = [col for col in column_order if col in database_df.columns]
            database_df = database_df[available_columns]
            
            # Save database.csv
            database_df.to_csv('data/database.csv', index=False)
            print_step("database.csv created successfully")
            
            # Copy to data-vis public folder
            database_df.to_csv('data-vis/public/database.csv', index=False)
            print_step("database.csv copied to data-vis/public/")
            
        except Exception as e:
            print(f"  ✗ Error creating database.csv: {e}")
            return False
    
    # Test data loading
    try:
        import pandas as pd
        df = pd.read_csv('data/database.csv')
        print_step(f"Database loaded successfully with {len(df)} records")
        
        # Check enhanced columns
        enhanced_columns = ['event_id', 'magnitude_category', 'year', 'month', 'day', 'hour', 'alert_description', 'tsunami_risk']
        for col in enhanced_columns:
            if col in df.columns:
                print_step(f"Enhanced column '{col}' available")
            else:
                print(f"  ✗ Enhanced column '{col}' missing")
        
        return True
    except Exception as e:
        print(f"  ✗ Error testing database loading: {e}")
        return False

def test_ml_pipeline():
    """Test ML pipeline with database integration."""
    print_header("Testing ML Pipeline")
    
    try:
        from earthquake_ml_pipeline import EarthquakeMLPipeline
        
        print_step("Initializing ML pipeline with database.csv")
        pipeline = EarthquakeMLPipeline()
        
        print_step("Loading and preprocessing data")
        df = pipeline.load_and_preprocess_data()
        
        print_step(f"Data loaded successfully: {len(df)} records")
        print_step("Creating features")
        features = pipeline.engineer_features()
        
        print_step(f"Features created: {len(features.columns)} features")
        print_step("Creating labels")
        labels = pipeline.create_labels()
        
        for label_name, label_values in labels.items():
            positive_count = label_values.sum()
            total_count = len(label_values)
            percentage = (positive_count / total_count) * 100
            print_step(f"Label '{label_name}': {positive_count}/{total_count} positive ({percentage:.1f}%)")
        
        return True
    except Exception as e:
        print(f"  ✗ ML pipeline test failed: {e}")
        return False

def test_realtime_detector():
    """Test real-time detector."""
    print_header("Testing Real-time Detector")
    
    try:
        from realtime_earthquake_detector import RealTimeEarthquakeDetector
        
        print_step("Initializing real-time detector")
        detector = RealTimeEarthquakeDetector()
        
        print_step("Loading trained models")
        tasks = ['major_earthquake', 'significant_earthquake', 'tsunami_generating']
        loaded_tasks = []
        
        for task in tasks:
            if detector.load_trained_models(task):
                loaded_tasks.append(task)
                print_step(f"Model '{task}' loaded successfully")
            else:
                print(f"  ✗ Model '{task}' failed to load")
        
        if loaded_tasks:
            print_step(f"{len(loaded_tasks)}/{len(tasks)} models loaded successfully")
            return True
        else:
            print("  ✗ No models loaded successfully")
            return False
            
    except Exception as e:
        print(f"  ✗ Real-time detector test failed: {e}")
        return False

def test_seismic_wave_fetcher():
    """Test seismic wave data fetcher."""
    print_header("Testing Seismic Wave Fetcher")
    
    if not check_file_exists("seismic_wave_fetcher.py", "Seismic wave fetcher script"):
        return False
    
    if not check_file_exists("seismic_waves_data", "Seismic waves data directory"):
        print_step("Creating seismic_waves_data directory")
        os.makedirs("seismic_waves_data", exist_ok=True)
    
    # Check subdirectories
    subdirs = ['before_events', 'after_events', 'station_metadata', 'logs']
    for subdir in subdirs:
        subdir_path = os.path.join("seismic_waves_data", subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
        print_step(f"Subdirectory '{subdir}' ready")
    
    try:
        from seismic_wave_fetcher import SeismicWaveFetcher
        
        print_step("Initializing seismic wave fetcher")
        fetcher = SeismicWaveFetcher()
        
        print_step("Fetcher initialized successfully")
        print_step(f"Available FDSN clients: {len(fetcher.clients)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Seismic wave fetcher test failed: {e}")
        return False

def test_frontend():
    """Test frontend build."""
    print_header("Testing Frontend")
    
    if not check_file_exists("data-vis", "Frontend directory"):
        return False
    
    # Check if node_modules exists
    if not os.path.exists("data-vis/node_modules"):
        print_step("Installing frontend dependencies")
        if not run_command("cd data-vis && npm install", "npm install"):
            return False
    
    print_step("Building frontend")
    if not run_command("cd data-vis && npm run build", "Frontend build"):
        return False
    
    # Check if database.csv is in public folder
    if not check_file_exists("data-vis/public/database.csv", "Database CSV in public folder"):
        # Copy it
        try:
            import shutil
            shutil.copy("data/database.csv", "data-vis/public/database.csv")
            print_step("Database CSV copied to public folder")
        except Exception as e:
            print(f"  ✗ Error copying database CSV: {e}")
            return False
    
    return True

def create_integration_summary():
    """Create a summary of the integration."""
    print_header("Creating Integration Summary")
    
    summary = {
        "integration_date": datetime.now().isoformat(),
        "enhancements": {
            "database_csv": {
                "description": "Enhanced CSV with computed fields and categories",
                "location": "data/database.csv",
                "fields_added": [
                    "event_id", "magnitude_category", "year", "month", "day", "hour",
                    "alert_description", "tsunami_risk"
                ]
            },
            "seismic_wave_data": {
                "description": "New directory for seismic wave data collection",
                "location": "seismic_waves_data/",
                "features": [
                    "Fetches data one week before/after earthquakes",
                    "Multiple FDSN data sources",
                    "Structured JSON output",
                    "Station metadata collection"
                ]
            },
            "frontend_integration": {
                "description": "Updated data visualization with database integration",
                "location": "data-vis/",
                "improvements": [
                    "Enhanced table with new database fields",
                    "Improved data loading with fallback",
                    "Better categorization and styling",
                    "Database CSV integration"
                ]
            },
            "ml_pipeline_updates": {
                "description": "Updated ML pipeline to use enhanced database",
                "improvements": [
                    "Uses database.csv by default",
                    "Handles multiple date formats",
                    "Leverages pre-computed temporal fields",
                    "Enhanced feature engineering"
                ]
            }
        },
        "files_created": [
            "data/database.csv",
            "seismic_wave_fetcher.py",
            "seismic_waves_data/README.md",
            "data-vis/public/database.csv"
        ],
        "files_modified": [
            "earthquake_ml_pipeline.py",
            "realtime_earthquake_detector.py",
            "test_earthquake_detection.py",
            "data-vis/src/App.tsx",
            "data-vis/src/utils/dataLoader.ts",
            "data-vis/src/types/earthquake.ts",
            "data-vis/src/components/EarthquakeTable.tsx",
            "data-vis/src/App.css",
            "requirements.txt"
        ],
        "system_status": "Enhanced with database integration and seismic wave data collection"
    }
    
    # Save summary
    with open("integration_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print_step("Integration summary saved to integration_summary.json")
    return True

def main():
    """Main setup and test function."""
    print_header("Earthquake Detection System - Enhanced Setup")
    print("This script will set up and test the enhanced earthquake detection system")
    print("with database integration and seismic wave data collection capabilities.")
    
    success_count = 0
    total_tests = 6
    
    # Run all tests
    tests = [
        ("Database Integration", test_database_integration),
        ("ML Pipeline", test_ml_pipeline),
        ("Real-time Detector", test_realtime_detector),
        ("Seismic Wave Fetcher", test_seismic_wave_fetcher),
        ("Frontend", test_frontend),
        ("Integration Summary", create_integration_summary)
    ]
    
    for test_name, test_func in tests:
        if test_func():
            success_count += 1
        else:
            print(f"  ⚠️  {test_name} had issues")
    
    # Final summary
    print_header("Setup Complete")
    print(f"  Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("  🎉 All systems ready!")
        print("\n  Next steps:")
        print("    1. Run 'python3 test_earthquake_detection.py' to test ML models")
        print("    2. Run 'python3 seismic_wave_fetcher.py' to collect seismic data")
        print("    3. Run 'cd data-vis && npm run dev' to start the frontend")
        print("    4. Run 'python3 realtime_earthquake_detector.py' for real-time monitoring")
    else:
        print("  ⚠️  Some components may need attention")
        print("    Check the error messages above for details")
    
    print(f"\n  System files:")
    print(f"    - Enhanced database: data/database.csv")
    print(f"    - Seismic data: seismic_waves_data/")
    print(f"    - Frontend: data-vis/dist/")
    print(f"    - ML models: ml_models/")
    print(f"    - Integration summary: integration_summary.json")

if __name__ == "__main__":
    main()