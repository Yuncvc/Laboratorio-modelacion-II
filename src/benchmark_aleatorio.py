"""
benchmark_aleatorio.py

Genera 10 asignaciones aleatorias FACTIBLES por instancia y calcula
estadísticas de costo para medir la mejora del Modelo 4 frente al azar.

Cada asignación aleatoria respeta capacidad, asigna cada curso a una sala,
no repite sala dentro del mismo bloque y permite salas sin usar cuando hay
sobreoferta. Libres y entrantes no generan costo (no están en F).

Uso:
    python src/benchmark_aleatorio.py data/instancias_modelo4/M4_E12
"""

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd

from resolver_modelo4 import cargar_instancia, calcular_metricas

BASE = Path(__file__).resolve().parents[1]
DIR_RESULTADOS = BASE / "outputs" / "resultados"

N_RANDOM = 10
MAX_INTENTOS_POR_ASIGNACION = 500


def asignacion_aleatoria(cursos, tamanos, R, cap, rng):
    """Asigna cada curso a una sala factible no usada, en orden aleatorio.

    Ordena los cursos de mayor a menor tamaño (con desempate aleatorio)
    para aumentar la probabilidad de éxito, y elige la sala al azar entre
    las factibles disponibles.
    """
    orden = sorted(cursos, key=lambda cid: (-tamanos[cid], rng.random()))
    usadas = set()
    asig = {}
    for cid in orden:
        factibles = [r for r in R if r not in usadas and cap[r] >= tamanos[cid]]
        if not factibles:
            return None
        r = factibles[rng.integers(len(factibles))]
        asig[cid] = r
        usadas.add(r)
    return asig


def benchmark_instancia(instance_dir, n_random=N_RANDOM, seed=12345):
    instance_dir = Path(instance_dir)
    nombre = instance_dir.name
    datos = cargar_instancia(instance_dir)
    I, K, R = datos["I"], datos["K"], datos["R"]
    n, m, cap = datos["n"], datos["m"], datos["cap"]
    F, c, edificio = datos["F"], datos["c"], datos["edificio"]

    rng = np.random.default_rng(seed)
    filas = []

    for rep in range(n_random):
        asig_b1 = asig_b2 = None
        for _ in range(MAX_INTENTOS_POR_ASIGNACION):
            asig_b1 = asignacion_aleatoria(I, n, R, cap, rng)
            if asig_b1 is not None:
                break
        for _ in range(MAX_INTENTOS_POR_ASIGNACION):
            asig_b2 = asignacion_aleatoria(K, m, R, cap, rng)
            if asig_b2 is not None:
                break
        if asig_b1 is None or asig_b2 is None:
            continue

        met = calcular_metricas(asig_b1, asig_b2, F, c, edificio, R)
        met["replica"] = rep
        filas.append(met)

    df = pd.DataFrame(filas)
    resumen = {"instancia": nombre, "n_random_exitosas": len(df)}

    if len(df) > 0:
        resumen.update({
            "costo_azar_promedio": round(df["costo_total"].mean(), 4),
            "costo_azar_min": round(df["costo_total"].min(), 4),
            "costo_azar_max": round(df["costo_total"].max(), 4),
            "costo_azar_std": round(df["costo_total"].std(ddof=0), 4),
            "estudiantes_misma_sala_azar_promedio":
                round(df["estudiantes_misma_sala"].mean(), 2),
            "estudiantes_mismo_edificio_azar_promedio":
                round(df["estudiantes_mismo_edificio"].mean(), 2),
            "estudiantes_cambio_edificio_azar_promedio":
                round(df["estudiantes_cambio_edificio"].mean(), 2),
        })

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(DIR_RESULTADOS / f"{nombre}_benchmark_azar.csv", index=False)
    with open(DIR_RESULTADOS / f"{nombre}_benchmark_azar.json", "w",
              encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    return resumen


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("instance_dir")
    parser.add_argument("--n_random", type=int, default=N_RANDOM)
    parser.add_argument("--seed", type=int, default=12345)
    args = parser.parse_args()

    res = benchmark_instancia(args.instance_dir, args.n_random, args.seed)
    print(json.dumps(res, indent=2, ensure_ascii=False))
