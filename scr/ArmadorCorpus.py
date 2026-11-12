"""
================================================================================
CODIFICADOR AUTOMÁTICO DE PROTESTAS — CHUBUT
================================================================================

DESCRIPCIÓN
-----------
Pipeline que toma un Excel con links a noticias periodísticas sobre protestas
en la provincia de Chubut (Argentina), scrapea el cuerpo de cada noticia, y usa
un LLM (Groq · `openai/gpt-oss-20b`) para extraer variables estructuradas según
un libro de códigos basado en la definición de acción colectiva contenciosa
discontinua de Charles Tilly.

FLUJO
-----
    Excel "Artículos" (Fecha / Link / Título)
        │
        ▼
    leer_links_desde_excel()        → List[{fecha, titulo, link}]
        │
        ▼
    scrape_article(url)             → {url, title, raw_text}
        │
        ▼
    extract_with_groq(text, title)  → Dict con claves estandarizadas
        │  (mapea español → estándar vía MAPEO_CLAVES
        │   y rellena claves faltantes con "No especificado" / 99)
        ▼
    validar_estructura()  +  validar_coherencia()
        │
        ▼
    output_chubut_prueba.json                       (noticias procesadas)
    reporte_validacion_chubut_prueba.json           (noticias con errores)

ENTRADA
-------
Archivo Excel en la raíz del proyecto:
    links_el_chubut_completo nov_dic_ene.xlsx
Hoja: "Artículos". Columnas:
    - "Fecha"  (obligatoria)
    - "Link"   (obligatoria)
    - "Título" (opcional; si falta se usa "Sin título")

SALIDA
------
- output_chubut_prueba.json : lista de noticias con datos extraídos.
  Cada ítem:
    {
      "id": <fecha>,
      "link": <url>,
      "fecha_publicacion": <fecha>,
      "titulo": <título>,
      "datos_extraidos": {<24 variables del libro de códigos>},
      "_errores_validacion": [<opcional, si hubo problemas>]
    }
- reporte_validacion_chubut_prueba.json : solo las noticias con errores.

DEPENDENCIAS
------------
    pip install requests beautifulsoup4 groq pandas openpyxl

VARIABLES DE ENTORNO
--------------------
    NINGUNA por ahora. La API key de Groq está hardcodeada (ver CONFIGURACIÓN
    y sección DEUDA TÉCNICA al final del archivo).

EJECUCIÓN
---------
    python codificador_protestas.py

NOTAS
-----
- Entre llamadas a Groq se espera `time.sleep(8)` para respetar rate limits.
- Los errores de validación NO bloquean el guardado: se adjuntan al campo
  `_errores_validacion` y se replican en el reporte.
- Ver bloque final "LIBRO DE CÓDIGOS (RESUMEN)" y "DEUDA TÉCNICA" para el
  detalle de las variables y los issues pendientes.

================================================================================
"""

import json
import re
import time
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from groq import Groq
import pandas as pd
import datetime  # noqa: F401  (reservado para uso futuro; hoy no se usa)


# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================
# Modelo de Groq y cliente. La API key está hardcodeada por simplicidad en la
# fase de prototipo; ver "DEUDA TÉCNICA" al final del archivo.
# ----------------------------------------------------------------------------
API_KEY =
client = Groq(api_key=API_KEY)
MODELO = "openai/gpt-oss-20b"

# Rutas "declarativas" — actualmente NO se usan (los paths reales están
# hardcodeados dentro de main()). Se conservan para refactor futuro.
ARCHIVO_RESULTADOS = 'output/resultados'
ARCHIVO_LECTURA = 'data/raw'


