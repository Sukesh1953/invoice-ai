def adjust_confidence(fields: dict) -> float:
    score = 1.0

    if not fields["vendor_name"]["value"]:
        score -= 0.3

    if not fields["invoice_number"]["value"]:
        score -= 0.2

    if not fields["total_amount"]["value"]:
        score -= 0.4

    return max(round(score, 2), 0.0)
