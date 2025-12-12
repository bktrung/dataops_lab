# DBT + Airflow + SQL Server DataOps Project

![DBT CI](https://github.com/bktrung/dbt-airflow-dataops/workflows/DBT%20CI%20Pipeline/badge.svg)
![Python Quality](https://github.com/bktrung/dbt-airflow-dataops/workflows/Python%20Code%20Quality/badge.svg)

# DBT and Airflow Data Pipeline Project

## Project Overview
This project implements an automated data transformation pipeline using DBT (Data Build Tool) and Apache Airflow. The pipeline extracts data from SQL Server (AdventureWorks 2014), transforms it using DBT models following a medallion architecture (Bronze → Silver → Gold), and orchestrates the workflow using Apache Airflow, following modern data engineering best practices.

### Key Features
- **Three-Layer Data Architecture**: Bronze (staging), Silver (cleaned), and Gold (business marts)
- **Automated Orchestration**: Apache Airflow DAGs with proper task dependencies and error handling
- **Comprehensive Testing**: Schema tests, custom generic tests, and data quality validations
- **Source Freshness Monitoring**: Automated checks for data staleness
- **Alert System**: Failure notifications integrated into Airflow workflows

### Architecture Overview
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  SQL Server │ ──► │    DBT     │ ──► │  Target DB  │
└─────────────┘     └─────────────┘     └─────────────┘
        ▲                  ▲                   ▲
        └──────────┬──────┴───────────┬───────┘
                   │                   │
            ┌──────┴───────┐    ┌─────┴──────┐
            │   Airflow    │    │  Docker    │
            └──────────────┘    └────────────┘
```

## Prerequisites
- Docker and Docker Compose
- Git
- Basic understanding of SQL, DBT, and Airflow
- Access to source SQL Server database

## Project Structure and Components

```
dataops_lab/
├── airflow/
│   ├── dags/                  # Contains Airflow DAG definitions
│   │   ├── dbt_dag.py        # Main DAG: Orchestrates bronze → silver → gold → test
│   │   ├── dbt_bronze_layer_test_alert_dag.py  # Bronze layer testing with alerts
│   │   ├── data_quality_dag.py  # Data quality validation DAG
│   │   └── utils/            # Utility modules
│   │       ├── alerting.py   # Alert management system
│   │       └── logging_utils.py  # Logging utilities
│   ├── logs/                  # Airflow execution logs
│   └── Dockerfile            # Airflow container configuration
├── dbt/
│   ├── models/               # Contains all DBT data models
│   │   ├── bronze/          # Bronze layer: Raw data extraction and basic cleaning
│   │   │   ├── brnz_customers.sql
│   │   │   ├── brnz_products.sql
│   │   │   ├── brnz_sales_orders.sql
│   │   │   ├── brnz_territory.sql
│   │   │   ├── schema.yml   # Model tests and documentation
│   │   │   └── src_adventureworks.yml  # Source definitions with freshness checks
│   │   ├── silver/          # Silver layer: Business logic transformations
│   │   │   ├── slvr_customers.sql
│   │   │   ├── slvr_products.sql
│   │   │   ├── slvr_sales_orders.sql
│   │   │   └── schema.yml
│   │   ├── gold/            # Gold layer: Business-ready marts
│   │   │   ├── gld_customer_metrics.sql
│   │   │   ├── gld_product_performance.sql
│   │   │   ├── gld_sales_summary.sql
│   │   │   └── schema.yml
│   │   └── sources.yml      # Source table definitions
│   ├── tests/               # Custom tests
│   │   ├── generic/        # Reusable generic tests
│   │   │   ├── test_positive_values.sql
│   │   │   ├── test_no_future_dates.sql
│   │   │   └── test_valid_email.sql
│   │   └── data_quality/   # Business logic tests
│   │       ├── test_positive_revenue.sql
│   │       ├── test_profit_margin_range.sql
│   │       ├── test_no_duplicate_orders.sql
│   │       └── test_order_customer_consistency.sql
│   ├── dbt_project.yml      # DBT project configurations
│   ├── packages.yml         # External DBT package dependencies
│   └── profiles.yml         # Database connection profiles
├── sqlserver/               # SQL Server setup scripts
└── docker-compose.yml       # Container orchestration configuration
```

### Component Details

#### 1. Airflow Components

**DAGs Implemented:**

1. **`dbt_transform_bronze_silver_gold`** (Main Pipeline DAG):
   - **Purpose**: Orchestrates the complete data transformation pipeline
   - **Schedule**: Daily (`@daily`)
   - **Task Flow**: Bronze → Silver → Gold → Tests
   - **Tasks**:
     - `dbt_run_bronze`: Runs all bronze layer models
     - `dbt_run_silver`: Runs all silver layer models (depends on bronze)
     - `dbt_run_gold`: Runs all gold layer models (depends on silver)
     - `dbt_test`: Executes all data quality tests (depends on gold)
   - **Error Handling**:
     - Retries: 2 attempts
     - Retry delay: 2 minutes
     - Failure callback: `notify_failure()` sends alerts via AlertManager
   - **Documentation**: Comprehensive DAG documentation in `doc_md`

2. **`dbt_bronze_layer_test_alert_layer`** (Bronze Layer Testing DAG):
   - **Purpose**: Dedicated DAG for bronze layer testing and monitoring
   - **Schedule**: Every 30 minutes
   - **Tasks**:
     - `log_start`: Logs pipeline start time
     - `dbt_run_bronze`: Runs bronze models
     - `dbt_test_bronze`: Tests bronze models
     - `log_complete`: Logs completion with execution metrics
   - **Features**:
     - Pipeline logging with execution time tracking
     - Alert testing capability
     - XCom integration for data passing between tasks

3. **`data_quality_dag`** (Data Quality Validation):
   - **Purpose**: Separate DAG for data quality checks
   - **Features**: Comprehensive data validation workflows

**Utility Modules (`dags/utils/`):**
- **`alerting.py`**: AlertManager class for failure notifications
  - Supports Slack webhook integration
  - Formats error messages with context
  - Handles alert failures gracefully
- **`logging_utils.py`**: DataOpsLogger for structured logging
  - Event logging
  - Metric tracking
  - Execution time measurement

**Logs:**
- **Purpose**: Contains Airflow execution logs
- **Usage**: Debugging and monitoring task execution
- **Location**: `airflow/logs/` organized by DAG ID and run ID

#### 2. DBT Components

**Bronze Layer (`models/bronze/`):**
- **Purpose**: First layer - Extract and stage raw data from source systems
- **Models Implemented**:
  - `brnz_customers.sql`: Customer data from AdventureWorks with person information joined
  - `brnz_products.sql`: Product data with subcategory information
  - `brnz_sales_orders.sql`: Sales order header and detail combined
  - `brnz_territory.sql`: Sales territory information
- **Materialization**: Views (for flexibility and freshness)
- **Features**:
  - Basic column renaming and standardization
  - Source freshness checks configured (warn after 12h, error after 24h)
  - Comprehensive schema tests (unique, not_null, accepted_values)
  - All columns documented with descriptions

**Silver Layer (`models/silver/`):**
- **Purpose**: Second layer - Business logic transformations and data cleaning
- **Models Implemented**:
  - `slvr_customers.sql`: Cleaned customer data with null handling and full name concatenation
  - `slvr_products.sql`: Standardized product data with default values for missing fields
  - `slvr_sales_orders.sql`: Enhanced sales orders with calculated fields (gross_amount, effective_unit_price, has_discount, line_net) and joined with products, customers, and territory
- **Materialization**: Tables (for performance)
- **Features**:
  - Data quality filters (e.g., `order_qty > 0`, `unit_price >= 0`)
  - Calculated business metrics
  - Referential integrity through joins
  - Comprehensive testing on key columns

**Gold Layer (`models/gold/`):**
- **Purpose**: Final layer - Business-ready analytical marts
- **Models Implemented**:
  - `gld_customer_metrics.sql`: Customer-level KPIs (total orders, revenue, net revenue, average order value, first/last order dates)
  - `gld_product_performance.sql`: Product-level metrics (total quantity sold, revenue, profit margin percentage)
  - `gld_sales_summary.sql`: Daily sales aggregations by territory, category, and subcategory
- **Materialization**: Tables (optimized for querying)
- **Features**:
  - Aggregated metrics and KPIs
  - Multi-dimensional analysis (by date, territory, product category)
  - Performance optimized for BI tools
  - Comprehensive data quality tests

- **dbt_project.yml**:
  - Purpose: DBT project configuration
  - Contents:
    - Project name and version
    - Model configurations
    - Materialization settings
    - Custom macro configurations

- **packages.yml**:
  - Purpose: Manages external DBT packages
  - Current Packages:
    - dbt-utils: Provides additional SQL macros and functions
  - Usage: Install packages using `dbt deps`

- **profiles.yml**:
  - Purpose: Database connection configuration
  - Contents:
    - Connection credentials
    - Target database settings
    - Environment-specific configurations

#### 3. Docker Components
- **docker-compose.yml**:
  - Purpose: Container orchestration
  - Services Defined:
    1. **airflow-webserver**: Web interface for Airflow
       - Port: 8080
       - Usage: Monitor and manage DAGs

    2. **airflow-scheduler**: Airflow task scheduler
       - Purpose: Executes DAGs based on schedule
       - Dependencies: PostgreSQL for metadata

    3. **postgres**: Airflow metadata database
       - Purpose: Stores Airflow state and history
       - Port: 5432

    4. **sqlserver**: Source database
       - Purpose: Stores raw data
       - Port: 1433
       - Database: AdventureWorks

    5. **dbt**: DBT transformation container
       - Purpose: Executes DBT commands
       - Mounts: ./dbt directory for access to models

#### 4. Testing Framework

**Schema Tests:**
- Primary key tests: `unique` and `not_null` on all primary keys
- Foreign key tests: `relationships` tests for referential integrity
- Data type tests: `dbt_expectations.expect_column_values_to_be_of_type`
- Accepted values: Business rule validation (e.g., EmailPromotion values: 0, 1, 2)
- Unique combinations: `dbt_utils.unique_combination_of_columns` for composite keys

**Custom Generic Tests (`tests/generic/`):**
- `test_positive_values.sql`: Ensures numeric values are non-negative
- `test_no_future_dates.sql`: Validates dates are not in the future
- `test_valid_email.sql`: Email format validation (if applicable)

**Custom Data Quality Tests (`tests/data_quality/`):**
- `test_positive_revenue.sql`: Ensures revenue calculations are positive
- `test_profit_margin_range.sql`: Validates profit margins are within acceptable range
- `test_no_duplicate_orders.sql`: Ensures no duplicate order entries
- `test_order_customer_consistency.sql`: Validates order-customer relationships

**Source Freshness Checks:**
- Configured for all source tables in `src_adventureworks.yml`
- Warning threshold: 12 hours
- Error threshold: 24 hours
- Uses `ModifiedDate` as the freshness field

## Container Workflow
1. **Data Flow**:
   ```
   SQL Server (source) → DBT (transformation) → SQL Server (transformed)
   ```

2. **Process Flow**:
   ```
   Airflow Scheduler → Triggers DBT Container → Runs Models → Updates Status
   ```

3. **Monitoring Flow**:
   ```
   Airflow UI → View Logs → Check Task Status → Monitor Transformations
   ```

## Step-by-Step Implementation Guide

### 1. Initial Setup

1.1. Clone the repository:
```bash
git clone <repository-url>
cd dataops_lab
```

1.2. Create necessary directories:
```bash
mkdir -p airflow/dags airflow/logs airflow/plugins dbt/models/{bronze,silver,gold} dbt/tests/{generic,data_quality}
```

### 2. Docker Configuration

2.1. Create `docker-compose.yml` with the following services:
- Airflow Webserver
- Airflow Scheduler
- PostgreSQL (Airflow metadata database)
- SQL Server (Source database)
- DBT container

2.2. Build custom Docker images:
```bash
docker-compose build
```

### 3. DBT Configuration

3.1. Configure DBT project (`dbt_project.yml`):
```yaml
name: 'dbt_sqlserver_project'
version: '1.0.0'
config-version: 2
profile: 'default'

model-paths: ["models"]
test-paths: ["tests"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
    - "target"
    - "dbt_packages"
    - "logs"

models:
  dbt_sqlserver_project:
    staging:
      materialized: view
    intermediate:
      materialized: table
    marts:
      materialized: table
```

3.2. Configure DBT profiles (`profiles.yml`):
```yaml
default:
  target: dev
  outputs:
    dev:
      type: sqlserver
      driver: 'ODBC Driver 17 for SQL Server'
      server: sqlserver
      port: 1433
      database: AdventureWorks
      schema: dbo
      user: sa
      password: YourStrong@Passw0rd
      threads: 4
```

3.3. Install DBT packages (`packages.yml`):
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
```

### 4. Model Development

**4.1. Bronze Layer Models:**

Bronze models extract and stage raw data from AdventureWorks. Example: `brnz_sales_orders.sql`:

```sql
with sales_order_header as (
    select
        SalesOrderID as sales_order_id,
        OrderDate as order_date,
        DueDate as due_date,
        ShipDate as ship_date,
        Status as status,
        OnlineOrderFlag as online_order_flag,
        CustomerID as customer_id,
        SalesPersonID as sales_person_id,
        TerritoryID as territory_id,
        TaxAmt as tax_amount,
        Freight as freight_amount,
        SubTotal as subtotal_amount,
        TotalDue as total_due_amount,
        ModifiedDate as last_modified_date
    from {{ source('adventureworks', 'SalesOrderHeader') }}
),
sales_order_detail as (
    select
        SalesOrderDetailID as order_detail_id,
        SalesOrderID as sales_order_id,
        ProductID as product_id,
        OrderQty as order_qty,
        UnitPrice as unit_price,
        UnitPriceDiscount as unit_price_discount,
        LineTotal as line_total
    from {{ source('adventureworks', 'SalesOrderDetail') }}
)

select
    h.sales_order_id,
    h.order_date,
    h.due_date,
    h.ship_date,
    h.status,
    h.customer_id,
    h.sales_person_id,
    h.territory_id,
    h.tax_amount,
    h.freight_amount,
    h.subtotal_amount,
    h.total_due_amount,
    h.last_modified_date,
    d.order_detail_id,
    d.product_id,
    d.order_qty,
    d.unit_price,
    d.unit_price_discount,
    d.line_total
from sales_order_header h
left join sales_order_detail d
    on h.sales_order_id = d.sales_order_id
```

**4.2. Silver Layer Models:**

Silver models apply business logic and data cleaning. Example: `slvr_sales_orders.sql`:

```sql
{{
    config(
        materialized='table'
    )
}}

with bronze_sales as (
    select * from {{ ref('brnz_sales_orders') }}
),
products as (
    select * from {{ ref('slvr_products') }}
),
customers as (
    select * from {{ ref('slvr_customers') }}
),
territory as (
    select * from {{ ref('brnz_territory') }}
),

cleaned as (
    select
        sales_order_id,
        order_detail_id,
        order_date,
        -- Calculated fields
        unit_price * order_qty as gross_amount,
        line_total / nullif(order_qty, 0) as effective_unit_price,
        case 
            when unit_price_discount > 0 then 1
            else 0
        end as has_discount,
        (unit_price * order_qty) * (1 - coalesce(unit_price_discount, 0)) as line_net,
        case 
            when online_order_flag = 1 then 'Online'
            else 'Offline'
        end as order_channel,
        -- ... other fields
    from bronze_sales
    where order_qty > 0
        and unit_price >= 0
)

select
    c.*,
    p.product_name,
    p.category_id,
    p.subcategory_id,
    p.subcategory_name,
    p.list_price,
    cust.full_name as customer_name,
    t.territory_name,
    t.territory_group
from cleaned c
left join products p on c.product_id = p.product_id
left join customers cust on c.customer_id = cust.customer_id
left join territory t on c.territory_id = t.territory_id
```

**4.3. Gold Layer Models:**

Gold models create business-ready analytical marts. Example: `gld_customer_metrics.sql`:

```sql
{{
    config(
        materialized='table'
    )
}}

with customers as (
    select * from {{ ref('slvr_customers') }}
),
sales as (
    select * from {{ ref('slvr_sales_orders') }}
),

customer_sales as (
    select
        c.customer_id,
        c.full_name,
        c.territory_id,
        s.territory_group,
        count(distinct s.sales_order_id) as total_orders,
        sum(s.line_total) as total_revenue,
        sum(s.line_net) as net_revenue,
        sum(s.order_qty) as total_items_purchased,
        avg(nullif(s.line_total,0)) as avg_order_value,
        min(s.order_date) as first_order_date,
        max(s.order_date) as last_order_date,
        sum(case when s.has_discount = 1 then 1 else 0 end) as orders_with_discount
    from customers c
    left join sales s
        on c.customer_id = s.customer_id
    group by c.customer_id, c.full_name, c.territory_id, s.territory_group
)

select * from customer_sales
```

**4.4. Schema Tests Configuration:**

Example from `bronze/schema.yml`:

```yaml
version: 2

models:
  - name: brnz_customers
    description: "Bronze layer customer data from AdventureWorks"
    columns:
      - name: CustomerID
        description: "Primary key for customer"
        tests:
          - unique
          - not_null
          - dbt_expectations.expect_column_values_to_be_of_type:
              column_type: int
      - name: EmailPromotion
        description: "Email promotion preference"
        tests:
          - accepted_values:
              values: [0, 1, 2]
```

### 5. Airflow DAG Configuration

**Main DAG Implementation (`airflow/dags/dbt_dag.py`):**

The main DAG orchestrates the three-layer transformation pipeline:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from utils.alerting import AlertManager

def notify_failure(context):
    """Send notification on task failure"""
    alert_manager = AlertManager()
    alert_manager.alert_pipeline_failure(
        dag_id=context["dag"].dag_id,
        task_id=context["task_instance"].task_id,
        error_message=str(context.get("exception", "Unknown error")),
    )

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": notify_failure,
}

with DAG(
    dag_id="dbt_transform_bronze_silver_gold",
    default_args=default_args,
    description="Run dbt models layer by layer (bronze → silver → gold)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "sqlserver"],
) as dag:

    # Bronze Layer
    dbt_run_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command="docker exec dbt dbt run --select path:models/bronze",
    )

    # Silver Layer
    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command="docker exec dbt dbt run --select path:models/silver",
    )

    # Gold Layer
    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command="docker exec dbt dbt run --select path:models/gold",
    )

    # Tests
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="docker exec dbt dbt test",
    )

    # Task dependencies: Bronze → Silver → Gold → Test
    dbt_run_bronze >> dbt_run_silver >> dbt_run_gold >> dbt_test
