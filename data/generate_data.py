"""
Genera CSVs con datos sintéticos para el sistema de fraude bancario.
Total de nodos generados: ~6,700 (supera el mínimo de 5,000)

Ejecutar: python generate_data.py
"""
import csv
import random
import uuid
from datetime import date, timedelta
from faker import Faker

fake = Faker("es_MX")
random.seed(42)

OUT = "csv"

N_CLIENTES    = 1000
N_CUENTAS     = 1500
N_TARJETAS    = 800
N_TRANSACCIONES = 2500
N_COMERCIOS   = 300
N_DISPOSITIVOS = 400
N_UBICACIONES  = 200


def fecha_aleatoria(inicio: str, fin: str) -> str:
    d1 = date.fromisoformat(inicio)
    d2 = date.fromisoformat(fin)
    delta = (d2 - d1).days
    return (d1 + timedelta(days=random.randint(0, delta))).isoformat()


def write_csv(filename: str, fieldnames: list, rows: list):
    path = f"{OUT}/{filename}"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Generado: {path} ({len(rows)} filas)")


# ── Ubicaciones ───────────────────────────────────────────────────────────────
print("Generando Ubicaciones...")
paises_latam = [
    ("Guatemala", "GT", "Centroamérica"),
    ("México", "MX", "Norteamérica"),
    ("Colombia", "CO", "Sudamérica"),
    ("Estados Unidos", "US", "Norteamérica"),
    ("Panamá", "PA", "Centroamérica"),
    ("Honduras", "HN", "Centroamérica"),
    ("El Salvador", "SV", "Centroamérica"),
    ("Costa Rica", "CR", "Centroamérica"),
    ("Venezuela", "VE", "Sudamérica"),
    ("Nigeria", "NG", "África"),
]
ciudades_por_pais = {
    "Guatemala":      ["Ciudad de Guatemala", "Quetzaltenango", "Escuintla", "Mixco", "Villa Nueva"],
    "México":         ["Ciudad de México", "Guadalajara", "Monterrey", "Cancún", "Tijuana"],
    "Colombia":       ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
    "Estados Unidos": ["Miami", "New York", "Los Angeles", "Houston", "Chicago"],
    "Panamá":         ["Ciudad de Panamá", "Colón", "David"],
    "Honduras":       ["Tegucigalpa", "San Pedro Sula", "La Ceiba"],
    "El Salvador":    ["San Salvador", "Santa Ana", "San Miguel"],
    "Costa Rica":     ["San José", "Alajuela", "Cartago"],
    "Venezuela":      ["Caracas", "Maracaibo", "Valencia"],
    "Nigeria":        ["Lagos", "Abuja", "Kano"],
}

ubicaciones = []
ubicacion_ids = []
for i in range(N_UBICACIONES):
    uid = f"UB-{i+1:04d}"
    pais, codigo, region = random.choice(paises_latam)
    ciudad = random.choice(ciudades_por_pais[pais])
    zona_riesgo = pais in ["Nigeria", "Venezuela"] or random.random() < 0.1
    ubicaciones.append({
        "ubicacionId":  uid,
        "ciudad":       ciudad,
        "pais":         pais,
        "latitud":      round(random.uniform(-55, 35), 6),
        "longitud":     round(random.uniform(-120, 30), 6),
        "zonaRiesgo":   str(zona_riesgo).lower(),
        "codigoPostal": fake.postcode(),
        "region":       region,
        "poblacion":    random.randint(50_000, 10_000_000),
        "codigoPais":   codigo,
    })
    ubicacion_ids.append(uid)

write_csv("ubicaciones.csv", list(ubicaciones[0].keys()), ubicaciones)

# ── Dispositivos ──────────────────────────────────────────────────────────────
print("Generando Dispositivos...")
tipos_disp = ["movil", "desktop", "tablet"]
sistemas_op = ["Android 13", "iOS 16", "Windows 11", "macOS 14", "Linux"]
marcas = ["Samsung Galaxy S23", "iPhone 14", "Xiaomi Redmi", "HP EliteBook", "Dell XPS", "iPad Pro"]