# ============================================================================
# 2. MAPEO DE CLAVES (español del LLM → nombre estándar)
# ============================================================================
# El SYSTEM_PROMPT pide las claves en español (para que el LLM devuelva algo
# legible) y este diccionario las traduce a snake_case estable para el JSON
# de salida. Si el LLM devuelve una clave que no está acá, se conserva tal cual
# (ver extract_with_groq paso 4).
# ----------------------------------------------------------------------------
MAPEO_CLAVES = {
    "ID": "id",
    "Localidad": "localidad",
    "Actores participantes": "actores_participantes",
    "Demanda principal": "demanda_principal",
    "Tipo de acción": "tipo_accion",
    "Tipo de acción_detalle": "tipo_accion_detalle",
    "Disrupción": "disrupcion",
    "Escala": "escala",
    "Intensidad": "intensidad",
    "Respuesta estatal": "respuesta_estatal",
    "Presencia policial": "presencia_policial",
    "Accionar policial / Tipo de presencia policial": "accionar_policial",
    "Tipo de intervención estatal": "tipo_intervencion_estatal",
    "Uso de fuerza": "uso_fuerza",
    "Heridos": "heridos",
    "Detenciones": "detenciones",
    "Judicialización": "judicializacion",
    "Coordinación interinstitucional": "coord_interinstitucional",
    "Activación canales informales": "canales_informales",
    "Nivel de amenaza política": "amenaza_politica",
    "Resultado del episodio": "resultado_episodio",
    "Fuente": "fuente",
    "Observaciones": "observaciones",
    "Notas_estandarizacion": "notas_estandarizacion",
}


# ============================================================================
# 3. LECTURA DE LINKS DESDE EXCEL
# ============================================================================
def leer_links_desde_excel(archivo: str, limite: int = 5) -> List[Dict]:
    """
    Lee la hoja "Artículos" de un Excel y devuelve los links a procesar.

    Args:
        archivo: Ruta al archivo .xlsx. Debe tener la hoja "Artículos" con
            las columnas "Fecha" y "Link"; "Título" es opcional.
        limite: Cantidad máxima de artículos a devolver. En main() se llama
            con ``limite=None`` para procesar todos (ojo: iterar [:None]
            devuelve la lista completa).

    Returns:
        Lista de diccionarios con claves ``fecha``, ``titulo`` y ``link``.
        Devuelve ``[]`` si:
          - el archivo no se puede leer,
          - faltan las columnas "Fecha" o "Link",
          - no hay filas con link válido.

    Notes:
        No levanta excepciones: los errores se imprimen por stdout y se
        devuelve lista vacía.
    """
    try:
        df = pd.read_excel(archivo, sheet_name="Artículos")
    except Exception as e:
        print(f"Error leyendo el Excel: {e}")
        return []

    if "Fecha" not in df.columns or "Link" not in df.columns:
        print("El Excel debe tener columnas 'Fecha' y 'Link'")
        return []

    articulos = []
    for _, row in df.iterrows():
        fecha = str(row["Fecha"]) if pd.notna(row["Fecha"]) else "Fecha no encontrada"
        titulo = (
            row["Título"]
            if "Título" in df.columns and pd.notna(row["Título"])
            else "Sin título"
        )
        link = row["Link"] if pd.notna(row["Link"]) else None
        if link:
            articulos.append({"fecha": fecha, "titulo": titulo, "link": link})

    return articulos[:limite]


