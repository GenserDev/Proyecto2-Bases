# Sistema de Detección de Fraude Bancario — Neo4j

## Pasos para ejecutar el proyecto

### 1. Configurar credenciales de Neo4j
Copiar `.env.example` a `.env` en la carpeta `backend/` y llenar:
```
NEO4J_URI=neo4j+s://0baab995.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password_aqui
```

### 2. Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 3. Generar datos (5000+ nodos) y cargarlos
```bash
cd data
pip install faker  # si no está instalado
python generate_data.py   # genera los CSV en data/csv/
python load_csv.py        # carga todo a Neo4j AuraDB
```

### 4. Levantar el backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Abrir el frontend
Abrir en el navegador: http://localhost:8000
O abrir directamente: frontend/index.html

### 6. Ver la documentación de la API
http://localhost:8000/docs

---

## Modelo de datos

### Labels de nodos (7)
| Label             | ID único         | Propiedades clave                                                    |
|-------------------|------------------|----------------------------------------------------------------------|
| Cliente           | clienteId        | nombre, email, fechaNacimiento(Date), activo(Bool), etiquetasRiesgo(List), ingresoMensual(Float) |
| Cuenta            | cuentaId         | numeroCuenta, tipoCuenta, saldo(Float), fechaApertura(Date), activa(Bool), bancosAsociados(List) |
| Tarjeta           | tarjetaId        | tipoTarjeta, limiteCredito(Float), fechaVencimiento(Date), bloqueada(Bool), redesContactadas(List) |
| Transaccion       | transaccionId    | monto(Float), fecha(Date), esSospechosa(Bool), canal, horaLocal(Int)  |
| Comercio          | comercioId       | nombre, categoria, calificacion(Float), esConocido(Bool), horario(List), registrado(Date) |
| Dispositivo       | dispositivoId    | tipo, ip, ultimoUso(Date), confiable(Bool), usuariosAsociados(Int), ubicacionesRegistradas(List) |
| Ubicacion         | ubicacionId      | ciudad, pais, latitud(Float), longitud(Float), zonaRiesgo(Bool), poblacion(Int) |

### Tipos de relaciones (12)
| Relación              | Origen       | Destino      | Propiedades                                          |
|-----------------------|--------------|--------------|------------------------------------------------------|
| POSEE                 | Cliente      | Cuenta       | fechaAsignacion(Date), esTitular(Bool), porcentajePropiedad(Float) |
| TIENE_TARJETA         | Cliente      | Tarjeta      | fechaAsignacion(Date), esTitular(Bool), limitePersonal(Float) |
| REALIZO               | Cliente      | Transaccion  | fecha(Date), canal(String), ipOrigen(String)         |
| ORIGEN                | Transaccion  | Cuenta       | monto(Float), fecha(Date), autorizado(Bool)          |
| DESTINO               | Transaccion  | Cuenta       | monto(Float), fecha(Date), bancoDestino(String)      |
| EN_COMERCIO           | Transaccion  | Comercio     | fecha(Date), metodoPago(String), montoTotal(Float)   |
| USO_DISPOSITIVO       | Transaccion  | Dispositivo  | fecha(Date), ipUsada(String), exitosa(Bool)          |
| EN_UBICACION          | Transaccion  | Ubicacion    | fecha(Date), distanciaUltimaTransaccion(Float), alertaGeo(Bool) |
| COMPARTE_DISPOSITIVO  | Cliente      | Dispositivo  | primerUso(Date), frecuencia(Int), esPropio(Bool)     |
| ASOCIADA_A            | Tarjeta      | Cuenta       | fechaAsociacion(Date), esPrincipal(Bool), limiteCompartido(Float) |
| VIVE_EN               | Cliente      | Ubicacion    | fechaRegistro(Date), esDomicilio(Bool), verificado(Bool) |
| SIMILAR_A             | Transaccion  | Transaccion  | similitudScore(Float), tipoPatron(String), fechaDeteccion(Date) |

### Nodos generados (~6,700 en total)
- Clientes: 1,000
- Cuentas: 1,500
- Tarjetas: 800
- Transacciones: 2,500
- Comercios: 300
- Dispositivos: 400
- Ubicaciones: 200

---

## Consultas Cypher (6 — 2 por integrante)

| # | Persona | Nombre                        | Descripción                                           |
|---|---------|-------------------------------|-------------------------------------------------------|
| 1 | P1      | Velocidad Geográfica          | Clientes con TX en 2+ países distintos                |
| 2 | P1      | Anillos de Fraude             | Dispositivos compartidos entre múltiples clientes     |
| 3 | P2      | Cuentas Alto Riesgo           | Cuentas con más transacciones sospechosas             |
| 4 | P2      | Comercios Sospechosos         | Ranking de comercios por fraude recibido              |
| 5 | P3      | Resumen Mensual Fraude        | Agregación temporal de transacciones sospechosas      |
| 6 | P3      | Rutas de Fraude               | Cadenas de clientes conectados por TX y dispositivos  |
