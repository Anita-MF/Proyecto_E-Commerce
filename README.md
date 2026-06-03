# Sistema de Optimización de Inventario E-Commerce

**Manual de Creación**

> Guía técnica completa de construcción

| Stack Tecnológico |  |  |  |
|---|---|---|---|
| **Python 3.13** lenguaje base | **FastAPI** framework API | **Pandas** procesamiento | **HTML/JS** frontend |

**Autores**: Mariana López · Ana Fernández  
**Institución**: Politécnico Malvinas Argentinas · Desarrollo de Sistemas IA  
**Año**: 2026

---

## 1. Introducción y alcance

Este manual describe el proceso completo de construcción del **Sistema de Optimización de Inventario E-Commerce**: desde la preparación del entorno hasta la ejecución del servidor. Está dirigido a desarrolladores que necesiten replicar, modificar o extender el sistema.

El sistema implementa un agente inteligente con arquitectura **Percepción → Razonamiento → Actuación**, expuesto a través de una **API REST con FastAPI** y un **dashboard visual en HTML/JavaScript**.

### 1.1 Stack tecnológico

| Componente | Tecnología | Función |
|---|---|---|
| **Backend** | Python 3.13 + FastAPI | Servidor API REST con endpoints documentados |
| **Datos** | Pandas + NumPy | Carga, limpieza y cálculo de métricas del CSV |
| **Agente** | Python (lógica propia) | Reglas SI-ENTONCES para toma de decisiones |
| **Validación** | Pydantic | Validación de modelos de entrada/salida en la API |
| **Servidor ASGI** | Uvicorn | Servidor de aplicaciones para FastAPI |
| **Frontend** | HTML + Chart.js + JS | Dashboard visual interactivo sin frameworks |
| **Dataset** | CSV (73.100 filas) | Retail Store Inventory 2022-2024 |

---

## 2. Estructura del proyecto

El proyecto está organizado en módulos separados por responsabilidad:

```
Proyecto E-Commerce/
├── backend/
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       ├── main.py                    ← punto de entrada FastAPI
│       ├── agents/
│       │   └── inventario_agent.py    ← agente inteligente
│       ├── core/
│       │   └── config.py              ← configuración global
│       ├── data/
│       │   └── loader.py              ← carga y procesamiento CSV
│       ├── routers/
│       │   └── inventario.py          ← endpoints de la API
│       └── services/
│           ├── analisis.py            ← clasificación de inventario
│           ├── alertas.py             ← generación de alertas
│           └── prediccion.py          ← lista de compras sugerida
├── data/
│   └── retail_store_inventory.csv
└── frontend/
    └── index.html                     ← dashboard visual
```

### 2.1 Descripción de cada módulo

- **main.py**: Punto de entrada de la aplicación. Configura FastAPI, registra el router de inventario, habilita CORS para el frontend y sirve el index.html en la ruta raíz.

- **config.py**: Configuración centralizada del sistema: nombre de la app, versión y descripción. Usa BaseSettings de Pydantic para facilitar la extensión con variables de entorno.

- **loader.py**: Carga el CSV, renombra columnas, limpia datos, y calcula todas las métricas derivadas (ritmo de venta, días de stock, score compuesto, clasificación, unidades sugeridas). Es la base de datos del sistema.

- **analisis.py**: Aplica clasificación CRÍTICO/BAJO/NORMAL/EXCESO, calcula el score compuesto de urgencia y detecta anomalías de demanda por desviación estándar.

- **alertas.py**: Genera 4 tipos de alertas: stock crítico (con métricas enriquecidas), vencimiento próximo (solo Groceries), promoción sin stock y competidor más barato.

- **prediccion.py**: Genera la lista de compras sugerida con prioridad de compra calculada según clasificación y factores de temporada/promoción.

- **inventario_agent.py**: Agente inteligente con estructura Percepción → Razonamiento → Actuación. Aplica 4 reglas SI-ENTONCES y genera decisiones priorizadas con justificación en lenguaje natural.

- **inventario.py (router)**: Define todos los endpoints GET de la API con validación Pydantic, manejo de errores y parámetros de filtro opcionales.

