#!/usr/bin/env python3
"""
Database Connection Diagnostic Script for QuickBite Food Delivery System.
"""
import sys
import pymysql
from pymysql.cursors import DictCursor
from config import Config

def main():
    print("=" * 65)
    print("  QuickBite Food Delivery System - Diagnostic Tool")
    print("=" * 65)
    print(f"Host:     {Config.DB_HOST}")
    print(f"Port:     {Config.DB_PORT}")
    print(f"User:     {Config.DB_USER}")
    print(f"Password: {'*' * len(Config.DB_PASSWORD) if Config.DB_PASSWORD else '(empty)'}")
    print(f"Database: {Config.DB_NAME}")
    print("-" * 65)

    # 1. Test Server Connectivity
    print("[1/3] Testing MySQL Server connectivity...")
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            cursorclass=DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version;")
            row = cursor.fetchone()
            print(f"✅ Connected to MySQL {row['version']} successfully.")
        conn.close()
    except Exception as e:
        print(f"❌ Failed to connect to MySQL server: {e}")
        sys.exit(1)

    # 2. Check Database existence
    print(f"\n[2/3] Checking if database '{Config.DB_NAME}' exists...")
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            cursorclass=DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{Config.DB_NAME}';")
            if not cursor.fetchone():
                print(f"⚠️  Database '{Config.DB_NAME}' does not exist yet. Run `python setup_db.py` to create it.")
                conn.close()
                return
        print(f"✅ Database '{Config.DB_NAME}' exists.")
        conn.close()
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        sys.exit(1)

    # 3. Check Tables and Row Counts
    print("\n[3/3] Checking tables inside database...")
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [list(r.values())[0] for r in cursor.fetchall()]
            print(f"Found {len(tables)} tables: {tables}")
            for table in sorted(tables):
                cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{table}`;")
                cnt = cursor.fetchone()['cnt']
                print(f"  • {table}: {cnt} rows")
        conn.close()
        print("\n🎉 Connection test and schema check completed successfully!")
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
