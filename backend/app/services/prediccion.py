import pandas as pd
import numpy as np
from backend.app.data.loader import cargar_datos

def predecir_compras() -> pd.DataFrame:
    df = cargar_datos()
    df = _predecir_demanda_proxima(df)
    df = _ajustar_por_contexto(df)
    df = _generar_lista_compras(df)
    return df

def _predecir_demanda_proxima(df: pd.DataFrame) -> pd.DataFrame:
    # Demanda real a 3 días (horizonte real del negocio de alta rotación)
    df["demanda_3_dias"] = (df["ritmo_venta_diario"] * 3).round(0).astype(int)

    # Demanda a 30 días solo para referencia en el dashboard
    df["demanda_30_dias"] = (df["ritmo_venta_diario"] * 30).round(0).astype(int)

    return df

def _ajustar_por_contexto(df: pd.DataFrame) -> pd.DataFrame:
    mapa_temporada = {
        "High":   1.30,
        "Winter": 1.20,
        "Summer": 1.10,
        "Spring": 1.00,
        "Autumn": 0.90,
        "Low":    0.80,
    }
    df["factor_temporada"]  = df["temporada"].map(mapa_temporada).fillna(1.0)
    df["factor_promocion"]  = df["promocion"].map({1: 1.40, 0: 1.0})
    df["factor_competidor"] = np.where(
        df["precio_competidor"] < df["precio"] * 0.9, 0.85, 1.0
    )

    # Demanda ajustada a 3 días con todos los factores
    df["demanda_ajustada_3_dias"] = (
        df["demanda_3_dias"]
        * df["factor_temporada"]
        * df["factor_promocion"]
        * df["factor_competidor"]
    ).round(0).astype(int)

    # Demanda ajustada a 30 días para mostrar en dashboard
    df["demanda_ajustada_30_dias"] = (
        df["demanda_30_dias"]
        * df["factor_temporada"]
        * df["factor_promocion"]
        * df["factor_competidor"]
    ).round(0).astype(int)

    return df

def _generar_lista_compras(df: pd.DataFrame) -> pd.DataFrame:
    # Comprar exactamente lo que falta para cubrir 3 días ajustados
    df["unidades_a_comprar"] = (
        df["demanda_ajustada_3_dias"] - df["stock_actual"]
    ).clip(lower=0).round(0).astype(int)

    # Prioridad según cobertura actual en días
    cobertura = df["stock_actual"] / df["ritmo_venta_diario"].replace(0, np.nan)

    condiciones = [
        cobertura < 1.0,
        cobertura < 2.0,
        cobertura < 4.0,
    ]
    df["prioridad_compra"] = np.select(
        condiciones, ["ALTA", "MEDIA", "BAJA"], default="SIN_COMPRA"
    )
    df["costo_estimado"] = (df["unidades_a_comprar"] * df["precio"]).round(2)
    return df

def obtener_lista_compras(categoria: str = None, prioridad: str = None) -> pd.DataFrame:
    df = predecir_compras()
    df = df[df["unidades_a_comprar"] > 0]
    if categoria:
        df = df[df["categoria"].str.lower() == categoria.lower()]
    if prioridad:
        df = df[df["prioridad_compra"].str.upper() == prioridad.upper()]
    return df.sort_values("prioridad_compra").reset_index(drop=True)


if __name__ == "__main__":
    lista = obtener_lista_compras()
    print(f"Productos que necesitan reposición: {len(lista)}")
    print(f"\n=== Lista de compras sugerida ===")
    print(lista[["producto_id", "tienda_id", "categoria", "prioridad_compra",
                 "stock_actual", "demanda_ajustada_3_dias",
                 "unidades_a_comprar", "costo_estimado"]].to_string())
    print(f"\n=== Costo total estimado ===")
    print(f"  ${lista['costo_estimado'].sum():,.2f}")