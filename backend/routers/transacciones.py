"""
Nodos: Transaccion
Labels: Transaccion | Transaccion:TransaccionSospechosa
Propiedades: transaccionId(String), monto(Float), fecha(Date), descripcion(String),
             estado(String), esSospechosa(Boolean), canal(String),
             moneda(String), categoriaGasto(String), horaLocal(Integer)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/transacciones", tags=["Transacciones"])


class TransaccionCreate(BaseModel):
    transaccionId: str
    monto: float
    fecha: str
    descripcion: str
    estado: str = "aprobada"
    esSospechosa: bool = False
    canal: str = "POS"
    moneda: str = "GTQ"
    categoriaGasto: str
    horaLocal: int = 12


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Transaccion (1 label)")
def crear_transaccion(tx: TransaccionCreate):
    query = """
    CREATE (t:Transaccion {
        transaccionId:  $transaccionId,
        monto:          $monto,
        fecha:          date($fecha),
        descripcion:    $descripcion,
        estado:         $estado,
        esSospechosa:   $esSospechosa,
        canal:          $canal,
        moneda:         $moneda,
        categoriaGasto: $categoriaGasto,
        horaLocal:      $horaLocal
    })
    RETURN t
    """
    result = run_query(query, tx.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear transaccion")
    return result[0]


@router.post("/multilabel", summary="Crear Transaccion con 2+ labels")
def crear_transaccion_multilabel(tx: TransaccionCreate, label_extra: str = "TransaccionSospechosa"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (t:Transaccion:`{label_extra_safe}` {{transaccionId: $transaccionId}})
    ON CREATE SET
        t.monto          = $monto,
        t.fecha          = date($fecha),
        t.descripcion    = $descripcion,
        t.estado         = $estado,
        t.esSospechosa   = $esSospechosa,
        t.canal          = $canal,
        t.moneda         = $moneda,
        t.categoriaGasto = $categoriaGasto,
        t.horaLocal      = $horaLocal
    RETURN t
    """
    result = run_query(query, tx.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear transaccion")
    return result[0]


@router.get("/", summary="Listar Transacciones con filtros")
def listar_transacciones(
    estado: Optional[str] = None,
    esSospechosa: Optional[bool] = None,
    canal: Optional[str] = None,
    montoMin: Optional[float] = None,
    montoMax: Optional[float] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if estado:
        filtros.append("t.estado = $estado")
        params["estado"] = estado
    if esSospechosa is not None:
        filtros.append("t.esSospechosa = $esSospechosa")
        params["esSospechosa"] = esSospechosa
    if canal:
        filtros.append("t.canal = $canal")
        params["canal"] = canal
    if montoMin is not None:
        filtros.append("t.monto >= $montoMin")
        params["montoMin"] = montoMin
    if montoMax is not None:
        filtros.append("t.monto <= $montoMax")
        params["montoMax"] = montoMax
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (t:Transaccion) {where} RETURN t ORDER BY t.fecha DESC SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Transacciones")
def agregaciones_transacciones():
    query = """
    MATCH (t:Transaccion)
    RETURN
        count(t)                              AS totalTransacciones,
        avg(t.monto)                          AS montoPromedio,
        sum(t.monto)                          AS montoTotal,
        max(t.monto)                          AS montoMaximo,
        count(CASE WHEN t.esSospechosa THEN 1 END) AS transaccionesSospechosas,
        collect(DISTINCT t.estado)            AS estados
    """
    return run_query(query)


@router.get("/{transaccion_id}", summary="Obtener una Transaccion por ID")
def obtener_transaccion(transaccion_id: str):
    result = run_query(
        "MATCH (t:Transaccion {transaccionId: $id}) RETURN t",
        {"id": transaccion_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return result[0]


@router.put("/{transaccion_id}", summary="Actualizar propiedades de 1 Transaccion")
def actualizar_transaccion(transaccion_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"id": transaccion_id, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Transaccion {{transaccionId: $id}}) SET {sets} RETURN t",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Transacciones")
def actualizar_transacciones_bulk(estado: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"estado": estado, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Transaccion {{estado: $estado}}) SET {sets} RETURN count(t) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{transaccion_id}/propiedades", summary="Agregar propiedades a 1 Transaccion")
def agregar_propiedades_transaccion(transaccion_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"id": transaccion_id, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Transaccion {{transaccionId: $id}}) SET {sets} RETURN t",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Transacciones")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Transaccion) WHERE t.transaccionId IN $ids SET {sets} RETURN count(t) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{transaccion_id}/propiedades", summary="Eliminar propiedades de 1 Transaccion")
def eliminar_propiedades_transaccion(transaccion_id: str, propiedades: List[str]):
    removes = ", ".join([f"t.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (t:Transaccion {{transaccionId: $id}}) REMOVE {removes} RETURN t",
        {"id": transaccion_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Transacciones")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"t.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (t:Transaccion) WHERE t.transaccionId IN $ids REMOVE {removes} RETURN count(t) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{transaccion_id}", summary="Eliminar 1 Transaccion")
def eliminar_transaccion(transaccion_id: str):
    result = run_query(
        "MATCH (t:Transaccion {transaccionId: $id}) DETACH DELETE t RETURN count(t) AS eliminados",
        {"id": transaccion_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Transacciones")
def eliminar_transacciones_bulk(ids: List[str]):
    result = run_query(
        "MATCH (t:Transaccion) WHERE t.transaccionId IN $ids DETACH DELETE t RETURN count(t) AS eliminados",
        {"ids": ids},
    )
    return result[0]
