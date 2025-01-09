from google.cloud import bigquery
import os
import pandas as pd
from pathlib import Path

from queries import retrofunding_graph

def fetch_and_save_dev_tool_relationships():
    # Set up GCP credentials and client
    GCP_PROJECT = 'opensource-observer'
    # Look for credentials in the project root directory
    credentials_path = Path(__file__).parent.parent / 'oso_gcp_credentials.json'
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
    
    client = bigquery.Client(GCP_PROJECT)
    result = client.query(retrofunding_graph)
    df = result.to_dataframe()

    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)

    # Save to CSV
    output_path = data_dir / 'dev_tool_relationships.csv'
    df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")

if __name__ == "__main__":
    fetch_and_save_dev_tool_relationships()
