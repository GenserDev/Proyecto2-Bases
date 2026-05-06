"""
Carga todos los CSVs generados a Neo4j.
Ejecutar DESPUÉS de generate_data.py.

Uso: python load_csv.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import run_query, close_driver

CSV_DIR = os.path.join(os.path.dirname(__file__), "csv")


def load_csv(filename: str) -> list[dict]:
    path = os.path.join(CSV_DIR, filename)
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def batch(items: list, size: int = 500):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def run_batch(query: str, rows: list, transform=None):
    total = 0
    for chunk in batch(rows):
        data = [transform(r) for r in chunk] if transform else chunk
        run_query(query, {"rows": data})
        total += len(chunk)
    return total


print("=== Cargando datos a Neo4j ===\n")

# ── Constraints ───────────────────────────────────────────────────────────────
print("Creando constraints...")
constraints = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Cliente)     REQUIRE n.clienteId     IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Cuenta)      REQUIRE n.cuentaId      IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Tarjeta)     REQUIRE n.tarjetaId     IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Transaccion) REQUIRE n.transaccionId IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Comercio)    REQUIRE n.comercioId    IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Dispositivo) REQUIRE n.dispositivoId IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Ubicacion)   REQUIRE n.ubicacionId   IS UNIQUE",
]
for c in constraints:
    run_query(c)
print("  Constraints creados ✓")

# ── Nodos ─────────────────────────────────────────────────────────────────────
print("\nCargando Ubicaciones...")
rows = load_csv("ubicaciones.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (u:Ubicacion {ubicacionId: r.ubicacionId})
ON CREATE SET
    u.ciudad       = r.ciudad,
    u.pais         = r.pais,
    u.latitud      = toFloat(r.latitud),
    u.longitud     = toFloat(r.longitud),
    u.zonaRiesgo   = (r.zonaRiesgo = 'true'),
    u.codigoPostal = r.codigoPostal,
    u.region       = r.region,
    u.poblacion    = toInteger(r.poblacion),
    u.codigoPais   = r.codigoPais
""", rows)
print(f"  {n} Ubicaciones ✓")

print("Cargando Dispositivos...")
rows = load_csv("dispositivos.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (d:Dispositivo {dispositivoId: r.dispositivoId})
ON CREATE SET
    d.tipo                   = r.tipo,
    d.sistemaOperativo       = r.sistemaOperativo,
    d.ip                     = r.ip,
    d.ultimoUso              = date(r.ultimoUso),
    d.confiable              = (r.confiable = 'true'),
    d.marcaModelo            = r.marcaModelo,
    d.versionApp             = r.versionApp,
    d.usuariosAsociados      = toInteger(r.usuariosAsociados),
    d.ubicacionesRegistradas = split(r.ubicacionesRegistradas, '|')
""", rows)
print(f"  {n} Dispositivos ✓")

print("Cargando Comercios...")
rows = load_csv("comercios.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (c:Comercio {comercioId: r.comercioId})
ON CREATE SET
    c.nombre             = r.nombre,
    c.categoria          = r.categoria,
    c.pais               = r.pais,
    c.calificacion       = toFloat(r.calificacion),
    c.esConocido         = (r.esConocido = 'true'),
    c.telefonoContacto   = r.telefonoContacto,
    c.horario            = split(r.horario, '|'),
    c.registrado         = date(r.registrado),
    c.totalTransacciones = toInteger(r.totalTransacciones)
""", rows)
print(f"  {n} Comercios ✓")

print("Cargando Clientes...")
rows = load_csv("clientes.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (c:Cliente {clienteId: r.clienteId})
ON CREATE SET
    c.nombre          = r.nombre,
    c.apellido        = r.apellido,
    c.email           = r.email,
    c.telefono        = r.telefono,
    c.fechaNacimiento = date(r.fechaNacimiento),
    c.activo          = (r.activo = 'true'),
    c.nivelRiesgo     = r.nivelRiesgo,
    c.etiquetasRiesgo = split(r.etiquetasRiesgo, '|'),
    c.ingresoMensual  = toFloat(r.ingresoMensual)
""", rows)
print(f"  {n} Clientes ✓")

print("Cargando Cuentas...")
rows = load_csv("cuentas.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (c:Cuenta {cuentaId: r.cuentaId})
ON CREATE SET
    c.numeroCuenta    = r.numeroCuenta,
    c.tipoCuenta      = r.tipoCuenta,
    c.saldo           = toFloat(r.saldo),
    c.fechaApertura   = date(r.fechaApertura),
    c.moneda          = r.moneda,
    c.activa          = (r.activa = 'true'),
    c.limiteCredito   = toFloat(r.limiteCredito),
    c.numeroPrestamos = toInteger(r.numeroPrestamos),
    c.bancosAsociados = split(r.bancosAsociados, '|')
""", rows)
print(f"  {n} Cuentas ✓")

