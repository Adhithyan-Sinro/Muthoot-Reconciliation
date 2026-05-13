import pandas as pd

from utils.helper import mark_group_reconciled


def run_delayed_accounting(bank_df, ledger_df, days=3):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    for bank_idx, bank_row in unmatched_bank.iterrows():

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        if pd.isna(bank_row["txn_date"]):
            continue

        amount_matches = unmatched_ledger[
            (unmatched_ledger["normalized_amount"] == bank_row["normalized_amount"])
            & unmatched_ledger["txn_date"].notna()
        ]

        date_diffs = (
            amount_matches["txn_date"] - bank_row["txn_date"]
        ).abs().dt.days

        matches = amount_matches[date_diffs <= days]

        if len(matches) == 1:

            ledger_idx = matches.index[0]

            delayed_days = int(date_diffs.loc[ledger_idx])

            bank_df, ledger_df = mark_group_reconciled(
                bank_df,
                ledger_df,
                bank_idx,
                ledger_idx,
                match_rule="DELAYED_ACCOUNTING",
                match_type="DELAYED_MATCH",
                remarks=f"Delayed accounting by {delayed_days} days",
                confidence=85
            )

    return bank_df, ledger_df
