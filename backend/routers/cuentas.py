"""
Nodos: Cuenta
Labels: Cuenta | Cuenta:CuentaSospechosa
Propiedades: cuentaId(String), numeroCuenta(String), tipoCuenta(String),
             saldo(Float), fechaApertura(Date), moneda(String),
             activa(Boolean), limiteCredito(Float), numeroPrestamos(Integer),
             bancosAsociados(List<String>)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from database import run_query

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


class CuentaCreate(BaseModel):
    cuentaId: str
    numeroCuenta: str
    tipoCuenta: str
    saldo: float
    fechaApertura: str
    moneda: str = "GTQ"
    activa: bool = True
    limiteCredito: float = 0.0
    numeroPrestamos: int = 0
    bancosAsociados: List[str] = []


class PropiedadesUpdate(BaseModel):
    propiedades: dict


@router.post("/", summary="Crear Cuenta (1 label)")
def crear_cuenta(cuenta: CuentaCreate):
    query = """
    CREATE (c:Cuenta {
        cuentaId:       $cuentaId,
        numeroCuenta:   $numeroCuenta,
        tipoCuenta:     $tipoCuenta,
        saldo:          $saldo,
        fechaApertura:  date($fechaApertura),
        moneda:         $moneda,
        activa:         $activa,
        limiteCredito:  $limiteCredito,
        numeroPrestamos:$numeroPrestamos,
        bancosAsociados:$bancosAsociados
    })
    RETURN c
    """
    result = run_query(query, cuenta.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear cuenta")
    return result[0]


@router.post("/multilabel", summary="Crear Cuenta con 2+ labels")
def crear_cuenta_multilabel(cuenta: CuentaCreate, label_extra: str = "CuentaSospechosa"):
    label_extra_safe = label_extra.replace("`", "")
    query = f"""
    MERGE (c:Cuenta:`{label_extra_safe}` {{cuentaId: $cuentaId}})
    ON CREATE SET
        c.numeroCuenta    = $numeroCuenta,
        c.tipoCuenta      = $tipoCuenta,
        c.saldo           = $saldo,
        c.fechaApertura   = date($fechaApertura),
        c.moneda          = $moneda,
        c.activa          = $activa,
        c.limiteCredito   = $limiteCredito,
        c.numeroPrestamos = $numeroPrestamos,
        c.bancosAsociados = $bancosAsociados
    RETURN c
    """
    result = run_query(query, cuenta.model_dump())
    if not result:
        raise HTTPException(status_code=500, detail="Error al crear cuenta")
    return result[0]


@router.get("/", summary="Listar Cuentas con filtros")
def listar_cuentas(
    tipoCuenta: Optional[str] = None,
    moneda: Optional[str] = None,
    activa: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    filtros = []
    params: dict = {"limit": limit, "skip": skip}
    if tipoCuenta:
        filtros.append("c.tipoCuenta = $tipoCuenta")
        params["tipoCuenta"] = tipoCuenta
    if moneda:
        filtros.append("c.moneda = $moneda")
        params["moneda"] = moneda
    if activa is not None:
        filtros.append("c.activa = $activa")
        params["activa"] = activa
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    query = f"MATCH (c:Cuenta) {where} RETURN c SKIP $skip LIMIT $limit"
    return run_query(query, params)


@router.get("/agregaciones/resumen", summary="Agregaciones de Cuentas")
def agregaciones_cuentas():
    query = """
    MATCH (c:Cuenta)
    RETURN
        count(c)                     AS totalCuentas,
        avg(c.saldo)                 AS saldoPromedio,
        sum(c.saldo)                 AS saldoTotal,
        max(c.saldo)                 AS saldoMaximo,
        collect(DISTINCT c.moneda)   AS monedas
    """
    return run_query(query)


@router.get("/{cuenta_id}", summary="Obtener una Cuenta por ID")
def obtener_cuenta(cuenta_id: str):
    result = run_query(
        "MATCH (c:Cuenta {cuentaId: $id}) RETURN c",
        {"id": cuenta_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return result[0]


@router.put("/{cuenta_id}", summary="Actualizar propiedades de 1 Cuenta")
def actualizar_cuenta(cuenta_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": cuenta_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cuenta {{cuentaId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return result[0]


@router.put("/bulk/update", summary="Actualizar propiedades de múltiples Cuentas")
def actualizar_cuentas_bulk(moneda: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"moneda": moneda, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cuenta {{moneda: $moneda}}) SET {sets} RETURN count(c) AS actualizados",
        params,
    )
    return result[0]


@router.patch("/{cuenta_id}/propiedades", summary="Agregar propiedades a 1 Cuenta")
def agregar_propiedades_cuenta(cuenta_id: str, datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"id": cuenta_id, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cuenta {{cuentaId: $id}}) SET {sets} RETURN c",
        params,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return result[0]


@router.patch("/bulk/propiedades", summary="Agregar propiedades a múltiples Cuentas")
def agregar_propiedades_bulk(ids: List[str], datos: PropiedadesUpdate):
    sets = ", ".join([f"c.{k} = ${k}" for k in datos.propiedades])
    params = {"ids": ids, **datos.propiedades}
    result = run_query(
        f"MATCH (c:Cuenta) WHERE c.cuentaId IN $ids SET {sets} RETURN count(c) AS modificados",
        params,
    )
    return result[0]


@router.delete("/{cuenta_id}/propiedades", summary="Eliminar propiedades de 1 Cuenta")
def eliminar_propiedades_cuenta(cuenta_id: str, propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Cuenta {{cuentaId: $id}}) REMOVE {removes} RETURN c",
        {"id": cuenta_id},
    )
    if not result:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    return result[0]


@router.delete("/bulk/propiedades", summary="Eliminar propiedades de múltiples Cuentas")
def eliminar_propiedades_bulk(ids: List[str], propiedades: List[str]):
    removes = ", ".join([f"c.{p}" for p in propiedades])
    result = run_query(
        f"MATCH (c:Cuenta) WHERE c.cuentaId IN $ids REMOVE {removes} RETURN count(c) AS modificados",
        {"ids": ids},
    )
    return result[0]


@router.delete("/{cuenta_id}", summary="Eliminar 1 Cuenta")
def eliminar_cuenta(cuenta_id: str):
    result = run_query(
        "MATCH (c:Cuenta {cuentaId: $id}) DETACH DELETE c RETURN count(c) AS eliminados",
        {"id": cuenta_id},
    )
    return result[0]


@router.delete("/bulk/eliminar", summary="Eliminar múltiples Cuentas")
def eliminar_cuentas_bulk(ids: List[str]):
    result = run_query(
        "MATCH (c:Cuenta) WHERE c.cuentaId IN $ids DETACH DELETE c RETURN count(c) AS eliminados",
        {"ids": ids},
    )
    return result[0]
