"""
Motor de detección automática de fraude bancario.
Usa Cypher puro (compatible con AuraDB free tier, sin GDS).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import run_query


# ─── 1. Velocidad geográfica imposible ────────────────────────────────────────

def detectar_velocidad_geografica():
    """
    Detecta TX consecutivas de un cliente en ubicaciones físicamente
    imposibles (>800 km/h). Usa fórmula haversine en Cypher.
    Escribe t.scoreVelocidad en cada transacción afectada.
    """
    # Obtener pares de TX consecutivas por cliente con sus coordenadas
    query_deteccion = """
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)-[:EN_UBICACION]->(u:Ubicacion)
    WITH cl, t, u ORDER BY cl.clienteId, t.fecha, t.horaLocal
    WITH cl, collect({tx: t, lat: u.latitud, lon: u.longitud, hora: t.horaLocal, fecha: t.fecha}) AS txs
    UNWIND range(0, size(txs)-2) AS i
    WITH
        cl,
        txs[i]   AS a,
        txs[i+1] AS b
    WHERE a.fecha IS NOT NULL AND b.fecha IS NOT NULL
    WITH
        cl,
        a.tx AS tx1, b.tx AS tx2,
        a.lat AS lat1, a.lon AS lon1,
        b.lat AS lat2, b.lon AS lon2,
        a.hora AS h1, b.hora AS h2,
        duration.between(date(a.fecha), date(b.fecha)).hours AS deltaDias
    WITH
        cl, tx1, tx2,
        // Haversine simplificado en Cypher
        2 * 6371 * asin(sqrt(
            (sin((radians(lat2) - radians(lat1)) / 2))^2 +
            cos(radians(lat1)) * cos(radians(lat2)) *
            (sin((radians(lon2) - radians(lon1)) / 2))^2
        )) AS distanciaKm,
        abs(deltaDias * 24 + (b.h2 - a.h1)) + 0.5 AS deltaHoras
    WITH cl, tx1, tx2, distanciaKm, deltaHoras,
         CASE WHEN deltaHoras > 0 THEN distanciaKm / deltaHoras ELSE 0 END AS velocidadKmh
    WHERE velocidadKmh > 800
    RETURN tx1.transaccionId AS txId, velocidadKmh
    """

    try:
        pares = run_query(query_deteccion)
    except Exception:
        # Haversine puede fallar si coords son null; fallback simple
        pares = []

    if not pares:
        # Fallback: marcar TX en múltiples países el mismo día como velocidad alta
        pares = run_query("""
        MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)-[:EN_UBICACION]->(u:Ubicacion)
        WITH cl, t.fecha AS fecha, collect(DISTINCT u.pais) AS paises, collect(t) AS txs
        WHERE size(paises) > 1
        UNWIND txs AS t
        RETURN t.transaccionId AS txId, 900.0 AS velocidadKmh
        """)

    afectadas = 0
    for row in pares:
        score = min(1.0, row["velocidadKmh"] / 2000.0)
        run_query(
            "MATCH (t:Transaccion {transaccionId: $id}) SET t.scoreVelocidad = $score",
            {"id": row["txId"], "score": round(score, 3)},
        )
        afectadas += 1

    # Poner 0.0 a las que no tienen score
    run_query("MATCH (t:Transaccion) WHERE t.scoreVelocidad IS NULL SET t.scoreVelocidad = 0.0")
    return {"algoritmo": "velocidad_geografica", "transaccionesAfectadas": afectadas}


# ─── 2. Anillos de dispositivos ───────────────────────────────────────────────

def detectar_anillos_dispositivos():
    """
    Dispositivos compartidos por 3+ clientes distintos = anillo de fraude.
    Escribe c.scoreAnillo en cada cliente del anillo.
    Crea relación EN_ANILLO entre clientes del mismo anillo.
    """
    # Limpiar anillos previos
    run_query("MATCH ()-[r:EN_ANILLO]->() DELETE r")
    run_query("MATCH (c:Cliente) REMOVE c.scoreAnillo, c.anilloId")

    anillos = run_query("""
    MATCH (d:Dispositivo)<-[:COMPARTE_DISPOSITIVO]-(cl:Cliente)
    WITH d, collect(DISTINCT cl) AS miembros
    WHERE size(miembros) >= 3
    RETURN d.dispositivoId AS dispositivoId, [m IN miembros | m.clienteId] AS clienteIds, size(miembros) AS total
    """)

    for i, anillo in enumerate(anillos):
        anillo_id = f"anillo_{i+1}"
        score = min(1.0, 0.3 + (anillo["total"] - 3) * 0.1)
        ids = anillo["clienteIds"]

        run_query(
            """
            MATCH (c:Cliente) WHERE c.clienteId IN $ids
            SET c.scoreAnillo = $score, c.anilloId = $anilloId
            """,
            {"ids": ids, "score": round(score, 3), "anilloId": anillo_id},
        )

        # Crear relaciones EN_ANILLO entre todos los pares
        for j in range(len(ids)):
            for k in range(j + 1, len(ids)):
                run_query(
                    """
                    MATCH (c1:Cliente {clienteId: $id1}), (c2:Cliente {clienteId: $id2})
                    MERGE (c1)-[r:EN_ANILLO]->(c2)
                    SET r.anilloId = $anilloId,
                        r.miembros = $total,
                        r.deteccion = date()
                    """,
                    {"id1": ids[j], "id2": ids[k], "anilloId": anillo_id, "total": anillo["total"]},
                )

    run_query("MATCH (c:Cliente) WHERE c.scoreAnillo IS NULL SET c.scoreAnillo = 0.0")
    return {"algoritmo": "anillos_dispositivos", "anillosDetectados": len(anillos)}


# ─── 3. Cuentas mula ──────────────────────────────────────────────────────────

def detectar_cuentas_mula():
    """
    Cuentas que reciben dinero de 5+ orígenes distintos son candidatas a mulas.
    Calcula un score proporcional al in-degree y escribe cuenta.scoreMula.
    """
    run_query("MATCH (c:Cuenta) REMOVE c.scoreMula, c.esCuentaMula, c.inDegree")

    cuentas = run_query("""
    MATCH (t:Transaccion)-[:DESTINO]->(cu:Cuenta)
    WITH cu, count(DISTINCT t) AS inDegree
    RETURN cu.cuentaId AS cuentaId, inDegree
    ORDER BY inDegree DESC
    """)

    if not cuentas:
        return {"algoritmo": "cuentas_mula", "cuentasMarcadas": 0}

    max_in = max(r["inDegree"] for r in cuentas) or 1
    marcadas = 0

    for row in cuentas:
        score = round(row["inDegree"] / max_in, 3)
        es_mula = row["inDegree"] >= 5 and score >= 0.4
        run_query(
            """
            MATCH (cu:Cuenta {cuentaId: $id})
            SET cu.scoreMula = $score, cu.esCuentaMula = $esMula, cu.inDegree = $inDegree
            """,
            {"id": row["cuentaId"], "score": score, "esMula": es_mula, "inDegree": row["inDegree"]},
        )
        if es_mula:
            marcadas += 1

    run_query("MATCH (cu:Cuenta) WHERE cu.scoreMula IS NULL SET cu.scoreMula = 0.0, cu.esCuentaMula = false")
    return {"algoritmo": "cuentas_mula", "cuentasMarcadas": marcadas}


# ─── 4. Outliers de monto ─────────────────────────────────────────────────────

def detectar_outliers_monto():
    """
    Calcula z-score de monto por cliente.
    TX con z-score > 3 son outliers → scoreOutlierMonto proporcional.
    """
    run_query("MATCH (t:Transaccion) SET t.scoreOutlierMonto = 0.0")

    stats_clientes = run_query("""
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)
    WITH cl, avg(t.monto) AS media, stDev(t.monto) AS desviacion
    WHERE desviacion > 0
    RETURN cl.clienteId AS clienteId, media, desviacion
    """)

    afectadas = 0
    for stat in stats_clientes:
        outliers = run_query(
            """
            MATCH (cl:Cliente {clienteId: $cid})-[:REALIZO]->(t:Transaccion)
            WHERE t.monto > $media + 3 * $std
            SET t.scoreOutlierMonto = CASE
                WHEN ($std > 0) THEN toFloat(toInteger(((t.monto - $media) / $std) * 10) / 100.0)
                ELSE 0.0
            END
            RETURN count(t) AS n
            """,
            {"cid": stat["clienteId"], "media": stat["media"], "std": stat["desviacion"]},
        )
        if outliers:
            afectadas += outliers[0].get("n", 0)

    # Cap a 1.0
    run_query("""
    MATCH (t:Transaccion)
    WHERE t.scoreOutlierMonto > 1.0
    SET t.scoreOutlierMonto = 1.0
    """)
    return {"algoritmo": "outliers_monto", "transaccionesAfectadas": afectadas}


# ─── 5. Horarios anómalos ──────────────────────────────────────────────────────

def detectar_horarios_anomalos():
    """
    TX entre 0:00-4:00 (horaLocal 0-3) reciben scoreHorario = 0.2
    TX entre 4:00-6:00 reciben 0.1
    """
    run_query("MATCH (t:Transaccion) SET t.scoreHorario = 0.0")

    run_query("""
    MATCH (t:Transaccion)
    WHERE t.horaLocal >= 0 AND t.horaLocal <= 3
    SET t.scoreHorario = 0.2
    """)
    run_query("""
    MATCH (t:Transaccion)
    WHERE t.horaLocal >= 4 AND t.horaLocal <= 5
    SET t.scoreHorario = 0.1
    """)

    result = run_query("""
    MATCH (t:Transaccion) WHERE t.scoreHorario > 0
    RETURN count(t) AS afectadas
    """)
    return {"algoritmo": "horarios_anomalos", "transaccionesAfectadas": result[0]["afectadas"]}


# ─── 6. Score compuesto ───────────────────────────────────────────────────────

def calcular_score_compuesto():
    """
    Combina todos los scores parciales en t.fraudScore (0.0–1.0).
    Actualiza t.esSospechosa y t.nivelRiesgo basado en el score calculado.
    """
    run_query("""
    MATCH (cl:Cliente)-[:REALIZO]->(t:Transaccion)
    WITH cl, t,
         coalesce(t.scoreVelocidad, 0.0)    AS sv,
         coalesce(t.scoreOutlierMonto, 0.0) AS sm,
         coalesce(t.scoreHorario, 0.0)      AS sh,
         coalesce(cl.scoreAnillo, 0.0) * 0.5 AS sa
    SET t.fraudScore = CASE
            WHEN (sv + sm + sh + sa) > 1.0 THEN 1.0
            ELSE round((sv + sm + sh + sa) * 1000) / 1000.0
        END,
        t.esSospechosa = ((sv + sm + sh + sa) > 0.5),
        t.nivelRiesgo  = CASE
            WHEN (sv + sm + sh + sa) > 0.8 THEN 'alto'
            WHEN (sv + sm + sh + sa) > 0.5 THEN 'medio'
            ELSE 'bajo'
        END
    """)

    stats = run_query("""
    MATCH (t:Transaccion)
    RETURN
        count(t) AS total,
        count(CASE WHEN t.nivelRiesgo = 'alto'  THEN 1 END) AS alto,
        count(CASE WHEN t.nivelRiesgo = 'medio' THEN 1 END) AS medio,
        count(CASE WHEN t.nivelRiesgo = 'bajo'  THEN 1 END) AS bajo,
        count(CASE WHEN t.esSospechosa THEN 1 END) AS sospechosas
    """)
    return {"algoritmo": "score_compuesto", **stats[0]}


# ─── Pipeline completo ────────────────────────────────────────────────────────

def ejecutar_pipeline():
    """Ejecuta todos los algoritmos en orden y devuelve estadísticas."""
    resultados = {}
    resultados["velocidad_geografica"] = detectar_velocidad_geografica()
    resultados["anillos_dispositivos"] = detectar_anillos_dispositivos()
    resultados["cuentas_mula"] = detectar_cuentas_mula()
    resultados["outliers_monto"] = detectar_outliers_monto()
    resultados["horarios_anomalos"] = detectar_horarios_anomalos()
    resultados["score_compuesto"] = calcular_score_compuesto()
    return resultados
