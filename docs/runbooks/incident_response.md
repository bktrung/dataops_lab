# Incident Response Runbook

## Overview
This runbook provides step-by-step procedures for responding to data pipeline incidents.

## Severity Levels

### P0 - Critical
- Production data pipeline completely down
- Data corruption affecting business decisions
- Security breach

**Response Time:** Immediate
**Escalation:** Notify management immediately

### P1 - High
- Partial pipeline failure
- Data quality issues affecting reports
- Performance degradation

**Response Time:** Within 1 hour
**Escalation:** Notify team lead

### P2 - Medium
- Non-critical test failures
- Minor data quality issues
- Slow pipeline execution

**Response Time:** Within 4 hours
**Escalation:** Standard team notification

### P3 - Low
- Documentation issues
- Non-blocking warnings
- Optimization opportunities

**Response Time:** Within 24 hours
**Escalation:** None required

## Incident Response Procedures

### 1. Data Pipeline Failure

**Symptoms:**
- Airflow DAG failing
- DBT models not running
- No data updates

**Diagnosis Steps:**

```bash
# 1. Check Airflow logs
docker logs dbt_airflow_project-airflow-scheduler-1 --tail 100

# 2. Check DBT logs
docker exec dbt_airflow_project-dbt-1 cat /usr/app/dbt/logs/dbt.log

# 3. Check database connectivity
docker exec dbt_airflow_project-dbt-1 dbt debug

# 4. Check recent changes
git log --oneline -10
```

**Resolution Steps:**

```bash
# 1. Identify failed task
# Check Airflow UI: http://localhost:8080

# 2. Review error messages
# Look for specific error in logs

# 3. Fix the issue
# Apply fix based on error

# 4. Clear failed task and retry
# In Airflow UI: Clear task and re-run

# 5. Verify fix
docker exec dbt_airflow_project-dbt-1 dbt run --select <model_name>
```

### 2. Data Quality Issue

**Symptoms:**
- DBT tests failing
- Unexpected data values
- Missing data

**Diagnosis Steps:**

```bash
# 1. Run specific test
cd dbt
dbt test --select <model_name>

# 2. Check test results
cat target/run_results.json | jq '.results[] | select(.status == "fail")'

# 3. Query the data
docker exec -it dbt_airflow_project-sqlserver-1 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "YourStrong@Passw0rd" \
  -Q "SELECT TOP 100 * FROM dbo.brnz_customers ORDER BY ModifiedDate DESC"

# 4. Check data lineage
dbt docs generate
# Open docs and review lineage
```

**Resolution Steps:**

```bash
# 1. Identify root cause
# Review source data and transformations

# 2. Fix data or model
# Update SQL or fix source data

# 3. Re-run affected models
dbt run --select <model_name>+

# 4. Verify fix
dbt test --select <model_name>
```

### 3. Performance Degradation

**Symptoms:**
- Slow pipeline execution
- Timeouts
- High resource usage

**Diagnosis Steps:**

```bash
# 1. Check execution times
cat dbt/target/run_results.json | jq '.results[] | {name: .unique_id, time: .execution_time}'

# 2. Check resource usage
docker stats

# 3. Check database performance
# Review SQL Server query plans

# 4. Identify slow models
dbt run --select <model_name> --debug
```

**Resolution Steps:**

```bash
# 1. Optimize slow models
# Add indexes, optimize SQL

# 2. Implement incremental models
# Convert full-refresh to incremental

# 3. Adjust resources
# Increase threads or memory

# 4. Test improvements
dbt run --select <model_name>
```

## Rollback Procedures

### Quick Rollback

Note: In this project, the DBT target names used by CI/CD are `staging` and `prod` (not `production`).

```bash
# 1. Identify backup to restore
ls -la backups/

# 2. Run rollback script
./scripts/rollback.sh <target> <backup_directory>

# Examples:
./scripts/rollback.sh staging backups/staging_YYYYMMDD_HHMMSS
./scripts/rollback.sh prod backups/production_YYYYMMDD_HHMMSS

# 3. Verify rollback
dbt test --target <target>
```

### Git Rollback

```bash
# 1. Identify commit to revert
git log --oneline -10

# 2. Revert commit
git revert <commit_hash>

# 3. Deploy reverted code
./scripts/deploy.sh <environment> <target>
```

## Post-Incident Actions

### 1. Document the Incident

Create incident report in `incidents/` directory:

```bash
cp docs/templates/incident_report_template.md incidents/$(date +%Y-%m-%d)-incident-name.md
```

### 2. Update Runbooks

Document any new procedures discovered during incident response.

### 3. Implement Preventive Measures

- Add tests to catch similar issues
- Improve monitoring
- Update alerts
- Enhance documentation

### 4. Conduct Post-Mortem

Schedule team meeting to review:
- What happened
- Why it happened
- How we responded
- What we learned
- How to prevent it

## Contact Information

**On-Call Rotation:**
- Week 1: Team Member A
- Week 2: Team Member B
- Week 3: Team Member C

**Escalation:**
- Team Lead: [email]
- Manager: [email]
- VP Engineering: [email]

**External Contacts:**
- Database Admin: [email]
- Infrastructure Team: [email]
- Security Team: [email]
```