```

**Key Features:**
- **Layer-by-layer execution**: Ensures proper data dependencies (Bronze → Silver → Gold → Test)
- **Error handling**: Automatic retries (2 attempts with 2-minute delay)
- **Alerting**: Failure notifications via AlertManager integration
- **Documentation**: Comprehensive DAG documentation in `doc_md`
- **Scheduling**: Daily execution (`@daily`) with no catchup

### 6. Starting the Project

6.1. Initialize the containers:
```bash
docker-compose up -d
```

6.2. Install DBT dependencies:
```bash
docker-compose exec dbt dbt deps
```

6.3. Run DBT models:
```bash
docker-compose exec dbt dbt run
```

6.4. Test DBT models:
```bash
docker-compose exec dbt dbt test
```

### 7. Accessing Services

- **Airflow UI**: http://localhost:8080
  - Username: `admin`
  - Password: `admin`
  - Features:
    - View DAG status and execution history
    - Monitor task logs and failures
    - Trigger DAGs manually
    - View task dependencies in Graph view

- **SQL Server**:
  - Host: `localhost`
  - Port: `1433`
  - Username: `sa`
  - Password: `YourStrong@Passw0rd`
  - Database: `AdventureWorks2014`
  - Schemas:
    - `bronze`: Bronze layer models (views)
    - `silver`: Silver layer models (tables)
    - `gold`: Gold layer models (tables)

### 8. Running the Pipeline

**8.1. Manual Execution via Airflow UI:**
1. Navigate to http://localhost:8080
2. Find the `dbt_transform_bronze_silver_gold` DAG
3. Click the "Play" button to trigger manually
4. Monitor execution in the Graph view

**8.2. Manual Execution via Command Line:**
```bash
# Run bronze layer
docker compose exec dbt dbt run --select path:models/bronze

