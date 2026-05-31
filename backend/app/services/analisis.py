import pandas as pd
import numpy as np
from backend.app.data.loader import cargar_datos

def analizar_inventario() -> pd.DataFrame:
    df = cargar_datos()
    df = _clasificar_stock(df)
    df = _calcular_score_compuesto(df)
    df = _detectar_anomalias(df)
    return df

def _clasificar_stock(df: pd.DataFrame) -> pd.DataFrame:
    # Umbrales reales: negocio de alta rotación, stock promedio = 2 días
    condiciones = [
        df["dias_stock_restante"] < 1.0,
        df["dias_stock_restante"] < 2.0,
        df["dias_stock_restante"] < 4.0,
        df["dias_stock_restante"] >= 4.0,
    ]
    etiquetas = ["CRÍTICO", "BAJO", "NORMAL", "EXCESO"]
    df["clasificacion"] = np.select(condiciones, etiquetas, default="NORMAL")
    return df

def _calcular_score_compuesto(df: pd.DataFrame) -> pd.DataFrame:
    # Factor 1: urgencia por días de stock (peso 50%)
    score_stock = (
        (1 / df["dias_stock_restante"].replace(0, np.nan)).clip(0, 1) * 50
    ).fillna(50)

    # Factor 2: diferencia entre forecast y stock actual (peso 30%)
    diferencia_forecast = (
        (df["demanda_forecast"] - df["stock_actual"]) /
        df["demanda_forecast"].replace(0, np.nan)
    ).clip(0, 1) * 30

    # Factor 3: promoción activa sube urgencia (peso 20%)
    bonus_promocion = df["promocion"].map({1: 20, 0: 0})

    df["score_compuesto"] = (
        score_stock +
        diferencia_forecast.fillna(0) +
        bonus_promocion
    ).round(1)

    return df

def _detectar_anomalias(df: pd.DataFrame) -> pd.DataFrame:
    # Detectar tiendas con ventas muy por encima del promedio general
    media  = df["ritmo_venta_diario"].mean()
    desvio = df["ritmo_venta_diario"].std()
    df["es_anomalia"]   = df["ritmo_venta_diario"] > (media + 2 * desvio)
    df["tipo_anomalia"] = np.where(df["es_anomalia"], "DEMANDA_INUSUAL", "NORMAL")
    return df

def obtener_criticos() -> pd.DataFrame:
    df = analizar_inventario()
    return df[df["clasificacion"] == "CRÍTICO"].sort_values(
        "score_compuesto", ascending=False
    )

def obtener_resumen_por_categoria() -> dict:
    df = analizar_inventario()
    resumen = df.groupby("categoria")["clasificacion"].value_counts().to_dict()
    return resumen


if __name__ == "__main__":
    df = analizar_inventario()
    print(f"Total registros: {len(df)}")
    print(f"\n=== Distribución ===")
    print(df["clasificacion"].value_counts())
    print(f"\n=== Top 10 más urgentes ===")
    print(df.sort_values("score_compuesto", ascending=False)[
        ["producto_id", "tienda_id", "categoria",
         "dias_stock_restante", "clasificacion", "score_compuesto"]
    ].head(10).to_string())
    print(f"\n=== Resumen por categoría ===")
    for k, v in obtener_resumen_por_categoria().items():
        print(f"  {k}: {v}")