import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

dash.register_page(__name__, path="/panorama", name="Panorama")

df = pd.read_csv("data/eventos.csv")
df["fecha"] = pd.to_datetime(df["fecha"])

COLOR_CHUBUT = "#2E86AB"
COLOR_JUJUY = "#A23B72"

# Configuración de Plotly limpia (sin cuadros)
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

df["mes"] = df["fecha"].dt.to_period("M").astype(str)
serie = df.groupby(["mes", "provincia"]).size().reset_index(name="n")

fig_serie = px.line(
    serie, x="mes", y="n", color="provincia", markers=True,
    color_discrete_map={"Chubut": COLOR_CHUBUT, "Jujuy": COLOR_JUJUY},
    labels={"mes": "Mes", "n": "Eventos", "provincia": ""}
)
fig_serie.update_layout(height=350)
fig_serie = aplicar_estilo(fig_serie)

layout = html.Div([
    # 1. Breadcrumbs
    html.Div("Inicio | Trabajo e ingresos | Protestas", className="breadcrumbs"),
    
    html.Div([
        # 2. Título principal
        html.H1("Dos ciclos, dos estrategias"),
        
        # 3. Texto introductorio
        html.P(
            "Chubut (oct 2021 – ene 2022, n=121) y Jujuy (jun – ago 2023, n=66) " \
            "son dos ciclos de conflicto con desenlaces opuestos: " \
            "derogación de la ley minera en un caso, sostenimiento de la reforma con represión en el otro. " \
            "Esta página resume el volumen, la temporalidad y el nivel de represión de cada ciclo."
        ),
        
        # 4. Sección de Mensajes Clave (Estilo Argendata)
        html.Div([
            html.H4("Mensajes clave", className="mensajes-clave-title"),
            dbc.Row([
                dbc.Col(html.Div("Chubut registró casi el doble de episodios que Jujuy (121 vs. 66), pero en un período más largo (4 meses vs. 3).", className="mensaje-card"), width=3),
                dbc.Col(html.Div("La represión fue más frecuente en Jujuy (7,6% vs. 4,1%). La diferencia se sostiene aun ajustando por cobertura (ver Represión).", className="mensaje-card destacado"), width=3),
                dbc.Col(html.Div("El corte de ruta fue el repertorio con mayor tasa de represión en ambos casos (Jujuy: 28,6%; Chubut: 7,7%).", className="mensaje-card"), width=3),
                dbc.Col(html.Div("Los episodios de Jujuy articulan más demandas por evento (1,48 vs. 0,95 en Chubut).", className="mensaje-card"), width=3),
            ])
        ], className="mensajes-clave-wrapper"),
        
        # 5. El Gráfico enmarcado (Estilo Argendata)
        html.Div([
            html.Div([
                html.P("Eventos por mes", className="chart-title"),
                html.Div("⬇️ ⛶", style={"color": "#999", "fontSize": "14px"}) # Simulación de botones
            ], className="chart-header"),
            html.P("Evolución de la cantidad de eventos registrados por mes en cada provincia.", className="chart-subtitle"),
            html.Div(dcc.Graph(figure=fig_serie, config={'displayModeBar': False}), className="chart-body"),
            html.Div("Fuente: base propia (n=187 episodios; 121 Chubut, 66 Jujuy) · Período: oct 2021 – ago 2023 · Codificación asistida por LLM + revisión manual.", className="chart-footer")
        ], className="chart-container"),
        
        # 6. Hallazgo final
        html.Div([
            html.H5("Hallazgo"),
            html.P("Lectura comparada. Los datos son compatibles con dos estrategias provinciales distintas: desescalada política en Chubut (derogación de la ley de zonificación) y sostenimiento con represión en Jujuy (reforma constitucional mantenida, con uso de fuerza y judicialización). " \
            "Limitación. Esta lectura se basa en los episodios cubiertos por prensa; no permite afirmar intencionalidad estatal, solo asociación entre contexto y repertorio de respuesta.")
        ], className="hallazgo-box"),

        # 7. Botones de navegación
        html.Div([
            dcc.Link("← Volver al inicio", href="/", className="btn btn-outline-secondary"),
            dcc.Link("Siguiente: Repertorios →", href="/repertorios", className="btn btn-primary float-end"),
        ], style={"marginTop": "40px", "overflow": "hidden"}),
        
    ], className="page-container")
])