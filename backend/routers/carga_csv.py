"""
Carga de datos desde archivos CSV a Neo4j.
Los CSV se suben como form-data y se procesan fila a fila.
"""
import csv
import io
from fastapi import APIRouter, File, UploadFile, HTTPException
from database import run_query

router = APIRouter(prefix="/csv", tags=["Carga CSV"])


def parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]


# ── Carga de Clientes ─────────────────────────────────────────────────────────
@router.post("/clientes", summary="Cargar Clientes desde CSV")
async def cargar_clientes_csv(file: UploadFile = File(...)):
    """
    Columnas esperadas:
    clienteId, nombre, apellido, email, telefono, fechaNacimiento,
    activo, nivelRiesgo, etiquetasRiesgo (separadas por |), ingresoMensual
    """
    rows = parse_csv(await file.read())
    if not rows:
        raise HTTPException(status_code=400, detail="CSV vacío")
    creados = 0
    errores = []
    for row in rows:
        try:
            etiquetas = [e.strip() for e in row.get("etiquetasRiesgo", "").split("|") if e.strip()]
            query = """
            MERGE (c:Cliente {clienteId: $clienteId})
            ON CREATE SET
                c.nombre          = $nombre,
                c.apellido        = $apellido,
                c.email           = $email,
                c.telefono        = $telefono,
                c.fechaNacimiento = date($fechaNacimiento),
                c.activo          = ($activo = 'true'),
                c.nivelRiesgo     = $nivelRiesgo,
                c.etiquetasRiesgo = $etiquetasRiesgo,
                c.ingresoMensual  = toFloat($ingresoMensual)
            """
            run_query(query, {
                "clienteId":       row["clienteId"],
                "nombre":          row["nombre"],
                "apellido":        row["apellido"],
                "email":           row["email"],
                "telefono":        row.get("telefono", ""),
                "fechaNacimiento": row["fechaNacimiento"],
                "activo":          row.get("activo", "true"),
                "nivelRiesgo":     row.get("nivelRiesgo", "bajo"),
                "etiquetasRiesgo": etiquetas,
                "ingresoMensual":  row.get("ingresoMensual", "0"),
            })
            creados += 1
        except Exception as e:
            errores.append({"fila": row, "error": str(e)})
    return {"creados": creados, "errores": len(errores), "detalleErrores": errores[:5]}


# ── Carga de Cuentas ──────────────────────────────────────────────────────────
@router.post("/cuentas", summary="Cargar Cuentas desde CSV")
async def cargar_cuentas_csv(file: UploadFile = File(...)):
    """
    Columnas: cuentaId, numeroCuenta, tipoCuenta, saldo, fechaApertura,
              moneda, activa, limiteCredito, numeroPrestamos, bancosAsociados (|)
    """
    rows = parse_csv(await file.read())
    creados = 0
    errores = []
    for row in rows:
        try:
            bancos = [b.strip() for b in row.get("bancosAsociados", "").split("|") if b.strip()]
            query = """
            MERGE (c:Cuenta {cuentaId: $cuentaId})
            ON CREATE SET
                c.numeroCuenta    = $numeroCuenta,
                c.tipoCuenta      = $tipoCuenta,
                c.saldo           = toFloat($saldo),
                c.fechaApertura   = date($fechaApertura),
                c.moneda          = $moneda,
                c.activa          = ($activa = 'true'),
                c.limiteCredito   = toFloat($limiteCredito),
                c.numeroPrestamos = toInteger($numeroPrestamos),
                c.bancosAsociados = $bancosAsociados
            """
            run_query(query, {
                "cuentaId":       row["cuentaId"],
                "numeroCuenta":   row["numeroCuenta"],
                "tipoCuenta":     row["tipoCuenta"],
                "saldo":          row.get("saldo", "0"),
                "fechaApertura":  row["fechaApertura"],
                "moneda":         row.get("moneda", "GTQ"),
                "activa":         row.get("activa", "true"),
                "limiteCredito":  row.get("limiteCredito", "0"),
                "numeroPrestamos": row.get("numeroPrestamos", "0"),
                "bancosAsociados": bancos,
            })
            creados += 1
        except Exception as e:
            errores.append({"fila": row, "error": str(e)})
    return {"creados": creados, "errores": len(errores), "detalleErrores": errores[:5]}


