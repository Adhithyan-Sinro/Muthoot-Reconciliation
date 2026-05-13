import pandas as pd

from db.connection import get_engine


engine = get_engine()



def write_reconciliation_bank(bank_df):

    bank_df.to_sql(
        "reconcile_bank",
        engine,
        schema="reconciliation_tables",
        if_exists="replace",
        index=False
    )



def write_reconciliation_ledger(ledger_df):

    ledger_df.to_sql(
        "reconcile_ledger",
        engine,
        schema="reconciliation_tables",
        if_exists="replace",
        index=False
    )


