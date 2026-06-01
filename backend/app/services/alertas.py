import pandas as pd
import numpy as np
from backend.app.data.loader import cargar_datos

def obtener_alertas() -> dict:
    df = cargar_datos()
    return {
        "alertas_vencimiento":   _alertas_vencimiento(df),
        "alertas_stock_critico": _alertas_stock_critico(df),
        "alertas_promocion":     _alertas_promocion(df),
        "alertas_competidor":    _alertas_competidor(df),
    }

def _alertas_vencimiento(df: pd.DataFrame) -> list:
    alertas = []
    hoy = pd.Timestamp.today()
    groceries = df[df["fecha_vencimiento"].notna()].copy()
    for _, row in groceries.iterrows():
        dias = (row["fecha_vencimiento"] - hoy).days
        if dias <= 10:
            alertas.append({
                "tipo":           "VENCIMIENTO",
                "nivel":          "URGENTE" if dias <= 3 else "ADVERTENCIA",
                "producto_id":    row["producto_id"],
                "tienda_id":      row["tienda_id"],
                "categoria":      row["categoria"],
                "mensaje":        f"Vence en {dias} días",
                "dias_restantes": int(dias),
                "stock_actual":   int(row["stock_actual"]),
            })
    return sorted(alertas, key=lambda x: x["dias_restantes"])

def _alertas_stock_critico(df: pd.DataFrame) -> list:
    alertas = []
    criticos = df[df["dias_stock_restante"] < 2.0]
    for _, row in criticos.iterrows():
        nivel = "URGENTE" if row["dias_stock_restante"] < 1.0 else "ADVERTENCIA"

        stock_actual     = int(row["stock_actual"])
        ritmo_diario     = round(float(row["ritmo_venta_diario"]), 1)
        dias_float       = float(row["dias_stock_restante"])
        dias_completos   = int(dias_float)  # floor — no contar días incompletos
        cubre_dia        = dias_float >= 1.0
        unidades_3_dias  = max(0, int(round(ritmo_diario * 3)) - stock_actual)

        alertas.append({
            "tipo":                "STOCK_CRITICO",
            "nivel":               nivel,
            "producto_id":         row["producto_id"],
            "tienda_id":           row["tienda_id"],
            "categoria":           row["categoria"],
            "mensaje":             f"Stock para {dias_completos} día{'s' if dias_completos != 1 else ''} completo{'s' if dias_completos != 1 else ''}",
            "stock_actual":        stock_actual,
            "ritmo_venta_diario":  ritmo_diario,
            "dias_stock_completos": dias_completos,
            "cubre_dia_completo":  cubre_dia,
            "unidades_para_3_dias": unidades_3_dias,
            "unidades_sugeridas":  int(row["unidades_sugeridas_compra"]),
        })
    return sorted(alertas, key=lambda x: x["dias_stock_completos"])

def _alertas_promocion(df: pd.DataFrame) -> list:
    alertas = []
    con_promo = df[df["promocion"] == 1]
    for _, row in con_promo.iterrows():
        stock_minimo = row["ritmo_venta_diario"] * 2 * 1.4
        if row["stock_actual"] < stock_minimo:
            alertas.append({
                "tipo":           "PROMOCION_SIN_STOCK",
                "nivel":          "ADVERTENCIA",
                "producto_id":    row["producto_id"],
                "tienda_id":      row["tienda_id"],
                "categoria":      row["categoria"],
                "mensaje":        f"Promoción activa — stock insuficiente ({int(row['stock_actual'])} uds)",
                "stock_actual":   int(row["stock_actual"]),
                "stock_minimo":   int(stock_minimo),
            })
    return sorted(alertas, key=lambda x: x["stock_actual"])

def _alertas_competidor(df: pd.DataFrame) -> list:
    alertas = []
    competencia = df[df["precio_competidor"] < df["precio"] * 0.9]
    for _, row in competencia.iterrows():
        dif = round(
            (row["precio"] - row["precio_competidor"]) / row["precio"] * 100, 1
        )
        alertas.append({
            "tipo":              "COMPETIDOR_MAS_BARATO",
            "nivel":             "INFO",
            "producto_id":       row["producto_id"],
            "tienda_id":         row["tienda_id"],
            "categoria":         row["categoria"],
            "mensaje":           f"Competidor {dif}% más barato — revisar precio",
            "precio_propio":     round(float(row["precio"]), 2),
            "precio_competidor": round(float(row["precio_competidor"]), 2),
            "diferencia_pct":    dif,
        })
    return sorted(alertas, key=lambda x: x["diferencia_pct"], reverse=True)


if __name__ == "__main__":
    alertas = obtener_alertas()
    for tipo, lista in alertas.items():
        print(f"\n=== {tipo.upper()} ({len(lista)}) ===")
        for a in lista[:3]:
            print(f"  [{a['nivel']}] {a['producto_id']}-{a['tienda_id']} — {a['mensaje']}")