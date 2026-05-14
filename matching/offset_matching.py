from utils.helper import mark_group_reconciled


AMOUNT_TOLERANCE  = 0.01
BOUNDARY_DAY_BUFF = 5     # days — catches reversals that cross a month boundary


# ---------------------------------------------------------------------------
# Date tolerance helper
# ---------------------------------------------------------------------------

def _within_date_tolerance(date_i, date_j):
    """
    Returns True if two dates are in the same month/year
    OR within BOUNDARY_DAY_BUFF days of each other.

    The day-buffer handles month-boundary edge cases:
        e.g. Jan 31 <-> Feb 1  →  1 day apart, different months → still a match
    """
    same_period = (
        date_i.month == date_j.month
        and date_i.year == date_j.year
    )
    near_boundary = abs((date_i - date_j).days) <= BOUNDARY_DAY_BUFF

    return same_period or near_boundary


# ---------------------------------------------------------------------------
# Core pair finder
# ---------------------------------------------------------------------------

def find_cancelling_pairs(df, match_or_cols, extra_and_col=None):
    """
    Yield index pairs from *df* whose amounts cancel out (sum ≈ 0)
    and that fall within date tolerance.

    Parameters
    ----------
    df : DataFrame
        Filtered to unreconciled rows before passing in.
    match_or_cols : list[str]
        At least one of these columns must match between the two rows (OR logic).
        e.g. ["normalized_cust_name", "normalized_cheque_no"]
    extra_and_col : str | None
        If given, this column must ALSO match (AND logic on top of OR).
        Used on the ledger side to prevent cross-account false positives.
        e.g. "acc_no"

    Yields
    ------
    (idx_i, idx_j) : tuple
    """

    seen = set()

    for idx_i, row_i in df.iterrows():

        amt_i = round(row_i["normalized_amount"], 2)

        # --- OR filter: share at least one identifier ---
        or_mask = False
        for col in match_or_cols:
            or_mask = or_mask | (df[col] == row_i[col])

        candidates = df[or_mask]
        candidates = candidates[candidates.index != idx_i]

        # --- AND filter: must also share acc_no (ledger side guard) ---
        if extra_and_col:
            candidates = candidates[
                candidates[extra_and_col] == row_i[extra_and_col]
            ]

        for idx_j, row_j in candidates.iterrows():

            pair_key = tuple(sorted((idx_i, idx_j)))
            if pair_key in seen:
                continue

            # Amounts must cancel
            amt_j = round(row_j["normalized_amount"], 2)
            if abs(amt_i + amt_j) > AMOUNT_TOLERANCE:
                continue

            # Date must be within tolerance
            if not _within_date_tolerance(row_i["txn_date"], row_j["txn_date"]):
                continue

            seen.add(pair_key)
            yield (idx_i, idx_j)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_offset_matching(bank_df, ledger_df):
    """
    Detect transactions that cancel each other out — covers both
    reversal entries and contra/nullified entries in a single pass.

    Pass 1 — Bank side
        Match by: cust_name OR cheque_no
        Date:     same month or within 5-day boundary buffer

    Pass 2 — Ledger side
        Match by: cust_name OR cheque_no
        AND:      acc_no must also match  <- prevents cross-account false positives
        Date:     same month or within 5-day boundary buffer
    """

    # ------------------------------------------------------------------
    # Pass 1: Bank reversals
    # ------------------------------------------------------------------

    unmatched_bank = bank_df[bank_df["is_reconciled"] == False]

    for idx_i, idx_j in find_cancelling_pairs(
        df            = unmatched_bank,
        match_or_cols = ["normalized_cust_name", "normalized_cheque_no"],
    ):
        bank_df, ledger_df = mark_group_reconciled(
            bank_df,
            ledger_df,
            bank_indices   = [idx_i, idx_j],
            ledger_indices = [],
            match_rule     = "REVERSAL_MATCH",
            match_type     = "REVERSAL",
            remarks        = "Possible reversal transaction identified in bank",
            confidence     = 80,
            reco_status    = "REVERSAL",
        )

    # ------------------------------------------------------------------
    # Pass 2: Ledger reversals / contra entries
    # ------------------------------------------------------------------

    unmatched_ledger = ledger_df[ledger_df["is_reconciled"] == False]
    ledger_account_guard = (
        "acc_no"
        if "acc_no" in unmatched_ledger.columns
        else None
    )

    for idx_i, idx_j in find_cancelling_pairs(
        df            = unmatched_ledger,
        match_or_cols = ["normalized_cust_name", "normalized_cheque_no"],
        extra_and_col = ledger_account_guard,
    ):
        bank_df, ledger_df = mark_group_reconciled(
            bank_df,
            ledger_df,
            bank_indices   = [],
            ledger_indices = [idx_i, idx_j],
            match_rule     = "REVERSAL_MATCH",
            match_type     = "REVERSAL",
            remarks        = "Possible reversal/contra transaction identified in ledger",
            confidence     = 80,
            reco_status    = "REVERSAL",
        )

    return bank_df, ledger_df
