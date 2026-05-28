import pandas as pd
from pathlib import Path


# ============================================================
# validar_data.py  (extensión para Modelo 3)
#
# Agrega la función validar_instancia_modelo_3, que extiende
# la validación del Modelo 2 con chequeos sobre edificios y gamma.
# ============================================================


def validar_columnas(df, columnas_necesarias, nombre_archivo):
    for columna in columnas_necesarias:
        if columna not in df.columns:
            raise ValueError(f"Error en {nombre_archivo}: falta la columna '{columna}'")


def validar_no_negativos(df, columna, nombre_archivo):
    if (df[columna] < 0).any():
        raise ValueError(
            f"Error en {nombre_archivo}: la columna '{columna}' tiene valores negativos"
        )


def validar_instancia_modelo_2(carpeta_test):
    """
    Valida una carpeta de datos sintéticos del Modelo 2.
    (Sin cambios respecto al original.)
    """

    carpeta_test = Path(carpeta_test)

    cursos_b1 = pd.read_csv(carpeta_test / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(carpeta_test / "cursos_b2.csv")
    salas     = pd.read_csv(carpeta_test / "salas.csv")
    flujos    = pd.read_csv(carpeta_test / "flujos.csv")
    libres    = pd.read_csv(carpeta_test / "libres.csv")

    validar_columnas(cursos_b1, ["curso_id", "tamano"], "cursos_b1.csv")
    validar_columnas(cursos_b2, ["curso_id", "tamano"], "cursos_b2.csv")
    validar_columnas(salas,     ["sala_id", "capacidad"], "salas.csv")
    validar_columnas(flujos,    ["curso_b1", "curso_b2", "flujo"], "flujos.csv")
    validar_columnas(libres,    ["curso_b1", "libres"], "libres.csv")

    validar_no_negativos(cursos_b1, "tamano",   "cursos_b1.csv")
    validar_no_negativos(cursos_b2, "tamano",   "cursos_b2.csv")
    validar_no_negativos(salas,     "capacidad","salas.csv")
    validar_no_negativos(flujos,    "flujo",    "flujos.csv")
    validar_no_negativos(libres,    "libres",   "libres.csv")

    I   = list(cursos_b1["curso_id"])
    K   = list(cursos_b2["curso_id"])
    R   = list(salas["sala_id"])

    n   = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    m   = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))
    cap = dict(zip(salas["sala_id"],      salas["capacidad"]))

    F = flujos.pivot(index="curso_b1", columns="curso_b2", values="flujo")
    F = F.reindex(index=I, columns=K).fillna(0)

    f_L = dict(zip(libres["curso_b1"], libres["libres"]))

    for i in I:
        total = F.loc[i].sum() + f_L[i]
        if total != n[i]:
            raise ValueError(
                f"Error en curso {i} del bloque 1:\n"
                f"  suma flujos + libres = {total}, tamaño declarado = {n[i]}"
            )

    for k in K:
        suma = F[k].sum()
        if suma != m[k]:
            raise ValueError(
                f"Error en curso {k} del bloque 2:\n"
                f"  suma flujos que llegan = {suma}, tamaño declarado = {m[k]}"
            )

    total_b1     = sum(n.values())
    total_b2     = sum(m.values())
    total_libres = sum(f_L.values())

    if total_b1 != total_b2 + total_libres:
        raise ValueError(
            "Error de consistencia global:\n"
            f"  total b1={total_b1}, total b2={total_b2}, libres={total_libres}"
        )

    for i in I:
        if not any(n[i] <= cap[r] for r in R):
            print(f"ADVERTENCIA: curso {i} (b1, tamaño {n[i]}) no cabe en ninguna sala.")

    for k in K:
        if not any(m[k] <= cap[r] for r in R):
            print(f"ADVERTENCIA: curso {k} (b2, tamaño {m[k]}) no cabe en ninguna sala.")

    if len(R) < len(I):
        print("ADVERTENCIA: hay menos salas que cursos del bloque 1.")
    if len(R) < len(K):
        print("ADVERTENCIA: hay menos salas que cursos del bloque 2.")

    print("Validación completada correctamente.")
    print()
    print("Resumen:")
    print(f"  Cursos bloque 1: {len(I)}")
    print(f"  Cursos bloque 2: {len(K)}")
    print(f"  Salas: {len(R)}")
    print(f"  Total estudiantes bloque 1: {total_b1}")
    print(f"  Total estudiantes bloque 2: {total_b2}")
    print(f"  Total estudiantes libres: {total_libres}")
    print(f"  Flujo total entre cursos: {int(F.values.sum())}")

    return {
        "I": I, "K": K, "R": R,
        "n": n, "m": m, "cap": cap,
        "F": F, "f_L": f_L,
        "cursos_b1": cursos_b1, "cursos_b2": cursos_b2,
        "salas": salas, "flujos": flujos, "libres": libres,
    }


