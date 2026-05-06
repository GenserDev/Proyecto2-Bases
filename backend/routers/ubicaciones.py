"""
Nodos: Ubicacion
Labels: Ubicacion | Ubicacion:ZonaRiesgo
Propiedades: ubicacionId(String), ciudad(String), pais(String),
             latitud(Float), longitud(Float), zonaRiesgo(Boolean),
             codigoPostal(String), region(String),
             poblacion(Integer), codigoPais(String)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/ubicaciones", tags=["Ubicaciones"])


class UbicacionCreate(BaseModel):
    ubicacionId: str
    ciudad: str
    pais: str
    latitud: float
    longitud: float
    zonaRiesgo: bool = False
    codigoPostal: str
    region: str
    poblacion: int
    codigoPais: str


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Ubicacion (1 label)")
def crear_ubicacion(ubicacion: UbicacionCreate):
    query = """
    CREATE (u:Ubicacion {
        ubicacionId:  $ubicacionId,
        ciudad:       $ciudad,
        pais:         $pais,
        latitud:      $latitud,
        longitud:     $longitud,
        zonaRiesgo:   $zonaRiesgo,
        codigoPostal: $codigoPostal,
        region:       $region,
        poblacion:    $poblacion,
        codigoPais:   $codigoPais
    })
    RETURN u
    """
    result = run_query(query, ubicacion.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear ubicacion")
    return result[0]


@router.post("/multilabel", summary="Crear Ubicacion con 2+ labels")
def crear_ubicacion_multilabel(ubicacion: UbicacionCreate, label_extra: str = "ZonaRiesgo"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (u:Ubicacion:`{label_extra_safe}` {{ubicacionId: $ubicacionId}})
    ON CREATE SET
        u.ciudad       = $ciudad,
        u.pais         = $pais,
        u.latitud      = $latitud,
        u.longitud     = $longitud,
        u.zonaRiesgo   = $zonaRiesgo,
        u.codigoPostal = $codigoPostal,
        u.region       = $region,
        u.poblacion    = $poblacion,
        u.codigoPais   = $codigoPais
    RETURN u
    """
    result = run_query(query, ubicacion.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear ubicacion")
    return result[0]


@router.get("/", summary="Listar Ubicaciones con filtros")
def listar_ubicaciones(
    pais: Optional[str] = None,
    zonaRiesgo: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if pais:
        filtros.append("u.pais = $pais")
        params["pais"] = pais
    if zonaRiesgo is not None:
        filtros.append("u.zonaRiesgo = $zonaRiesgo")
        params["zonaRiesgo"] = zonaRiesgo
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (u:Ubicacion) {where} RETURN u SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Ubicaciones")
def agregaciones_ubicaciones():
    query = """
    MATCH (u:Ubicacion)
    RETURN
        count(u)                           AS totalUbicaciones,
        count(CASE WHEN u.zonaRiesgo THEN 1 END) AS zonasRiesgo,
        collect(DISTINCT u.pais)           AS paises,
        avg(u.poblacion)                   AS poblacionPromedio
    """
    return run_query(query)


@router.get("/{ubicacion_id}", summary="Obtener una Ubicacion por ID")
def obtener_ubicacion(ubicacion_id: str):
    result = run_query(
        "MATCH (u:Ubicacion {ubicacionId: $id}) RETURN u",
        {"id": ubicacion_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return result[0]


@router.put("/{ubicacion_id}", summary="Actualizar propiedades de 1 Ubicacion")
def actualizar_ubicacion(ubicacion_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"u.{k} = ${k}" for k in datos.propiedades])
    params = {"id": ubicacion_id, **datos.propiedades}
    result = run_query(
        f"MATCH (u:Ubicacion {{ubicacionId: $id}}) SET {sets} RETURN u",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Ubicaciones")
def actualizar_ubicaciones_bulk(pais: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"u.{k} = ${k}" for k in datos.propiedades])
    params = {"pais": pais, **datos.propiedades}
    result = run_query(
        f"MATCH (u:Ubicacion {{pais: $pais}}) SET {sets} RETURN count(u) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{ubicacion_id}/propiedades", summary="Agregar propiedades a 1 Ubicacion")
def agregar_propiedades_ubicacion(ubicacion_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"u.{k} = ${k}" for k in datos.propiedades])
    params = {"id": ubicacion_id, **datos.propiedades}
    result = run_query(
        f"MATCH (u:Ubicacion {{ubicacionId: $id}}) SET {sets} RETURN u",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Ubicaciones")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"u.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (u:Ubicacion) WHERE u.ubicacionId IN $ids SET {sets} RETURN count(u) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{ubicacion_id}/propiedades", summary="Eliminar propiedades de 1 Ubicacion")
def eliminar_propiedades_ubicacion(ubicacion_id: str, propiedades: List[str]):
    removes = ", ".join([f"u.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (u:Ubicacion {{ubicacionId: $id}}) REMOVE {removes} RETURN u",
        {"id": ubicacion_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Ubicacion no encontrada")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Ubicaciones")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"u.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (u:Ubicacion) WHERE u.ubicacionId IN $ids REMOVE {removes} RETURN count(u) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{ubicacion_id}", summary="Eliminar 1 Ubicacion")
def eliminar_ubicacion(ubicacion_id: str):
    result = run_query(
        "MATCH (u:Ubicacion {ubicacionId: $id}) DETACH DELETE u RETURN count(u) AS eliminados",
        {"id": ubicacion_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Ubicaciones")
def eliminar_ubicaciones_bulk(ids: List[str]):
    result = run_query(
        "MATCH (u:Ubicacion) WHERE u.ubicacionId IN $ids DETACH DELETE u RETURN count(u) AS eliminados",
        {"ids": ids},
    )
    return result[0]
