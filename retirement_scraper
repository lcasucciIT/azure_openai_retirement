"""
Model Retirement Data Aggregator (Web Scraping Version)

This module provides utilities to collect model retirement information for Azure OpenAI and Foundry models
by scraping official Microsoft Learn documentation tables.

Functions:
- scrape_retirement_table: Scrapes model retirement tables from a given documentation URL.
- get_combined_model_retirement_dict: Merges OpenAI and Foundry web-scraped model retirement data into a single dictionary.
"""

import requests
from bs4 import BeautifulSoup

def scrape_retirement_table(url, source_label):
    """
    Scrape model/version/retirement tables from a Microsoft Learn URL.

    Args:
        url (str): The URL to scrape.
        source_label (str): Label to identify the data source.

    Returns:
        dict: Dictionary mapping model-version keys to retirement info.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    lookup = {}
    tables = soup.find_all("table")
    for table in tables:
        # Find the closest preceding heading (h2 or h3) for context
        caption_tag = table.find_previous("h2") or table.find_previous("h3")
        model_type = caption_tag.get_text(strip=True) if caption_tag else "Unknown"
        # Extract table headers and normalize to lowercase
        headers_row = [th.text.strip().lower() for th in table.find_all("th")]
        # Check for tables with model/version/retirement columns
        if "model" in headers_row and "version" in headers_row and "retirement date" in headers_row:
            model_idx = headers_row.index("model")
            version_idx = headers_row.index("version")
            retirement_idx = headers_row.index("retirement date")
            # Iterate over table rows (skip header)
            for row in table.find_all("tr")[1:]:
                cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
                # Skip rows with insufficient columns
                if len(cols) <= max(model_idx, version_idx, retirement_idx):
                    continue
                # Normalize model and version strings
                model = cols[model_idx].strip().lower().replace("–", "-").replace(" ", "")
                version = cols[version_idx].strip().lower().replace("–", "-").replace(" ", "")
                retirement = cols[retirement_idx].strip()
                # Create a unique key for the model-version
                key = f"{model}-{version}".strip("-")
                lookup[key] = {
                    "retirement": retirement,
                    "type": model_type,
                    "source": source_label
                }
        # Check for tables with only model/retirement columns
        elif "model" in headers_row and "retirement date" in headers_row:
            model_idx = headers_row.index("model")
            retirement_idx = headers_row.index("retirement date")
            for row in table.find_all("tr")[1:]:
                cols = [td.get_text(" ", strip=True) for td in row.find_all("td")]
                if len(cols) <= max(model_idx, retirement_idx):
                    continue
                model = cols[model_idx].strip().lower().replace("–", "-").replace(" ", "")
                retirement = cols[retirement_idx].strip()
                key = model.strip("-")
                lookup[key] = {
                    "retirement": retirement,
                    "type": model_type,
                    "source": source_label
                }
    return lookup

def get_combined_model_retirement_dict():
    """
    Merge OpenAI and Foundry model retirement data with resilience checks.

    Returns:
        dict: Combined dictionary of model retirements, with OpenAI data taking precedence.
    """
    openai_url = "https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-retirements?tabs=text"
    foundry_url = "https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/model-lifecycle-retirement"
    openai_retirements = scrape_retirement_table(openai_url, source_label="OpenAI")
    foundry_retirements = scrape_retirement_table(foundry_url, source_label="Foundry")
    # Merge dictionaries, OpenAI data takes precedence if conflict
    combined = {**foundry_retirements, **openai_retirements}
    return combined
