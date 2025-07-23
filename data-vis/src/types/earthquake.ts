export interface EarthquakeData {
  title: string;
  magnitude: number;
  date_time: string;
  cdi: number;
  mmi: number;
  alert: string;
  tsunami: number;
  sig: number;
  net: string;
  nst: number;
  dmin: number;
  gap: number;
  magType: string;
  depth: number;
  latitude: number;
  longitude: number;
  location: string;
  continent: string;
  country: string;
}

export interface FilterOptions {
  minMagnitude: number;
  maxMagnitude: number;
  startDate: string;
  endDate: string;
  location: string;
  alertLevel: string;
}