dispositivos = []
dispositivo_ids = []
for i in range(N_DISPOSITIVOS):
    did = f"DV-{i+1:04d}"
    confiable = random.random() > 0.15
    dispositivos.append({
        "dispositivoId":         did,
        "tipo":                  random.choice(tipos_disp),
        "sistemaOperativo":      random.choice(sistemas_op),
        "ip":                    fake.ipv4(),
        "ultimoUso":             fecha_aleatoria("2023-01-01", "2024-12-31"),
        "confiable":             str(confiable).lower(),
        "marcaModelo":           random.choice(marcas),
        "versionApp":            f"2.{random.randint(0,9)}.{random.randint(0,15)}",
        "usuariosAsociados":     random.randint(1, 5 if not confiable else 2),
        "ubicacionesRegistradas": "|".join(random.sample(
            [u["ciudad"] for u in ubicaciones[:50]], k=random.randint(1, 3)
        )),
    })
    dispositivo_ids.append(did)

write_csv("dispositivos.csv", list(dispositivos[0].keys()), dispositivos)

# ── Comercios ─────────────────────────────────────────────────────────────────
print("Generando Comercios...")
categorias_com = [
    "supermercado", "farmacia", "restaurante", "gasolinera", "tienda_online",
    "hotel", "aerolinea", "casino", "joyeria", "transferencia",
]
horarios_posibles = ["L-V 8-18", "L-S 9-21", "24/7", "L-V 9-17", "L-D 10-22"]

comercios = []
comercio_ids = []
for i in range(N_COMERCIOS):
    cid = f"CO-{i+1:04d}"
    cat = random.choice(categorias_com)
    es_conocido = cat not in ["casino", "joyeria"] or random.random() > 0.3
    pais, _, _ = random.choice(paises_latam)
    comercios.append({
        "comercioId":        cid,
        "nombre":            fake.company()[:50],
        "categoria":         cat,
        "pais":              pais,
        "calificacion":      round(random.uniform(1.0, 5.0), 1),
        "esConocido":        str(es_conocido).lower(),
        "telefonoContacto":  fake.phone_number()[:20],
        "horario":           "|".join(random.sample(horarios_posibles, k=random.randint(1, 2))),
        "registrado":        fecha_aleatoria("2010-01-01", "2023-01-01"),
        "totalTransacciones": random.randint(0, 50000),
    })
    comercio_ids.append(cid)

write_csv("comercios.csv", list(comercios[0].keys()), comercios)

# ── Clientes ──────────────────────────────────────────────────────────────────
print("Generando Clientes...")
niveles_riesgo = ["bajo", "medio", "alto", "critico"]
etiquetas_posibles = ["viajero_frecuente", "alto_volumen", "nuevo_usuario",
                      "historial_fraude", "cliente_vip", "empresa"]

clientes = []
cliente_ids = []
for i in range(N_CLIENTES):
    cid = f"CL-{i+1:04d}"
    nivel = random.choices(niveles_riesgo, weights=[60, 25, 10, 5])[0]
    n_etiquetas = random.randint(0, 3)
    etiquetas = random.sample(etiquetas_posibles, k=n_etiquetas)
    clientes.append({
        "clienteId":       cid,
        "nombre":          fake.first_name(),
        "apellido":        fake.last_name(),
        "email":           fake.email(),
        "telefono":        fake.phone_number()[:15],
        "fechaNacimiento": fecha_aleatoria("1950-01-01", "2003-12-31"),
        "activo":          str(random.random() > 0.05).lower(),
        "nivelRiesgo":     nivel,
        "etiquetasRiesgo": "|".join(etiquetas),
        "ingresoMensual":  round(random.uniform(2000, 100000), 2),
    })
    cliente_ids.append(cid)

write_csv("clientes.csv", list(clientes[0].keys()), clientes)

# ── Cuentas ───────────────────────────────────────────────────────────────────
print("Generando Cuentas...")
tipos_cuenta = ["ahorro", "corriente", "monetaria", "credito"]
monedas = ["GTQ", "USD", "EUR", "MXN"]
bancos_posibles = ["BAC", "Banrural", "G&T Continental", "Industrial", "HSBC",
                   "Citibank", "Banistmo", "Davivienda"]

cuentas = []
cuenta_ids = []
for i in range(N_CUENTAS):
    cid = f"CU-{i+1:04d}"
    cuentas.append({
        "cuentaId":       cid,
        "numeroCuenta":   str(random.randint(10_000_000, 99_999_999)),
        "tipoCuenta":     random.choice(tipos_cuenta),
        "saldo":          round(random.uniform(-500, 500_000), 2),
        "fechaApertura":  fecha_aleatoria("2000-01-01", "2024-01-01"),
        "moneda":         random.choices(monedas, weights=[60, 25, 5, 10])[0],
        "activa":         str(random.random() > 0.08).lower(),
        "limiteCredito":  round(random.uniform(0, 100_000), 2),
        "numeroPrestamos": random.randint(0, 5),
        "bancosAsociados": "|".join(random.sample(bancos_posibles, k=random.randint(1, 3))),
    })
    cuenta_ids.append(cid)

