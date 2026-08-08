// Query 1: últimos 10 movimientos
InventoryMovements
| top 10 by Timestamp desc

// Query 2: movimientos por tienda en los últimos 5 minutos
InventoryMovements
| where Timestamp > ago(5m)
| summarize count() by Store, MovementType
| order by Store, MovementType

// Query 3: productos con más salidas hoy
InventoryMovements
| where Timestamp > ago(1d) and MovementType == "SALIDA"
| summarize total_units = sum(Quantity) by StockCode
| top 10 by total_units desc

// Query 4: timechart de movimientos por minuto
InventoryMovements
| where Timestamp > ago(30m)
| summarize count() by bin(Timestamp, 1m), MovementType
| render timechart