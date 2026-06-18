import requests
import json

HOST = "http://127.0.0.1:8000"

print("Fetching /api/excel/allocation...")
r = requests.get(f"{HOST}/api/excel/allocation")
if r.status_code == 200:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
else:
    print(f"Error {r.status_code}: {r.text}")
