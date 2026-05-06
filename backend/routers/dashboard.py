"""
Endpoint de métricas para el dashboard principal.
"""
from fastapi import APIRouter
from database import run_query

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metricas", summary="Métricas consolidadas para el dashboard")
def metricas():
    # Conteos base
    conteos = run_query("""
    MATCH (n)
    RETURN
        count(CASE WHEN 'Cliente'     IN labels(n) THEN 1 END) AS clientes,
        count(CASE WHEN 'Cuenta'      IN labels(n) THEN 1 END) AS cuentas,
        count(CASE WHEN 'Tarjeta'     IN labels(n) THEN 1 END) AS tarjetas,
        count(CASE WHEN 'Transaccion' IN labels(n) THEN 1 END) AS transacciones,
        count(CASE WHEN 'Comercio'    IN labels(n) THEN 1 END) AS comercios,
        count(CASE WHEN 'Dispositivo' IN labels(n) THEN 1 END) AS dispositivos,
        count(CASE WHEN 'Ubicacion'   IN labels(n) THEN 1 END) AS ubicaciones
    """)

    rels = run_query("MATCH ()-[r]->() RETURN count(r) AS totalRelaciones")

    sospechosas = run_query("""
    MATCH (t:Transaccion)
    WHERE t.esSospechosa = true
    RETURN
        count(t)       AS totalSospechosas,
        sum(t.monto)   AS montoFraude,
        avg(t.fraudScore) AS avgScore
    """)

    # TX por mes (últimos 12 meses)
    por_mes = run_query("""
    MATCH (t:Transaccion)
    WHERE t.fecha IS NOT NULL
    WITH t.fecha.year AS anio, t.fecha.month AS mes,
         count(t) AS total,
         count(CASE WHEN t.esSospechosa THEN 1 END) AS sospechosas
    RETURN anio, mes, total, sospechosas
    ORDER BY anio DESC, mes DESC
    LIMIT 12
    """)

    # Distribución por nivelRiesgo
    por_nivel = run_query("""
    MATCH (t:Transaccion)
    WHERE t.nivelRiesgo IS NOT NULL
    RETURN t.nivelRiesgo AS nivel, count(t) AS cantidad
    ORDER BY cantidad DESC
    """)

    # Top 10 países por TX sospechosas
    por_pais = run_query("""
    MATCH (t:Transaccion {esSospechosa: true})-[:EN_UBICACION]->(u:Ubicacion)
    RETURN u.pais AS pais, count(t) AS cantidad, sum(t.monto) AS monto
    ORDER BY cantidad DESC
    LIMIT 10
    """)

    # TX por hora del día
    por_hora = run_query("""
    MATCH (t:Transaccion)
    WHERE t.horaLocal IS NOT NULL
    RETURN t.horaLocal AS hora,
           count(t) AS total,
           count(CASE WHEN t.esSospechosa THEN 1 END) AS sospechosas
    ORDER BY hora
    """)

    return {
        "conteos":     {**(conteos[0] if conteos else {}), "relaciones": rels[0]["totalRelaciones"] if rels else 0},
        "sospechosas": sospechosas[0] if sospechosas else {},
        "porMes":      list(reversed(por_mes)),
        "porNivel":    por_nivel,
        "porPais":     por_pais,
        "porHora":     por_hora,
    }
