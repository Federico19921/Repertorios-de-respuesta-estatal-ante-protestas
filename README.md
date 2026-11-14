<div align="center">

# Repertorios de respuesta estatal ante protestas

### Chubut (2021–2022) · Jujuy (2023)

*Un estudio comparado sobre acción colectiva contenciosa y respuesta estatal en Argentina*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-Plotly-3F4F75?logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![pandas](https://img.shields.io/badge/pandas-2.x-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-en%20curso-yellow.svg)]()

</div>

---

## Tabla de contenidos

- [Sobre el proyecto](#-sobre-el-proyecto)
- [Preguntas de investigación](#-preguntas-de-investigación)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Datos](#-datos)
- [Metodología](#-metodología)
- [Notebooks](#-notebooks)
- [Pipeline de codificación (`scr/`)](#-pipeline-de-codificación-scr)
- [Dashboard interactivo](#-dashboard-interactivo)
- [Instalación](-instalación)
- [Uso rápido](#-uso-rápido)
- [Reproducibilidad](#-reproducibilidad)
- [Citación](#-citación)
- [Autor](#-autor)
- [Licencia](#-licencia)

---

## Sobre el proyecto

Este repositorio reúne el **corpus, los datos codificados, los scripts de procesamiento y los análisis** de una investigación sobre los **repertorios de respuesta estatal frente a episodios de protesta** en dos provincias argentinas:

| Caso | Período | Contexto |
|------|---------|----------|
| **Chubut** | oct. 2021 – ene. 2022 | Conflicto ley de zonificación minera |
| **Jujuy** | jun. – ago. 2023 | Conflicto reforma judicial |

El proyecto adopta como unidad de análisis el **episodio de acción colectiva contenciosa discontinua** (Tilly & Tarrow) y codifica sistemáticamente la **interacción Estado–protesta** a partir de fuentes periodísticas.

El objetivo es aportar evidencia empírica comparada sobre **cómo, cuándo y con qué intensidad el Estado despliega distintos repertorios de respuesta** (negociación, intervención policial, represión, judicialización) y qué factores del contexto del conflicto se asocian a cada uno.

---

## Preguntas de investigación

1. ¿Qué **repertorios de acción colectiva** predominaron en cada ciclo de protesta?
2. ¿Qué **demandas** articularon los actores movilizados y cómo se combinaron?
3. ¿Qué **tipo de respuesta estatal** se desplegó en cada caso y con qué intensidad?
4. ¿Qué relación existe entre el **contexto del conflicto** (escala, disrupción, amenaza política) y el **nivel de represión**?
5. ¿Qué **diferencias y continuidades** emergen al comparar un conflicto laboral-provincial (Chubut) con uno socioambiental-territorial (Jujuy)?

---

## Estructura del repositorio

```text
.
├── Dashboard_protestas/          # Aplicación web interactiva (Dash + Plotly)
│   ├── app.py                    # Punto de entrada del dashboard
│   ├── pages/                    # Módulos por sección (Panorama, Repertorios, ...)
│   ├── assets/                   # CSS / imágenes
│   └── requirements.txt
├── data/
│   ├── raw/                      # Excels originales con enlaces a noticias
│   ├── processed/
│   │   └── eventos.csv           # Base codificada final (>40 variables)
│   └── acled/                    # Datos contextuales ACLED (2020–2024)
├── notebooks/
│   ├── 00_homogenizado.ipynb
│   ├── 01_limpieza_chubut.ipynb
│   ├── 02_EDA_Chubut.ipynb
│   ├── 03_EDA_Jujuy.ipynb
│   ├── 04_Analisis_comparativo_Chubut_Jujuy.ipynb
│   ├── 05_datos_acled.ipynb
│   └── 06_analisis_contextual_ACLED_2020-2024.ipynb
├── scr/                          # Scripts de scraping y codificación
│   ├── ArmadorCorpus.py
│   ├── JSON_a_Excel.py
│   ├── auditoria.py
│   └── revision_manual.py
├── requirements.txt
└── README.md
---

```

## Datos

El dataset principal (`data/processed/eventos.csv`) contiene **un registro por episodio de protesta** codificado a partir de noticias periodísticas. Está organizado en seis bloques temáticos:

### Diccionario de variables (resumen)

| Bloque | Variables representativas | Descripción |
|--------|---------------------------|-------------|
| **Identificación** | `noticia_id`, `provincia`, `localidad`, `fecha`, `medio` | Metadatos del episodio y de la fuente |
| **Actores** | `actores_participantes`, `docentes`, `gremios_estatales`, `sindicatos_privados`, `organizaciones_sociales`, `comunidades_indigenas`, `vecinos`, `colectivos_ambientales` | Presencia (0/1) de cada tipo de actor |
| **Repertorios** | `tipo_accion`, `tiene_marcha`, `tiene_corte`, `tiene_paro`, `tiene_acto`, `tiene_escrache`, `tiene_destrozos`, `tiene_toma` | Tácticas desplegadas por los manifestantes |
| **Demandas** | `demanda_principal`, `demanda_salarial`, `demanda_laboral`, `demanda_ambiental_territorial`, `demanda_politica_legal`, `demanda_ddhh`, `demanda_servicios`, `demanda_derechos_especificos`, `demanda_institucional`, `demanda_conmemoracion` | Ejes de reclamación |
| **Respuesta estatal** | `respuesta_estatal`, `presencia_policial`, `accionar_policial`, `tipo_intervencion_estatal`, `uso_fuerza`, `heridos`, `detenciones`, `judicializacion`, `intervencion_armonizada`, `es_represion` | Repertorio estatal desplegado |
| **Contexto del conflicto** | `escala`, `intensidad`, `disrupcion`, `amenaza_politica`, `resultado_episodio` | Dimensiones contextuales del episodio |

---

## Metodología

La estrategia metodológica combina **codificación automatizada asistida por LLM** con **auditoría y revisión manual**:

1. **Construcción del corpus** — A partir de un Excel con `Fecha`, `Link` y `Título`, el script `ArmadorCorpus.py` scrapea el cuerpo de cada noticia.
2. **Codificación automática** — Cada artículo se procesa con un LLM (`openai/gpt-oss-20b` vía Groq) utilizando un *libro de códigos* estructurado en JSON, derivado de la definición tillyana de acción colectiva contenciosa discontinua.
3. **Auditoría** — `auditoria.py` valida consistencia interna (rangos, valores permitidos, cardinalidad) y detecta casos anómalos.
4. **Revisión manual** — `revision_manual.py` permite corregir episodios dudosos y registrar decisiones de codificación.
5. **Homogeneización** — `00_homogenizado.ipynb` unifica los esquemas de Chubut y Jujuy en una única base comparable.
6. **Análisis** — EDA por caso, análisis comparativo y contextualización con ACLED.

El diseño busca **balancear escalabilidad y rigor**, dejando trazabilidad completa entre noticia → codificación automática → revisión → dato final.

---

## Notebooks

| # | Notebook | Propósito |
|---|----------|-----------|
| 00 | `homogenizado.ipynb` | Unificación de esquemas Chubut–Jujuy |
| 01 | `limpieza_chubut.ipynb` | Limpieza y preparación del caso Chubut |
| 02 | `limpieza_jujuy.ipynb` | Limpieza y preparación del caso Jujuy |
| 03 | `EDA_Chubut.ipynb` | Análisis exploratorio: actores, repertorios, demandas, respuesta estatal |
| 04 | `EDA_Jujuy.ipynb` | Análisis exploratorio del caso Jujuy |
| 05 | `Analisis_comparativo_Chubut_Jujuy.ipynb` | Comparación sistemática entre ambos ciclos |
| 06 | `datos_acled.ipynb` | Procesamiento de datos ACLED |
| 07 | `analisis_contextual_ACLED_2020-2024.ipynb` | Contextualización temporal y territorial del conflicto |

---

## Pipeline de codificación (`scr/`)

| Script | Función |
|--------|---------|
| **`ArmadorCorpus.py`** | Scraping + codificación por LLM. Entrada: Excel con `Fecha`, `Link`, `Título`. Salida: JSON por noticia. |
| **`JSON_a_Excel.py`** | Consolidación de los JSON individuales en una planilla Excel única. |
| **`auditoria.py`** | Validación automática de la base codificada: nulos, rangos, valores fuera de catálogo, duplicados. |
| **`revision_manual.py`** | Interfaz de revisión asistida para corregir casos marcados por la auditoría. |

> `ArmadorCorpus.py` requiere una **API key de Groq**. Se recomienda definirla como variable de entorno (`GROQ_API_KEY`) en lugar de hardcodearla. Si vas a forkear el repo, **no subas tu clave**.

---

## Dashboard interactivo

Aplicación desarrollada con **Dash + Plotly + Dash Bootstrap Components** para explorar los datos sin necesidad de programar.

**Secciones:**

- **Panorama** — métricas generales, distribución temporal y territorial de los episodios.
- **Repertorios** — tácticas de protesta y su frecuencia relativa por caso.
- **Demandas** — principales ejes de reclamación y su combinación.
- **Cruces** — relaciones bivariadas entre actores, repertorios y demandas.
- **Represión** — presencia policial, uso de la fuerza, detenciones y judicialización.
- **Contexto ACLED** — datos contextuales 2020–2024.
- **Métodos** — libro de códigos y decisiones metodológicas.

**Ejecución local:**

```bash
cd Dashboard_protestas
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:8050/
```

## Instalación

1. Clonar
```
git clone https://github.com/Federico19921/Repertorios-de-respuesta-estatal-ante-protestas.git
cd Repertorios-de-respuesta-estatal-ante-protestas
```

2. Entorno virtual (recomendado)
```
python -m venv venv
source venv/bin/activate      #Linux/macOS
venv\Scripts\activate       #Windows
```

3. Dependencias
```
pip install -r requirements.txt
```

## Uso rápido

**Explorar los datos ya codificados:**

```python
import pandas as pd
df = pd.read_csv("data/processed/eventos.csv")
df.groupby("provincia")["es_represion"].mean()
```

**Codificar un nuevo corpus de noticias:**

```bash
export GROQ_API_KEY="tu_api_key"
python scr/ArmadorCorpus.py --input data/raw/noticias.xlsx --output data/processed/codificacion.json
python scr/JSON_a_Excel.py --input data/processed/codificacion.json --output data/processed/eventos.xlsx
python scr/auditoria.py --input data/processed/eventos.xlsx
```

## Reproducibilidad

Para replicar los resultados del paper:

1. Clonar el repositorio y crear el entorno (ver [Instalación](#instalación)).
2. Ejecutar los notebooks.
3. Los gráficos y tablas del análisis comparativo se regeneran íntegramente desde `data/processed/eventos.csv` y `data/acled/`.

## Citación

Si utilizás este repositorio, los datos o el dashboard en una publicación académica:

```bibtex
@misc{llanes2026repertorios,
  author       = {Llanes, Federico Nicolás},
  title        = {Repertorios de respuesta estatal ante protestas:
                  Chubut (2021–2022) y Jujuy (2023)},
  year         = {2026},
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/Federico19921/Repertorios-de-respuesta-estatal-ante-protestas}}
}
```

---

## Autor

**Federico Nicolás Llanes**
GitHub: [@Federico19921](https://github.com/Federico19921)

---

## Licencia

Distribuido bajo licencia **MIT**. Ver [`LICENSE`](LICENSE) para más detalles.

Los datos de **ACLED** incluidos en `data/acled/` se rigen por los [términos de uso de ACLED](https://acleddata.com/terms-of-use/) y no por la licencia MIT de este repositorio.