print("Cargando Tarjetas...")
rows = load_csv("tarjetas.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (t:Tarjeta {tarjetaId: r.tarjetaId})
ON CREATE SET
    t.ultimosCuatroDigitos = r.ultimosCuatroDigitos,
    t.tipoTarjeta          = r.tipoTarjeta,
    t.limiteCredito        = toFloat(r.limiteCredito),
    t.fechaVencimiento     = date(r.fechaVencimiento),
    t.bloqueada            = (r.bloqueada = 'true'),
    t.intentosFallidos     = toInteger(r.intentosFallidos),
    t.redesContactadas     = split(r.redesContactadas, '|'),
    t.fechaEmision         = date(r.fechaEmision),
    t.banco                = r.banco
""", rows)
print(f"  {n} Tarjetas ✓")

print("Cargando Transacciones...")
rows = load_csv("transacciones.csv")
n = run_batch("""
UNWIND $rows AS r
MERGE (t:Transaccion {transaccionId: r.transaccionId})
ON CREATE SET
    t.monto          = toFloat(r.monto),
    t.fecha          = date(r.fecha),
    t.descripcion    = r.descripcion,
    t.estado         = r.estado,
    t.esSospechosa   = (r.esSospechosa = 'true'),
    t.canal          = r.canal,
    t.moneda         = r.moneda,
    t.categoriaGasto = r.categoriaGasto,
    t.horaLocal      = toInteger(r.horaLocal)
""", rows)
print(f"  {n} Transacciones ✓")

# ── Relaciones ────────────────────────────────────────────────────────────────
print("\nCargando relaciones POSEE...")
rows = load_csv("rel_posee.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (cl:Cliente {clienteId: r.clienteId})
MATCH (cu:Cuenta {cuentaId: r.cuentaId})
MERGE (cl)-[rel:POSEE]->(cu)
ON CREATE SET
    rel.fechaAsignacion    = date(r.fechaAsignacion),
    rel.esTitular          = (r.esTitular = 'true'),
    rel.porcentajePropiedad = toFloat(r.porcentajePropiedad)
""", rows)
print(f"  {n} POSEE ✓")

print("Cargando relaciones TIENE_TARJETA...")
rows = load_csv("rel_tiene_tarjeta.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (cl:Cliente {clienteId: r.clienteId})
MATCH (t:Tarjeta {tarjetaId: r.tarjetaId})
MERGE (cl)-[rel:TIENE_TARJETA]->(t)
ON CREATE SET
    rel.fechaAsignacion = date(r.fechaAsignacion),
    rel.esTitular       = (r.esTitular = 'true'),
    rel.limitePersonal  = toFloat(r.limitePersonal)
""", rows)
print(f"  {n} TIENE_TARJETA ✓")

print("Cargando relaciones REALIZO...")
rows = load_csv("rel_realizo.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (cl:Cliente {clienteId: r.clienteId})
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MERGE (cl)-[rel:REALIZO]->(t)
ON CREATE SET
    rel.fecha    = date(r.fecha),
    rel.canal    = r.canal,
    rel.ipOrigen = r.ipOrigen
""", rows)
print(f"  {n} REALIZO ✓")

print("Cargando relaciones ORIGEN...")
rows = load_csv("rel_origen.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MATCH (c:Cuenta {cuentaId: r.cuentaId})
MERGE (t)-[rel:ORIGEN]->(c)
ON CREATE SET
    rel.monto     = toFloat(r.monto),
    rel.fecha     = date(r.fecha),
    rel.autorizado = (r.autorizado = 'true')
""", rows)
print(f"  {n} ORIGEN ✓")

print("Cargando relaciones DESTINO...")
rows = load_csv("rel_destino.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MATCH (c:Cuenta {cuentaId: r.cuentaId})
MERGE (t)-[rel:DESTINO]->(c)
ON CREATE SET
    rel.monto       = toFloat(r.monto),
    rel.fecha       = date(r.fecha),
    rel.bancoDestino = r.bancoDestino
""", rows)
print(f"  {n} DESTINO ✓")

