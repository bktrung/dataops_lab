# DataOps Project Presentation
## DBT + Airflow + SQL Server Pipeline

---

## 1. Project Overview

**Goal:** Automated data transformation pipeline
- Extract: SQL Server (AdventureWorks 2014)
- Transform: DBT (Bronze → Silver → Gold)
- Orchestrate: Apache Airflow
- Apply: DataOps principles

**Tech Stack:**
- DBT | Airflow | SQL Server | Docker | GitHub Actions

**Key Features:**
- ✅ 3-layer architecture (Bronze/Silver/Gold)
- ✅ Automated orchestration
- ✅ Comprehensive testing
- ✅ Alert system

---

## 2. Architecture

```
SQL Server → DBT → SQL Server
    ↑         ↑         ↑
    └───── Airflow ─────┘
```

**5 Containers:**
- SQL Server | PostgreSQL | Airflow Web | Airflow Scheduler | DBT

**Data Flow:**
1. Extract → 2. Transform (Bronze→Silver→Gold) → 3. Store

**Medallion Architecture:**
- **Bronze:** Views (raw data)
- **Silver:** Tables (cleaned data)
- **Gold:** Tables (business marts)

---

## 3. Key Decisions

**Why Medallion Architecture?**
- Clear separation | Incremental refinement | Data lineage

**Why Docker?**
- Isolation | Reproducibility | Portability

**Why ELT over ETL?**
- Load first | Transform in warehouse | Faster iteration

**Why DBT + Airflow?**
- DBT: SQL-centric, version-controlled, built-in testing
- Airflow: Python-based, flexible scheduling, monitoring

---

## 4. Challenges & Solutions

**Challenge 1: Docker API Version**
- Problem: Client version too old
- Solution: Updated Dockerfile with docker-ce-cli
- ✅ Fixed docker exec commands

**Challenge 2: Container Permissions**
- Problem: Docker group missing
- Solution: Added groupadd before usermod
- ✅ Airflow can execute Docker commands

**Challenge 3: Cross-Platform Issues**
- Problem: Windows/Linux path differences
- Solution: Standardized paths and line endings
- ✅ Works on all platforms

---

## 5. Implementation

**DBT Models:**
- Bronze: 5 models (customers, products, sales, territory)
- Silver: 3 models (cleaned & transformed)
- Gold: 3 models (customer metrics, product performance, sales summary)

**Airflow DAGs:**
- Main pipeline: Daily schedule, Bronze→Silver→Gold→Tests
- Bronze testing: Every 30 min
- Data quality: Every 6 hours (Great Expectations)

**Testing:**
- Schema tests | Custom tests | Source freshness checks

---

## 6. Lessons Learned

**Technical:**
- Container compatibility matters
- Error handling is essential
- Testing catches issues early
- Documentation saves time

**Process:**
- Start with MVP, iterate
- Version control everything
- Test locally first
- Monitor and alert

**Best Practices:**
- Modular architecture
- Code-based workflows
- Automated testing
- Comprehensive docs

---

## 7. Demo

**Steps:**
1. Airflow UI → Trigger DAG
2. Monitor execution → View logs
3. Verify data → Check test results

**Access:**
- Airflow: http://localhost:8080 (admin/admin)
- SQL Server: localhost:1433
- Schemas: bronze | silver | gold

---

## Key Takeaways

1. ELT approach with code-based transformations
2. Docker enables reproducible environments
3. Testing catches issues early
4. Airflow provides reliable workflows
5. Documentation is essential

---

## Questions?

