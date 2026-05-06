"""
6 Consultas Cypher para detección de fraude (2 por integrante).
Persona 1: velocidad geográfica + anillos de fraude
Persona 2: cuentas de alto riesgo + comercios sospechosos
Persona 3: resumen mensual de fraude + paths de fraude
"""
from fastapi import APIRouter
from database import run_query

router = APIRouter(prefix="/consultas", tags=["Consultas Cypher"])


# ── Consulta 1 (Persona 1) ────────────────────────────────────────────────────
# Clientes con transacciones en múltiples países distintos
@router.get("/velocidad-geografica", summary="[P1] Clientes con transacciones en múltiples países")
def velocidad_geografica(min_paises: int = 2):
    """
    Detecta clientes cuyas transacciones ocurrieron en 2 o más países distintos.
    Indicador clásico de fraude por velocidad geográfica imposible.
    """
    query = """
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)-[:EN_UBICACION]->(u:Ubicacion)
    WITH cl, collect(DISTINCT u.pais) AS paises, count(t) AS totalTx
    WHERE size(paises) >= $minPaises
    RETURN
        cl.clienteId    AS clienteId,
        cl.nombre       AS nombre,
        cl.apellido     AS apellido,
        cl.nivelRiesgo  AS nivelRiesgo,
        paises          AS paisesDetectados,
        size(paises)    AS cantidadPaises,
        totalTx         AS totalTransacciones
    ORDER BY cantidadPaises DESC
    """
    return run_query(query, {"minPaises": min_paises})


# ── Consulta 2 (Persona 1) ────────────────────────────────────────────────────
# Anillos de fraude: clientes que comparten el mismo dispositivo
@router.get("/anillos-fraude", summary="[P1] Anillos de fraude por dispositivos compartidos")
def anillos_fraude(min_clientes: int = 2):
    """
    Encuentra dispositivos compartidos por 2 o más clientes distintos.
    Patrón típico de fraude organizado en anillo.
    """
    query = """
    MATCH (c1:Cliente)-[:COMPARTE_DISPOSITIVO]->(d:Dispositivo)<-[:COMPARTE_DISPOSITIVO]-(c2:Cliente)
    WHERE c1.clienteId < c2.clienteId
    WITH d, collect(DISTINCT c1) + collect(DISTINCT c2) AS clientes
    WITH d, [cl IN clientes | cl.clienteId] AS clientesIds,
            [cl IN clientes | cl.nombre + ' ' + cl.apellido] AS nombres
    WHERE size(clientesIds) >= $minClientes
    RETURN
        d.dispositivoId     AS dispositivoId,
        d.ip                AS ip,
        d.tipo              AS tipoDispositivo,
        d.confiable         AS confiable,
        clientesIds         AS clientesCompartidos,
        nombres             AS nombresClientes,
        size(clientesIds)   AS totalClientes
    ORDER BY totalClientes DESC
    """
    return run_query(query, {"minClientes": min_clientes})


# ── Consulta 3 (Persona 2) ────────────────────────────────────────────────────
# Cuentas de alto riesgo por transacciones sospechosas
@router.get("/cuentas-alto-riesgo", summary="[P2] Cuentas con mayor volumen de transacciones sospechosas")
def cuentas_alto_riesgo(min_sospechosas: int = 3):
    """
    Identifica cuentas origen de múltiples transacciones sospechosas.
    Útil para congelar cuentas comprometidas.
    """
    query = """
    MATCH (cu:Cuenta)<-[:ORIGEN]-(t:Transaccion)
    WHERE t.esSospechosa = true
    WITH cu, count(t) AS txSospechosas, sum(t.monto) AS montoTotal, avg(t.monto) AS montoPromedio
    WHERE txSospechosas >= $minSospechosas
    RETURN
        cu.cuentaId      AS cuentaId,
        cu.numeroCuenta  AS numeroCuenta,
        cu.tipoCuenta    AS tipoCuenta,
        cu.saldo         AS saldo,
        cu.activa        AS activa,
        txSospechosas    AS transaccionesSospechosas,
        montoTotal       AS montoTotalSospechoso,
        montoPromedio    AS montoPromedioSospechoso
    ORDER BY txSospechosas DESC
    """
    return run_query(query, {"minSospechosas": min_sospechosas})


