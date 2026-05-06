"""
Endpoints para visualización de grafos con vis-network.
Devuelve nodos y aristas en el formato que vis-network espera.
"""
from fastapi import APIRouter, Query, HTTPException
from database import run_query

router = APIRouter(prefix="/grafo", tags=["Visualización de Grafo"])

# Colores por label
COLORES = {
    "Cliente":      {"background": "#4f46e5", "border": "#3730a3", "font": "#ffffff"},
    "Cuenta":       {"background": "#16a34a", "border": "#15803d", "font": "#ffffff"},
    "Tarjeta":      {"background": "#0891b2", "border": "#0e7490", "font": "#ffffff"},
    "Transaccion":  {"background": "#d97706", "border": "#b45309", "font": "#ffffff"},
    "Comercio":     {"background": "#7c3aed", "border": "#6d28d9", "font": "#ffffff"},
    "Dispositivo":  {"background": "#64748b", "border": "#475569", "font": "#ffffff"},
    "Ubicacion":    {"background": "#0d9488", "border": "#0f766e", "font": "#ffffff"},
    "sospechosa":   {"background": "#dc2626", "border": "#b91c1c", "font": "#ffffff"},
}


def _label_color(labels: list, es_sospechosa: bool = False):
    if es_sospechosa:
        return COLORES["sospechosa"]
    for l in labels:
        if l in COLORES:
            return COLORES[l]
    return {"background": "#94a3b8", "border": "#64748b", "font": "#ffffff"}


def _formato_vis(records):
    """Convierte resultados Cypher a {nodes, edges} para vis-network."""
    nodes_map = {}
    edges = []

    for r in records:
        # Nodo inicio
        if r.get("nId") and r["nId"] not in nodes_map:
            color = _label_color(
                r.get("nLabels", []),
                r.get("nEsSospechosa", False)
            )
            nodes_map[r["nId"]] = {
                "id":    r["nId"],
                "label": r.get("nLabel", r["nId"]),
                "title": r.get("nProps", ""),
                "color": color,
                "group": r.get("nLabels", ["?"])[0],
            }
        # Nodo fin
        if r.get("mId") and r["mId"] not in nodes_map:
            color = _label_color(
                r.get("mLabels", []),
                r.get("mEsSospechosa", False)
            )
            nodes_map[r["mId"]] = {
                "id":    r["mId"],
                "label": r.get("mLabel", r["mId"]),
                "title": r.get("mProps", ""),
                "color": color,
                "group": r.get("mLabels", ["?"])[0],
            }
        # Arista
        if r.get("rId"):
            edges.append({
                "id":     r["rId"],
                "from":   r["nId"],
                "to":     r["mId"],
                "label":  r.get("rType", ""),
                "width":  max(1, min(8, int(r.get("rMonto", 0) / 5000))),
                "title":  r.get("rProps", ""),
                "arrows": "to",
            })

    return {"nodes": list(nodes_map.values()), "edges": edges}


_RETURN_COLS = """
    elementId(src)      AS nId,
    labels(src)         AS nLabels,
    CASE
        WHEN src.clienteId     IS NOT NULL THEN src.nombre + ' ' + coalesce(src.apellido,'')
        WHEN src.transaccionId IS NOT NULL THEN 'TX ' + src.transaccionId
        WHEN src.cuentaId      IS NOT NULL THEN 'Cta ' + src.numeroCuenta
        WHEN src.comercioId    IS NOT NULL THEN src.nombre
        WHEN src.dispositivoId IS NOT NULL THEN src.tipo + ' ' + src.ip
        WHEN src.ubicacionId   IS NOT NULL THEN src.ciudad + ', ' + src.pais
        ELSE elementId(src)
    END AS nLabel,
    coalesce(src.esSospechosa, false) AS nEsSospechosa,
    '' AS nProps,
    elementId(rel)                    AS rId,
    type(rel)                         AS rType,
    coalesce(rel.monto, 0)            AS rMonto,
    '' AS rProps,
    elementId(dst)      AS mId,
    labels(dst)         AS mLabels,
    CASE
        WHEN dst.clienteId     IS NOT NULL THEN dst.nombre + ' ' + coalesce(dst.apellido,'')
        WHEN dst.transaccionId IS NOT NULL THEN 'TX ' + dst.transaccionId
        WHEN dst.cuentaId      IS NOT NULL THEN 'Cta ' + dst.numeroCuenta
        WHEN dst.comercioId    IS NOT NULL THEN dst.nombre
        WHEN dst.dispositivoId IS NOT NULL THEN dst.tipo + ' ' + dst.ip
        WHEN dst.ubicacionId   IS NOT NULL THEN dst.ciudad + ', ' + dst.pais
        ELSE elementId(dst)
    END AS mLabel,
    coalesce(dst.esSospechosa, false) AS mEsSospechosa,
    '' AS mProps
"""


