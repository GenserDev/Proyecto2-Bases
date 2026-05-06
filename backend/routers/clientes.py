"""
Nodos: Cliente
Labels: Cliente | Cliente:ClienteVIP | Cliente:ClienteSospechoso
Propiedades: clienteId(String), nombre(String), apellido(String), email(String),
             telefono(String), fechaNacimiento(Date), activo(Boolean),
             nivelRiesgo(String), etiquetasRiesgo(List<String>), ingresoMensual(Float)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/clientes", tags=["Clientes"])


class ClienteCreate(BaseModel):
    clienteId: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    fechaNacimiento: str  # ISO: "YYYY-MM-DD"
    activo: bool = True
    nivelRiesgo: str = "bajo"
    etiquetasRiesgo: List[str] = []
    ingresoMensual: float = 0.0


class PropiedadesUpdate(BaseModel):
    propiedades: dict


# ── CREATE con 1 label ────────────────────────────────────────────────────────
@router.post("/", summary="Crear Cliente (1 label)")
def crear_cliente(cliente: ClienteCreate):
    query = """
    CREATE (c:Cliente {
        clienteId:       $clienteId,
        nombre:          $nombre,
        apellido:        $apellido,
        email:           $email,
        telefono:        $telefono,
        fechaNacimiento: date($fechaNacimiento),
        activo:          $activo,
        nivelRiesgo:     $nivelRiesgo,
        etiquetasRiesgo: $etiquetasRiesgo,
        ingresoMensual:  $ingresoMensual
    })
    RETURN c
    """
    result = run_query(query, cliente.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear cliente")
    return result[0]


# ── CREATE con 2+ labels ──────────────────────────────────────────────────────
@router.post("/multilabel", summary="Crear Cliente con 2+ labels (Cliente + extra)")
def crear_cliente_multilabel(cliente: ClienteCreate, label_extra: str = "ClienteVIP"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (c:Cliente:`{label_extra_safe}` {{clienteId: $clienteId}})
    ON CREATE SET
        c.nombre          = $nombre,
        c.apellido        = $apellido,
        c.email           = $email,
        c.telefono        = $telefono,
        c.fechaNacimiento = date($fechaNacimiento),
        c.activo          = $activo,
        c.nivelRiesgo     = $nivelRiesgo,
        c.etiquetasRiesgo = $etiquetasRiesgo,
        c.ingresoMensual  = $ingresoMensual
    RETURN c
    """
    result = run_query(query, cliente.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear cliente")
    return result[0]


# ── READ: un cliente ──────────────────────────────────────────────────────────
@router.get("/{cliente_id}", summary="Obtener un Cliente por ID")
def obtener_cliente(cliente_id: str):
    result = run_query(
        "MATCH (c:Cliente {clienteId: $id}) RETURN c",
        {"id": cliente_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result[0]


# ── READ: muchos clientes con filtros ────────────────────────────────────────
@router.get("/", summary="Listar Clientes con filtros")
def listar_clientes(
    nivelRiesgo: Optional[str] = None,
    activo: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if nivelRiesgo:
        filtros.append("c.nivelRiesgo = $nivelRiesgo")
        params["nivelRiesgo"] = nivelRiesgo
    if activo is not None:
        filtros.append("c.activo = $activo")
        params["activo"] = activo
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (c:Cliente) {where} RETURN c SKIP $skip LIMIT $limit"
    return run_query(query, params)


# ── READ: agregaciones ────────────────────────────────────────────────────────
@router.get("/agregaciones/resumen", summary="Conteos y promedios de Clientes")
def agregaciones_clientes():
    query = """
    MATCH (c:Cliente)
    RETURN
        count(c)                        AS totalClientes,
        avg(c.ingresoMensual)           AS ingresoPromedio,
        count(CASE WHEN c.activo THEN 1 END) AS clientesActivos,
        collect(DISTINCT c.nivelRiesgo) AS nivelesRiesgo
    """
    return run_query(query)


# ── UPDATE: actualizar propiedades de 1 nodo ─────────────────────────────────
@router.put("/{cliente_id}", summary="Actualizar propiedades de 1 Cliente")
def actualizar_cliente(cliente_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": cliente_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cliente {{clienteId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result[0]


# ── UPDATE: actualizar propiedades de múltiples nodos ───────────────────────
@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Clientes")
def actualizar_clientes_bulk(nivelRiesgo: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"nivelRiesgo": nivelRiesgo, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cliente {{nivelRiesgo: $nivelRiesgo}}) SET {sets} RETURN count(c) AS actualizados",
        params,
    )
    return result[0]


# ── PATCH: agregar propiedades a 1 nodo ──────────────────────────────────────
@router.patch("/{cliente_id}/propiedades", summary="Agregar propiedades a 1 Cliente")
def agregar_propiedades_cliente(cliente_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": cliente_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cliente {{clienteId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result[0]


# ── PATCH: agregar propiedades a múltiples nodos ─────────────────────────────
@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Clientes")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cliente) WHERE c.clienteId IN $ids SET {sets} RETURN count(c) AS modificados",
        params,
    )
    return result[0]


# ── DELETE propiedades de 1 nodo ─────────────────────────────────────────────
@router.delete("/{cliente_id}/propiedades", summary="Eliminar propiedades de 1 Cliente")
def eliminar_propiedades_cliente(cliente_id: str, propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Cliente {{clienteId: $id}}) REMOVE {removes} RETURN c",
        {"id": cliente_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result[0]


# ── DELETE propiedades de múltiples nodos ────────────────────────────────────
@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Clientes")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Cliente) WHERE c.clienteId IN $ids REMOVE {removes} RETURN count(c) AS modificados",
        {"ids": ids},
    )
    return result[0]


# ── DELETE: eliminar 1 nodo ───────────────────────────────────────────────────
@router.delete("/{cliente_id}", summary="Eliminar 1 Cliente")
def eliminar_cliente(cliente_id: str):
    result = run_query(
        "MATCH (c:Cliente {clienteId: $id}) DETACH DELETE c RETURN count(c) AS eliminados",
        {"id": cliente_id},
    )
    return result[0]


# ── DELETE: eliminar múltiples nodos ─────────────────────────────────────────
@router.delete("/bulk/eliminar", summary="Eliminar múltiples Clientes")
def eliminar_clientes_bulk(ids: List[str]):
    result = run_query(
        "MATCH (c:Cliente) WHERE c.clienteId IN $ids DETACH DELETE c RETURN count(c) AS eliminados",
        {"ids": ids},
    )
    return result[0]