# ── Consulta 4 (Persona 2) ────────────────────────────────────────────────────
# Comercios con más transacciones sospechosas
@router.get("/comercios-sospechosos", summary="[P2] Comercios asociados a transacciones sospechosas")
def comercios_sospechosos(limit: int = 20):
    """
    Rankea comercios por cantidad de transacciones sospechosas recibidas.
    Permite identificar puntos de venta comprometidos.
    """
    query = """
    MATCH (t:Transaccion)-[:EN_COMERCIO]->(co:Comercio)
    WHERE t.esSospechosa = true
    WITH co,
         count(t)       AS txSospechosas,
         sum(t.monto)   AS montoFraude,
         collect(DISTINCT t.canal) AS canales
    RETURN
        co.comercioId   AS comercioId,
        co.nombre       AS nombre,
        co.categoria    AS categoria,
        co.pais         AS pais,
        co.esConocido   AS esConocido,
        txSospechosas   AS transaccionesSospechosas,
        montoFraude     AS montoTotalFraude,
        canales         AS canalesUsados
    ORDER BY txSospechosas DESC
    LIMIT $limit
    """
    return run_query(query, {"limit": limit})


# ── Consulta 5 (Persona 3) ────────────────────────────────────────────────────
# Resumen mensual de fraude con agregaciones
@router.get("/resumen-mensual-fraude", summary="[P3] Resumen mensual de transacciones sospechosas")
def resumen_mensual_fraude():
    """
    Agrega transacciones sospechosas por mes y año.
    Permite identificar tendencias temporales de fraude.
    """
    query = """
    MATCH (t:Transaccion)
    WHERE t.esSospechosa = true
    WITH
        t.fecha.year   AS anio,
        t.fecha.month  AS mes,
        count(t)       AS totalSospechosas,
        sum(t.monto)   AS montoTotal,
        avg(t.monto)   AS montoPromedio,
        collect(DISTINCT t.canal) AS canales,
        collect(DISTINCT t.estado) AS estados
    RETURN anio, mes, totalSospechosas, montoTotal, montoPromedio, canales, estados
    ORDER BY anio DESC, mes DESC
    """
    return run_query(query, {})


# ── Consulta 6 (Persona 3) ────────────────────────────────────────────────────
# Paths de fraude: clientes conectados a través de transacciones y dispositivos
@router.get("/paths-fraude", summary="[P3] Rutas de contagio de fraude entre clientes")
def paths_fraude(limit: int = 15):
    """
    Encuentra cadenas de clientes conectados por transacciones sospechosas
    que usan los mismos dispositivos. Visualiza la propagación del fraude.
    """
    query = """
    MATCH path = (c1:Cliente)-[:REALIZO]->(t1:Transaccion {esSospechosa: true})
                 -[:USO_DISPOSITIVO]->(d:Dispositivo)
                 <-[:USO_DISPOSITIVO]-(t2:Transaccion {esSospechosa: true})
                 <-[:REALIZO]-(c2:Cliente)
    WHERE c1.clienteId <> c2.clienteId
    RETURN
        c1.clienteId   AS clienteOrigen,
        c1.nombre      AS nombreOrigen,
        t1.transaccionId AS tx1,
        d.dispositivoId  AS dispositivoCompartido,
        d.ip             AS ipCompartida,
        t2.transaccionId AS tx2,
        c2.clienteId   AS clienteDestino,
        c2.nombre      AS nombreDestino
    LIMIT $limit
    """
    return run_query(query, {"limit": limit})
