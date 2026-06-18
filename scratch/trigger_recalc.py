import requests
import json

HOST = "http://127.0.0.1:8000"

print("1. Triggering /api/excel/recalculate-all...")
r_recalc = requests.post(f"{HOST}/api/excel/recalculate-all")
if r_recalc.status_code == 200:
    print("Recalculation successful.")
else:
    print(f"Error {r_recalc.status_code}: {r_recalc.text}")

print("\n2. Fetching /api/excel/flows-forecasts...")
r = requests.get(f"{HOST}/api/excel/flows-forecasts")
if r.status_code == 200:
    res = r.json()
    print("\nFlows (Table A):")
    for f in res["market_flows"]:
        print(f)
    print("\nForecasts (Table B):")
    for fc in res["forecasts"]:
        print(fc)
else:
    print(f"Error {r.status_code}: {r.text}")
