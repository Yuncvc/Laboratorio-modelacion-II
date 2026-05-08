from pathlib import Path
import json
import pandas as pd


# ============================================================
# generar_data_modelo_2.py
#
# Este archivo genera data sintética para el Modelo 2.
#
# Modelo 2:
# - Cursos con tamaños distintos
# - Salas con capacidades distintas
# - Un solo edificio
# - Costo binario:
#       0 si es la misma sala
#       1 si cambia de sala
# ============================================================


def crear_costos_binarios(salas):
    """
    Crea la tabla costos.csv para el Modelo 2.

    costo = 0 si sala_origen == sala_destino
    costo = 1 si sala_origen != sala_destino
    """

    filas = []

    for sala_origen in salas["sala_id"]:
        for sala_destino in salas["sala_id"]:
            if sala_origen == sala_destino:
                costo = 0
            else:
                costo = 1

            filas.append(
                {
                    "sala_origen": sala_origen,
                    "sala_destino": sala_destino,
                    "costo": costo,
                }
            )

    costos = pd.DataFrame(filas)

    return costos


def guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata):
    """
    Guarda todos los archivos de un test en su carpeta correspondiente.
    """

    # Este archivo está en src/generar_data_modelo_2.py
    # parents[1] sube desde src/ a la carpeta principal del proyecto
    ROOT = Path(__file__).resolve().parents[1]
    DATA_MODELO_2 = ROOT / "data" / "modelo2"

    carpeta = DATA_MODELO_2 / nombre_test

    carpeta.mkdir(parents=True, exist_ok=True)

    costos = crear_costos_binarios(salas)

    cursos_b1.to_csv(carpeta / "cursos_b1.csv", index=False)
    cursos_b2.to_csv(carpeta / "cursos_b2.csv", index=False)
    salas.to_csv(carpeta / "salas.csv", index=False)
    flujos.to_csv(carpeta / "flujos.csv", index=False)
    libres.to_csv(carpeta / "libres.csv", index=False)
    costos.to_csv(carpeta / "costos.csv", index=False)

    with open(carpeta / "metadata.json", "w", encoding="utf-8") as archivo:
        json.dump(metadata, archivo, indent=4, ensure_ascii=False)

    print(f"Test generado: {nombre_test}")


# ============================================================
# TEST 1
# Caso factible con costo óptimo 0
# ============================================================


def generar_test_01():

    nombre_test = "M2_T01_factible_costo_0"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2", "i3"], "tamano": [40, 30, 20]})

    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2", "k3"], "tamano": [40, 30, 20]})

    salas = pd.DataFrame({"sala_id": ["r1", "r2", "r3"], "capacidad": [40, 30, 20]})

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i2", "i3"],
            "curso_b2": ["k1", "k2", "k3"],
            "flujo": [40, 30, 20],
        }
    )

    libres = pd.DataFrame({"curso_b1": ["i1", "i2", "i3"], "libres": [0, 0, 0]})

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Caso factible donde todos los estudiantes pueden quedarse en la misma sala.",
        "expected_status": "OPTIMAL",
        "expected_obj": 0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 2
# Capacidad cambia el óptimo
# ============================================================


def generar_test_02():

    nombre_test = "M2_T02_capacidad_cambia_optimo"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [50, 30]})

    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [30, 50]})

    salas = pd.DataFrame({"sala_id": ["r1", "r2"], "capacidad": [50, 30]})

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i1", "i2"],
            "curso_b2": ["k1", "k2", "k2"],
            "flujo": [30, 20, 30],
        }
    )

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    metadata = {
        "nombre": nombre_test,
        "descripcion": "La capacidad obliga a usar una asignación más costosa.",
        "expected_status": "OPTIMAL",
        "expected_obj": 60,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 3
# Infactible por capacidad
# ============================================================


def generar_test_03():

    nombre_test = "M2_T03_infactible_capacidad"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [60, 30]})

    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [60, 30]})

    salas = pd.DataFrame({"sala_id": ["r1", "r2"], "capacidad": [50, 30]})

    flujos = pd.DataFrame(
        {"curso_b1": ["i1", "i2"], "curso_b2": ["k1", "k2"], "flujo": [60, 30]}
    )

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Un curso tiene tamaño 60, pero la sala más grande tiene capacidad 50.",
        "expected_status": "INFEASIBLE",
        "expected_obj": None,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 4
# Múltiples óptimos
# ============================================================


def generar_test_04():

    nombre_test = "M2_T04_multiples_optimos"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [30, 30]})

    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [30, 30]})

    salas = pd.DataFrame({"sala_id": ["r1", "r2"], "capacidad": [40, 40]})

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i1", "i2", "i2"],
            "curso_b2": ["k1", "k2", "k1", "k2"],
            "flujo": [15, 15, 15, 15],
        }
    )

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Existen varias asignaciones óptimas con el mismo costo.",
        "expected_status": "OPTIMAL",
        "expected_obj": 30,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 5
