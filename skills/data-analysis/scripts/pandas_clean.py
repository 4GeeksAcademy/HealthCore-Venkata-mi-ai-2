"""
Safe snippet for basic pandas cleaning. Copy and adapt for your dataset.
Run: python pandas_clean.py  (ensure pandas is installed)
"""
from __future__ import annotations

import sys

import pandas as pd


def main() -> int:
    try:
        df = pd.read_csv("data.csv")  # or read_json, read_excel
    except FileNotFoundError:
        print("Could not find data.csv.", file=sys.stderr)
        return 1
    except OSError:
        print("Could not read data.csv.", file=sys.stderr)
        return 1
    except ValueError:
        print("Could not parse data.csv.", file=sys.stderr)
        return 1

    print("df_shape", df.shape)
    print("df_dtypes", df.dtypes)

    df = df.dropna(axis=1, how="all")
    print("df_shape_after_drop_all_null_cols", df.shape)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    print("df_columns", list(df.columns))

    before = len(df)
    df = df.drop_duplicates()
    print("rows_dropped_duplicates", before - len(df))
    print("df_head", df.head())
    return 0


if __name__ == "__main__":
    sys.exit(main())
