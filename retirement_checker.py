# azure_retirement_checker2.py
"""
Azure OpenAI Deployment Retirement Checker (DevOps Ready)

This script scans Azure subscriptions for OpenAI/AIServices resources,
lists deployed models, and checks their retirement status by scraping
Microsoft's model retirement documentation and combining it with API data.

Key Features:
- Scans one or more Azure subscriptions for OpenAI/AIServices resources and their deployments.
- Retrieves model and version information for each deployment.
- Cross-references deployed models with retirement data from Microsoft Learn and the Azure OpenAI API.
- Outputs results in text, CSV, or JSON format for easy integration with DevOps pipelines or reporting tools.
- Supports parameterization for single-subscription runs and silent operation for automation.
- Designed for use in CI/CD environments such as GitHub Actions, Azure DevOps, or local scripts.

Usage Examples:
    python azure_retirement_checker2.py --output-format csv
    python azure_retirement_checker2.py --subscription-id <SUBSCRIPTION_ID> --silent

Environment:
- Requires Azure CLI for authentication.
- Requires the `retirement_scraper2.py` module in the same directory.


Author: Lucia Casucci
Date: 2025-10-02
"""


import requests
import subprocess
import json
import argparse
import csv
import os
from datetime import datetime
from retirement_scraper import get_combined_model_retirement_dict

def get_azure_access_token(cli_path=None):
    """
    Fetch an Azure bearer token using the Azure CLI.

    Args:
        cli_path (str, optional): Custom path to the Azure CLI executable.

    Returns:
        str: Azure access token for ARM API.
    """
    cli = cli_path or r"C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd"
    result = subprocess.run(
        [cli, "account", "get-access-token", "--resource", "https://management.azure.com"],
        capture_output=True,
        text=True
    )
    token = json.loads(result.stdout)["accessToken"]
    return token

def get_custom_subscriptions():
    """
    Return a list of fallback Azure subscriptions if no subscription ID is provided.

    Returns:
        list of tuples: Each tuple contains (subscription_id, subscription_name).
    """
    return [
        ("ADD_SUB1", "Primary AI Sub"),
        ("ADD_SUB2", "Test Sandbox"),
    ]

def get_openai_resources(subscription_id, token):
    """
    Retrieve all OpenAI and AIServices resources in a given Azure subscription.

    Args:
        subscription_id (str): Azure subscription ID.
        token (str): Azure access token.

    Returns:
        list: List of resource dictionaries.
    """
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resources?api-version=2022-12-01"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    all_resources = response.json().get("value", [])
    return [
        res for res in all_resources
        if res.get("type") == "Microsoft.CognitiveServices/accounts"
        and res.get("kind") in ["OpenAI", "AIServices"]
    ]

def get_deployments(subscription_id, resource_group, resource_name, token):
    """
    Retrieve all deployments for a given OpenAI/AIServices resource.

    Args:
        subscription_id (str): Azure subscription ID.
        resource_group (str): Resource group name.
        resource_name (str): Resource name.
        token (str): Azure access token.

    Returns:
        list: List of deployment dictionaries.
    """
    url = (
        f"https://management.azure.com/subscriptions/{subscription_id}" 
        f"/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices"
        f"/accounts/{resource_name}/deployments?api-version=2024-10-01"
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("value", [])

def parse_args():
    """
    Parse command-line arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Azure OpenAI Model Retirement Checker")
    parser.add_argument('--output-format', choices=['text', 'csv', 'json'], default='text')
    parser.add_argument('--output-path', help='Optional custom file name for output')
    parser.add_argument('--subscription-id', help='Run against single subscription ID')
    parser.add_argument('--cli-path', help='Override Azure CLI path if needed')
    parser.add_argument('--silent', action='store_true', help='Suppress printouts')
    return parser.parse_args()

def main():
    """
    Main entry point for the script.
    Orchestrates authentication, resource discovery, deployment inspection,
    retirement status lookup, and output formatting.
    """
    args = parse_args()
    token = get_azure_access_token(args.cli_path)
    retirement_lookup = get_combined_model_retirement_dict()
    subscriptions = (
        [(args.subscription_id, args.subscription_id)] 
        if args.subscription_id else get_custom_subscriptions()
    )
    results = []
    for sub_id, sub_name in subscriptions:
        try:
            resources = get_openai_resources(sub_id, token)
        except Exception as e:
            if not args.silent:
                print(f"Failed to fetch resources in {sub_name}: {e}")
            continue
        if not resources:
            if not args.silent:
                print(f"No OpenAI resources found in subscription {sub_name}")
            continue
        total_deployments = 0
        for resource in resources:
            resource_name = resource["name"]
            resource_group = resource["id"].split("/")[4]
            kind = resource.get("kind")
            try:
                deployments = get_deployments(sub_id, resource_group, resource_name, token)
                for dep in deployments:
                    model = dep.get('properties', {}).get('model', {})
                    model_name = model.get('name', '').lower()
                    model_version = model.get('version', '').lower()
                    lookup_key = f"{model_name}-{model_version}".replace(" ", "").replace("–", "-").strip("-")
                    retirement = retirement_lookup.get(lookup_key, {}).get("retirement", "Not Available")
                    result = {
                        "subscription": sub_name,
                        "resource_group": resource_group,
                        "deployment": dep.get("name"),
                        "model": model_name,
                        "version": model_version,
                        "retirement": retirement,
                        "kind": kind
                    }
                    results.append(result)
                    total_deployments += 1
                    if not args.silent and args.output_format == 'text':
                        print(f"[{sub_name}] {resource_group} / {dep['name']} - {model_name} ({model_version}) | Kind: {kind} | Retirement: {retirement}")
            except Exception as e:
                if not args.silent:
                    print(f"Error fetching deployments for {resource_name}: {e}")
        if not args.silent:
            print(f"Processed {total_deployments} deployments in subscription '{sub_name}'")
    # Save results to file if requested
    if args.output_format in ['csv', 'json']:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "model_retirement_results"
        os.makedirs(output_dir, exist_ok=True)
        output_path = args.output_path or os.path.join(output_dir, f"deployment_retirement_{timestamp}.{args.output_format}")
        with open(output_path, 'w', newline='') as f:
            if args.output_format == 'csv':
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            else:
                json.dump(results, f, indent=2)
        if not args.silent:
            print(f"Output written to {output_path}")

if __name__ == "__main__":
    main()