write_csv("cuentas.csv", list(cuentas[0].keys()), cuentas)

# ── Tarjetas ──────────────────────────────────────────────────────────────────
print("Generando Tarjetas...")
tipos_tarjeta = ["credito", "debito", "prepago"]

tarjetas = []
tarjeta_ids = []
for i in range(N_TARJETAS):
    tid = f"TJ-{i+1:04d}"
    bloqueada = random.random() < 0.12
    redes = ["Visa", "Mastercard", "Amex"]
    tarjetas.append({
        "tarjetaId":            tid,
        "ultimosCuatroDigitos": str(random.randint(1000, 9999)),
        "tipoTarjeta":          random.choice(tipos_tarjeta),
        "limiteCredito":        round(random.uniform(1000, 50000), 2),
        "fechaVencimiento":     fecha_aleatoria("2024-01-01", "2029-12-31"),
        "bloqueada":            str(bloqueada).lower(),
        "intentosFallidos":     random.randint(3, 10) if bloqueada else random.randint(0, 2),
        "redesContactadas":     "|".join(random.sample(redes, k=random.randint(1, 2))),
        "fechaEmision":         fecha_aleatoria("2018-01-01", "2024-01-01"),
        "banco":                random.choice(bancos_posibles),
    })
    tarjeta_ids.append(tid)

write_csv("tarjetas.csv", list(tarjetas[0].keys()), tarjetas)

# ── Transacciones ─────────────────────────────────────────────────────────────
print("Generando Transacciones...")
estados = ["aprobada", "rechazada", "pendiente", "revertida"]
canales = ["POS", "ATM", "online", "app_movil", "transferencia"]
categorias_gasto = [
    "alimentacion", "transporte", "entretenimiento", "salud",
    "educacion", "ropa", "viajes", "servicios", "retiro_efectivo", "transferencia",
]

transacciones = []
transaccion_ids = []
for i in range(N_TRANSACCIONES):
    tid = f"TX-{i+1:05d}"
    estado = random.choices(estados, weights=[75, 12, 8, 5])[0]
    canal = random.choice(canales)
    hora = random.randint(0, 23)
    monto = round(random.uniform(10, 50_000), 2)
    # esSospechosa lo calcula el motor de detección automática después de cargar
    transacciones.append({
        "transaccionId": tid,
        "monto":         monto,
        "fecha":         fecha_aleatoria("2023-01-01", "2024-12-31"),
        "descripcion":   fake.sentence(nb_words=4)[:100],
        "estado":        estado,
        "esSospechosa":  "false",
        "canal":         canal,
        "moneda":        random.choices(["GTQ", "USD"], weights=[70, 30])[0],
        "categoriaGasto": random.choice(categorias_gasto),
        "horaLocal":     hora,
    })
    transaccion_ids.append(tid)

write_csv("transacciones.csv", list(transacciones[0].keys()), transacciones)

# ── Relaciones ────────────────────────────────────────────────────────────────
print("Generando Relaciones...")

