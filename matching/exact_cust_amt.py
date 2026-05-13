from utils.helper import mark_group_reconciled

def run_exact_cust_amt(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    for bank_idx, bank_row in unmatched_bank.iterrows():

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        matches = unmatched_ledger[
            (
                unmatched_ledger["normalized_cust_name"]
                == bank_row["normalized_cust_name"]
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
                match_rule="CUST_AMT",
                match_type="EXACT_MATCH",
                remarks="Matched using customer and amount"
            )

    return bank_df, ledger_df