def validar_instancia_modelo_3(carpeta_test):
    """
    Valida una carpeta de datos sintéticos del Modelo 3.

    Extiende la validación del Modelo 2 con:
    - salas.csv debe tener columna 'edificio'
    - gamma.csv debe existir y ser completo para todos los pares de edificios
    - los valores de gamma entre distintos edificios deben ser >= 1
    - gamma de un edificio consigo mismo debe ser 1

    Archivos esperados:
    - cursos_b1.csv, cursos_b2.csv, salas.csv, flujos.csv, libres.csv  (igual que M2)
    - gamma.csv  (nuevo en M3)
    """

    carpeta_test = Path(carpeta_test)

    # --------------------------------------------------
    # 1. Leer y validar archivos heredados del Modelo 2
    # --------------------------------------------------

    cursos_b1 = pd.read_csv(carpeta_test / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(carpeta_test / "cursos_b2.csv")
    salas     = pd.read_csv(carpeta_test / "salas.csv")
    flujos    = pd.read_csv(carpeta_test / "flujos.csv")
    libres    = pd.read_csv(carpeta_test / "libres.csv")

    validar_columnas(cursos_b1, ["curso_id", "tamano"], "cursos_b1.csv")
    validar_columnas(cursos_b2, ["curso_id", "tamano"], "cursos_b2.csv")
    validar_columnas(flujos,    ["curso_b1", "curso_b2", "flujo"], "flujos.csv")
    validar_columnas(libres,    ["curso_b1", "libres"], "libres.csv")

    # --------------------------------------------------
    # 2. salas.csv ahora requiere columna 'edificio'
    # --------------------------------------------------

    validar_columnas(salas, ["sala_id", "capacidad", "edificio"], "salas.csv")

    validar_no_negativos(cursos_b1, "tamano",    "cursos_b1.csv")
    validar_no_negativos(cursos_b2, "tamano",    "cursos_b2.csv")
    validar_no_negativos(salas,     "capacidad", "salas.csv")
    validar_no_negativos(flujos,    "flujo",     "flujos.csv")
    validar_no_negativos(libres,    "libres",    "libres.csv")

    # Ninguna sala puede tener edificio vacío
    if salas["edificio"].isnull().any() or (salas["edificio"] == "").any():
        raise ValueError("Error en salas.csv: hay salas sin edificio asignado.")

    # --------------------------------------------------
    # 3. Leer y validar gamma.csv
    # --------------------------------------------------

    ruta_gamma = carpeta_test / "gamma.csv"

    if not ruta_gamma.exists():
        raise FileNotFoundError("Error: no se encontró el archivo gamma.csv.")

    gamma_df = pd.read_csv(ruta_gamma)

    validar_columnas(gamma_df, ["edificio_origen", "edificio_destino", "gamma"], "gamma.csv")

    if (gamma_df["gamma"] < 0).any():
        raise ValueError("Error en gamma.csv: hay valores de gamma negativos.")

    # Verificar que gamma está definido para todos los pares de edificios
    edificios = sorted(salas["edificio"].unique())

    gamma = {}
    for _, fila in gamma_df.iterrows():
        gamma[(fila["edificio_origen"], fila["edificio_destino"])] = fila["gamma"]

    for e1 in edificios:
        for e2 in edificios:
            if (e1, e2) not in gamma:
                raise ValueError(
                    f"Error en gamma.csv: falta el par ({e1}, {e2})."
                )

    # gamma de un edificio consigo mismo debe ser 1
    for e in edificios:
        if gamma[(e, e)] != 1:
            raise ValueError(
                f"Error en gamma.csv: gamma({e}, {e}) = {gamma[(e, e)]}, debería ser 1."
            )

    # gamma entre distintos edificios debe ser >= 1
    for e1 in edificios:
        for e2 in edificios:
            if e1 != e2 and gamma[(e1, e2)] < 1:
                raise ValueError(
                    f"Error en gamma.csv: gamma({e1}, {e2}) = {gamma[(e1, e2)]} < 1."
                )

    # --------------------------------------------------
    # 4. Construir conjuntos y parámetros
    # --------------------------------------------------

    I   = list(cursos_b1["curso_id"])
    K   = list(cursos_b2["curso_id"])
    R   = list(salas["sala_id"])

    n   = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    m   = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))
    cap = dict(zip(salas["sala_id"],      salas["capacidad"]))
    ed  = dict(zip(salas["sala_id"],      salas["edificio"]))   # edificio de cada sala

    F = flujos.pivot(index="curso_b1", columns="curso_b2", values="flujo")
    F = F.reindex(index=I, columns=K).fillna(0)

    f_L = dict(zip(libres["curso_b1"], libres["libres"]))

    # --------------------------------------------------
    # 5. Conservación de estudiantes (igual que Modelo 2)
    # --------------------------------------------------

    for i in I:
        total = F.loc[i].sum() + f_L[i]
        if total != n[i]:
            raise ValueError(
                f"Error en curso {i} del bloque 1:\n"
                f"  suma flujos + libres = {total}, tamaño declarado = {n[i]}"
            )

    for k in K:
        suma = F[k].sum()
        if suma != m[k]:
            raise ValueError(
                f"Error en curso {k} del bloque 2:\n"
                f"  suma flujos que llegan = {suma}, tamaño declarado = {m[k]}"
            )

    total_b1     = sum(n.values())
    total_b2     = sum(m.values())
    total_libres = sum(f_L.values())

    if total_b1 != total_b2 + total_libres:
        raise ValueError(
            "Error de consistencia global:\n"
            f"  total b1={total_b1}, total b2={total_b2}, libres={total_libres}"
        )

    # --------------------------------------------------
    # 6. Advertencias de capacidad (igual que Modelo 2)
    # --------------------------------------------------

    for i in I:
        if not any(n[i] <= cap[r] for r in R):
            print(f"ADVERTENCIA: curso {i} (b1, tamaño {n[i]}) no cabe en ninguna sala.")

    for k in K:
        if not any(m[k] <= cap[r] for r in R):
            print(f"ADVERTENCIA: curso {k} (b2, tamaño {m[k]}) no cabe en ninguna sala.")

    if len(R) < len(I):
        print("ADVERTENCIA: hay menos salas que cursos del bloque 1.")
    if len(R) < len(K):
        print("ADVERTENCIA: hay menos salas que cursos del bloque 2.")

    # --------------------------------------------------
    # 7. Resumen
    # --------------------------------------------------

    print("Validación completada correctamente.")
    print()
    print("Resumen:")
    print(f"  Cursos bloque 1: {len(I)}")
    print(f"  Cursos bloque 2: {len(K)}")
    print(f"  Salas: {len(R)}")
    print(f"  Edificios: {edificios}")
    print(f"  Total estudiantes bloque 1: {total_b1}")
    print(f"  Total estudiantes bloque 2: {total_b2}")
    print(f"  Total estudiantes libres: {total_libres}")
    print(f"  Flujo total entre cursos: {int(F.values.sum())}")

    return {
        "I": I, "K": K, "R": R,
        "n": n, "m": m, "cap": cap,
        "ed": ed,
        "gamma": gamma,
        "edificios": edificios,
        "F": F, "f_L": f_L,
        "cursos_b1": cursos_b1, "cursos_b2": cursos_b2,
        "salas": salas, "flujos": flujos, "libres": libres,
        "gamma_df": gamma_df,
    }


