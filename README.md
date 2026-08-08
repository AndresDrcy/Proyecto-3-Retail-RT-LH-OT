<div align="center">

# 🏪 Retail Analytics End-to-End con Microsoft Fabric

**Portfolio project para la certificación DP-600 — Fabric Analytics Engineer Associate**

![Microsoft Fabric](https://img.shields.io/badge/Microsoft-Fabric-blue)
![Status](https://img.shields.io/badge/status-Completado-brightgreen)
![DP-600](https://img.shields.io/badge/Certificación-DP--600-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## 📖 ¿Qué es este proyecto?

Un sistema completo de análisis de datos retail construido sobre **Microsoft Fabric**, que combina cuatro cosas al mismo tiempo:

1. **Análisis histórico de ventas** con arquitectura medallion (bronze/silver/gold).
2. **Análisis en tiempo real** de movimientos de inventario con streaming.
3. **Modelo semántico** con Direct Lake para reportes en Power BI.
4. **Inteligencia artificial** con una ontología (Fabric IQ) y un data agent conversacional que responde preguntas en lenguaje natural.

Todo sobre datos reales de un retailer británico (~1 millón de transacciones).

---

## 🎯 ¿Para qué sirve?

Este proyecto tiene tres objetivos:

- **Aprender**: aplicar todo lo estudiado del examen DP-600 en un caso end-to-end, no en ejercicios sueltos.
- **Demostrar**: servir como portfolio para hiring managers y reviewers técnicos.
- **Practicar debugging**: los errores encontrados durante la implementación están documentados como aprendizaje (ver [sección de debugging](#-hallazgos-de-debugging-lo-que-más-aprendí)).

---

## 🧩 Cómo funciona (explicación simple)

Imaginate que tenés una tienda de regalos con datos que llegan de dos formas distintas:

**Datos que llegan cada tanto (batch)**: cada noche, un archivo CSV con todas las ventas del día. Como cuando descargás el resumen bancario a fin de mes.

**Datos que llegan todo el tiempo (streaming)**: cada vez que entra o sale un producto de una tienda, se emite un evento con timestamp. Como cuando ves los mensajes de WhatsApp llegando en vivo.

Este proyecto procesa **los dos tipos** en paralelo:

```
┌────────────────────┐         ┌───────────────────┐
│ Ventas históricas  │         │ Inventario en     │
│ (archivo CSV)      │         │ tiempo real       │
└─────────┬──────────┘         │ (stream Python)   │
          │                    └──────────┬────────┘
          ▼                               │
   ┌──────────────┐                       │
   │   BRONZE     │  ← datos crudos       │
   │              │                       │
   └──────┬───────┘                       ▼
          │                        ┌──────────────┐
          ▼                        │  Eventhouse  │
   ┌──────────────┐                │  (KQL DB)    │
   │   SILVER     │  ← limpiados   └──────┬───────┘
   │              │                       │
   └──────┬───────┘                       │
          │                               │
          ▼                               ▼
   ┌──────────────┐                ┌──────────────┐
   │    GOLD      │                │  Dashboard   │
   │ (star schema)│                │  Tiempo Real │
   └──────┬───────┘                └──────────────┘
          │
          ▼
   ┌──────────────────┐
   │  Semantic Model  │  ← Direct Lake
   │  + Power BI      │
   └────────┬─────────┘
            │
            └──────────┐
                       ▼
         ┌─────────────────────────┐
         │  Ontología (Fabric IQ)  │  ← Vocabulario unificado
         │  + Data Agent           │  ← Chat en lenguaje natural
         └─────────────────────────┘
```

**Al final**, un usuario puede preguntarle al data agent: *"¿Cuál fue el revenue del último año?"* — y responde combinando información de ambos flujos.

---

## 🏗️ Arquitectura y decisiones técnicas

**Patrón utilizado**: Lambda simplificado — dos "carriles" de datos (batch y streaming) que convergen en la capa de consumo.

**Stack técnico**:

| Capa | Tecnología |
|---|---|
| Storage batch | Lakehouse `lh_retail` (Delta Lake sobre OneLake) |
| Storage streaming | Eventhouse `eh_inventario` (KQL Database) |
| Modelo semántico | Direct Lake mode |
| Ingesta batch | PySpark en notebooks Fabric |
| Ingesta streaming | Python + `azure-kusto-ingest` |
| Query streaming | KQL (Kusto Query Language) |
| Reporting | Power BI |
| AI | Fabric IQ (ontología + data agent) |
| Governance | Sensitivity labels + endorsement jerárquico |

Las decisiones justificadas (por qué lakehouse en vez de warehouse, por qué Direct Lake, por qué medallion, etc.) están documentadas en detalle en [`docs/decisiones-tecnicas.md`](docs/decisiones-tecnicas.md).

---

## 📚 Módulos DP-600 cubiertos

| # | Módulo | Cómo se aplica |
|:-:|---|---|
| M2 | Lakehouses | `lh_retail` con bronze/silver/gold |
| M4 | Real-Time Intelligence | `eh_inventario` + KQL + dashboard |
| M5 | Discover data in OneLake | Storage unificado, endorsement |
| M6 | Choose data stores | Decisión lakehouse vs warehouse justificada |
| M7 | Design dimensional models | Star schema con fact + 5 dims |
| M9 | Transform with notebooks | Spark notebooks para las 3 capas |
| M11 | DAX calculations | 6 measures del semantic model |
| M15 | Fabric IQ fundamentals | Ontology + data agent implementados |
| M16 | Create ontology with Fabric IQ | 6 entities + 5 relationships + dual binding |
| M19 | Govern analytics data | Endorsement Certified/Master data + descriptions |

Los módulos no cubiertos (warehouse, dataflows, CI/CD, RLS) están explicados en el documento oficial del proyecto.

---

## 📂 Estructura del repo

```
proyecto-dp600-retail/
├── README.md                              ← Estás acá
├── .gitignore
│
├── codigo/                                ← Scripts y código
│   ├── 00-prepare-data.py                 ← Convierte xlsx → CSVs
│   └── 04-inventory-stream.py             ← Generador de streaming
│   [nota: los notebooks 01-03 viven en Fabric]
│
├── consultas/                             ← Queries del proyecto
│   ├── dax-measures.md                    ← 6 measures documentadas
│   └── qs_inventory_analysisKQL.md        ← 4 queries KQL
│
├── docs/                                  ← Documentación
│   └── decisiones-tecnicas.md             ← Decisiones + hallazgos de debugging
│
├── screenshots/                           ← Evidencia visual (26 imágenes)
│   ├── 01-workspace-created.PNG
│   ├── 02-prepared-data.PNG
│   └── ... (hasta 28)
│
└── datos/                                 ← NO se sube a Git (ver .gitignore)
    ├── online_retail_II.xlsx              ← Dataset original
    ├── bronze_raw/                        ← CSVs preparados
    └── stockcodes.csv                     ← Extraído del gold
```

---

## 🔧 Cómo reproducir el proyecto

### Prerrequisitos

- Cuenta Microsoft Fabric con una **capacity habilitada** (F64+ recomendado para Copilot y data agent).
- **Tenant settings habilitados**:
  - Fabric habilitado.
  - Ontology (preview).
  - Copilot in Fabric.
- **Python 3.10+** con `pandas`, `openpyxl`, `azure-kusto-data`, `azure-kusto-ingest`.
- **Power BI Desktop** para reportes.

### Setup (10 días de trabajo efectivo)

1. **Descargar el dataset**:
   - [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) (licencia CC BY 4.0)
   - [Mirror en Kaggle](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci)
2. **Correr `codigo/00-prepare-data.py`** para convertir el xlsx en dos CSVs por año.
3. **Crear workspace, lakehouse y notebooks** en Fabric (bronze → silver → gold).
4. **Crear eventhouse** y correr `codigo/04-inventory-stream.py` para simular streaming.
5. **Crear semantic model** en Direct Lake y measures DAX (ver `consultas/dax-measures.md`).
6. **Aplicar governance** (sensitivity labels si tenés Purview, endorsement jerárquico).
7. **Crear ontología** con Fabric IQ (patrón dual-binding, ver hallazgo #1).
8. **Configurar data agent** y marcar todas las tablas en el AI data schema (ver hallazgo #2).

> ⚠️ **Antes de correr los scripts .py**: ajustá los paths hardcodeados (`C:\Users\...`) a tu ambiente local. En el script del stream, poné tu **Cluster URI del Eventhouse** en la variable `CLUSTER_URI` (buscar el placeholder `**Link Uri de EventHouse***`).

---

## 🐛 Hallazgos de debugging (lo que más aprendí)

Durante la implementación aparecieron **tres errores no triviales**. Los documento porque el proceso de encontrarlos y resolverlos fue el aprendizaje más valioso del proyecto — más que seguir la guía sin problemas.

### 🔍 Hallazgo #1: Patrón dual-binding en ontologías con datos temporales

**Síntoma**: al configurar el binding de `InventoryMovement` en la ontología, aparecían tres errores encadenados que no dejaban ni siquiera crear las relationships desde esa entity.

**Causa**: en Fabric IQ, una entity con datos temporales necesita **DOS bindings coexistiendo**, no uno solo:
- Un binding *static* que enumere qué entidades existen (como una tabla dimensional).
- Un binding *timeseries* que provea las mediciones a lo largo del tiempo (como una fact table).

Sin el static, la ontología no sabe qué combinaciones únicas de `StockCode + Store` son válidas.

**Solución**: crear una tabla `dim_inventory_movement_instance` en el lakehouse que enumere las combinaciones válidas, y bindearla como *static*. Después, el binding *timeseries* al eventhouse funciona sin problemas.

**Screenshot**: [`26-ontology-dual-binding-inventorymovement.PNG`](screenshots/26-ontology-dual-binding-inventorymovement.PNG)

Detalles completos en [`docs/decisiones-tecnicas.md`](docs/decisiones-tecnicas.md#hallazgo-1--patrón-dual-binding-para-entities-con-dimensión-temporal).

---

### 🔍 Hallazgo #2: El AI Data Schema no es descubrimiento — es autorización silenciosa

**Síntoma**: el data agent respondía "revenue del último año = 829,951.53 GBP" para 2011. Pero el reporte manual en Power BI (contra el **mismo semantic model**) daba **8,179,422.07 GBP**. Diferencia de ~10x.

**Descartes durante el diagnóstico**:
1. La measure `Total Revenue = SUM(fact_sales[TotalAmount])` estaba correcta.
2. El SQL directo contra gold confirmaba los números correctos.
3. El agent mostraba una query DAX correcta cuando se le pedía.

**Causa**: al conectar el semantic model al data agent, Fabric expone un panel de **AI data schema** con checkboxes. Las tablas críticas (`fact_sales` y la tabla `Measures1`) **no estaban marcadas**. El agent respondía usando un subset del modelo, **sin avisar** al usuario que le faltaba data.

**Solución**: marcar TODAS las tablas del semantic model en el AI data schema del data agent.

**Aprendizaje clave**: el AI data schema es un mecanismo de **autorización explícita**. Cualquier tabla no marcada es invisible al agent, y el agent responde con lo que ve — sin ninguna señal de que la respuesta es incompleta.

**Screenshots**: [`27-data-agent-validation-response-projection.PNG`](screenshots/27-data-agent-validation-response-projection.PNG) y [`28-data-agent-response-projection.PNG`](screenshots/28-data-agent-response-projection.PNG)

Detalles completos en [`docs/decisiones-tecnicas.md`](docs/decisiones-tecnicas.md#hallazgo-2--el-ai-data-schema-del-data-agent-no-es-descubrimiento-es-autorización).

---

### 🔍 Hallazgo #3: Property types en Fabric IQ deben matchear el tipo de binding

**Síntoma**: `TimeSeries mapping cannot bind static property` — el binding timeseries rechazaba las properties porque estaban definidas como Static en el entity type.

**Causa**: las properties que representan mediciones que cambian en el tiempo (`MovementType`, `Quantity`, `OperatorId`) deben marcarse como **Time series** en el entity type — no como Static.

**Solución**: cambiar el Property type de esas tres a Time series. Además, eliminar la property `MovementTimestamp` (redundante — el timestamp lo maneja el propio binding).

---

## 📸 Screenshots destacados

<div align="center">

| Milestone | Screenshot |
|---|---|
| Workspace creado | [`01-workspace-created.PNG`](screenshots/01-workspace-created.PNG) |
| Gold layer con star schema | [`09-gold-star-schema.PNG`](screenshots/09-gold-star-schema.PNG) |
| Streaming KQL en vivo | [`13-kql-stream-live.PNG`](screenshots/13-kql-stream-live.PNG) |
| Dashboard tiempo real (momento inicial) | [`15-dashboard-realtime.PNG`](screenshots/15-dashboard-realtime.PNG) |
| Dashboard tiempo real (1 min después) | [`15-dashboard-realtime (1Min).PNG`](screenshots/15-dashboard-realtime%20(1Min).PNG) |
| Semantic model + relaciones | [`16-semantic-model-relationships.PNG`](screenshots/16-semantic-model-relationships.PNG) |
| Reporte Power BI | [`18-report-powerbi.PNG`](screenshots/18-report-powerbi.PNG) |
| Endorsement Certified | [`20-endorsement-certified.PNG`](screenshots/20-endorsement-certified.PNG) |
| Ontology creada | [`21-ontology-created.PNG`](screenshots/21-ontology-created.PNG) |
| Preview de entity Product | [`23-ontology-preview-product.PNG`](screenshots/23-ontology-preview-product.PNG) |
| Data agent — respuesta inicial | [`25-data-agent-conversation.PNG`](screenshots/25-data-agent-conversation.PNG) |
| Data agent — validación cruzada (mismo resultado) | [`25-data-agent-conversation V2.PNG`](screenshots/25-data-agent-conversation%20V2.PNG) |
| Dual-binding (debug #1) | [`26-ontology-dual-binding-inventorymovement.PNG`](screenshots/26-ontology-dual-binding-inventorymovement.PNG) |
| Data agent — validación pre-fix (debug #2) | [`27-data-agent-validation-response-projection.PNG`](screenshots/27-data-agent-validation-response-projection.PNG) |
| Data agent corregido (debug #2) | [`28-data-agent-response-projection.PNG`](screenshots/28-data-agent-response-projection.PNG) |

</div>

> 📌 **Sobre los pares de screenshots**:
> - El par `15-dashboard-realtime` muestra el dashboard en **dos momentos consecutivos** (inicial y 1 minuto después), evidenciando el auto-refresh y la evolución del stream en vivo.
> - El par `25-data-agent-conversation` muestra la **validación cruzada** — el agent respondiendo la misma pregunta desde dos formulaciones distintas y devolviendo resultados consistentes.

Los 26 screenshots están en la carpeta [`screenshots/`](screenshots/).

---

## 🔗 Recursos

### Dataset
- **UCI Online Retail II**: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **Licencia**: Creative Commons Attribution 4.0 (CC BY 4.0)
- **Citation**: Chen, D. (2019). Online Retail II. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D

### Documentación Microsoft
- **Fabric**: https://learn.microsoft.com/en-us/fabric/
- **DP-600 exam**: https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/
- **Learning path**: https://learn.microsoft.com/en-us/training/paths/implement-analytics-solutions-using-microsoft-fabric/

### Referencias técnicas
- **KQL**: https://learn.microsoft.com/en-us/kusto/query/
- **DAX**: https://learn.microsoft.com/en-us/dax/
- **Delta Lake**: https://docs.delta.io/

---

## 📝 Notas honestas sobre el scope

Este proyecto **NO cubre** algunas cosas del DP-600 por decisión de scope o por limitaciones del tenant:

- **Warehouse Fabric**: se usó solo lakehouse. Un warehouse agregaría trabajo sin nuevo aprendizaje relevante para el scope.
- **Dataflows Gen2**: se prefirieron notebooks Spark por control de código.
- **CI/CD con Git y deployment pipelines**: fuera de scope para mantener la simplicidad.
- **RLS/OLS**: fuera de scope para proyecto single-user.
- **Sensitivity labels**: **no aplicadas** porque el tenant utilizado **no tiene Microsoft Purview Information Protection habilitado**. Esta es una limitación del tenant, no un olvido — los sensitivity labels requieren configuración de Purview a nivel organizacional, algo fuera del alcance de un tenant individual de aprendizaje. Por eso no existe el screenshot `19-sensitivity-labels-applied.png` en el proyecto.
- **Sample notebooks (SemPy)**: opcional, no incluido para mantener el scope contenido.

Estas exclusiones **son intencionales** y están documentadas en profundidad en `docs/decisiones-tecnicas.md`.

<div align="center">

Hecho como parte de la preparación para el examen **Microsoft DP-600**.

</div>
