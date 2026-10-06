import sqlite3
import pandas as pd
import os

DB = "stock_market.db"
DATA_FOLDER = "cleaned_data"

FILES = {
    "bajaj_auto": "bajaj_auto.csv",
    "eicher_motors": "eicher_motors.csv",
    "hero_motocorp": "hero_motocorp.csv",
    "infosys": "infosys.csv",
    "tcs": "tcs.csv",
    "tvs_motors": "tvs_motors.csv"
}

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)

for table, file in FILES.items():
    path = os.path.join(DATA_FOLDER, file)

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(df["date"])

    df.to_sql(
        table,
        conn,
        if_exists="replace",
        index=False
    )

    print(f"{table}: {len(df)} rows")

conn.close()

print("\n" + "=" * 50)
print("DATABASE CREATED SUCCESSFULLY")
print("=" * 50)
print(f"Database: {DB}")