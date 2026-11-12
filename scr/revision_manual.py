import pandas as pd

# Cargar el corpus ya corregido por el script anterior
df = pd.read_excel("eventos_chubut_corregido.xlsx")

# Excluir filas que no son eventos
df_eventos = df[~df["localidad"].isin(["No aplica", "Error", "Fuera de Chubut"])].copy()

# ============================================
# COLAS DE REVISIÓN
# ============================================
colas = []

def agregar_cola(nombre, mask, campos_extra=None):
    campos_base = ["noticia_id", "titulo", "localidad", "respuesta_estatal",
                   "presencia_policial", "accionar_policial",
                   "tipo_intervencion_estatal", "uso_fuerza", "heridos",
                   "detenciones", "observaciones"]
    if campos_extra:
        campos_base = campos_base + campos_extra
    campos_presentes = [c for c in campos_base if c in df.columns]
    sub = df_eventos.loc[mask, campos_presentes].copy()
    if len(sub) > 0:
        sub["tipo_revision"] = nombre
        colas.append(sub)

# --- Cola 1: Gestión estatal con tipo_intervencion≠2
PATRON_GESTION = r"(?i)reuni|recibi|mediaci|mediar|diálogo|dialog|se comprometió|gestion|prometió|veto|vetó|disculpas|plan de emergencia"
mask_1 = (
    df_eventos["respuesta_estatal"].astype(str).str.contains(PATRON_GESTION, regex=True, na=False)
    & (df_eventos["tipo_intervencion_estatal"] != 2)
)
agregar_cola("Gestión estatal sin código 2", mask_1)

# --- Cola 2: Coerción con tipo_intervencion≠3
PATRON_COERCION = r"(?i)desalojo|despeje|balas|gases|detenciones|detención|represión|disparó|arrestos|prisión preventiva"
mask_2 = (
    df_eventos["respuesta_estatal"].astype(str).str.contains(PATRON_COERCION, regex=True, na=False)
    & (df_eventos["tipo_intervencion_estatal"] != 3)
)
agregar_cola("Coerción estatal sin código 3", mask_2)

# --- Cola 3: uso_fuerza=1 sin presencia policial=1
mask_3 = (
    (df_eventos["uso_fuerza"] == 1)
    & (df_eventos["presencia_policial"] != 1)
)
agregar_cola("uso_fuerza=1 sin presencia policial", mask_3)

# --- Cola 4: accionar_policial=4 (arrestos) con detenciones≠1
mask_4 = (
    (df_eventos["accionar_policial"] == 4)
    & (df_eventos["detenciones"] != 1)
)
agregar_cola("Accionar=4 pero detenciones≠1", mask_4)

# --- Cola 5: tipo_intervencion=3 con uso_fuerza=0
mask_5 = (
    (df_eventos["tipo_intervencion_estatal"] == 3)
    & (df_eventos["uso_fuerza"] == 0)
)
agregar_cola("Represión sin uso_fuerza", mask_5)

# --- Cola 6: Eventos multi-actor no separados
PATRON_MULTI = r"(?i)varias protestas|varias localidades|evento simultáneo"
mask_6 = df_eventos["notas_estandarizacion"].astype(str).str.contains(PATRON_MULTI, regex=True, na=False)
agregar_cola("Eventos multi-actor", mask_6)

# --- Cola 7: Disrupción por servicios paralizados
PATRON_DISRUPCION = r"(?i)paraliz|suspend|sin recolección|sin servicio|paralizó"
mask_7 = (
    df_eventos["observaciones"].astype(str).str.contains(PATRON_DISRUPCION, regex=True, na=False)
    & (df_eventos["disrupcion"] == 0)
)
agregar_cola("Disrupción por servicios", mask_7)

# ============================================
# CONSOLIDAR Y EXPORTAR
# ============================================
if colas:
    revision = pd.concat(colas, ignore_index=True)
    # Ordenar por tipo de revisión para leer agrupado
    revision = revision.sort_values(["tipo_revision", "noticia_id"]).reset_index(drop=True)
    
    # Agregar columna vacía para que anotes el cambio
    revision["ACCION"] = ""  # qué hacer: cambiar a X, dejar como está, etc.
    revision["NUEVO_VALOR"] = ""  # valor corregido
    revision["JUSTIFICACION"] = ""  # por qué
    
    revision.to_excel("revision_manual.xlsx", index=False)
    
    print("=" * 50)
    print("COLA DE REVISIÓN MANUAL")
    print("=" * 50)
    print(f"Total de filas a revisar: {len(revision)}")
    print("\nPor tipo de revisión:")
    print(revision["tipo_revision"].value_counts().to_string())
    print("\nArchivo generado: revision_manual.xlsx")
    print("\nColumnas para completar: ACCION, NUEVO_VALOR, JUSTIFICACION")
else:
    print("No hay filas para revisar.")