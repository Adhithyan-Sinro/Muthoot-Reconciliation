import pandas as pd

from utils.combination_matcher import (
    find_matching_combinations
)
from utils.helper import mark_group_reconciled


BANK_CHARGES = {
    (49000, 100000): 4.72,
    (100001, 199999): 14.16,
    (200000, 499999): 23.60,
    (500000, 999999999): 47.20
}

BANK_TRANSFER_KEYWORDS = ["RTGS", "NEFT", "IMPS", ]
AMOUNT_TOLERANCE = 1
DATE_TOLERANCE = 3
MAX_CONSOLIDATED_CHARGE_SIZE = 5


def adjusted_amount_after_charge(amount, charge):

    if amount < 0:
        return -(abs(amount) - charge)

    return amount - charge


def get_charge(amount):

    amount = abs(amount)

    for rng, charge in BANK_CHARGES.items():

        if rng[0] <= amount <= rng[1]:
            return charge

    return None


def contains_keyword(value, keywords):

    value = str(value).upper()

    return any(
        keyword in value
        for keyword in keywords
    )


def has_value(value):

    return str(value).strip() != ""


def same_identifier(row, other_row):

    row_cheque = str(row["normalized_cheque_no"]).strip()
    other_cheque = str(other_row["normalized_cheque_no"]).strip()

    if has_value(row_cheque) and row_cheque == other_cheque:
        return True

    row_customer = str(row["normalized_cust_name"]).strip()
    other_customer = str(other_row["normalized_cust_name"]).strip()

    if has_value(row_customer) and row_customer == other_customer:
        return True

    return False


def is_bank_transfer(row):

    particulars = str(
        row.get(
            "particulars",
            row.get("normalized_particulars", "")
        )
    ).upper()

    return contains_keyword(
        particulars,
        BANK_TRANSFER_KEYWORDS
    )


def with_adjusted_charge_amounts(bank_rows):

    bank_rows = bank_rows.copy()

    bank_rows["expected_bank_charge"] = bank_rows[
        "normalized_amount"
    ].apply(get_charge)

    bank_rows = bank_rows[
        bank_rows["expected_bank_charge"].notna()
    ]

    bank_rows["charge_adjusted_amount"] = bank_rows.apply(
        lambda row: adjusted_amount_after_charge(
            row["normalized_amount"],
            row["expected_bank_charge"]
        ),
        axis=1
    )

    return bank_rows


def filter_by_date_tolerance(candidate_bank, ledger_row):

    if pd.isna(ledger_row["txn_date"]):
        return candidate_bank

    return candidate_bank[
        candidate_bank["txn_date"].notna()
        & (
            abs(
                (
                    candidate_bank["txn_date"]
                    - ledger_row["txn_date"]
                ).dt.days
            ) <= DATE_TOLERANCE
        )
    ]


def run_bank_charges(bank_df, ledger_df):

    unmatched_bank = bank_df[
        bank_df["is_reconciled"] == False
    ]

    for bank_idx, bank_row in unmatched_bank.iterrows():

        unmatched_ledger = ledger_df[
            ledger_df["is_reconciled"] == False
        ]

        particulars = str(
            bank_row.get(
                "particulars",
                bank_row.get("particulars", "")
            )
        ).upper()

        if not contains_keyword(
            particulars,
            BANK_TRANSFER_KEYWORDS
        ):
            continue

        bank_amount = bank_row["normalized_amount"]

        expected_charge = get_charge(bank_amount)

        if expected_charge is None:
            continue

        amount_after_charge = adjusted_amount_after_charge(
            bank_amount,
            expected_charge
        )

        bank_cheque_no = str(
            bank_row["normalized_cheque_no"]
        ).strip()

        bank_customer = str(
            bank_row["normalized_cust_name"]
        ).strip()

        amount_matches = unmatched_ledger[
            abs(
                unmatched_ledger["normalized_amount"]
                - amount_after_charge
            ) <= AMOUNT_TOLERANCE
        ]

        cheque_matches = pd.Series(
            False,
            index=amount_matches.index
        )

        customer_matches = pd.Series(
            False,
            index=amount_matches.index
        )

        if has_value(bank_cheque_no):
            cheque_matches = (
                amount_matches["normalized_cheque_no"]
                .astype(str)
                .str.strip()
                == bank_cheque_no
            )

        if has_value(bank_customer):
            customer_matches = (
                amount_matches["normalized_cust_name"]
                .astype(str)
                .str.strip()
                == bank_customer
            )

        matches = amount_matches[
            cheque_matches | customer_matches
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
                remarks=(
                    f"Matched after bank charge adjustment "
                    f"of {expected_charge}"
                ),
                confidence=80
            )

    unmatched_ledger = ledger_df[
        ledger_df["is_reconciled"] == False
    ]

    for ledger_idx, ledger_row in unmatched_ledger.iterrows():

        unmatched_bank = bank_df[
            bank_df["is_reconciled"] == False
        ]

        charge_bank = unmatched_bank[
            unmatched_bank.apply(is_bank_transfer, axis=1)
        ]

        charge_bank = with_adjusted_charge_amounts(charge_bank)
        charge_bank = filter_by_date_tolerance(
            charge_bank,
            ledger_row
        )

        if charge_bank.empty:
            continue

        anchor_indices = [
            bank_idx
            for bank_idx, bank_row in charge_bank.iterrows()
            if same_identifier(bank_row, ledger_row)
        ]

        if not anchor_indices:
            continue

        candidate_indices = list(charge_bank.index)

        candidate_amounts = {
            bank_idx: charge_bank.loc[
                bank_idx,
                "charge_adjusted_amount"
            ]
            for bank_idx in candidate_indices
        }

        matched_combo = find_matching_combinations(
            candidate_indices=candidate_indices,
            candidate_amounts=candidate_amounts,
            target_amount=ledger_row["normalized_amount"],
            max_combination_size=MAX_CONSOLIDATED_CHARGE_SIZE,
            tolerance=AMOUNT_TOLERANCE
        )

        if not matched_combo:
            continue

        if not any(
            bank_idx in anchor_indices
            for bank_idx in matched_combo
        ):
            continue

        split_size = len(matched_combo)
        total_charge = charge_bank.loc[
            list(matched_combo),
            "expected_bank_charge"
        ].sum()

        bank_df, ledger_df = mark_group_reconciled(
            bank_df,
            ledger_df,
            bank_indices=list(matched_combo),
            ledger_indices=ledger_idx,
            match_rule="BANK_CHARGE",
            match_type="CONSOLIDATED_CHARGE_MATCH",
            remarks=(
                f"Consolidated bank charge adjustment "
                f"of {total_charge}"
            ),
            confidence=75
        )

        for bank_idx in matched_combo:
            bank_df.loc[
                bank_idx,
                "charge_adjusted_amount"
            ] = charge_bank.loc[
                bank_idx,
                "charge_adjusted_amount"
            ]

            bank_df.loc[
                bank_idx,
                "bank_charge_amount"
            ] = charge_bank.loc[
                bank_idx,
                "expected_bank_charge"
            ]

            bank_df.loc[
                bank_idx,
                "bank_charge_group_size"
            ] = split_size

        ledger_df.loc[
            ledger_idx,
            "bank_charge_group_size"
        ] = split_size

    return bank_df, ledger_df
