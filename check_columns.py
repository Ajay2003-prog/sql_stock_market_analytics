import sqlite3

conn = sqlite3.connect("stock_market.db")

tables = [
    "bajaj_auto",
    "eicher_motors",
    "hero_motocorp",
    "infosys",
    "tcs",
    "tvs_motors"
]

for table in tables:
    print(f"\n{table}")
    print("=" * 40)

    columns = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    for column in columns:
        print(column[1])

conn.close()