# Estudiantes libres
# ============================================================


def generar_test_05():

    nombre_test = "M2_T05_estudiantes_libres"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2", "i3"], "tamano": [40, 30, 20]})

    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2", "k3"], "tamano": [30, 25, 20]})

    salas = pd.DataFrame({"sala_id": ["r1", "r2", "r3"], "capacidad": [40, 30, 25]})

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i2", "i3"],
            "curso_b2": ["k1", "k2", "k3"],
            "flujo": [30, 25, 20],
        }
    )

    libres = pd.DataFrame({"curso_b1": ["i1", "i2", "i3"], "libres": [10, 5, 0]})

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Parte de los estudiantes queda libre y no genera costo de movilidad.",
        "expected_status": "OPTIMAL",
        "expected_obj": 0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 6
# 5 cursos con capacidades heterogéneas
# ============================================================


def generar_test_06():

    nombre_test = "M2_T06_5_cursos_capacidades_heterogeneas"

    cursos_b1 = pd.DataFrame(
        {"curso_id": ["i1", "i2", "i3", "i4", "i5"], "tamano": [50, 45, 35, 30, 20]}
    )

    cursos_b2 = pd.DataFrame(
        {"curso_id": ["k1", "k2", "k3", "k4", "k5"], "tamano": [45, 50, 35, 30, 20]}
    )

    salas = pd.DataFrame(
        {"sala_id": ["r1", "r2", "r3", "r4", "r5"], "capacidad": [50, 45, 35, 30, 20]}
    )

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i1", "i2", "i2", "i3", "i4", "i5"],
            "curso_b2": ["k1", "k2", "k1", "k2", "k3", "k4", "k5"],
            "flujo": [10, 40, 35, 10, 35, 30, 20],
        }
    )

    libres = pd.DataFrame(
        {"curso_b1": ["i1", "i2", "i3", "i4", "i5"], "libres": [0, 0, 0, 0, 0]}
    )

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Test mediano con 5 cursos y capacidades heterogéneas. Las capacidades fuerzan una asignación casi determinada.",
        "expected_status": "OPTIMAL",
        "expected_obj": 20,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 7
# 6 cursos con estudiantes libres
# ============================================================


def generar_test_07():

    nombre_test = "M2_T07_6_cursos_con_libres"

    cursos_b1 = pd.DataFrame(
        {
            "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6"],
            "tamano": [50, 45, 40, 35, 30, 25],
        }
    )

    cursos_b2 = pd.DataFrame(
        {
            "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6"],
            "tamano": [45, 40, 35, 30, 25, 20],
        }
    )

    salas = pd.DataFrame(
        {
            "sala_id": ["r1", "r2", "r3", "r4", "r5", "r6"],
            "capacidad": [50, 45, 40, 35, 30, 25],
        }
    )

    flujos = pd.DataFrame(
        {
            "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6"],
            "curso_b2": ["k1", "k2", "k3", "k4", "k5", "k6"],
            "flujo": [45, 40, 35, 30, 25, 20],
        }
    )

    libres = pd.DataFrame(
        {"curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6"], "libres": [5, 5, 5, 5, 5, 5]}
    )

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Test mediano con 6 cursos donde todos los cursos del bloque 1 tienen estudiantes libres.",
        "expected_status": "OPTIMAL",
        "expected_obj": 0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 8
# 8 cursos donde la capacidad cambia la solución
# ============================================================


def generar_test_08():

    nombre_test = "M2_T08_8_cursos_capacidad_cambia_solucion"

    cursos_b1 = pd.DataFrame(
        {
            "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
            "tamano": [60, 55, 45, 40, 35, 30, 25, 20],
        }
    )

    cursos_b2 = pd.DataFrame(
        {
            "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
            "tamano": [55, 60, 45, 40, 35, 30, 25, 20],
        }
    )

    salas = pd.DataFrame(
        {
            "sala_id": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"],
            "capacidad": [60, 55, 45, 40, 35, 30, 25, 20],
        }
    )

    flujos = pd.DataFrame(
        {
            "curso_b1": [
                "i1",
                "i1",
                "i2",
                "i2",
                "i3",
                "i3",
                "i4",
                "i4",
                "i5",
                "i5",
                "i6",
                "i6",
                "i7",
                "i7",
                "i8",
                "i8",
            ],
            "curso_b2": [
                "k1",
                "k2",
                "k1",
                "k2",
                "k3",
                "k4",
                "k3",
                "k4",
                "k5",
                "k6",
                "k5",
                "k6",
                "k7",
                "k8",
                "k7",
                "k8",
            ],
            "flujo": [10, 50, 45, 10, 35, 10, 10, 30, 25, 10, 10, 20, 15, 10, 10, 10],
        }
    )

    libres = pd.DataFrame(
        {
            "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
            "libres": [0, 0, 0, 0, 0, 0, 0, 0],
        }
    )

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Test mediano con 8 cursos donde las capacidades fuerzan una solución más costosa.",
        "expected_status": "OPTIMAL",
        "expected_obj": 80,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# TEST 9
