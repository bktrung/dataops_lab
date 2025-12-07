# Module 5 – Great Expectations + Airflow (Corrected Walkthrough)

This guide rewrites **Module 5** using the exact configuration that is currently working in your repo. Follow it step‑by‑step and you should avoid all the errors we hit before.

> All paths and container names assume your project root is `dbt_airflow_project` and you're using the existing `docker-compose.yml`.

---

## 1. Prerequisites

Before starting:

- `docker compose ps` shows these services running:
  - `dbt_airflow_project-sqlserver-1`
  - `dbt_airflow_project-postgres-1`
  - `dbt_airflow_project-airflow-webserver-1`
  - `dbt_airflow_project-airflow-scheduler-1`
  - `dbt_airflow_project-dbt-1`
- AdventureWorks2014 is restored into SQL Server (your existing `sqlserver` setup).
- The `dbt` project is already working (you can run `dbt run` inside the `dbt` container without errors).

**Volume layout inside containers** (important for paths later):

- dbt container: `/opt/dbt` → host `./dbt`
- Airflow containers: `/opt/airflow/dags` → host `./airflow/dags`
- Airflow containers: `/opt/airflow/dbt` → host `./dbt`

This means the same `great_expectations` folder is seen as:

- `/opt/dbt/great_expectations` in the **dbt** container
- `/opt/airflow/dbt/great_expectations` in the **Airflow** containers

---

## 2. Install Great Expectations in the right containers

You must have Great Expectations (GE) and the SQL Server/ODBC stack installed wherever you run checkpoints.

### 2.1. dbt container

Inside `dbt_airflow_project-dbt-1`:

- `great_expectations` (0.18.x)
- `pyodbc`
- SQL Server ODBC driver (e.g., `msodbcsql17`)

Your dbt container is already configured and can run a simple `pyodbc.connect` to SQL Server. If you rebuild the container or start fresh, ensure the Dockerfile for `dbt` installs:

- `python -m pip install great_expectations pyodbc`
- OS‑level SQL Server ODBC driver (`msodbcsql17`) and a driver entry like `ODBC Driver 17 for SQL Server` in `/etc/odbcinst.ini`.

### 2.2. Airflow containers

The Airflow DAG *also* runs GE, so `airflow-webserver` and `airflow-scheduler` must have GE installed.

In both containers (or, better, baked into the Airflow `Dockerfile`):

- `python -m pip install great_expectations pyodbc`
- Same SQL Server ODBC driver as the dbt container

If you add this to `airflow/Dockerfile`, you won’t need to install it by hand each time.

---

## 3. Configure Great Expectations project in dbt

Your GE project lives in `dbt/great_expectations`. The most critical file is `great_expectations.yml`.

### 3.1. Datasource for SQL Server

We use a **`SqlAlchemyExecutionEngine`** with a **`RuntimeDataConnector`**, and we connect to SQL Server via a properly encoded `odbc_connect` string.

In `dbt/great_expectations/great_expectations.yml`, ensure you have a datasource similar to this (names should match what you already use):

- `datasource_name`: `adventureworks_datasource`
- Execution engine: `SqlAlchemyExecutionEngine`
- Connection string: `mssql+pyodbc:///?odbc_connect=...`
- Data connector: `default_runtime_data_connector` using `RuntimeDataConnector`

Key points:

- The `DRIVER` must match the installed ODBC driver name, e.g. `ODBC Driver 17 for SQL Server`.
- The `SERVER` should be `sqlserver,1433` (because that’s the Compose service name and port).
- The connection string must be URL‑encoded and wrapped in `odbc_connect=...`.
- Include `TrustServerCertificate=yes` to avoid certificate issues inside Docker.

> You already tested a working `pyodbc.connect` in the dbt container. Build your GE URL from that same string.

### 3.2. RuntimeDataConnector and batch identifiers

In the datasource config, the `RuntimeDataConnector` must be set up to accept **runtime SQL queries** and **batch identifiers**. Example pattern:

- `data_connector_name`: `default_runtime_data_connector`
- `class_name`: `RuntimeDataConnector`
- `batch_identifiers`: include something like `default_identifier_name`

