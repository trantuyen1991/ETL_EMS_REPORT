# Energy Consumption PDF Reporting Tool

## Overview

This project builds a Python reporting tool to read machine energy consumption data from MySQL, aggregate the data by day, week, month, and quarter, generate charts and summary tables, and export the final report to PDF files.

## Main Features

- Read energy consumption data from MySQL
- Aggregate data by:
  - day
  - week
  - month
  - quarter
- Generate summary tables
- Generate charts using Apache ECharts
- Use local ECharts library files stored in the project
- Export reports to PDF
- Save PDF files to a configured output directory
- Use predefined file naming rules with dynamic export timestamp
- Include logging and error handling

## Project Structure

```text
02_MySQL/
├── config/                # Application and logging configuration
├── docs/                  # Project context and working rules for OpenClaw
├── logs/                  # Runtime logs
├── output/reports/        # Generated PDF reports
├── src/
│   ├── db/                # MySQL access layer
│   ├── services/          # Aggregation, chart, table, and PDF services
│   ├── models/            # Data models
│   ├── utils/             # Logging, validation, datetime helpers
│   └── templates/         # HTML templates and local static assets
├── tests/                 # Test files
├── README.md
├── .gitignore
├── .env.example
└── requirements.txt
