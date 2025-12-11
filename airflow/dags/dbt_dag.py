from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_transform_bronze_silver_gold",
    default_args=default_args,
    description="Run dbt models layer by layer (bronze → silver → gold)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["dbt", "sqlserver"],
    doc_md="""
    ### DBT layer orchestration
    - Runs bronze → silver → gold layers, then tests.
    - Uses Airflow Variable `DBT_TARGET` (default `dev`) for target selection.
    - Runs inside the `dbt` container via simple `docker exec dbt dbt ...` commands.
    - Scheduled daily; retries are enabled for basic error handling.
    - Add Airflow alerting/email/Slack on failure at the DAG or task level if needed.
    """,
) as dag:

    # Keep commands simple and consistent
    dbt_target = "{{ var.value.DBT_TARGET | default('dev') }}"

    # --- Bronze Layer ---
    dbt_run_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command=(
            f"docker exec dbt dbt run --select path:models/bronze --target {dbt_target}"
        ),
    )

    # --- Silver Layer ---
    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=(
            f"docker exec dbt dbt run --select path:models/silver --target {dbt_target}"
        ),
    )

    # --- Gold Layer ---
    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=(
            f"docker exec dbt dbt run --select path:models/gold --target {dbt_target}"
        ),
    )

    # --- Tests (after all transformations) ---
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"docker exec dbt dbt test --target {dbt_target}",
    )

    # Set task dependencies: Bronze → Silver → Gold → Test
    dbt_run_bronze >> dbt_run_silver >> dbt_run_gold >> dbt_test
