import React, { useState } from 'react';
import type { EarthquakeData } from '../types/earthquake';
import { formatDate } from '../utils/dataLoader';
import { ChevronUp, ChevronDown } from 'lucide-react';
import './EarthquakeTable.css';

interface EarthquakeTableProps {
  data: EarthquakeData[];
}

type SortField = keyof EarthquakeData;
type SortDirection = 'asc' | 'desc';

const EarthquakeTable: React.FC<EarthquakeTableProps> = ({ data }) => {
  const [sortField, setSortField] = useState<SortField>('magnitude');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setCurrentPage(1); // Reset to first page when sorting
  };

  const sortedData = [...data].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    // Handle string comparison
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }
    
    if (aValue !== undefined && bValue !== undefined) {
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  const SortHeader: React.FC<{ field: SortField; children: React.ReactNode }> = ({ field, children }) => (
    <th onClick={() => handleSort(field)} className="sortable">
      <div className="sort-header">
        {children}
        {sortField === field && (
          sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />
        )}
      </div>
    </th>
  );

  return (
    <div className="earthquake-table-container">
      <div className="table-info">
        <p>Showing {paginatedData.length} of {data.length} earthquakes</p>
      </div>
      
      <div className="table-wrapper">
        <table className="earthquake-table">
          <thead>
            <tr>
              {data.length > 0 && data[0].event_id && <SortHeader field="event_id">ID</SortHeader>}
              <SortHeader field="magnitude">Magnitude</SortHeader>
              {data.length > 0 && data[0].magnitude_category && <SortHeader field="magnitude_category">Category</SortHeader>}
              <SortHeader field="date_time">Date & Time</SortHeader>
              <SortHeader field="location">Location</SortHeader>
              <SortHeader field="depth">Depth (km)</SortHeader>
              <SortHeader field="alert">Alert</SortHeader>
              {data.length > 0 && data[0].alert_description && <SortHeader field="alert_description">Alert Level</SortHeader>}
              <th>Tsunami</th>
              {data.length > 0 && data[0].tsunami_risk && <SortHeader field="tsunami_risk">Tsunami Risk</SortHeader>}
              <SortHeader field="sig">Significance</SortHeader>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((earthquake, index) => (
              <tr key={earthquake.event_id || index} className="earthquake-row">
                {earthquake.event_id && <td className="id-cell">{earthquake.event_id}</td>}
                <td 
                  className={`magnitude-cell magnitude-${Math.floor(earthquake.magnitude)}`}
                >
                  <strong>{earthquake.magnitude.toFixed(1)}</strong>
                </td>
                {earthquake.magnitude_category && (
                  <td className={`category-cell category-${earthquake.magnitude_category.toLowerCase()}`}>
                    {earthquake.magnitude_category}
                  </td>
                )}
                <td className="date-cell">{formatDate(earthquake.date_time)}</td>
                <td className="location-cell">
                  <div className="location-info">
                    <div className="location-title">{earthquake.location}</div>
                    {earthquake.country && (
                      <div className="country">{earthquake.country}</div>
                    )}
                  </div>
                </td>
                <td>{earthquake.depth.toFixed(1)}</td>
                <td>
                  <span className={`alert-badge alert-${earthquake.alert || 'none'}`}>
                    {earthquake.alert || 'N/A'}
                  </span>
                </td>
                {earthquake.alert_description && (
                  <td className={`alert-desc alert-desc-${earthquake.alert_description.toLowerCase()}`}>
                    {earthquake.alert_description}
                  </td>
                )}
                <td>
                  <span className={`tsunami-indicator ${earthquake.tsunami ? 'yes' : 'no'}`}>
                    {earthquake.tsunami ? 'Yes' : 'No'}
                  </span>
                </td>
                {earthquake.tsunami_risk && (
                  <td className={`tsunami-risk tsunami-risk-${earthquake.tsunami_risk.toLowerCase()}`}>
                    {earthquake.tsunami_risk}
                  </td>
                )}
                <td>{earthquake.sig}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          
          <button 
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default EarthquakeTable;
