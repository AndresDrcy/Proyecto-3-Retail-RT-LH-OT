### Total Revenue
```dax
Total Revenue =
SUM(fact_sales[TotalAmount])
```
**Caso de uso:** Mostrar los ingresos totales por cualquier dimensión (fecha, producto, cliente, región, etc.).

---

### Total Units Sold
```dax
Total Units Sold =
SUM(fact_sales[Quantity])
```
**Caso de uso:** Analizar el volumen total de unidades vendidas.

---

### Distinct Customers
```dax
Distinct Customers =
DISTINCTCOUNT(fact_sales[CustomerKey])
```
**Caso de uso:** Medir la cantidad de clientes únicos que realizaron compras.

---

### Distinct Products Sold
```dax
Distinct Products Sold =
DISTINCTCOUNT(fact_sales[ProductKey])
```
**Caso de uso:** Conocer cuántos productos diferentes fueron vendidos.

---

### Avg Order Value
```dax
Avg Order Value =
DIVIDE(
    [Total Revenue],
    DISTINCTCOUNT(fact_sales[InvoiceNumber])
)
```
**Caso de uso:** Calcular el valor promedio de cada pedido (ticket promedio).

---

### Revenue YoY %
```dax
Revenue YoY % =
VAR CurrentRev = [Total Revenue]
VAR PreviousRev = CALCULATE(
    [Total Revenue],
    DATEADD(dim_date[FullDate], -1, YEAR)
)
RETURN
DIVIDE(CurrentRev - PreviousRev, PreviousRev)
```
**Caso de uso:** Comparar el crecimiento o disminución de los ingresos frente al mismo período del año anterior.