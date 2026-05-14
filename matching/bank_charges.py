from utils.helper import mark_group_reconciled


BANK_CHARGES = {
    (49000, 100000): 47.2,
    (100001, 199999): 14.16,
    (200000, 499999): 23.60,
    (500000, 999999999): 47.20
}



def get_charge(amount):

    amount = abs(amount)

    for rng, charge in BANK_CHARGES.items():

        if rng[0] <= amount <= rng[1]:
            return charge

    return None

def run_bank_charges(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    keywords = ["RTGS", "NEFT", "IMPS"]

    for bank_idx, bank_row in unmatched_bank.iterrows():

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        particulars = str(bank_row["normalized_particulars"])

        if not any(k in particulars for k in keywords):
            continue

        expected_charge = get_charge(bank_row["normalized_amount"])

        if expected_charge is None:
            continue

        matches = unmatched_ledger[
            abs(
                unmatched_ledger["normalized_amount"]
                - (bank_row["normalized_amount"] - expected_charge)
            ) < 1
        ]

        if len(matches) == 1:

            ledger_idx = matches.index[0]

            bank_df, ledger_df = mark_group_reconciled(
                bank_df,
                ledger_df,
                bank_idx,
                ledger_idx,
                match_rule="BANK_CHARGE",
                match_type="CHARGE_MATCH",
                remarks="Matched after adjusting bank charges",
                confidence=80
            )

    return bank_df, ledger_df
