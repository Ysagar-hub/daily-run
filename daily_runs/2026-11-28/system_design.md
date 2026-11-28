# System Design Note — Ecommerce (2026-11-28)

## 1. Problem & Context
- **Reference Dataset:** `olistbr/brazilian-ecommerce` (`~99,441` rows observed in sample/snapshot)
- **Observed Columns (5):** `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state`
- **Primary Workload:** Order event ingestion, seller/region analytics, and checkout/fulfillment pipelines
- **Latency Target:** Near-real-time for order status tracking; daily/hourly for BI & cohort aggregations

## 2. High-Level Architecture
1. **Ingestion Layer:** Scheduled batch connector lands raw files into an immutable **Raw/Bronze Zone** with `ingestion_date` metadata.
2. **Validation & Transformation Layer:** Schema validation, null/type checks, and deduplication transform raw records into **Silver** and **Gold** tables.
3. **Serving & Consumption Layer:** Analytical queries hit curated tables/OLAP store; low-latency lookups/features are served via indexed stores or caches.

## 3. Key Design Decisions & Trade-offs
- **Idempotency & Partitioning:** Partition by event/ingestion date and deduplicate by business/event key so retries stay idempotent.
- **Storage Format:** Columnar storage (`Parquet`) with compression reduces scan cost and I/O for analytical SQL workloads.
- **Primary Bottleneck:** Peak traffic spikes (flash sales) and late-arriving order/shipment events — mitigated via partition pruning, caching/pre-aggregations, and backpressure/rate limiting.

## 4. Failure Modes & Reliability
- **Schema Drift:** Enforce schema contracts and quarantine malformed batches instead of silently corrupting tables.
- **Partial Runs / Retries:** Keep partition writes atomic with dead-letter handling for bad records.
- **Observability:** Track row-count anomalies, null-rate spikes, job duration, and failure alerts.