# Run silver layer
docker compose exec dbt dbt run --select path:models/silver

# Run gold layer
docker compose exec dbt dbt run --select path:models/gold

# Run all tests
docker compose exec dbt dbt test
```

**8.3. View Model Lineage:**
```bash
docker compose exec dbt dbt docs generate
docker compose exec dbt dbt docs serve --port 8081
```
Then access http://localhost:8081 to view interactive documentation and lineage graphs.

## Why Containers?

We use containers for several important reasons:

1. **Isolation**: Each service runs in its own container, preventing conflicts between dependencies and ensuring consistent environments.

2. **Reproducibility**: Docker ensures that the development, testing, and production environments are identical.

3. **Scalability**: Containers can be easily scaled up or down based on workload requirements.

4. **Version Control**: Container configurations are version-controlled, making it easy to track changes and roll back if needed.

5. **Portability**: The project can run on any system that supports Docker, regardless of the underlying OS or infrastructure.

## Best Practices

1. **Version Control**
   - Keep all code in version control
   - Use meaningful commit messages
   - Create branches for new features

2. **Testing**
   - Write tests for all DBT models
   - Test data quality and business logic
   - Run tests before deploying changes

3. **Documentation**
   - Document all models and transformations
   - Keep README up to date
   - Use clear naming conventions

4. **Security**
   - Never commit sensitive credentials
   - Use environment variables for secrets
   - Regularly update dependencies

## Implementation Summary

### Part 1: DBT Data Models (Completed)

**Bronze Layer (5 models):**
- ✅ `brnz_customers`: Customer data with person information
- ✅ `brnz_products`: Product data with subcategory joins
- ✅ `brnz_sales_orders`: Combined sales order header and detail
- ✅ `brnz_territory`: Sales territory information
- ✅ Source freshness checks configured for all sources
- ✅ Comprehensive column documentation
- ✅ Schema tests (unique, not_null, accepted_values)

**Silver Layer (3 models):**
- ✅ `slvr_customers`: Cleaned customer data with null handling
- ✅ `slvr_products`: Standardized product data with defaults
- ✅ `slvr_sales_orders`: Enhanced sales orders with calculated fields
- ✅ Business logic transformations implemented
- ✅ Data quality filters applied
- ✅ Referential integrity through joins

**Gold Layer (3 models):**
- ✅ `gld_customer_metrics`: Customer-level KPIs and metrics
- ✅ `gld_product_performance`: Product-level sales and profitability metrics
- ✅ `gld_sales_summary`: Daily sales aggregations by dimensions
- ✅ Optimized for analytical queries
- ✅ Comprehensive aggregations and calculations

**Testing:**
- ✅ Schema tests on all primary keys and critical columns
- ✅ Custom generic tests (positive_values, no_future_dates, valid_email)
- ✅ Custom data quality tests (4 business logic tests)
- ✅ Source freshness monitoring configured

### Part 3: Airflow Orchestration (Completed)

**DAGs Implemented:**
- ✅ `dbt_transform_bronze_silver_gold`: Main pipeline DAG
  - Daily schedule
  - Proper task dependencies (Bronze → Silver → Gold → Test)
  - Error handling with retries (2 attempts, 2-minute delay)
  - Failure alerting via AlertManager
- ✅ `dbt_bronze_layer_test_alert_layer`: Bronze layer testing DAG
  - 30-minute schedule
  - Pipeline logging with execution metrics
  - Alert testing capability
- ✅ `data_quality_dag`: Data quality validation DAG

**Features:**
- ✅ Task dependencies properly configured (Bronze → Silver → Gold → Test)
- ✅ Error handling with retries (2 attempts, 2-minute delay)
- ✅ Failure notifications via AlertManager integration
- ✅ Comprehensive DAG documentation
- ✅ Scheduling configured (daily and periodic)
- ✅ Logging utilities for monitoring (DataOpsLogger)

## Troubleshooting

Common issues and solutions:

1. **Container Connection Issues**
   - Check if all containers are running: `docker compose ps`
   - Verify network connectivity: `docker network ls`
   - Ensure Docker socket is mounted: `/var/run/docker.sock`

2. **DBT Errors**
   - Check `profiles.yml` configuration
   - Verify database credentials
   - Run `dbt debug` for diagnostics
   - Check source freshness: `dbt source freshness`

3. **Airflow DAG Issues**
   - Check DAG syntax in Airflow UI
   - Verify task dependencies in Graph view
   - Check Airflow logs: `airflow/logs/`
   - Ensure DAG files are in `airflow/dags/` directory
   - Verify Docker exec permissions (Docker API version compatibility)

4. **Docker API Version Error**
   - Error: "client version 1.41 is too old. Minimum supported API version is 1.44"
   - Solution: Rebuild Airflow image with updated Dockerfile that installs `docker-ce-cli` from Docker's official repository
   - Run: `docker compose build airflow-webserver airflow-scheduler`
   - Restart: `docker compose up -d airflow-webserver airflow-scheduler`

5. **DBT Model Compilation Errors**
   - Check model SQL syntax
   - Verify source definitions in `sources.yml`
   - Ensure all referenced models exist
   - Check schema names match between models

6. **Test Failures**
   - Review test output in Airflow logs
   - Check data quality issues in source data
   - Verify test logic matches business rules
   - Run tests individually: `dbt test --select test_name`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For additional support:
- Check the project issues
- Contact the development team
- Refer to DBT and Airflow documentation
