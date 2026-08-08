# Decisiones técnicas y hallazgos de debugging

Este documento cumple dos funciones:

1. **Documentar las decisiones técnicas** tomadas durante el proyecto — qué se eligió, qué alternativas se consideraron, y por qué se decidió lo que se decidió.
2. **Documentar los hallazgos de debugging** que aparecieron durante la implementación — el proceso de diagnóstico, la causa raíz, la solución, y el aprendizaje transferible.

---

## Parte 1: Decisiones de arquitectura

### Decisión 1 — Lakehouse en vez de Warehouse

**Qué se eligió**: Lakehouse Fabric con SQL analytics endpoint read-only.

**Alternativa considerada**: Warehouse Fabric con T-SQL completo (DDL + DML).

**Por qué**:
- Toda la ingesta y transformación se hace con **Spark en notebooks**, no con T-SQL. El warehouse aportaría capacidad T-SQL escribible que no se usa.
- El lakehouse permite mezclar **Files + Tables**, necesario para bronze (CSV raw en Files).
- El SQL analytics endpoint del lakehouse cubre las necesidades de query de validación sin necesidad de escritura T-SQL.
- El semantic model Direct Lake funciona nativamente sobre lakehouse — un warehouse agregaría un paso adicional sin valor claro.

---

### Decisión 2 — Direct Lake como storage mode del semantic model

**Qué se eligió**: Direct Lake.

**Alternativas consideradas**:
- **Import**: máxima velocidad pero requiere refresh programado y duplica data.
- **DirectQuery**: en tiempo real pero cada query hace round-trip al SQL endpoint.

**Por qué Direct Lake**:
- Combina velocidad de Import (lectura columnar en memoria) con frescura de DirectQuery.
- No requiere refresh programado — al aterrizar nuevos datos en gold, el semantic model los ve automáticamente.
- Habilita automáticamente el large semantic model storage format.
- Es requisito para que la ontology con data bindings sea query-able.
- Es el modo default y recomendado para workloads Fabric-native.

---

### Decisión 3 — Medallion con prefijos en vez de schemas separados

**Qué se eligió**: usar prefijos convencionales (`bronze_sales`, `silver_sales`, tablas gold sin prefijo) todas en el schema `dbo` default.

**Alternativa considerada**: crear schemas Fabric explícitos `bronze`, `silver`, `gold` (soportado en lakehouse enabled-schemas).

**Por qué**: para un proyecto de scope contenido, la overhead de gestionar múltiples schemas y sus permisos supera el beneficio. Con prefijos convencionales el orden queda claro. Para un proyecto productivo real, schemas separados serían la elección correcta.

---

### Decisión 4 — Python + ingest directo en vez de Eventstream

**Qué se eligió**: script Python que usa `azure-kusto-ingest` para insertar eventos directamente en la KQL DB.

**Alternativas consideradas**:
- **Eventstream + custom endpoint**: más real-world pero requiere configuración adicional.
- **Eventstream + Sample data**: rápido pero no permite usar los StockCodes reales del dataset.

**Por qué**: el script Python permite generar eventos que **referencien StockCodes reales** del gold, lo cual es la clave para que la ontology unifique batch + streaming vía entity Product. Se sacrifica "realismo del eventstream" por control de contenido — trade-off explícito.

---

### Decisión 5 — Ontology unificando por Product (no dos ontologías separadas)

**Qué se eligió**: una sola ontología con la entity Product apareciendo en Sale y en InventoryMovement.

**Alternativa considerada**: dos ontologías separadas — una para ventas, otra para inventario.

**Por qué**: el propósito de una ontología es **unificar vocabulario cross-source**. Dos ontologías separadas serían equivalentes a no tener ontología. La entity Product como nodo compartido es exactamente el caso de uso que la ontología resuelve.

---

### Decisión 6 — Endorsement jerárquico

**Qué se eligió**: bronze sin endorsement, silver Promoted, gold + semantic model + reporte Certified, ontology Master data.

**Alternativa considerada**: marcar todo como Certified.

**Por qué**: la jerarquía comunica grado de madurez y confianza al reviewer. Bronze contiene raw sin vetar (por eso es bronze). Silver está limpio pero no modelado. Gold y downstream son production-ready. La ontology, como vocabulario autoritativo, es Master data.

---

## Parte 2: Reglas de calidad de silver

Reglas aplicadas al transformar bronze → silver:

