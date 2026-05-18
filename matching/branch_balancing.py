import uuid

import pandas as pd

from utils.remark_builder import (
    branch_balanced,
    manual_review,
    soft_amount_match
)


AMOUNT_TOLERANCE = 0.01
DATE_TOLERANCE_DAYS = 3
MONTH_DATE_COLUMN = "txn_date"

BRANCH_COLUMN_CANDIDATES = [
    "branch_id",
    "branch_code",
    "branch",
    "branch_name",
    "br_code",
    "br_name",
    "office_id",
    "office_code",
    "office_name",
    "acc_no",
]


def _common_branch_columns(bank_df, ledger_df, branch_columns=None):
    if branch_columns:
        columns = [
            column
            for column in branch_columns
            if column in bank_df.columns and column in ledger_df.columns
        ]
        return columns

    return [
        column
        for column in BRANCH_COLUMN_CANDIDATES
        if column in bank_df.columns and column in ledger_df.columns
    ]


def _unmatched(df):
    return df[df["is_reconciled"] == False]


def _identifier_mismatch_details(bank_row, ledger_row):
    bank_customer = str(bank_row.get("normalized_cust_name", "")).strip()
    ledger_customer = str(ledger_row.get("normalized_cust_name", "")).strip()

    bank_cheque = str(bank_row.get("normalized_cheque_no", "")).strip()
    ledger_cheque = str(ledger_row.get("normalized_cheque_no", "")).strip()

    customer_mismatch = (
        (bank_customer or ledger_customer)
        and bank_customer != ledger_customer
    )

    cheque_mismatch = (
        (bank_cheque or ledger_cheque)
        and bank_cheque != ledger_cheque
    )

    if customer_mismatch and cheque_mismatch:
        return (
            True,
            "INTERNAL_ADJUSTMENT",
            "Customer and cheque differ between bank and ledger"
        )

    if customer_mismatch:
        return (
            True,
            "INTERNAL_ADJUSTMENT",
            "Customer differs between bank and ledger"
        )

    if cheque_mismatch:
        return (
            True,
            "POSSIBLE_MAPPING_ERROR",
            "Cheque differs between bank and ledger"
        )

    return False, None, None


def _date_diff_days(bank_row, ledger_row):
    bank_date = bank_row.get("txn_date")
    ledger_date = ledger_row.get("txn_date")

    if pd.isna(bank_date) or pd.isna(ledger_date):
        return None

    return abs((ledger_date - bank_date).days)


def _same_branch_mask(df, branch_values):
    mask = pd.Series(True, index=df.index)

    for column, value in branch_values.items():
        if pd.isna(value):
            mask = mask & df[column].isna()
        else:
            mask = mask & (df[column] == value)

    return mask


def _branch_label(branch_values):
    return ", ".join(
        f"{column}={value}"
        for column, value in branch_values.items()
    )


def _month_start(value):
    if pd.isna(value):
        return pd.NaT

    return pd.Timestamp(value).to_period("M").to_timestamp()


def _month_label(month_start):
    month_end = month_start + pd.offsets.MonthEnd(0)
    return (
        f"{month_start.strftime('%Y-%m-%d')} to "
        f"{month_end.strftime('%Y-%m-%d')}"
    )


def _same_month_mask(df, month_start):
    if pd.isna(month_start):
        return pd.Series(False, index=df.index)

    txn_months = df[MONTH_DATE_COLUMN].apply(_month_start)

    return txn_months == month_start


