from pathlib import Path
import json
import pandas as pd

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError as exc:
    raise ImportError(
        "No se pudo importar gurobipy. Verifica que Gurobi y gurobipy estén instalados."
    ) from exc


# ============================================================
# Configuración general
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]


# ============================================================
# Import opcional del validador
# ============================================================

try:
    from .validar_data_modelo_4 import validar_instancia_modelo_4
except ImportError:
    try:
        from validar_data_modelo_4 import validar_instancia_modelo_4
    except ImportError:
        validar_instancia_modelo_4 = None


# ============================================================
# Utilidades
# ============================================================


def resolver_ruta(carpeta_test):
    """
    Permite entregar rutas absolutas o relativas.
    Ejemplos válidos:
    - data/modelo4/M4_T01_misma_sala_costo_0
    - ./data/modelo4/M4_T01_misma_sala_costo_0
    """
    ruta = Path(carpeta_test)

    if ruta.exists():
        return ruta

    ruta_desde_root = ROOT_DIR / ruta

    if ruta_desde_root.exists():
        return ruta_desde_root

    raise FileNotFoundError(f"No existe la carpeta de instancia: {carpeta_test}")


def leer_csv(ruta):
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {ruta}")
    return pd.read_csv(ruta)


def leer_metadata(carpeta):
    ruta = carpeta / "metadata.json"

    if not ruta.exists():
        return {}

    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def normalizar_columna_tamano(df):
    """
    Permite usar 'tamano' o 'tamaño'.
    Internamente se trabaja con 'tamano'.
    """
    df = df.copy()

    if "tamano" in df.columns:
        return df

    if "tamaño" in df.columns:
        return df.rename(columns={"tamaño": "tamano"})

    raise ValueError("El archivo de cursos debe tener columna 'tamano' o 'tamaño'.")


def convertir_ids_a_string(data):
    """
    Evita problemas si pandas interpreta algún ID como número.
    """
    data["cursos_b1"]["curso_id"] = data["cursos_b1"]["curso_id"].astype(str)
    data["cursos_b2"]["curso_id"] = data["cursos_b2"]["curso_id"].astype(str)

    data["salas"]["sala_id"] = data["salas"]["sala_id"].astype(str)
    data["salas"]["edificio"] = data["salas"]["edificio"].astype(str)

    data["flujos"]["curso_b1"] = data["flujos"]["curso_b1"].astype(str)
    data["flujos"]["curso_b2"] = data["flujos"]["curso_b2"].astype(str)

    data["libres"]["curso_b1"] = data["libres"]["curso_b1"].astype(str)
    data["entrantes"]["curso_b2"] = data["entrantes"]["curso_b2"].astype(str)

    data["costos"]["sala_origen"] = data["costos"]["sala_origen"].astype(str)
    data["costos"]["sala_destino"] = data["costos"]["sala_destino"].astype(str)

    return data


def cargar_datos_modelo_4(carpeta_test):
    carpeta = resolver_ruta(carpeta_test)

    cursos_b1 = normalizar_columna_tamano(leer_csv(carpeta / "cursos_b1.csv"))
    cursos_b2 = normalizar_columna_tamano(leer_csv(carpeta / "cursos_b2.csv"))
    salas = leer_csv(carpeta / "salas.csv")
    flujos = leer_csv(carpeta / "flujos.csv")
    libres = leer_csv(carpeta / "libres.csv")
    entrantes = leer_csv(carpeta / "entrantes.csv")
    costos = leer_csv(carpeta / "costos_sala_sala.csv")
    metadata = leer_metadata(carpeta)

    data = {
        "carpeta": carpeta,
        "cursos_b1": cursos_b1,
        "cursos_b2": cursos_b2,
        "salas": salas,
        "flujos": flujos,
        "libres": libres,
        "entrantes": entrantes,
        "costos": costos,
        "metadata": metadata,
    }

    data = convertir_ids_a_string(data)

    return data


def nombre_status_gurobi(status_code):
    mapa = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }

    return mapa.get(status_code, f"STATUS_{status_code}")


def construir_diccionarios(data):
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    salas = data["salas"]
    flujos = data["flujos"]
    costos = data["costos"]

    I = cursos_b1["curso_id"].tolist()
    K = cursos_b2["curso_id"].tolist()
    R = salas["sala_id"].tolist()

    n = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    m = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))
    cap = dict(zip(salas["sala_id"], salas["capacidad"]))
    edificio = dict(zip(salas["sala_id"], salas["edificio"]))

    # Flujo f_ik. Se acumula por si el CSV trae pares repetidos.
    F = {}

    for _, fila in flujos.iterrows():
        i = fila["curso_b1"]
        k = fila["curso_b2"]
        flujo = float(fila["flujo"])

        F[(i, k)] = F.get((i, k), 0.0) + flujo

    # Pares de cursos que realmente generan costo.
    pares_flujo = [(i, k) for (i, k), valor in F.items() if valor > 0]

    # Costos sala-sala c_rs.
    c = {}

    for _, fila in costos.iterrows():
        r = fila["sala_origen"]
        s = fila["sala_destino"]
        costo = float(fila["costo"])

        c[(r, s)] = costo

    return I, K, R, n, m, cap, edificio, F, pares_flujo, c


