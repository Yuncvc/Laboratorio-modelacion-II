"""
correr_experimentos_m4.py

Pipeline completo de experimentos del Modelo 4:
    1. Crea carpetas de salida.
    2. Genera todas las instancias (familias A y B).
    3. Resuelve cada instancia con Gurobi (time_limit por instancia).
    4. Corre el benchmark aleatorio (10 réplicas factibles).
    5. Consolida resultados en resultados_modelo4.csv / .json.

Ejecución desde la raíz del proyecto:
    python src/correr_experimentos_m4.py
Luego:
    python src/construir_notebook_final.py
    jupyter nbconvert --to notebook --execute notebooks/Modelo4_Analisis_Final.ipynb
"""

from pathlib import Path
import json

import pandas as pd

import generar_instancias_m4 as gen
from resolver_modelo4 import resolver_instancia
from benchmark_aleatorio import benchmark_instancia

BASE = Path(__file__).resolve().parents[1]
DIRS = [
    BASE / "data" / "instancias_modelo4",
    BASE / "outputs" / "resultados",
    BASE / "outputs" / "asignaciones",
    BASE / "outputs" / "graficos",
    BASE / "outputs" / "notebooks",
    BASE / "notebooks",
]

COLUMNAS_RESUMEN = [
    "instancia", "familia", "I", "K", "R", "edificios", "carreras",
    "num_x", "num_y", "num_z", "num_vars", "num_constraints",
    "runtime", "status", "obj_modelo", "best_bound", "mip_gap",
    "costo_azar_promedio", "costo_azar_min", "costo_azar_max",
    "costo_azar_std", "mejora_vs_azar",
    "estudiantes_misma_sala", "estudiantes_mismo_edificio",
    "estudiantes_cambio_edificio",
    "costo_mismo_edificio", "costo_cambio_edificio",
    "salas_usadas_b1", "salas_usadas_b2",
    "salas_no_usadas_b1", "salas_no_usadas_b2",
    "total_libres", "total_entrantes",
    "time_limit",
]


def main():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)

    print("== 1. Generando instancias ==")
    gen.generar_todas()

    filas = []
    for cfg in gen.INSTANCIAS:
        nombre = cfg["nombre"]
        instance_dir = BASE / "data" / "instancias_modelo4" / nombre

        with open(instance_dir / "metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)

        print(f"== 2. Resolviendo {nombre} (time_limit={cfg['time_limit']}s) ==")
        res_solver = resolver_instancia(instance_dir,
                                        time_limit=cfg["time_limit"])

        print(f"== 3. Benchmark aleatorio {nombre} ==")
        res_azar = benchmark_instancia(instance_dir)

        fila = {
            "instancia": nombre, "familia": cfg["familia"],
            "I": cfg["I"], "K": cfg["K"], "R": cfg["R"],
            "edificios": cfg["edificios"], "carreras": cfg["carreras"],
            "time_limit": cfg["time_limit"],
            "total_libres": metadata.get("total_libres"),
            "total_entrantes": metadata.get("total_entrantes"),
        }
        fila.update({k: v for k, v in res_solver.items()
                     if k not in ("instancia", "time_limit")})
        fila.update({k: v for k, v in res_azar.items() if k != "instancia"})

        obj = fila.get("obj_modelo")
        prom = fila.get("costo_azar_promedio")
        if obj is not None and prom not in (None, 0):
            fila["mejora_vs_azar"] = round((prom - obj) / prom * 100, 2)
        else:
            fila["mejora_vs_azar"] = None

        filas.append(fila)

    df = pd.DataFrame(filas)
    extras = [c for c in df.columns if c not in COLUMNAS_RESUMEN]
    df = df.reindex(columns=COLUMNAS_RESUMEN + extras)

    salida_csv = BASE / "outputs" / "resultados" / "resultados_modelo4.csv"
    salida_json = BASE / "outputs" / "resultados" / "resultados_modelo4.json"
    df.to_csv(salida_csv, index=False)
    df.to_json(salida_json, orient="records", indent=2, force_ascii=False)

    print(f"\n[OK] Resultados consolidados en:\n  {salida_csv}\n  {salida_json}")
    print(df[["instancia", "status", "obj_modelo", "mip_gap", "runtime",
              "mejora_vs_azar"]].to_string(index=False))


if __name__ == "__main__":
    main()
