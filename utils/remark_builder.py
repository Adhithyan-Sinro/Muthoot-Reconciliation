def exact_match(rule_name):
    remarks = {
        "DATE_AMT": "Exact date and amount match",
        "CHQ_AMT": "Exact cheque and amount match",
        "CUST_AMT": "Exact customer and amount match",
    }

    return remarks.get(rule_name, "Exact transaction match")


def branch_balanced(branch_label, bank_total, ledger_total, row_count):
    return (
        f"Branch residual balanced for {branch_label}: unmatched bank total "
        f"{bank_total:.2f} equals unmatched ledger total {ledger_total:.2f} "
        f"across {row_count} residual transactions after all transaction-level "
        f"rules failed. Transaction-level identity not established."
    )


def soft_amount_match(branch_label, amount, date_diff_days):
    date_text = (
        f"date difference {date_diff_days} days"
        if date_diff_days is not None
        else "date proximity not available"
    )

    return (
        f"Amount {amount:.2f} matched within {branch_label} after primary "
        f"rules failed, but customer/cheque differs between bank and ledger "
        f"({date_text}). Possible internal adjustment or mapping error."
    )


def manual_review():
    return (
        "Unresolved after all transaction-level and branch-level "
        "reconciliation rules."
    )