def validar_todas_las_carpetas(carpeta_base, modelo=3):
    """
    Valida todas las carpetas dentro de carpeta_base.
    modelo=2 usa validar_instancia_modelo_2, modelo=3 usa validar_instancia_modelo_3.
    """

    carpeta_base = Path(carpeta_base)
    fn = validar_instancia_modelo_3 if modelo == 3 else validar_instancia_modelo_2

    carpetas_tests = sorted(c for c in carpeta_base.iterdir() if c.is_dir())

    if not carpetas_tests:
        print("No se encontraron carpetas de tests.")
        return

    print("Validando carpetas de tests...")
    print("=" * 60)

    ok = 0
    errores = 0

    for carpeta_test in carpetas_tests:
        print()
        print(f"Validando: {carpeta_test.name}")
        print("-" * 60)

        try:
            fn(carpeta_test)
            print(f"RESULTADO: OK - {carpeta_test.name}")
            ok += 1
        except Exception as error:
            print(f"RESULTADO: ERROR - {carpeta_test.name}")
            print(error)
            errores += 1

    print()
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Tests validados correctamente: {ok}")
    print(f"Tests con error: {errores}")
    print(f"Total revisados: {ok + errores}")


if __name__ == "__main__":
    validar_todas_las_carpetas("data/modelo3", modelo=3)
