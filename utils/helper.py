import uuid


def infer_reconciliation_character(
    match_rule,
    match_type,
    reco_status
):
    if reco_status == "SOFT_MATCH":
        return "OPERATIONAL_ADJUSTMENT"

    if reco_status == "BRANCH_BALANCED_EXCEPTION":
        return "BRANCH_LEVEL"

    if reco_status == "MANUAL_REVIEW":
        return "MANUAL_REVIEW"

    if match_type == "EXACT_MATCH":
        return "EXACT"

    if match_type == "BUSINESS_RULE_MATCH":
        return "BUSINESS_RULE"

    if match_rule in {
        "BANK_CHARGE",
        "DELAYED_ACCOUNTING",
        "CHEQUE_CASH_MATCH"
    }:
        return "BUSINESS_RULE"

    return "INFERRED"


def initialize_reconciliation_metadata(df):
    defaults = {
        "reco_status": "MANUAL_REVIEW",
        "match_rule": None,
        "match_type": None,
        "remarks": None,
        "confidence_score": 0.0,
        "group_match_id": None,
        "matched_ledger_ids": None,
        "matched_bank_ids": None,
        "matched_amount": 0.0,
        "reconciliation_character": "MANUAL_REVIEW",
        "requires_manual_review": True,
        "exception_reason": None,
    }

    for column, default_value in defaults.items():
        if column not in df.columns:
            df[column] = default_value

    text_columns = [
        "reco_status",
        "match_rule",
        "match_type",
        "remarks",
        "group_match_id",
        "matched_ledger_ids",
        "matched_bank_ids",
        "reconciliation_character",
        "exception_reason",
    ]

    for column in text_columns:
        df[column] = df[column].astype("object")

    df["confidence_score"] = df["confidence_score"].astype("float64")
    df["matched_amount"] = df["matched_amount"].astype("float64")
    df["requires_manual_review"] = df["requires_manual_review"].astype("bool")

    return df


def mark_group_reconciled(

    bank_df,
    ledger_df,

    bank_indices,
    ledger_indices,

    match_rule,
    match_type,

    remarks,

    confidence=100,

    reco_status="MATCHED",

    reconciliation_character=None,

    requires_manual_review=False,

    exception_reason=None
):

    """
    Group reconciliation helper
    Supports:
    - one-to-one
    - one-to-many
    - many-to-one
    - many-to-many
    """

    group_id = str(uuid.uuid4())

    if reconciliation_character is None:
        reconciliation_character = infer_reconciliation_character(
            match_rule,
            match_type,
            reco_status
        )

    # -----------------------------------------
    # Convert single values to list
    # -----------------------------------------

    if not isinstance(bank_indices, list):
        bank_indices = [bank_indices]

    if not isinstance(ledger_indices, list):
        ledger_indices = [ledger_indices]

    # -----------------------------------------
    # Prepare matching ids
    # -----------------------------------------

    bank_ids_str = ",".join(
        map(str, bank_indices)
    )

    ledger_ids_str = ",".join(
        map(str, ledger_indices)
    )

    # -----------------------------------------
    # Update bank dataframe
    # -----------------------------------------

    for bank_idx in bank_indices:

        matched_amount = abs(

            bank_df.loc[
                bank_idx,
                "normalized_amount"
            ]

        )

        bank_df.loc[
            bank_idx,
            "reco_status"
        ] = reco_status

        bank_df.loc[
            bank_idx,
            "match_rule"
        ] = match_rule

        bank_df.loc[
            bank_idx,
            "match_type"
        ] = match_type

        bank_df.loc[
            bank_idx,
            "remarks"
        ] = remarks

        bank_df.loc[
            bank_idx,
            "confidence_score"
        ] = confidence

        bank_df.loc[
            bank_idx,
            "reconciliation_character"
        ] = reconciliation_character

        bank_df.loc[
            bank_idx,
            "requires_manual_review"
        ] = requires_manual_review

        bank_df.loc[
            bank_idx,
            "exception_reason"
        ] = exception_reason

        bank_df.loc[
            bank_idx,
            "group_match_id"
        ] = group_id

        bank_df.loc[
            bank_idx,
            "matched_ledger_ids"
        ] = ledger_ids_str

        bank_df.loc[
            bank_idx,
            "matched_amount"
        ] = matched_amount

        bank_df.loc[
            bank_idx,
            "is_reconciled"
        ] = True

    # -----------------------------------------
    # Update ledger dataframe
    # -----------------------------------------

    for ledger_idx in ledger_indices:

        matched_amount = abs(

            ledger_df.loc[
                ledger_idx,
                "normalized_amount"
            ]

        )

        ledger_df.loc[
            ledger_idx,
            "reco_status"
        ] = reco_status

        ledger_df.loc[
            ledger_idx,
            "match_rule"
        ] = match_rule

        ledger_df.loc[
            ledger_idx,
            "match_type"
        ] = match_type

        ledger_df.loc[
            ledger_idx,
            "remarks"
        ] = remarks

        ledger_df.loc[
            ledger_idx,
            "confidence_score"
        ] = confidence

        ledger_df.loc[
            ledger_idx,
            "reconciliation_character"
        ] = reconciliation_character

        ledger_df.loc[
            ledger_idx,
            "requires_manual_review"
        ] = requires_manual_review

        ledger_df.loc[
            ledger_idx,
            "exception_reason"
        ] = exception_reason

        ledger_df.loc[
            ledger_idx,
            "group_match_id"
        ] = group_id

        ledger_df.loc[
            ledger_idx,
            "matched_bank_ids"
        ] = bank_ids_str

        ledger_df.loc[
            ledger_idx,
            "matched_amount"
        ] = matched_amount

        ledger_df.loc[
            ledger_idx,
            "is_reconciled"
        ] = True

    return bank_df, ledger_df
