import datetime
import pathlib
import subprocess
import sys
import duckdb
import pandas as pd

DATASETS = [
    {"domain": "entertainment", "slug": "shivamb/netflix-shows"},
    {"domain": "ecommerce", "slug": "olistbr/brazilian-ecommerce"},
    {"domain": "finance", "slug": "nelgiriyewithana/credit-card-fraud-detection-dataset-2023"},
]

DOMAIN_CONTEXT = {
    "entertainment": {
        "workload": "Catalog indexing, content metadata search, and regional recommendation features",
        "latency": "Low-to-medium read latency (< 200 ms for catalog queries; batch updates hourly/daily)",
        "bottleneck": "Skewed popularity (hot titles) and frequent metadata/tag updates",
    },
    "ecommerce": {
        "workload": "Order event ingestion, seller/region analytics, and checkout/fulfillment pipelines",
        "latency": "Near-real-time for order status tracking; daily/hourly for BI & cohort aggregations",
        "bottleneck": "Peak traffic spikes (flash sales) and late-arriving order/shipment events",
    },
    "finance": {
        "workload": "High-throughput transaction scoring, fraud risk evaluation, and audit logging",
        "latency": "Strict low latency (< 100 ms p99 on inline scoring path; batch retraining daily)",
        "bottleneck": "Class imbalance, bursty transaction spikes, and strict auditability/immutability",
    },
}


def pick_dataset_for_today() -> dict:
    day_index = datetime.date.today().toordinal() % len(DATASETS)
    return DATASETS[day_index]


def download_dataset(slug: str, raw_dir: pathlib.Path) -> pathlib.Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["kaggle", "datasets", "download", "-d", slug, "-p", str(raw_dir), "--unzip"]
    subprocess.run(cmd, check=True)
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found after downloading {slug}")
    return csv_files[0]


def generate_system_design(
    out_dir: pathlib.Path,
    run_date: str,
    domain: str,
    slug: str,
    total_rows: int,
    columns: list[str],
) -> None:
    ctx = DOMAIN_CONTEXT.get(
        domain,
        {
            "workload": "General tabular ingestion, analytical aggregations, and downstream feature serving",
            "latency": "Batch-first with optional near-real-time micro-batches",
            "bottleneck": "Schema drift, data quality issues, and uneven partition sizes",
        },
    )

    sample_cols = ", ".join(f"`{c}`" for c in columns[:8]) if columns else "N/A"
    design_md = f"""# System Design Note — {domain.title()} ({run_date})

## 1. Problem & Context
- **Reference Dataset:** `{slug}` (`~{total_rows:,}` rows observed in sample/snapshot)
- **Observed Columns ({len(columns)}):** {sample_cols}
- **Primary Workload:** {ctx["workload"]}
- **Latency Target:** {ctx["latency"]}

## 2. High-Level Architecture
1. **Ingestion Layer:** Scheduled batch connector lands raw files into an immutable **Raw/Bronze Zone** with `ingestion_date` metadata.
2. **Validation & Transformation Layer:** Schema validation, null/type checks, and deduplication transform raw records into **Silver** and **Gold** tables.
3. **Serving & Consumption Layer:** Analytical queries hit curated tables/OLAP store; low-latency lookups/features are served via indexed stores or caches.

## 3. Key Design Decisions & Trade-offs
- **Idempotency & Partitioning:** Partition by event/ingestion date and deduplicate by business/event key so retries stay idempotent.
- **Storage Format:** Columnar storage (`Parquet`) with compression reduces scan cost and I/O for analytical SQL workloads.
- **Primary Bottleneck:** {ctx["bottleneck"]} — mitigated via partition pruning, caching/pre-aggregations, and backpressure/rate limiting.

## 4. Failure Modes & Reliability
- **Schema Drift:** Enforce schema contracts and quarantine malformed batches instead of silently corrupting tables.
- **Partial Runs / Retries:** Keep partition writes atomic with dead-letter handling for bad records.
- **Observability:** Track row-count anomalies, null-rate spikes, job duration, and failure alerts.
"""
    (out_dir / "system_design.md").write_text(design_md.strip() + "\n", encoding="utf-8")


def run_sql_and_dsa(csv_path: pathlib.Path, out_dir: pathlib.Path, domain: str, slug: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    run_date = datetime.date.today().isoformat()

    con = duckdb.connect(database=":memory:")
    con.execute(
        f"CREATE OR REPLACE TABLE raw_data AS SELECT * FROM read_csv_auto('{csv_path.as_posix()}', sample_size=-1)"
    )

    total_rows = con.execute("SELECT COUNT(*) FROM raw_data").fetchone()[0]
    columns = [row[1] for row in con.execute("PRAGMA table_info('raw_data')").fetchall()]

    sql_query = """
    -- Daily SQL Inspection: Row count
    SELECT COUNT(*) AS total_rows FROM raw_data;
    """
    sql_result = con.execute(sql_query).df()
    (out_dir / "query.sql").write_text(sql_query.strip() + "\n", encoding="utf-8")
    sql_result.to_csv(out_dir / "sql_output.csv", index=False)

    df = pd.read_csv(csv_path, nrows=5000)
    target_col = columns[0] if columns else None
    top_k = []

    if target_col:
        freq_map = {}
        for val in df[target_col].dropna().astype(str):
            freq_map[val] = freq_map.get(val, 0) + 1
        sorted_items = sorted(freq_map.items(), key=lambda item: (-item[1], item[0]))
        top_k = sorted_items[:10]

    dsa_code = f"""# DSA Task: Top-10 Frequency Count using HashMap + Custom Sort
# Time Complexity: O(N + U log U), Space Complexity: O(U)

top_10_results = {top_k!r}

if __name__ == "__main__":
    for rank, (value, count) in enumerate(top_10_results, start=1):
        print(f"{{rank}}. {{value}} -> {{count}}")
"""
    (out_dir / "dsa_top_k.py").write_text(dsa_code, encoding="utf-8")
    subprocess.run([sys.executable, str(out_dir / "dsa_top_k.py")], check=True)

    generate_system_design(
        out_dir=out_dir,
        run_date=run_date,
        domain=domain,
        slug=slug,
        total_rows=total_rows,
        columns=columns,
    )

    readme_text = f"""# Daily Run — {run_date}

- **Domain:** `{domain}`
- **Kaggle Dataset:** `{slug}`
- **Source CSV:** `{csv_path.name}`
- **Total Rows:** `{total_rows}`
- **Columns ({len(columns)}):** `{", ".join(columns[:10])}`
"""
    (out_dir / "README.md").write_text(readme_text, encoding="utf-8")


def main() -> None:
    today = datetime.date.today().isoformat()
    chosen = pick_dataset_for_today()
    out_dir = pathlib.Path(f"daily_runs/{today}")
    temp_raw = pathlib.Path("/tmp/kaggle_raw")

    csv_file = download_dataset(chosen["slug"], temp_raw)
    run_sql_and_dsa(csv_file, out_dir, chosen["domain"], chosen["slug"])
    print(f"Successfully generated daily run at {out_dir}")


if __name__ == "__main__":
    main()