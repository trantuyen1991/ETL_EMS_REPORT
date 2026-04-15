# Business Rules

## Reporting Scope
- The report covers energy consumption data for machines in one workshop.
- The report must support multiple reporting periods:
  - daily
  - weekly
  - monthly
  - quarterly

## Aggregation Rules
- Daily report:
  - aggregate energy consumption by day
- Weekly report:
  - aggregate energy consumption by week
- Monthly report:
  - aggregate energy consumption by month
- Quarterly report:
  - aggregate energy consumption by quarter

## Report Content Rules
Each generated report should include:
- report title
- export timestamp
- reporting period information
- summary tables
- charts for each aggregation level
- optional remarks or summary section if needed

## Machine Data Rules
- The report must show energy consumption for machines in the workshop.
- The grouping level must allow comparing machine consumption across periods.
- Machine names or machine identifiers must be preserved clearly in the output.

## Data Quality Rules
- Missing data must be handled safely.
- The script must not crash because of one bad record.
- Null or invalid values should be handled with clear rules in code.
- Important data processing issues must be logged.

## Reliability Rules
- The script should fail safely and log meaningful errors.
- Logging is required for key processing steps.
- The solution should prefer maintainability and correctness over shortcuts.

## Output Rules
- The final output is a PDF file.
- The PDF file is saved to a configured output directory.
- The base file name is predefined.
- Only the export date/time suffix changes dynamically when exporting.

## Chart Rules
- Charts must be generated using Apache ECharts.
- The ECharts library must be stored locally in the project.
- Do not use external CDN links.
- Charts included in the PDF must match the aggregated report data.

## Configuration Rules
- Database connection settings must not be hard-coded.
- Output directory must be configurable.
- File naming rules must be configurable.
- Report settings should be placed in config files where possible.

## Coding Rules
- Use modular Python code.
- Add concise English comments where needed.
- Include logging and error handling.
- Keep database access, aggregation, chart generation, and PDF export separated into different modules.
