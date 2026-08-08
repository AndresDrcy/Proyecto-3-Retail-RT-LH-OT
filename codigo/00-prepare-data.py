"""
00-preparar-datos.py
Convierte el .xlsx de Online Retail II en dos CSVs separados por año.
Este es el output que después se subirá a Bronze en Fabric.
"""

import pandas as pd
from pathlib import Path
import openpyxl

INPUT = Path("../datos/...")
OUTPUT_DIR = Path("../datos/...")
OUTPUT_DIR.mkdir(exist_ok=True)

# Hoja 2009-2010
print("Leyendo hoja Year 2009-2010...")
df_2010 = pd.read_excel(INPUT, sheet_name="Year 2009-2010")
df_2010.to_csv(OUTPUT_DIR / "sales_2010.csv", index=False, encoding="utf-8")
print(f"  {len(df_2010)} filas → sales_2010.csv")

# Hoja 2010-2011
print("Leyendo hoja Year 2010-2011...")
df_2011 = pd.read_excel(INPUT, sheet_name="Year 2010-2011")
df_2011.to_csv(OUTPUT_DIR / "sales_2011.csv", index=False, encoding="utf-8")
print(f"  {len(df_2011)} filas → sales_2011.csv")

print("\nDatos listos para upload a Bronze layer.")
