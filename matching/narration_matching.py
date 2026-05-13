import uuid

import pandas as pd
from rapidfuzz import fuzz


SIMILARITY_THRESHOLD = 85
AMOUNT_TOLERANCE = 5

NARRATION_MATCH_COLUMNS = [
    "txn_id",
    "txn_date",
    "vh_no",
    "type",
    "cheque_no",
    "particulars",
    "debit_amount",
    "credit_amount",
    "source_table",
    "matched_txn_id",
    "matched_source_table",
    "match_rule",
    "match_type",
    "confidence_score",
    "similarity_score",
    "remarks",
    "group_match_id",
    "reconciliation_run_id",
    "normalized_particulars",
    "requires_manual_review"
]


def _confidence_from_similarity(similarity):
    if similarity >= 95:
        return 90

    if similarity >= 90:
        return 80

    return 70


def run_narration_matching(
    bank_df,
    ledger_df,
    reconciliation_run_id
):
    narration_matches = []

    for _, bank_row in bank_df.iterrows():
        bank_narration = str(
            bank_row["normalized_particulars"]
        )

        bank_amount = abs(
            bank_row["normalized_amount"]
        )

        candidate_ledger = ledger_df[
            abs(
                abs(ledger_df["normalized_amount"])
                - bank_amount
            ) <= AMOUNT_TOLERANCE
        ]

        for _, ledger_row in candidate_ledger.iterrows():
            ledger_narration = str(
                ledger_row["normalized_particulars"]
            )

            similarity = fuzz.token_sort_ratio(
                bank_narration,
                ledger_narration
            )

            if similarity < SIMILARITY_THRESHOLD:
                continue

            confidence = _confidence_from_similarity(similarity)
            group_id = str(uuid.uuid4())

            remarks = (
                "Potential narration-based "
                "transaction match"
            )

            narration_matches.append({
                "txn_id": bank_row.get("bank_txn_id"),
                "txn_date": bank_row.get("txn_date"),
                "vh_no": None,
                "type": "BANK",
                "cheque_no": bank_row.get("cheque_no"),
                "particulars": bank_row.get("particulars"),
                "debit_amount": bank_row.get("debit_amount"),
                "credit_amount": bank_row.get("credit_amount"),
                "source_table": "reconcile_bank",
                "matched_txn_id": str(ledger_row.get("ledger_txn_id")),
                "matched_source_table": "reconcile_ledger",
                "match_rule": "NARRATION_MATCH",
                "match_type": "POTENTIAL_MATCH",
                "confidence_score": confidence,
                "similarity_score": similarity,
                "remarks": remarks,
                "group_match_id": group_id,
                "reconciliation_run_id": reconciliation_run_id,
                "normalized_particulars": bank_narration,
                "requires_manual_review": True
            })

            narration_matches.append({
                "txn_id": ledger_row.get("ledger_txn_id"),
                "txn_date": ledger_row.get("txn_date"),
                "vh_no": ledger_row.get("vh_no"),
                "type": "LEDGER",
                "cheque_no": ledger_row.get("cheque_no"),
                "particulars": ledger_row.get("particulars"),
                "debit_amount": ledger_row.get("debit_amount"),
                "credit_amount": ledger_row.get("credit_amount"),
                "source_table": "reconcile_ledger",
                "matched_txn_id": str(bank_row.get("bank_txn_id")),
                "matched_source_table": "reconcile_bank",
                "match_rule": "NARRATION_MATCH",
                "match_type": "POTENTIAL_MATCH",
                "confidence_score": confidence,
                "similarity_score": similarity,
                "remarks": remarks,
                "group_match_id": group_id,
                "reconciliation_run_id": reconciliation_run_id,
                "normalized_particulars": ledger_narration,
                "requires_manual_review": True
            })

    print("Narration matching completed")

    return pd.DataFrame(
        narration_matches,
        columns=NARRATION_MATCH_COLUMNS
    )
