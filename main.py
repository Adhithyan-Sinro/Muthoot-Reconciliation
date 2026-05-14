import uuid

from db.read_data import read_bank_data
from db.read_data import read_ledger_data

from preprocessing.normalization import normalize_bank
from preprocessing.normalization import normalize_ledger

from matching.exact_date_amt import run_exact_date_amt
from matching.exact_chq_amt import run_exact_chq_amt
from matching.exact_cust_amt import run_exact_cust_amt
from matching.delayed_accounting import run_delayed_accounting
from matching.bank_charges import run_bank_charges
# from matching.contra_matching import run_contra_matching

from db.write_back import write_reconciliation_bank
from db.write_back import write_reconciliation_ledger


from matching.split_matching import run_split_matching
from matching.difference_matching import (run_difference_matching)
# from matching.reversal_matching import (run_reversal_matching)
from matching.offset_matching import run_offset_matching
from matching.cash_chq_matching import (run_cheque_cash_matching)

reconciliation_run_id = str(uuid.uuid4())

print("Reading data...")

bank_df = read_bank_data()
ledger_df = read_ledger_data()

print("Normalizing...")

bank_df = normalize_bank(bank_df)
ledger_df = normalize_ledger(ledger_df)

bank_df["is_reconciled"] = False
ledger_df["is_reconciled"] = False

print("Running exact date amount matching...")

bank_df, ledger_df = run_exact_date_amt(
    bank_df,
    ledger_df
)

print("Running exact cheque amount matching...")

bank_df, ledger_df = run_exact_chq_amt(
    bank_df,
    ledger_df
)

print("Running exact customer amount matching...")

bank_df, ledger_df = run_exact_cust_amt(
    bank_df,
    ledger_df
)

# print("Running contra matching...")
#
# bank_df, ledger_df = run_contra_matching(
#     bank_df,
#     ledger_df
# )

print("Running offset matching...")

bank_df, ledger_df = run_offset_matching(
    bank_df,
    ledger_df
)

print("Running split matching...")

bank_df, ledger_df = run_split_matching(
    bank_df,
    ledger_df
)

print("Running difference matching...")

bank_df, ledger_df = run_difference_matching(
    bank_df,
    ledger_df
)

# print("Running reversal matching...")
#
# bank_df, ledger_df = run_reversal_matching(
#     bank_df,
#     ledger_df
# )

print("Running narration matching...")


narration_matches_df = run_cheque_cash_matching(
    bank_df,
    ledger_df
)

print("Running delayed accounting matching...")

bank_df, ledger_df = run_delayed_accounting(
    bank_df,
    ledger_df
)

print("Running bank charges matching...")

bank_df, ledger_df = run_bank_charges(
    bank_df,
    ledger_df
)

print("Writing reconciliation results...")

write_reconciliation_bank(bank_df)
write_reconciliation_ledger(ledger_df)
# write_narration_matches(narration_matches_df)

print("Reconciliation completed successfully")
