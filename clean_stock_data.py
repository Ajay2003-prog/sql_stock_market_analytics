import pandas as pd
import os

OUTPUT_FOLDER = "cleaned_data"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

FILES = {
    "Bajaj Auto.csv": "bajaj_auto.csv",
    "Eicher Motors.csv": "eicher_motors.csv",
    "Hero Motocorp.csv": "hero_motocorp.csv",
    "Infosys.csv": "infosys.csv",
    "TCS.csv": "tcs.csv",
    "TVS Motors.csv": "tvs_motors.csv"
}

for input_file, output_file in FILES.items():
    print(f"\nProcessing: {input_file}")

    df = pd.read_csv(input_file)

    # Clean column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    # Convert date
    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True,
        errors="coerce"
    )

    # Convert numeric columns
    numeric_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "wap",
        "no_of_shares",
        "no_of_trades",
        "total_turnover",
        "deliverable_qty",
        "pct_deli_qty"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Remove duplicate rows
    duplicate_rows = df.duplicated().sum()

    if duplicate_rows > 0:
        df = df.drop_duplicates()

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    # Create analysis columns
    df["spread_high_low"] = (
        df["high_price"] - df["low_price"]
    )

    df["spread_close_open"] = (
        df["close_price"] - df["open_price"]
    )

    # Save cleaned CSV
    output_path = os.path.join(
        OUTPUT_FOLDER,
        output_file
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Duplicates removed: {duplicate_rows}")
    print(f"Missing values: {df.isna().sum().sum()}")
    print(
        f"Date range: "
        f"{df['date'].min().date()} → "
        f"{df['date'].max().date()}"
    )
    print(f"Saved: {output_path}")

print("\n" + "=" * 50)
print("DATA CLEANING COMPLETED")
print("=" * 50)