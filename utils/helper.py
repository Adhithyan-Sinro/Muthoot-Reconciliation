import uuid


def mark_group_reconciled(

    bank_df,
    ledger_df,

    bank_indices,
    ledger_indices,

    match_rule,
    match_type,

    remarks,

    confidence=100,

    reco_status="MATCHED"
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