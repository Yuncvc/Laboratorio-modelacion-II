from pathlib import Path
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

from validar_data import validar_instancia_modelo_2
from IPython.display import display


def leer_costos(carpeta_test):
    """
    Lee el archivo costos.csv y lo convierte en un diccionario.

    El diccionario tendrá esta forma:
        c[r, s] = costo de ir desde sala r hacia sala s
    """

    carpeta_test = Path(carpeta_test)

    costos = pd.read_csv(carpeta_test / "costos.csv")

    c = {}

    for _, fila in costos.iterrows():
        sala_origen = fila["sala_origen"]
        sala_destino = fila["sala_destino"]
        costo = fila["costo"]

        c[sala_origen, sala_destino] = costo

    return c


def nombre_status_gurobi(status):
    """
    Convierte el código numérico de Gurobi en un texto más entendible.
    """

    if status == GRB.OPTIMAL:
        return "OPTIMAL"

    if status == GRB.INFEASIBLE:
        return "INFEASIBLE"

    if status == GRB.UNBOUNDED:
        return "UNBOUNDED"

    if status == GRB.TIME_LIMIT:
        return "TIME_LIMIT"

    return f"OTRO_STATUS_{status}"


def resolver_modelo_2(carpeta_test, mostrar_output=True):
    """
    Resuelve una instancia del Modelo 2.

    Entrada:
        carpeta_test:
            ruta a una carpeta que contiene:
            - cursos_b1.csv
            - cursos_b2.csv
            - salas.csv
            - flujos.csv
            - libres.csv
            - costos.csv

    Salida:
        Un diccionario con:
            - status
            - objetivo
            - asignacion_b1
            - asignacion_b2
    """

    # --------------------------------------------------
    # 1. Validar y cargar datos
    # --------------------------------------------------

    datos = validar_instancia_modelo_2(carpeta_test)

    I = datos["I"]  # Cursos bloque 1  # noqa: E741
    K = datos["K"]  # Cursos bloque 2
    R = datos["R"]  # Salas

    n = datos["n"]  # Tamaños cursos bloque 1
    m = datos["m"]  # Tamaños cursos bloque 2
    cap = datos["cap"]  # Capacidades salas
    F = datos["F"]  # Matriz de flujos

    c = leer_costos(carpeta_test)

    # --------------------------------------------------
    # 2. Crear modelo
    # --------------------------------------------------

    modelo = gp.Model("Modelo_2_capacidades_heterogeneas")

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
    # Minimizar:
    # sum_i sum_k sum_r sum_s F[i,k] * c[r,s] * z[i,k,r,s]

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
    # Cada curso del bloque 1 va a exactamente una sala.

    for i in I:
        modelo.addConstr(
            gp.quicksum(x[i, r] for r in R) == 1, name=f"asignacion_b1_{i}"
        )

    # Cada curso del bloque 2 va a exactamente una sala.

    for k in K:
        modelo.addConstr(
            gp.quicksum(y[k, r] for r in R) == 1, name=f"asignacion_b2_{k}"
        )

    # --------------------------------------------------
    # 6. Restricciones de ocupación única
    # --------------------------------------------------
    # Cada sala recibe a lo más un curso en el bloque 1.

    for r in R:
        modelo.addConstr(gp.quicksum(x[i, r] for i in I) <= 1, name=f"ocupacion_b1_{r}")

    # Cada sala recibe a lo más un curso en el bloque 2.

    for r in R:
        modelo.addConstr(gp.quicksum(y[k, r] for k in K) <= 1, name=f"ocupacion_b2_{r}")

    # --------------------------------------------------
    # 7. Restricciones de capacidad
    # --------------------------------------------------
    # Si el curso i va a sala r, entonces debe caber en la sala.

    for i in I:
        for r in R:
            modelo.addConstr(n[i] * x[i, r] <= cap[r], name=f"capacidad_b1_{i}_{r}")

    # Si el curso k va a sala r, entonces debe caber en la sala.

    for k in K:
        for r in R:
            modelo.addConstr(m[k] * y[k, r] <= cap[r], name=f"capacidad_b2_{k}_{r}")

    # --------------------------------------------------
    # 8. Linealización de z = x * y
    # --------------------------------------------------
    # z[i,k,r,s] debe valer 1 solo si:
    # x[i,r] = 1 e y[k,s] = 1

    for i in I:
        for k in K:
            for r in R:
                for s in R:
                    modelo.addConstr(
                        z[i, k, r, s] <= x[i, r], name=f"lin1_{i}_{k}_{r}_{s}"
                    )

                    modelo.addConstr(
                        z[i, k, r, s] <= y[k, s], name=f"lin2_{i}_{k}_{r}_{s}"
                    )

                    modelo.addConstr(
                        z[i, k, r, s] >= x[i, r] + y[k, s] - 1,
                        name=f"lin3_{i}_{k}_{r}_{s}",
                    )

    # --------------------------------------------------
    # 9. Resolver modelo
    # --------------------------------------------------

    modelo.optimize()

    status_texto = nombre_status_gurobi(modelo.Status)

    # --------------------------------------------------
    # 10. Si no es óptimo, devolver solo status
    # --------------------------------------------------

    if modelo.Status != GRB.OPTIMAL:
        return {
            "status": status_texto,
            "objetivo": None,
            "asignacion_b1": {},
            "asignacion_b2": {},
        }

    # --------------------------------------------------
    # 11. Extraer solución
    # --------------------------------------------------

    asignacion_b1 = {}

    for i in I:
        for r in R:
            if x[i, r].X > 0.5:
                asignacion_b1[i] = r

    asignacion_b2 = {}

    for k in K:
        for r in R:
            if y[k, r].X > 0.5:
                asignacion_b2[k] = r

    # --------------------------------------------------
    # 12. Retornar resultados
    # --------------------------------------------------

    return {
        "status": status_texto,
        "objetivo": modelo.ObjVal,
        "asignacion_b1": asignacion_b1,
        "asignacion_b2": asignacion_b2,
    }


