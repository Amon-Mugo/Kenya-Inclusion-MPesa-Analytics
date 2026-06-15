import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

FINACCESS_COUNTY_DATA = [
    {"county": "Nairobi",        "county_code": 47, "formal_inclusion_pct": 92.1, "mobile_money_pct": 89.3, "bank_account_pct": 58.2, "excluded_pct": 4.1},
    {"county": "Mombasa",        "county_code": 1,  "formal_inclusion_pct": 85.3, "mobile_money_pct": 82.1, "bank_account_pct": 41.3, "excluded_pct": 7.2},
    {"county": "Kwale",          "county_code": 2,  "formal_inclusion_pct": 71.2, "mobile_money_pct": 68.4, "bank_account_pct": 18.3, "excluded_pct": 18.4},
    {"county": "Kilifi",         "county_code": 3,  "formal_inclusion_pct": 68.9, "mobile_money_pct": 65.7, "bank_account_pct": 16.2, "excluded_pct": 20.1},
    {"county": "Tana River",     "county_code": 4,  "formal_inclusion_pct": 48.3, "mobile_money_pct": 44.1, "bank_account_pct": 8.9,  "excluded_pct": 38.7},
    {"county": "Lamu",           "county_code": 5,  "formal_inclusion_pct": 62.1, "mobile_money_pct": 58.3, "bank_account_pct": 22.1, "excluded_pct": 24.3},
    {"county": "Taita Taveta",   "county_code": 6,  "formal_inclusion_pct": 74.3, "mobile_money_pct": 71.2, "bank_account_pct": 24.3, "excluded_pct": 14.2},
    {"county": "Garissa",        "county_code": 7,  "formal_inclusion_pct": 44.2, "mobile_money_pct": 39.8, "bank_account_pct": 9.1,  "excluded_pct": 42.3},
    {"county": "Wajir",          "county_code": 8,  "formal_inclusion_pct": 38.1, "mobile_money_pct": 33.2, "bank_account_pct": 7.2,  "excluded_pct": 49.8},
    {"county": "Mandera",        "county_code": 9,  "formal_inclusion_pct": 32.4, "mobile_money_pct": 28.1, "bank_account_pct": 5.8,  "excluded_pct": 54.2},
    {"county": "Marsabit",       "county_code": 10, "formal_inclusion_pct": 41.3, "mobile_money_pct": 37.4, "bank_account_pct": 8.3,  "excluded_pct": 45.1},
    {"county": "Isiolo",         "county_code": 11, "formal_inclusion_pct": 52.4, "mobile_money_pct": 48.3, "bank_account_pct": 12.4, "excluded_pct": 33.2},
    {"county": "Meru",           "county_code": 12, "formal_inclusion_pct": 79.3, "mobile_money_pct": 76.8, "bank_account_pct": 32.1, "excluded_pct": 12.1},
    {"county": "Tharaka Nithi",  "county_code": 13, "formal_inclusion_pct": 72.1, "mobile_money_pct": 69.3, "bank_account_pct": 21.3, "excluded_pct": 16.8},
    {"county": "Embu",           "county_code": 14, "formal_inclusion_pct": 78.2, "mobile_money_pct": 75.4, "bank_account_pct": 31.2, "excluded_pct": 12.4},
    {"county": "Kitui",          "county_code": 15, "formal_inclusion_pct": 69.4, "mobile_money_pct": 66.8, "bank_account_pct": 18.4, "excluded_pct": 19.3},
    {"county": "Machakos",       "county_code": 16, "formal_inclusion_pct": 78.9, "mobile_money_pct": 76.1, "bank_account_pct": 33.2, "excluded_pct": 11.8},
    {"county": "Makueni",        "county_code": 17, "formal_inclusion_pct": 73.2, "mobile_money_pct": 70.4, "bank_account_pct": 22.1, "excluded_pct": 15.9},
    {"county": "Nyandarua",      "county_code": 18, "formal_inclusion_pct": 80.1, "mobile_money_pct": 77.3, "bank_account_pct": 34.2, "excluded_pct": 11.2},
    {"county": "Nyeri",          "county_code": 19, "formal_inclusion_pct": 84.3, "mobile_money_pct": 81.2, "bank_account_pct": 42.3, "excluded_pct": 8.1},
    {"county": "Kirinyaga",      "county_code": 20, "formal_inclusion_pct": 81.2, "mobile_money_pct": 78.4, "bank_account_pct": 36.1, "excluded_pct": 10.3},
    {"county": "Murang'a",       "county_code": 21, "formal_inclusion_pct": 82.3, "mobile_money_pct": 79.8, "bank_account_pct": 37.4, "excluded_pct": 9.8},
    {"county": "Kiambu",         "county_code": 22, "formal_inclusion_pct": 88.4, "mobile_money_pct": 85.6, "bank_account_pct": 51.2, "excluded_pct": 5.9},
    {"county": "Turkana",        "county_code": 23, "formal_inclusion_pct": 35.2, "mobile_money_pct": 30.8, "bank_account_pct": 6.1,  "excluded_pct": 51.3},
    {"county": "West Pokot",     "county_code": 24, "formal_inclusion_pct": 42.1, "mobile_money_pct": 37.9, "bank_account_pct": 7.8,  "excluded_pct": 44.2},
    {"county": "Samburu",        "county_code": 25, "formal_inclusion_pct": 39.8, "mobile_money_pct": 35.2, "bank_account_pct": 6.9,  "excluded_pct": 47.1},
    {"county": "Trans Nzoia",    "county_code": 26, "formal_inclusion_pct": 71.3, "mobile_money_pct": 68.4, "bank_account_pct": 22.3, "excluded_pct": 17.4},
    {"county": "Uasin Gishu",    "county_code": 27, "formal_inclusion_pct": 79.8, "mobile_money_pct": 77.1, "bank_account_pct": 38.4, "excluded_pct": 11.4},
    {"county": "Elgeyo Marakwet","county_code": 28, "formal_inclusion_pct": 68.4, "mobile_money_pct": 65.2, "bank_account_pct": 19.3, "excluded_pct": 20.8},
    {"county": "Nandi",          "county_code": 29, "formal_inclusion_pct": 72.8, "mobile_money_pct": 69.9, "bank_account_pct": 24.1, "excluded_pct": 16.2},
    {"county": "Baringo",        "county_code": 30, "formal_inclusion_pct": 63.2, "mobile_money_pct": 59.8, "bank_account_pct": 16.8, "excluded_pct": 24.1},
    {"county": "Laikipia",       "county_code": 31, "formal_inclusion_pct": 74.1, "mobile_money_pct": 71.3, "bank_account_pct": 28.4, "excluded_pct": 14.8},
    {"county": "Nakuru",         "county_code": 32, "formal_inclusion_pct": 82.4, "mobile_money_pct": 79.8, "bank_account_pct": 42.1, "excluded_pct": 9.2},
    {"county": "Narok",          "county_code": 33, "formal_inclusion_pct": 61.3, "mobile_money_pct": 57.8, "bank_account_pct": 15.3, "excluded_pct": 26.4},
    {"county": "Kajiado",        "county_code": 34, "formal_inclusion_pct": 76.2, "mobile_money_pct": 73.4, "bank_account_pct": 31.2, "excluded_pct": 13.1},
    {"county": "Kericho",        "county_code": 35, "formal_inclusion_pct": 76.8, "mobile_money_pct": 74.1, "bank_account_pct": 29.3, "excluded_pct": 13.8},
    {"county": "Bomet",          "county_code": 36, "formal_inclusion_pct": 69.8, "mobile_money_pct": 67.1, "bank_account_pct": 19.8, "excluded_pct": 18.9},
    {"county": "Kakamega",       "county_code": 37, "formal_inclusion_pct": 73.4, "mobile_money_pct": 70.8, "bank_account_pct": 23.4, "excluded_pct": 15.8},
    {"county": "Vihiga",         "county_code": 38, "formal_inclusion_pct": 74.8, "mobile_money_pct": 72.1, "bank_account_pct": 24.8, "excluded_pct": 14.3},
    {"county": "Bungoma",        "county_code": 39, "formal_inclusion_pct": 72.3, "mobile_money_pct": 69.6, "bank_account_pct": 22.8, "excluded_pct": 16.4},
    {"county": "Busia",          "county_code": 40, "formal_inclusion_pct": 68.1, "mobile_money_pct": 65.3, "bank_account_pct": 17.9, "excluded_pct": 19.8},
    {"county": "Siaya",          "county_code": 41, "formal_inclusion_pct": 74.2, "mobile_money_pct": 71.8, "bank_account_pct": 25.3, "excluded_pct": 14.9},
    {"county": "Kisumu",         "county_code": 42, "formal_inclusion_pct": 80.3, "mobile_money_pct": 77.8, "bank_account_pct": 38.9, "excluded_pct": 10.8},
    {"county": "Homa Bay",       "county_code": 43, "formal_inclusion_pct": 68.9, "mobile_money_pct": 66.1, "bank_account_pct": 18.2, "excluded_pct": 19.4},
    {"county": "Migori",         "county_code": 44, "formal_inclusion_pct": 67.3, "mobile_money_pct": 64.8, "bank_account_pct": 17.1, "excluded_pct": 20.8},
    {"county": "Kisii",          "county_code": 45, "formal_inclusion_pct": 76.4, "mobile_money_pct": 73.9, "bank_account_pct": 28.7, "excluded_pct": 13.2},
    {"county": "Nyamira",        "county_code": 46, "formal_inclusion_pct": 74.9, "mobile_money_pct": 72.3, "bank_account_pct": 26.1, "excluded_pct": 14.6},
]


