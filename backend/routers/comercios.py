"""
Nodos: Comercio
Labels: Comercio | Comercio:ComercioSospechoso
Propiedades: comercioId(String), nombre(String), categoria(String),
             pais(String), calificacion(Float), esConocido(Boolean),
             telefonoContacto(String), horario(List<String>),
             registrado(Date), totalTransacciones(Integer)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/comercios", tags=["Comercios"])


class ComercioCreate(BaseModel):
    comercioId: str
    nombre: str
    categoria: str
    pais: str
    calificacion: float = 5.0
    esConocido: bool = True
    telefonoContacto: str
    horario: List[str] = []
    registrado: str
    totalTransacciones: int = 0


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Comercio (1 label)")
def crear_comercio(comercio: ComercioCreate):
    query = """
    CREATE (c:Comercio {
        comercioId:         $comercioId,
        nombre:             $nombre,
        categoria:          $categoria,
        pais:               $pais,
        calificacion:       $calificacion,
        esConocido:         $esConocido,
        telefonoContacto:   $telefonoContacto,
        horario:            $horario,
        registrado:         date($registrado),
        totalTransacciones: $totalTransacciones
    })
    RETURN c
    """
    result = run_query(query, comercio.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear comercio")
    return result[0]


@router.post("/multilabel", summary="Crear Comercio con 2+ labels")
def crear_comercio_multilabel(comercio: ComercioCreate, label_extra: str = "ComercioSospechoso"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (c:Comercio:`{label_extra_safe}` {{comercioId: $comercioId}})
    ON CREATE SET
        c.nombre             = $nombre,
        c.categoria          = $categoria,
        c.pais               = $pais,
        c.calificacion       = $calificacion,
        c.esConocido         = $esConocido,
        c.telefonoContacto   = $telefonoContacto,
        c.horario            = $horario,
        c.registrado         = date($registrado),
        c.totalTransacciones = $totalTransacciones
    RETURN c
    """
    result = run_query(query, comercio.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear comercio")
    return result[0]


@router.get("/", summary="Listar Comercios con filtros")
def listar_comercios(
    categoria: Optional[str] = None,
    pais: Optional[str] = None,
    esConocido: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if categoria:
        filtros.append("c.categoria = $categoria")
        params["categoria"] = categoria
    if pais:
        filtros.append("c.pais = $pais")
        params["pais"] = pais
    if esConocido is not None:
        filtros.append("c.esConocido = $esConocido")
        params["esConocido"] = esConocido
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (c:Comercio) {where} RETURN c SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Comercios")
def agregaciones_comercios():
    query = """
    MATCH (c:Comercio)
    RETURN
        count(c)                         AS totalComercios,
        avg(c.calificacion)              AS calificacionPromedio,
        collect(DISTINCT c.categoria)    AS categorias,
        sum(c.totalTransacciones)        AS transaccionesTotal
    """
    return run_query(query)


@router.get("/{comercio_id}", summary="Obtener un Comercio por ID")
def obtener_comercio(comercio_id: str):
    result = run_query(
        "MATCH (c:Comercio {comercioId: $id}) RETURN c",
        {"id": comercio_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return result[0]


@router.put("/{comercio_id}", summary="Actualizar propiedades de 1 Comercio")
def actualizar_comercio(comercio_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": comercio_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Comercio {{comercioId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Comercios")
def actualizar_comercios_bulk(pais: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"pais": pais, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Comercio {{pais: $pais}}) SET {sets} RETURN count(c) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{comercio_id}/propiedades", summary="Agregar propiedades a 1 Comercio")
def agregar_propiedades_comercio(comercio_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": comercio_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Comercio {{comercioId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Comercios")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Comercio) WHERE c.comercioId IN $ids SET {sets} RETURN count(c) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{comercio_id}/propiedades", summary="Eliminar propiedades de 1 Comercio")
def eliminar_propiedades_comercio(comercio_id: str, propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Comercio {{comercioId: $id}}) REMOVE {removes} RETURN c",
        {"id": comercio_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Comercio no encontrado")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Comercios")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Comercio) WHERE c.comercioId IN $ids REMOVE {removes} RETURN count(c) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{comercio_id}", summary="Eliminar 1 Comercio")
def eliminar_comercio(comercio_id: str):
    result = run_query(
        "MATCH (c:Comercio {comercioId: $id}) DETACH DELETE c RETURN count(c) AS eliminados",
        {"id": comercio_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Comercios")
def eliminar_comercios_bulk(ids: List[str]):
    result = run_query(
        "MATCH (c:Comercio) WHERE c.comercioId IN $ids DETACH DELETE c RETURN count(c) AS eliminados",
        {"ids": ids},
    )
    return result[0]