| Regla | Razón |
|---|---|
| Excluir filas con `Quantity <= 0` | Son cancelaciones/devoluciones (Invoice empieza con 'C'). Silver = transacciones válidas. |
| Excluir filas con `Price <= 0` | Precio cero o negativo indica ajustes/errores, no ventas reales. |
| Excluir filas con `Customer ID` NULL | ~25% del dataset. Mantener solo transacciones B2B/B2C identificadas. |
| Excluir filas con `StockCode` no numérico | Códigos como "POST", "DOT", "M" son ajustes contables, no productos. |
| Excluir filas con `Description` NULL | Sin descripción confiable no podemos usar el StockCode en ontology. |
| Agregar `TotalAmount = Quantity * Price` | Cálculo derivado que gold/reporting necesita. |
| Renombrar `Customer ID` → `CustomerID` | Sin espacios, más limpio para downstream. |
| Cast explícito de tipos | Bronze usó `inferSchema`; silver enforce schema. |

---

## Parte 3: Hallazgos de debugging

Durante la implementación aparecieron tres errores no triviales. Se documentan acá porque el proceso de encontrarlos y resolverlos fue el aprendizaje más valioso del proyecto.

---

### Hallazgo 1 — Patrón dual-binding para entities con dimensión temporal

**Contexto**: al configurar la ontology, la entity `InventoryMovement` debía bindearse a la tabla `InventoryMovements` del eventhouse como timeseries binding.

**Síntoma**: aparecieron tres errores encadenados al intentar configurar el binding:
1. `TimeSeries mapping cannot bind static property` — las properties del entity type estaban como Static pero se mapeaban en un binding Timeseries.
2. `At least one timeseries property must be bound to a source data column`.
3. `Non-timeseries binding required` — banner persistente que también bloqueaba las relationships salientes desde `InventoryMovement`.

**Descarte inicial**: se pensó que el problema era solo el mapping de properties, pero al corregir las properties, el banner "Non-timeseries binding required" persistía y las relationships seguían bloqueadas.

**Causa raíz**: una entity type con dimensión temporal en Fabric IQ requiere **dos bindings coexistiendo**, no uno:

- Un **static binding** que enumere las entities únicas (equivalente conceptual a una tabla dimensional: qué entidades existen).
- Un **timeseries binding** que provea los measurements over time (equivalente a una fact table de eventos temporales).

Sin el static binding, la ontology no puede resolver preguntas como "¿cuáles son las entities válidas?", que son necesarias para configurar relationships desde esa entity. Además, las properties que representan measurements variables en el tiempo deben marcarse como **Time series** en el entity type, no como Static.

**Solución**:

1. Ajustar el entity type `InventoryMovement`: cambiar `MovementType`, `Quantity` y `OperatorId` a Property type = **Time series**. Eliminar la property `MovementTimestamp` (redundante — el timestamp lo maneja el propio binding).

2. Crear una tabla en el lakehouse que enumere las entities válidas:

```python
stockcodes = [row.StockCode for row in spark.table("dim_product").collect()]
stores = ["STORE_LON", "STORE_MAN", "STORE_BIR"]
combos = [(sc, st) for sc in stockcodes for st in stores]

df = spark.createDataFrame(combos, ["StockCode", "Store"])
df.write.mode("overwrite").format("delta").saveAsTable("dim_inventory_movement_instance")
```

3. Agregar dos bindings a `InventoryMovement`:
   - **Static** → tabla `dim_inventory_movement_instance` del lakehouse. Mapea el entity key (StockCode + Store).
   - **Timeseries** → tabla `InventoryMovements` del eventhouse. Mapea Timestamp column y properties timeseries.

**Aprendizaje transferible**: cualquier entity type que vaya a tener un timeseries binding necesita **también** un static binding que defina sus instances únicas. Este es el patrón esperado en Fabric IQ para entities con dimensión temporal.

**Evidencia visual**: ver `screenshots/26-ontology-dual-binding-inventorymovement.PNG`.

---

### Hallazgo 2 — El AI data schema del data agent NO es descubrimiento, es autorización

**Contexto**: después de configurar el data agent conectándolo al semantic model `sm_retail`, se probaron las preguntas de testing.

**Síntoma**: al preguntarle al data agent "¿cuál es el revenue total del último año?", devolvía **829,951.53 GBP** para 2011. Pero:
- El SQL directo contra el gold layer daba **8,179,422.07 GBP**.
- Un reporte Power BI manual conectado al **mismo** semantic model daba también **8,179,422.07 GBP**.

Diferencia de aproximadamente **10x**. La respuesta del agent decía "aproximadamente" — pista sospechosa porque los motores DAX no aproximan.

**Descartes durante el diagnóstico**:

1. **Descartada — Definición de la measure**: la measure `Total Revenue = SUM(fact_sales[TotalAmount])` estaba correctamente definida.

2. **Descartada — Data en el gold**: el SQL directo contra `fact_sales` joineado con `dim_date` confirmaba los números correctos (669k / 8.5M / 8.2M para 2009 / 2010 / 2011).