GE 0.18.x will throw a `DataConnectorError` if you pass a `RuntimeBatchRequest` without batch identifiers, so we’ll include them in the checkpoints later.

---

## 4. Create expectation suites

Expectation suites live under `dbt/great_expectations/expectations`.

### 4.1. Customer suite

File: `dbt/great_expectations/expectations/customer_quality_suite.json`

Important:

- The file name and the internal `expectation_suite_name` **must match**.
- In your working setup both are:
  - File: `customer_quality_suite.json`
  - Inside JSON: `"expectation_suite_name": "customer_quality_suite"`

The guide in `DATAOPS_LAB_GUIDE.md` previously called this file `customer_suite.json`, which caused GE not to find the suite. The corrected, working state uses `customer_quality_suite` everywhere.

### 4.2. Sales order suite

File: `dbt/great_expectations/expectations/sales_order_suite.json`

- Internal name: `"expectation_suite_name": "sales_order_quality_suite"`

You already have expectations defined for:

- Uniqueness and non‑null checks on `SalesOrderID`
- Range checks on `TotalDue`
- Non‑null checks on `OrderDate`

As long as the suite name and file name are consistent, GE will recognize this suite.

### 4.3. Verify suites

From the **dbt** container:

- `great_expectations suite list`

You should see at least:

- `customer_quality_suite`
- `sales_order_quality_suite`

If not, double‑check:

- File names in `expectations/`
- The `expectation_suite_name` values inside the JSON files

---

## 5. Create checkpoints (with runtime queries)

Old instructions in `DATAOPS_LAB_GUIDE.md` created checkpoints **without** runtime queries or batch identifiers. This caused errors with the `RuntimeDataConnector`. The working version includes both.

### 5.1. Customer checkpoint

File: `dbt/great_expectations/checkpoints/customer_checkpoint.yml`

Key elements in your working config:

- `name: customer_checkpoint`
- `class_name: SimpleCheckpoint`
- `datasource_name: adventureworks_datasource`
- `data_connector_name: default_runtime_data_connector`
- `data_asset_name: Sales.Customer`
- `runtime_parameters.query: SELECT * FROM Sales.Customer` (or a limited `TOP N` if you prefer)
- `batch_identifiers` with a key that matches your connector (e.g. `default_identifier_name`)
- `expectation_suite_name: customer_quality_suite`

This structure satisfies the `RuntimeDataConnector` requirements and directly queries the `Sales.Customer` table.

### 5.2. Sales order checkpoint

File: `dbt/great_expectations/checkpoints/sales_order_checkpoint.yml`

Mirrors the customer checkpoint but targets `Sales.SalesOrderHeader` and `sales_order_quality_suite`. Core pieces:

- `name: sales_order_checkpoint`
- `class_name: SimpleCheckpoint`
- `datasource_name: adventureworks_datasource`
- `data_connector_name: default_runtime_data_connector`
- `data_asset_name: Sales.SalesOrderHeader`
- `runtime_parameters.query: SELECT * FROM Sales.SalesOrderHeader`
- `batch_identifiers` with appropriate identifier name/value
- `expectation_suite_name: sales_order_quality_suite`

### 5.3. Test checkpoints in dbt container

From `dbt_airflow_project-dbt-1`:

- `great_expectations checkpoint run customer_checkpoint`
- `great_expectations checkpoint run sales_order_checkpoint`

Both should succeed and create validation results under:

- `dbt/great_expectations/uncommitted/validations/...`

If you see driver errors (`HYT00`, `IM002`, `Can't open lib 'ODBC Driver 17 for SQL Server'`), revisit:

- The ODBC driver installation in the dbt container
- The `DRIVER` name and `SERVER` value in `great_expectations.yml`

---

## 6. Integrate GE with Airflow DAG

Now we wire everything into Airflow via `airflow/dags/data_quality_dag.py`.

### 6.1. Correct context root directory

Because Airflow mounts your dbt project at `/opt/airflow/dbt`, the correct GE path in **Airflow** is:

- `/opt/airflow/dbt/great_expectations`

The earlier lab text used `/opt/airflow/great_expectations`, which led to:

