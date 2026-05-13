from utils.helper import mark_group_reconciled


DATE_TOLERANCE = 7
AMOUNT_TOLERANCE = 0.01


def run_reversal_matching(bank_df, ledger_df):

    """
    Detect reversal transactions.

    Example:
    --------
    Debit 100
    Credit 100

    same customer / cheque
    opposite txn direction
    within date tolerance
    """

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    # -------------------------------------------------
    # BANK REVERSALS
    # -------------------------------------------------

    for bank_idx, bank_row in unmatched_bank.iterrows():

        bank_amount = round(
            bank_row["normalized_amount"],
            2
        )

        # ---------------------------------------------
        # Find opposite side transaction
        # ---------------------------------------------

        reversal_candidates = unmatched_bank[

            (
                unmatched_bank["normalized_cust_name"]
                == bank_row["normalized_cust_name"]
            )

            |

            (
                unmatched_bank["normalized_cheque_no"]
                == bank_row["normalized_cheque_no"]
            )

        ]

        reversal_candidates = reversal_candidates[

            reversal_candidates.index != bank_idx
        ]

        # ---------------------------------------------
        # Opposite amount
        # ---------------------------------------------

        reversal_candidates = reversal_candidates[

            abs(
                reversal_candidates["normalized_amount"]
                + bank_amount
            ) <= AMOUNT_TOLERANCE

        ]

        # ---------------------------------------------
        # Date tolerance
        # ---------------------------------------------

        reversal_candidates = reversal_candidates[

            abs(
                (
                    reversal_candidates["txn_date"]
                    - bank_row["txn_date"]
                ).dt.days
            ) <= DATE_TOLERANCE

        ]

        if len(reversal_candidates) >= 1:

            reversal_idx = reversal_candidates.index[0]

            remarks = (
                "Possible reversal transaction "
                "identified in bank"
            )

            bank_df, ledger_df = mark_group_reconciled(

                bank_df,
                ledger_df,

                bank_indices=[
                    bank_idx,
                    reversal_idx
                ],

                ledger_indices=[],

                match_rule="REVERSAL_MATCH",

                match_type="REVERSAL",

                remarks=remarks,

                confidence=80,

                reco_status="REVERSAL"
            )

    # -------------------------------------------------
    # LEDGER REVERSALS
    # -------------------------------------------------

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    for ledger_idx, ledger_row in unmatched_ledger.iterrows():

        ledger_amount = round(
            ledger_row["normalized_amount"],
            2
        )

        reversal_candidates = unmatched_ledger[

            (
                unmatched_ledger["normalized_cust_name"]
                == ledger_row["normalized_cust_name"]
            )

            |

            (
                unmatched_ledger["normalized_cheque_no"]
                == ledger_row["normalized_cheque_no"]
            )

        ]

        reversal_candidates = reversal_candidates[

            reversal_candidates.index != ledger_idx
        ]

        reversal_candidates = reversal_candidates[

            abs(
                reversal_candidates["normalized_amount"]
                + ledger_amount
            ) <= AMOUNT_TOLERANCE

        ]

        reversal_candidates = reversal_candidates[

            abs(
                (
                    reversal_candidates["txn_date"]
                    - ledger_row["txn_date"]
                ).dt.days
            ) <= DATE_TOLERANCE

        ]

        if len(reversal_candidates) >= 1:

            reversal_idx = reversal_candidates.index[0]

            remarks = (
                "Possible reversal transaction "
                "identified in ledger"
            )

            bank_df, ledger_df = mark_group_reconciled(

                bank_df,
                ledger_df,

                bank_indices=[],

                ledger_indices=[
                    ledger_idx,
                    reversal_idx
                ],

                match_rule="REVERSAL_MATCH",

                match_type="REVERSAL",

                remarks=remarks,

                confidence=80,

                reco_status="REVERSAL"
            )

    return bank_df, ledger_df