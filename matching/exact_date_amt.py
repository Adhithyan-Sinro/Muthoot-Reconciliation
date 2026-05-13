import os

import pandas as pd

from utils.helper import mark_group_reconciled


def _debug_enabled():
    return os.getenv("MATCH_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y"
    }


def _debug_target_matches(bank_row):
    debug_date = os.getenv("MATCH_DEBUG_DATE")
    debug_amount = os.getenv("MATCH_DEBUG_AMOUNT")

    if debug_date:
        target_date = pd.to_datetime(debug_date, errors="coerce").normalize()

        if pd.isna(target_date) or bank_row["txn_date"] != target_date:
            return False

    if debug_amount:
        try:
            if float(bank_row["normalized_amount"]) != float(debug_amount):
                return False
        except (TypeError, ValueError):
            return False

    return True


def _print_debug_rows(title, df):
    columns = [
        column
        for column in [
            "txn_date",
            "normalized_amount",
            "credit_amount",
            "debit_amount",
            "cust_name",
            "cheque_no",
            "particulars",
            "is_reconciled"
        ]
        if column in df.columns
    ]

    print(title)

    if df.empty:
        print("  No rows found")
        return

    print(df[columns].head(20).to_string())


def _normalize_dtypes(bank_df, ledger_df):
    for df in [bank_df, ledger_df]:
        df["normalized_amount"] = pd.to_numeric(
            df["normalized_amount"], errors="coerce"
        )
        df["txn_date"] = pd.to_datetime(
            df["txn_date"], errors="coerce"
        ).dt.normalize()

    return bank_df, ledger_df


def run_exact_date_amt(bank_df, ledger_df, debug=None):

    if debug is None:
        debug = _debug_enabled()

    bank_df, ledger_df = _normalize_dtypes(bank_df, ledger_df)

    unmatched_bank_indices = bank_df[
        bank_df["is_reconciled"] == False
    ].index

    for bank_idx in unmatched_bank_indices:

        # Re-check against the live bank_df since a prior iteration
        # may have already reconciled this row
        if bank_df.at[bank_idx, "is_reconciled"]:
            continue

        bank_row = bank_df.loc[bank_idx]

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        matches = unmatched_ledger[
            (unmatched_ledger["txn_date"] == bank_row["txn_date"])
            & (
                unmatched_ledger["normalized_amount"]
                == bank_row["normalized_amount"]
            )
        ]

        should_debug = debug and _debug_target_matches(bank_row)

        if should_debug:
            print("\n[DEBUG exact_date_amt]")
            print(
                "Bank index:",
                bank_idx,
                "| txn_date:",
                bank_row["txn_date"],
                "| normalized_amount:",
                bank_row["normalized_amount"]
            )
            print(
                "Bank normalized_amount dtype:",
                bank_df["normalized_amount"].dtype
            )
            print(
                "Ledger normalized_amount dtype:",
                ledger_df["normalized_amount"].dtype
            )
            print("Unmatched ledger rows available:", len(unmatched_ledger))

            same_date = unmatched_ledger[
                unmatched_ledger["txn_date"] == bank_row["txn_date"]
            ]
            same_amount = unmatched_ledger[
                unmatched_ledger["normalized_amount"]
                == bank_row["normalized_amount"]
            ]

            _print_debug_rows("Ledger rows with same txn_date:", same_date)
            _print_debug_rows("Ledger rows with same normalized_amount:", same_amount)
            _print_debug_rows("Final date + amount matches:", matches)

        if len(matches) == 1:

            ledger_idx = matches.index[0]

            bank_df, ledger_df = mark_group_reconciled(
                bank_df,
                ledger_df,
                bank_idx,
                ledger_idx,
                match_rule="DATE_AMT",
                match_type="EXACT_MATCH",
                remarks="Matched using date and amount"
            )

            if should_debug:
                print("Marked MATCHED with ledger index:", ledger_idx)

        elif should_debug:
            print("Not marked because match count is:", len(matches))

    return bank_df, ledger_df
