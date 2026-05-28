from pathlib import Path
import json
import pandas as pd


# ============================================================
# generar_data_modelo_3.py
#
# Este archivo genera data sintética para el Modelo 3.
#
# Modelo 3:
# - Cursos con tamaños distintos
# - Salas con capacidades distintas
# - Múltiples edificios (cada sala pertenece a uno)
# - Costo según tipo de transición:
#       0 si es la misma sala
#       1 si cambia de sala dentro del mismo edificio
#       gamma[e1, e2] si cambia de edificio
#
# Grupos de tests:
#   Pequeños  (T01-T05): 2-3 cursos, 2-3 salas
#   Medianos  (T06-T09): 5-6 cursos, 5-6 salas
#   Grandes   (T10-T13): 8-10 cursos, 8-10 salas
# ============================================================


def crear_costos_modelo_3(salas, gamma):
    """
    Crea la tabla costos.csv para el Modelo 3.

    costo(r, s) =
        0                   si r == s
        1                   si r != s y edificio(r) == edificio(s)
        gamma[e1, e2]       si edificio(r) != edificio(s)
    """

    edificio_sala = dict(zip(salas["sala_id"], salas["edificio"]))

    filas = []

    for sala_origen in salas["sala_id"]:
        for sala_destino in salas["sala_id"]:
            e_origen  = edificio_sala[sala_origen]
            e_destino = edificio_sala[sala_destino]

            if sala_origen == sala_destino:
                costo = 0
            elif e_origen == e_destino:
                costo = 1
            else:
                costo = gamma[(e_origen, e_destino)]

            filas.append({
                "sala_origen":  sala_origen,
                "sala_destino": sala_destino,
                "costo":        costo,
            })

    return pd.DataFrame(filas)


def crear_gamma_csv(gamma, edificios):
    """
    Convierte el diccionario gamma en un DataFrame para guardar como gamma.csv.
    """

    filas = []

    for e1 in edificios:
        for e2 in edificios:
            filas.append({
                "edificio_origen":  e1,
                "edificio_destino": e2,
                "gamma":            gamma[(e1, e2)],
            })

    return pd.DataFrame(filas)


def guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata):
    """
    Guarda todos los archivos de un test en su carpeta correspondiente.
    """

    ROOT = Path(__file__).resolve().parents[1]
    DATA_MODELO_3 = ROOT / "data" / "modelo3"

    carpeta = DATA_MODELO_3 / nombre_test
    carpeta.mkdir(parents=True, exist_ok=True)

    edificios = sorted(salas["edificio"].unique())
    costos    = crear_costos_modelo_3(salas, gamma)
    gamma_df  = crear_gamma_csv(gamma, edificios)

    cursos_b1.to_csv(carpeta / "cursos_b1.csv", index=False)
    cursos_b2.to_csv(carpeta / "cursos_b2.csv", index=False)
    salas.to_csv(carpeta / "salas.csv",          index=False)
    flujos.to_csv(carpeta / "flujos.csv",         index=False)
    libres.to_csv(carpeta / "libres.csv",         index=False)
    costos.to_csv(carpeta / "costos.csv",         index=False)
    gamma_df.to_csv(carpeta / "gamma.csv",        index=False)

    with open(carpeta / "metadata.json", "w", encoding="utf-8") as archivo:
        json.dump(metadata, archivo, indent=4, ensure_ascii=False)

    print(f"Test generado: {nombre_test}")


# ============================================================
# TESTS PEQUEÑOS (T01-T05)
# 2-3 cursos, 2-3 salas
# ============================================================