---

## 3. Instalación y configuración

### 3.1 Prerrequisitos

- Python 3.10 o superior (recomendado 3.13)
- pip (gestor de paquetes de Python)
- Navegador web moderno (Chrome, Firefox, Edge)
- Terminal PowerShell (Windows) o bash (Linux/Mac)

### 3.2 Pasos de instalación

1. **Clonar o descargar** el repositorio del proyecto

2. **Abrir la terminal** en la carpeta raíz del proyecto (donde está la carpeta `backend/`)

3. **Crear el entorno virtual**:
   ```bash
   python -m venv venv
   ```

4. **Activar el entorno virtual**:
   
   *En Windows (PowerShell)*:
   ```bash
   venv\Scripts\activate
   ```
   
   *En Linux / Mac*:
   ```bash
   source venv/bin/activate
   ```

5. **Instalar las dependencias**:
   ```bash
   pip install pandas fastapi uvicorn numpy pydantic pydantic-settings
   ```

6. **Verificar que el archivo CSV esté en la carpeta correcta**:
   ```
   data/retail_store_inventory.csv
   ```

7. **Iniciar el servidor**:
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```

8. **Acceder al sistema**:
   - Dashboard: http://localhost:8000
   - Documentación API: http://localhost:8000/docs

> **⚠️ Importante**: El comando debe ejecutarse siempre desde la carpeta raíz del proyecto (Proyecto E-Commerce/), no desde dentro de backend/. El prefijo `python -m` es necesario para que Python resuelva correctamente los imports del paquete backend.

---

## 4. Capa de datos — loader.py

El loader es el núcleo del sistema. Todo parte de aquí. Carga el CSV histórico y lo transforma en un snapshot actual de 100 registros (20 productos × 5 sucursales).

### 4.1 Pipeline de procesamiento

| # | Función | Qué hace |
|---|---|---|
| **1** | `_renombrar_columnas()` | Mapea los nombres del CSV (inglés) a nombres en español más descriptivos |
| **2** | `_limpiar_datos()` | Elimina nulos, filtra ventas = 0, normaliza strings, imputa medianas |
| **3** | `_agregar_metricas()` | Agrupa por producto+sucursal (groupby+last) y calcula todas las métricas derivadas |

### 4.2 Métricas calculadas

**ritmo_venta_diario**  
Fórmula: promedio histórico de unidades_vendidas por producto+sucursal  
Uso: Base para calcular días de stock y unidades sugeridas

**dias_stock_restante**  
Fórmula: stock_actual ÷ ritmo_venta_diario  
Uso: Determina la clasificación y urgencia del producto

**score_compuesto**  
Fórmula: `(1/dias_stock × 50) + (brecha_forecast × 30) + (promocion × 20)`  
Uso: Indicador de urgencia 0-100 para ordenamiento

**unidades_sugeridas_compra**  
Fórmula: `(ritmo × 3 × factor_temp × factor_promo) - stock_actual`  
Uso: Base para la lista de compras y las decisiones del agente

**clasificacion**  
Fórmula: CRÍTICO (<1d) / BAJO (<2d) / NORMAL (<4d) / EXCESO (≥4d)  
Uso: Segmentación para filtros y alertas

**fecha_vencimiento**  
Fórmula: Generada aleatoriamente 1-10 días para productos Groceries  
Uso: Alertas de vencimiento próximo

### 4.3 Decisión clave de diseño

El CSV contiene 73.100 filas históricas (2022-2024). Para obtener el estado actual del inventario se usa:

```python
df.groupby(['producto_id', 'tienda_id']).agg(..., promocion=('promocion', 'last')).reset_index()
```

El uso de `last()` en vez de `max()` para el campo promocion fue crítico: `max()` tomaba el valor histórico máximo (casi siempre 1), generando falsas alertas de promoción. `last()` toma el estado del día más reciente del dataset.

---

## 5. Agente Inteligente — inventario_agent.py

El agente implementa el ciclo clásico de un agente inteligente: percibe el entorno, razona aplicando reglas y actúa generando un reporte de decisiones.

### 5.1 Estructura del agente

**percibir()**  
Carga todos los datos del entorno llamando a los servicios correspondientes y almacena el estado interno del agente.
```python
df_analisis   = analizar_inventario()
df_prediccion = obtener_lista_compras()
alertas       = obtener_alertas()
```

**razonar()**  
Itera sobre todos los productos y aplica las 4 reglas SI-ENTONCES. Devuelve la lista de decisiones generadas.

**actuar()**  
Integra percepción y razonamiento, ordena las decisiones por prioridad y calcula el costo total estimado de reposición.

### 5.2 Las 4 reglas de decisión

| Pri. | Regla | Condición | Efecto sobre unidades |
|---|---|---|---|
| **1** | STOCK_CRÍTICO_URGENTE | dias_stock < 1.0 | unidades_sugeridas sin modificar |
| **2** | STOCK_BAJO_CON_PROMOCION | dias_stock < 2.0 AND promocion = 1 | unidades_sugeridas × 1.4 (+40%) |
| **3** | STOCK_BAJO_TEMPORADA_ALTA | dias_stock < 2.0 AND temporada IN [High, Winter] | unidades_sugeridas × 1.2 (+20%) |
| **4** | STOCK_BAJO | dias_stock < 2.0 (caso base) | unidades_sugeridas sin modificar |

Las reglas son excluyentes: el agente aplica la primera que se cumple para cada producto. Un producto con menos de 1 día de stock nunca llega a evaluarse contra la regla 2 o 3.

---

## 6. API REST — routers/inventario.py

### 6.1 Configuración de FastAPI

El servidor se configura en main.py con CORS habilitado para permitir el acceso desde el frontend en el mismo host:

```python
app = FastAPI(title=settings.app_name, version=settings.version)
app.add_middleware(CORSMiddleware, allow_origins=['*'], ...)
app.include_router(inventario.router)
```

### 6.2 Modelos Pydantic

Cada endpoint tiene su modelo de respuesta definido con Pydantic para validación automática:

- **DecisionAgente**: producto_id, tienda_id, categoria, regla, accion, justificacion, unidades_sugeridas, prioridad

- **ResumenAgente**: total_productos, criticos, bajos, normales, excesos, total_decisiones, costo_total_estimado

- **ItemListaCompras**: producto_id, tienda_id, categoria, prioridad_compra, stock_actual, demanda_ajustada_3_dias, unidades_a_comprar, costo_estimado

- **AlertaItem**: tipo, nivel, producto_id, tienda_id, categoria, mensaje

### 6.3 Endpoints y parámetros

Todos los endpoints son GET. Los parámetros son opcionales y se pasan como query strings:

**GET /inventario/agente**  
Sin parámetros. Ejecuta el ciclo completo del agente.

**GET /inventario/lista-compras**  
Parámetros: `?categoria=Toys&prioridad=ALTA&tienda=S004&limite=50`

**GET /inventario/alertas**  
Parámetros: `?tipo=stock_critico&tienda=S003`  
Tipos válidos: `vencimiento | stock_critico | promocion | competidor`

**GET /inventario/analisis**  
Parámetros: `?categoria=Groceries&estado=CRÍTICO&tienda=S001`  
Estados válidos: `CRÍTICO | BAJO | NORMAL | EXCESO`

**GET /inventario/resumen-categoria**

**GET /inventario/resumen-tienda**

---

## 7. Frontend — index.html

El dashboard es un único archivo HTML que consume la API mediante `fetch()`. No requiere instalación adicional ni frameworks — solo un navegador moderno.

### 7.1 Librerías externas utilizadas

- **Chart.js 4.4.0** (CDN): gráficos de barras y donut
- **Google Fonts**: Fraunces (serif) + DM Sans (sans-serif)

Ambas se cargan desde CDN, sin instalación local.

### 7.2 Estructura del código JS

**cargarTodo()**  
Llama en paralelo a `cargarAgente()`, `cargarCompras()`, `cargarAlertas()` y `cargarDecisiones()`. Se ejecuta al cargar la página.

**cargarAgente()**  
Consume `/inventario/agente` y actualiza las métricas del resumen y el hero.

**cargarCompras()**  
Consume `/inventario/lista-compras` y renderiza las tarjetas de sucursal, filtros de categoría y gráfico de costos.

**cargarAlertas()**  
Consume `/inventario/alertas` y almacena los datos en `alertasData` para filtrado posterior.

**cargarDecisiones()**  
Consume `/inventario/agente` y cuenta las decisiones por tipo de regla para las tarjetas resumen.

**renderChartVentas()**  
Dibuja el gráfico de barras agrupadas de ventas por categoría. Usa `todosProductos` (demanda_ajustada_3_dias / 3).

**renderChartCosto()**  
Dibuja el gráfico de barras de costo de reposición por sucursal. Se actualiza al seleccionar una sucursal.

**renderChartTopUrgentes(suc)**  
Dibuja el gráfico horizontal de top 8 productos más urgentes de una sucursal (por score_compuesto).

**renderChartStockVsCompra(suc)**  
Dibuja stock disponible vs. necesidad 3 días por categoría al seleccionar una sucursal.

**filtrarAlerta(tipo, suc, cat)**  
Filtra el detalle de alertas por tipo, sucursal y categoría simultáneamente.

**filtrarDecision(regla, el)**  
Muestra la tabla de decisiones del tipo de regla seleccionado.

### 7.3 Conexión con el backend

La URL base de la API se define al inicio del script:

```javascript
const API = 'http://localhost:8000';
```

Para despliegues en producción, cambiar esta constante a la URL del servidor real.

---

## 8. Dificultades encontradas y soluciones

| Problema | Causa | Solución aplicada |
|---|---|---|
| Servidor no iniciaba con `uvicorn backend.main:app` | main.py está en backend/app/, no en backend/ | Usar `python -m uvicorn backend.app.main:app --reload` desde la raíz |
| 78 alertas de promoción (infladas) | `promocion=('promocion','max')` tomaba el máximo histórico | Cambiar a `last()` para tomar el valor del día más reciente |
| Gráfico de ventas vacío al inicio | `renderChartVentas()` se llamaba antes de cargar los datos | Llamar `renderChartVentas()` desde `cargarCompras()` después de cargar `todosProductos` |
| Justificaciones con decimales en decisiones | El agente usaba directamente `dias_stock_restante` en el mensaje | Traducir en el frontend: `floor()` para días completos y texto descriptivo |
| Botones Alta/Media/Baja quedaban verdes al deseleccionar | Heredaban el estilo `.btn-f.active` del CSS global | Crear clase `.btn-pri` independiente con estado `.sel` propio |

---

## 9. Posibles extensiones futuras

### 9.1 Machine Learning real

Las reglas fijas del agente podrían reemplazarse por un modelo de predicción de demanda. Opciones sugeridas:

- Regresión lineal con scikit-learn para predecir ventas futuras por producto
- LSTM (Long Short-Term Memory) para series temporales de ventas
- XGBoost para clasificación de urgencia con múltiples features

### 9.2 Actualización dinámica de datos

Agregar un endpoint POST `/inventario/cargar-datos` que permita subir un nuevo CSV sin reiniciar el servidor:

```python
@router.post('/cargar-datos')
async def cargar_nuevo_csv(file: UploadFile = File(...)):
    # guardar el archivo y recargar loader
```

### 9.3 Despliegue en producción

- Dockerizar con Dockerfile y docker-compose para facilitar el despliegue
- Desplegar en Railway o Render con acceso desde cualquier sucursal
- Usar variables de entorno para la ruta del CSV y configuración del servidor

### 9.4 Integración con sistemas ERP

El agente podría conectarse directamente con sistemas de gestión empresarial para:

- Recibir actualizaciones de stock en tiempo real vía webhook
- Generar órdenes de compra automáticas al detectar stock crítico
- Sincronizar precios con datos de competidores en tiempo real

---

**Politécnico Malvinas Argentinas · 2026**  
**Autores**: Mariana López · Ana Fernández