# Project Context

## Project Name
Energy Consumption PDF Reporting Tool

## Objective
Build a Python reporting tool that reads energy consumption data from MySQL, aggregates the data by day, week, month, and quarter, then generates charts and summary tables and exports the final result to a PDF file.

## Main Purpose
The tool is used to create energy consumption reports for machines in a workshop. The reports must support multiple aggregation levels and must be suitable for sharing or printing as PDF documents.

## Data Source
- Source database: MySQL
- Data type: machine energy consumption data
- Scope: machines in one workshop

## Output
- Output format: PDF
- Output content:
  - report header
  - export timestamp
  - summary tables
  - charts
  - remarks or summary section if needed

## Output File Rules
- The output PDF file is saved to a configured folder
- The base file name is predefined
- Only the export date/time part changes dynamically when the file is generated

## Technical Requirements
- Language: Python
- Configuration must be externalized
- Logging and error handling are required
- Code structure must be modular and maintainable
- Avoid hard-coded values where possible

## Chart Requirements
- Use Apache ECharts
- Use a local ECharts library file stored in the project
- Do not use CDN or external chart URLs
- Charts should be rendered as part of the reporting pipeline and included in the final PDF output

## Suggested Rendering Flow
MySQL -> pandas -> aggregate data -> generate chart images -> render HTML template -> convert HTML to PDF

## Expected Project Style
- Clear project structure
- Step-by-step implementation
- Reusable modules
- Production-friendly code
