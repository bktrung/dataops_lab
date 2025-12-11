FROM apache/airflow:2.7.1-python3.9

# Switch to root to install system packages
USER root

# Install ODBC driver and dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        curl \
        gnupg2 \
        ca-certificates \
        lsb-release \
        git \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        docker-ce-cli \
        msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add airflow user to docker group (create group if missing)
RUN groupadd -f docker && usermod -aG docker airflow

# Switch back to airflow user
USER airflow

# Install Python packages
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt \
    && pip install apache-airflow-providers-docker \
    && pip install dbt-sqlserver

# Create DBT directory
RUN mkdir -p /opt/airflow/dbt

# Copy DAGs and plugins
COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root plugins/ /opt/airflow/plugins/

# Copy DBT project - FIXED: Use a volume mount instead of COPY
# The DBT directory will be mounted at runtime via docker-compose.yml 