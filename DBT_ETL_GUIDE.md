# DBT ETL Guide
## End‑to‑End Transformations with Bronze, Silver, Gold

---

## Table of Contents

1. [Overview](#overview)
2. [DBT Project Structure](#dbt-project-structure)
3. [Source Configuration (AdventureWorks)](#source-configuration-adventureworks)
4. [Bronze Layer – Raw Cleaned Views](#bronze-layer--raw-cleaned-views)
5. [Silver Layer – Business Entities](#silver-layer--business-entities)
6. [Gold Layer – Analytics Marts](#gold-layer--analytics-marts)
7. [Running DBT Locally](#running-dbt-locally)
8. [Tests & Data Quality](#tests--data-quality)
9. [How DBT Integrates with Airflow](#how-dbt-integrates-with-airflow)
10. [Debugging & Troubleshooting](#debugging--troubleshooting)

---

## Overview

This guide explains how the **DBT** part of the project is organised and how the **ETL / ELT** flow works from **SQL Server (AdventureWorks)** into the **Bronze → Silver → Gold** model layers.

You should read this guide together with:

- `DATAOPS_GUIDE.md` – DataOps concepts, CI/CD, and testing strategy
- `DATAOPS_LAB_GUIDE.md` – step‑by‑step lab for implementing automation
- `DATAOPS_PROJECT_REQUIREMENTS.md` – what your final project will be graded on

The goal of this document is to answer:

- *Where does the data come from?*
- *How is it transformed in each layer?*
- *How do I run and test the DBT project?*

---

## DBT Project Structure

The DBT project lives in the `dbt/` folder.

Key files and folders:

- `dbt/dbt_project.yml` – DBT project configuration (name, paths, model settings)
- `dbt/profiles.yml` – DBT profile used to connect to SQL Server (mounted in the container)
- `dbt/models/` – all DBT models organised by layer
	- `dbt/models/bronze/` – raw but lightly cleaned source views
	- `dbt/models/silver/` – conformed business entities
	- `dbt/models/gold/` – final analytics marts
- `dbt/models/sources.yml` – global source definitions (if used)
- `dbt/tests/` – additional tests (generic / data quality)
- `dbt/target/` – compiled models and run artefacts (ignored by Git)

From `dbt/dbt_project.yml`:

```yaml
name: 'dbt_sqlserver_project'
profile: 'dbt_airflow_project'

models:
	dbt_sqlserver_project:
		bronze:
			+materialized: view
			+schema: bronze
		silver:
			+materialized: table
			+schema: silver
		gold:
			+materialized: table
			+schema: gold
```

**Important:**

- **Bronze** models are **views** in the `bronze` schema.
- **Silver** and **Gold** models are **tables** in the `silver` and `gold` schemas.

---

## Source Configuration (AdventureWorks)

The project assumes an **AdventureWorks 2014** database restored into SQL Server (see `sqlserver/` directory for Docker and restore scripts).

Sources for DBT are configured in the Bronze layer, in `dbt/models/bronze/src_adventureworks.yml`:

```yaml
version: 2

sources:
	- name: adventureworks
		database: AdventureWorks2014
		schema: Sales
		tables:
			- name: Customer
			- name: SalesOrderHeader
			- name: SalesOrderDetail
			- name: Product
```

> Note: The exact table list and schema names may differ slightly in your file, but the idea is the same – define **source tables** once and reference them with `source('adventureworks', 'Customer')` in models.

Why this matters:

- Keeps raw sources **centralised and documented**.
- Enables **source freshness** checks in DBT.
- Provides automatic lineage from models back to tables in SQL Server.

---

## Bronze Layer – Raw Cleaned Views

**Folder:** `dbt/models/bronze/`

**Purpose:**

- Provide a thin layer on top of raw AdventureWorks tables.
- Apply simple cleaning and standardisation (renaming, basic casting, trimming).
- Keep business logic out of this layer.

### Key Models

You should see files similar to:

- `brnz_customers.sql`
- `brnz_products.sql`
- `brnz_sales_orders.sql`
- `brnz_example.sql` (playground/demo model)

Each model typically:

1. References a source table using `source()`.
2. Selects the columns you care about.
3. Applies basic cleaning/standardisation.

Example pattern (simplified):

```sql
with src as (
		select *
		from {{ source('adventureworks', 'Customer') }}
),
renamed as (
		select
				CustomerID       as customer_id,
				PersonID         as person_id,
				StoreID          as store_id,
				TerritoryID      as territory_id,
				rowguid,
				modifieddate
		from src
)

select *
from renamed
```

Because Bronze models are **views**, they always reflect the current state of the source tables.

Metadata and tests for Bronze live in `dbt/models/bronze/schema.yml`.

---

## Silver Layer – Business Entities

**Folder:** `dbt/models/silver/`

**Purpose:**

- Transform Bronze views into **clean, conformed entities**.
- Apply joins, filtering, and enrichment.
- Ensure each entity has a clean grain and keys.

### Key Models

- `slvr_customers.sql`
- `slvr_products.sql`
- `slvr_sales_orders.sql`

Typical transformations in this layer include:

- Joining multiple Bronze models together (e.g., orders + order details + customers).
- Handling nulls, data type conversions, and business‑friendly naming.
- Creating calculated fields that are **reused** in multiple Gold models.

Example pattern (simplified):

```sql
with orders as (
		select * from {{ ref('brnz_sales_orders') }}
),
customers as (
		select * from {{ ref('brnz_customers') }}
),
joined as (
		select
				o.sales_order_id,
				o.order_date,
				o.customer_id,
				c.territory_id,
				c.store_id,
				o.subtotal,
				o.taxamt,
				o.freight,
				o.total_due
		from orders o
		left join customers c
			on o.customer_id = c.customer_id
)

select *
from joined
```

Silver models are **materialized as tables** in the `silver` schema for performance and stability.

---

## Gold Layer – Analytics Marts

**Folder:** `dbt/models/gold/`

**Purpose:**

- Provide **business‑ready** tables and views for reporting, dashboards, and analytics.
- Aggregate Silver entities to key business grains (customer, product, time).
- Implement metrics defined in your project requirements.

### Key Models

- `gld_sales_summary.sql` – overall sales metrics at a chosen grain (e.g., by date, territory).
- `gld_customer_metrics.sql` – customer‑level KPIs (lifetime value, order counts, etc.).
- `gld_product_performance.sql` – product‑level KPIs (revenue, quantity sold, margin).

Example pattern (simplified):

```sql
with sales as (
		select * from {{ ref('slvr_sales_orders') }}
),
agg as (
		select
				order_date,
				sum(total_due)         as total_revenue,
				count(*)               as order_count
		from sales
		group by order_date
)

select *
from agg
```

Gold models are also **materialized as tables** (see `dbt_project.yml`) so they can be queried efficiently by BI tools.

---

## Running DBT Locally

You normally run DBT **inside the `dbt` Docker container** defined in `docker-compose.yml`.

### 1. Build and Start the Stack

From the project root:

```bash
docker compose up -d --build
```

Wait until SQL Server, Airflow, and DBT containers are healthy.

### 2. Open a Shell in the DBT Container

```bash
docker compose exec dbt bash
```

Inside the container, the working directory is usually `/usr/app/dbt` or similar (check your `Dockerfile`).

### 3. Run DBT Commands

Common commands:

```bash
dbt debug              # Check connection and configuration
dbt run                # Build all models (bronze, silver, gold)
dbt test               # Run tests
dbt run --models gold  # Only build gold layer
dbt docs generate      # Build documentation site
dbt docs serve         # Serve docs (for local exploration)
```

> Tip: During development, you can run specific models with `dbt run --select slvr_sales_orders` or `dbt run --select gld_sales_summary+`.

---

## Tests & Data Quality

Tests are defined mainly in the `schema.yml` files in each layer, plus any custom tests in `dbt/tests/`.

Typical tests you should see or add:

- **Uniqueness & not‑null** on primary keys (e.g., `sales_order_id`, `customer_id`).
- **Relationships** between fact and dimension tables.
- **Accepted values** for status columns (e.g., order status).
- **Freshness** tests on key source tables (configured against `sources`).

Example snippet (schema.yml):

```yaml
models:
	- name: slvr_sales_orders
		tests:
			- unique:
					column_name: sales_order_id
		columns:
			- name: sales_order_id
				tests:
					- not_null
```

You run all tests with:

```bash
dbt test
```

These tests are also executed in CI/CD as described in `DATAOPS_GUIDE.md` and `DATAOPS_LAB_GUIDE.md`.

---

## How DBT Integrates with Airflow

Airflow DAGs in `airflow/dags/` orchestrate DBT runs. Typical patterns you will see:

- A DAG that **runs DBT models** using `BashOperator` or a custom operator.
- Separate tasks to run **`dbt run`**, **`dbt test`**, and possibly **data quality checks**.

For example (conceptual):

```python
dbt_run = BashOperator(
		task_id='dbt_run',
		bash_command='cd /usr/app/dbt && dbt run',
)

dbt_test = BashOperator(
		task_id='dbt_test',
		bash_command='cd /usr/app/dbt && dbt test',
)

dbt_run >> dbt_test
```

In this project, look at DAGs like:

- `airflow/dags/dbt_dag.py`
- `airflow/dags/dbt_bronze_layer_test_alert_dag.py`

These DAGs wire DBT runs into a schedule, logging, and alerting.

---

## Debugging & Troubleshooting

If DBT fails or data looks wrong, use this checklist:

1. **Check connection**
	 - Run `dbt debug` inside the DBT container.
	 - Verify `dbt/profiles.yml` matches your SQL Server container settings.

2. **Inspect logs**
	 - DBT logs: `dbt/logs/dbt.log`
	 - Airflow logs: `airflow/logs/` (per DAG and task)

3. **Run a single model**
	 - `dbt run --select brnz_customers`
	 - `dbt run --select slvr_sales_orders`
	 - `dbt run --select gld_sales_summary`

4. **Use `dbt ls` for dependencies**
	 - `dbt ls --select gld_sales_summary+` to see all upstream models.

5. **Validate SQL in the database**
	 - Connect to SQL Server with a client (Azure Data Studio, DBeaver, etc.).
	 - Inspect schemas: `bronze`, `silver`, `gold`.

6. **Rebuild from scratch (dev only)**
	 - Drop schemas or use `dbt run --full-refresh` if you change materializations or keys.

If you consistently hit issues, cross‑check the expectations in `DATAOPS_PROJECT_REQUIREMENTS.md` to ensure your model logic matches the required business definitions.

---

**Next steps:**

- Implement or refine the SQL inside each **bronze / silver / gold** model to match your chosen business questions.
- Add tests for critical columns and relationships.
- Integrate your DBT runs with Airflow and CI/CD so that every change is automatically built, tested, and deployed.
