#!/usr/bin/env python3
"""
Test script to run the advanced country detection on a small sample.
"""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backup.add_country_advanced import process_earthquake_database
import logging

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'data', 'database.csv')
    output_file = os.path.join(script_dir, 'data', 'database_sample_with_advanced_countries.csv')
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    print("Testing advanced country detection on a sample...")
    
    # Process with both methods
    print("\n1. Testing with geographical rules only (fast):")
    process_earthquake_database(
        input_file=input_file,
        output_file=output_file.replace('.csv', '_geo_only.csv'),
        use_geocoding=False,
        sample_size=100
    )
    
    print("\n2. Testing with geocoding enabled (slower but more accurate):")
    process_earthquake_database(
        input_file=input_file,
        output_file=output_file.replace('.csv', '_with_geocoding.csv'),
        use_geocoding=True,
        sample_size=100
    )

if __name__ == "__main__":
    main()
