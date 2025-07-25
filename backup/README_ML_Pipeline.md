# Earthquake Detection Machine Learning Pipeline

This repository contains a comprehensive machine learning pipeline for earthquake detection and analysis using real seismic data.

## Overview

The system includes:
1. **Data Processing**: Load and preprocess earthquake catalog data
2. **Feature Engineering**: Create relevant features for ML models
3. **Model Training**: Train multiple ML models for earthquake classification
4. **Real-time Detection**: Monitor live earthquake feeds and apply ML models
5. **Evaluation**: Comprehensive model evaluation and visualization

## Features

### Machine Learning Models
- Random Forest Classifier
- Gradient Boosting Classifier  
- Support Vector Machine (SVM)
- Neural Network (MLP)
- Automated hyperparameter optimization
- Cross-validation and performance metrics

### Classification Tasks
- **Major Earthquake Detection**: Classify earthquakes ≥ M6.0
- **Significant Event Detection**: Identify high-significance earthquakes
- **Tsunami Risk Assessment**: Predict tsunami-generating potential

### Real-time Capabilities
- Live earthquake monitoring from USGS and EMSC feeds
- Automated alert system for high-confidence detections
- Batch processing of earthquake datasets

## Quick Start

### 1. Setup Environment

```bash
# Navigate to the data directory
cd data/

# Run the setup script
python setup_earthquake_detection.py
```

Choose option 1 for full setup (installs packages and trains models).

### 2. Train ML Models

```bash
# Train all ML models
python earthquake_ml_pipeline.py
```

This will:
- Load earthquake data from `earthquake_1995-2023.csv`
- Engineer features
- Train multiple ML models
- Optimize hyperparameters
- Generate evaluation plots
- Save trained models

### 3. Real-time Monitoring

```bash
# Start real-time earthquake monitoring
python realtime_earthquake_detector.py
```

Choose option 1 for real-time monitoring or option 3 to test on latest earthquakes.

## File Structure

```
data/
├── earthquake_1995-2023.csv          # Main earthquake dataset
├── earthquake_ml_pipeline.py         # ML training pipeline
├── realtime_earthquake_detector.py   # Real-time detection system
├── setup_earthquake_detection.py     # Setup and installation script
├── requirements.txt                   # Python dependencies
├── ml_models/                         # Trained models (created after training)
│   ├── major_earthquake/
│   ├── significant_earthquake/
│   └── tsunami_generating/
└── monitoring_results_*/              # Real-time monitoring results
```

## Data Requirements

The system expects a CSV file with the following columns:
- `title`: Earthquake event title
- `magnitude`: Earthquake magnitude
- `date_time`: Date and time (format: DD-MM-YYYY HH:MM)
- `latitude`, `longitude`: Geographic coordinates
- `depth`: Earthquake depth (km)
- `location`: Location description
- `sig`: Significance score
- `alert`: Alert level (green, yellow, orange, red)
- `tsunami`: Tsunami flag (0/1)
- `nst`: Number of stations
- `gap`: Azimuthal gap
- `dmin`: Minimum distance to stations

## Machine Learning Pipeline Details

### Feature Engineering

The pipeline creates 30+ features including:
- **Magnitude features**: Raw magnitude, squared, logarithmic
- **Geographic features**: Latitude, longitude, distance from equator
- **Temporal features**: Year, month, day, hour, seasonal cycles
- **Seismic context**: Recent activity, magnitude trends
- **Network features**: Number of stations, gaps, distances

### Model Training Process

1. **Data Loading**: Load and validate earthquake dataset
2. **Feature Engineering**: Create ML-ready features
3. **Feature Selection**: Select top K features using statistical tests
4. **Model Training**: Train multiple algorithms with cross-validation
5. **Hyperparameter Optimization**: Grid search for best parameters
6. **Evaluation**: Generate performance metrics and plots
7. **Model Saving**: Save trained models and metadata

### Evaluation Metrics

- ROC-AUC scores
- Precision, Recall, F1-score
- Confusion matrices
- Cross-validation scores
- Feature importance analysis

## Real-time Detection

### Data Sources
- **USGS**: Latest and significant earthquake feeds
- **EMSC**: European-Mediterranean earthquake data

