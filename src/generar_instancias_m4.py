"""
generar_instancias_m4.py

Genera instancias sintéticas del Modelo 4 (asignación de salas en dos bloques).

Estructura física: edificios, pisos y salas con coordenadas (x, y, z).
Estructura académica: carreras y años que condicionan los flujos f_ik.
Incluye estudiantes libres (salen tras el bloque 1, sin costo) y
estudiantes ENTRANTES (llegan al bloque 2 sin haber tenido clases en el
bloque 1, sin costo). Ambos afectan capacidades, no la función objetivo.

Conservación:
    sum_k f_ik + libres_i    = tamano_i   (bloque 1)
    sum_i f_ik + entrantes_k = tamano_k   (bloque 2)

Uso:
    python src/generar_instancias_m4.py
"""

from pathlib import Path
import json
import math

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data" / "instancias_modelo4"

# ----------------------------------------------------------------------
# Parámetros físicos
# ----------------------------------------------------------------------
ALTURA_PISO = 4.0          # metros por piso -> coord_z = piso * ALTURA_PISO
SALAS_POR_PISO = 3
SEPARACION_EDIFICIOS = 70.0
ESCALA_DIST = 10.0         # costo_final = distancia / ESCALA + penalización

PEN_MISMO_PISO = 0.5
PEN_DISTINTO_PISO = 2.0
PEN_CAMBIO_EDIFICIO = 6.0

# ----------------------------------------------------------------------
# Parámetros académicos
# ----------------------------------------------------------------------
PESO_ALTO = 8.0    # misma carrera, mismo año
PESO_MEDIO = 2.0   # misma carrera, distinto año
PESO_BAJO = 0.3    # distinta carrera (electivos, ramos comunes)
ANIOS = [1, 2, 3]

FRAC_LIBRES = (0.03, 0.15)      # fracción de libres por curso B1 (uniforme)
FRAC_ENTRANTES = (0.00, 0.20)   # entrantes por curso B2, relativo al flujo entrante

CAPACIDADES = [35, 40, 45, 50, 60, 80]
TAMANO_CURSO = (20, 55)         # tamaño base de cursos B1 (uniforme entero)
TIPOS_SALA = ["catedra", "laboratorio", "auditorio"]
TIPOS_CURSO = ["catedra", "laboratorio"]

MAX_REINTENTOS = 50

# ----------------------------------------------------------------------
# Definición de instancias
# ----------------------------------------------------------------------
INSTANCIAS = [
    # Familia A: escalabilidad por tamaño
    dict(nombre="M4_E12", familia="A_escalabilidad", I=12, K=12, R=12,
         edificios=3, carreras=3, time_limit=300, seed=101),
    dict(nombre="M4_E16", familia="A_escalabilidad", I=16, K=16, R=16,
         edificios=4, carreras=4, time_limit=600, seed=102),
    dict(nombre="M4_E20", familia="A_escalabilidad", I=20, K=20, R=20,
         edificios=4, carreras=4, time_limit=900, seed=103),
    dict(nombre="M4_E24", familia="A_escalabilidad", I=24, K=24, R=24,
         edificios=5, carreras=5, time_limit=1200, seed=104),
    # Familia B: sobreoferta de salas
    dict(nombre="M4_S18_R18", familia="B_sobreoferta", I=18, K=18, R=18,
         edificios=4, carreras=4, time_limit=600, seed=201),
    dict(nombre="M4_S18_R24", familia="B_sobreoferta", I=18, K=18, R=24,
         edificios=4, carreras=4, time_limit=600, seed=202),
    dict(nombre="M4_S18_R30", familia="B_sobreoferta", I=18, K=18, R=30,
         edificios=4, carreras=4, time_limit=900, seed=203),
    dict(nombre="M4_S18_R36", familia="B_sobreoferta", I=18, K=18, R=36,
         edificios=4, carreras=4, time_limit=1200, seed=204),
]