def generar_test_01():
    """
    2 cursos, 2 salas en 2 edificios distintos.
    Flujos directos: cada curso de b2 va a la misma sala que su curso de b1.
    Costo esperado: 0.
    """

    nombre_test = "M3_T01_misma_sala_costo_0"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [30, 20]})
    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [30, 20]})

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2"],
        "capacidad": [30,   20],
        "edificio":  ["A",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2"],
        "curso_b2": ["k1", "k2"],
        "flujo":    [30,   20],
    })

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    gamma = {
        ("A", "A"): 1, ("A", "B"): 5,
        ("B", "A"): 5, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "Todos los estudiantes permanecen en la misma sala. Costo esperado: 0.",
        "expected_status": "OPTIMAL",
        "expected_obj":    0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_02():
    """
    2 cursos, 2 salas en el mismo edificio.
    Flujos cruzados y capacidades exactas fuerzan intercambio de salas.
    Costo esperado: 60.
    """

    nombre_test = "M3_T02_mismo_edificio_costo_1"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [40, 30]})
    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [40, 30]})

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2"],
        "capacidad": [40,   30],
        "edificio":  ["A",  "A"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2"],
        "curso_b2": ["k1", "k2", "k1"],
        "flujo":    [10,   30,   30],
    })

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    gamma = {
        ("A", "A"): 1, ("A", "B"): 5,
        ("B", "A"): 5, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "Flujos cruzados dentro del mismo edificio. Costo = 60.",
        "expected_status": "OPTIMAL",
        "expected_obj":    60,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_03():
    """
    2 cursos b1, 1 curso b2, 3 salas en 2 edificios.
    El modelo elige una solución donde parte del flujo cruza de edificio.
    Costo esperado: 30.
    """

    nombre_test = "M3_T03_distinto_edificio_costo_gamma"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [20, 20]})
    cursos_b2 = pd.DataFrame({"curso_id": ["k1"],        "tamano": [30]})

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3"],
        "capacidad": [20,   20,   30],
        "edificio":  ["A",  "A",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2"],
        "curso_b2": ["k1", "k1"],
        "flujo":    [20,   10],
    })

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 10]})

    gamma = {
        ("A", "A"): 1, ("A", "B"): 3,
        ("B", "A"): 3, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "Parte del flujo cruza de edificio A a B. Costo = 10 * gamma(A,B) = 10 * 3 = 30.",
        "expected_status": "OPTIMAL",
        "expected_obj":    30,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_04():
    """
    Instancia infactible: un curso no cabe en ninguna sala.
    """

    nombre_test = "M3_T04_infactible_capacidad"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [60, 30]})
    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [60, 30]})

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2"],
        "capacidad": [50,   30],
        "edificio":  ["A",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2"],
        "curso_b2": ["k1", "k2"],
        "flujo":    [60,   30],
    })

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [0, 0]})

    gamma = {
        ("A", "A"): 1, ("A", "B"): 5,
        ("B", "A"): 5, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "Curso i1 tiene tamaño 60 pero la sala más grande tiene cap 50. INFEASIBLE.",
        "expected_status": "INFEASIBLE",
        "expected_obj":    None,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_05():
    """
    2 cursos b1, 2 cursos b2, 2 salas en 2 edificios.
    Estudiantes libres en ambos cursos. Los que continúan permanecen en la misma sala.
    Costo esperado: 0.
    """

    nombre_test = "M3_T05_estudiantes_libres"

    cursos_b1 = pd.DataFrame({"curso_id": ["i1", "i2"], "tamano": [40, 30]})
    cursos_b2 = pd.DataFrame({"curso_id": ["k1", "k2"], "tamano": [30, 20]})

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2"],
        "capacidad": [40,   30],
        "edificio":  ["A",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2"],
        "curso_b2": ["k1", "k2"],
        "flujo":    [30,   20],
    })

    libres = pd.DataFrame({"curso_b1": ["i1", "i2"], "libres": [10, 10]})

    gamma = {
        ("A", "A"): 1, ("A", "B"): 5,
        ("B", "A"): 5, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "Estudiantes libres no generan costo. Los que continúan permanecen en la misma sala. Costo: 0.",
        "expected_status": "OPTIMAL",
        "expected_obj":    0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


# ============================================================
# TESTS MEDIANOS (T06-T09)
# 5-6 cursos, 5-6 salas, 2-3 edificios
# ============================================================


def generar_test_06():
    """
    5 cursos, 5 salas en 2 edificios (2 salas en A, 3 salas en B).
    gamma(A,B) = 8: muy costoso cruzar de edificio.

    Las capacidades fuerzan intercambio dentro del Edificio A.
    Los cursos del Edificio B permanecen en la misma sala.
    Costo esperado: 20.

    Edificio A: r1(50), r2(40)
    Edificio B: r3(35), r4(30), r5(20)

    b1: i1(50)→r1(A), i2(40)→r2(A), i3(35)→r3(B), i4(30)→r4(B), i5(20)→r5(B)
    b2: k2(50)→r1(A), k1(40)→r2(A), k3(35)→r3(B), k4(30)→r4(B), k5(20)→r5(B)

    Flujos:
    i1→k1(10), i1→k2(40): i1 en r1A, k1 va a r2A → 10 est. cambian (mismo edif.)
    i2→k1(30), i2→k2(10): i2 en r2A, k2 va a r1A → 10 est. cambian (mismo edif.)
    i3→k3(35), i4→k4(30), i5→k5(20): misma sala → costo 0.
    Costo = 10 + 10 = 20.
    """

    nombre_test = "M3_T06_5_cursos_2_edificios_gamma_alto"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5"],
        "tamano":   [50,   40,   35,   30,   20],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5"],
        "tamano":   [40,   50,   35,   30,   20],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5"],
        "capacidad": [50,   40,   35,   30,   20],
        "edificio":  ["A",  "A",  "B",  "B",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2", "i2", "i3", "i4", "i5"],
        "curso_b2": ["k1", "k2", "k1", "k2", "k3", "k4", "k5"],
        "flujo":    [10,   40,   30,   10,   35,   30,   20],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5"],
        "libres":   [0, 0, 0, 0, 0],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 8,
        ("B", "A"): 8, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "5 cursos en 2 edificios. gamma=8 evita cruces. Capacidades fuerzan intercambio en A. Costo esperado: 20.",
        "expected_status": "OPTIMAL",
        "expected_obj":    20,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_07():
    """
    6 cursos, 6 salas en 3 edificios (2 salas por edificio).
    Todos los cursos del bloque 1 tienen estudiantes libres.
    Los flujos permiten que todos permanezcan en la misma sala.
    Costo esperado: 0.
    """

    nombre_test = "M3_T07_6_cursos_3_edificios_con_libres"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6"],
        "tamano":   [50,   45,   40,   35,   30,   25],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6"],
        "tamano":   [45,   40,   35,   30,   25,   20],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5", "r6"],
        "capacidad": [50,   45,   40,   35,   30,   25],
        "edificio":  ["A",  "A",  "B",  "B",  "C",  "C"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6"],
        "curso_b2": ["k1", "k2", "k3", "k4", "k5", "k6"],
        "flujo":    [45,   40,   35,   30,   25,   20],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6"],
        "libres":   [5,    5,    5,    5,    5,    5],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 4, ("A", "C"): 6,
        ("B", "A"): 4, ("B", "B"): 1, ("B", "C"): 4,
        ("C", "A"): 6, ("C", "B"): 4, ("C", "C"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "6 cursos en 3 edificios con libres. Todos permanecen en la misma sala. Costo: 0.",
        "expected_status": "OPTIMAL",
        "expected_obj":    0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_08():
    """
    5 cursos, 5 salas en 2 edificios.
    gamma(A,B) = 2: moderado.
    Flujos cruzados entre cursos de distintos edificios.
    El modelo prefiere pagar costo 1 dentro del mismo edificio
    antes que cruzar con costo 2.
    Costo esperado: 20.

    Edificio A: r1(50), r2(40)
    Edificio B: r3(35), r4(30), r5(25)

    b1: i1(50)→r1(A), i2(40)→r2(A), i3(35)→r3(B), i4(30)→r4(B), i5(25)→r5(B)
    b2: k2(50)→r1(A), k1(40)→r2(A), k3(35)→r3(B), k4(30)→r4(B), k5(25)→r5(B)

    Flujos cruzados en cada edificio:
    i1→k2(40), i1→k1(10): i1(r1A) → k1(r2A): 10 est. * 1 = 10
    i2→k1(30), i2→k2(10): i2(r2A) → k2(r1A): 10 est. * 1 = 10
    i3→k3(35), i4→k4(30), i5→k5(25): misma sala → 0

    Costo = 10 + 10 = 20.
    """

    nombre_test = "M3_T08_5_cursos_2_edificios_gamma_moderado"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5"],
        "tamano":   [50,   40,   35,   30,   25],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5"],
        "tamano":   [40,   50,   35,   30,   25],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5"],
        "capacidad": [50,   40,   35,   30,   25],
        "edificio":  ["A",  "A",  "B",  "B",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2", "i2", "i3", "i4", "i5"],
        "curso_b2": ["k1", "k2", "k1", "k2", "k3", "k4", "k5"],
        "flujo":    [10,   40,   30,   10,   35,   30,   25],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5"],
        "libres":   [0, 0, 0, 0, 0],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 2,
        ("B", "A"): 2, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "5 cursos en 2 edificios. gamma=2. Capacidades fuerzan intercambio en A. El modelo prefiere quedarse en el mismo edificio. Costo esperado: 20.",
        "expected_status": "OPTIMAL",
        "expected_obj":    20,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_09():
    """
    6 cursos, 6 salas en 3 edificios (2 salas por edificio).
    Flujos simétricos dentro de cada edificio generan múltiples óptimos.
    Costo esperado: 60 (flujos cruzados dentro de cada edificio).

    Edificio A: r1(40), r2(40)  → i1, i2, k1, k2
    Edificio B: r3(34), r4(34)  → i3, i4, k3, k4
    Edificio C: r5(28), r6(28)  → i5, i6, k5, k6

    Flujos simétricos dentro de cada grupo:
    i1→k1(20), i1→k2(20): i1 cambia a k2 en r2 → 20 est. * 1 = 20
    i2→k1(20), i2→k2(20): i2 cambia a k1 en r1 → 20 est. * 1 = 20
    i3→k3(17), i3→k4(17), i4→k3(17), i4→k4(17): 17+17=34 est. cambian * 1 = ... no

    Análisis detallado:
    Cada grupo tiene 2 cursos b1 y 2 cursos b2, todos de igual tamaño.
    Flujos simétricos: cada i manda la mitad a cada k del grupo.
    La asignación óptima pone cada k en la misma sala que un i del grupo.
    Los flujos cruzados generan costo: 20+20+17+17+14+14 = 102? No.

    Recalculo:
    Grupo A (r1,r2 cap40): i1→r1, i2→r2, k1→r1 o r2, k2→r1 o r2.
    Si k1→r1: i1(r1)→k1(r1)=20*0=0, i2(r2)→k1(r1)=20*1=20.
    Si k2→r2: i1(r1)→k2(r2)=20*1=20, i2(r2)→k2(r2)=20*0=0. Total grupo A = 40.
    Grupo B: igual, 17+17=34 est. cruzan * 1 = 34.
    Grupo C: 14+14=28 est. * 1 = 28.
    Costo total = 40 + 34 + 28 = 102.
    """

    nombre_test = "M3_T09_6_cursos_3_edificios_multiples_optimos"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6"],
        "tamano":   [40,   40,   34,   34,   28,   28],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6"],
        "tamano":   [40,   40,   34,   34,   28,   28],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5", "r6"],
        "capacidad": [40,   40,   34,   34,   28,   28],
        "edificio":  ["A",  "A",  "B",  "B",  "C",  "C"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2", "i2",
                     "i3", "i3", "i4", "i4",
                     "i5", "i5", "i6", "i6"],
        "curso_b2": ["k1", "k2", "k1", "k2",
                     "k3", "k4", "k3", "k4",
                     "k5", "k6", "k5", "k6"],
        "flujo":    [20,   20,   20,   20,
                     17,   17,   17,   17,
                     14,   14,   14,   14],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6"],
        "libres":   [0, 0, 0, 0, 0, 0],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 8, ("A", "C"): 8,
        ("B", "A"): 8, ("B", "B"): 1, ("B", "C"): 8,
        ("C", "A"): 8, ("C", "B"): 8, ("C", "C"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "6 cursos en 3 edificios con flujos simétricos. gamma=8 evita cruces. Múltiples óptimos dentro de cada edificio. Costo esperado: 102.",
        "expected_status": "OPTIMAL",
        "expected_obj":    102,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


# ============================================================
# TESTS GRANDES (T10-T13)
# 8-10 cursos, 8-10 salas, 2-4 edificios
# ============================================================


def generar_test_10():
    """
    8 cursos, 8 salas en 2 edificios (4 salas por edificio).
    gamma(A,B) = 10: muy alto, el modelo nunca cruza de edificio.

    Las capacidades fuerzan intercambio dentro de cada edificio.
    Edificio A: r1(60), r2(55), r3(45), r4(40)
    Edificio B: r5(35), r6(30), r7(25), r8(20)

    b1: i1(60)→r1(A), i2(55)→r2(A), i3(45)→r3(A), i4(40)→r4(A)
        i5(35)→r5(B), i6(30)→r6(B), i7(25)→r7(B), i8(20)→r8(B)

    b2: k2(60)→r1(A), k1(55)→r2(A), k4(45)→r3(A), k3(40)→r4(A)
        k6(35)→r5(B), k5(30)→r6(B), k8(25)→r7(B), k7(20)→r8(B)

    Flujos en edificio A:
    i1→k1(10), i1→k2(50): i1(r1A)→k1(r2A): 10*1=10
    i2→k1(45), i2→k2(10): i2(r2A)→k2(r1A): 10*1=10
    i3→k3(35), i3→k4(10): i3(r3A)→k3(r4A): 35*1=35
    i4→k3(5),  i4→k4(35): i4(r4A)→k4(r3A): 5*1=5  (pero k3 recibe 35+5=40 ✓)

    Flujos en edificio B:
    i5→k5(20), i5→k6(15): i5(r5B)→k5(r6B): 20*1=20
    i6→k5(10), i6→k6(20): i6(r6B)→k6(r5B): 10*1=10  (k5=30 recibe 20+10 ✓, k6=35 recibe 15+20 ✓)
    i7→k7(15), i7→k8(10): i7(r7B)→k7(r8B): 15*1=15
    i8→k7(5),  i8→k8(15): i8(r8B)→k8(r7B): 5*1=5

    Recalculo:
    Edificio A:
    k1(55): recibe i1→k1(10) + i2→k1(45) = 55 ✓
    k2(60): recibe i1→k2(50) + i2→k2(10) = 60 ✓
    k3(40): recibe i3→k3(35) + i4→k3(5) = 40 ✓
    k4(45): recibe i3→k4(10) + i4→k4(35) = 45 ✓

    Movilidad en A:
    i1(r1A)→k1(r2A): 10*1=10
    i1(r1A)→k2(r1A): 50*0=0
    i2(r2A)→k1(r2A): 45*0=0
    i2(r2A)→k2(r1A): 10*1=10
    i3(r3A)→k3(r4A): 35*1=35
    i3(r3A)→k4(r3A): 10*0=0
    i4(r4A)→k3(r4A): 5*0=0
    i4(r4A)→k4(r3A): 35*1=35
    Subtotal A = 10+10+35+35 = 90

    Edificio B:
    k5(30): recibe i5→k5(20) + i6→k5(10) = 30 ✓
    k6(35): recibe i5→k6(15) + i6→k6(20) = 35 ✓
    k7(20): recibe i7→k7(15) + i8→k7(5) = 20 ✓
    k8(25): recibe i7→k8(10) + i8→k8(15) = 25 ✓

    Movilidad en B:
    i5(r5B)→k5(r6B): 20*1=20
    i5(r5B)→k6(r5B): 15*0=0
    i6(r6B)→k5(r6B): 10*0=0
    i6(r6B)→k6(r5B): 20*1=20
    i7(r7B)→k7(r8B): 15*1=15
    i7(r7B)→k8(r7B): 10*0=0
    i8(r8B)→k7(r8B): 5*0=0
    i8(r8B)→k8(r7B): 15*1=15
    Subtotal B = 20+20+15+15 = 70

    Costo total = 90 + 70 = 160
    """

    nombre_test = "M3_T10_8_cursos_2_edificios_gamma_alto"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "tamano":   [60,   55,   45,   40,   35,   30,   25,   20],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
        "tamano":   [55,   60,   40,   45,   30,   35,   20,   25],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"],
        "capacidad": [60,   55,   45,   40,   35,   30,   25,   20],
        "edificio":  ["A",  "A",  "A",  "A",  "B",  "B",  "B",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2", "i2", "i3", "i3", "i4", "i4",
                     "i5", "i5", "i6", "i6", "i7", "i7", "i8", "i8"],
        "curso_b2": ["k1", "k2", "k1", "k2", "k3", "k4", "k3", "k4",
                     "k5", "k6", "k5", "k6", "k7", "k8", "k7", "k8"],
        "flujo":    [10,   50,   45,   10,   35,   10,    5,   35,
                     20,   15,   10,   20,   15,   10,    5,   15],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "libres":   [0, 0, 0, 0, 0, 0, 0, 0],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 10,
        ("B", "A"): 10, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "8 cursos en 2 edificios. gamma=10 evita cruces. Capacidades fuerzan intercambios dentro de cada edificio. Costo esperado: 160.",
        "expected_status": "OPTIMAL",
        "expected_obj":    160,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_11():
    """
    8 cursos, 8 salas en 2 edificios (4 salas por edificio).
    Todos los cursos tienen estudiantes libres.
    Los que continúan permanecen en la misma sala.
    Costo esperado: 0.
    """

    nombre_test = "M3_T11_8_cursos_2_edificios_con_libres"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "tamano":   [60,   55,   45,   40,   35,   30,   25,   20],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
        "tamano":   [55,   50,   40,   35,   30,   25,   20,   15],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"],
        "capacidad": [60,   55,   45,   40,   35,   30,   25,   20],
        "edificio":  ["A",  "A",  "A",  "A",  "B",  "B",  "B",  "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "curso_b2": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
        "flujo":    [55,   50,   40,   35,   30,   25,   20,   15],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "libres":   [5,    5,    5,    5,    5,    5,    5,    5],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 5,
        ("B", "A"): 5, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "8 cursos en 2 edificios con libres. Todos los que continúan permanecen en la misma sala. Costo: 0.",
        "expected_status": "OPTIMAL",
        "expected_obj":    0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_12():
    """
    8 cursos, 8 salas en 4 edificios (2 salas por edificio).
    Flujos simétricos dentro de cada edificio.
    gamma alto evita cruces entre edificios.
    Costo esperado: 80 + 68 + 56 + 44 = 248... recalculo.

    Edificio A: r1(40), r2(40)  → i1, i2 (tam 40)
    Edificio B: r3(34), r4(34)  → i3, i4 (tam 34)
    Edificio C: r5(28), r6(28)  → i5, i6 (tam 28)
    Edificio D: r7(22), r8(22)  → i7, i8 (tam 22)

    Flujos simétricos (20/20 para A, 17/17 para B, 14/14 para C, 11/11 para D):
    Dentro de cada edificio, el modelo debe cruzar las salas.
    Movilidad por edificio:
    A: i1→k2(20)*1 + i2→k1(20)*1 = 40
    B: i3→k4(17)*1 + i4→k3(17)*1 = 34
    C: i5→k6(14)*1 + i6→k5(14)*1 = 28
    D: i7→k8(11)*1 + i8→k7(11)*1 = 22

    Costo total = 40 + 34 + 28 + 22 = 124
    """

    nombre_test = "M3_T12_8_cursos_4_edificios_multiples_optimos"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "tamano":   [40,   40,   34,   34,   28,   28,   22,   22],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8"],
        "tamano":   [40,   40,   34,   34,   28,   28,   22,   22],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"],
        "capacidad": [40,   40,   34,   34,   28,   28,   22,   22],
        "edificio":  ["A",  "A",  "B",  "B",  "C",  "C",  "D",  "D"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1", "i1", "i2", "i2",
                     "i3", "i3", "i4", "i4",
                     "i5", "i5", "i6", "i6",
                     "i7", "i7", "i8", "i8"],
        "curso_b2": ["k1", "k2", "k1", "k2",
                     "k3", "k4", "k3", "k4",
                     "k5", "k6", "k5", "k6",
                     "k7", "k8", "k7", "k8"],
        "flujo":    [20,   20,   20,   20,
                     17,   17,   17,   17,
                     14,   14,   14,   14,
                     11,   11,   11,   11],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8"],
        "libres":   [0, 0, 0, 0, 0, 0, 0, 0],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 9, ("A", "C"): 9, ("A", "D"): 9,
        ("B", "A"): 9, ("B", "B"): 1, ("B", "C"): 9, ("B", "D"): 9,
        ("C", "A"): 9, ("C", "B"): 9, ("C", "C"): 1, ("C", "D"): 9,
        ("D", "A"): 9, ("D", "B"): 9, ("D", "C"): 9, ("D", "D"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "8 cursos en 4 edificios. Flujos simétricos. gamma=9 evita cruces. Múltiples óptimos dentro de cada edificio. Costo esperado: 124.",
        "expected_status": "OPTIMAL",
        "expected_obj":    124,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


def generar_test_13():
    """
    10 cursos, 10 salas en 2 edificios (5 salas por edificio).
    gamma(A,B) = 6.
    Todos los cursos permanecen en la misma sala.
    Costo esperado: 0.
    """

    nombre_test = "M3_T13_10_cursos_2_edificios_costo_0"

    cursos_b1 = pd.DataFrame({
        "curso_id": ["i1",  "i2",  "i3",  "i4",  "i5",
                     "i6",  "i7",  "i8",  "i9",  "i10"],
        "tamano":   [60,    55,    50,    45,    40,
                     35,    30,    25,    20,    15],
    })

    cursos_b2 = pd.DataFrame({
        "curso_id": ["k1",  "k2",  "k3",  "k4",  "k5",
                     "k6",  "k7",  "k8",  "k9",  "k10"],
        "tamano":   [55,    50,    45,    40,    35,
                     30,    25,    20,    15,    10],
    })

    salas = pd.DataFrame({
        "sala_id":   ["r1",  "r2",  "r3",  "r4",  "r5",
                      "r6",  "r7",  "r8",  "r9",  "r10"],
        "capacidad": [60,    55,    50,    45,    40,
                      35,    30,    25,    20,    15],
        "edificio":  ["A",   "A",   "A",   "A",   "A",
                      "B",   "B",   "B",   "B",   "B"],
    })

    flujos = pd.DataFrame({
        "curso_b1": ["i1",  "i2",  "i3",  "i4",  "i5",
                     "i6",  "i7",  "i8",  "i9",  "i10"],
        "curso_b2": ["k1",  "k2",  "k3",  "k4",  "k5",
                     "k6",  "k7",  "k8",  "k9",  "k10"],
        "flujo":    [55,    50,    45,    40,    35,
                     30,    25,    20,    15,    10],
    })

    libres = pd.DataFrame({
        "curso_b1": ["i1",  "i2",  "i3",  "i4",  "i5",
                     "i6",  "i7",  "i8",  "i9",  "i10"],
        "libres":   [5,     5,     5,     5,     5,
                     5,     5,     5,     5,     5],
    })

    gamma = {
        ("A", "A"): 1, ("A", "B"): 6,
        ("B", "A"): 6, ("B", "B"): 1,
    }

    metadata = {
        "nombre":          nombre_test,
        "descripcion":     "10 cursos en 2 edificios con libres. Todos permanecen en la misma sala. Costo: 0.",
        "expected_status": "OPTIMAL",
        "expected_obj":    0,
    }

    guardar_test(nombre_test, cursos_b1, cursos_b2, salas, flujos, libres, gamma, metadata)


# ============================================================
# Generar todos los tests
# ============================================================


def generar_tests_pequenos():
    generar_test_01()
    generar_test_02()
    generar_test_03()
    generar_test_04()
    generar_test_05()
    print()
    print("Tests pequeños del Modelo 3 generados correctamente.")


def generar_tests_medianos():
    generar_test_06()
    generar_test_07()
    generar_test_08()
    generar_test_09()
    print()
    print("Tests medianos del Modelo 3 generados correctamente.")


def generar_tests_grandes():
    generar_test_10()
    generar_test_11()
    generar_test_12()
    generar_test_13()
    print()
    print("Tests grandes del Modelo 3 generados correctamente.")


def generar_todos_los_tests():
    generar_tests_pequenos()
    generar_tests_medianos()
    generar_tests_grandes()
    print()
    print("Todos los tests del Modelo 3 fueron generados correctamente.")


if __name__ == "__main__":
    generar_todos_los_tests()