### Alert System
The system generates alerts for:
- High-confidence major earthquake predictions
- Significant earthquake events
- Potential tsunami-generating earthquakes

### Monitoring Features
- Configurable monitoring intervals
- JSON output of all detections
- High-confidence alert notifications
- Batch processing capabilities

## Usage Examples

### Training Models
```python
from earthquake_ml_pipeline import EarthquakeMLPipeline

# Initialize pipeline
pipeline = EarthquakeMLPipeline()

# Run full pipeline
pipeline.run_full_pipeline()

# Train specific task only
pipeline.load_and_preprocess_data()
pipeline.engineer_features()
pipeline.create_labels()
pipeline.train_models('major_earthquake')
```

### Real-time Detection
```python
from realtime_earthquake_detector import RealTimeEarthquakeDetector

# Initialize detector
detector = RealTimeEarthquakeDetector()

# Load trained models
detector.load_trained_models('major_earthquake')

# Get latest earthquakes
earthquakes = detector.fetch_latest_earthquakes()

# Apply ML prediction
for eq in earthquakes:
    prediction = detector.predict_earthquake_class(eq, 'major_earthquake')
    print(f"Prediction: {prediction}")
```

### Batch Processing
```python
# Apply models to historical data
detector.batch_predict_csv('earthquake_1995-2023.csv', 'predictions.json')
```

## Model Performance

After training, models typically achieve:
- **Major Earthquake Detection**: ~85-90% ROC-AUC
- **Significant Event Detection**: ~80-85% ROC-AUC  
- **Tsunami Risk Assessment**: ~75-80% ROC-AUC

Performance varies based on data quality and size.

## Output Files

### Training Output
- `ml_models/[task]/`: Trained models and metadata
- `ml_models/[task]/metadata.json`: Model performance metrics
- `ml_models/[task]/*_model.pkl`: Saved model files
- `ml_models/[task]/scaler.pkl`: Feature scaler
- `feature_importance_*.png`: Feature importance plots
- `roc_curves_*.png`: ROC curve comparisons
- `confusion_matrices_*.png`: Confusion matrix plots

### Monitoring Output
- `monitoring_results_*/monitoring_results.json`: Live monitoring data
- `earthquake_alert_*.json`: High-confidence alerts
- `batch_predictions_*.json`: Batch processing results

## Requirements

### Python Packages
```
pandas>=1.5.0
numpy>=1.21.0
scikit-learn>=1.1.0
matplotlib>=3.5.0
seaborn>=0.11.0
requests>=2.28.0
obspy>=1.3.0 (for seismic data processing)
```

### Data Requirements
- Minimum 1000+ earthquake records for training
- Geographic diversity for better generalization
- Recent data for relevant patterns

## Troubleshooting

### Common Issues

1. **Import Errors**: Install requirements using `pip install -r requirements.txt`

2. **Data Loading Errors**: Check CSV format and column names

3. **Model Loading Errors**: Ensure models are trained before real-time detection

4. **API Errors**: Check internet connection for real-time feeds

### Performance Tips

1. **Large Datasets**: Use feature selection to reduce computational load
2. **Real-time Performance**: Load models once and reuse for multiple predictions
3. **Memory Usage**: Process data in batches for very large datasets

## Advanced Configuration

### Custom Classification Tasks
```python
# Define custom labels
pipeline.labels['custom_task'] = (pipeline.df['magnitude'] >= 7.5).astype(int)

# Train models for custom task
pipeline.train_models('custom_task')
```

### Custom Feature Engineering
```python
# Add custom features
pipeline.features['custom_feature'] = pipeline.df['magnitude'] * pipeline.df['depth']

# Retrain with new features
pipeline.train_models()
```

### Hyperparameter Tuning
```python
# Modify hyperparameter grids in optimize_best_model()
param_grids = {
    'Random Forest': {
        'n_estimators': [50, 100, 200, 500],
        'max_depth': [5, 10, 15, 20, None]
    }
}
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality  
4. Submit pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- USGS for earthquake data and real-time feeds
- EMSC for European earthquake data
- ObsPy community for seismic data processing tools
- scikit-learn for machine learning algorithms

## Support

For questions or issues:
1. Check this documentation
2. Review error messages and logs
3. Ensure all requirements are installed
4. Verify data format and availability
