from utils.helper import mark_group_reconciled

AMOUNT_TOLERANCE = 0.01


def run_contra_matching(bank_df, ledger_df):
    """
    Detect ledger transactions that cancel each other out (nullified/contra).
    Works on unmatched ledger transactions only.
    """

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    # Group by customer or account
    group_cols = ["normalized_cust_name", "acc_no"]

    for _, group in unmatched_ledger.groupby(group_cols):

        if len(group) < 2:
            continue

        # Check all combinations of two or more transactions
        txn_indices = list(group.index)
        n = len(txn_indices)

        # Simple 2-transaction contra check
        for i in range(n):
            for j in range(i + 1, n):
                amt_i = round(group.loc[txn_indices[i], "normalized_amount"], 2)
                amt_j = round(group.loc[txn_indices[j], "normalized_amount"], 2)

                # Opposite side
                if abs(amt_i + amt_j) <= AMOUNT_TOLERANCE:

                    # Mark these two as nullified
                    bank_df, ledger_df = mark_group_reconciled(
                        bank_df,
                        ledger_df,
                        bank_indices=[],
                        ledger_indices=[txn_indices[i], txn_indices[j]],
                        match_rule="CONTRA_MATCH",
                        match_type="CONTRA",
                        remarks="Ledger contra/nullified transaction",
                        confidence=95,
                        reco_status="CONTRA_MATCH"
                    )

        # Optional: multi-entry nullification
        # Check if sum of 3+ transactions = 0
        # Can extend later using combination_matcher
        # for larger groups
    return bank_df, ledger_df