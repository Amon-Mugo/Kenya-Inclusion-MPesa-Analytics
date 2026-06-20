FROM python:3.11-slim

RUN pip install --no-cache-dir dbt-bigquery==1.8.*

WORKDIR /app

COPY dbt/kenya_inclusion /app

ENV DBT_PROFILES_DIR=/app

ENTRYPOINT ["dbt", "run", "--target", "prod"]