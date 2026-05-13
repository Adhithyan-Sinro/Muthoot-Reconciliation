import pandas as pd
from db.connection import get_engine


engine = get_engine()


def read_bank_data():

    query = """
    SELECT *
    FROM standardized_tables.stg_bank_txn
    """

    return pd.read_sql(query, engine)



def read_ledger_data():

    query = """
    SELECT *
    FROM standardized_tables.stg_ledger_txn
    """

    return pd.read_sql(query, engine)