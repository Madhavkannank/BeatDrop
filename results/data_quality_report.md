# Data Quality & Observability Audit Report

**Generated:** 2026-09-27T16:57:53.228320+00:00
**Pipeline Status:** SUCCESS (827s)

## 1. Data Quality & Integrity Metrics

- **Total Ingested Records:** 5060
- **Valid Admitted Records:** 5000
- **Quarantined Records:** 60
- **Duplicate Records:** 10
- **Null Records:** 11
- **Data Quality Score:** **98.81%**

### Quarantine Rejection Breakdown

| Anomaly Category | Rejected Count |
| :--- | :--- |
| `MISSING_REQUIRED` | 11 |
| `YEAR_OUT` | 10 |
| `DURATION_OUT` | 15 |
| `POPULARITY_OUT` | 13 |
| `DUPLICATE_TRACK` | 10 |
| `INVALID_EXPLICIT` | 1 |

## 2. HDFS Lake Storage Inventory

| HDFS Layer Path | Size on Disk |
| :--- | :--- |
| `/music_project/raw` | `468.7 K  468.7 K  /music_project/raw` |
| `/music_project/processed` | `464.4 K  464.4 K  /music_project/processed` |
| `/music_project/curated` | `518.2 K  518.2 K  /music_project/curated` |
| `/music_project/analytics` | `7.0 K  7.0 K  /music_project/analytics` |
| `/music_project/quarantine` | `20.1 K  20.1 K  /music_project/quarantine` |

## 3. High-Level Analytics KPIs

- **Total Genres Evaluated:** 10
- **Highest Rated Genre:** `Pop` (71.86/100)
- **Lowest Rated Genre:** `Metal` (51.16/100)
