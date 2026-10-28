# FinSight AI — Financial Research MVP

Developed by Misbah Khizar.

A local financial research application that turns uploaded annual
reports and historical-price files into reviewable analysis.

## Features

- Text-based annual-report PDF upload and keyword search.
- Consolidated financial-figure extraction with human review.
- Source units, financial years and PDF page references.
- Revenue growth, profitability, liquidity and cash-flow analysis.
- Free-cash-flow proxy when separate PPE and intangible cash
  purchases are available.
- Downloadable financial research reports.
- Local AI question answering using Ollama and Qwen3 1.7B.
- Historical-price charts with moving averages, RSI and MACD.
- Company profiles, reviewed logos and leadership snapshots
  where previously collected.

## Technology

Python, Streamlit, pandas, Plotly, SQLite, pdfplumber,
ReportLab, Requests, Beautiful Soup and Ollama.

## Run the existing project

Activate the project environment:

    conda activate finsight-ai

Start the dashboard from the project folder:

    python -m streamlit run app.py --server.port 8503

Open http://localhost:8503.

For AI answers, start Ollama and install the model:

    ollama pull qwen3:1.7b

Financial calculations and charts do not require the model.

## How to use

1. Upload a text-based annual report.
2. Choose the correct PDF page layout.
3. Select the company and financial year.
4. Extract and review figures against the original PDF.
5. Save reviewed figures.
6. Open the company dashboard and download the analyst report.
7. Upload historical-price CSV data to explore charts.

## Data and calculation design

Source amounts are normalized to PKR thousands.
EPS remains PKR per share.

Financial calculations use Python, not generated AI arithmetic.

Free-cash-flow proxy:
Operating cash flow minus separate PPE and intangible cash purchases.
This excludes acquisitions and purchases of financial investments.

Business commentary consists of keyword-selected source excerpts.
It does not establish the causes of financial changes.

## Limitations

- Extraction depends on PDF layout; scanned PDFs need OCR,
  which is not implemented.
- Systems Limited was used to exercise the financial-report workflow.
  Universal company and banking-sector support is not claimed.
- AI citations and unit checks do not guarantee factual correctness.
- Company/group scope of commentary may remain unverified.
- Prices are uploaded historical data, not a live market feed.
- Complete PSX coverage, insider-trade analysis, automatic report
  downloads, valuation and price forecasting are not implemented.
- The application is designed for local use; public deployment
  and multi-user security have not been completed.

## Data availability

The application needs local company records and user-provided data.
Source reports, price files, logos, saved financial datasets and the
SQLite database are not included in the code-only package.

Public source access does not automatically grant redistribution
rights. Check source permissions before publishing third-party data.

## Project status

Working local portfolio MVP.
Not a trading platform or an investment recommendation service.
