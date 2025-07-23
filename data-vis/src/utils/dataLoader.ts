import Papa from 'papaparse';
import type { EarthquakeData } from '../types/earthquake';

export const loadEarthquakeData = async (): Promise<EarthquakeData[]> => {
  try {
    const response = await fetch('/earthquake_1995-2023.csv');
    const csvText = await response.text();
    
    const parsed = Papa.parse<EarthquakeData>(csvText, {
      header: true,
      skipEmptyLines: true,
      transform: (value, field) => {
        // Convert numeric fields
        if (typeof field === 'string' && ['magnitude', 'cdi', 'mmi', 'tsunami', 'sig', 'nst', 'dmin', 'gap', 'depth', 'latitude', 'longitude'].includes(field)) {
          const num = parseFloat(value);
          return isNaN(num) ? 0 : num;
        }
        return value;
      }
    });

    if (parsed.errors.length > 0) {
      console.warn('CSV parsing errors:', parsed.errors);
    }

    return parsed.data.filter(row => row.title && row.magnitude); // Filter out invalid rows
  } catch (error) {
    console.error('Error loading earthquake data:', error);
    return [];
  }
};

export const filterEarthquakeData = (
  data: EarthquakeData[],
  filters: {
    minMagnitude?: number;
    maxMagnitude?: number;
    startDate?: string;
    endDate?: string;
    location?: string;
    alertLevel?: string;
  }
): EarthquakeData[] => {
  return data.filter(earthquake => {
    // Magnitude filter
    if (filters.minMagnitude && earthquake.magnitude < filters.minMagnitude) return false;
    if (filters.maxMagnitude && earthquake.magnitude > filters.maxMagnitude) return false;

    // Date filter
    if (filters.startDate) {
      const earthquakeDate = new Date(earthquake.date_time);
      const startDate = new Date(filters.startDate);
      if (earthquakeDate < startDate) return false;
    }
    
    if (filters.endDate) {
      const earthquakeDate = new Date(earthquake.date_time);
      const endDate = new Date(filters.endDate);
      if (earthquakeDate > endDate) return false;
    }

    // Location filter
    if (filters.location && 
        !earthquake.location.toLowerCase().includes(filters.location.toLowerCase()) &&
        !earthquake.country.toLowerCase().includes(filters.location.toLowerCase())) {
      return false;
    }

    // Alert level filter
    if (filters.alertLevel && earthquake.alert !== filters.alertLevel) return false;

    return true;
  });
};

export const getMagnitudeColor = (magnitude: number): string => {
  if (magnitude >= 8.0) return '#8B0000'; // Dark red for major earthquakes
  if (magnitude >= 7.0) return '#FF0000'; // Red for strong earthquakes
  if (magnitude >= 6.5) return '#FF6600'; // Orange for moderate earthquakes
  return '#FFB300'; // Yellow for lighter earthquakes
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};
