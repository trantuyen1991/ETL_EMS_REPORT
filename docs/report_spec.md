# Report Specification

## Report Type
Energy consumption PDF report for machines in one workshop.

## Output Format
- Final output format: PDF
- Intended usage:
  - archive
  - sharing
  - printing

## Report Layout
The report should be structured in clear sections.

### Section 1 - Report Header
Include:
- report title
- workshop name or identifier
- export timestamp
- reporting scope
- optional company or project name if configured

### Section 2 - Overview / Summary
Include:
- short summary of the reporting scope
- total number of machines included
- optional total energy consumption summary if data is available

### Section 3 - Daily Report
Include:
- daily summary table
- daily energy consumption chart

### Section 4 - Weekly Report
Include:
- weekly summary table
- weekly energy consumption chart

### Section 5 - Monthly Report
Include:
- monthly summary table
- monthly energy consumption chart

### Section 6 - Quarterly Report
Include:
- quarterly summary table
- quarterly energy consumption chart

### Section 7 - Remarks / Notes
Optional section for:
- warnings
- missing data notes
- summary remarks

## Table Specification
Each summary table should support the following fields where applicable:
- machine name or machine code
- reporting period
- energy consumption value
- unit
- optional ranking or notes

## Chart Specification
- Use Apache ECharts
- Use local ECharts library files from the project
- Do not use external URLs
- One chart for each aggregation level
- Charts must have:
  - title
  - axis labels
  - legend if needed
  - readable layout for PDF export

## PDF Rendering Requirements
- The report should be suitable for A4 PDF export
- The layout should remain readable when printed
- Tables and charts should not overlap
- Section titles should be clear and consistent
- Export timestamp must be visible

## File Naming Requirement
- The file name has a fixed predefined base name
- Only the export timestamp changes dynamically
- The final file path is controlled by external configuration

## Design Preference
- Clean and professional report layout
- Easy to read
- Suitable for workshop or management reporting
