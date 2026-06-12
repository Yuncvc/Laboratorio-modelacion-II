"""
resolver_modelo4.py

Resuelve una instancia del Modelo 4 con Gurobi.

min  sum_{i,k: f_ik>0} sum_r sum_s f_ik * c_rs * z_ikrs
s.a. sum_r x_ir = 1                       (asignación obligatoria B1)
     sum_s y_ks = 1                       (asignación obligatoria B2)
     sum_i x_ir <= 1, sum_k y_ks <= 1     (ocupación única por bloque)
     x_ir = 0 si tamano_i > capacidad_r   (capacidad; se omite la variable)
     z <= x, z <= y, z >= x + y - 1       (linealización de McCormick)
     x, y binarias; z continua en [0,1]

Los estudiantes libres y entrantes NO aparecen en la función objetivo:
solo afectan los tamaños de los cursos y, por tanto, la capacidad.

Optimización clave: z_ikrs se crea solo para pares (i,k) con f_ik > 0.

Uso:
    python src/resolver_modelo4.py data/instancias_modelo4/M4_E12 --time_limit 300
"""

from pathlib import Path
import argparse
import json
import time

import pandas as pd
import gurobipy as gp
from gurobipy import GRB

BASE = Path(__file__).resolve().parents[1]
DIR_RESULTADOS = BASE / "outputs" / "resultados"
DIR_ASIGNACIONES = BASE / "outputs" / "asignaciones"


# ----------------------------------------------------------------------
# Carga de datos
# ----------------------------------------------------------------------
def cargar_instancia(instance_dir):
    instance_dir = Path(instance_dir)
    cursos_b1 = pd.read_csv(instance_dir / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(instance_dir / "cursos_b2.csv")
    salas = pd.read_csv(instance_dir / "salas.csv")
    flujos = pd.read_csv(instance_dir / "flujos.csv")
    costos = pd.read_csv(instance_dir / "costos_sala_sala.csv")

    with open(instance_dir / "metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)

    I = cursos_b1["curso_id"].tolist()
    K = cursos_b2["curso_id"].tolist()
    R = salas["sala_id"].tolist()
    n = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    m = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))
    cap = dict(zip(salas["sala_id"], salas["capacidad"]))
    edificio = dict(zip(salas["sala_id"], salas["edificio"]))

    F = {}
    for _, fila in flujos.iterrows():
        if fila["flujo"] > 0:
            F[(fila["curso_b1"], fila["curso_b2"])] = float(fila["flujo"])

    col_costo = "costo_final" if "costo_final" in costos.columns else "costo"
    c = {(f["sala_origen"], f["sala_destino"]): float(f[col_costo])
         for _, f in costos.iterrows()}
    tipo = {(f["sala_origen"], f["sala_destino"]): f["tipo_transicion"]
            for _, f in costos.iterrows()} if "tipo_transicion" in costos.columns else {}

    return dict(I=I, K=K, R=R, n=n, m=m, cap=cap, edificio=edificio,
                F=F, c=c, tipo=tipo, salas=salas, metadata=metadata)


# ----------------------------------------------------------------------
# Métricas interpretativas (también usadas por benchmark_aleatorio)
# ----------------------------------------------------------------------
def calcular_metricas(asig_b1, asig_b2, F, c, edificio, R):
    """asig_b1: {curso_b1: sala}, asig_b2: {curso_b2: sala}."""
    met = dict(costo_total=0.0,
               estudiantes_misma_sala=0, estudiantes_mismo_edificio=0,
               estudiantes_cambio_edificio=0,
               costo_misma_sala=0.0, costo_mismo_edificio=0.0,
               costo_cambio_edificio=0.0)

    for (i, k), flujo in F.items():
        r, s = asig_b1[i], asig_b2[k]
        costo = flujo * c[(r, s)]
        met["costo_total"] += costo

        if r == s:
            met["estudiantes_misma_sala"] += flujo
            met["costo_misma_sala"] += costo  # = 0 por construcción
        elif edificio[r] == edificio[s]:
            met["estudiantes_mismo_edificio"] += flujo
            met["costo_mismo_edificio"] += costo
        else:
            met["estudiantes_cambio_edificio"] += flujo
            met["costo_cambio_edificio"] += costo

    usadas_b1 = set(asig_b1.values())
    usadas_b2 = set(asig_b2.values())
    met["salas_usadas_b1"] = len(usadas_b1)
    met["salas_usadas_b2"] = len(usadas_b2)
    met["salas_no_usadas_b1"] = len(R) - len(usadas_b1)
    met["salas_no_usadas_b2"] = len(R) - len(usadas_b2)
    return met


