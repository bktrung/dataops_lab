from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='dbt_transform_bronze_silver_gold',
    default_args=default_args,
    description='Run dbt models layer by layer (bronze → silver → gold)',
    schedule_interval=timedelta(hours=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['dbt', 'sqlserver'],
) as dag:

    # --- Bronze Layer ---
    dbt_run_bronze = BashOperator(
        task_id='dbt_run_bronze',
        bash_command='docker exec dbt_airflow_project-dbt-1 dbt run --select path:models/bronze',
    )

    # --- Silver Layer ---
    dbt_run_silver = BashOperator(
        task_id='dbt_run_silver',
        bash_command='docker exec dbt_airflow_project-dbt-1 dbt run --select path:models/silver',
    )

    # --- Gold Layer ---
    dbt_run_gold = BashOperator(
        task_id='dbt_run_gold',
        bash_command='docker exec dbt_airflow_project-dbt-1 dbt run --select path:models/gold',
    )

    # --- Tests (after all transformations) ---
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='docker exec dbt_airflow_project-dbt-1 dbt test',
    )

    # --- Task dependencies: Bronze → Silver → Gold → Test ---
    dbt_run_bronze >> dbt_run_silver >> dbt_run_gold >> dbt_test
