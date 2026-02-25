# api/hybrid.py
def hybrid_merge(donut_data: dict, rule_data: dict) -> dict:
    final = {}

    final["vendor_name"] = (
        donut_data.get("vendor_name")
        or rule_data["vendor_name"]["value"]
    )

    final["invoice_number"] = (
        donut_data.get("invoice_number")
        or rule_data["invoice_number"]["value"]
    )

    final["total_amount"] = (
        donut_data.get("total_amount")
        or rule_data["total_amount"]["value"]
    )

    # Confidence logic
    confidence = 0.95 if donut_data else 0.75

    return {
        "final_fields": final,
        "confidence": confidence
    }