# POSEE (Cliente -> Cuenta): cada cliente tiene 1-2 cuentas
posee_rels = []
cuenta_owner = {}
for i, cliente_id in enumerate(cliente_ids):
    n_cuentas = random.randint(1, 2)
    start = (i * N_CUENTAS // N_CLIENTES) % N_CUENTAS
    for j in range(n_cuentas):
        cid = cuenta_ids[(start + j) % N_CUENTAS]
        cuenta_owner[cid] = cliente_id
        posee_rels.append({
            "clienteId":           cliente_id,
            "cuentaId":            cid,
            "fechaAsignacion":     fecha_aleatoria("2015-01-01", "2024-01-01"),
            "esTitular":           str(j == 0).lower(),
            "porcentajePropiedad": "100" if j == 0 else str(random.randint(25, 75)),
        })

write_csv("rel_posee.csv", list(posee_rels[0].keys()), posee_rels)

# TIENE_TARJETA (Cliente -> Tarjeta)
tiene_tarjeta_rels = []
for i, tarjeta_id in enumerate(tarjeta_ids):
    cliente_id = cliente_ids[i % N_CLIENTES]
    tiene_tarjeta_rels.append({
        "clienteId":    cliente_id,
        "tarjetaId":    tarjeta_id,
        "fechaAsignacion": fecha_aleatoria("2018-01-01", "2024-01-01"),
        "esTitular":    "true",
        "limitePersonal": round(random.uniform(1000, 50000), 2),
    })

write_csv("rel_tiene_tarjeta.csv", list(tiene_tarjeta_rels[0].keys()), tiene_tarjeta_rels)

# REALIZO (Cliente -> Transaccion) + ORIGEN (Transaccion -> Cuenta)
realizo_rels = []
origen_rels = []
destino_rels = []
en_comercio_rels = []
uso_dispositivo_rels = []
en_ubicacion_rels = []

for i, tx_id in enumerate(transaccion_ids):
    cliente_id = cliente_ids[i % N_CLIENTES]
    cuenta_origen = cuenta_ids[i % N_CUENTAS]
    cuenta_destino = cuenta_ids[(i + random.randint(1, 50)) % N_CUENTAS]
    comercio_id = comercio_ids[i % N_COMERCIOS]
    dispositivo_id = dispositivo_ids[i % N_DISPOSITIVOS]
    ubicacion_id = ubicacion_ids[i % N_UBICACIONES]
    fecha = transacciones[i]["fecha"]

    realizo_rels.append({
        "clienteId":     cliente_id,
        "transaccionId": tx_id,
        "fecha":         fecha,
        "canal":         transacciones[i]["canal"],
        "ipOrigen":      fake.ipv4(),
    })
    origen_rels.append({
        "transaccionId": tx_id,
        "cuentaId":      cuenta_origen,
        "monto":         transacciones[i]["monto"],
        "fecha":         fecha,
        "autorizado":    str(transacciones[i]["estado"] == "aprobada").lower(),
    })
    if random.random() > 0.4:
        destino_rels.append({
            "transaccionId": tx_id,
            "cuentaId":      cuenta_destino,
            "monto":         transacciones[i]["monto"],
            "fecha":         fecha,
            "bancoDestino":  random.choice(bancos_posibles),
        })
    en_comercio_rels.append({
        "transaccionId": tx_id,
        "comercioId":    comercio_id,
        "fecha":         fecha,
        "metodoPago":    transacciones[i]["canal"],
        "montoTotal":    transacciones[i]["monto"],
    })
    uso_dispositivo_rels.append({
        "transaccionId": tx_id,
        "dispositivoId": dispositivo_id,
        "fecha":         fecha,
        "ipUsada":       fake.ipv4(),
        "exitosa":       str(transacciones[i]["estado"] == "aprobada").lower(),
    })
    en_ubicacion_rels.append({
        "transaccionId":               tx_id,
        "ubicacionId":                 ubicacion_id,
        "fecha":                       fecha,
        "distanciaUltimaTransaccion":  round(random.uniform(0, 5000), 2),
        "alertaGeo":                   "false",
    })

write_csv("rel_realizo.csv", list(realizo_rels[0].keys()), realizo_rels)
write_csv("rel_origen.csv", list(origen_rels[0].keys()), origen_rels)
write_csv("rel_destino.csv", list(destino_rels[0].keys()), destino_rels)
write_csv("rel_en_comercio.csv", list(en_comercio_rels[0].keys()), en_comercio_rels)
write_csv("rel_uso_dispositivo.csv", list(uso_dispositivo_rels[0].keys()), uso_dispositivo_rels)
write_csv("rel_en_ubicacion.csv", list(en_ubicacion_rels[0].keys()), en_ubicacion_rels)

# COMPARTE_DISPOSITIVO (Cliente -> Dispositivo)
comparte_disp_rels = []
for i, disp_id in enumerate(dispositivo_ids):
    c1 = cliente_ids[i % N_CLIENTES]
    c2 = cliente_ids[(i + 7) % N_CLIENTES]
    for cl in [c1, c2] if c1 != c2 else [c1]:
        comparte_disp_rels.append({
            "clienteId":    cl,
            "dispositivoId": disp_id,
            "primerUso":    fecha_aleatoria("2022-01-01", "2024-01-01"),
            "frecuencia":   random.randint(1, 200),
            "esPropio":     str(cl == c1).lower(),
        })

write_csv("rel_comparte_dispositivo.csv", list(comparte_disp_rels[0].keys()), comparte_disp_rels)

# ASOCIADA_A (Tarjeta -> Cuenta)
asociada_a_rels = []
for i, tarjeta_id in enumerate(tarjeta_ids):
    cuenta_id = cuenta_ids[i % N_CUENTAS]
    asociada_a_rels.append({
        "tarjetaId":       tarjeta_id,
        "cuentaId":        cuenta_id,
        "fechaAsociacion": fecha_aleatoria("2018-01-01", "2024-01-01"),
        "esPrincipal":     "true",
        "limiteCompartido": round(random.uniform(1000, 50000), 2),
    })

write_csv("rel_asociada_a.csv", list(asociada_a_rels[0].keys()), asociada_a_rels)

# VIVE_EN (Cliente -> Ubicacion)
vive_en_rels = []
for i, cliente_id in enumerate(cliente_ids):
    ubicacion_id = ubicacion_ids[i % N_UBICACIONES]
    vive_en_rels.append({
        "clienteId":    cliente_id,
        "ubicacionId":  ubicacion_id,
        "fechaRegistro": fecha_aleatoria("2015-01-01", "2024-01-01"),
        "esDomicilio":  "true",
        "verificado":   str(random.random() > 0.2).lower(),
    })

write_csv("rel_vive_en.csv", list(vive_en_rels[0].keys()), vive_en_rels)

# SIMILAR_A (Transaccion -> Transaccion): pares sospechosos
similar_a_rels = []
# SIMILAR_A usa una muestra aleatoria (el motor de detección decide después cuáles son realmente sospechosas)
sospechosas_ids = [t["transaccionId"] for t in transacciones if t["monto"] > 15_000 or t["horaLocal"] <= 4]
for i in range(min(300, len(sospechosas_ids) - 1)):
    t1 = sospechosas_ids[i]
    t2 = sospechosas_ids[(i + random.randint(1, 5)) % len(sospechosas_ids)]
    if t1 != t2:
        similar_a_rels.append({
            "transaccionId1":  t1,
            "transaccionId2":  t2,
            "similitudScore":  round(random.uniform(0.7, 1.0), 3),
            "tipoPatron":      random.choice(["monto_similar", "mismo_comercio", "mismo_dispositivo"]),
            "fechaDeteccion":  fecha_aleatoria("2024-01-01", "2024-12-31"),
        })

write_csv("rel_similar_a.csv", list(similar_a_rels[0].keys()), similar_a_rels)

# ── Resumen ────────────────────────────────────────────────────────────────────
print("\n=== RESUMEN DE DATOS GENERADOS ===")
total_nodos = N_CLIENTES + N_CUENTAS + N_TARJETAS + N_TRANSACCIONES + N_COMERCIOS + N_DISPOSITIVOS + N_UBICACIONES
print(f"  Clientes:      {N_CLIENTES}")
print(f"  Cuentas:       {N_CUENTAS}")
print(f"  Tarjetas:      {N_TARJETAS}")
print(f"  Transacciones: {N_TRANSACCIONES}")
print(f"  Comercios:     {N_COMERCIOS}")
print(f"  Dispositivos:  {N_DISPOSITIVOS}")
print(f"  Ubicaciones:   {N_UBICACIONES}")
print(f"  TOTAL NODOS:   {total_nodos} ✓ (mínimo: 5,000)")
print(f"\n  Relaciones generadas:")
print(f"  POSEE:               {len(posee_rels)}")
print(f"  TIENE_TARJETA:       {len(tiene_tarjeta_rels)}")
print(f"  REALIZO:             {len(realizo_rels)}")
print(f"  ORIGEN:              {len(origen_rels)}")
print(f"  DESTINO:             {len(destino_rels)}")
print(f"  EN_COMERCIO:         {len(en_comercio_rels)}")
print(f"  USO_DISPOSITIVO:     {len(uso_dispositivo_rels)}")
print(f"  EN_UBICACION:        {len(en_ubicacion_rels)}")
print(f"  COMPARTE_DISPOSITIVO:{len(comparte_disp_rels)}")
print(f"  ASOCIADA_A:          {len(asociada_a_rels)}")
print(f"  VIVE_EN:             {len(vive_en_rels)}")
print(f"  SIMILAR_A:           {len(similar_a_rels)}")
