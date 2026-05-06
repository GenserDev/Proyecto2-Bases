"""
Endpoints del motor de detección automática de fraude.
"""
from fastapi import APIRouter, Query
from database import run_query
from services.fraud_engine import (
    ejecutar_pipeline,
    detectar_velocidad_geografica,
    detectar_anillos_dispositivos,
    detectar_cuentas_mula,
    detectar_outliers_monto,
    detectar_horarios_anomalos,
    calcular_score_compuesto,
)

router = APIRouter(prefix="/deteccion", tags=["Detección de Fraude"])

ALGORITMOS = {
    "velocidad":  detectar_velocidad_geografica,
    "anillos":    detectar_anillos_dispositivos,
    "mula":       detectar_cuentas_mula,
    "outliers":   detectar_outliers_monto,
    "horarios":   detectar_horarios_anomalos,
    "compuesto":  calcular_score_compuesto,
}


@router.post("/recalcular", summary="Ejecutar pipeline completo de detección")
def recalcular():
    """Ejecuta los 5 algoritmos + score compuesto y devuelve estadísticas."""
    return ejecutar_pipeline()


@router.post("/{nombre}", summary="Ejecutar un algoritmo individual")
def ejecutar_algoritmo(nombre: str):
    """
    Nombres válidos: velocidad, anillos, mula, outliers, horarios, compuesto
    """
    fn = ALGORITMOS.get(nombre)
    if fn is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Algoritmo '{nombre}' no existe. Válidos: {list(ALGORITMOS)}")
    return fn()


@router.get("/alertas", summary="Transacciones con fraudScore alto")
def alertas(
    min_score: float = Query(0.5, ge=0.0, le=1.0, alias="minScore"),
    limit: int = Query(50, ge=1, le=500),
    pais: str = Query(None),
    fecha_inicio: str = Query(None, alias="fechaInicio"),
    fecha_fin: str = Query(None, alias="fechaFin"),
):
    filtros = ["t.fraudScore >= $minScore"]
    params: dict = {"minScore": min_score, "limit": limit}

    if pais:
        filtros.append("u.pais = $pais")
        params["pais"] = pais
    if fecha_inicio:
        filtros.append("t.fecha >= date($fechaInicio)")
        params["fechaInicio"] = fecha_inicio
    if fecha_fin:
        filtros.append("t.fecha <= date($fechaFin)")
        params["fechaFin"] = fecha_fin

    where = " AND ".join(filtros)
    query = f"""
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)
    OPTIONAL MATCH (t)-[:EN_UBICACION]->(u:Ubicacion)
    OPTIONAL MATCH (t)-[:ORIGEN]->(cu:Cuenta)
    WHERE {where}
    RETURN
        t.transaccionId     AS transaccionId,
        t.monto             AS monto,
        t.fecha             AS fecha,
        t.horaLocal         AS horaLocal,
        t.canal             AS canal,
        t.fraudScore        AS fraudScore,
        t.nivelRiesgo       AS nivelRiesgo,
        t.esSospechosa      AS esSospechosa,
        t.scoreVelocidad    AS scoreVelocidad,
        t.scoreOutlierMonto AS scoreOutlierMonto,
        t.scoreHorario      AS scoreHorario,
        cl.clienteId        AS clienteId,
        cl.nombre           AS clienteNombre,
        cl.apellido         AS clienteApellido,
        cl.scoreAnillo      AS scoreAnillo,
        u.pais              AS pais,
        u.ciudad            AS ciudad,
        cu.cuentaId         AS cuentaId
    ORDER BY t.fraudScore DESC
    LIMIT $limit
    """
    return run_query(query, params)


@router.get("/clientes-riesgo", summary="Ranking de clientes por riesgo de fraude")
def clientes_riesgo(top: int = Query(20, ge=1, le=200)):
    return run_query("""
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)
    WHERE t.fraudScore IS NOT NULL
    WITH cl,
         count(t)                      AS totalTx,
         count(CASE WHEN t.esSospechosa THEN 1 END) AS sospechosas,
         avg(t.fraudScore)             AS avgScore,
         max(t.fraudScore)             AS maxScore,
         sum(t.monto)                  AS montoTotal
    RETURN
        cl.clienteId   AS clienteId,
        cl.nombre      AS nombre,
        cl.apellido    AS apellido,
        cl.nivelRiesgo AS nivelRiesgo,
        cl.scoreAnillo AS scoreAnillo,
        totalTx, sospechosas, avgScore, maxScore, montoTotal,
        round(sospechosas * 100.0 / totalTx) AS pctSospechosas
    ORDER BY maxScore DESC, sospechosas DESC
    LIMIT $top
    """, {"top": top})


@router.get("/anillos", summary="Anillos de fraude detectados")
def listar_anillos():
    return run_query("""
    MATCH (c1:Cliente)-[r:EN_ANILLO]->(c2:Cliente)
    RETURN DISTINCT
        r.anilloId           AS anilloId,
        r.miembros           AS miembros,
        collect(DISTINCT c1.clienteId + ' ' + c1.nombre) AS participantes
    ORDER BY r.miembros DESC
    """)


@router.get("/estadisticas", summary="Estadísticas globales de fraude detectado")
def estadisticas():
    stats_tx = run_query("""
    MATCH (t:Transaccion)
    RETURN
        count(t)                                           AS totalTransacciones,
        count(CASE WHEN t.esSospechosa    THEN 1 END)     AS sospechosas,
        count(CASE WHEN t.nivelRiesgo='alto'  THEN 1 END) AS nivelAlto,
        count(CASE WHEN t.nivelRiesgo='medio' THEN 1 END) AS nivelMedio,
        count(CASE WHEN t.nivelRiesgo='bajo'  THEN 1 END) AS nivelBajo,
        avg(t.fraudScore)                                  AS avgFraudScore,
        sum(CASE WHEN t.esSospechosa THEN t.monto ELSE 0 END) AS montoFraude
    """)
    stats_anillos = run_query("MATCH ()-[r:EN_ANILLO]->() RETURN count(r)/2 AS anillosActivos")
    stats_mulas   = run_query("MATCH (cu:Cuenta {esCuentaMula: true}) RETURN count(cu) AS cuentasMula")

    return {
        "transacciones": stats_tx[0] if stats_tx else {},
        "anillosActivos": stats_anillos[0].get("anillosActivos", 0) if stats_anillos else 0,
        "cuentasMula":    stats_mulas[0].get("cuentasMula", 0) if stats_mulas else 0,
    }
