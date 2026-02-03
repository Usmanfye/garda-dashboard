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

# Nettoyage
df.columns = df.columns.str.strip()
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
df["Date"] = df["Date"].ffill()

if "Prix" not in df.columns:
    df["Prix"] = 0

# =========================
# APP
# =========================
app = Dash(__name__)
auth = dash_auth.BasicAuth(app, VALID_USERS)
app.title = "Dashboard Sécurité – CVA"

# =========================
# LAYOUT
# =========================
app.layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[

        html.H1("📊 Dashboard Sécurité – CVA",
                style={"textAlign": "center", "color": "#0058a3"}),

        # Filtres
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

        # KPI
        html.Div(
            style={"display": "flex", "gap": "40px", "justifyContent": "center"},
            children=[
                html.Div(id="kpi-total"),
                html.Div(id="kpi-vols"),
                html.Div(id="kpi-valeur")
            ]
        ),

        html.Br(),

        # Graphiques
        dcc.Graph(id="graph-prix"),
        dcc.Graph(id="graph-evolution"),
        dcc.Graph(id="graph-pie"),

        html.Br(),

        # Export
        html.Button("📤 Export Excel", id="btn-export-excel"),
        dcc.Download(id="download-excel"),

        html.H3("Détails des incidents"),

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
    Output("graph-evolution", "figure"),
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

    total = len(dff)
    vols = len(dff[dff["Type d’incident"] == "Vol confirmé"])
    valeur = dff["Prix"].sum()

    # Message auto
    if vols == 0:
        message = "✅ Aucun incident critique aujourd’hui"
        style = {"backgroundColor": "#e6f4ea", "padding": "10px"}
    else:
        message = f"⚠️ {vols} vol(s) confirmé(s)"
        style = {"backgroundColor": "#fdecea", "padding": "10px"}

    # Histogramme prix
    fig_prix = px.histogram(
        dff, x="Prix", nbins=20,
        title="Distribution des prix",
        template="plotly_white"
    )

    # Évolution
    evo = dff.groupby("Date").size().reset_index(name="Incidents")
    fig_evolution = px.line(
        evo, x="Date", y="Incidents",
        markers=True,
        title="Évolution des incidents",
        template="plotly_white"
    )

    # Pie chart
    counts = dff["Type d’incident"].value_counts()
    fig_pie = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.4,
            hovertemplate="<b>%{label}</b><br>%{value} incidents<br>%{percent}<extra></extra>"
        )
    )
    fig_pie.update_layout(
        title="Répartition des incidents",
        template="plotly_white"
    )

    data = dff.to_dict("records")
    columns = [{"name": c, "id": c} for c in dff.columns]

    return (
        f"📌 Total incidents : {total}",
        f"🚨 Vols confirmés : {vols}",
        f"💰 Valeur totale : {valeur:,.2f} $",
        fig_prix,
        fig_evolution,
        fig_pie,
        data,
        columns,
        message,
        style
    )

# =========================
# EXPORT
# =========================
@app.callback(
    Output("download-excel", "data"),
    Input("btn-export-excel", "n_clicks"),
    prevent_initial_call=True
)
def export_excel(n):
    return dcc.send_data_frame(df.to_excel, "export_dashboard.xlsx", sheet_name="Incidents")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