# ============================================================================
# 4. SYSTEM_PROMPT — LIBRO DE CÓDIGOS ENVIADO AL LLM
# ============================================================================
# Este string ES el libro de códigos operativo. Cualquier cambio en definiciones,
# escalas o reglas de segmentación debe reflejarse acá Y en CLAVES_REQUERIDAS /
# VALORES_PERMITIDOS / CAMPOS_NUMERICOS más abajo.
#
# Resumen de las 24 variables codificadas (detalle completo en el prompt):
#   Texto:
#     1.  ID                       (YYYYMMDD + nro de episodio)
#     2.  Localidad                (ciudad > provincia > "No especificado")
#     3.  Actores participantes    (separados por "/"; NO incluye Estado)
#     4.  Demanda principal        (1 frase)
#     5.  Tipo de acción           (enum cerrado)
#     6.  Tipo de acción_detalle   (detalle libre)
#     9.  Respuesta estatal
#     21. Fuente                   (URL)
#     22. Observaciones
#     23. Notas_estandarizacion
#   Ordinales / categóricos:
#     6.  Disrupción               (0/1/99)
#     7.  Escala                   (baja/media/alta)
#     8.  Intensidad               (baja/media/alta)
#     10. Presencia policial       (0/1/99)
#     11. Accionar policial        (1..7 / 99)
#     12. Tipo de intervención     (0/1/2/3/99)
#     13. Uso de fuerza            (0/1/99)
#     16. Judicialización          (0/1/99)
#     17. Coordinación interinst.  (0/1/2/99)
#     18. Canales informales       (0/1/2/99)
#     19. Amenaza política         (0..3 / 99)
#     20. Resultado del episodio   (0..3 / 99)
#   Numéricos:
#     14. Heridos                   (nro / 99)  [ver DEUDA TÉCNICA]
#     15. Detenciones               (nro / 99)  [ver DEUDA TÉCNICA]
#
# Reglas de negocio que el prompt impone y que validar_coherencia() luego
# controla programáticamente:
#   - Corte ⇒ disrupción = 1
#   - Disrupción = 1 ⇒ intensidad ∈ {media, alta}
#   - Represión (intervención = 3) ⇒ uso_fuerza = 1
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = """
Sos un asistente de investigación especializado en codificación de protestas. Tenés que extraer información de noticias periodísticas y estructurarla según el siguiente libro de códigos.

DEFINICIÓN DE PROTESTA:
Utilizamos la definición de Charles Tilly de acción colectiva contenciosa discontinua: ocasiones en las que las personas actúan conjuntamente en defensa de sus intereses de maneras que afectan visible y significativamente los intereses de otras personas. Se requiere un mínimo de tres personas para que un evento se considere "colectivo".

REGLAS DE CODIFICACIÓN:

1. Separar eventos SOLO si la noticia menciona EXPLÍCITAMENTE que hay protestas en diferentes lugares o con diferentes actores. Por ejemplo, si la noticia dice "En Rawson, docentes cortaron la ruta; en Trelew, estudiantes marcharon", son DOS EVENTOS. Pero si la noticia describe una misma protesta en varios párrafos (ej: primero describe la marcha, después los cortes, después las detenciones), es UN SOLO EVENTO. No separar una misma protesta aunque se describa en varios párrafos. Si hay dudas, codificá como UN SOLO evento.
2. Toda la codificación se basa ÚNICAMENTE en la información publicada en la noticia. NO infieras ni deduzcas información que no esté explícita.
3. Si una información no aparece en la noticia, usá el valor 99 (sin datos) o "No especificado" según corresponda.
4. Solo codificar eventos que ya están ocurriendo o que ya ocurrieron. Si la noticia anuncia una protesta futura (ej: "los docentes realizarán un paro mañana", "se convoca a una marcha para el próximo martes", "planean un corte de ruta"), NO la codifiques. En ese caso, devolvé todos los campos de texto con "No aplica" y los numéricos con 99. Solo codificá si la acción ya está en desarrollo o ya sucedió (ej: "los docentes realizaron un paro", "están llevando a cabo una asamblea", "cortaron la ruta").

VARIABLES A EXTRAER (formato JSON):

1. ID: Texto libre (usá el formato año mes dia + número de episodio. Ej: 20211201 para el primer episodio del 1/12/2021)
2. Localidad: Texto. Extraé la ciudad o localidad más específica que aparezca en la noticia. Revisá primero el título, porque suele contener la ubicación. Si el título menciona una ciudad (ej: "Rawson", "Trelew", "Esquel"), usá esa. Si no, buscá en el cuerpo de la noticia. Si se menciona una ciudad en el cuerpo, usá esa. Si solo aparece la provincia (ej: "Chubut"), usá la provincia. Si no aparece ninguna ubicación, usá "No especificado". No uses "Chubut" si la noticia menciona una ciudad.
3. Actores participantes: Texto. ¿Quiénes protestan? Listá SOLO los actores que se manifiestan o protestan, exactamente como los nombra la noticia. NO incluyas al gobierno, fuerzas de seguridad, ni a las autoridades como actores participantes (ellos son el target o el receptor de la protesta, no quienes protestan). Si la noticia menciona a varios actores, separalos con "/". Ejemplo: "Docentes/Comunidades indígenas/Estudiantes".
4. Demanda principal: Texto (resumí en una frase el reclamo principal)
5. Tipo de acción: Elegí el término más específico de esta lista: "Marcha", "Corte", "Acampe", "Toma de edificio", "Mixta", "Asamblea", "Paro", "Manifestación", "Reunión", "Escrache", "Cacerolazo", "Caravana", "Sentada", "Festival", "Pintadas", "Destrozos", "Apagón", "Difusión de comunicado", "Recolección de firmas", "Acto". Si ninguna describe la acción, usá "Otra".
   - "Mixta" se usa cuando la protesta combina varias formas de acción (ej: marcha + corte, o paro + movilización).
   - "Corte" incluye cualquier interrupción (ruta, calle, puente, servicio, acceso, etc.). En "Tipo de acción_detalle" especificá QUÉ se corta.
6. Tipo de acción_detalle: Texto. Detalles adicionales de la acción. Si es "Corte", indicá el objeto (ej: "ruta nacional 3", "servicio de luz"). Para otros casos, podés agregar información relevante (ej: "marcha con antorchas", "paro de 48 horas"). Si no hay detalles, dejalo vacío.
6. Disrupción: 0 (no) o 1 (sí) - ¿La protesta interrumpe la circulación (calles/rutas), bloquea actividades, impide el funcionamiento normal de servicios, o genera alteración visible del orden público? Una marcha o concentración en una plaza NO es disruptiva.
7. Escala: "baja", "media" o "alta"
   - BAJA: pocos participantes; acción localizada (una escuela, barrio, oficina); un solo actor.
   - MEDIA: varias decenas o cientos; una ciudad o localidad; uno o dos sectores.
   - ALTA: gran cantidad (cientos/miles), múltiples localidades o toda la provincia; articulación multisectorial.
   - Codificá como ALTA si hay al menos 2 de: ampliación geográfica, muchos actores, lenguaje de masividad. Media si hay 1 y Baja si no hay ninguno.
8. Intensidad: "baja", "media" o "alta"
   - La intensidad NO depende de la represión. Es combinación de disrupción y escala.
   - Si la protesta es MASIVA pero NO disruptiva → intensidad MEDIA.
   - Si la protesta es MASIVA Y disruptiva → intensidad ALTA.
   - Si es POCOS participantes Y disruptiva → intensidad MEDIA.
   - Si es POCOS participantes Y NO disruptiva → intensidad BAJA.
9. Respuesta estatal: Texto (describí cómo aparece el Estado según la noticia. Si no aparece, usá "No especificado").
10. Presencia policial: 0 (no), 1 (sí), 99 (sin datos) - ¿La noticia menciona a la policía?
11. Accionar policial / Tipo de presencia policial: (solo si aparece en la noticia). Usá UNO de estos códigos numéricos:
    1 = aparecer/estar presente pero sin accionar (con carros hidrantes/escudos/caballos)
    2 = custodiar edificio/casa/institución (con vallado o similar)
    3 = evitar el paso
    4 = hacer arrestos/detenciones
    5 = desalojos (corte de ruta/edificios)
    6 = hacer uso de fuerza física mano a mano (empujar, golpear)
    7 = hacer uso de fuerza con armas (armas, gas lacrimógeno, balas de goma, fuego, bombas)
    99 = sin datos (si no se menciona o no hay suficiente información)
12. Tipo de intervención estatal: 0 (ausencia), 1 (monitoreo/presencia preventiva), 2 (contención/gestión), 3 (represión/coerción), 99 (sin datos)
    - 0: No hay intervención estatal.
    - 1: Policía o autoridades presentes observando, vigilando, sin intervenir sobre el desarrollo de la protesta.
    - 2: El Estado ordena, controla o gestiona la situación (ej: organiza el tránsito, establece un perímetro, intima a liberar un corte) sin usar coerción directa para dispersar o desalojar.
    - 3: Se emplea coerción directa para dispersar, desalojar, detener o controlar físicamente a manifestantes (ej: avanzan, golpean, disparan gases o balas de goma, realizan arrestos o desalojos forzosos).
13. Uso de fuerza: 0 (no), 1 (sí), 99 (sin datos) - ¿Hubo uso de fuerza física (golpes, gases, balas de goma, etc.)? Esto es un indicador de represión directa.
14. Heridos: Número (si hay heridos) o 99 (sin datos)
15. Detenciones: Número (si hay detenciones) o 99 (sin datos)
16. Judicialización: 0 (no), 1 (sí), 99 (sin datos) - ¿Intervino el sistema judicial (causas, imputaciones, acciones legales)?
17. Coordinación interinstitucional: 0 (no), 1 (débil), 2 (clara), 99 (sin datos) - ¿Hay acción conjunta entre distintos actores estatales (gobierno, policía, justicia)?
18. Activación canales informales: 0 (no), 1 (posible), 2 (explícito), 99 (sin datos) - ¿Hay uso de vínculos no formalizados (diálogo directo, contactos personales) para gestionar el conflicto?
19. Nivel de amenaza política: 0 (sin amenaza), 1 (baja), 2 (media), 3 (alta), 99 (sin datos)
    - 0: No cuestiona decisiones del gobierno.
    - 1: Cuestiona una política, pero es acotado y fácilmente gestionable.
    - 2: Afecta una decisión relevante, genera costos políticos, o se extiende territorialmente.
    - 3: Desafía la autoridad o capacidad de gobierno, genera crisis política, o provoca respuesta extraordinaria.
20. Resultado del episodio: 0 (continúa), 1 (desmovilización), 2 (desalojo), 3 (negociación), 99 (sin datos)
    - 0: La protesta sigue activa.
    - 1: Los manifestantes se retiran voluntariamente.
    - 2: La protesta es desalojada por la fuerza.
    - 3: Hay acuerdo o negociación entre las partes.
21. Fuente: Texto (URL de la noticia, si está disponible)
22. Observaciones: Texto (cualquier otra información relevante que no entre en las variables anteriores, especialmente si aparecen varias protestas en la misma noticia)
23. Notas_estandarizacion: Texto (si hay alguna observación sobre la codificación, ej: "varias protestas en una nota", "fecha inferida", etc. Si no, usá "No especificado").

INSTRUCCIONES FINALES:
- Devolvé SOLO el JSON sin explicaciones adicionales.
- Usá formato JSON válido (claves entre comillas dobles, valores separados por comas).
- Si una variable no aparece en la noticia, usá "No especificado" para texto y 99 para numéricas.
- La codificación debe ser ESTRICTAMENTE a partir de la información explícita de la noticia. NO infieras ni deduzcas.

Noticia:
"""


