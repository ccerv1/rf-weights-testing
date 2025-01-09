# RF Weights Testing

Testing repo for RetroFunding (RF) dependency graph weighting visualization. This tool helps analyze and visualize relationships between projects and developer tools in the Optimism ecosystem.

## Overview

The project consists of three main components:

1. **Data Fetcher** (`oso.py`): Fetches project and dev tool relationship data from BigQuery
2. **Interactive Dashboard** (`dashboard.py`): Provides a Sankey diagram visualization with configurable weights
3. **Query Logic** (`queries.py`): Contains the BigQuery SQL for extracting relationship data

## Requirements

- Python 3.12
- Poetry for dependency management
- Google Cloud credentials for BigQuery access

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ccerv1/rf-weights-testing.git
   cd rf-weights-testing
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

    This will install all required packages.

3. Add your Google Cloud credentials file (eg, `oso_gcp_credentials.json`) to the project root directory. See [here](https://docs.opensource.observer/docs/guides/notebooks/jupyter#obtain-a-gcp-service-account-key) for instructions.


4. Review the config file `app/config.py`:

    - `GCP_PROJECT`: The name of your GCP project.
    - `GCP_CREDENTIALS_PATH`: The path to your GCP credentials file.
    - `CSV_PATH`: The path to the CSV file where the relationship data will be saved (eg, `data/dev_tool_relationships.csv`).

5. Fetch the latest relationship data:
   ```bash
   poetry run python app/oso.py
   ```

   This will save the data to `data/dev_tool_relationships.csv`.

6. Run the dashboard:
   ```bash
   poetry run python app/dashboard.py
   ```

   This will start a local server and open a browser window with the dashboard.