def construir_tablas_resultado(I, K, R, n, m, cap, edificio, F, c, x, y):
    asignacion_b1 = {}
    asignacion_b2 = {}

    for i in I:
        for r in R:
            if x[i, r].X > 0.5:
                asignacion_b1[i] = r

    for k in K:
        for s in R:
            if y[k, s].X > 0.5:
                asignacion_b2[k] = s

    filas_asignacion_b1 = []

    for i in I:
        r = asignacion_b1[i]
        filas_asignacion_b1.append(
            {
                "curso_b1": i,
                "tamano": n[i],
                "sala": r,
                "capacidad_sala": cap[r],
                "edificio": edificio[r],
            }
        )

    filas_asignacion_b2 = []

    for k in K:
        s = asignacion_b2[k]
        filas_asignacion_b2.append(
            {
                "curso_b2": k,
                "tamano": m[k],
                "sala": s,
                "capacidad_sala": cap[s],
                "edificio": edificio[s],
            }
        )

    filas_salas = []

    for r in R:
        curso_b1 = next((i for i in I if asignacion_b1[i] == r), None)
        curso_b2 = next((k for k in K if asignacion_b2[k] == r), None)

        filas_salas.append(
            {
                "sala": r,
                "capacidad": cap[r],
                "edificio": edificio[r],
                "curso_b1": curso_b1 if curso_b1 is not None else "—",
                "tamano_b1": n[curso_b1] if curso_b1 is not None else "—",
                "curso_b2": curso_b2 if curso_b2 is not None else "—",
                "tamano_b2": m[curso_b2] if curso_b2 is not None else "—",
            }
        )

    filas_movimientos = []

    for (i, k), flujo in F.items():
        if flujo <= 0:
            continue

        r = asignacion_b1[i]
        s = asignacion_b2[k]
        costo_unitario = c[(r, s)]
        costo_total = flujo * costo_unitario

        filas_movimientos.append(
            {
                "curso_b1": i,
                "sala_origen": r,
                "curso_b2": k,
                "sala_destino": s,
                "flujo": flujo,
                "costo_unitario": costo_unitario,
                "costo_total": costo_total,
            }
        )

    df_asignacion_b1 = pd.DataFrame(filas_asignacion_b1)
    df_asignacion_b2 = pd.DataFrame(filas_asignacion_b2)
    df_salas = pd.DataFrame(filas_salas)
    df_movimientos = pd.DataFrame(filas_movimientos)

    return {
        "asignacion_b1": asignacion_b1,
        "asignacion_b2": asignacion_b2,
        "df_asignacion_b1": df_asignacion_b1,
        "df_asignacion_b2": df_asignacion_b2,
        "df_salas": df_salas,
        "df_movimientos": df_movimientos,
    }


# ============================================================
# Resolución del Modelo 4
# ============================================================


