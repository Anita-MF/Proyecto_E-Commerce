import pandas as pd
from backend.app.data.loader import cargar_datos
from backend.app.services.analisis import analizar_inventario, obtener_criticos
from backend.app.services.prediccion import obtener_lista_compras
from backend.app.services.alertas import obtener_alertas

class AgenteInventario:
    """
    Agente Inteligente de Optimización de Inventario.
    Estructura: Percepción → Razonamiento → Actuación
    (Libro 1 - Clase 2: Agentes Inteligentes)
    """

    def __init__(self):
        self.nombre = "Agente de Inventario E-Commerce"
        self.estado = {}

    def percibir(self) -> dict:
        """Lee el entorno: carga y analiza todos los datos"""
        df_analisis   = analizar_inventario()
        df_prediccion = obtener_lista_compras()
        alertas       = obtener_alertas()

        self.estado = {
            "df_analisis":     df_analisis,
            "df_prediccion":   df_prediccion,
            "alertas":         alertas,
            "total_productos": len(df_analisis),
            "criticos":        len(df_analisis[df_analisis["clasificacion"] == "CRÍTICO"]),
            "bajos":           len(df_analisis[df_analisis["clasificacion"] == "BAJO"]),
            "normales":        len(df_analisis[df_analisis["clasificacion"] == "NORMAL"]),
            "excesos":         len(df_analisis[df_analisis["clasificacion"] == "EXCESO"]),
        }
        return self.estado

    def razonar(self) -> dict:
        """
        Aplica reglas SI-ENTONCES para tomar decisiones
        (Sistema de Producción - Libro 1 Clase 3)
        """
        if not self.estado:
            self.percibir()

        decisiones = []
        for _, producto in self.estado["df_analisis"].iterrows():
            d = self._evaluar_producto(producto)
            if d:
                decisiones.append(d)

        return {"decisiones": decisiones, "total": len(decisiones)}

    def _evaluar_producto(self, producto) -> dict | None:
        """Reglas de producción SI condición ENTONCES acción"""

        dias = producto["dias_stock_restante"]
        promo = producto["promocion"]
        temp  = producto["temporada"]

        # Regla 1: Stock crítico — menos de 1 día
        if dias < 1.0:
            return {
                "producto_id":        producto["producto_id"],
                "tienda_id":          producto["tienda_id"],
                "categoria":          producto["categoria"],
                "regla":              "STOCK_CRÍTICO_URGENTE",
                "accion":             "COMPRAR_INMEDIATO",
                "justificacion":      f"Solo {dias} días de stock — riesgo de quiebre",
                "unidades_sugeridas": int(producto["unidades_sugeridas_compra"]),
                "prioridad":          1,
            }

        # Regla 2: Stock bajo con promoción activa
        if dias < 2.0 and promo == 1:
            return {
                "producto_id":        producto["producto_id"],
                "tienda_id":          producto["tienda_id"],
                "categoria":          producto["categoria"],
                "regla":              "STOCK_BAJO_CON_PROMOCION",
                "accion":             "COMPRAR_URGENTE",
                "justificacion":      f"Stock bajo ({dias} días) y promoción activa — demanda aumentada 40%",
                "unidades_sugeridas": int(producto["unidades_sugeridas_compra"] * 1.4),
                "prioridad":          2,
            }

        # Regla 3: Stock bajo en temporada alta
        if dias < 2.0 and temp in ["High", "Winter"]:
            return {
                "producto_id":        producto["producto_id"],
                "tienda_id":          producto["tienda_id"],
                "categoria":          producto["categoria"],
                "regla":              "STOCK_BAJO_TEMPORADA_ALTA",
                "accion":             "COMPRAR_PRIORITARIO",
                "justificacion":      f"Stock bajo ({dias} días) en temporada {temp} — demanda aumentada 20%",
                "unidades_sugeridas": int(producto["unidades_sugeridas_compra"] * 1.2),
                "prioridad":          3,
            }

        # Regla 4: Stock bajo normal
        if dias < 2.0:
            return {
                "producto_id":        producto["producto_id"],
                "tienda_id":          producto["tienda_id"],
                "categoria":          producto["categoria"],
                "regla":              "STOCK_BAJO",
                "accion":             "COMPRAR_PLANIFICADO",
                "justificacion":      f"{dias} días de stock restante — reponer pronto",
                "unidades_sugeridas": int(producto["unidades_sugeridas_compra"]),
                "prioridad":          4,
            }

        return None

    def actuar(self) -> dict:
        """Genera el reporte final con todas las decisiones del agente"""
        estado       = self.percibir()
        razonamiento = self.razonar()
        decisiones   = sorted(razonamiento["decisiones"], key=lambda x: x["prioridad"])

        costo_total = sum(
            d["unidades_sugeridas"] *
            estado["df_analisis"].loc[
                estado["df_analisis"]["producto_id"] == d["producto_id"], "precio"
            ].values[0]
            for d in decisiones
        )

        return {
            "agente": self.nombre,
            "resumen": {
                "total_productos":      estado["total_productos"],
                "criticos":             estado["criticos"],
                "bajos":                estado["bajos"],
                "normales":             estado["normales"],
                "excesos":              estado["excesos"],
                "total_decisiones":     len(decisiones),
                "costo_total_estimado": round(float(costo_total), 2),
            },
            "decisiones": decisiones,
            "alertas_criticas": (
                estado["alertas"]["alertas_vencimiento"] +
                [a for a in estado["alertas"]["alertas_stock_critico"]
                 if a["nivel"] == "URGENTE"]
            ),
        }


def ejecutar_agente() -> dict:
    agente = AgenteInventario()
    return agente.actuar()


if __name__ == "__main__":
    resultado = ejecutar_agente()
    resumen   = resultado["resumen"]

    print(f"\n{'='*55}")
    print(f"  {resultado['agente']}")
    print(f"{'='*55}")
    print(f"  Total registros:    {resumen['total_productos']}")
    print(f"  Críticos:           {resumen['criticos']}")
    print(f"  Bajos:              {resumen['bajos']}")
    print(f"  Normales:           {resumen['normales']}")
    print(f"  Excesos:            {resumen['excesos']}")
    print(f"  Decisiones tomadas: {resumen['total_decisiones']}")
    print(f"  Costo estimado:     ${resumen['costo_total_estimado']:,.2f}")
    print(f"\n=== Primeras 5 decisiones ===")
    for d in resultado["decisiones"][:5]:
        print(f"  [{d['prioridad']}] {d['producto_id']}-{d['tienda_id']} | {d['regla']}")
        print(f"      → {d['accion']}: {d['unidades_sugeridas']} unidades")
        print(f"      Motivo: {d['justificacion']}")
    print(f"\n=== Alertas críticas: {len(resultado['alertas_criticas'])} ===")
    for a in resultado["alertas_criticas"][:5]:
        print(f"  [{a['nivel']}] {a['producto_id']}-{a['tienda_id']} — {a['mensaje']}")