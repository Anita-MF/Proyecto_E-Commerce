from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.agents.inventario_agent import ejecutar_agente
from backend.app.services.analisis import analizar_inventario, obtener_resumen_por_categoria
from backend.app.services.prediccion import obtener_lista_compras
from backend.app.services.alertas import obtener_alertas

router = APIRouter(prefix="/inventario", tags=["Inventario"])

class DecisionAgente(BaseModel):
    producto_id:        str
    tienda_id:          str
    categoria:          str
    regla:              str
    accion:             str
    justificacion:      str
    unidades_sugeridas: int
    prioridad:          int

class ResumenAgente(BaseModel):
    total_productos:      int
    criticos:             int
    bajos:                int
    normales:             int
    excesos:              int
    total_decisiones:     int
    costo_total_estimado: float

class ItemListaCompras(BaseModel):
    producto_id:             str
    tienda_id:               str
    categoria:               str
    prioridad_compra:        str
    stock_actual:            int
    demanda_ajustada_3_dias: int
    unidades_a_comprar:      int
    costo_estimado:          float

class AlertaItem(BaseModel):
    tipo:        str
    nivel:       str
    producto_id: str
    tienda_id:   str
    categoria:   str
    mensaje:     str

@router.get("/", summary="Estado del agente")
def estado_agente():
    return {
        "estado":  "activo",
        "agente":  "Agente de Optimización de Inventario E-Commerce",
        "version": "1.0.0",
        "endpoints": [
            "/inventario/agente",
            "/inventario/lista-compras",
            "/inventario/alertas",
            "/inventario/analisis",
            "/inventario/resumen-categoria",
            "/inventario/resumen-tienda",
        ]
    }

@router.get("/agente", summary="Ejecutar agente completo")
def ejecutar():
    try:
        return ejecutar_agente()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lista-compras", summary="Lista de compras sugerida")
def lista_compras(
    categoria: str = None,
    prioridad: str = None,
    tienda:    str = None,
    limite:    int = 100,
):
    try:
        df = obtener_lista_compras(
            categoria=categoria or None,
            prioridad=prioridad or None,
        )

        if tienda:
            df = df[df["tienda_id"].str.upper() == tienda.upper()]

        if df.empty:
            raise HTTPException(status_code=404, detail="No se encontraron productos")

        resultado = df[[
            "producto_id", "tienda_id", "categoria", "prioridad_compra",
            "stock_actual", "demanda_ajustada_3_dias",
            "unidades_a_comprar", "costo_estimado"
        ]].head(limite)

        return {
            "total":       len(resultado),
            "costo_total": round(float(resultado["costo_estimado"].sum()), 2),
            "productos":   resultado.to_dict(orient="records"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alertas", summary="Alertas del sistema")
def alertas(
    tipo:   str = None,
    tienda: str = None,
):
    try:
        todas = obtener_alertas()

        if tipo:
            mapa = {
                "vencimiento":   "alertas_vencimiento",
                "stock_critico": "alertas_stock_critico",
                "promocion":     "alertas_promocion",
                "competidor":    "alertas_competidor",
            }
            key = mapa.get(tipo.lower())
            if not key:
                raise HTTPException(status_code=400, detail=f"Tipo inválido. Usar: {list(mapa.keys())}")
            lista = todas[key]
            if tienda:
                lista = [a for a in lista if a.get("tienda_id","").upper() == tienda.upper()]
            return {"tipo": tipo, "total": len(lista), "alertas": lista}

        if tienda:
            todas_filtradas = {}
            for k, v in todas.items():
                todas_filtradas[k] = [a for a in v if a.get("tienda_id","").upper() == tienda.upper()]
            total = sum(len(v) for v in todas_filtradas.values())
            return {"total_alertas": total, **todas_filtradas}

        total = sum(len(v) for v in todas.values())
        return {"total_alertas": total, **todas}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analisis", summary="Análisis completo de inventario")
def analisis(
    categoria: str = None,
    estado:    str = None,
    tienda:    str = None,
):
    try:
        df = analizar_inventario()

        if categoria:
            df = df[df["categoria"].str.lower() == categoria.lower()]
        if estado:
            df = df[df["clasificacion"].str.upper() == estado.upper()]
        if tienda:
            df = df[df["tienda_id"].str.upper() == tienda.upper()]

        if df.empty:
            raise HTTPException(status_code=404, detail="No se encontraron productos")

        cols = ["producto_id", "tienda_id", "categoria", "clasificacion",
                "dias_stock_restante", "stock_critico_score",
                "score_compuesto", "tipo_anomalia", "unidades_sugeridas_compra"]

        return {
            "total":     len(df),
            "productos": df[cols].to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumen-categoria", summary="Resumen de estado por categoría")
def resumen_categoria():
    try:
        return {"resumen": obtener_resumen_por_categoria()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumen-tienda", summary="Resumen de estado por tienda")
def resumen_tienda():
    try:
        df = analizar_inventario()
        resumen = df.groupby("tienda_id")["clasificacion"].value_counts().to_dict()
        return {"resumen": resumen}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))