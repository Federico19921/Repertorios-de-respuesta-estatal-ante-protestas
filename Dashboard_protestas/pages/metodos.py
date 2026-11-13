import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/metodos", name="Métodos")

layout = html.Div([
    html.Div("Inicio | Trabajo e ingresos | Métodos", className="breadcrumbs"),
    html.Div([
        html.H1("¿Cómo se construyeron los datos?"),
        html.P("Decisiones de codificación, revisión y limitaciones del corpus. Todo el código y los datos están disponibles en el repositorio.", style={"fontSize": "1.1rem", "color": "#4B5563"}),

        html.Div([
            html.H2("Fuente de datos"),
            html.P("Chubut. Codificación asistida por LLM (Groq · openai/gpt-oss-20b) con un libro de códigos estructurado en JSON, derivado de la definición tillyana de acción contenciosa discontinua."),
            html.P("Jujuy. Base provista por la cátedra, codificada manualmente."),

            html.H2("Definición de protesta"),
            html.P("Se utilizó la definición de acción contenciosa de Tilly y Tarrow (2015). Se incluyeron únicamente las noticias que reportaban un hecho ocurrido. Se excluyeron anuncios de protestas futuras, notas de opinión y artículos que no describían una acción concreta."),

            html.H2("Definición de represión segun ACLED"),
            html.P("Se considera represión a los eventos con subtipos 'Protest with intervention' o 'Excessive force against protesters', o con uso de fuerza confirmado. Se distingue de otras formas de intervención estatal como monitoreo, contención o disuasión."),

            html.H2("Limitaciones"),

# --- Sesgos de fuente ---
html.H3(
    "Sesgos de fuente",
    style={
        "fontSize": "1.15rem",
        "fontWeight": "600",
        "color": "#1F2937",
        "marginTop": "24px",
        "marginBottom": "8px",
    },
),
html.Ul([
    html.Li("La cobertura periodística subrepresenta protestas pequeñas o rurales."),
    html.Li("Chubut tiene 24,8% de episodios sin datos de respuesta estatal; Jujuy, 19,8%. La tasa ajustada corrige parcialmente este sesgo."),
]),

# --- Sesgos de codificación ---
html.H3(
    "Sesgos de codificación",
    style={
        "fontSize": "1.15rem",
        "fontWeight": "600",
        "color": "#1F2937",
        "marginTop": "24px",
        "marginBottom": "8px",
    },
),
html.Ul([
    html.Li([
        "La codificación con LLM introduce riesgo de alucinación: se revisaron manualmente 20 de 121 episodios de Chubut y se detectaron casos, corregidos en ",
        html.Code(
            "data/processed/",
            style={
                "backgroundColor": "#F3F4F6",
                "padding": "2px 6px",
                "borderRadius": "4px",
                "fontSize": "0.9em",
            },
        ),
        ".",
    ]),
    html.Li("La diferencia de tamaño entre corpus (121 vs. 66) se aborda con comparaciones relativas (porcentajes), no absolutas."),
]),

# --- Sesgos de inferencia ---
html.H3(
    "Sesgos de inferencia",
    style={
        "fontSize": "1.15rem",
        "fontWeight": "600",
        "color": "#1F2937",
        "marginTop": "24px",
        "marginBottom": "8px",
    },
),
html.Ul([
    html.Li("Las asociaciones observadas (represión–repertorio, represión–actor) no implican causalidad."),
    html.Li("El n de causas judiciales es bajo; los porcentajes deben leerse como indicio."),
]),

            html.H2("Uso de ACLED"),
            html.P("Se consultó ACLED para el período 2020-2024. Solo se encontraron 8 eventos de represión para Chubut y Jujuy combinadas, todos ya presentes en la base propia. Se optó por usar la base propia como fuente principal y mencionar ACLED únicamente como contexto nacional."),
        ]),

        html.Div([
            dcc.Link("← Volver al inicio", href="/", className="btn btn-outline-secondary"),
        ], style={"marginTop": "40px"}),
    ], className="page-container")
])