# ============================================================================
# 5. SCRAPING
# ============================================================================
def scrape_article(url: str) -> Dict[str, str]:
    """
    Descarga una noticia y extrae su título y cuerpo de texto.

    Limpia el HTML eliminando <script>, <style>, <nav>, <footer> y <aside>,
    y concatena el contenido de todos los <p>. El texto se normaliza
    (espacios colapsados) y se trunca a 15.000 caracteres.

    Args:
        url: URL de la noticia.

    Returns:
        ``{"url": str, "title": str, "raw_text": str}`` si todo va bien,
        o ``None`` si la descarga o el parseo fallan.

    Notes:
        - Timeout de 15 s.
        - User-Agent de navegador para evitar bloqueos simples.
        - No hay reintentos ni rotación de UA (ver DEUDA TÉCNICA).
        - Páginas que publican el cuerpo en <div>/<article> sin <p> pueden
          devolver raw_text vacío.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()

        title = soup.title.string.strip() if soup.title else ""
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text(strip=True) for p in paragraphs])
        text = re.sub(r'\s+', ' ', text).strip()

        return {"url": url, "title": title, "raw_text": text[:15000]}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


# ============================================================================
# 6. EXTRACCIÓN CON GROQ (con mapeo de claves y validación de valores)
# ============================================================================

# Claves que SIEMPRE debe tener el dict de salida (ya en formato estándar).
# Coincide con MAPEO_CLAVES.values() + "id". Si el LLM omitió alguna, se
# rellena con "No especificado" (texto) o 99 (numérico).
CLAVES_REQUERIDAS = [
    "localidad", "actores_participantes", "demanda_principal",
    "tipo_accion", "tipo_accion_detalle", "disrupcion",
    "escala", "intensidad", "respuesta_estatal",
    "presencia_policial", "accionar_policial",
    "tipo_intervencion_estatal", "uso_fuerza", "heridos",
    "detenciones", "judicializacion", "coord_interinstitucional",
    "canales_informales", "amenaza_politica", "resultado_episodio",
    "fuente", "observaciones", "notas_estandarizacion"
]

# Subconjunto de CLAVES_REQUERIDAS que DEBE ser numérico.
CAMPOS_NUMERICOS = [
    "disrupcion", "presencia_policial", "accionar_policial",
    "tipo_intervencion_estatal", "uso_fuerza", "heridos",
    "detenciones", "judicializacion", "coord_interinstitucional",
    "canales_informales", "amenaza_politica", "resultado_episodio"
]

# Dominio de valores admitido por campo (ver libro de códigos).
# heridos y detenciones se documentan como "nro o 99" pero acá solo se
# admite {0, 1, 99}. Ver DEUDA TÉCNICA al final.
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


def extract_with_groq(text: str, title: str) -> Dict:
    """
    Llama a Groq con el SYSTEM_PROMPT y normaliza la respuesta del LLM.

    Pasos:
        1. Envía título + texto (máx. 12.000 chars) con
           ``response_format=json_object`` y ``temperature=0.1``.
        2. Limpia posibles fences ```json ... ``` que el modelo agregue.
        3. Acepta dos formas de respuesta:
             - ``{"events": [...]}``  → se devuelve tal cual (multi-evento).
             - ``{...}`` o ``[{...}]`` → se toma el primer dict.
        4. Mapea claves español → estándar vía ``MAPEO_CLAVES``. Las claves
           ya estandarizadas se dejan intactas.
        5. Rellena claves faltantes con "No especificado" / 99.

    Args:
        text:  Cuerpo de la noticia (raw_text del scraper).
        title: Título de la noticia.

    Returns:
        - Si el LLM devolvió ``{"events": [...]}``: ``{"events": [...]}``.
          (OJO: el validador posterior NO itera este caso; ver DEUDA TÉCNICA.)
        - En cualquier otro caso: dict plano con todas las CLAVES_REQUERIDAS.
        - Si falla la API o el parseo: dict con "Error" / 99 en cada clave.
    """
    user_content = f"Título: {title}\n\nTexto de la noticia:\n{text[:12000]}"
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        content = response.choices[0].message.content

        content = re.sub(r"```json\n?", "", content)
        content = re.sub(r"\n?```", "", content)
        data = json.loads(content)

        if isinstance(data, dict) and "events" in data:
            return {"events": data["events"]}

        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                data = {}

        mapped_data = {}
        for key, value in data.items():
            new_key = MAPEO_CLAVES.get(key)
            if new_key:
                mapped_data[new_key] = value
            else:
                mapped_data[key] = value

        for key in CLAVES_REQUERIDAS:
            if key not in mapped_data:
                mapped_data[key] = (
                    "No especificado" if key not in CAMPOS_NUMERICOS else 99
                )

        return mapped_data
    except Exception as e:
        print(f"Error en Groq: {e}")
        return {
            key: ("Error" if key not in CAMPOS_NUMERICOS else 99)
            for key in CLAVES_REQUERIDAS
        }


# ============================================================================
# 7. VALIDACIÓN
# ============================================================================
def validar_estructura(data: Dict) -> Dict:
    """
    Valida presencia, no-vacío y tipo/dominio de las claves requeridas.

    Reglas:
        - Todas las CLAVES_REQUERIDAS deben existir y no ser None/"".
        - Los CAMPOS_NUMERICOS deben poder convertirse a int y estar en
          VALORES_PERMITIDOS[campo]. La conversión se hace in-place.

    Args:
        data: Diccionario de datos extraídos.

    Returns:
        ``{"valido": bool, "errores": List[str]}``.
    """
    errores = []
    if not isinstance(data, dict):
        errores.append(f"La respuesta no es un diccionario: {type(data)}")
        return {"valido": False, "errores": errores}

    for clave in CLAVES_REQUERIDAS:
        if clave not in data:
            errores.append(f"Falta clave: {clave}")
        elif data[clave] in [None, ""]:
            errores.append(f"Clave vacía: {clave}")

    for campo in CAMPOS_NUMERICOS:
        if campo in data:
            valor = data[campo]
            permitidos = VALORES_PERMITIDOS.get(campo, set())

            if not isinstance(valor, (int, float)):
                try:
                    valor = int(valor)
                    data[campo] = valor
                except Exception:
                    errores.append(f"Valor no numérico en {campo}: {valor}")
                    continue
            if permitidos and valor not in permitidos:
                errores.append(f"Valor inválido en {campo}: {valor}")

    return {"valido": len(errores) == 0, "errores": errores}


def validar_coherencia(data: Dict) -> Dict:
    """
    Aplica reglas de negocio entre variables (cross-field checks).

    Reglas:
        1. ``tipo_accion == "Corte"`` ⇒ ``disrupcion == 1``
        2. ``disrupcion == 1``         ⇒ ``intensidad != "baja"``
        3. ``tipo_intervencion_estatal == 3`` (represión) ⇒ ``uso_fuerza == 1``

    Args:
        data: Diccionario de datos extraídos.

    Returns:
        ``{"coherente": bool, "inconsistencias": List[str]}``.
    """
    inconsistencias = []
    if data.get("tipo_accion") == "Corte" and data.get("disrupcion") != 1:
        inconsistencias.append("Corte debería tener disrupción=1")
    if data.get("disrupcion") == 1 and data.get("intensidad") == "baja":
        inconsistencias.append("Disrupción=1 implica intensidad mínima media")
    if data.get("tipo_intervencion_estatal") == 3 and data.get("uso_fuerza") != 1:
        inconsistencias.append("Represión (3) implica uso de fuerza=1")
    return {"coherente": len(inconsistencias) == 0, "inconsistencias": inconsistencias}


# ============================================================================
# 8. MAIN — orquesta el pipeline completo
# ============================================================================
def main():
    """
    Ejecuta el pipeline completo:

        1. Localiza el Excel en el cwd (ruta hardcodeada, ver DEUDA TÉCNICA).
        2. Lee los links (limite=None ⇒ todos).
        3. Para cada artículo:
             a. scrape_article
             b. extract_with_groq
             c. validar_estructura + validar_coherencia
             d. adjunta ``_errores_validacion`` si hubo problemas
             e. agrega a ``resultados``
             f. ``time.sleep(8)`` entre llamadas
        4. Escribe:
             - output_chubut_prueba.json
             - reporte_validacion_chubut_prueba.json
        5. Imprime un resumen por stdout.

    Efectos secundarios:
        - Consume cuota de la API de Groq (1 request por artículo).
        - Crea el directorio ``resultados/`` (hoy sin uso, ver DEUDA TÉCNICA).
    """
    import os

    archivo_excel = os.path.join(
        os.getcwd(), "links_el_chubut_completo nov_dic_ene.xlsx"
    )

    os.makedirs("resultados", exist_ok=True)

    print("=" * 60)
    print("INICIANDO PRUEBA CON NOTICIAS DE CHUBUT")
    print("=" * 60)

    articulos = leer_links_desde_excel(archivo_excel, limite=None)
    if not articulos:
        print("No se encontraron artículos.")
        return

    print(f"Procesando {len(articulos)} artículos (prueba)\n")

    resultados = []
    noticias_con_errores = []

    for idx, articulo in enumerate(articulos):
        print(f"[{idx+1}/{len(articulos)}] {articulo['titulo']}")
        print(f"Fecha: {articulo['fecha']}")
        print(f"Link: {articulo['link']}")

        article_data = scrape_article(articulo['link'])
        if not article_data:
            print("Saltando (scraping fallido)\n")
            continue
        print(f"Texto extraído: {len(article_data['raw_text'])} caracteres")

        print(f"Consultando a Groq ({MODELO})...")
        structured_data = extract_with_groq(
            article_data["raw_text"], articulo['titulo']
        )

        val_est = validar_estructura(structured_data)
        val_coh = validar_coherencia(structured_data)

        if not val_est["valido"] or not val_coh["coherente"]:
            errores = val_est["errores"] + val_coh["inconsistencias"]
            noticias_con_errores.append({
                "id": articulo['fecha'],
                "link": articulo['link'],
                "errores": errores,
            })
            structured_data["_errores_validacion"] = errores
            print(f"Validación: {len(errores)} problemas")
        else:
            print("Validación: OK")

        nota_completa = {
            "id": articulo['fecha'],
            "link": articulo['link'],
            "fecha_publicacion": articulo['fecha'],
            "titulo": articulo['titulo'],
            "datos_extraidos": structured_data,
        }
        resultados.append(nota_completa)
        print(f"OK - Localidad: {structured_data.get('localidad', 'N/A')}\n")

        time.sleep(8)

    with open("output_chubut.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    with open("reporte_validacion_chubut.json", "w", encoding="utf-8") as f:
        json.dump(noticias_con_errores, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("REPORTE")
    print("=" * 60)
    print(f"Noticias procesadas: {len(resultados)}")
    print(f"Noticias con problemas: {len(noticias_con_errores)}")
    print("\nArchivos generados: output_chubut.json "
          "y reporte_validacion_chubut.json")


if __name__ == "__main__":
    main()