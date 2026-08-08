"""
04-inventory-stream.py

Genera movimientos de inventario simulados usando StockCodes reales del gold layer.
Los inserta directamente en la KQL database del Eventhouse.

REQUERIDO:
pip install azure-kusto-data azure-kusto-ingest
"""

import csv
import random
import time
import io

from datetime import datetime, timezone
from pathlib import Path

from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.data_format import DataFormat

from azure.kusto.ingest import (
    QueuedIngestClient,
    IngestionProperties
)


# ==========================================================
# CONFIGURACIÓN FABRIC EVENTHOUSE
# ==========================================================

# Query URI del Eventhouse (sin /database)
CLUSTER_URI = "**Link Uri de EventHouse***"

DATABASE = "eh_inventario"
TABLE = "InventoryMovements"


# ==========================================================
# ARCHIVOS Y DATOS SIMULADOS
# ==========================================================

STOCKCODES_FILE = Path("../datos/...")

STORES = [
    "STORE_LON",
    "STORE_MAN",
    "STORE_BIR"
]

MOVEMENT_TYPES = [
    "RECEPCION",
    "SALIDA",
    "AJUSTE"
]

OPERATORS = [
    "OP001",
    "OP002",
    "OP003",
    "OP004",
    "OP005"
]


EVENTS_PER_SECOND = 2
BATCH_SIZE = 20
TOTAL_MINUTES = 10


# ==========================================================
# CARGA STOCKCODES
# ==========================================================

if not STOCKCODES_FILE.exists():
    raise FileNotFoundError(
        f"No existe el archivo: {STOCKCODES_FILE}"
    )


with open(
    STOCKCODES_FILE,
    encoding="utf-8"
) as f:

    reader = csv.reader(f)

    next(reader)

    stockcodes = [
        row[0]
        for row in reader
        if row and row[0]
    ]


print(f"StockCodes cargados: {len(stockcodes)}")


# ==========================================================
# CONEXIÓN EVENTHOUSE
# ==========================================================

print("Autenticando contra Fabric Eventhouse...")

kcsb = KustoConnectionStringBuilder.with_interactive_login(
    CLUSTER_URI
)

client = QueuedIngestClient(kcsb)


ingestion_props = IngestionProperties(
    database=DATABASE,
    table=TABLE,
    data_format=DataFormat.CSV
)


print("Conectado correctamente")


# ==========================================================
# GENERADOR DE EVENTOS
# ==========================================================

def generate_event():

    return {

        "Timestamp":
            datetime.now(timezone.utc).isoformat(),

        "StockCode":
            random.choice(stockcodes),

        "Store":
            random.choice(STORES),

        "MovementType":
            random.choices(
                MOVEMENT_TYPES,
                weights=[3,5,1]
            )[0],

        "Quantity":
            random.randint(1,50),

        "OperatorId":
            random.choice(OPERATORS)
    }



# ==========================================================
# LOOP INGESTA
# ==========================================================

start = time.time()

total_sent = 0


try:

    while time.time() - start < TOTAL_MINUTES * 60:


        batch = [
            generate_event()
            for _ in range(BATCH_SIZE)
        ]


        buffer = io.StringIO()

        writer = csv.writer(buffer)


        for event in batch:

            writer.writerow(
                [
                    event["Timestamp"],
                    event["StockCode"],
                    event["Store"],
                    event["MovementType"],
                    event["Quantity"],
                    event["OperatorId"]
                ]
            )


        buffer.seek(0)


        client.ingest_from_stream(
            io.BytesIO(
                buffer.getvalue().encode("utf-8")
            ),
            ingestion_properties=ingestion_props
        )


        total_sent += BATCH_SIZE


        print(
            f"Batch enviado correctamente | Total eventos: {total_sent}"
        )


        time.sleep(
            BATCH_SIZE / EVENTS_PER_SECOND
        )


except KeyboardInterrupt:

    print("\nProceso detenido manualmente")


print(
    f"\nTotal eventos enviados: {total_sent}"
)
