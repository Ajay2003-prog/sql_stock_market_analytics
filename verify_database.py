import sqlite3

conn = sqlite3.connect("stock_market.db")

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("DATABASE TABLES")
print("=" * 40)

for table in tables:
    name = table[0]

    count = conn.execute(
        f"SELECT COUNT(*) FROM {name}"
    ).fetchone()[0]

    columns = conn.execute(
        f"PRAGMA table_info({name})"
    ).fetchall()

    print(f"{name}: {count} rows, {len(columns)} columns")

conn.close()