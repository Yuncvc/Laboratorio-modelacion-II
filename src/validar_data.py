import pandas as pd
from pathlib import Path


def validar_columnas(df, columnas_necesarias, nombre_archivo):
    """
    Revisa que un archivo tenga las columnas que necesitamos.
    """
    for columna in columnas_necesarias:
        if columna not in df.columns:
            raise ValueError(f"Error en {nombre_archivo}: falta la columna '{columna}'")


def validar_no_negativos(df, columna, nombre_archivo):
    """
    Revisa que una columna no tenga valores negativos.
    """
    if (df[columna] < 0).any():
        raise ValueError(
            f"Error en {nombre_archivo}: la columna '{columna}' tiene valores negativos"
        )


def validar_instancia_modelo_2(carpeta_test):
    """
    Valida una carpeta de datos sintéticos del Modelo 2.

    Archivos esperados:
    - cursos_b1.csv
    - cursos_b2.csv
    - salas.csv
    - flujos.csv
    - libres.csv
    """

    carpeta_test = Path(carpeta_test)

    # --------------------------------------------------
    # 1. Leer archivos
    # --------------------------------------------------

    cursos_b1 = pd.read_csv(carpeta_test / "cursos_b1.csv")
    cursos_b2 = pd.read_csv(carpeta_test / "cursos_b2.csv")
    salas = pd.read_csv(carpeta_test / "salas.csv")
    flujos = pd.read_csv(carpeta_test / "flujos.csv")
    libres = pd.read_csv(carpeta_test / "libres.csv")

    # --------------------------------------------------
    # 2. Revisar columnas
    # --------------------------------------------------

    validar_columnas(cursos_b1, ["curso_id", "tamano"], "cursos_b1.csv")
    validar_columnas(cursos_b2, ["curso_id", "tamano"], "cursos_b2.csv")
    validar_columnas(salas, ["sala_id", "capacidad"], "salas.csv")
    validar_columnas(flujos, ["curso_b1", "curso_b2", "flujo"], "flujos.csv")
    validar_columnas(libres, ["curso_b1", "libres"], "libres.csv")

    # --------------------------------------------------
    # 3. Revisar que no haya valores negativos
    # --------------------------------------------------

    validar_no_negativos(cursos_b1, "tamano", "cursos_b1.csv")
    validar_no_negativos(cursos_b2, "tamano", "cursos_b2.csv")
    validar_no_negativos(salas, "capacidad", "salas.csv")
    validar_no_negativos(flujos, "flujo", "flujos.csv")
    validar_no_negativos(libres, "libres", "libres.csv")

    # --------------------------------------------------
    # 4. Crear listas de cursos y salas
    # --------------------------------------------------

    I = list(cursos_b1["curso_id"])
    K = list(cursos_b2["curso_id"])
    R = list(salas["sala_id"])

    # Diccionarios:
    # n[i] = tamaño curso bloque 1
    # m[k] = tamaño curso bloque 2
    # cap[r] = capacidad sala r

    n = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    m = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))
    cap = dict(zip(salas["sala_id"], salas["capacidad"]))

    # --------------------------------------------------
    # 5. Crear matriz de flujos F
    # --------------------------------------------------
    # Las filas son cursos del bloque 1.
    # Las columnas son cursos del bloque 2.
    # Si falta un par i,k, se interpreta como flujo 0.

    F = flujos.pivot(index="curso_b1", columns="curso_b2", values="flujo")

    F = F.reindex(index=I, columns=K)
    F = F.fillna(0)

    # --------------------------------------------------
    # 6. Crear vector de estudiantes libres
    # --------------------------------------------------

    f_L = dict(zip(libres["curso_b1"], libres["libres"]))

    # --------------------------------------------------
    # 7. Validar conservación por curso del bloque 1
    # --------------------------------------------------
    # Debe cumplirse:
    # suma de flujos que salen desde i + libres de i = tamaño de i

    for i in I:
        suma_flujos = F.loc[i].sum()
        libres_i = f_L[i]
        total = suma_flujos + libres_i

        if total != n[i]:
            raise ValueError(
                f"Error en curso {i} del bloque 1:\n"
                f"  suma de flujos = {suma_flujos}\n"
                f"  estudiantes libres = {libres_i}\n"
                f"  total = {total}\n"
                f"  tamaño declarado = {n[i]}"
            )

    # --------------------------------------------------
    # 8. Validar conservación por curso del bloque 2
    # --------------------------------------------------
    # Debe cumplirse:
    # suma de flujos que llegan a k = tamaño de k

    for k in K:
        suma_flujos = F[k].sum()

        if suma_flujos != m[k]:
            raise ValueError(
                f"Error en curso {k} del bloque 2:\n"
                f"  suma de flujos que llegan = {suma_flujos}\n"
                f"  tamaño declarado = {m[k]}"
            )

    # --------------------------------------------------
    # 9. Validar consistencia global
    # --------------------------------------------------
    # Total bloque 1 = total bloque 2 + total libres

    total_b1 = sum(n.values())
    total_b2 = sum(m.values())
    total_libres = sum(f_L.values())

    if total_b1 != total_b2 + total_libres:
        raise ValueError(
            "Error de consistencia global:\n"
            f"  total bloque 1 = {total_b1}\n"
            f"  total bloque 2 = {total_b2}\n"
            f"  total libres = {total_libres}\n"
            f"  bloque 2 + libres = {total_b2 + total_libres}"
        )

    # --------------------------------------------------
    # 10. Revisiones simples de capacidad
    # --------------------------------------------------
    # Esto NO reemplaza a Gurobi.
    # Solo avisa si hay problemas obvios.

    for i in I:
        cabe_en_alguna_sala = False

        for r in R:
            if n[i] <= cap[r]:
                cabe_en_alguna_sala = True

        if not cabe_en_alguna_sala:
            print(
                f"ADVERTENCIA: el curso {i} del bloque 1 tiene tamaño {n[i]}, "
                "pero no cabe en ninguna sala."
            )

    for k in K:
        cabe_en_alguna_sala = False

        for r in R:
            if m[k] <= cap[r]:
                cabe_en_alguna_sala = True

        if not cabe_en_alguna_sala:
            print(
                f"ADVERTENCIA: el curso {k} del bloque 2 tiene tamaño {m[k]}, "
                "pero no cabe en ninguna sala."
            )

    if len(R) < len(I):
        print(
            "ADVERTENCIA: hay menos salas que cursos del bloque 1. "
            "El modelo probablemente será infactible."
        )

    if len(R) < len(K):
        print(
            "ADVERTENCIA: hay menos salas que cursos del bloque 2. "
            "El modelo probablemente será infactible."
        )

    # --------------------------------------------------
    # 11. Si llegó hasta aquí, la data está bien
    # --------------------------------------------------

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
        "I": I,
        "K": K,
        "R": R,
        "n": n,
        "m": m,
        "cap": cap,
        "F": F,
        "f_L": f_L,
        "cursos_b1": cursos_b1,
        "cursos_b2": cursos_b2,
        "salas": salas,
        "flujos": flujos,
        "libres": libres,
    }


