import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

dash.register_page(__name__, path="/repertorios", name="Repertorios")

df = pd.read_csv("data/eventos.csv")

COLS_ACCION = ["tiene_marcha", "tiene_corte", "tiene_paro", "tiene_acto",
               "tiene_escrache", "tiene_destrozos", "tiene_toma"]
COLS_ACTORES = ["docentes", "gremios_estatales", "sindicatos_privados",
                "organizaciones_sociales", "comunidades_indigenas", "vecinos",
                "colectivos_ambientales", "colectivos_especificos",
                "partidos_politicos", "policias_actores",
                "publico_general", "colectivos_violentos"]

COLOR_CHUBUT = "#2E86AB"
COLOR_JUJUY = "#A23B72"

def aplicar_estilo(fig):
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=12, color="#4B5563"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, title=None),
        xaxis=dict(showgrid=False, showline=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#F3F4F6",
                   showline=False, zeroline=False),
        # estas dos solo afectan a bar, son inocuas si no hay barras
        bargap=0.3,
        bargroupgap=0.1,
    )

    # Aplicar props específicas según el tipo de trace
    for tr in fig.data:
        if tr.type == "bar":
            tr.update(width=0.4)
        elif tr.type == "scatter":
            # si querés controlar la línea/markers:
            tr.update(line=dict(width=2), marker=dict(size=7))
        elif tr.type == "heatmap":
            tr.update(xgap=2, ygap=2)

    return fig

def chart_box(titulo, subtitulo, fig, fuente="Fuente: Base propia de eventos."):
    return html.Div([
        html.Div([html.P(titulo, className="chart-title")], className="chart-header"),
        html.P(subtitulo, className="chart-subtitle"),
        html.Div(dcc.Graph(figure=fig, config={'displayModeBar': False}), className="chart-body"),
        html.Div(fuente, className="chart-footer")
    ], className="chart-container")

# Gráfico 1: Repertorios
repertorios = (df.groupby("provincia")[COLS_ACCION].mean() * 100).round(1).T
repertorios.columns = ["Chubut", "Jujuy"]
repertorios = repertorios.sort_values("Jujuy")

# ACÁ ESTÁ LA CORRECCIÓN: var_name="provincia"
long_rep = repertorios.reset_index().melt(id_vars="index", var_name="provincia", value_name="value")
fig_rep = px.bar(long_rep, x="value", y="index", color="provincia", orientation="h", barmode="group",
                 color_discrete_map={"Chubut": COLOR_CHUBUT, "Jujuy": COLOR_JUJUY},
                 labels={"index": "", "value": "% de eventos", "provincia": ""})
fig_rep.update_layout(height=350)
fig_rep = aplicar_estilo(fig_rep)

# Gráfico 2: Actores
actores = (df.groupby("provincia")[COLS_ACTORES].mean() * 100).round(1).T
actores.columns = ["Chubut", "Jujuy"]
actores = actores.sort_values("Jujuy")

# ACÁ ESTÁ LA CORRECCIÓN: var_name="provincia"
long_act = actores.reset_index().melt(id_vars="index", var_name="provincia", value_name="value")
fig_act = px.bar(long_act, x="value", y="index", color="provincia", orientation="h", barmode="group",
                 color_discrete_map={"Chubut": COLOR_CHUBUT, "Jujuy": COLOR_JUJUY},
                 labels={"index": "", "value": "% de eventos", "provincia": ""})
fig_act.update_layout(height=450)
fig_act = aplicar_estilo(fig_act)

# Gráfico 3: Densidad
densidad = df.groupby("provincia")[["n_actores", "n_demandas"]].mean().round(2).reset_index()
long_dens = densidad.melt(id_vars="provincia", var_name="variable", value_name="value")
fig_dens = px.bar(long_dens, x="variable", y="value", color="provincia", barmode="group",
                  color_discrete_map={"Chubut": COLOR_CHUBUT, "Jujuy": COLOR_JUJUY},
                  labels={"variable": "Métrica", "value": "Promedio por evento", "provincia": ""})
fig_dens.update_layout(height=350)
fig_dens = aplicar_estilo(fig_dens)

layout = html.Div([
    html.Div("Inicio | Trabajo e ingresos | Repertorios", className="breadcrumbs"),
    html.Div([
        html.H1("¿Cómo protestaron? Tácticas y actores"),
        html.P("Qué tácticas desplegaron y qué actores las sostuvieron en Chubut (n=121) y Jujuy (n=66). Los porcentajes indican la proporción de episodios en los que aparece cada táctica o actor.", style={"fontSize": "1.1rem", "color": "#4B5563"}),

        html.Div([
            html.H4("Mensajes clave", className="mensajes-clave-title"),
            dbc.Row([
                dbc.Col(html.Div("En Jujuy predominan el paro y el corte de ruta (21,2% cada uno); en Chubut, la marcha y el acto.", className="mensaje-card"), width=4),
                dbc.Col(html.Div("Chubut desplegó repertorios expresivos (escraches, destrozos) ausentes en Jujuy, lo que sugiere un repertorio más heterogéneo.", className="mensaje-card destacado"), width=4),
                dbc.Col(html.Div("Los episodios de Jujuy convocan más actores por evento (1,77 vs. 1,01 en Chubut).", className="mensaje-card"), width=4),
            ])
        ], className="mensajes-clave-wrapper"),

        chart_box("Tácticas desplegadas (% de episodios que las incluyen)", fig_rep),
        chart_box("Actores movilizados (% de episodios en los que participan)", fig_act),
        chart_box("Densidad por episodio (promedio de actores y demandas)", fig_dens),

        html.Div([
            html.H5("El hallazgo de la densidad"),
            html.P("Chubut funciona como un conflicto de agregación: muchos episodios simples, con un actor predominante por evento. " \
            "Jujuy funciona como un conflicto de articulación: menos episodios, pero con más actores y demandas combinadas por evento. " \
            "Limitación. La densidad se mide por codificación de menciones en prensa; puede reflejar estilo periodístico además de la " \
            "organización real del conflicto.")
        ], className="hallazgo-box"),

        html.Div([
            dcc.Link("← Volver", href="/panorama", className="btn btn-outline-secondary"),
            dcc.Link("Siguiente: Demandas →", href="/demandas", className="btn btn-primary float-end"),
        ], style={"marginTop": "40px", "overflow": "hidden"}),
    ], className="page-container")
])