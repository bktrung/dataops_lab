#!/usr/bin/env python3
"""
Smoke tests for post-deployment validation
"""

import sys
import pyodbc
import argparse
from datetime import datetime


class SmokeTests:
    def __init__(self, server, database, user, password):
        self.conn_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={user};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = pyodbc.connect(self.conn_string)
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def test_table_exists(self, schema, table):
        """Test if a table exists"""
        query = f"""
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = '{table}'
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()

        if result[0] > 0:
            print(f"✅ Table {schema}.{table} exists")
            return True
        else:
            print(f"❌ Table {schema}.{table} not found")
            return False

    def test_table_has_data(self, schema, table, min_rows=1):
        """Test if a table has minimum number of rows"""
        query = f"SELECT COUNT(*) as cnt FROM {schema}.{table}"
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        row_count = result[0]

        if row_count >= min_rows:
            print(f"✅ Table {schema}.{table} has {row_count} rows (min: {min_rows})")
            return True
        else:
            print(f"❌ Table {schema}.{table} has {row_count} rows (expected min: {min_rows})")
            return False

    def test_no_nulls_in_column(self, schema, table, column):
        """Test that a column has no null values"""
        query = f"""
        SELECT COUNT(*) as null_count
        FROM {schema}.{table}
        WHERE {column} IS NULL
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        null_count = result[0]

        if null_count == 0:
            print(f"✅ Column {schema}.{table}.{column} has no nulls")
            return True
        else:
            print(f"❌ Column {schema}.{table}.{column} has {null_count} null values")
            return False

    def test_data_freshness(self, schema, table, date_column, max_age_hours=24):
        """Test that data is fresh"""
        query = f"""
        SELECT MAX({date_column}) as latest_date
        FROM {schema}.{table}
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        latest_date = result[0]

        if latest_date:
            age_hours = (datetime.now() - latest_date).total_seconds() / 3600
            if age_hours <= max_age_hours:
                print(f"✅ Data in {schema}.{table} is fresh (age: {age_hours:.1f}h)")
                return True
            else:
                print(f"❌ Data in {schema}.{table} is stale (age: {age_hours:.1f}h, max: {max_age_hours}h)")
                return False
        else:
            print(f"❌ No data found in {schema}.{table}")
            return False

    def run_all_tests(self):
        """Run all smoke tests"""
        print("\n🧪 Running smoke tests...\n")

        tests_passed = 0
        tests_failed = 0

        # Test 1: Check bronze tables exist
        if self.test_table_exists("dbo", "brnz_customers"):
            tests_passed += 1
        else:
            tests_failed += 1

        # Test 2: Check bronze tables have data
        if self.test_table_has_data("dbo", "brnz_customers", min_rows=100):
            tests_passed += 1
        else:
            tests_failed += 1

        # Test 3: Check for nulls in primary key
        if self.test_no_nulls_in_column("dbo", "brnz_customers", "CustomerID"):
            tests_passed += 1
        else:
            tests_failed += 1

        # Test 4: Check data freshness
        if self.test_data_freshness("dbo", "brnz_customers", "ModifiedDate", max_age_hours=168):
            tests_passed += 1
        else:
            tests_failed += 1

        # Summary
        print("\n Test Summary:")
        print(f"   Passed: {tests_passed}")
        print(f"   Failed: {tests_failed}")
        print(f"   Total: {tests_passed + tests_failed}")

        return tests_failed == 0

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


def main():
    parser = argparse.ArgumentParser(description="Run smoke tests")
    parser.add_argument("--server", default="localhost", help="SQL Server hostname")
    parser.add_argument("--database", default="AdventureWorks2014", help="Database name")
    parser.add_argument("--user", default="sa", help="Username")
    parser.add_argument("--password", default="YourStrong@Passw0rd", help="Password")

    args = parser.parse_args()

    # Run tests
    smoke_tests = SmokeTests(args.server, args.database, args.user, args.password)

    if not smoke_tests.connect():
        sys.exit(1)

    success = smoke_tests.run_all_tests()
    smoke_tests.close()

    if success:
        print("\n✅ All smoke tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some smoke tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
