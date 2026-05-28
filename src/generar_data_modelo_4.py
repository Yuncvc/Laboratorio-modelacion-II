from pathlib import Path
import csv
import json
import shutil


# ============================================================
# Configuración general
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT_DIR / "data" / "modelo4"

# Si en tus modelos anteriores usaste "tamaño" con ñ,
# cambia esta constante a "tamaño".
COL_TAMANO = "tamano"


# ============================================================
# Funciones auxiliares para escribir archivos
# ============================================================

def escribir_csv(ruta_archivo, filas, columnas):
    """
    Escribe un archivo CSV a partir de una lista de diccionarios.
    No valida los datos; solo los guarda.
    """
    ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def escribir_json(ruta_archivo, data):
    """
    Escribe metadata de la instancia.
    Sirve para guardar el propósito y el resultado esperado.
    """
    ruta_archivo.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def construir_costos_completos(salas, costos_pares=None, costo_default=5, diagonal=0):
    """
    Construye una matriz completa de costos sala-sala.

    salas: lista de diccionarios con clave 'sala_id'.
    costos_pares: diccionario con costos especiales.
                  Ejemplo:
                  {
                      ("r1", "r2"): 2,
                      ("r1", "r3"): 10
                  }

                  Se interpreta como simétrico:
                  si se entrega ("r1", "r2"), también se crea ("r2", "r1").

    costo_default: costo usado para pares no especificados.
    diagonal: costo de permanecer en la misma sala.
    """
    costos_pares = costos_pares or {}

    salas_ids = [s["sala_id"] for s in salas]

    costos = {}

    for (origen, destino), costo in costos_pares.items():
        costos[(origen, destino)] = costo
        costos[(destino, origen)] = costo

    filas = []

    for origen in salas_ids:
        for destino in salas_ids:
            if origen == destino:
                costo = diagonal
            else:
                costo = costos.get((origen, destino), costo_default)

            filas.append({
                "sala_origen": origen,
                "sala_destino": destino,
                "costo": costo
            })

    return filas


def crear_instancia(
    nombre,
    cursos_b1,
    cursos_b2,
    salas,
    flujos,
    libres,
    entrantes,
    costos_sala_sala,
    metadata,
    sobrescribir=True
):
    """
    Crea una carpeta de test para el Modelo 4 con todos sus CSV.
    No valida consistencia ni factibilidad.
    """
    carpeta = BASE_DIR / nombre

    if carpeta.exists() and sobrescribir:
        shutil.rmtree(carpeta)

    carpeta.mkdir(parents=True, exist_ok=True)

    escribir_csv(
        carpeta / "cursos_b1.csv",
        cursos_b1,
        ["curso_id", COL_TAMANO]
    )

    escribir_csv(
        carpeta / "cursos_b2.csv",
        cursos_b2,
        ["curso_id", COL_TAMANO]
    )

    escribir_csv(
        carpeta / "salas.csv",
        salas,
        ["sala_id", "capacidad", "edificio"]
    )

    escribir_csv(
        carpeta / "flujos.csv",
        flujos,
        ["curso_b1", "curso_b2", "flujo"]
    )

    escribir_csv(
        carpeta / "libres.csv",
        libres,
        ["curso_b1", "libres"]
    )

    escribir_csv(
        carpeta / "entrantes.csv",
        entrantes,
        ["curso_b2", "entrantes"]
    )

    escribir_csv(
        carpeta / "costos_sala_sala.csv",
        costos_sala_sala,
        ["sala_origen", "sala_destino", "costo"]
    )

    escribir_json(
        carpeta / "metadata.json",
        metadata
    )

    print(f"Instancia creada: {carpeta}")


# ============================================================
# Instancias del Modelo 4
# ============================================================

