from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = "logs.db"
DATA_DIR = Path("data")

TABLES = [
    "SigninLogs",
    "EmailEvents",
    "DeviceLogonEvents",
    "DeviceProcessEvents",
    "DeviceNetworkEvents",
]


def main():
    db = duckdb.connect(DB_PATH)

    for table in TABLES:
        csv_path = DATA_DIR / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"missing generated dataset: {csv_path}")

        df = pd.read_csv(csv_path)
        db.execute(f'DROP TABLE IF EXISTS "{table}"')
        db.register("incoming_df", df)
        db.execute(f'CREATE TABLE "{table}" AS SELECT * FROM incoming_df')
        db.unregister("incoming_df")

        count = db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        print(f"loaded {table}: {count} rows")

    db.close()
    print("database ready")


if __name__ == "__main__":
    main()