# ── Carga de Transacciones ────────────────────────────────────────────────────
@router.post("/transacciones", summary="Cargar Transacciones desde CSV")
async def cargar_transacciones_csv(file: UploadFile = File(...)):
    """
    Columnas: transaccionId, monto, fecha, descripcion, estado,
              esSospechosa, canal, moneda, categoriaGasto, horaLocal
    """
    rows = parse_csv(await file.read())
    creados = 0
    errores = []
    for row in rows:
        try:
            query = """
            MERGE (t:Transaccion {transaccionId: $transaccionId})
            ON CREATE SET
                t.monto          = toFloat($monto),
                t.fecha          = date($fecha),
                t.descripcion    = $descripcion,
                t.estado         = $estado,
                t.esSospechosa   = ($esSospechosa = 'true'),
                t.canal          = $canal,
                t.moneda         = $moneda,
                t.categoriaGasto = $categoriaGasto,
                t.horaLocal      = toInteger($horaLocal)
            """
            run_query(query, {
                "transaccionId": row["transaccionId"],
                "monto":         row["monto"],
                "fecha":         row["fecha"],
                "descripcion":   row.get("descripcion", ""),
                "estado":        row.get("estado", "aprobada"),
                "esSospechosa":  row.get("esSospechosa", "false"),
                "canal":         row.get("canal", "POS"),
                "moneda":        row.get("moneda", "GTQ"),
                "categoriaGasto": row.get("categoriaGasto", "general"),
                "horaLocal":     row.get("horaLocal", "12"),
            })
            creados += 1
        except Exception as e:
            errores.append({"fila": row, "error": str(e)})
    return {"creados": creados, "errores": len(errores), "detalleErrores": errores[:5]}


# ── Carga de Relaciones ───────────────────────────────────────────────────────
@router.post("/relaciones/posee", summary="Cargar relaciones POSEE (Cliente->Cuenta) desde CSV")
async def cargar_relaciones_posee(file: UploadFile = File(...)):
    """
    Columnas: clienteId, cuentaId, fechaAsignacion, esTitular, porcentajePropiedad
    """
    rows = parse_csv(await file.read())
    creados = 0
    errores = []
    for row in rows:
        try:
            query = """
            MATCH (cl:Cliente {clienteId: $clienteId})
            MATCH (cu:Cuenta {cuentaId: $cuentaId})
            MERGE (cl)-[r:POSEE]->(cu)
            ON CREATE SET
                r.fechaAsignacion    = date($fechaAsignacion),
                r.esTitular          = ($esTitular = 'true'),
                r.porcentajePropiedad = toFloat($porcentajePropiedad)
            """
            run_query(query, {
                "clienteId":           row["clienteId"],
                "cuentaId":            row["cuentaId"],
                "fechaAsignacion":     row.get("fechaAsignacion", "2020-01-01"),
                "esTitular":           row.get("esTitular", "true"),
                "porcentajePropiedad": row.get("porcentajePropiedad", "100"),
            })
            creados += 1
        except Exception as e:
            errores.append({"fila": row, "error": str(e)})
    return {"creados": creados, "errores": len(errores), "detalleErrores": errores[:5]}


# ── Carga masiva completa ─────────────────────────────────────────────────────
@router.get("/estado", summary="Contar nodos y relaciones en la BD")
def estado_bd():
    result = run_query("""
    MATCH (n)
    RETURN labels(n)[0] AS label, count(n) AS cantidad
    ORDER BY cantidad DESC
    """)
    rels = run_query("""
    MATCH ()-[r]->()
    RETURN type(r) AS tipo, count(r) AS cantidad
    ORDER BY cantidad DESC
    """)
    total_nodes = run_query("MATCH (n) RETURN count(n) AS total")
    return {
        "totalNodos": total_nodes[0]["total"] if total_nodes else 0,
        "nodosPorLabel": result,
        "relacionesPorTipo": rels,
    }
