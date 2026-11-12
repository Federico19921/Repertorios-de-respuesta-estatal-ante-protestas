import json
import pandas as pd
from collections import OrderedDict

# ------------------------------------------------------------
# 1. Cargar el JSON completo
# ------------------------------------------------------------
with open('output_chubut_prueba.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# ------------------------------------------------------------
# 2. MAPEO EXPLÍCITO (cubre todas las variantes de los ejemplos)
# ------------------------------------------------------------
CANONICAL_MAP = {
    # === Claves del evento simple (minúsculas con guión bajo) ===
    'id': 'id',
    'localidad': 'localidad',
    'actores_participantes': 'actores_participantes',
    'demanda_principal': 'demanda_principal',
    'tipo_accion': 'tipo_accion',
    'tipo_accion_detalle': 'tipo_accion_detalle',
    'disrupcion': 'disrupcion',
    'escala': 'escala',
    'intensidad': 'intensidad',
    'respuesta_estatal': 'respuesta_estatal',
    'presencia_policial': 'presencia_policial',
    'accionar_policial': 'accionar_policial',
    'tipo_intervencion_estatal': 'tipo_intervencion_estatal',
    'uso_fuerza': 'uso_fuerza',
    'heridos': 'heridos',
    'detenciones': 'detenciones',
    'judicializacion': 'judicializacion',
    'coord_interinstitucional': 'coord_interinstitucional',
    'canales_informales': 'canales_informales',
    'amenaza_politica': 'amenaza_politica',
    'resultado_episodio': 'resultado_episodio',
    'fuente': 'fuente',
    'observaciones': 'observaciones',
    'notas_estandarizacion': 'notas_estandarizacion',

    # === Claves del evento múltiple (mayúsculas, espacios, tildes) ===
    'ID': 'id',
    'Localidad': 'localidad',
    'Actores participantes': 'actores_participantes',
    'Demanda principal': 'demanda_principal',
    'Tipo de acción': 'tipo_accion',
    'Tipo de acción_detalle': 'tipo_accion_detalle',
    'Disrupción': 'disrupcion',
    'Escala': 'escala',
    'Intensidad': 'intensidad',
    'Respuesta estatal': 'respuesta_estatal',
    'Presencia policial': 'presencia_policial',
    'Accionar policial / Tipo de presencia policial': 'accionar_policial',
    'Tipo de intervención estatal': 'tipo_intervencion_estatal',
    'Uso de fuerza': 'uso_fuerza',
    'Heridos': 'heridos',
    'Detenciones': 'detenciones',
    'Judicialización': 'judicializacion',
    'Coordinación interinstitucional': 'coord_interinstitucional',
    'Activación canales informales': 'canales_informales',
    'Nivel de amenaza política': 'amenaza_politica',
    'Resultado del episodio': 'resultado_episodio',
    'Fuente': 'fuente',
    'Observaciones': 'observaciones',
    'Notas_estandarizacion': 'notas_estandarizacion',

    # === Posibles variantes adicionales (por si aparecen) ===
    'accionar_policial___tipo_de_presencia_policial': 'accionar_policial',
    'tipo_de_acción': 'tipo_accion',
    'tipo_de_acción_detalle': 'tipo_accion_detalle',
    'uso_de_fuerza': 'uso_fuerza',
    'nivel_de_amenaza_política': 'amenaza_politica',
    'resultado_del_episodio': 'resultado_episodio',
    'coordinación_interinstitucional': 'coord_interinstitucional',
    'judicialización': 'judicializacion',
}

# ------------------------------------------------------------
# 3. Extraer eventos (uno por cada elemento en la lista 'events' o 'eventos')
# ------------------------------------------------------------
all_rows = []

for noticia in data:
    # Campos fijos de la noticia (los renombramos para no chocar con 'id' del evento)
    base = {
        'noticia_id': noticia.get('id', ''),
        'link': noticia.get('link', ''),
        'fecha_publicacion': noticia.get('fecha_publicacion', ''),
        'titulo': noticia.get('titulo', '')
    }

    datos = noticia.get('datos_extraidos', {})

    # Detectar si hay lista de eventos
    if 'events' in datos and isinstance(datos['events'], list):
        eventos_list = datos['events']
    elif 'eventos' in datos and isinstance(datos['eventos'], list):
        eventos_list = datos['eventos']
    else:
        # Si no hay lista, todo 'datos_extraidos' es un solo evento
        eventos_list = [datos]

    for ev in eventos_list:
        fila = OrderedDict()
        # Añadir campos base
        for k, v in base.items():
            fila[k] = v
        # Añadir campos del evento (mapeados)
        for k, v in ev.items():
            if k.startswith('_'):
                continue
            # Si la clave está en el mapa, usar el nombre canónico; si no, dejarla tal cual (pero no debería pasar)
            canon = CANONICAL_MAP.get(k, k)
            fila[canon] = v
        all_rows.append(fila)

print(f"Se generaron {len(all_rows)} filas (eventos)")

# ------------------------------------------------------------
# 4. Unificar columnas: todas las filas deben tener las mismas claves
# ------------------------------------------------------------
# Recoger todas las claves en orden de primera aparición
all_keys = []
for row in all_rows:
    for k in row.keys():
        if k not in all_keys:
            all_keys.append(k)

# Rellenar filas con claves faltantes (valor vacío '')
for i, row in enumerate(all_rows):
    new_row = OrderedDict()
    for k in all_keys:
        new_row[k] = row.get(k, '')
    all_rows[i] = new_row

# ------------------------------------------------------------
# 5. Crear DataFrame y guardar a Excel
# ------------------------------------------------------------
df = pd.DataFrame(all_rows)

output_file = 'eventos_chubut_SIN_DUPLICADOS.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Archivo guardado: {output_file}")
print(f"Número de columnas: {len(df.columns)}")
print(f"Columnas: {list(df.columns)}")