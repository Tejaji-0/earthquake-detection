# Seismic Waves Data Collection

This directory contains seismic wave data collected one week before and after earthquake events.

## Structure

```
seismic_waves_data/
├── before_events/     # Seismic data from one week before earthquakes
├── after_events/      # Seismic data from one week after earthquakes 
├── station_metadata/  # Information about seismic monitoring stations
├── logs/             # Processing logs and error reports
└── event_*/          # Individual earthquake event directories
    ├── metadata.json                    # Event metadata and station info
    ├── before_NETWORK_STATION.json     # Before-event waveform data
    └── after_NETWORK_STATION.json      # After-event waveform data
```

## Data Sources

The seismic wave fetcher uses multiple FDSN (International Federation of Digital Seismograph Networks) data centers:

- **IRIS** - Incorporated Research Institutions for Seismology
- **USGS** - United States Geological Survey
- **ORFEUS** - Observatories and Research Facilities for European Seismology
- **GFZ** - GeoForschungsZentrum Potsdam

## Usage

### Automated Batch Processing
```bash
python3 seismic_wave_fetcher.py
# Choose option 1 for batch processing
# Specify CSV file (default: data/database.csv)
# Set maximum events to process (default: 5)
```

### Manual Single Event
```bash
python3 seismic_wave_fetcher.py
# Choose option 2 for single earthquake
# Enter latitude, longitude, magnitude, date/time, location
```

### Test Connectivity
```bash
python3 seismic_wave_fetcher.py
# Choose option 3 to test FDSN client connectivity
```

## Data Format

### Event Metadata (metadata.json)
```json
{
  "event_id": "unique_event_identifier",
  "earthquake_time": "2023-07-16T06:48:00",
  "latitude": 55.3,
  "longitude": -160.8,
  "magnitude": 7.2,
  "location": "Sand Point, Alaska",
  "time_windows": {
    "before": {"start": "2023-07-09T06:48:00", "end": "2023-07-16T06:48:00"},
    "after": {"start": "2023-07-16T06:48:00", "end": "2023-07-23T06:48:00"}
  },
  "stations": [...],
  "data_fetched": {
    "before": ["before_IU_ADK.json", ...],
    "after": ["after_IU_ADK.json", ...]
  }
}
```

### Waveform Data (before_*/after_*.json)
```json
{
  "event_id": "unique_event_identifier",
  "network": "IU",
  "station": "ADK",
  "latitude": 51.88,
  "longitude": -176.68,
  "distance_km": 234.5,
  "channels": [
    {
      "channel": "BHZ",
      "sampling_rate": 20.0,
      "npts": 1209600,
      "start_time": "2023-07-09T06:48:00",
      "end_time": "2023-07-16T06:48:00",
      "statistics": {
        "max": 1234.5,
        "min": -987.3,
        "mean": 12.4,
        "std": 45.7,
        "rms": 46.3,
        "dominant_frequency": 2.3,
        "frequency_content": {
          "low_freq_energy": 1234.5,
          "mid_freq_energy": 5678.9,
          "high_freq_energy": 234.1
        }
      }
    }
  ],
  "duration_seconds": 604800.0,
  "statistics": {
    "overall_max": 1234.5,
    "overall_min": -987.3,
    "overall_mean": 15.2,
    "overall_std": 42.1,
    "num_channels": 3
  }
}
```

## Features

### Station Selection
- Automatically finds seismic stations within 500km of earthquake epicenter
- Sorts stations by distance from epicenter
- Supports multiple seismic networks (IRIS, USGS, ORFEUS, GFZ)

### Data Processing
- Fetches raw waveform data for multiple channels (BHZ, BHN, BHE, HHZ, HHN, HHE)
- Calculates statistical measures (max, min, mean, std, RMS)
- Performs frequency domain analysis when scipy is available
- Handles multiple trace merging and data quality checks

### Time Window Analysis
- Configurable time windows (default: 7 days before/after)
- Separate data collection for pre-event and post-event periods
- Enables comparative analysis of seismic activity patterns

## Requirements

- Python 3.7+
- obspy>=1.3.0
- scipy>=1.9.0 (for frequency analysis)
- requests>=2.28.0
- pandas>=1.5.0
- numpy>=1.21.0

## Error Handling

The fetcher includes comprehensive error handling for:
- Network connectivity issues
- Data availability problems
- Station metadata errors
- Waveform processing failures
- File I/O operations

## Integration

This module integrates with the main earthquake detection system:
- Uses database.csv as input for batch processing
- Saves data in structured JSON format for ML analysis
- Provides metadata for correlation with earthquake predictions
- Supports real-time processing for recent events

## Future Enhancements

- Integration with machine learning pipeline for pattern recognition
- Real-time streaming data collection
- Advanced signal processing and feature extraction
- Automated quality control and data validation
- Support for additional seismic data formats