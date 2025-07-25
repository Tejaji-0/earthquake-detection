export interface EarthquakeData {
  event_id?: number;
  title: string;
  magnitude: number;
  magnitude_category?: string;
  date_time: string;
  year?: number;
  month?: number;
  day?: number;
  hour?: number;
  cdi: number;
  mmi: number;
  alert: string;
  alert_description?: string;
  tsunami: number;
  tsunami_risk?: string;
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

export interface DatabaseData extends EarthquakeData {
  event_id: number;
  magnitude_category: string;
  year: number;
  month: number;
  day: number;
  hour: number;
  alert_description: string;
  tsunami_risk: string;
}

export interface FilterOptions {
  minMagnitude: number;
  maxMagnitude: number;
  startDate: string;
  endDate: string;
  location: string;
  alertLevel: string;
}
