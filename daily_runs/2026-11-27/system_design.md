# System Design Note — Entertainment (2026-11-27)

## 1. Problem & Context
- **Reference Dataset:** `shivamb/netflix-shows` (`~8,807` rows observed in sample/snapshot)
- **Observed Columns (12):** `show_id`, `type`, `title`, `director`, `cast`, `country`, `date_added`, `release_year`
- **Primary Workload:** Catalog indexing, content metadata search, and regional recommendation features
- **Latency Target:** Low-to-medium read latency (< 200 ms for catalog queries; batch updates hourly/daily)

## 2. High-Level Architecture
1. **Ingestion Layer:** Scheduled batch connector lands raw files into an immutable **Raw/Bronze Zone** with `ingestion_date` metadata.
2. **Validation & Transformation Layer:** Schema validation, null/type checks, and deduplication transform raw records into **Silver** and **Gold** tables.
3. **Serving & Consumption Layer:** Analytical queries hit curated tables/OLAP store; low-latency lookups/features are served via indexed stores or caches.

## 3. Key Design Decisions & Trade-offs
- **Idempotency & Partitioning:** Partition by event/ingestion date and deduplicate by business/event key so retries stay idempotent.
- **Storage Format:** Columnar storage (`Parquet`) with compression reduces scan cost and I/O for analytical SQL workloads.
- **Primary Bottleneck:** Skewed popularity (hot titles) and frequent metadata/tag updates — mitigated via partition pruning, caching/pre-aggregations, and backpressure/rate limiting.

## 4. Failure Modes & Reliability
- **Schema Drift:** Enforce schema contracts and quarantine malformed batches instead of silently corrupting tables.
- **Partial Runs / Retries:** Keep partition writes atomic with dead-letter handling for bad records.
- **Observability:** Track row-count anomalies, null-rate spikes, job duration, and failure alerts.
