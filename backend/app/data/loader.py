import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "data.csv"

def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df = _renombrar_columnas(df)
    df = _limpiar_datos(df)
    df = _agregar_metricas(df)
    return df

def _renombrar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={
        "Date":                 "fecha",
        "Store ID":             "tienda_id",
        "Product ID":           "producto_id",
        "Category":             "categoria",
        "Region":               "region",
        "Inventory Level":      "stock_actual",
        "Units Sold":           "unidades_vendidas",
        "Units Ordered":        "unidades_ordenadas",
        "Demand Forecast":      "demanda_forecast",
        "Price":                "precio",
        "Discount":             "descuento",
        "Weather Condition":    "clima",
        "Holiday/Promotion":    "promocion",
        "Competitor Pricing":   "precio_competidor",
        "Seasonality":          "temporada",
    })

def _limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.dropna(subset=["producto_id", "unidades_vendidas", "stock_actual"])
    df = df[df["unidades_vendidas"] > 0]
    df["categoria"] = df["categoria"].str.strip().str.title()
    df["region"]    = df["region"].str.strip().str.title()
    df["temporada"] = df["temporada"].str.strip().str.title()
    df["clima"]     = df["clima"].str.strip().str.title()
    for col in ["stock_actual", "precio", "descuento", "precio_competidor"]:
        df[col] = df.groupby("producto_id")[col].transform(
            lambda x: x.fillna(x.median())
        )
    df = df.fillna(df.median(numeric_only=True))
    return df

def _agregar_metricas(df: pd.DataFrame) -> pd.DataFrame:

    resumen = df.groupby(["producto_id", "tienda_id"]).agg(
        promedio_vendido    = ("unidades_vendidas", "mean"),
        std_vendido         = ("unidades_vendidas", "std"),
        cant_registros      = ("unidades_vendidas", "count"),
        stock_actual        = ("stock_actual", "last"),
        demanda_forecast    = ("demanda_forecast", "mean"),
        precio              = ("precio", "mean"),
        descuento           = ("descuento", "mean"),
        precio_competidor   = ("precio_competidor", "mean"),
        categoria           = ("categoria", "last"),
        region              = ("region", "last"),
        temporada           = ("temporada", "last"),
        promocion           = ("promocion", "last"),
    ).reset_index()

    resumen["ritmo_venta_diario"] = resumen["promedio_vendido"].round(2)

    resumen["dias_stock_restante"] = (
        resumen["stock_actual"] / resumen["ritmo_venta_diario"].replace(0, np.nan)
    ).round(2).fillna(999)

    resumen["stock_critico_score"] = (
        (1 / resumen["dias_stock_restante"].replace(0, np.nan))
        .clip(0, 1) * 100
    ).round(1).fillna(0)

    resumen["estado_stock"] = pd.cut(
        resumen["dias_stock_restante"],
        bins=[-1, 1.0, 2.0, 4.0, float("inf")],
        labels=["CRÍTICO", "BAJO", "NORMAL", "EXCESO"]
    )

    factor_temporada = resumen["temporada"].map(
        {"High": 1.3, "Winter": 1.2, "Summer": 1.1,
         "Spring": 1.0, "Autumn": 0.9, "Low": 0.8}
    ).fillna(1.0)

    factor_promocion = resumen["promocion"].map({1: 1.4, 0: 1.0})

    resumen["unidades_sugeridas_compra"] = (
        resumen["ritmo_venta_diario"] * 3
        * factor_temporada
        * factor_promocion
        - resumen["stock_actual"]
    ).clip(lower=0).round(0).astype(int)

    resumen["fecha_vencimiento"] = pd.NaT
    mask = resumen["categoria"] == "Groceries"
    resumen.loc[mask, "fecha_vencimiento"] = (
        pd.Timestamp.today() +
        pd.to_timedelta(
            np.random.randint(1, 10, mask.sum()), unit="D"
        )
    )

    return resumen


if __name__ == "__main__":
    df = cargar_datos()
    print(f"Total registros producto-tienda: {len(df)}")
    print(f"\n=== Distribución de estados ===")
    print(df["estado_stock"].value_counts())
    print(f"\n=== Muestra ===")
    print(df[["producto_id", "tienda_id", "categoria", "stock_actual",
              "ritmo_venta_diario", "dias_stock_restante",
              "estado_stock", "unidades_sugeridas_compra"]].head(15).to_string())