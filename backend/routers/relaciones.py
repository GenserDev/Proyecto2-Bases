"""
Tipos de relaciones (12 tipos, cada una con 3+ propiedades):
  POSEE             Cliente -> Cuenta
  TIENE_TARJETA     Cliente -> Tarjeta
  REALIZO           Cliente -> Transaccion
  ORIGEN            Transaccion -> Cuenta
  DESTINO           Transaccion -> Cuenta
  EN_COMERCIO       Transaccion -> Comercio
  USO_DISPOSITIVO   Transaccion -> Dispositivo
  EN_UBICACION      Transaccion -> Ubicacion
  COMPARTE_DISPOSITIVO Cliente -> Dispositivo
  ASOCIADA_A        Tarjeta -> Cuenta
  VIVE_EN           Cliente -> Ubicacion
  SIMILAR_A         Transaccion -> Transaccion
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from database import run_query

router = APIRouter(prefix="/relaciones", tags=["Relaciones"])

TIPOS_VALIDOS = {
    "POSEE", "TIENE_TARJETA", "REALIZO", "ORIGEN", "DESTINO",
    "EN_COMERCIO", "USO_DISPOSITIVO", "EN_UBICACION",
    "COMPARTE_DISPOSITIVO", "ASOCIADA_A", "VIVE_EN", "SIMILAR_A",
}

ID_PROP_MAP = {
    "Cliente":     "clienteId",
    "Cuenta":      "cuentaId",
    "Tarjeta":     "tarjetaId",
    "Transaccion": "transaccionId",
    "Comercio":    "comercioId",
    "Dispositivo": "dispositivoId",
    "Ubicacion":   "ubicacionId",
}


class RelacionCreate(BaseModel):
    tipoRelacion: str
    labelOrigen: str
    idOrigen: str
    labelDestino: str
    idDestino: str
    propiedades: dict = {}


class PropiedadesUpdate(BaseModel):
    propiedades: dict


def _validate_tipo(tipo: str):
    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Tipo de relacion no valido: {tipo}")


# ── Crear relacion con propiedades ────────────────────────────────────────────
@router.post("/", summary="Crear relacion entre 2 nodos con propiedades")
def crear_relacion(rel: RelacionCreate):
    _validate_tipo(rel.tipoRelacion)
    prop_origen = ID_PROP_MAP.get(rel.labelOrigen, "id")
    prop_destino = ID_PROP_MAP.get(rel.labelDestino, "id")

    set_clause = ""
    if rel.propiedades:
        sets = ", ".join([f"r.{k} = $p_{k}" for k in rel.propiedades])
        set_clause = f"SET {sets}"

    params = {
        "idOrigen": rel.idOrigen,
        "idDestino": rel.idDestino,
        **{f"p_{k}": v for k, v in rel.propiedades.items()},
    }

    query = f"""
    MATCH (a:{rel.labelOrigen} {{{prop_origen}: $idOrigen}})
    MATCH (b:{rel.labelDestino} {{{prop_destino}: $idDestino}})
    CREATE (a)-[r:{rel.tipoRelacion}]->(b)
    {set_clause}
    RETURN type(r) AS tipo, properties(r) AS propiedades
    """
    result = run_query(query, params)
    if not result:
        raise HTTPException(status_code=404, detail="Nodos no encontrados")
    return result[0]


# ── Agregar propiedades a 1 relacion ─────────────────────────────────────────
@router.patch("/propiedades", summary="Agregar propiedades a 1 relacion")
def agregar_propiedades_relacion(
    tipoRelacion: str,
    labelOrigen: str,
    idOrigen: str,
    labelDestino: str,
    idDestino: str,
    datos: PropiedadesUpdate,
):
    _validate_tipo(tipoRelacion)
    prop_origen = ID_PROP_MAP.get(labelOrigen, "id")
    prop_destino = ID_PROP_MAP.get(labelDestino, "id")
    sets = ", ".join([f"r.{k} = ${k}" for k in datos.propiedades])
    params = {"idOrigen": idOrigen, "idDestino": idDestino, **datos.propiedades}
    query = f"""
    MATCH (a:{labelOrigen} {{{prop_origen}: $idOrigen}})-[r:{tipoRelacion}]->(b:{labelDestino} {{{prop_destino}: $idDestino}})
    SET {sets}
    RETURN type(r) AS tipo, properties(r) AS propiedades
    """
    result = run_query(query, params)
    if not result:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    return result[0]


# ── Agregar propiedades a múltiples relaciones ───────────────────────────────
@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples relaciones")
def agregar_propiedades_relaciones_bulk(tipoRelacion: str, datos: PropiedadesUpdate):
    _validate_tipo(tipoRelacion)
    sets = ", ".join([f"r.{k} = ${k}" for k in datos.propiedades])
    params = {**datos.propiedades}
    query = f"""
    MATCH ()-[r:{tipoRelacion}]->()
    SET {sets}
    RETURN count(r) AS modificadas
    """
    result = run_query(query, params)
    return result[0]


# ── Actualizar propiedades de 1 relacion ─────────────────────────────────────
@router.put("/propiedades", summary="Actualizar propiedades de 1 relacion")
def actualizar_propiedades_relacion(
    tipoRelacion: str,
    labelOrigen: str,
    idOrigen: str,
    labelDestino: str,
    idDestino: str,
    datos: PropiedadesUpdate,
):
    _validate_tipo(tipoRelacion)
    prop_origen = ID_PROP_MAP.get(labelOrigen, "id")
    prop_destino = ID_PROP_MAP.get(labelDestino, "id")
    sets = ", ".join([f"r.{k} = ${k}" for k in datos.propiedades])
    params = {"idOrigen": idOrigen, "idDestino": idDestino, **datos.propiedades}
    query = f"""
    MATCH (a:{labelOrigen} {{{prop_origen}: $idOrigen}})-[r:{tipoRelacion}]->(b:{labelDestino} {{{prop_destino}: $idDestino}})
    SET {sets}
    RETURN type(r) AS tipo, properties(r) AS propiedades
    """
    result = run_query(query, params)
    if not result:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    return result[0]


# ── Actualizar propiedades de múltiples relaciones ───────────────────────────
@router.put("/bulk/propiedades", summary="Actualizar propiedades de múltiples relaciones")
def actualizar_propiedades_relaciones_bulk(tipoRelacion: str, datos: PropiedadesUpdate):
    _validate_tipo(tipoRelacion)
    sets = ", ".join([f"r.{k} = ${k}" for k in datos.propiedades])
    params = {**datos.propiedades}
    query = f"""
    MATCH ()-[r:{tipoRelacion}]->()
    SET {sets}
    RETURN count(r) AS actualizadas
    """
    result = run_query(query, params)
    return result[0]


# ── Eliminar propiedades de 1 relacion ───────────────────────────────────────
@router.delete("/propiedades", summary="Eliminar propiedades de 1 relacion")
def eliminar_propiedades_relacion(
    tipoRelacion: str,
    labelOrigen: str,
    idOrigen: str,
    labelDestino: str,
    idDestino: str,
    propiedades: List[str],
):
    _validate_tipo(tipoRelacion)
    prop_origen = ID_PROP_MAP.get(labelOrigen, "id")
    prop_destino = ID_PROP_MAP.get(labelDestino, "id")
    removes = ", ".join([f"r.{p}" for p in propiedades])
    params = {"idOrigen": idOrigen, "idDestino": idDestino}
    query = f"""
    MATCH (a:{labelOrigen} {{{prop_origen}: $idOrigen}})-[r:{tipoRelacion}]->(b:{labelDestino} {{{prop_destino}: $idDestino}})
    REMOVE {removes}
    RETURN type(r) AS tipo, properties(r) AS propiedades
    """
    result = run_query(query, params)
    if not result:
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    return result[0]


# ── Eliminar propiedades de múltiples relaciones ──────────────────────────────
@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples relaciones")
def eliminar_propiedades_relaciones_bulk(tipoRelacion: str, propiedades: List[str]):
    _validate_tipo(tipoRelacion)
    removes = ", ".join([f"r.{p}" for p in propiedades])
    query = f"""
    MATCH ()-[r:{tipoRelacion}]->()
    REMOVE {removes}
    RETURN count(r) AS modificadas
    """
    result = run_query(query, {})
    return result[0]


# ── Eliminar 1 relacion ───────────────────────────────────────────────────────
@router.delete("/", summary="Eliminar 1 relacion")
def eliminar_relacion(
    tipoRelacion: str,
    labelOrigen: str,
    idOrigen: str,
    labelDestino: str,
    idDestino: str,
):
    _validate_tipo(tipoRelacion)
    prop_origen = ID_PROP_MAP.get(labelOrigen, "id")
    prop_destino = ID_PROP_MAP.get(labelDestino, "id")
    params = {"idOrigen": idOrigen, "idDestino": idDestino}
    query = f"""
    MATCH (a:{labelOrigen} {{{prop_origen}: $idOrigen}})-[r:{tipoRelacion}]->(b:{labelDestino} {{{prop_destino}: $idDestino}})
    DELETE r
    RETURN count(r) AS eliminadas
    """
    result = run_query(query, params)
    return result[0]


# ── Eliminar múltiples relaciones ─────────────────────────────────────────────
@router.delete("/bulk/eliminar", summary="Eliminar múltiples relaciones del mismo tipo")
def eliminar_relaciones_bulk(tipoRelacion: str):
    _validate_tipo(tipoRelacion)
    query = f"""
    MATCH ()-[r:{tipoRelacion}]->()
    WITH r LIMIT 1000
    DELETE r
    RETURN count(r) AS eliminadas
    """
    result = run_query(query, {})
    return result[0]


# ── Listar relaciones ─────────────────────────────────────────────────────────
@router.get("/", summary="Listar relaciones por tipo")
def listar_relaciones(tipoRelacion: str, limit: int = 50):
    _validate_tipo(tipoRelacion)
    query = f"""
    MATCH (a)-[r:{tipoRelacion}]->(b)
    RETURN
        labels(a)[0] AS labelOrigen,
        labels(b)[0] AS labelDestino,
        properties(r) AS propiedades
    LIMIT $limit
    """
    return run_query(query, {"limit": limit})
