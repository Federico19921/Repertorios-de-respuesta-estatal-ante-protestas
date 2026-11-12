import pandas as pd

df = pd.read_excel('C:/Users/Federico/Desktop/TP Opta/data/raw/eventos_chubut.xlsx')
df.columns = [c.strip() for c in df.columns]


reporte = {}

# --- 1. Totales
reporte["Total de filas"] = len(df)
reporte["Filas únicas por noticia_id"] = df["noticia_id"].nunique()
reporte["IDs duplicados (cantidad)"] = df["noticia_id"].duplicated().sum()

# --- 2. Filas con "Error" (no-protesta mal etiquetada)
error_mask = df.apply(lambda r: (r.astype(str) == "Error").any(), axis=1)
reporte["Filas con 'Error'"] = int(error_mask.sum())
reporte["Filas 'No aplica'"] = int((df["localidad"] == "No aplica").sum())

# --- 3. Valores numéricos inválidos
VALORES_PERMITIDOS = {
    "disrupcion": {0, 1, 99},
    "presencia_policial": {0, 1, 99},
    "accionar_policial": {1, 2, 3, 4, 5, 6, 7, 99},
    "tipo_intervencion_estatal": {0, 1, 2, 3, 99},
    "uso_fuerza": {0, 1, 99},
    "heridos": {0, 1, 99},
    "detenciones": {0, 1, 99},
    "judicializacion": {0, 1, 99},
    "coord_interinstitucional": {0, 1, 2, 99},
    "canales_informales": {0, 1, 2, 99},
    "amenaza_politica": {0, 1, 2, 3, 99},
    "resultado_episodio": {0, 1, 2, 3, 99},
}
invalidos = {}
for campo, permitidos in VALORES_PERMITIDOS.items():
    if campo in df.columns:
        serie = pd.to_numeric(df[campo], errors="coerce")
        mask = ~serie.isin(permitidos) & serie.notna()
        if mask.sum() > 0:
            invalidos[campo] = df.loc[mask, ["noticia_id", campo]].to_dict("records")
reporte["Campos con valores inválidos"] = invalidos

FUERA_DE_CHUBUT = {"El Bolsón", "Ushuaia"}
df_fuera = df[df["localidad"].isin(FUERA_DE_CHUBUT)]
reporte["Filas fuera de Chubut"] = df_fuera[["noticia_id", "localidad"]].to_dict("records")

SOSPECHOSAS = {"Ate", "Madryn", "Puerto Rawson", "Parque Nacional Los Alerces"}
df_sosp = df[df["localidad"].isin(SOSPECHOSAS)]
reporte["Localidades sospechosas"] = df_sosp[["noticia_id", "localidad"]].to_dict("records")

df_mayus = df[df["escala"].isin(["ALTA", "MEDIA", "BAJA"]) | df["intensidad"].isin(["ALTA", "MEDIA", "BAJA"])]
reporte["Filas con mayúsculas en escala/intensidad"] = df_mayus[["noticia_id", "escala", "intensidad"]].to_dict("records")

mask_poli = (
    df["actores_participantes"].astype(str).str.contains(
        "polic|CoBiPol|Consejo de Bienestar", case=False, na=False
    )
    & (df["presencia_policial"] == 1)
)
reporte["Policías manifestantes con presencia_policial=1"] = df.loc[
    mask_poli, ["noticia_id", "actores_participantes", "presencia_policial"]
].to_dict("records")

reporte["Distribución por localidad (top 10)"] = df["localidad"].value_counts().head(10).to_dict()
reporte["Distribución por tipo_accion"] = df["tipo_accion"].value_counts().to_dict()
reporte["Distribución por resultado_episodio"] = df["resultado_episodio"].value_counts().to_dict()

# --- Imprimir
for k, v in reporte.items():
    print(f"\n=== {k} ===")
    print(v if not isinstance(v, list) else pd.DataFrame(v).to_string(index=False))

df["fecha_publicacion"] = df["fecha_publicacion"].astype(str).str.zfill(8)
df["mes"] = df["fecha_publicacion"].str[:6]
print(df["mes"].value_counts().sort_index())

print(pd.crosstab(df["tipo_accion"], df["resultado_episodio"]))
print(pd.crosstab(df["mes"], df["resultado_episodio"]))