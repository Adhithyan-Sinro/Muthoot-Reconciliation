from utils.helper import mark_group_reconciled


BANK_KEYWORDS = [
    "MUTHOOT",
    "SELF",
    "CHQ TRANSFER",
    "CHEQUE TRANSFER"
]

LEDGER_KEYWORDS = [
    "CASH",
    "CHQ",
    "TRANSFER"
]

AMOUNT_TOLERANCE = 1
DATE_TOLERANCE = 5


def contains_keyword(text, keywords):

    text = str(text).upper()

    return any(
        keyword in text
        for keyword in keywords
    )


def run_cheque_cash_matching(
    bank_df,
    ledger_df
):

    # -----------------------------------------
    # Unmatched pools only
    # -----------------------------------------

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    # -----------------------------------------
    # Loop bank transactions
    # -----------------------------------------

    for bank_idx, bank_row in unmatched_bank.iterrows():

        bank_particulars = str(
            bank_row["normalized_particulars"]
        ).upper()

        # -------------------------------------
        # Bank keyword validation
        # -------------------------------------

        if not contains_keyword(
            bank_particulars,
            BANK_KEYWORDS
        ):
            continue

        bank_amount = abs(
            bank_row["normalized_amount"]
        )

        bank_cheque = str(
            bank_row["normalized_cheque_no"]
        ).strip()

        bank_customer = str(
            bank_row["normalized_cust_name"]
        ).strip()

        # -------------------------------------
        # Find ledger candidates
        # -------------------------------------

        candidate_ledger = unmatched_ledger[

            (
                abs(
                    abs(
                        unmatched_ledger[
                            "normalized_amount"
                        ]
                    )
                    - bank_amount
                ) <= AMOUNT_TOLERANCE
            )

        ]

        # -------------------------------------
        # Date tolerance
        # -------------------------------------

        candidate_ledger = candidate_ledger[

            abs(
                (
                    candidate_ledger["txn_date"]
                    - bank_row["txn_date"]
                ).dt.days
            ) <= DATE_TOLERANCE

        ]

        # -------------------------------------
        # Customer / cheque validation
        # -------------------------------------

        candidate_ledger = candidate_ledger[

            (
                candidate_ledger[
                    "normalized_cheque_no"
                ].astype(str)
                == bank_cheque
            )

            |

            (
                candidate_ledger[
                    "normalized_cust_name"
                ].astype(str)
                == bank_customer
            )

        ]

        # -------------------------------------
        # Ledger narration validation
        # -------------------------------------

        candidate_ledger = candidate_ledger[

            candidate_ledger[
                "normalized_particulars"
            ].apply(

                lambda x:
                contains_keyword(
                    x,
                    LEDGER_KEYWORDS
                )

            )

        ]

        # -------------------------------------
        # Match found
        # -------------------------------------

        if len(candidate_ledger) == 1:

            ledger_idx = candidate_ledger.index[0]

            remarks = (
                "Bank marked as cheque transfer "
                "while ledger marked as cash"
            )

            bank_df, ledger_df = mark_group_reconciled(

                bank_df,
                ledger_df,

                bank_indices=[bank_idx],

                ledger_indices=[ledger_idx],

                match_rule="CHEQUE_CASH_MATCH",

                match_type="BUSINESS_RULE_MATCH",

                remarks=remarks,

                confidence=90,

                reco_status="MATCHED"
            )

            # ---------------------------------
            # Additional tagging
            # ---------------------------------

            bank_df.loc[
                bank_idx,
                "cheque_cash_tag"
            ] = "CHEQUE_TO_CASH"

            ledger_df.loc[
                ledger_idx,
                "cheque_cash_tag"
            ] = "CHEQUE_TO_CASH"

    print(
        "Cheque cash matching completed"
    )

    return bank_df, ledger_df