import openpyxl

wb = openpyxl.load_workbook("AI_Stock_Investment_Dashboard.xlsx", data_only=True)
ws = wb["Dashboard Tong Quan"]

print("Dashboard Tong Quan Sheet Rows:")
for r in range(1, 60):
    row_vals = [ws.cell(row=r, column=c).value for c in range(1, 12)]
    if any(row_vals):
        print(f"Row {r:02d}: {row_vals}")
