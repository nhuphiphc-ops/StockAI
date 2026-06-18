import sys
import os
sys.path.append(os.getcwd())

from core.excel_manager import ExcelManager

print("Initializing ExcelManager...")
em = ExcelManager()

print("\nCalling get_asset_allocation()...")
res = em.get_asset_allocation()

print("\nResult allocations:")
for alloc in res["allocations"]:
    print(alloc)