# ----------------------------------------------------------------------
# Resolución
# ----------------------------------------------------------------------
def resolver_instancia(instance_dir, time_limit=600, mip_gap=None, verbose=False):
    instance_dir = Path(instance_dir)
    nombre = instance_dir.name
    datos = cargar_instancia(instance_dir)
    I, K, R = datos["I"], datos["K"], datos["R"]
    n, m, cap = datos["n"], datos["m"], datos["cap"]
    F, c = datos["F"], datos["c"]

    t0 = time.time()
    model = gp.Model(f"Modelo4_{nombre}")
    model.Params.OutputFlag = 1 if verbose else 0
    model.Params.TimeLimit = time_limit
    if mip_gap is not None:
        model.Params.MIPGap = mip_gap

    # Salas factibles por capacidad (la restricción de capacidad se impone
    # no creando variables infactibles).
    R_i = {i: [r for r in R if cap[r] >= n[i]] for i in I}
    S_k = {k: [s for s in R if cap[s] >= m[k]] for k in K}

    x = model.addVars([(i, r) for i in I for r in R_i[i]],
                      vtype=GRB.BINARY, name="x")
    y = model.addVars([(k, s) for k in K for s in S_k[k]],
                      vtype=GRB.BINARY, name="y")

    # z solo para pares con flujo positivo.
    claves_z = [(i, k, r, s) for (i, k) in F for r in R_i[i] for s in S_k[k]]
    z = model.addVars(claves_z, vtype=GRB.CONTINUOUS, lb=0.0, ub=1.0, name="z")

    model.addConstrs((gp.quicksum(x[i, r] for r in R_i[i]) == 1 for i in I),
                     name="asig_b1")
    model.addConstrs((gp.quicksum(y[k, s] for s in S_k[k]) == 1 for k in K),
                     name="asig_b2")
    model.addConstrs((gp.quicksum(x[i, r] for i in I if r in R_i[i]) <= 1
                      for r in R), name="ocup_b1")
    model.addConstrs((gp.quicksum(y[k, s] for k in K if s in S_k[k]) <= 1
                      for s in R), name="ocup_b2")

    model.addConstrs((z[i, k, r, s] <= x[i, r] for (i, k, r, s) in claves_z),
                     name="lin1")
    model.addConstrs((z[i, k, r, s] <= y[k, s] for (i, k, r, s) in claves_z),
                     name="lin2")
    model.addConstrs((z[i, k, r, s] >= x[i, r] + y[k, s] - 1
                      for (i, k, r, s) in claves_z), name="lin3")

    model.setObjective(
        gp.quicksum(F[(i, k)] * c[(r, s)] * z[i, k, r, s]
                    for (i, k, r, s) in claves_z),
        GRB.MINIMIZE)

    model.optimize()
    runtime = time.time() - t0

    estado = {GRB.OPTIMAL: "OPTIMAL", GRB.TIME_LIMIT: "TIME_LIMIT",
              GRB.INFEASIBLE: "INFEASIBLE"}.get(model.Status,
                                                f"STATUS_{model.Status}")

    resumen = {
        "instancia": nombre,
        "status": estado,
        "runtime": round(runtime, 2),
        "time_limit": time_limit,
        "num_vars": model.NumVars,
        "num_constraints": model.NumConstrs,
        "num_x": len(x), "num_y": len(y), "num_z": len(z),
        "obj_modelo": None, "best_bound": None, "mip_gap": None,
    }

    tiene_solucion = model.SolCount > 0
    if tiene_solucion:
        resumen["obj_modelo"] = round(model.ObjVal, 4)
        resumen["best_bound"] = round(model.ObjBound, 4)
        resumen["mip_gap"] = round(model.MIPGap, 6) if model.ObjVal > 1e-9 else 0.0

        asig_b1 = {i: r for (i, r) in x if x[i, r].X > 0.5}
        asig_b2 = {k: s for (k, s) in y if y[k, s].X > 0.5}

        # Verificación: recalcular el costo desde las asignaciones.
        met = calcular_metricas(asig_b1, asig_b2, F, c, datos["edificio"], R)
        if abs(met["costo_total"] - model.ObjVal) > 1e-4 * max(1.0, model.ObjVal):
            raise RuntimeError(
                f"{nombre}: costo recalculado {met['costo_total']:.4f} "
                f"no coincide con ObjVal {model.ObjVal:.4f}")
        resumen["costo_recalculado"] = round(met.pop("costo_total"), 4)
        resumen.update({k2: (round(v, 4) if isinstance(v, float) else v)
                        for k2, v in met.items()})

        dir_asig = DIR_ASIGNACIONES / nombre
        dir_asig.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([{"curso_b1": i, "tamano": n[i], "sala": r,
                       "capacidad_sala": cap[r],
                       "edificio": datos["edificio"][r]}
                      for i, r in asig_b1.items()]) \
            .to_csv(dir_asig / "asignaciones_b1.csv", index=False)
        pd.DataFrame([{"curso_b2": k, "tamano": m[k], "sala": s,
                       "capacidad_sala": cap[s],
                       "edificio": datos["edificio"][s]}
                      for k, s in asig_b2.items()]) \
            .to_csv(dir_asig / "asignaciones_b2.csv", index=False)

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    with open(DIR_RESULTADOS / f"{nombre}_resumen_solver.json", "w",
              encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    return resumen


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("instance_dir")
    parser.add_argument("--time_limit", type=float, default=600)
    parser.add_argument("--mip_gap", type=float, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    res = resolver_instancia(args.instance_dir, args.time_limit,
                             args.mip_gap, args.verbose)
    print(json.dumps(res, indent=2, ensure_ascii=False))
