
# Project Title

GCP Data Engineering Portfolio
## Description
 4-week hands-on GCP data engineering project built from scratch. Covers the full data engineering lifecycle from raw file ingestion to automated cloud pipelines and business insights. Built using Google Cloud Platform free tier with zero infrastructure cost.


WHAT WAS BUILT:

1:Queried 212 million rows of Chicago taxi data on BigQuery in under 2 seconds

2:Built a 3-layer dbt project with staging and mart models running on BigQuery

3:Created a GCS bucket and automated file ingestion pipeline

4:Deployed a Cloud Function that automatically loads CSV files into BigQuery when uploaded

5:Built and orchestrated two Airflow DAGs connecting GCS, BigQuery and dbt

6:Designed a Kenya Financial Inclusion analysis revealing that North Eastern counties like Wajir (74% excluded) and Mandera (71% excluded) are severely underserved compared to Nairobi (4% excluded)



## Tech Stack: 

 BigQuery — cloud data warehouse
- dbt — data transformation
- Google Cloud Storage — raw data lake
- Cloud Functions — event-driven ingestion
- Apache Airflow — pipeline orchestration
## Features/Project

### Chicago Taxi Analysis
- 212 million rows queried on BigQuery public dataset
- 5 business questions answered with SQL
- dbt staging and mart models

### Kenya Financial Inclusion Pipeline
- County-level financial inclusion data
- GCS → BigQuery → dbt automated pipeline
- Key finding: Wajir has 74% financial exclusion rate vs Nairobi at 4%
- Airflow DAG runs weekly
## Architecture:


Raw file → GCS bucket → Cloud Function triggers → BigQuery loads → dbt transforms → Airflow orchestrates → Business insights