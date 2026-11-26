# System Design Note — Finance (2026-11-26)

## 1. Problem & Context
- **Reference Dataset:** `nelgiriyewithana/credit-card-fraud-detection-dataset-2023` (`~568,630` rows observed in sample/snapshot)
- **Observed Columns (31):** `id`, `V1`, `V2`, `V3`, `V4`, `V5`, `V6`, `V7`
- **Primary Workload:** High-throughput transaction scoring, fraud risk evaluation, and audit logging
- **Latency Target:** Strict low latency (< 100 ms p99 on inline scoring path; batch retraining daily)

## 2. High-Level Architecture
1. **Ingestion Layer:** Scheduled batch connector lands raw files into an immutable **Raw/Bronze Zone** with `ingestion_date` metadata.
2. **Validation & Transformation Layer:** Schema validation, null/type checks, and deduplication transform raw records into **Silver** and **Gold** tables.
3. **Serving & Consumption Layer:** Analytical queries hit curated tables/OLAP store; low-latency lookups/features are served via indexed stores or caches.

## 3. Key Design Decisions & Trade-offs
- **Idempotency & Partitioning:** Partition by event/ingestion date and deduplicate by business/event key so retries stay idempotent.
- **Storage Format:** Columnar storage (`Parquet`) with compression reduces scan cost and I/O for analytical SQL workloads.
- **Primary Bottleneck:** Class imbalance, bursty transaction spikes, and strict auditability/immutability — mitigated via partition pruning, caching/pre-aggregations, and backpressure/rate limiting.

## 4. Failure Modes & Reliability
- **Schema Drift:** Enforce schema contracts and quarantine malformed batches instead of silently corrupting tables.
- **Partial Runs / Retries:** Keep partition writes atomic with dead-letter handling for bad records.
- **Observability:** Track row-count anomalies, null-rate spikes, job duration, and failure alerts.
