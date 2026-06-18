import requests
import json

HOST = "http://127.0.0.1:8000"

print("1. Fetching /api/excel/portfolio...")
r = requests.get(f"{HOST}/api/excel/portfolio")
if r.status_code == 200:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
else:
    print(f"Error {r.status_code}: {r.text}")

print("\n2. Triggering /api/excel/recalculate-all...")
r_recalc = requests.post(f"{HOST}/api/excel/recalculate-all")
if r_recalc.status_code == 200:
    print(json.dumps(r_recalc.json(), indent=2, ensure_ascii=False))
else:
    print(f"Error {r_recalc.status_code}: {r_recalc.text}")
