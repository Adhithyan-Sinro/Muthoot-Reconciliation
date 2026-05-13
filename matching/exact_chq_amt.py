from utils.helper import mark_group_reconciled


def run_exact_chq_amt(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    for bank_idx, bank_row in unmatched_bank.iterrows():

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        matches = unmatched_ledger[
            (
                unmatched_ledger["normalized_cheque_no"]
                == bank_row["normalized_cheque_no"]
            )
            & (
                unmatched_ledger["normalized_amount"]
                == bank_row["normalized_amount"]
            )
        ]


        if len(matches) == 1:

            ledger_idx = matches.index[0]

            bank_df, ledger_df = mark_group_reconciled(
                bank_df,
                ledger_df,
                bank_idx,
                ledger_idx,
                match_rule="CHQ_AMT",
                match_type="EXACT_MATCH",
                remarks="Matched using cheque and amount"
            )

    return bank_df, ledger_df
