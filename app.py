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
    raise FileNotFoundError("❌ securite.db introuvable. Lance d'abord : python etl.py")

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

# =========================
# LAYOUT
# =========================
app.layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial", "backgroundColor": "#fdfbf6"},
    children=[

        html.H1("Dashboard Sécurité – CVA",
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
                    placeholder="Filtrer par type d’incident",
                    multi=True,
                    style={"width": "320px"}
                ),
            ]
        ),

        html.Br(),

        # Message auto
        html.Div(id="message-auto"),

        html.Br(),

        # KPI
        html.Div(
            style={"display": "flex", "gap": "40px", "justifyContent": "center"},
            children=[
                html.Div(id="kpi-total", style={"fontWeight": "bold", "color": "#0058a3"}),
                html.Div(id="kpi-vols", style={"fontWeight": "bold", "color": "#0058a3"}),
                html.Div(id="kpi-valeur", style={"fontWeight": "bold", "color": "#0058a3"}),
            ]
        ),

        html.Br(),

        # Graphiques
        dcc.Graph(id="graph-incidents"),
        dcc.Graph(id="graph-pie"),        # 👈 CAMEMBERT
        dcc.Graph(id="graph-prix"),
        dcc.Graph(id="graph-evolution"),

        # Export
        html.Div(
            style={"display": "flex", "justifyContent": "center", "marginBottom": "20px"},
            children=[
                html.Button("📤 Export Excel", id="btn-export-excel",
                            n_clicks=0, style={"backgroundColor": "#ffcc00"}),
                dcc.Download(id="download-excel")
            ]
        ),

        # Tableau
        html.H3("Détails des incidents"),
        dash_table.DataTable(
            id="tableau",
            page_size=10,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "6px"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0"}
        )
    ]
)

# =========================
# CALLBACK PRINCIPAL
# =========================
@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-vols", "children"),
    Output("kpi-valeur", "children"),
    Output("graph-incidents", "figure"),
    Output("graph-pie", "figure"),
    Output("graph-prix", "figure"),
    Output("graph-evolution", "figure"),
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

    # Message automatique
    if vols == 0:
        message = "✅ Aucun incident critique aujourd’hui"
        style = {
            "backgroundColor": "#e6f4ea",
            "padding": "10px",
            "borderRadius": "6px",
            "fontWeight": "bold",
            "textAlign": "center"
        }
    else:
        message = f"⚠️ {vols} vol(s) confirmé(s)"
        style = {
            "backgroundColor": "#fdecea",
            "padding": "10px",
            "borderRadius": "6px",
            "fontWeight": "bold",
            "textAlign": "center"
        }

    # Graphique bar
    fig_incidents = px.bar(
        dff,
        x="Type d’incident",
        color="Type d’incident",
        title="Incidents par type",
        template="plotly_white"
    )
    fig_incidents.update_layout(showlegend=False)

    # Pie chart (camembert)
    incident_counts = dff["Type d’incident"].value_counts()

    fig_pie = go.Figure(
        go.Pie(
            labels=incident_counts.index,
            values=incident_counts.values,
            hole=0.4,
            hovertemplate=
                "<b>%{label}</b><br>" +
                "Nombre : %{value}<br>" +
                "Pourcentage : %{percent}<extra></extra>"
        )
    )
    fig_pie.update_layout(
        title="Répartition des incidents par type",
        template="plotly_white"
    )

    # Histogramme prix
    fig_prix = px.histogram(
        dff,
        x="Prix",
        nbins=20,
        title="Distribution de la valeur des articles",
        template="plotly_white"
    )

    # Évolution temporelle
    evolution = dff.groupby("Date").size().reset_index(name="Incidents")
    fig_evolution = px.line(
        evolution,
        x="Date",
        y="Incidents",
        markers=True,
        title="Évolution des incidents",
        template="plotly_white"
    )

    data = dff.to_dict("records")
    columns = [{"name": c, "id": c} for c in dff.columns]

    return (
        f"📌 Total incidents : {total}",
        f"🚨 Vols confirmés : {vols}",
        f"💰 Valeur totale : {valeur:,.2f} $",
        fig_incidents,
        fig_pie,
        fig_prix,
        fig_evolution,
        data,
        columns,
        message,
        style
    )

# =========================
# EXPORT EXCEL
# =========================
@app.callback(
    Output("download-excel", "data"),
    Input("btn-export-excel", "n_clicks"),
    prevent_initial_call=True
)
def export_excel(n_clicks):
    return dcc.send_data_frame(
        df.to_excel,
        "Dashboard_Securite_Export.xlsx",
        sheet_name="Incidents"
    )

# =========================
# LANCEMENT
# =========================
server = app.server

if __name__ == "__main__":
    app.run(debug=False)
