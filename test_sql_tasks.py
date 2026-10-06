import sqlite3
import pandas as pd
from sql_tasks import TASKS

conn = sqlite3.connect("stock_market.db")

print("SQL TASK VALIDATION")
print("=" * 50)

for name, sql in TASKS.items():
    try:
        df = pd.read_sql_query(sql, conn)
        print(f"✓ {name}: {len(df)} rows")
    except Exception as e:
        print(f"✗ {name}: {e}")

conn.close()