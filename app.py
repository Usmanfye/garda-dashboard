from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import dash_auth
import os
import etl  # Import ETL

# =========================
# LANCER L'ETL AUTOMATIQUEMENT
# =========================
etl.run_etl()  # Crée securite.db à partir du fichier Excel

# =========================
# AUTHENTIFICATION
# =========================
VALID_USERS = {
    "manager": "mdp123",
    "securite": "agent2026"
}

# =========================
# CHARGEMENT DES DONNÉES
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "securite.db")

if not os.path.exists(DB_FILE):
    raise FileNotFoundError("❌ securite.db introuvable. L'ETL a échoué ?")

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM incidents", conn)
conn.close()

# Nettoyage
df.columns = df.columns.str.strip()
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
df = df.sort_values(by=["Date", "Heure"])
df["Date"] = df["Date"].ffill()
if "Prix" not in df.columns:
    df["Prix"] = 0
df["Prix"] = df["Prix"].fillna(0)

# =========================
# INITIALISATION DASH
# =========================
app = Dash(__name__)
auth = dash_auth.BasicAuth(app, VALID_USERS)
app.title = "Dashboard Sécurité – CVA"
server = app.server  # requis par Render

# =========================
# LAYOUT
# =========================
# ... (le layout reste exactement le même que ton précédent app.py)
# Tu peux copier/coller le layout et les callbacks existants
