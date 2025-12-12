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
    doc_md="""
    ### DBT layer orchestration
    - Runs bronze → silver → gold layers, then tests.
    - Runs inside the `dbt` container via simple `docker exec dbt dbt ...` commands.
    - Scheduled daily; retries are enabled for basic error handling.
    - Add Airflow alerting/email/Slack on failure at the DAG or task level if needed.
    """,
) as dag:
    # --- Bronze Layer ---
    dbt_run_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command="docker exec dbt dbt run --select path:models/bronze",
    )

    # --- Silver Layer ---
    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command="docker exec dbt dbt run --select path:models/silver",
    )

    # --- Gold Layer ---
    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command="docker exec dbt dbt run --select path:models/gold",
    )

    # --- Tests (after all transformations) ---
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="docker exec dbt dbt test",
    )

    # Set task dependencies: Bronze → Silver → Gold → Test
    dbt_run_bronze >> dbt_run_silver >> dbt_run_gold >> dbt_test
