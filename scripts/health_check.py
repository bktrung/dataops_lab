#!/usr/bin/env python3
"""
System health check script
Checks the health of all components in the data pipeline
"""

import sys
import subprocess
import requests
import pyodbc
from datetime import datetime


class HealthCheck:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def print_header(self, text):
        print(f"\n{'=' * 60}")
        print(f"  {text}")
        print(f"{'=' * 60}\n")

    def check_docker_containers(self):
        """Check if Docker containers are running"""
        print("🐳 Checking Docker containers...")

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], capture_output=True, text=True, check=True
            )

            containers = result.stdout.strip().split("\n")
            required_containers = ["airflow-scheduler", "airflow-webserver", "sqlserver", "dbt"]

            running_containers = [c.split("\t")[0] for c in containers]

            for req in required_containers:
                found = any(req in container for container in running_containers)
                if found:
                    print(f"  ✅ {req} is running")
                    self.checks_passed += 1
                else:
                    print(f"  ❌ {req} is not running")
                    self.checks_failed += 1

            return self.checks_failed == 0

        except Exception as e:
            print(f"  ❌ Error checking Docker: {e}")
            self.checks_failed += 1
            return False

    def check_airflow_webserver(self):
        """Check if Airflow webserver is accessible"""
        print("\n🌐 Checking Airflow webserver...")

        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ Airflow webserver is healthy")
                self.checks_passed += 1
                return True
            else:
                print(f"  ❌ Airflow webserver returned status {response.status_code}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"  ❌ Cannot reach Airflow webserver: {e}")
            self.checks_failed += 1
            return False

    def check_database_connection(self):
        """Check SQL Server database connection"""
        print("\n🗄️  Checking database connection...")

        try:
            conn_string = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=localhost;"
                "DATABASE=AdventureWorks2014;"
                "UID=sa;"
                "PWD=YourStrong@Passw0rd;"
                "TrustServerCertificate=yes;"
            )

            conn = pyodbc.connect(conn_string, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]

            print("  ✅ Database connection successful")
            print(f"     Version: {version.split('\\n')[0]}")

            conn.close()
            self.checks_passed += 1
            return True

        except Exception as e:
            print(f"  ❌ Database connection failed: {e}")
            self.checks_failed += 1
            return False

    def check_dbt_models(self):
        """Check if DBT models exist and are compiled"""
        print("\n📊 Checking DBT models...")

        try:
            # Check if models directory exists
            result = subprocess.run(["ls", "-la", "dbt/models/"], capture_output=True, text=True)

            if result.returncode == 0:
                print("  ✅ DBT models directory exists")
                self.checks_passed += 1
            else:
                print("  ❌ DBT models directory not found")
                self.checks_failed += 1
                return False

            # Check if models can be compiled
            result = subprocess.run(
                ["docker", "exec", "dbt_airflow_project-dbt-1", "dbt", "compile"],
                capture_output=True,
                text=True,
                cwd=".",
            )

            if "Completed successfully" in result.stdout:
                print("  ✅ DBT models compile successfully")
                self.checks_passed += 1
                return True
            else:
                print("  ⚠️  DBT compilation has warnings")
                self.warnings += 1
                return True

        except Exception as e:
            print(f"  ❌ Error checking DBT models: {e}")
            self.checks_failed += 1
            return False

    def check_disk_space(self):
        """Check available disk space"""
        print("\n💾 Checking disk space...")

        try:
            result = subprocess.run(["df", "-h", "."], capture_output=True, text=True)

            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                parts = lines[1].split()
                usage = parts[4].rstrip("%")

                if int(usage) < 80:
                    print(f"  ✅ Disk usage: {usage}% (healthy)")
                    self.checks_passed += 1
                elif int(usage) < 90:
                    print(f"  ⚠️  Disk usage: {usage}% (warning)")
                    self.warnings += 1
                else:
                    print(f"  ❌ Disk usage: {usage}% (critical)")
                    self.checks_failed += 1

                return True

        except Exception as e:
            print(f"  ⚠️  Could not check disk space: {e}")
            self.warnings += 1
            return True

    def check_recent_pipeline_runs(self):
        """Check if pipelines have run recently"""
        print("\n⏰ Checking recent pipeline runs...")

        try:
            # Check DBT run results
            result = subprocess.run(["cat", "dbt/target/run_results.json"], capture_output=True, text=True)

            if result.returncode == 0:
                print("  ✅ Recent DBT run results found")
                self.checks_passed += 1
                return True
            else:
                print("  ⚠️  No recent DBT run results")
                self.warnings += 1
                return True

        except Exception as e:
            print(f"  ⚠️  Could not check pipeline runs: {e}")
            self.warnings += 1
            return True

    def run_all_checks(self):
        """Run all health checks"""
        self.print_header("DataOps Health Check")
        print(f"Timestamp: {datetime.now().isoformat()}\n")

        # Run all checks
        self.check_docker_containers()
        self.check_airflow_webserver()
        self.check_database_connection()
        self.check_dbt_models()
        self.check_disk_space()
        self.check_recent_pipeline_runs()

        # Print summary
        self.print_header("Health Check Summary")
        print(f"✅ Checks Passed: {self.checks_passed}")
        print(f"❌ Checks Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print(f"\nTotal Checks: {self.checks_passed + self.checks_failed + self.warnings}")

        # Determine overall health
        if self.checks_failed == 0:
            if self.warnings == 0:
                print("\n🎉 System is HEALTHY")
                return 0
            else:
                print("\n⚠️  System is HEALTHY with warnings")
                return 0
        else:
            print("\n🚨 System has ISSUES that need attention")
            return 1


def main():
    health_check = HealthCheck()
    exit_code = health_check.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
