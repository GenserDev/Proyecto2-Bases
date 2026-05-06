"""
Nodos: Dispositivo
Labels: Dispositivo | Dispositivo:DispositivoSospechoso
Propiedades: dispositivoId(String), tipo(String), sistemaOperativo(String),
             ip(String), ultimoUso(Date), confiable(Boolean),
             marcaModelo(String), versionApp(String),
             usuariosAsociados(Integer), ubicacionesRegistradas(List<String>)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos"])


class DispositivoCreate(BaseModel):
    dispositivoId: str
    tipo: str
    sistemaOperativo: str
    ip: str
    ultimoUso: str
    confiable: bool = True
    marcaModelo: str
    versionApp: str
    usuariosAsociados: int = 1
    ubicacionesRegistradas: List[str] = []


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Dispositivo (1 label)")
def crear_dispositivo(dispositivo: DispositivoCreate):
    query = """
    CREATE (d:Dispositivo {
        dispositivoId:          $dispositivoId,
        tipo:                   $tipo,
        sistemaOperativo:       $sistemaOperativo,
        ip:                     $ip,
        ultimoUso:              date($ultimoUso),
        confiable:              $confiable,
        marcaModelo:            $marcaModelo,
        versionApp:             $versionApp,
        usuariosAsociados:      $usuariosAsociados,
        ubicacionesRegistradas: $ubicacionesRegistradas
    })
    RETURN d
    """
    result = run_query(query, dispositivo.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear dispositivo")
    return result[0]


@router.post("/multilabel", summary="Crear Dispositivo con 2+ labels")
def crear_dispositivo_multilabel(dispositivo: DispositivoCreate, label_extra: str = "DispositivoSospechoso"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (d:Dispositivo:`{label_extra_safe}` {{dispositivoId: $dispositivoId}})
    ON CREATE SET
        d.tipo                   = $tipo,
        d.sistemaOperativo       = $sistemaOperativo,
        d.ip                     = $ip,
        d.ultimoUso              = date($ultimoUso),
        d.confiable              = $confiable,
        d.marcaModelo            = $marcaModelo,
        d.versionApp             = $versionApp,
        d.usuariosAsociados      = $usuariosAsociados,
        d.ubicacionesRegistradas = $ubicacionesRegistradas
    RETURN d
    """
    result = run_query(query, dispositivo.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear dispositivo")
    return result[0]


@router.get("/", summary="Listar Dispositivos con filtros")
def listar_dispositivos(
    tipo: Optional[str] = None,
    confiable: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if tipo:
        filtros.append("d.tipo = $tipo")
        params["tipo"] = tipo
    if confiable is not None:
        filtros.append("d.confiable = $confiable")
        params["confiable"] = confiable
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (d:Dispositivo) {where} RETURN d SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Dispositivos")
def agregaciones_dispositivos():
    query = """
    MATCH (d:Dispositivo)
    RETURN
        count(d)                              AS totalDispositivos,
        avg(d.usuariosAsociados)              AS usuariosPromedio,
        count(CASE WHEN NOT d.confiable THEN 1 END) AS dispositivosSospechosos,
        collect(DISTINCT d.tipo)              AS tipos
    """
    return run_query(query)


@router.get("/{dispositivo_id}", summary="Obtener un Dispositivo por ID")
def obtener_dispositivo(dispositivo_id: str):
    result = run_query(
        "MATCH (d:Dispositivo {dispositivoId: $id}) RETURN d",
        {"id": dispositivo_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return result[0]


@router.put("/{dispositivo_id}", summary="Actualizar propiedades de 1 Dispositivo")
def actualizar_dispositivo(dispositivo_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"d.{k} = ${k}" for k in datos.propiedades])
    params = {"id": dispositivo_id, **datos.propiedades}
    result = run_query(
        f"MATCH (d:Dispositivo {{dispositivoId: $id}}) SET {sets} RETURN d",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Dispositivos")
def actualizar_dispositivos_bulk(tipo: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"d.{k} = ${k}" for k in datos.propiedades])
    params = {"tipo": tipo, **datos.propiedades}
    result = run_query(
        f"MATCH (d:Dispositivo {{tipo: $tipo}}) SET {sets} RETURN count(d) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{dispositivo_id}/propiedades", summary="Agregar propiedades a 1 Dispositivo")
def agregar_propiedades_dispositivo(dispositivo_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"d.{k} = ${k}" for k in datos.propiedades])
    params = {"id": dispositivo_id, **datos.propiedades}
    result = run_query(
        f"MATCH (d:Dispositivo {{dispositivoId: $id}}) SET {sets} RETURN d",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Dispositivos")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"d.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (d:Dispositivo) WHERE d.dispositivoId IN $ids SET {sets} RETURN count(d) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{dispositivo_id}/propiedades", summary="Eliminar propiedades de 1 Dispositivo")
def eliminar_propiedades_dispositivo(dispositivo_id: str, propiedades: List[str]):
    removes = ", ".join([f"d.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (d:Dispositivo {{dispositivoId: $id}}) REMOVE {removes} RETURN d",
        {"id": dispositivo_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Dispositivos")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"d.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (d:Dispositivo) WHERE d.dispositivoId IN $ids REMOVE {removes} RETURN count(d) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{dispositivo_id}", summary="Eliminar 1 Dispositivo")
def eliminar_dispositivo(dispositivo_id: str):
    result = run_query(
        "MATCH (d:Dispositivo {dispositivoId: $id}) DETACH DELETE d RETURN count(d) AS eliminados",
        {"id": dispositivo_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Dispositivos")
def eliminar_dispositivos_bulk(ids: List[str]):
    result = run_query(
        "MATCH (d:Dispositivo) WHERE d.dispositivoId IN $ids DETACH DELETE d RETURN count(d) AS eliminados",
        {"ids": ids},
    )
    return result[0]