def _mark_soft_match(bank_df, ledger_df, bank_idx, ledger_idx, branch_label):
    group_id = str(uuid.uuid4())
    bank_amount = abs(bank_df.loc[bank_idx, "normalized_amount"])
    has_mismatch, match_type, exception_reason = _identifier_mismatch_details(
        bank_df.loc[bank_idx],
        ledger_df.loc[ledger_idx]
    )

    if not has_mismatch:
        return bank_df, ledger_df

    date_diff = _date_diff_days(
        bank_df.loc[bank_idx],
        ledger_df.loc[ledger_idx]
    )
    remarks = soft_amount_match(
        branch_label,
        bank_amount,
        date_diff
    )

    bank_df.loc[bank_idx, "reco_status"] = "SOFT_MATCH"
    bank_df.loc[bank_idx, "match_rule"] = "RESIDUAL_AMOUNT_MATCH"
    bank_df.loc[bank_idx, "match_type"] = match_type
    bank_df.loc[bank_idx, "remarks"] = remarks
    bank_df.loc[bank_idx, "confidence_score"] = 65
    bank_df.loc[bank_idx, "group_match_id"] = group_id
    bank_df.loc[bank_idx, "matched_ledger_ids"] = str(ledger_idx)
    bank_df.loc[bank_idx, "matched_amount"] = bank_amount
    bank_df.loc[bank_idx, "reconciliation_character"] = (
        "OPERATIONAL_ADJUSTMENT"
    )
    bank_df.loc[bank_idx, "requires_manual_review"] = True
    bank_df.loc[bank_idx, "exception_reason"] = exception_reason
    bank_df.loc[bank_idx, "is_reconciled"] = True

    ledger_amount = abs(ledger_df.loc[ledger_idx, "normalized_amount"])
    ledger_df.loc[ledger_idx, "reco_status"] = "SOFT_MATCH"
    ledger_df.loc[ledger_idx, "match_rule"] = "RESIDUAL_AMOUNT_MATCH"
    ledger_df.loc[ledger_idx, "match_type"] = match_type
    ledger_df.loc[ledger_idx, "remarks"] = remarks
    ledger_df.loc[ledger_idx, "confidence_score"] = 65
    ledger_df.loc[ledger_idx, "group_match_id"] = group_id
    ledger_df.loc[ledger_idx, "matched_bank_ids"] = str(bank_idx)
    ledger_df.loc[ledger_idx, "matched_amount"] = ledger_amount
    ledger_df.loc[ledger_idx, "reconciliation_character"] = (
        "OPERATIONAL_ADJUSTMENT"
    )
    ledger_df.loc[ledger_idx, "requires_manual_review"] = True
    ledger_df.loc[ledger_idx, "exception_reason"] = exception_reason
    ledger_df.loc[ledger_idx, "is_reconciled"] = True

    return bank_df, ledger_df


def _run_soft_amount_matches(
    bank_df,
    ledger_df,
    branch_columns,
    amount_tolerance,
    date_tolerance_days
):
    unmatched_bank = _unmatched(bank_df)

    for bank_idx, bank_row in unmatched_bank.iterrows():
        if bank_df.loc[bank_idx, "is_reconciled"]:
            continue

        branch_values = {
            column: bank_row[column]
            for column in branch_columns
        }

        candidate_ledger = ledger_df[
            (ledger_df["is_reconciled"] == False)
            & _same_branch_mask(ledger_df, branch_values)
            & (
                abs(
                    ledger_df["normalized_amount"]
                    - bank_row["normalized_amount"]
                ) <= amount_tolerance
            )
        ]

        if date_tolerance_days is not None:
            bank_date = bank_row.get("txn_date")

            if not pd.isna(bank_date):
                candidate_ledger = candidate_ledger[
                    candidate_ledger["txn_date"].notna()
                    & (
                        abs(
                            (
                                candidate_ledger["txn_date"]
                                - bank_date
                            ).dt.days
                        ) <= date_tolerance_days
                    )
                ]

        candidate_ledger = candidate_ledger[
            candidate_ledger.apply(
                lambda ledger_row: _identifier_mismatch_details(
                    bank_row,
                    ledger_row
                )[0],
                axis=1
            )
        ]

        if len(candidate_ledger) != 1:
            continue

        ledger_idx = candidate_ledger.index[0]
        bank_df, ledger_df = _mark_soft_match(
            bank_df,
            ledger_df,
            bank_idx,
            ledger_idx,
            _branch_label(branch_values)
        )

    return bank_df, ledger_df


def _set_branch_balanced_columns(
    df,
    indices,
    matched_ids_column,
    matched_ids,
    group_id,
    remarks,
    bank_total,
    ledger_total
):
    ids_text = ",".join(map(str, matched_ids))

    for idx in indices:
        df.loc[idx, "reco_status"] = "BRANCH_BALANCED_EXCEPTION"
        df.loc[idx, "match_rule"] = "BRANCH_BALANCING"
        df.loc[idx, "match_type"] = "BRANCH_BALANCED"
        df.loc[idx, "remarks"] = remarks
        df.loc[idx, "confidence_score"] = 55
        df.loc[idx, "group_match_id"] = group_id
        df.loc[idx, matched_ids_column] = ids_text
        df.loc[idx, "matched_amount"] = abs(
            df.loc[idx, "normalized_amount"]
        )
        df.loc[idx, "reconciliation_character"] = "BRANCH_LEVEL"
        df.loc[idx, "requires_manual_review"] = True
        df.loc[idx, "exception_reason"] = (
            "Branch residual totals balanced but transaction identity unknown"
        )
        df.loc[idx, "branch_residual_bank_total"] = bank_total
        df.loc[idx, "branch_residual_ledger_total"] = ledger_total
        df.loc[idx, "is_reconciled"] = True