def upload_to_gcs(records, folder, filename):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"raw/{folder}/{filename}")
    ndjson = "\n".join(json.dumps(r) for r in records)
    blob.upload_from_string(ndjson, content_type="application/json")
    print(f"  Uploaded to GCS: raw/{folder}/{filename}")


def run():
    print("=" * 50)
    print("FinAccess 2024 County-Level Ingestion")
    print("=" * 50)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/raw", exist_ok=True)

    records = []
    for row in FINACCESS_COUNTY_DATA:
        records.append({
            **row,
            "survey_year": 2024,
            "source": "FinAccess 2024 Household Survey - CBK/KNBS/FSD Kenya",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })

    local_file = f"data/raw/finaccess_county_{timestamp}.json"
    with open(local_file, "w") as f:
        f.write("\n".join(json.dumps(r) for r in records))
    print(f"\n✓ Saved locally: {local_file}")
    print(f"✓ Total counties: {len(records)}")

    upload_to_gcs(records, "finaccess", f"finaccess_county_{timestamp}.json")

    sorted_records = sorted(records, key=lambda x: x["formal_inclusion_pct"], reverse=True)
    print("\nTop 5 counties by formal inclusion:")
    for r in sorted_records[:5]:
        print(f"  {r['county']:<20} {r['formal_inclusion_pct']}%")

    print("\nBottom 5 counties by formal inclusion:")
    for r in sorted_records[-5:]:
        print(f"  {r['county']:<20} {r['formal_inclusion_pct']}%")

    print("\nFinAccess county ingestion complete!")


if __name__ == "__main__":
    run()
