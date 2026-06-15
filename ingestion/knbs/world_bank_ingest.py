import requests
import pandas as pd
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

INDICATORS = {
    "FX.OWN.TOTL.ZS": "account_ownership_pct",
    "FB.CBK.BRCH.P5": "bank_branches_per_100k",
    "FX.OWN.TOTL.FE.ZS": "female_account_ownership_pct",
    "FX.OWN.TOTL.OL.ZS": "older_adults_account_pct",
    "FB.ATM.TOTL.P5": "atms_per_100k",
}

COUNTRY = "KE"
START_YEAR = 2010
END_YEAR = 2024
BASE_URL = "https://api.worldbank.org/v2"


def fetch_indicator(indicator_code, indicator_name):
    url = f"{BASE_URL}/country/{COUNTRY}/indicator/{indicator_code}"
    params = {"format": "json", "date": f"{START_YEAR}:{END_YEAR}", "per_page": 100}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if len(data) < 2 or not data[1]:
        print(f"  No data for {indicator_name}")
        return []

    records = []
    for entry in data[1]:
        if entry["value"] is not None:
            records.append({
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "country": entry["country"]["value"],
                "country_code": entry["countryiso3code"],
                "year": int(entry["date"]),
                "value": float(entry["value"]),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            })

    print(f"  {indicator_name}: {len(records)} records")
    return records


def upload_to_gcs(records, folder, filename):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"raw/{folder}/{filename}")
    ndjson = "\n".join(json.dumps(r) for r in records)
    blob.upload_from_string(ndjson, content_type="application/json")
    print(f"   Uploaded to GCS: raw/{folder}/{filename}")


def run():
    print("=" * 50)
    print("World Bank Kenya Indicators Ingestion")
    print(f"Period: {START_YEAR} - {END_YEAR}")
    print("=" * 50)

    all_records = []
    for code, name in INDICATORS.items():
        print(f"\nFetching: {name}")
        records = fetch_indicator(code, name)
        all_records.extend(records)

    if not all_records:
        print("No data fetched. Exiting.")
        return

    os.makedirs("data/raw", exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    local_file = f"data/raw/world_bank_{timestamp}.json"
    with open(local_file, "w") as f:
        f.write("\n".join(json.dumps(r) for r in all_records))
    print(f"\n Saved locally: {local_file}")
    print(f"Total records: {len(all_records)}")

    df = pd.DataFrame(all_records)
    print("\nSample data:")
    print(df[["indicator_name", "year", "value"]].head(5).to_string(index=False))

    upload_to_gcs(all_records, "world_bank", f"world_bank_{timestamp}.json")
    print("\n World Bank ingestion complete!")


if __name__ == "__main__":
    run()
