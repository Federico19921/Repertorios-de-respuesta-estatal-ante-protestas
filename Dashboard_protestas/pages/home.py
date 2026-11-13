import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Inicio")

def card_tema(titulo, descripcion, href, color):
    return dbc.Col(
        dcc.Link(
            dbc.Card([
                dbc.CardBody([
                    html.Div(style={
                        "width": "40px",
                        "height": "4px",
                        "backgroundColor": color,
                        "marginBottom": "16px",
                        "borderRadius": "2px"
                    }),
                    html.H5(titulo),
                    html.P(descripcion, className="text-muted mb-0",
                           style={"fontSize": "0.85rem"})
                ])
            ], style={"height": "100%"}),
            href=href,
            className="tema-card"
        ),
        width=6,
        className="mb-4"
    )

layout = html.Div([
    html.H1("Dos provincias, dos respuestas estatales"),
    html.P(
        "Un análisis comparado de la respuesta estatal a dos ciclos de protesta: Chubut (oct 2021 – ene 2022, n=121) y Jujuy (jun – ago 2023, n=66). Los datos combinan codificación asistida por LLM con revisión manual.",
        className="text-muted mb-5"
    ),

    html.H2("Explorá el análisis"),

    dbc.Row([
        card_tema("Panorama general",
                  "Cuántos episodios hubo, cuándo se concentraron y qué revela la comparación.",
                  "/panorama", "#7BB4C2"),
        card_tema("Repertorios y actores",
                  "Qué tácticas se usaron y qué actores las sostuvieron.",
                  "/repertorios", "#9D9ECE"),
        card_tema("Demandas",
                  "Qué se reclamó y cuántas demandas se combinaron por episodio.",
                  "/demandas", "#2E86AB"),
        card_tema("Cruces",
                  "Qué actor sostuvo qué reclamo",
                  "/cruces", "#A23B72"),
        card_tema("Represión",
                  "Cómo respondió el Estado y a quién castigó.",
                  "/represion", "#E53935"),
        card_tema("Métodos",
                  "Cómo se construyeron los datos y qué no se puede concluir.",
                  "/metodos", "#6B7280"),
    ]),

], className="page-container")