- `ConfigNotFoundError: No gx directory was found here!`

### 6.2. DAG structure (final working version)

File: `airflow/dags/data_quality_dag.py`

Key points in the implementation:

- DAG ID: `data_quality_validation`
- Two PythonOperators:
  - `validate_customer_data` → `customer_checkpoint`
  - `validate_sales_order_data` → `sales_order_checkpoint`
- One BashOperator:
  - `generate_data_docs` → build GE docs
- The Python callable:
  - Creates a `DataContext` with `context_root_dir='/opt/airflow/dbt/great_expectations'`
  - Calls `run_checkpoint(checkpoint_name=...)`
  - Checks `result["success"]` and raises an exception if `False`
  - **Does not** return the raw `CheckpointResult` (to avoid Airflow XCom serialization errors)

Earlier, returning `CheckpointResult` caused:

- `TypeError: Object of type CheckpointResult is not JSON serializable`

The fix is to either return `None` or a simple string.

### 6.3. Data docs task

The docs task should run in the GE project root inside Airflow:

- `bash_command='cd /opt/airflow/dbt/great_expectations && great_expectations docs build'`

This generates HTML docs under:

- `dbt/great_expectations/uncommitted/data_docs/local_site`

In the Airflow containers, the path is:

- `/opt/airflow/dbt/great_expectations/uncommitted/data_docs/local_site/index.html`

---

## 7. File permissions for GE artifacts

Because both dbt and Airflow containers write into `dbt/great_expectations/uncommitted`, you must ensure the host directory is writable by the user inside the Airflow containers.

If you see:

- `PermissionError: [Errno 13] Permission denied: '/opt/airflow/dbt/great_expectations/uncommitted/validations/...'`

Fix the permissions on the host:

- Make `dbt/great_expectations` owned by a user/group that maps correctly to Airflow’s UID (often 50000), or
- Loosen permissions to allow writes (e.g., `chmod -R a+rwX dbt/great_expectations`).

Once fixed, rerun the DAG and confirm that validation results and data docs are written successfully.

---

## 8. End‑to‑end tests

### 8.1. From dbt container (CLI)

- Run `great_expectations checkpoint run customer_checkpoint`
- Run `great_expectations checkpoint run sales_order_checkpoint`

Both should complete with `success: true`.

### 8.2. From Airflow (DAG test)

From the **scheduler** container (`dbt_airflow_project-airflow-scheduler-1`):

- `airflow dags test data_quality_validation 2024-01-01`

You should see:

- `validate_customer_data` task: success
- `validate_sales_order_data` task: success
- `generate_data_docs` task: success

If any checkpoint fails, the corresponding task should raise an exception and the DAG test will fail (this is good: it enforces data quality).

### 8.3. View data docs

On the host, open:

- `dbt/great_expectations/uncommitted/data_docs/local_site/index.html`

This lets you inspect the GE expectation suites and validation results in a browser.

---

## 9. Quick checklist (Module 5, working version)

Use this checklist to confirm Module 5 is truly complete:

- [ ] Great Expectations installed in **dbt** and **Airflow** containers (plus ODBC driver)
- [ ] `adventureworks_datasource` datasource in `great_expectations.yml` uses a working `mssql+pyodbc:///?odbc_connect=...` string
- [ ] `RuntimeDataConnector` configured with appropriate `batch_identifiers`
- [ ] `customer_quality_suite` and `sales_order_quality_suite` expectation suites exist and appear in `suite list`
- [ ] `customer_checkpoint` and `sales_order_checkpoint` include `runtime_parameters.query` and `batch_identifiers`
- [ ] `data_quality_validation` DAG uses `context_root_dir='/opt/airflow/dbt/great_expectations'`
- [ ] DAG tasks do **not** return `CheckpointResult` (only simple values or `None`)
- [ ] Airflow can write to `dbt/great_expectations/uncommitted/validations` and `.../data_docs`
- [ ] `airflow dags test data_quality_validation 2024-01-01` passes

Once all boxes are checked, Module 5 (Data Quality Framework with GE + Airflow) matches the fully working state from our debugging session.
