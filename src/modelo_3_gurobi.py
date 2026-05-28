from pathlib import Path
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

from validar_data_3 import validar_instancia_modelo_3
from IPython.display import display


def leer_costos(carpeta_test):
    """
    Lee costos.csv y lo convierte en un diccionario c[r, s] = costo.
    Igual que en el Modelo 2; la diferencia está en cómo se generó el archivo.
    """

    carpeta_test = Path(carpeta_test)
    costos = pd.read_csv(carpeta_test / "costos.csv")

    c = {}
    for _, fila in costos.iterrows():
        c[fila["sala_origen"], fila["sala_destino"]] = fila["costo"]

    return c


def nombre_status_gurobi(status):
    if status == GRB.OPTIMAL:
        return "OPTIMAL"
    if status == GRB.INFEASIBLE:
        return "INFEASIBLE"
    if status == GRB.UNBOUNDED:
        return "UNBOUNDED"
    if status == GRB.TIME_LIMIT:
        return "TIME_LIMIT"
    return f"OTRO_STATUS_{status}"


def resolver_modelo_3(carpeta_test, mostrar_output=True):
    """
    Resuelve una instancia del Modelo 3.

    La formulación es idéntica al Modelo 2.
    La única diferencia es la matriz de costos c[r,s], que ahora
    depende del tipo de transición entre edificios:
        c[r,s] = 0             si r == s
        c[r,s] = 1             si r != s y edificio(r) == edificio(s)
        c[r,s] = gamma[e1,e2]  si edificio(r) != edificio(s)

    Entrada:
        carpeta_test: ruta a carpeta con cursos_b1.csv, cursos_b2.csv,
                      salas.csv, flujos.csv, libres.csv, costos.csv, gamma.csv

    Salida:
        Diccionario con status, objetivo, asignacion_b1, asignacion_b2.
    """

    # --------------------------------------------------
    # 1. Validar y cargar datos
    # --------------------------------------------------

    datos = validar_instancia_modelo_3(carpeta_test)

    I   = datos["I"]
    K   = datos["K"]
    R   = datos["R"]

    n   = datos["n"]
    m   = datos["m"]
    cap = datos["cap"]
    F   = datos["F"]

    c = leer_costos(carpeta_test)

    # --------------------------------------------------
    # 2. Crear modelo
    # --------------------------------------------------

    modelo = gp.Model("Modelo_3_multiples_edificios")

    if not mostrar_output:
        modelo.setParam("OutputFlag", 0)

    # --------------------------------------------------
    # 3. Variables de decisión
    # --------------------------------------------------
    # x[i,r] = 1 si curso i del bloque 1 se asigna a sala r
    # y[k,s] = 1 si curso k del bloque 2 se asigna a sala s
    # z[i,k,r,s] = 1 si i está en r y k está en s

    x = modelo.addVars(I, R, vtype=GRB.BINARY, name="x")
    y = modelo.addVars(K, R, vtype=GRB.BINARY, name="y")
    z = modelo.addVars(I, K, R, R, vtype=GRB.BINARY, name="z")

    # --------------------------------------------------
    # 4. Función objetivo
    # --------------------------------------------------
    # min sum_i sum_k sum_r sum_s F[i,k] * c[r,s] * z[i,k,r,s]

    modelo.setObjective(
        gp.quicksum(
            F.loc[i, k] * c[r, s] * z[i, k, r, s]
            for i in I
            for k in K
            for r in R
            for s in R
        ),
        GRB.MINIMIZE,
    )

    # --------------------------------------------------
    # 5. Restricciones de asignación única
    # --------------------------------------------------

    for i in I:
        modelo.addConstr(
            gp.quicksum(x[i, r] for r in R) == 1,
            name=f"asignacion_b1_{i}"
        )

    for k in K:
        modelo.addConstr(
            gp.quicksum(y[k, r] for r in R) == 1,
            name=f"asignacion_b2_{k}"
        )

    # --------------------------------------------------
    # 6. Restricciones de ocupación única
    # --------------------------------------------------

    for r in R:
        modelo.addConstr(
            gp.quicksum(x[i, r] for i in I) <= 1,
            name=f"ocupacion_b1_{r}"
        )

    for r in R:
        modelo.addConstr(
            gp.quicksum(y[k, r] for k in K) <= 1,
            name=f"ocupacion_b2_{r}"
        )

    # --------------------------------------------------
    # 7. Restricciones de capacidad
    # --------------------------------------------------

    for i in I:
        for r in R:
            modelo.addConstr(n[i] * x[i, r] <= cap[r], name=f"capacidad_b1_{i}_{r}")

    for k in K:
        for r in R:
            modelo.addConstr(m[k] * y[k, r] <= cap[r], name=f"capacidad_b2_{k}_{r}")

    # --------------------------------------------------
    # 8. Linealización de z = x * y
    # --------------------------------------------------

    for i in I:
        for k in K:
            for r in R:
                for s in R:
                    modelo.addConstr(z[i, k, r, s] <= x[i, r], name=f"lin1_{i}_{k}_{r}_{s}")
                    modelo.addConstr(z[i, k, r, s] <= y[k, s], name=f"lin2_{i}_{k}_{r}_{s}")
                    modelo.addConstr(
                        z[i, k, r, s] >= x[i, r] + y[k, s] - 1,
                        name=f"lin3_{i}_{k}_{r}_{s}"
                    )

    # --------------------------------------------------
    # 9. Resolver
    # --------------------------------------------------

    modelo.optimize()

    status_texto = nombre_status_gurobi(modelo.Status)

    if modelo.Status != GRB.OPTIMAL:
        return {
            "status": status_texto,
            "objetivo": None,
            "asignacion_b1": {},
            "asignacion_b2": {},
        }

    # --------------------------------------------------
    # 10. Extraer solución
    # --------------------------------------------------

    asignacion_b1 = {i: r for i in I for r in R if x[i, r].X > 0.5}
    asignacion_b2 = {k: r for k in K for r in R if y[k, r].X > 0.5}

    return {
        "status": status_texto,
        "objetivo": modelo.ObjVal,
        "asignacion_b1": asignacion_b1,
        "asignacion_b2": asignacion_b2,
    }