@router.get("/subgrafo/{node_id}", summary="Subgrafo de N saltos alrededor de un nodo")
def subgrafo(node_id: str, saltos: int = Query(2, ge=1, le=3)):
    central = run_query("""
    MATCH (n)
    WHERE n.clienteId = $id OR n.transaccionId = $id OR n.cuentaId = $id
       OR n.tarjetaId = $id OR n.comercioId = $id OR n.dispositivoId = $id
       OR n.ubicacionId = $id
    RETURN elementId(n) AS eid
    LIMIT 1
    """, {"id": node_id})

    if not central:
        raise HTTPException(status_code=404, detail=f"Nodo '{node_id}' no encontrado")

    eid = central[0]["eid"]

    # Hop 1: vecinos directos del nodo central
    hop1 = run_query(f"""
    MATCH (src)-[rel]-(dst)
    WHERE elementId(src) = $eid
    RETURN {_RETURN_COLS}
    LIMIT 50
    """, {"eid": eid})

    records = hop1

    if saltos >= 2 and hop1:
        neighbor_eids = list({r["mId"] for r in hop1 if r.get("mId")})[:25]
        hop2 = run_query(f"""
        MATCH (src)-[rel]-(dst)
        WHERE elementId(src) IN $eids
          AND elementId(dst) <> $centerEid
        RETURN {_RETURN_COLS}
        LIMIT 120
        """, {"eids": neighbor_eids, "centerEid": eid})
        records = hop1 + hop2

    if saltos >= 3 and len(records) > len(hop1):
        hop2_eids = list({r["mId"] for r in records if r.get("mId") and r["mId"] != eid})[:20]
        hop3 = run_query(f"""
        MATCH (src)-[rel]-(dst)
        WHERE elementId(src) IN $eids
          AND elementId(dst) <> $centerEid
        RETURN {_RETURN_COLS}
        LIMIT 80
        """, {"eids": hop2_eids, "centerEid": eid})
        records = records + hop3

    return _formato_vis(records)


@router.get("/overview", summary="Vista general del grafo (muestra aleatoria)")
def overview(limit: int = Query(80, ge=10, le=300)):
    """Devuelve una muestra del grafo para vista inicial."""
    records = run_query(f"""
    MATCH (n)-[r]->(m)
    WITH n, r, m, rand() AS rnd
    ORDER BY rnd
    LIMIT {limit}
    RETURN
        elementId(n)        AS nId,
        labels(n)           AS nLabels,
        CASE
            WHEN n.clienteId     IS NOT NULL THEN n.nombre + ' ' + coalesce(n.apellido,'')
            WHEN n.transaccionId IS NOT NULL THEN 'TX'
            WHEN n.cuentaId      IS NOT NULL THEN 'Cta'
            WHEN n.comercioId    IS NOT NULL THEN n.nombre
            WHEN n.dispositivoId IS NOT NULL THEN n.tipo
            WHEN n.ubicacionId   IS NOT NULL THEN n.ciudad
            ELSE 'Nodo'
        END AS nLabel,
        coalesce(n.esSospechosa, false) AS nEsSospechosa,
        '' AS nProps,
        elementId(r)  AS rId,
        type(r)       AS rType,
        coalesce(r.monto, 0) AS rMonto,
        '' AS rProps,
        elementId(m)        AS mId,
        labels(m)           AS mLabels,
        CASE
            WHEN m.clienteId     IS NOT NULL THEN m.nombre + ' ' + coalesce(m.apellido,'')
            WHEN m.transaccionId IS NOT NULL THEN 'TX'
            WHEN m.cuentaId      IS NOT NULL THEN 'Cta'
            WHEN m.comercioId    IS NOT NULL THEN m.nombre
            WHEN m.dispositivoId IS NOT NULL THEN m.tipo
            WHEN m.ubicacionId   IS NOT NULL THEN m.ciudad
            ELSE 'Nodo'
        END AS mLabel,
        coalesce(m.esSospechosa, false) AS mEsSospechosa,
        '' AS mProps
    """)
    return _formato_vis(records)
