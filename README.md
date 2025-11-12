# Azure OpenAI Model Retirement Scraper

## Overview

This script extracts model retirement dates from:

* **Azure OpenAI model deployments** (via Azure Resource Manager + REST API)
* **Azure AI Services (Foundry)** model deployments (via Microsoft Learn web scraping)

It helps you:

* Proactively monitor deprecated models across subscriptions
* Prepare upgrade plans before forced retirements
* Automate validation of enterprise-scale deployments

---

## Limitations of Web Scraping

* Relies on the current HTML structure (for example, `<table>` format).
  If Microsoft changes the page formatting, scraping may break.
* Future updates are not guaranteed unless URLs and HTML structures remain consistent.

---

## How It Works

The script combines web scraping and API queries to build a unified lookup table.

1. **Web Scraping** – Scrapes official Microsoft Learn pages for Foundry and OSS models.
2. **API Calls** – Queries legacy OpenAI REST API endpoints to detect model deprecation based on inference timestamps.
3. **Data Merge** – Combines results from both sources. API results take precedence when duplicates are found.

---

## API Key Configuration (Optional)

To fetch retirement information via REST API for legacy OpenAI resources, create a `.env` file in the same folder as the script.

**Example:**

```bash
OPENAI_ENDPOINT_1=openai-east-us
OPENAI_KEY_1=abcdef123456789

OPENAI_ENDPOINT_2=openai-west-eu
OPENAI_KEY_2=xyz987654321
```

**Notes:**

* Add as many indexed keys as needed (`OPENAI_ENDPOINT_3`, etc.)
* Do not include quotes or extra spaces
* Used to query:

  ```
  https://<resource>.openai.azure.com/openai/models?api-version=2024-10-21
  ```

---

## Prerequisites

### System Requirements

* Python 3.9+
* Azure CLI installed and authenticated

```bash
az login
az account set --subscription "<Your Subscription Name or ID>"
```

### Python Dependencies

Install required modules:

```bash
pip install requests beautifulsoup4 python-dotenv
```

### Access Requirements

* Reader access to the subscription is required
  (needed to fetch resource metadata and deployments via the Azure REST API)

---

## Script Output

The script generates a CSV or JSON file containing:

| Field             | Description                          |
| ----------------- | ------------------------------------ |
| Subscription name | Azure subscription name              |
| Resource group    | Resource group name                  |
| Deployment name   | Model deployment name                |
| Model + Version   | Model identifier and version         |
| Retirement Date   | Model retirement date (if available) |
| Source            | Data source (`OpenAI` or `Foundry`)  |

Output files are saved inside:

```
model_retirement_results/
```

**Example file:**

```
model_retirement_results/model_retirement_report.csv
```

---

## Example Directory Layout

```
azure-model-retirement-scraper/
├── model_retirement_scraper.py
├── .env
├── requirements.txt
├── README.md
└── model_retirement_results/
    └── model_retirement_report.csv
```

---

If you copy **this exact version** into your `README.md`, it will render cleanly with proper headings, code blocks, and tables in GitHub Preview.

Would you like me to include a short “Usage” section (example command and output snippet) so it looks like a complete GitHub README?