def validar_todas_las_carpetas(carpeta_base):
    """
    Valida todas las carpetas que están dentro de carpeta_base.

    Por ejemplo:
    data/modelo2/
        M2_T01_factible_costo_0/
        M2_T02_capacidad_cambia_optimo/
        M2_T03_infactible_capacidad/
        ...
    """

    carpeta_base = Path(carpeta_base)

    carpetas_tests = []

    for carpeta in carpeta_base.iterdir():
        if carpeta.is_dir():
            carpetas_tests.append(carpeta)

    carpetas_tests = sorted(carpetas_tests)

    if len(carpetas_tests) == 0:
        print("No se encontraron carpetas de tests.")
        return

    print("Validando carpetas de tests...")
    print("=" * 60)

    cantidad_ok = 0
    cantidad_error = 0

    for carpeta_test in carpetas_tests:
        print()
        print(f"Validando: {carpeta_test.name}")
        print("-" * 60)

        try:
            validar_instancia_modelo_2(carpeta_test)
            print(f"RESULTADO: OK - {carpeta_test.name}")
            cantidad_ok += 1

        except Exception as error:
            print(f"RESULTADO: ERROR - {carpeta_test.name}")
            print(error)
            cantidad_error += 1

    print()
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"Tests validados correctamente: {cantidad_ok}")
    print(f"Tests con error: {cantidad_error}")
    print(f"Total de tests revisados: {cantidad_ok + cantidad_error}")


# --------------------------------------------------
# Para ejecutar desde terminal
# --------------------------------------------------

if __name__ == "__main__":
    carpeta_base = "data/modelo2"

    validar_todas_las_carpetas(carpeta_base)
