from utils.helper import mark_group_reconciled
from utils.combination_matcher import (
    find_matching_combinations
)


MAX_COMBINATION_SIZE = 3
AMOUNT_TOLERANCE = 0.01


def _has_value(value):
    return value is not None and str(value).strip() != ""


def run_difference_matching(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    # -------------------------------------------------
    # Loop through unmatched bank transactions
    # -------------------------------------------------

    for bank_idx, bank_row in unmatched_bank.iterrows():

        if bank_df.loc[bank_idx, "is_reconciled"]:
            continue

        bank_amount = bank_row["normalized_amount"]
        customer_name = bank_row["normalized_cust_name"]
        cheque_no = bank_row["normalized_cheque_no"]

        if not _has_value(customer_name) and not _has_value(cheque_no):
            continue

        # -------------------------------------------------
        # Find possible ledger candidates
        # Same customer OR same cheque
        # But amount different
        # -------------------------------------------------

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        candidate_mask = False

        if _has_value(customer_name):
            candidate_mask = (
                candidate_mask
                | (
                    unmatched_ledger["normalized_cust_name"]
                    == customer_name
                )
            )

        if _has_value(cheque_no):
            candidate_mask = (
                candidate_mask
                | (
                    unmatched_ledger["normalized_cheque_no"]
                    == cheque_no
                )
            )

        candidate_ledger = unmatched_ledger[candidate_mask]

        candidate_ledger = candidate_ledger[

            candidate_ledger["normalized_amount"]
            != bank_amount

        ]

        # -------------------------------------------------
        # Try each candidate ledger
        # -------------------------------------------------

        for ledger_idx, ledger_row in candidate_ledger.iterrows():

            ledger_amount = ledger_row["normalized_amount"]

            difference = round(
                abs(bank_amount - ledger_amount),
                2
            )

            # -------------------------------------------------
            # Determine which side needs balancing
            # -------------------------------------------------

            if abs(bank_amount) > abs(ledger_amount):

                # Need more amount in ledger

                balancing_pool = ledger_df[
                    (ledger_df["is_reconciled"] == False)
                    & (ledger_df.index != ledger_idx)
                ]

            else:

                # Need more amount in bank

                balancing_pool = bank_df[
                    (bank_df["is_reconciled"] == False)
                    & (bank_df.index != bank_idx)
                ]

            # -------------------------------------------------
            # Build candidate amounts
            # -------------------------------------------------

            candidate_indices = list(balancing_pool.index)
            candidate_amounts = (
                balancing_pool["normalized_amount"]
                .abs()
                .to_dict()
            )

            matched_combo = find_matching_combinations(

                candidate_indices=candidate_indices,

                candidate_amounts=candidate_amounts,

                target_amount=difference,

                max_combination_size=MAX_COMBINATION_SIZE,

                tolerance=AMOUNT_TOLERANCE
            )

            # -------------------------------------------------
            # If balancing transactions found
            # -------------------------------------------------

            if matched_combo:

                # ---------------------------------------------
                # Main pair reconciliation
                # ---------------------------------------------

                bank_df, ledger_df = mark_group_reconciled(

                    bank_df,
                    ledger_df,

                    bank_idx,
                    ledger_idx,

                    match_rule="DIFFERENCE_MATCH",

                    match_type="PARTIAL_MATCH",

                    remarks=(
                        "Matched using "
                        "difference balancing"
                    ),

                    confidence=75
                )

                # ---------------------------------------------
                # Mark balancing transactions
                # ---------------------------------------------

                if abs(bank_amount) > abs(ledger_amount):

                    # balancing entries in ledger

                    for extra_ledger_idx in matched_combo:

                        bank_df, ledger_df = mark_group_reconciled(

                            bank_df,
                            ledger_df,

                            bank_idx,
                            extra_ledger_idx,

                            match_rule="DIFFERENCE_BALANCE",

                            match_type="GROUP_MATCH",

                            remarks=(
                                "Balanced difference "
                                "amount from ledger"
                            ),

                            confidence=70
                        )

                else:

                    # balancing entries in bank

                    for extra_bank_idx in matched_combo:

                        bank_df, ledger_df = mark_group_reconciled(

                            bank_df,
                            ledger_df,

                            extra_bank_idx,
                            ledger_idx,

                            match_rule="DIFFERENCE_BALANCE",

                            match_type="GROUP_MATCH",

                            remarks=(
                                "Balanced difference "
                                "amount from bank"
                            ),

                            confidence=70
                        )

                break

    return bank_df, ledger_df
