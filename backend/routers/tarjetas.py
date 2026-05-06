"""
Nodos: Tarjeta
Labels: Tarjeta | Tarjeta:TarjetaBloqueada
Propiedades: tarjetaId(String), ultimosCuatroDigitos(String), tipoTarjeta(String),
             limiteCredito(Float), fechaVencimiento(Date), bloqueada(Boolean),
             intentosFallidos(Integer), redesContactadas(List<String>),
             fechaEmision(Date), banco(String)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/tarjetas", tags=["Tarjetas"])


class TarjetaCreate(BaseModel):
    tarjetaId: str
    ultimosCuatroDigitos: str
    tipoTarjeta: str
    limiteCredito: float
    fechaVencimiento: str
    bloqueada: bool = False
    intentosFallidos: int = 0
    redesContactadas: List[str] = []
    fechaEmision: str
    banco: str


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Tarjeta (1 label)")
def crear_tarjeta(tarjeta: TarjetaCreate):
    query = """
    CREATE (t:Tarjeta {
        tarjetaId:            $tarjetaId,
        ultimosCuatroDigitos: $ultimosCuatroDigitos,
        tipoTarjeta:          $tipoTarjeta,
        limiteCredito:        $limiteCredito,
        fechaVencimiento:     date($fechaVencimiento),
        bloqueada:            $bloqueada,
        intentosFallidos:     $intentosFallidos,
        redesContactadas:     $redesContactadas,
        fechaEmision:         date($fechaEmision),
        banco:                $banco
    })
    RETURN t
    """
    result = run_query(query, tarjeta.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear tarjeta")
    return result[0]


@router.post("/multilabel", summary="Crear Tarjeta con 2+ labels")
def crear_tarjeta_multilabel(tarjeta: TarjetaCreate, label_extra: str = "TarjetaBloqueada"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (t:Tarjeta:`{label_extra_safe}` {{tarjetaId: $tarjetaId}})
    ON CREATE SET
        t.ultimosCuatroDigitos = $ultimosCuatroDigitos,
        t.tipoTarjeta          = $tipoTarjeta,
        t.limiteCredito        = $limiteCredito,
        t.fechaVencimiento     = date($fechaVencimiento),
        t.bloqueada            = $bloqueada,
        t.intentosFallidos     = $intentosFallidos,
        t.redesContactadas     = $redesContactadas,
        t.fechaEmision         = date($fechaEmision),
        t.banco                = $banco
    RETURN t
    """
    result = run_query(query, tarjeta.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear tarjeta")
    return result[0]


@router.get("/", summary="Listar Tarjetas con filtros")
def listar_tarjetas(
    tipoTarjeta: Optional[str] = None,
    bloqueada: Optional[bool] = None,
    banco: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if tipoTarjeta:
        filtros.append("t.tipoTarjeta = $tipoTarjeta")
        params["tipoTarjeta"] = tipoTarjeta
    if bloqueada is not None:
        filtros.append("t.bloqueada = $bloqueada")
        params["bloqueada"] = bloqueada
    if banco:
        filtros.append("t.banco = $banco")
        params["banco"] = banco
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (t:Tarjeta) {where} RETURN t SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Tarjetas")
def agregaciones_tarjetas():
    query = """
    MATCH (t:Tarjeta)
    RETURN
        count(t)                          AS totalTarjetas,
        avg(t.limiteCredito)              AS limiteCreditoPromedio,
        count(CASE WHEN t.bloqueada THEN 1 END) AS tarjetasBloqueadas,
        collect(DISTINCT t.tipoTarjeta)   AS tipos
    """
    return run_query(query)


@router.get("/{tarjeta_id}", summary="Obtener una Tarjeta por ID")
def obtener_tarjeta(tarjeta_id: str):
    result = run_query(
        "MATCH (t:Tarjeta {tarjetaId: $id}) RETURN t",
        {"id": tarjeta_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
    return result[0]


@router.put("/{tarjeta_id}", summary="Actualizar propiedades de 1 Tarjeta")
def actualizar_tarjeta(tarjeta_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"id": tarjeta_id, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Tarjeta {{tarjetaId: $id}}) SET {sets} RETURN t",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Tarjetas")
def actualizar_tarjetas_bulk(banco: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"banco": banco, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Tarjeta {{banco: $banco}}) SET {sets} RETURN count(t) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{tarjeta_id}/propiedades", summary="Agregar propiedades a 1 Tarjeta")
def agregar_propiedades_tarjeta(tarjeta_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"id": tarjeta_id, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Tarjeta {{tarjetaId: $id}}) SET {sets} RETURN t",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Tarjetas")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"t.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (t:Tarjeta) WHERE t.tarjetaId IN $ids SET {sets} RETURN count(t) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{tarjeta_id}/propiedades", summary="Eliminar propiedades de 1 Tarjeta")
def eliminar_propiedades_tarjeta(tarjeta_id: str, propiedades: List[str]):
    removes = ", ".join([f"t.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (t:Tarjeta {{tarjetaId: $id}}) REMOVE {removes} RETURN t",
        {"id": tarjeta_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Tarjetas")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"t.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (t:Tarjeta) WHERE t.tarjetaId IN $ids REMOVE {removes} RETURN count(t) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{tarjeta_id}", summary="Eliminar 1 Tarjeta")
def eliminar_tarjeta(tarjeta_id: str):
    result = run_query(
        "MATCH (t:Tarjeta {tarjetaId: $id}) DETACH DELETE t RETURN count(t) AS eliminados",
        {"id": tarjeta_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Tarjetas")
def eliminar_tarjetas_bulk(ids: List[str]):
    result = run_query(
        "MATCH (t:Tarjeta) WHERE t.tarjetaId IN $ids DETACH DELETE t RETURN count(t) AS eliminados",
        {"ids": ids},
    )
    return result[0]