print("Cargando relaciones EN_COMERCIO...")
rows = load_csv("rel_en_comercio.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MATCH (c:Comercio {comercioId: r.comercioId})
MERGE (t)-[rel:EN_COMERCIO]->(c)
ON CREATE SET
    rel.fecha      = date(r.fecha),
    rel.metodoPago = r.metodoPago,
    rel.montoTotal = toFloat(r.montoTotal)
""", rows)
print(f"  {n} EN_COMERCIO ✓")

print("Cargando relaciones USO_DISPOSITIVO...")
rows = load_csv("rel_uso_dispositivo.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MATCH (d:Dispositivo {dispositivoId: r.dispositivoId})
MERGE (t)-[rel:USO_DISPOSITIVO]->(d)
ON CREATE SET
    rel.fecha   = date(r.fecha),
    rel.ipUsada = r.ipUsada,
    rel.exitosa = (r.exitosa = 'true')
""", rows)
print(f"  {n} USO_DISPOSITIVO ✓")

print("Cargando relaciones EN_UBICACION...")
rows = load_csv("rel_en_ubicacion.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Transaccion {transaccionId: r.transaccionId})
MATCH (u:Ubicacion {ubicacionId: r.ubicacionId})
MERGE (t)-[rel:EN_UBICACION]->(u)
ON CREATE SET
    rel.fecha                       = date(r.fecha),
    rel.distanciaUltimaTransaccion  = toFloat(r.distanciaUltimaTransaccion),
    rel.alertaGeo                   = (r.alertaGeo = 'true')
""", rows)
print(f"  {n} EN_UBICACION ✓")

print("Cargando relaciones COMPARTE_DISPOSITIVO...")
rows = load_csv("rel_comparte_dispositivo.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (cl:Cliente {clienteId: r.clienteId})
MATCH (d:Dispositivo {dispositivoId: r.dispositivoId})
MERGE (cl)-[rel:COMPARTE_DISPOSITIVO]->(d)
ON CREATE SET
    rel.primerUso  = date(r.primerUso),
    rel.frecuencia = toInteger(r.frecuencia),
    rel.esPropio   = (r.esPropio = 'true')
""", rows)
print(f"  {n} COMPARTE_DISPOSITIVO ✓")

print("Cargando relaciones ASOCIADA_A...")
rows = load_csv("rel_asociada_a.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t:Tarjeta {tarjetaId: r.tarjetaId})
MATCH (c:Cuenta {cuentaId: r.cuentaId})
MERGE (t)-[rel:ASOCIADA_A]->(c)
ON CREATE SET
    rel.fechaAsociacion = date(r.fechaAsociacion),
    rel.esPrincipal     = (r.esPrincipal = 'true'),
    rel.limiteCompartido = toFloat(r.limiteCompartido)
""", rows)
print(f"  {n} ASOCIADA_A ✓")

print("Cargando relaciones VIVE_EN...")
rows = load_csv("rel_vive_en.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (cl:Cliente {clienteId: r.clienteId})
MATCH (u:Ubicacion {ubicacionId: r.ubicacionId})
MERGE (cl)-[rel:VIVE_EN]->(u)
ON CREATE SET
    rel.fechaRegistro = date(r.fechaRegistro),
    rel.esDomicilio   = (r.esDomicilio = 'true'),
    rel.verificado    = (r.verificado = 'true')
""", rows)
print(f"  {n} VIVE_EN ✓")

print("Cargando relaciones SIMILAR_A...")
rows = load_csv("rel_similar_a.csv")
n = run_batch("""
UNWIND $rows AS r
MATCH (t1:Transaccion {transaccionId: r.transaccionId1})
MATCH (t2:Transaccion {transaccionId: r.transaccionId2})
MERGE (t1)-[rel:SIMILAR_A]->(t2)
ON CREATE SET
    rel.similitudScore  = toFloat(r.similitudScore),
    rel.tipoPatron      = r.tipoPatron,
    rel.fechaDeteccion  = date(r.fechaDeteccion)
""", rows)
print(f"  {n} SIMILAR_A ✓")

# ── Verificación final ────────────────────────────────────────────────────────
print("\n=== VERIFICACIÓN FINAL ===")
result = run_query("MATCH (n) RETURN count(n) AS totalNodos")
print(f"  Total nodos en BD: {result[0]['totalNodos']}")
result = run_query("MATCH ()-[r]->() RETURN count(r) AS totalRels")
print(f"  Total relaciones:  {result[0]['totalRels']}")

close_driver()
print("\n¡Carga completada exitosamente!")
