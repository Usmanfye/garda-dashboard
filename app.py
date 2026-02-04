from dash import Dash, html, dcc, Input, Output, dash_table
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import dash_auth
import os

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
    raise FileNotFoundError("❌ securite.db introuvable")

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM incidents", conn)
conn.close()

# =========================
# NETTOYAGE DES DONNÉES
# =========================
df.columns = df.columns.str.strip()

# Date
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
df["Date"] = df["Date"].ffill()

# Heure
df["Heure"] = df["Heure"].astype(str).str.strip()

# Date + Heure réelle
df["DateHeure"] = pd.to_datetime(
    df["Date"].dt.strftime("%Y-%m-%d") + " " + df["Heure"],
    errors="coerce"
)

# Sécurité si Prix absent
if "Prix" not in df.columns:
    df["Prix"] = 0

# =========================
# APP
# =========================
app = Dash(__name__)
server = app.server
auth = dash_auth.BasicAuth(app, VALID_USERS)
app.title = "Dashboard Sécurité – CVA"

# =========================
# LAYOUT
# =========================
app.layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[

        # =========================
        # HEADER : TITRE + LOGO
        # =========================
        html.Div(
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "marginBottom": "10px"
            },
            children=[
                html.H1(
                    "📊 Infractions Entrée PRINCIPALE",
                    style={"color": "#0058a3", "margin": 0}
                ),
                html.A(
    href="https://www.ikea.com/ca/fr/",
    target="_blank",  # ouvre dans un nouvel onglet
    children=[
        html.Img(
            src="/assets/ikea_logo.png",
            style={
                "height": "60px",
                "cursor": "pointer"
            }
        )
    ]
)
            ]
        ),

        # =========================
        # BANDEAU PÉRIODE
        # =========================
        html.Div(
            "🗓️ Période analysée : Décembre 2025 – Février 2026",
            style={
                "textAlign": "center",
                "backgroundColor": "#0058a3",
                "color": "white",
                "padding": "8px",
                "borderRadius": "6px",
                "fontWeight": "bold",
                "marginBottom": "20px"
            }
        ),

        # =========================
        # FILTRES
        # =========================
        html.Div(
            style={"display": "flex", "gap": "20px", "justifyContent": "center"},
            children=[
                dcc.DatePickerRange(
                    id="filtre-date",
                    start_date=df["Date"].min(),
                    end_date=df["Date"].max(),
                    display_format="DD/MM/YYYY"
                ),
                dcc.Dropdown(
                    id="filtre-incident",
                    options=[
                        {"label": i, "value": i}
                        for i in sorted(df["Type d’incident"].dropna().unique())
                    ],
                    multi=True,
                    placeholder="Type d’incident",
                    style={"width": "300px"}
                )
            ]
        ),

        html.Br(),

        html.Div(id="message-auto"),

        html.Br(),

        # =========================
        # KPI
        # =========================
        html.Div(
            style={
                "display": "flex",
                "gap": "40px",
                "justifyContent": "center",
                "fontWeight": "bold"
            },
            children=[
                html.Div(id="kpi-total"),
                html.Div(id="kpi-vols"),
                html.Div(id="kpi-valeur")
            ]
        ),

        html.Br(),

        # =========================
        # GRAPHIQUES
        # =========================
        dcc.Graph(id="graph-prix"),
        dcc.Graph(id="graph-pie"),

        html.H3("📋 Détails des incidents"),

        dash_table.DataTable(
            id="tableau",
            page_size=10,
            filter_action="native",
            sort_action="native",
            style_table={"overflowX": "auto"}
        )
    ]
)


# =========================
# CALLBACK
# =========================
@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-vols", "children"),
    Output("kpi-valeur", "children"),
    Output("graph-prix", "figure"),
    Output("graph-pie", "figure"),
    Output("tableau", "data"),
    Output("tableau", "columns"),
    Output("message-auto", "children"),
    Output("message-auto", "style"),
    Input("filtre-date", "start_date"),
    Input("filtre-date", "end_date"),
    Input("filtre-incident", "value"),
)
def update_dashboard(start_date, end_date, incidents):

    dff = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    if incidents:
        dff = dff[dff["Type d’incident"].isin(incidents)]

    # TRI TEMPOREL
    dff = dff.sort_values("DateHeure").reset_index(drop=True)
    dff["IndexIncident"] = dff.index + 1

    total = len(dff)
    vols = len(dff[dff["Type d’incident"] == "Vol confirmé"])
    valeur = dff["Prix"].sum()

    # MESSAGE AUTO
    if vols == 0:
        message = "✅ Aucun incident critique"
        style = {"backgroundColor": "#e6f4ea", "padding": "10px"}
    else:
        message = f"⚠️ {vols} vol(s) confirmé(s)"
        style = {"backgroundColor": "#fdecea", "padding": "10px"}

    # =========================
    # HISTOGRAMME PRIX MODERNE
    # =========================
    fig_prix = px.histogram(
        dff,
        x="Prix",
        nbins=25,
        color_discrete_sequence=["#0058a3"],
        marginal="box",
        title="Distribution des prix des incidents",
        template="plotly_white"
    )

    fig_prix.update_layout(
        xaxis_title="Prix ($)",
        yaxis_title="Nombre d'incidents",
        bargap=0.1
    )

    # =========================
    # ÉVOLUTION RÉELLE (NUAGE)
    # =========================


    


    # =========================
    # PIE CHART
    # =========================
    counts = dff["Type d’incident"].value_counts()

    fig_pie = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.4
        )
    )

    fig_pie.update_layout(
        title="Répartition des incidents",
        template="plotly_white"
    )

    return (
        f"📌 Total incidents : {total}",
        f"🚨 Vols confirmés : {vols}",
        f"💰 Valeur totale : {valeur:,.2f} $",
        fig_prix,
        fig_pie,
        dff.to_dict("records"),
        [{"name": c, "id": c} for c in dff.columns],
        message,
        style
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
