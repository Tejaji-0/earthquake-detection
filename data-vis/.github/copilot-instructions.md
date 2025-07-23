# Copilot Instructions for Earthquake Data Visualization React App

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a React TypeScript application built with Vite for visualizing earthquake data from a CSV dataset spanning 1995-2023. The application displays earthquake information including magnitude, location, time, and various seismic parameters.

## Key Features
- Interactive earthquake data table with sorting and filtering
- Data visualization charts (magnitude distribution, geographic mapping, temporal trends)
- Search and filter functionality by location, magnitude, date range
- Responsive design for desktop and mobile devices

## Technology Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: CSS Modules or Styled Components
- **Data Visualization**: Chart.js or D3.js
- **Data Processing**: CSV parsing and filtering utilities

## Development Guidelines
- Use functional components with React hooks
- Implement proper TypeScript typing for all data structures
- Create reusable components for data display
- Follow React best practices for state management
- Ensure accessibility standards are met
- Optimize performance for large datasets (1000+ earthquake records)

## Data Structure
The earthquake dataset contains the following key fields:
- title, magnitude, date_time, location, latitude, longitude
- cdi, mmi, alert, tsunami, sig, net, depth
- continent, country

Please generate code that handles this specific data structure and provides meaningful visualizations for earthquake analysis.
