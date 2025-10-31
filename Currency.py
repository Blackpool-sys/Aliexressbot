import requests

def usd_to_dzd(amount_usd: float) -> float:
    """تحويل الدولار إلى الدينار الجزائري"""
    try:
        res = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=DZD")
        rate = res.json()["rates"]["DZD"]
        return round(amount_usd * rate, 2)
    except Exception:
        return 0.0