def generar_todas_las_instancias_modelo_4():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # M4_T01 - Misma sala, costo 0
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 30, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 20, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T01_misma_sala_costo_0",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 30},
            {"curso_id": "i2", COL_TAMANO: 20},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 30},
            {"curso_id": "k2", COL_TAMANO: 20},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 20},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={("r1", "r2"): 5}
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T01",
            "proposito": "Verificar que permanecer en la misma sala tiene costo 0.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 0
        }
    )

    # ------------------------------------------------------------
    # M4_T02 - Costo detallado forzado por capacidad
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "A"},
    ]

    crear_instancia(
        nombre="M4_T02_costo_detallado_forzado",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 50},
            {"curso_id": "i2", COL_TAMANO: 30},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 30},
            {"curso_id": "k2", COL_TAMANO: 50},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
            {"curso_b1": "i1", "curso_b2": "k2", "flujo": 20},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 30},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={("r1", "r2"): 2}
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T02",
            "proposito": "Verificar que se utiliza el costo detallado sala-sala y no un costo binario.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 120
        }
    )

    # ------------------------------------------------------------
    # M4_T03 - Elección de salas por matriz de costos
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r3", "capacidad": 10, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T03_eleccion_por_matriz_costos",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 10},
            {"curso_id": "i2", COL_TAMANO: 10},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 10},
            {"curso_id": "k2", COL_TAMANO: 10},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 6},
            {"curso_b1": "i1", "curso_b2": "k2", "flujo": 4},
            {"curso_b1": "i2", "curso_b2": "k1", "flujo": 4},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 6},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={
                ("r1", "r2"): 1,
                ("r1", "r3"): 5,
                ("r2", "r3"): 5,
            }
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T03",
            "proposito": "Verificar que el modelo escoge las salas de menor costo según la matriz detallada.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 8
        }
    )

    # ------------------------------------------------------------
    # M4_T04 - Estudiantes entrantes al segundo bloque
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "A"},
        {"sala_id": "r3", "capacidad": 20, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T04_estudiantes_entrantes",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 30},
            {"curso_id": "i2", COL_TAMANO: 20},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 50},
            {"curso_id": "k2", COL_TAMANO: 20},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 20},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 20},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={
                ("r1", "r2"): 2,
                ("r1", "r3"): 4,
                ("r2", "r3"): 1,
            }
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T04",
            "proposito": "Verificar que estudiantes entrantes aumentan el tamaño del curso del bloque 2, pero no generan costo.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 0
        }
    )

    # ------------------------------------------------------------
    # M4_T05 - Estudiantes salientes desde el primer bloque
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "A"},
        {"sala_id": "r3", "capacidad": 20, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T05_estudiantes_salientes",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 50},
            {"curso_id": "i2", COL_TAMANO: 20},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 30},
            {"curso_id": "k2", COL_TAMANO: 20},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 20},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 20},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={
                ("r1", "r2"): 2,
                ("r1", "r3"): 4,
                ("r2", "r3"): 1,
            }
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T05",
            "proposito": "Verificar que estudiantes salientes afectan la capacidad del bloque 1, pero no generan costo.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 0
        }
    )

    # ------------------------------------------------------------
    # M4_T06 - Entrantes y salientes cambian el óptimo por capacidad
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "A"},
    ]

    crear_instancia(
        nombre="M4_T06_entrantes_salientes_cambian_optimo",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 50},
            {"curso_id": "i2", COL_TAMANO: 30},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 30},
            {"curso_id": "k2", COL_TAMANO: 50},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 30},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 20},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 20},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={("r1", "r2"): 2}
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T06",
            "proposito": "Verificar que entrantes y salientes no generan costo directo, pero sí pueden cambiar el óptimo por capacidad.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 120
        }
    )

    # ------------------------------------------------------------
    # M4_T07 - Infactible por estudiantes entrantes
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T07_infactible_por_entrantes",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 30},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 60},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 30},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={("r1", "r2"): 3}
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T07",
            "proposito": "Verificar infactibilidad cuando estudiantes entrantes hacen que un curso del bloque 2 no quepa en ninguna sala.",
            "status_esperado": "INFEASIBLE",
            "costo_esperado": None
        }
    )

    # ------------------------------------------------------------
    # M4_T08 - Infactible por estudiantes salientes
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 50, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 30, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T08_infactible_por_salientes",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 60},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 30},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 30},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 30},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={("r1", "r2"): 3}
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T08",
            "proposito": "Verificar infactibilidad cuando estudiantes salientes hacen que un curso del bloque 1 no quepa en ninguna sala.",
            "status_esperado": "INFEASIBLE",
            "costo_esperado": None
        }
    )

    # ------------------------------------------------------------
    # M4_T09 - Matriz de costos incompleta
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r3", "capacidad": 10, "edificio": "B"},
    ]

    costos_completos = construir_costos_completos(
        salas,
        costos_pares={
            ("r1", "r2"): 1,
            ("r1", "r3"): 5,
            ("r2", "r3"): 5,
        }
    )

    # Se elimina intencionalmente un par para probar luego la validación.
    costos_incompletos = [
        fila for fila in costos_completos
        if not (
            fila["sala_origen"] == "r3"
            and fila["sala_destino"] == "r1"
        )
    ]

    crear_instancia(
        nombre="M4_T09_matriz_costos_incompleta",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 10},
            {"curso_id": "i2", COL_TAMANO: 10},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 10},
            {"curso_id": "k2", COL_TAMANO: 10},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 10},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 10},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=costos_incompletos,
        metadata={
            "modelo": 4,
            "test": "M4_T09",
            "proposito": "Dejar una matriz de costos incompleta para probar posteriormente la validación.",
            "status_esperado": "ERROR_VALIDACION",
            "costo_esperado": None
        }
    )

    # ------------------------------------------------------------
    # M4_T10 - Costos no equivalentes a gamma por edificio
    # ------------------------------------------------------------

    salas = [
        {"sala_id": "r1", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r2", "capacidad": 10, "edificio": "A"},
        {"sala_id": "r3", "capacidad": 10, "edificio": "B"},
    ]

    crear_instancia(
        nombre="M4_T10_costos_no_equivalentes_a_gamma",
        cursos_b1=[
            {"curso_id": "i1", COL_TAMANO: 10},
            {"curso_id": "i2", COL_TAMANO: 10},
        ],
        cursos_b2=[
            {"curso_id": "k1", COL_TAMANO: 10},
            {"curso_id": "k2", COL_TAMANO: 10},
        ],
        salas=salas,
        flujos=[
            {"curso_b1": "i1", "curso_b2": "k1", "flujo": 6},
            {"curso_b1": "i1", "curso_b2": "k2", "flujo": 4},
            {"curso_b1": "i2", "curso_b2": "k1", "flujo": 4},
            {"curso_b1": "i2", "curso_b2": "k2", "flujo": 6},
        ],
        libres=[
            {"curso_b1": "i1", "libres": 0},
            {"curso_b1": "i2", "libres": 0},
        ],
        entrantes=[
            {"curso_b2": "k1", "entrantes": 0},
            {"curso_b2": "k2", "entrantes": 0},
        ],
        costos_sala_sala=construir_costos_completos(
            salas,
            costos_pares={
                ("r1", "r2"): 10,
                ("r1", "r3"): 2,
                ("r2", "r3"): 10,
            }
        ),
        metadata={
            "modelo": 4,
            "test": "M4_T10",
            "proposito": "Verificar que el Modelo 4 usa directamente la matriz sala-sala, incluso si una sala de otro edificio es más barata.",
            "status_esperado": "OPTIMAL",
            "costo_esperado": 16
        }
    )

    print("\nTodas las instancias del Modelo 4 fueron creadas correctamente.")
    print(f"Ruta base: {BASE_DIR}")


# ============================================================
# Ejecución directa
# ============================================================

if __name__ == "__main__":
    generar_todas_las_instancias_modelo_4()