def _run_branch_balance(
    bank_df,
    ledger_df,
    branch_columns,
    amount_tolerance
):
    unmatched_bank = _unmatched(bank_df)

    if (
        MONTH_DATE_COLUMN not in bank_df.columns
        or MONTH_DATE_COLUMN not in ledger_df.columns
    ):
        print(
            "Branch balancing skipped: txn_date column required for "
            "month-wise branch balancing"
        )
        return bank_df, ledger_df

    unmatched_bank = unmatched_bank.copy()
    unmatched_bank["_branch_balance_month"] = unmatched_bank[
        MONTH_DATE_COLUMN
    ].apply(_month_start)
    unmatched_bank = unmatched_bank[
        unmatched_bank["_branch_balance_month"].notna()
    ]

    for branch_key, bank_group in unmatched_bank.groupby(
        branch_columns + ["_branch_balance_month"],
        dropna=False
    ):
        if not isinstance(branch_key, tuple):
            branch_key = (branch_key,)

        branch_values = dict(zip(branch_columns, branch_key[:-1]))
        branch_month = branch_key[-1]

        ledger_group = ledger_df[
            (ledger_df["is_reconciled"] == False)
            & _same_branch_mask(ledger_df, branch_values)
            & _same_month_mask(ledger_df, branch_month)
        ]

        if bank_group.empty or ledger_group.empty:
            continue

        bank_total = round(bank_group["normalized_amount"].sum(), 2)
        ledger_total = round(ledger_group["normalized_amount"].sum(), 2)

        if abs(bank_total - ledger_total) > amount_tolerance:
            continue

        group_id = str(uuid.uuid4())
        bank_indices = list(bank_group.index)
        ledger_indices = list(ledger_group.index)
        row_count = len(bank_indices) + len(ledger_indices)
        branch_month_label = (
            f"{_branch_label(branch_values)}, "
            f"month={_month_label(branch_month)}"
        )
        remarks = branch_balanced(
            branch_month_label,
            bank_total,
            ledger_total,
            row_count
        )

        _set_branch_balanced_columns(
            bank_df,
            bank_indices,
            "matched_ledger_ids",
            ledger_indices,
            group_id,
            remarks,
            bank_total,
            ledger_total
        )
        _set_branch_balanced_columns(
            ledger_df,
            ledger_indices,
            "matched_bank_ids",
            bank_indices,
            group_id,
            remarks,
            bank_total,
            ledger_total
        )

    return bank_df, ledger_df


def _mark_remaining_manual_review(bank_df, ledger_df):
    for df in [bank_df, ledger_df]:
        mask = df["is_reconciled"] == False

        df.loc[mask, "reco_status"] = "MANUAL_REVIEW"
        df.loc[mask, "reconciliation_character"] = "MANUAL_REVIEW"
        df.loc[mask, "requires_manual_review"] = True
        df.loc[mask, "remarks"] = df.loc[mask, "remarks"].fillna(
            manual_review()
        )

    return bank_df, ledger_df


def run_branch_balancing(
    bank_df,
    ledger_df,
    branch_columns=None,
    amount_tolerance=AMOUNT_TOLERANCE,
    date_tolerance_days=DATE_TOLERANCE_DAYS
):
    branch_columns = _common_branch_columns(
        bank_df,
        ledger_df,
        branch_columns
    )

    if not branch_columns:
        print(
            "Branch balancing skipped: no common branch/account column found"
        )
        return _mark_remaining_manual_review(bank_df, ledger_df)

    bank_df, ledger_df = _run_soft_amount_matches(
        bank_df,
        ledger_df,
        branch_columns,
        amount_tolerance,
        date_tolerance_days
    )

    bank_df, ledger_df = _run_branch_balance(
        bank_df,
        ledger_df,
        branch_columns,
        amount_tolerance
    )

    return _mark_remaining_manual_review(bank_df, ledger_df)