def resolver_modelo_4(
    carpeta_test,
    mostrar_output=False,
    validar=True,
    time_limit=None,
    calcular_iis=False,
):
    """
    Resuelve una instancia del Modelo 4 usando Gurobi.

    Parámetros
    ----------
    carpeta_test:
        Ruta a la carpeta de la instancia.
    mostrar_output:
        Si True, muestra el output de Gurobi.
    validar:
        Si True, ejecuta validar_instancia_modelo_4 antes de resolver.
    time_limit:
        Límite de tiempo opcional en segundos.
    calcular_iis:
        Si True y el modelo es INFEASIBLE, calcula un IIS y lo guarda en la carpeta.

    Retorna
    -------
    dict con:
        - status
        - objetivo
        - asignaciones
        - tablas de resultados
        - modelo gurobi
    """

    carpeta = resolver_ruta(carpeta_test)

    if validar:
        if validar_instancia_modelo_4 is None:
            raise ImportError(
                "No se pudo importar validar_instancia_modelo_4. "
                "Verifica que exista src/validar_data_modelo_4.py."
            )

        validar_instancia_modelo_4(carpeta)

    data = cargar_datos_modelo_4(carpeta)

    I, K, R, n, m, cap, edificio, F, pares_flujo, c = construir_diccionarios(data)

    # ========================================================
    # Crear modelo
    # ========================================================

    model = gp.Model("modelo_4_costos_detallados_sala_sala")

    if not mostrar_output:
        model.Params.OutputFlag = 0

    if time_limit is not None:
        model.Params.TimeLimit = time_limit

    # ========================================================
    # Variables de decisión
    # ========================================================

    # x[i,r] = 1 si el curso i del bloque 1 se asigna a la sala r
    x = model.addVars(I, R, vtype=GRB.BINARY, name="x")

    # y[k,s] = 1 si el curso k del bloque 2 se asigna a la sala s
    y = model.addVars(K, R, vtype=GRB.BINARY, name="y")

    # z[i,k,r,s] = 1 si i está en r y k está en s
    # Solo se crean z para pares (i,k) con flujo positivo.
    z = {}

    for i, k in pares_flujo:
        for r in R:
            for s in R:
                z[i, k, r, s] = model.addVar(
                    vtype=GRB.BINARY, name=f"z[{i},{k},{r},{s}]"
                )

    model.update()

    # ========================================================
    # Función objetivo
    # ========================================================

    model.setObjective(
        gp.quicksum(
            F[(i, k)] * c[(r, s)] * z[i, k, r, s]
            for (i, k) in pares_flujo
            for r in R
            for s in R
        ),
        GRB.MINIMIZE,
    )

    # ========================================================
    # Restricciones
    # ========================================================

    # Cada curso del bloque 1 se asigna exactamente a una sala.
    for i in I:
        model.addConstr(
            gp.quicksum(x[i, r] for r in R) == 1, name=f"asignacion_b1[{i}]"
        )

    # Cada curso del bloque 2 se asigna exactamente a una sala.
    for k in K:
        model.addConstr(
            gp.quicksum(y[k, s] for s in R) == 1, name=f"asignacion_b2[{k}]"
        )

    # Cada sala puede tener a lo más un curso del bloque 1.
    for r in R:
        model.addConstr(gp.quicksum(x[i, r] for i in I) <= 1, name=f"ocupacion_b1[{r}]")

    # Cada sala puede tener a lo más un curso del bloque 2.
    for s in R:
        model.addConstr(gp.quicksum(y[k, s] for k in K) <= 1, name=f"ocupacion_b2[{s}]")

    # Capacidad suficiente para cursos del bloque 1.
    # n[i] incluye estudiantes que luego pueden salir/liberarse.
    for i in I:
        for r in R:
            model.addConstr(
                float(n[i]) * x[i, r] <= float(cap[r]), name=f"capacidad_b1[{i},{r}]"
            )

    # Capacidad suficiente para cursos del bloque 2.
    # m[k] incluye estudiantes que llegan desde fuera.
    for k in K:
        for s in R:
            model.addConstr(
                float(m[k]) * y[k, s] <= float(cap[s]), name=f"capacidad_b2[{k},{s}]"
            )

    # Linealización z = x * y.
    for i, k in pares_flujo:
        for r in R:
            for s in R:
                model.addConstr(z[i, k, r, s] <= x[i, r], name=f"lin1[{i},{k},{r},{s}]")

                model.addConstr(z[i, k, r, s] <= y[k, s], name=f"lin2[{i},{k},{r},{s}]")

                model.addConstr(
                    z[i, k, r, s] >= x[i, r] + y[k, s] - 1,
                    name=f"lin3[{i},{k},{r},{s}]",
                )

    # ========================================================
    # Resolver
    # ========================================================

    model.optimize()

    status = nombre_status_gurobi(model.Status)

    resultado = {
        "status": status,
        "objetivo": None,
        "carpeta": carpeta,
        "metadata": data["metadata"],
        "modelo": model,
        "x": x,
        "y": y,
        "z": z,
    }

    # ========================================================
    # Si es infactible
    # ========================================================

    if model.Status == GRB.INFEASIBLE:
        if calcular_iis:
            model.computeIIS()
            ruta_iis = carpeta / "modelo_4_iis.ilp"
            model.write(str(ruta_iis))
            resultado["iis_path"] = ruta_iis

        return resultado

    # ========================================================
    # Si no hay solución disponible
    # ========================================================

    if model.SolCount == 0:
        return resultado

    # ========================================================
    # Extraer solución
    # ========================================================

    resultado["objetivo"] = model.ObjVal

    tablas = construir_tablas_resultado(
        I=I,
        K=K,
        R=R,
        n=n,
        m=m,
        cap=cap,
        edificio=edificio,
        F=F,
        c=c,
        x=x,
        y=y,
    )

    resultado.update(tablas)

    return resultado


# ============================================================
# Impresión simple de resultados
# ============================================================


def imprimir_resultado_modelo_4(resultado):
    print("========================================")
    print("Resultado Modelo 4")
    print("========================================")
    print(f"Carpeta: {resultado['carpeta'].name}")
    print(f"Status: {resultado['status']}")

    if resultado["objetivo"] is not None:
        print(f"Costo óptimo: {resultado['objetivo']}")

    metadata = resultado.get("metadata", {})

    if metadata:
        print(f"Status esperado: {metadata.get('status_esperado')}")
        print(f"Costo esperado: {metadata.get('costo_esperado')}")

    if resultado["status"] == "INFEASIBLE":
        print("La instancia es infactible.")
        if "iis_path" in resultado:
            print(f"IIS guardado en: {resultado['iis_path']}")
        return

    if resultado["objetivo"] is None:
        print("No hay solución disponible.")
        return

    print("\nAsignación por sala:")
    print(resultado["df_salas"].to_string(index=False))

    print("\nMovimientos con costo:")
    print(resultado["df_movimientos"].to_string(index=False))


# ============================================================
# Ejecución directa de prueba
# ============================================================

if __name__ == "__main__":
    instancia = ROOT_DIR / "data" / "modelo4" / "M4_T01_misma_sala_costo_0"

    res = resolver_modelo_4(instancia, mostrar_output=False, validar=True)

    imprimir_resultado_modelo_4(res)
