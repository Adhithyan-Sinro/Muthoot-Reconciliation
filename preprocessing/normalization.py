import pandas as pd


def normalize_txn_date(df):

    if "txn_date" in df.columns:
        df["txn_date"] = pd.to_datetime(
            df["txn_date"],
            errors="coerce"
        ).dt.normalize()

    return df


def normalize_text(value):

    if pd.isna(value):
        return None

    value = str(value).upper().strip()

    remove_words = [
        "MUTHOOT FINANCE LIMITED",
        "CHQ TRANSFER",
        "RTGS",
        "NEFT",
        "IMPS"
    ]

    for word in remove_words:
        value = value.replace(word, "")

    value = " ".join(value.split())

    return value

def normalize_bank(bank_df):

    bank_df = normalize_txn_date(bank_df)

    bank_df["normalized_cust_name"] = (
        bank_df["cust_name"]
        .fillna("")
        .str.upper()
        .str.strip()
    )

    bank_df["normalized_cheque_no"] = (
        bank_df["cheque_no"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    bank_df["normalized_particulars"] = (
        bank_df["particulars"]
        .apply(normalize_text)
    )

    bank_df["normalized_amount"] = (
        bank_df["credit_amount"].fillna(0)
        - bank_df["debit_amount"].fillna(0)
    )

    return bank_df

def normalize_ledger(ledger_df):

    ledger_df = normalize_txn_date(ledger_df)

    ledger_df["normalized_cust_name"] = (
        ledger_df["cust_name"]
        .fillna("")
        .str.upper()
        .str.strip()
    )

    ledger_df["normalized_cheque_no"] = (
        ledger_df["cheque_no"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    ledger_df["normalized_particulars"] = (
        ledger_df["particulars"]
        .apply(normalize_text)
    )

    ledger_df["normalized_amount"] = (
        ledger_df["debit_amount"].fillna(0)
        - ledger_df["credit_amount"].fillna(0)
    )

    return ledger_df