# ----------------------------------------------------------------------
# Generación física: salas y costos
# ----------------------------------------------------------------------
def generar_salas(R, n_edificios, rng):
    filas = []
    contador_edificio = {e: 0 for e in range(n_edificios)}

    for j in range(R):
        e = j % n_edificios
        idx = contador_edificio[e]
        contador_edificio[e] += 1

        piso = idx // SALAS_POR_PISO + 1
        pos = idx % SALAS_POR_PISO

        ex = (e % 3) * SEPARACION_EDIFICIOS
        ey = (e // 3) * SEPARACION_EDIFICIOS

        filas.append({
            "sala_id": f"r{j + 1}",
            "edificio": f"E{e + 1}",
            "piso": piso,
            "capacidad": int(rng.choice(CAPACIDADES)),
            "tipo_sala": str(rng.choice(TIPOS_SALA)),
            "coord_x": round(ex + 5.0 + (pos % 2) * 8.0, 2),
            "coord_y": round(ey + 5.0 + (pos // 2) * 8.0, 2),
            "coord_z": round(piso * ALTURA_PISO, 2),
        })

    return pd.DataFrame(filas)


def generar_costos(salas):
    filas = []
    registros = salas.to_dict("records")

    for a in registros:
        for b in registros:
            if a["sala_id"] == b["sala_id"]:
                tipo, dist, costo = "misma_sala", 0.0, 0.0
            else:
                dist = math.sqrt(
                    (a["coord_x"] - b["coord_x"]) ** 2
                    + (a["coord_y"] - b["coord_y"]) ** 2
                    + (a["coord_z"] - b["coord_z"]) ** 2
                )
                if a["edificio"] != b["edificio"]:
                    tipo, pen = "cambio_edificio", PEN_CAMBIO_EDIFICIO
                elif a["piso"] != b["piso"]:
                    tipo, pen = "distinto_piso", PEN_DISTINTO_PISO
                else:
                    tipo, pen = "mismo_piso", PEN_MISMO_PISO
                costo = dist / ESCALA_DIST + pen

            filas.append({
                "sala_origen": a["sala_id"],
                "sala_destino": b["sala_id"],
                "edificio_origen": a["edificio"],
                "edificio_destino": b["edificio"],
                "piso_origen": a["piso"],
                "piso_destino": b["piso"],
                "distancia": round(dist, 4),
                "tipo_transicion": tipo,
                "costo_final": round(costo, 4),
                # Alias por compatibilidad con código previo del proyecto.
                "costo": round(costo, 4),
            })

    return pd.DataFrame(filas)


# ----------------------------------------------------------------------
# Generación académica: cursos, flujos, libres y entrantes
# ----------------------------------------------------------------------
def generar_cursos_b1(I, n_carreras, rng):
    filas = []
    for idx in range(I):
        carrera = f"C{idx % n_carreras + 1}"
        anio = ANIOS[(idx // n_carreras) % len(ANIOS)]
        filas.append({
            "curso_id": f"i{idx + 1}",
            "bloque": 1,
            "tamano": int(rng.integers(TAMANO_CURSO[0], TAMANO_CURSO[1] + 1)),
            "carrera": carrera,
            "anio": anio,
            "grupo": f"{carrera}_{anio}",
            "tipo_curso": str(rng.choice(TIPOS_CURSO)),
        })
    return pd.DataFrame(filas)


def atributos_cursos_b2(K, n_carreras, rng):
    filas = []
    for idx in range(K):
        carrera = f"C{idx % n_carreras + 1}"
        anio = ANIOS[(idx // n_carreras) % len(ANIOS)]
        filas.append({
            "curso_id": f"k{idx + 1}",
            "bloque": 2,
            "carrera": carrera,
            "anio": anio,
            "grupo": f"{carrera}_{anio}",
            "tipo_curso": str(rng.choice(TIPOS_CURSO)),
        })
    return pd.DataFrame(filas)


def generar_flujos(cursos_b1, cursos_b2, rng):
    """Devuelve matriz F (I x K), libres por curso B1 y entrantes por curso B2.

    Los entrantes son alumnos que NO tuvieron clases en el bloque 1 pero
    sí en el bloque 2: no aparecen en F ni generan costo, pero suman al
    tamaño del curso B2 (afectan capacidad).
    """
    b1 = cursos_b1.to_dict("records")
    b2 = cursos_b2.to_dict("records")
    I, K = len(b1), len(b2)

    F = np.zeros((I, K), dtype=int)
    libres = np.zeros(I, dtype=int)

    for ii, ci in enumerate(b1):
        frac_libres = rng.uniform(*FRAC_LIBRES)
        libres[ii] = int(rng.binomial(ci["tamano"], frac_libres))
        movers = ci["tamano"] - libres[ii]

        pesos = np.array([
            PESO_ALTO if (ci["carrera"] == ck["carrera"] and ci["anio"] == ck["anio"])
            else PESO_MEDIO if ci["carrera"] == ck["carrera"]
            else PESO_BAJO
            for ck in b2
        ])
        F[ii, :] = rng.multinomial(movers, pesos / pesos.sum())

    inflow = F.sum(axis=0)
    entrantes = np.zeros(K, dtype=int)
    for kk in range(K):
        frac = rng.uniform(*FRAC_ENTRANTES)
        entrantes[kk] = int(rng.integers(0, max(2, int(inflow[kk] * frac) + 1)))

    # Tamaño mínimo razonable para cursos B2 (se completa con entrantes).
    tamanos_b2 = inflow + entrantes
    for kk in range(K):
        if tamanos_b2[kk] < 5:
            entrantes[kk] += 5 - tamanos_b2[kk]
            tamanos_b2[kk] = 5

    return F, libres, entrantes, tamanos_b2


def cabe_asignacion(tamanos, capacidades):
    """Matching factible (un curso por sala) sii ordenando ambos de mayor a
    menor, cada curso cabe en la sala correspondiente."""
    t = sorted(tamanos, reverse=True)
    c = sorted(capacidades, reverse=True)
    if len(t) > len(c):
        return False
    return all(t[j] <= c[j] for j in range(len(t)))


# ----------------------------------------------------------------------
# Construcción y guardado de instancias
# ----------------------------------------------------------------------
def construir_instancia(cfg):
    for intento in range(MAX_REINTENTOS):
        rng = np.random.default_rng(cfg["seed"] + 1000 * intento)

        salas = generar_salas(cfg["R"], cfg["edificios"], rng)
        cursos_b1 = generar_cursos_b1(cfg["I"], cfg["carreras"], rng)
        cursos_b2 = atributos_cursos_b2(cfg["K"], cfg["carreras"], rng)

        F, libres, entrantes, tamanos_b2 = generar_flujos(cursos_b1, cursos_b2, rng)
        cursos_b2 = cursos_b2.copy()
        cursos_b2.insert(2, "tamano", tamanos_b2)

        caps = salas["capacidad"].tolist()
        if cabe_asignacion(cursos_b1["tamano"].tolist(), caps) and \
           cabe_asignacion(cursos_b2["tamano"].tolist(), caps):
            return salas, cursos_b1, cursos_b2, F, libres, entrantes, intento

    raise RuntimeError(f"No se logró instancia factible para {cfg['nombre']} "
                       f"tras {MAX_REINTENTOS} intentos.")


def guardar_instancia(cfg, salas, cursos_b1, cursos_b2, F, libres, entrantes, intento):
    carpeta = DATA_DIR / cfg["nombre"]
    carpeta.mkdir(parents=True, exist_ok=True)

    ids_b1 = cursos_b1["curso_id"].tolist()
    ids_b2 = cursos_b2["curso_id"].tolist()

    # Verificación de conservación (B1 y B2, incluyendo entrantes).
    assert all(F[ii, :].sum() + libres[ii] == cursos_b1["tamano"].iloc[ii]
               for ii in range(len(ids_b1)))
    assert all(F[:, kk].sum() + entrantes[kk] == cursos_b2["tamano"].iloc[kk]
               for kk in range(len(ids_b2)))

    flujos = pd.DataFrame(
        [{"curso_b1": ids_b1[ii], "curso_b2": ids_b2[kk], "flujo": int(F[ii, kk])}
         for ii in range(len(ids_b1)) for kk in range(len(ids_b2))
         if F[ii, kk] > 0]
    )

    cursos_b1.to_csv(carpeta / "cursos_b1.csv", index=False)
    cursos_b2.to_csv(carpeta / "cursos_b2.csv", index=False)
    salas.to_csv(carpeta / "salas.csv", index=False)
    flujos.to_csv(carpeta / "flujos.csv", index=False)
    pd.DataFrame({"curso_b1": ids_b1, "libres": libres}) \
        .to_csv(carpeta / "libres.csv", index=False)
    pd.DataFrame({"curso_b2": ids_b2, "entrantes": entrantes}) \
        .to_csv(carpeta / "entrantes.csv", index=False)
    generar_costos(salas).to_csv(carpeta / "costos_sala_sala.csv", index=False)

    metadata = {
        "nombre_instancia": cfg["nombre"],
        "familia": cfg["familia"],
        "I": cfg["I"], "K": cfg["K"], "R": cfg["R"],
        "edificios": cfg["edificios"], "carreras": cfg["carreras"],
        "time_limit": cfg["time_limit"],
        "seed": cfg["seed"], "seed_efectiva": cfg["seed"] + 1000 * intento,
        "total_libres": int(libres.sum()),
        "total_entrantes": int(entrantes.sum()),
        "descripcion_costos": (
            f"costo_final = distancia_euclidiana/{ESCALA_DIST} + penalizacion; "
            f"0 misma sala, {PEN_MISMO_PISO} mismo piso, {PEN_DISTINTO_PISO} "
            f"distinto piso, {PEN_CAMBIO_EDIFICIO} cambio de edificio. "
            f"coord_z = piso * {ALTURA_PISO}."
        ),
        "descripcion_flujos": (
            f"Pesos multinomiales por afinidad academica: {PESO_ALTO} misma "
            f"carrera y anio, {PESO_MEDIO} misma carrera distinto anio, "
            f"{PESO_BAJO} distinta carrera. Libres por curso B1: fraccion "
            f"uniforme en {FRAC_LIBRES}."
        ),
        "descripcion_entrantes": (
            "Estudiantes entrantes llegan al bloque 2 sin clases en el bloque 1; "
            "no generan costo pero suman al tamano del curso B2 "
            f"(sum_i f_ik + entrantes_k = tamano_k). Fraccion uniforme en "
            f"{FRAC_ENTRANTES} del flujo entrante."
        ),
    }
    with open(carpeta / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return carpeta


def generar_todas():
    rutas = []
    for cfg in INSTANCIAS:
        partes = construir_instancia(cfg)
        ruta = guardar_instancia(cfg, *partes)
        rutas.append(ruta)
        print(f"[OK] {cfg['nombre']} -> {ruta}")
    return rutas


if __name__ == "__main__":
    generar_todas()