# 8 cursos con múltiples óptimos parciales
# ============================================================


def generar_test_09():

    nombre_test = "M2_T09_8_cursos_multiples_optimos_parciales"

    cursos_b1 = pd.DataFrame(
        {
            "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
            "tamano": [40, 40, 34, 34, 28, 28, 22, 22],
        }
    )

    cursos_b2 = pd.DataFrame(
        {
            "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
            "tamano": [40, 40, 34, 34, 28, 28, 22, 22],
        }
    )

    salas = pd.DataFrame(
        {
            "sala_id": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"],
            "capacidad": [40, 40, 34, 34, 28, 28, 22, 22],
        }
    )

    flujos = pd.DataFrame(
        {
            "curso_b1": [
                "i1",
                "i1",
                "i2",
                "i2",
                "i3",
                "i3",
                "i4",
                "i4",
                "i5",
                "i5",
                "i6",
                "i6",
                "i7",
                "i7",
                "i8",
                "i8",
            ],
            "curso_b2": [
                "k1",
                "k2",
                "k1",
                "k2",
                "k3",
                "k4",
                "k3",
                "k4",
                "k5",
                "k6",
                "k5",
                "k6",
                "k7",
                "k8",
                "k7",
                "k8",
            ],
            "flujo": [20, 20, 20, 20, 17, 17, 17, 17, 14, 14, 14, 14, 11, 11, 11, 11],
        }
    )

    libres = pd.DataFrame(
        {
            "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
            "libres": [0, 0, 0, 0, 0, 0, 0, 0],
        }
    )

    metadata = {
        "nombre": nombre_test,
        "descripcion": "Test mediano con 8 cursos donde existen múltiples óptimos dentro de grupos de cursos del mismo tamaño.",
        "expected_status": "OPTIMAL",
        "expected_obj": 124,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# CASO DEMOSTRATIVO
# 12 cursos, capacidades heterogéneas y flujos divididos
# ============================================================


def generar_caso_demo_modelo_2():

    nombre_test = "M2_T10_demo_16_cursos_split_capacidades"

    # --------------------------------------------------
    # Cursos bloque 1
    # --------------------------------------------------

    cursos_b1 = pd.DataFrame(
        {
            "curso_id": [
                "i1",
                "i2",
                "i3",
                "i4",
                "i5",
                "i6",
                "i7",
                "i8",
                "i9",
                "i10",
                "i11",
                "i12",
                "i13",
                "i14",
                "i15",
                "i16",
            ],
            "tamano": [
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                55,
                50,
                45,
                40,
                35,
                30,
                25,
                20,
                15,
            ],
        }
    )

    # --------------------------------------------------
    # Cursos bloque 2
    # --------------------------------------------------
    # Los tamaños son los mismos que en bloque 1,
    # pero intercambiados por pares.
    # Esto fuerza una asignación distinta en el bloque 2.

    cursos_b2 = pd.DataFrame(
        {
            "curso_id": [
                "k1",
                "k2",
                "k3",
                "k4",
                "k5",
                "k6",
                "k7",
                "k8",
                "k9",
                "k10",
                "k11",
                "k12",
                "k13",
                "k14",
                "k15",
                "k16",
            ],
            "tamano": [
                110,
                120,
                90,
                100,
                70,
                80,
                55,
                60,
                45,
                50,
                35,
                40,
                25,
                30,
                15,
                20,
            ],
        }
    )

    # --------------------------------------------------
    # Salas
    # --------------------------------------------------
    # Las capacidades coinciden con los tamaños del bloque 1.
    # Como son capacidades únicas y ordenadas, la asignación
    # queda prácticamente forzada por capacidad.

    salas = pd.DataFrame(
        {
            "sala_id": [
                "r1",
                "r2",
                "r3",
                "r4",
                "r5",
                "r6",
                "r7",
                "r8",
                "r9",
                "r10",
                "r11",
                "r12",
                "r13",
                "r14",
                "r15",
                "r16",
            ],
            "capacidad": [
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                55,
                50,
                45,
                40,
                35,
                30,
                25,
                20,
                15,
            ],
        }
    )

    # --------------------------------------------------
    # Flujos
    # --------------------------------------------------
    # La instancia se arma por pares:
    #
    # Par 1:
    #   i1, i2 se reparten entre k1, k2
    #
    # Par 2:
    #   i3, i4 se reparten entre k3, k4
    #
    # etc.
    #
    # Dentro de cada par, hay flujo dividido.
    # La asignación por capacidad determina qué parte queda
    # en la misma sala y qué parte se mueve.

    filas_flujos = []

    tamanos_b1 = list(cursos_b1["tamano"])

    for posicion in range(0, 16, 2):
        # Curso grande y curso pequeño dentro del par
        i_grande = f"i{posicion + 1}"
        i_pequeno = f"i{posicion + 2}"

        tamano_grande = tamanos_b1[posicion]
        tamano_pequeno = tamanos_b1[posicion + 1]

        # En bloque 2 están intercambiados por par
        k_pequeno = f"k{posicion + 1}"
        k_grande = f"k{posicion + 2}"

        # Flujo que queda en la misma sala para el curso grande
        flujo_mismo_grande = int(round(0.65 * tamano_grande))

        # Flujo cruzado desde curso grande hacia curso pequeño
        flujo_cruzado = tamano_grande - flujo_mismo_grande

        # Flujo que queda en la misma sala para el curso pequeño
        flujo_mismo_pequeno = tamano_pequeno - flujo_cruzado

        filas_flujos.append(
            {"curso_b1": i_grande, "curso_b2": k_grande, "flujo": flujo_mismo_grande}
        )

        filas_flujos.append(
            {"curso_b1": i_grande, "curso_b2": k_pequeno, "flujo": flujo_cruzado}
        )

        filas_flujos.append(
            {"curso_b1": i_pequeno, "curso_b2": k_pequeno, "flujo": flujo_mismo_pequeno}
        )

        filas_flujos.append(
            {"curso_b1": i_pequeno, "curso_b2": k_grande, "flujo": flujo_cruzado}
        )

    flujos = pd.DataFrame(filas_flujos)

    # --------------------------------------------------
    # Estudiantes libres
    # --------------------------------------------------
    # En este caso demo no usamos estudiantes libres,
    # para concentrarnos en capacidades y movilidad.

    libres = pd.DataFrame(
        {
            "curso_b1": [
                "i1",
                "i2",
                "i3",
                "i4",
                "i5",
                "i6",
                "i7",
                "i8",
                "i9",
                "i10",
                "i11",
                "i12",
                "i13",
                "i14",
                "i15",
                "i16",
            ],
            "libres": [0] * 16,
        }
    )

    # --------------------------------------------------
    # Cálculo del costo esperado
    # --------------------------------------------------
    # La asignación queda forzada por capacidad.
    # Por eso podemos calcular el costo esperado contando
    # cuántos estudiantes permanecen en la misma sala.

    flujo_total = flujos["flujo"].sum()

    estudiantes_no_se_mueven = 0

    for posicion in range(0, 16, 2):
        tamano_grande = tamanos_b1[posicion]
        tamano_pequeno = tamanos_b1[posicion + 1]

        flujo_mismo_grande = int(round(0.65 * tamano_grande))
        flujo_cruzado = tamano_grande - flujo_mismo_grande
        flujo_mismo_pequeno = tamano_pequeno - flujo_cruzado

        estudiantes_no_se_mueven += flujo_mismo_grande
        estudiantes_no_se_mueven += flujo_mismo_pequeno

    expected_obj = int(flujo_total - estudiantes_no_se_mueven)

    metadata = {
        "nombre": nombre_test,
        "descripcion": (
            "Caso demostrativo difícil con 16 cursos, 16 salas, "
            "capacidades heterogéneas y flujos divididos por pares."
        ),
        "expected_status": "OPTIMAL",
        "expected_obj": expected_obj,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, metadata)


# ============================================================
# Generar todos los tests
# ============================================================


def generar_tests_pequenos():
    """
    Genera los tests pequeños del Modelo 2:
    M2_T01 a M2_T05.
    """

    generar_test_01()
    generar_test_02()
    generar_test_03()
    generar_test_04()
    generar_test_05()

    print()
    print("Tests pequeños del Modelo 2 generados correctamente.")


def generar_tests_medianos():
    """
    Genera los tests medianos del Modelo 2:
    M2_T06 a M2_T09.
    """

    generar_test_06()
    generar_test_07()
    generar_test_08()
    generar_test_09()

    print()
    print("Tests medianos del Modelo 2 generados correctamente.")


def generar_todos_los_tests():
    """
    Genera todos los tests del Modelo 2:
    M2_T01 a M2_T09.
    """

    generar_tests_pequenos()
    generar_tests_medianos()

    print()
    print("Todos los tests del Modelo 2 fueron generados correctamente.")


if __name__ == "__main__":
    generar_todos_los_tests()
