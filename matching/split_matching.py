from utils.combination_matcher import (
    find_matching_combinations
)
from utils.helper import mark_group_reconciled


MAX_SPLIT_SIZE = 3
DATE_TOLERANCE = 3


def run_split_matching(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    for ledger_idx, ledger_row in unmatched_ledger.iterrows():

        ledger_amount = ledger_row["normalized_amount"]

        # ----------------------------------------
        # Candidate bank rows
        # ----------------------------------------

        candidate_bank = unmatched_bank[

            (
                unmatched_bank["normalized_cust_name"]
                == ledger_row["normalized_cust_name"]
            )

            |

            (
                unmatched_bank["normalized_cheque_no"]
                == ledger_row["normalized_cheque_no"]
            )

        ]

        # ----------------------------------------
        # Date tolerance
        # ----------------------------------------

        candidate_bank = candidate_bank[

            abs(
                (
                    candidate_bank["txn_date"]
                    - ledger_row["txn_date"]
                ).dt.days
            ) <= DATE_TOLERANCE

        ]

        candidate_indices = list(candidate_bank.index)

        candidate_amounts = {
            idx: candidate_bank.loc[idx, "normalized_amount"]
            for idx in candidate_indices
        }

        matched_combo = find_matching_combinations(
            candidate_indices=candidate_indices,
            candidate_amounts=candidate_amounts,
            target_amount=ledger_amount,
            max_combination_size=MAX_SPLIT_SIZE
        )

        if matched_combo:

            split_size = len(matched_combo)

            bank_df, ledger_df = mark_group_reconciled(
                bank_df,
                ledger_df,
                list(matched_combo),
                ledger_idx,
                match_rule="SPLIT_MATCH",
                match_type="ONE_TO_MANY",
                remarks=(
                    f"Split match with "
                    f"{split_size} bank entries"
                ),
                confidence=85
            )

            for bank_idx in matched_combo:

                bank_df.loc[
                    bank_idx,
                    "split_group_size"
                ] = split_size

            ledger_df.loc[
                ledger_idx,
                "split_group_size"
            ] = split_size

    return bank_df, ledger_df
