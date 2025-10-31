import hashlib, time, requests, os
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
TRACKING_ID = os.getenv("TRACKING_ID")
API_URL = "https://api-sg.aliexpress.com/sync"

def generate_signature(params: dict) -> str:
    sorted_params = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    string_to_sign = APP_SECRET + sorted_params + APP_SECRET
    return hashlib.md5(string_to_sign.encode("utf-8")).hexdigest().upper()

def get_product_details(product_id: str):
    method = "aliexpress.affiliate.productdetail.get"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    params = {
        "app_key": APP_KEY,
        "method": method,
        "timestamp": timestamp,
        "sign_method": "md5",
        "format": "json",
        "v": "2.0",
        "tracking_id": TRACKING_ID,
        "product_ids": product_id,
    }

    params["sign"] = generate_signature(params)
    response = requests.get(API_URL, params=params, timeout=15)
    return response.json()