def imprimir_resultado(resultado):
    print()
    print("=" * 60)
    print("RESULTADO MODELO 3")
    print("=" * 60)
    print(f"Status: {resultado['status']}")

    if resultado["objetivo"] is not None:
        print(f"Objetivo: {resultado['objetivo']}")

    print()
    print("Asignación bloque 1:")
    for curso, sala in resultado["asignacion_b1"].items():
        print(f"  {curso} -> {sala}")

    print()
    print("Asignación bloque 2:")
    for curso, sala in resultado["asignacion_b2"].items():
        print(f"  {curso} -> {sala}")

    print("=" * 60)


def mostrar_caso_demo_modelo_3(nombre_test):
    """
    Resuelve el caso demostrativo del Modelo 3 y muestra:
    - status y objetivo
    - asignación con edificio y capacidad
    - validación de capacidad
    - resumen de movilidad desagregado por tipo de transición
    """

    ROOT = Path(__file__).resolve().parents[1]
    DATA_MODELO_3 = ROOT / "data" / "modelo3"

    carpeta_test = DATA_MODELO_3 / nombre_test

    resultado = resolver_modelo_3(carpeta_test, mostrar_output=False)

    cursos_b1 = pd.read_csv(carpeta_test / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(carpeta_test / "cursos_b2.csv")
    salas     = pd.read_csv(carpeta_test / "salas.csv")
    flujos    = pd.read_csv(carpeta_test / "flujos.csv")
    gamma_df  = pd.read_csv(carpeta_test / "gamma.csv")

    import json
    with open(carpeta_test / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    objetivo_esperado = metadata["expected_obj"]

    edificio_sala = dict(zip(salas["sala_id"], salas["edificio"]))

    print("Test:", nombre_test)
    print("Status obtenido:", resultado["status"])
    print("Objetivo esperado:", objetivo_esperado)
    print("Objetivo obtenido:", resultado["objetivo"])

    if resultado["status"] == "OPTIMAL":
        status_ok   = True
        objetivo_ok = abs(resultado["objetivo"] - objetivo_esperado) <= 1e-6
        print()
        print("Status correcto:", status_ok)
        print("Objetivo correcto:", objetivo_ok)

    # --------------------------------------------------
    # Tabla asignación bloque 1
    # --------------------------------------------------

    tabla_b1 = pd.DataFrame(
        list(resultado["asignacion_b1"].items()),
        columns=["curso_b1", "sala_asignada"]
    )
    tabla_b1 = tabla_b1.merge(cursos_b1, left_on="curso_b1", right_on="curso_id", how="left")
    tabla_b1 = tabla_b1.merge(salas,     left_on="sala_asignada", right_on="sala_id", how="left")
    tabla_b1 = tabla_b1.rename(columns={
        "tamano":    "estudiantes",
        "capacidad": "cap_sala",
        "edificio":  "edificio_sala",
    })
    tabla_b1 = tabla_b1[["curso_b1", "estudiantes", "sala_asignada", "edificio_sala", "cap_sala"]]
    tabla_b1["cumple_capacidad"] = tabla_b1["estudiantes"] <= tabla_b1["cap_sala"]

    # --------------------------------------------------
    # Tabla asignación bloque 2
    # --------------------------------------------------

    tabla_b2 = pd.DataFrame(
        list(resultado["asignacion_b2"].items()),
        columns=["curso_b2", "sala_asignada"]
    )
    tabla_b2 = tabla_b2.merge(cursos_b2, left_on="curso_b2", right_on="curso_id", how="left")
    tabla_b2 = tabla_b2.merge(salas,     left_on="sala_asignada", right_on="sala_id", how="left")
    tabla_b2 = tabla_b2.rename(columns={
        "tamano":    "estudiantes",
        "capacidad": "cap_sala",
        "edificio":  "edificio_sala",
    })
    tabla_b2 = tabla_b2[["curso_b2", "estudiantes", "sala_asignada", "edificio_sala", "cap_sala"]]
    tabla_b2["cumple_capacidad"] = tabla_b2["estudiantes"] <= tabla_b2["cap_sala"]

    print()
    print("Asignación bloque 1:")
    display(tabla_b1)

    print("Asignación bloque 2:")
    display(tabla_b2)

    capacidad_ok = tabla_b1["cumple_capacidad"].all() and tabla_b2["cumple_capacidad"].all()
    print("Todas las capacidades se respetan:", capacidad_ok)

    # --------------------------------------------------
    # Resumen de movilidad desagregado por tipo de transición
    # --------------------------------------------------

    gamma = {}
    for _, fila in gamma_df.iterrows():
        gamma[(fila["edificio_origen"], fila["edificio_destino"])] = fila["gamma"]

    misma_sala        = 0
    mismo_edificio    = 0
    distinto_edificio = 0
    costo_calculado   = 0.0

    for _, fila in flujos.iterrows():
        i     = fila["curso_b1"]
        k     = fila["curso_b2"]
        flujo = fila["flujo"]

        sala_i = resultado["asignacion_b1"].get(i)
        sala_k = resultado["asignacion_b2"].get(k)

        if sala_i is None or sala_k is None:
            continue

        e_i = edificio_sala[sala_i]
        e_k = edificio_sala[sala_k]

        if sala_i == sala_k:
            misma_sala += flujo
            costo_calculado += 0
        elif e_i == e_k:
            mismo_edificio += flujo
            costo_calculado += flujo * 1
        else:
            distinto_edificio += flujo
            costo_calculado += flujo * gamma[(e_i, e_k)]

    flujo_total = misma_sala + mismo_edificio + distinto_edificio

    resumen = pd.DataFrame([{
        "flujo_total":               flujo_total,
        "misma_sala (costo 0)":      misma_sala,
        "mismo_edificio (costo 1)":  mismo_edificio,
        "distinto_edificio (costo γ)": distinto_edificio,
        "costo_calculado":           costo_calculado,
    }])

    print()
    print("Resumen de movilidad por tipo de transición:")
    display(resumen)

    return resultado


# --------------------------------------------------
# Para probar desde terminal
# --------------------------------------------------

if __name__ == "__main__":
    carpeta = "data/modelo3/M3_T02_mismo_edificio_costo_1"
    resultado = resolver_modelo_3(carpeta)
    imprimir_resultado(resultado)
