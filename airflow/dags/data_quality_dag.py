from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from great_expectations.data_context import DataContext

default_args = {
    "owner": "dataops",
    "depends_on_past": False,
    "email_on_failure": False,
    "email": [],
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "data_quality_validation",
    default_args=default_args,
    description="Run Great Expectations data quality validations",
    schedule_interval="0 */6 * * *",  # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["data-quality", "great-expectations"],
)


def run_ge_checkpoint(checkpoint_name, **context):
    """Run a Great Expectations checkpoint"""

    # Use the GE project mounted from the dbt folder
    context_root_dir = "/opt/airflow/dbt/great_expectations"
    data_context = DataContext(context_root_dir=context_root_dir)

    print(f"Running checkpoint: {checkpoint_name}")
    result = data_context.run_checkpoint(checkpoint_name=checkpoint_name)

    # Fail the task if validation failed
    if not result["success"]:
        # Raise an AirflowException (or generic Exception) to mark task as failed
        raise Exception(f"Data quality check failed for checkpoint: {checkpoint_name}")

    # DO NOT return the CheckpointResult object (not JSON-serializable)
    # Optionally return a simple message or nothing
    return f"Checkpoint {checkpoint_name} succeeded"


# Tasks
validate_customers = PythonOperator(
    task_id="validate_customer_data",
    python_callable=run_ge_checkpoint,
    op_kwargs={"checkpoint_name": "customer_checkpoint"},
    dag=dag,
)

validate_orders = PythonOperator(
    task_id="validate_sales_order_data",
    python_callable=run_ge_checkpoint,
    op_kwargs={"checkpoint_name": "sales_order_checkpoint"},
    dag=dag,
)

generate_docs = BashOperator(
    task_id="generate_data_docs",
    # GE prompts "Would you like to proceed? [Y/n]"; pipe "Y" to make it non-interactive in Airflow
    bash_command=(
        "cd /opt/airflow/dbt/great_expectations && "
        "echo 'Y' | great_expectations docs build"
    ),
    dag=dag,
)

# Dependencies
[validate_customers, validate_orders] >> generate_docs
