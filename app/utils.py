def classify_risk(stress):
    if stress >= 9:
        return "CRITICAL"
    elif stress >= 7:
        return "HIGH"
    elif stress >= 4:
        return "MEDIUM"
    return "LOW"