def imprimir_resultado(resultado):
    """
    Imprime de forma simple el resultado del modelo.
    """

    print()
    print("=" * 60)
    print("RESULTADO MODELO 2")
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


def mostrar_caso_demo_modelo_2(
    nombre_test, objetivo_esperado, asignacion_esperada_b1, asignacion_esperada_b2
):
    """
    Resuelve un caso demostrativo del Modelo 2 y muestra:
    - status
    - objetivo
    - asignación obtenida
    - validación de asignación esperada
    - resumen de movilidad
    - validación de capacidad
    """

    ROOT = Path(__file__).resolve().parents[1]
    DATA_MODELO_2 = ROOT / "data" / "modelo2"

    carpeta_test = DATA_MODELO_2 / nombre_test

    resultado = resolver_modelo_2(carpeta_test, mostrar_output=False)

    cursos_b1 = pd.read_csv(carpeta_test / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(carpeta_test / "cursos_b2.csv")
    salas = pd.read_csv(carpeta_test / "salas.csv")
    flujos = pd.read_csv(carpeta_test / "flujos.csv")

    print("Test:", nombre_test)
    print("Status obtenido:", resultado["status"])
    print("Objetivo esperado:", objetivo_esperado)
    print("Objetivo obtenido:", resultado["objetivo"])

    status_ok = resultado["status"] == "OPTIMAL"
    objetivo_ok = abs(resultado["objetivo"] - objetivo_esperado) <= 1e-6

    asignacion_b1_ok = resultado["asignacion_b1"] == asignacion_esperada_b1
    asignacion_b2_ok = resultado["asignacion_b2"] == asignacion_esperada_b2

    print()
    print("Status correcto:", status_ok)
    print("Objetivo correcto:", objetivo_ok)
    print("Asignación bloque 1 correcta:", asignacion_b1_ok)
    print("Asignación bloque 2 correcta:", asignacion_b2_ok)

    # --------------------------------------------------
    # Tabla asignación bloque 1
    # --------------------------------------------------

    tabla_b1 = pd.DataFrame(
        list(resultado["asignacion_b1"].items()), columns=["curso_b1", "sala_asignada"]
    )

    tabla_b1 = tabla_b1.merge(
        cursos_b1, left_on="curso_b1", right_on="curso_id", how="left"
    )

    tabla_b1 = tabla_b1.merge(
        salas, left_on="sala_asignada", right_on="sala_id", how="left"
    )

    tabla_b1 = tabla_b1.rename(
        columns={
            "tamano": "cantidad_estudiantes_curso_b1",
            "capacidad": "capacidad_sala_asignada",
        }
    )

    tabla_b1 = tabla_b1[
        [
            "curso_b1",
            "cantidad_estudiantes_curso_b1",
            "sala_asignada",
            "capacidad_sala_asignada",
        ]
    ]

    tabla_b1["cumple_capacidad"] = (
        tabla_b1["cantidad_estudiantes_curso_b1"] <= tabla_b1["capacidad_sala_asignada"]
    )

    # --------------------------------------------------
    # Tabla asignación bloque 2
    # --------------------------------------------------

    tabla_b2 = pd.DataFrame(
        list(resultado["asignacion_b2"].items()), columns=["curso_b2", "sala_asignada"]
    )

    tabla_b2 = tabla_b2.merge(
        cursos_b2, left_on="curso_b2", right_on="curso_id", how="left"
    )

    tabla_b2 = tabla_b2.merge(
        salas, left_on="sala_asignada", right_on="sala_id", how="left"
    )

    tabla_b2 = tabla_b2.rename(
        columns={
            "tamano": "cantidad_estudiantes_curso_b2",
            "capacidad": "capacidad_sala_asignada",
        }
    )

    tabla_b2 = tabla_b2[
        [
            "curso_b2",
            "cantidad_estudiantes_curso_b2",
            "sala_asignada",
            "capacidad_sala_asignada",
        ]
    ]

    tabla_b2["cumple_capacidad"] = (
        tabla_b2["cantidad_estudiantes_curso_b2"] <= tabla_b2["capacidad_sala_asignada"]
    )

    print()
    print("Asignación bloque 1:")
    display(tabla_b1)

    print("Asignación bloque 2:")
    display(tabla_b2)

    capacidad_ok = (
        tabla_b1["cumple_capacidad"].all() and tabla_b2["cumple_capacidad"].all()
    )

    print("Todas las capacidades se respetan:", capacidad_ok)

    # --------------------------------------------------
    # Calcular movilidad inducida por la asignación
    # --------------------------------------------------

    estudiantes_no_se_mueven = 0
    estudiantes_se_mueven = 0

    for _, fila in flujos.iterrows():
        i = fila["curso_b1"]
        k = fila["curso_b2"]
        flujo = fila["flujo"]

        sala_i = resultado["asignacion_b1"][i]
        sala_k = resultado["asignacion_b2"][k]

        if sala_i == sala_k:
            estudiantes_no_se_mueven += flujo
        else:
            estudiantes_se_mueven += flujo

    flujo_total = estudiantes_no_se_mueven + estudiantes_se_mueven

    resumen_movilidad = pd.DataFrame(
        [
            {
                "flujo_total": flujo_total,
                "estudiantes_no_se_mueven": estudiantes_no_se_mueven,
                "estudiantes_se_mueven": estudiantes_se_mueven,
                "porcentaje_no_se_mueve": estudiantes_no_se_mueven / flujo_total,
                "porcentaje_se_mueve": estudiantes_se_mueven / flujo_total,
            }
        ]
    )

    print()
    print("Resumen de movilidad:")
    display(resumen_movilidad)

    return resultado


# --------------------------------------------------
# Para probar desde terminal
# --------------------------------------------------

if __name__ == "__main__":
    carpeta = "data/modelo2/M2_T02_capacidad_cambia_optimo"

    resultado = resolver_modelo_2(carpeta)

    imprimir_resultado(resultado)