3. **Descartada — El semantic model**: el reporte Power BI manual conectado al mismo semantic model daba los números correctos que matcheaban el SQL.

4. **Descartada — Query generada por el agent**: al pedirle al agent la query DAX que ejecutaba, mostraba una query correcta (`CALCULATE([Total Revenue], 'dim_date'[Year] = 2011)`), pero el resultado seguía sin matchear lo que esa query debería devolver.

Esto descartó problemas de definición, de data y de query. La discrepancia era específica del agent.

**Causa raíz**: al conectar un semantic model al data agent, Fabric expone un panel llamado **AI data schema** donde se marcan explícitamente qué tablas del modelo son visibles para el agent. Las tablas críticas (`fact_sales` y la tabla `Measures1` que contiene las measures del modelo) no estaban marcadas en el schema del agent.

El resultado: el agent respondía operando sobre un subset del modelo, sin acceso a la fact table completa ni a las measures. Y el punto crítico: **el agent no comunica esta limitación al usuario**. Responde con lo que sí puede ver, dando resultados silenciosamente incompletos, sin ningún warning ni disclaimer.

**Solución**: en la vista **Data → sm_retail** del data agent, marcar explícitamente todas las tablas del modelo: `fact_sales`, `dim_date`, `dim_product`, `dim_customer`, `dim_country` y `Measures1`. Después de guardar, la query devolvió el resultado correcto de 8,179,422.07 GBP para 2011.

**Aprendizaje transferible**: el AI data schema es un mecanismo de **autorización explícita**, no un feature de descubrimiento o UI. Cualquier tabla o measure no marcada es invisible para el agent. Y el agent no falla ni avisa cuando la data que necesita no está autorizada — simplemente responde con lo que ve, generando resultados que parecen legítimos pero son incompletos.

**Verificaciones recomendadas después de conectar cada data source a un data agent**:
- Confirmar que todas las fact tables están marcadas.
- Confirmar que la tabla/folder de measures (a veces llamada `Measures1`, "Local measures", o similar) está marcada.
- Ejecutar al menos una query cuyo resultado se pueda verificar contra SQL directo o un reporte manual, para descartar respuestas silenciosamente incompletas.

**Evidencia visual**: ver `screenshots/27-data-agent-validation-response-projection.PNG` (respuesta incorrecta) y `screenshots/28-data-agent-response-projection.PNG` (respuesta correcta post-fix).

---

### Hallazgo 3 — Property types deben matchear el tipo de binding

**Contexto**: relacionado con el Hallazgo 1 pero conceptualmente distinto — este es el problema de propiedades individuales, no del patrón dual-binding completo.

**Síntoma**: `TimeSeries mapping cannot bind static property '6654171769307993648'` — el binding timeseries rechazaba las properties porque estaban marcadas como Static en el entity type.

**Causa raíz**: en Fabric IQ, cada property tiene un Property type (Static o Time series) definido a nivel del entity type. Un binding timeseries **solo acepta properties Time series o properties que sean parte del entity key**. Si intentás mapear una property Static en un binding timeseries, falla.

Además, no hace falta definir una property manual para el timestamp — el propio binding lo maneja vía el campo "Timestamp column".

**Solución**:
1. Cambiar las properties que representan measurements variables en el tiempo (`MovementType`, `Quantity`, `OperatorId`) a Property type = **Time series**.
2. Eliminar la property `MovementTimestamp` — es redundante con el "Timestamp column" del binding.
3. Mantener `StockCode` y `Store` como Static (son parte del entity key).

**Aprendizaje transferible**: al diseñar un entity type que va a tener binding timeseries, definir desde el inicio qué properties son time series (measurements) y cuáles son static (entity keys o atributos que no cambian). Esto evita el retrabajo de reconfigurar properties después.

---

## Parte 4: Aprendizajes generales

Los tres hallazgos comparten un patrón común: **Fabric IQ tiene comportamientos "silenciosos" que no son evidentes en la UI**. Un binding faltante, una property mal categorizada, una tabla no marcada — todo esto genera errores o resultados incorrectos sin mensajes claros al usuario.

Estos aprendizajes son transferibles a cualquier proyecto con Fabric IQ:

1. **Verificar siempre resultados contra fuentes independientes**. Un data agent puede devolver números incorrectos sin errores explícitos. Comparar contra SQL directo o Power BI manual es el único chequeo confiable.

2. **Diseñar entities pensando en su tipo de binding desde el inicio**. Timeseries entities requieren dual-binding y properties específicas.

3. **El AI data schema debe revisarse explícitamente después de cada conexión**. No confiar en que "estar conectado = todo visible".

4. **Documentar debugging es más valioso que documentar solo éxitos**. En un portfolio, mostrar el proceso diagnóstico transmite capacidad técnica mucho mejor que "todo funcionó perfecto".
