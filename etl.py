import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, "Dashboard_Securite.xlsx")
DB_FILE = os.path.join(BASE_DIR, "securite.db")

# Charger Excel
df = pd.read_excel(EXCEL_FILE, sheet_name="Données")
df.columns = df.columns.str.strip()
df = df.rename(columns={"prix":"Prix"})
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

# Connecter SQLite
conn = sqlite3.connect(DB_FILE)

# Envoyer les données à SQLite (remplace la table si déjà existante)
df.to_sql("incidents", conn, if_exists="replace", index=False)

print("✅ ETL terminé : données chargées dans SQLite")

conn.close()
