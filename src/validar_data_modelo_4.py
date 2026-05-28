from pathlib import Path
import json
import pandas as pd


# ============================================================
# Configuración general
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT_DIR / "data" / "modelo4"


# ============================================================
# Excepción personalizada
# ============================================================


class ErrorValidacion(Exception):
    pass


# ============================================================
# Funciones auxiliares
# ============================================================


def leer_csv(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        raise ErrorValidacion(f"No existe el archivo: {ruta.name}")
    return pd.read_csv(ruta)


def leer_metadata(carpeta: Path) -> dict:
    ruta = carpeta / "metadata.json"
    if not ruta.exists():
        return {}

    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def normalizar_columna_tamano(df: pd.DataFrame, nombre_archivo: str) -> pd.DataFrame:
    """
    Permite usar 'tamano' o 'tamaño'.
    Internamente se transforma a 'tamano'.
    """
    df = df.copy()

    if "tamano" in df.columns:
        return df

    if "tamaño" in df.columns:
        df = df.rename(columns={"tamaño": "tamano"})
        return df

    raise ErrorValidacion(
        f"El archivo {nombre_archivo} debe tener columna 'tamano' o 'tamaño'."
    )


def exigir_columnas(df: pd.DataFrame, columnas_requeridas, nombre_archivo: str):
    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        raise ErrorValidacion(
            f"Al archivo {nombre_archivo} le faltan columnas: {faltantes}"
        )


def exigir_no_vacios(df: pd.DataFrame, columnas, nombre_archivo: str):
    for col in columnas:
        if df[col].isna().any():
            raise ErrorValidacion(
                f"El archivo {nombre_archivo} tiene valores vacíos en la columna '{col}'."
            )


def exigir_no_negativos(df: pd.DataFrame, columnas, nombre_archivo: str):
    for col in columnas:
        if (df[col] < 0).any():
            raise ErrorValidacion(
                f"El archivo {nombre_archivo} tiene valores negativos en la columna '{col}'."
            )


def exigir_ids_unicos(df: pd.DataFrame, columna_id: str, nombre_archivo: str):
    duplicados = df[df[columna_id].duplicated()][columna_id].tolist()

    if duplicados:
        raise ErrorValidacion(
            f"El archivo {nombre_archivo} tiene IDs duplicados en '{columna_id}': {duplicados}"
        )


def comparar_float(a, b, tol=1e-9):
    return abs(float(a) - float(b)) <= tol


# ============================================================
# Validaciones principales
# ============================================================


def validar_archivos_basicos(carpeta: Path):
    archivos = [
        "cursos_b1.csv",
        "cursos_b2.csv",
        "salas.csv",
        "flujos.csv",
        "libres.csv",
        "entrantes.csv",
        "costos_sala_sala.csv",
    ]

    for archivo in archivos:
        ruta = carpeta / archivo
        if not ruta.exists():
            raise ErrorValidacion(f"Falta el archivo obligatorio: {archivo}")


def cargar_instancia(carpeta: Path):
    cursos_b1 = leer_csv(carpeta / "cursos_b1.csv")
    cursos_b2 = leer_csv(carpeta / "cursos_b2.csv")
    salas = leer_csv(carpeta / "salas.csv")
    flujos = leer_csv(carpeta / "flujos.csv")
    libres = leer_csv(carpeta / "libres.csv")
    entrantes = leer_csv(carpeta / "entrantes.csv")
    costos = leer_csv(carpeta / "costos_sala_sala.csv")
    metadata = leer_metadata(carpeta)

    cursos_b1 = normalizar_columna_tamano(cursos_b1, "cursos_b1.csv")
    cursos_b2 = normalizar_columna_tamano(cursos_b2, "cursos_b2.csv")

    return {
        "cursos_b1": cursos_b1,
        "cursos_b2": cursos_b2,
        "salas": salas,
        "flujos": flujos,
        "libres": libres,
        "entrantes": entrantes,
        "costos": costos,
        "metadata": metadata,
    }


def validar_columnas_y_tipos(data):
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    salas = data["salas"]
    flujos = data["flujos"]
    libres = data["libres"]
    entrantes = data["entrantes"]
    costos = data["costos"]

    exigir_columnas(cursos_b1, ["curso_id", "tamano"], "cursos_b1.csv")
    exigir_columnas(cursos_b2, ["curso_id", "tamano"], "cursos_b2.csv")
    exigir_columnas(salas, ["sala_id", "capacidad", "edificio"], "salas.csv")
    exigir_columnas(flujos, ["curso_b1", "curso_b2", "flujo"], "flujos.csv")
    exigir_columnas(libres, ["curso_b1", "libres"], "libres.csv")
    exigir_columnas(entrantes, ["curso_b2", "entrantes"], "entrantes.csv")
    exigir_columnas(
        costos, ["sala_origen", "sala_destino", "costo"], "costos_sala_sala.csv"
    )

    exigir_no_vacios(cursos_b1, ["curso_id", "tamano"], "cursos_b1.csv")
    exigir_no_vacios(cursos_b2, ["curso_id", "tamano"], "cursos_b2.csv")
    exigir_no_vacios(salas, ["sala_id", "capacidad", "edificio"], "salas.csv")
    exigir_no_vacios(flujos, ["curso_b1", "curso_b2", "flujo"], "flujos.csv")
    exigir_no_vacios(libres, ["curso_b1", "libres"], "libres.csv")
    exigir_no_vacios(entrantes, ["curso_b2", "entrantes"], "entrantes.csv")
    exigir_no_vacios(
        costos, ["sala_origen", "sala_destino", "costo"], "costos_sala_sala.csv"
    )

    exigir_no_negativos(cursos_b1, ["tamano"], "cursos_b1.csv")
    exigir_no_negativos(cursos_b2, ["tamano"], "cursos_b2.csv")
    exigir_no_negativos(salas, ["capacidad"], "salas.csv")
    exigir_no_negativos(flujos, ["flujo"], "flujos.csv")
    exigir_no_negativos(libres, ["libres"], "libres.csv")
    exigir_no_negativos(entrantes, ["entrantes"], "entrantes.csv")
    exigir_no_negativos(costos, ["costo"], "costos_sala_sala.csv")

    if (salas["capacidad"] <= 0).any():
        raise ErrorValidacion(
            "Todas las salas deben tener capacidad estrictamente positiva."
        )


def validar_ids(data):
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    salas = data["salas"]

    exigir_ids_unicos(cursos_b1, "curso_id", "cursos_b1.csv")
    exigir_ids_unicos(cursos_b2, "curso_id", "cursos_b2.csv")
    exigir_ids_unicos(salas, "sala_id", "salas.csv")


def validar_referencias(data):
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    salas = data["salas"]
    flujos = data["flujos"]
    libres = data["libres"]
    entrantes = data["entrantes"]
    costos = data["costos"]

    ids_b1 = set(cursos_b1["curso_id"])
    ids_b2 = set(cursos_b2["curso_id"])
    ids_salas = set(salas["sala_id"])

    ref_b1_flujos = set(flujos["curso_b1"])
    ref_b2_flujos = set(flujos["curso_b2"])
    ref_b1_libres = set(libres["curso_b1"])
    ref_b2_entrantes = set(entrantes["curso_b2"])

    if not ref_b1_flujos.issubset(ids_b1):
        raise ErrorValidacion(
            f"flujos.csv referencia cursos B1 inexistentes: {sorted(ref_b1_flujos - ids_b1)}"
        )

    if not ref_b2_flujos.issubset(ids_b2):
        raise ErrorValidacion(
            f"flujos.csv referencia cursos B2 inexistentes: {sorted(ref_b2_flujos - ids_b2)}"
        )

    if ref_b1_libres != ids_b1:
        raise ErrorValidacion(
            "libres.csv debe tener exactamente una fila por cada curso del bloque 1. "
            f"Faltan: {sorted(ids_b1 - ref_b1_libres)}; sobran: {sorted(ref_b1_libres - ids_b1)}"
        )

    if ref_b2_entrantes != ids_b2:
        raise ErrorValidacion(
            "entrantes.csv debe tener exactamente una fila por cada curso del bloque 2. "
            f"Faltan: {sorted(ids_b2 - ref_b2_entrantes)}; sobran: {sorted(ref_b2_entrantes - ids_b2)}"
        )

    ref_salas_origen = set(costos["sala_origen"])
    ref_salas_destino = set(costos["sala_destino"])

    if not ref_salas_origen.issubset(ids_salas):
        raise ErrorValidacion(
            f"costos_sala_sala.csv tiene salas de origen inexistentes: {sorted(ref_salas_origen - ids_salas)}"
        )

    if not ref_salas_destino.issubset(ids_salas):
        raise ErrorValidacion(
            f"costos_sala_sala.csv tiene salas de destino inexistentes: {sorted(ref_salas_destino - ids_salas)}"
        )


def validar_conservacion_estudiantes(data):
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    flujos = data["flujos"]
    libres = data["libres"]
    entrantes = data["entrantes"]

    tam_b1 = dict(zip(cursos_b1["curso_id"], cursos_b1["tamano"]))
    tam_b2 = dict(zip(cursos_b2["curso_id"], cursos_b2["tamano"]))

    libres_dict = dict(zip(libres["curso_b1"], libres["libres"]))
    entrantes_dict = dict(zip(entrantes["curso_b2"], entrantes["entrantes"]))

    flujo_salida = flujos.groupby("curso_b1")["flujo"].sum().to_dict()
    flujo_entrada = flujos.groupby("curso_b2")["flujo"].sum().to_dict()

    for curso_id, tamano in tam_b1.items():
        salida = flujo_salida.get(curso_id, 0)
        libres_i = libres_dict.get(curso_id, 0)

        if not comparar_float(salida + libres_i, tamano):
            raise ErrorValidacion(
                f"Conservación incorrecta en B1 para {curso_id}: "
                f"flujos que salen ({salida}) + libres ({libres_i}) "
                f"= {salida + libres_i}, pero tamano = {tamano}."
            )

    for curso_id, tamano in tam_b2.items():
        entrada = flujo_entrada.get(curso_id, 0)
        entrantes_k = entrantes_dict.get(curso_id, 0)

        if not comparar_float(entrada + entrantes_k, tamano):
            raise ErrorValidacion(
                f"Conservación incorrecta en B2 para {curso_id}: "
                f"flujos que llegan ({entrada}) + entrantes ({entrantes_k}) "
                f"= {entrada + entrantes_k}, pero tamano = {tamano}."
            )

    total_continuan_desde_b1 = flujos["flujo"].sum()
    total_continuan_hacia_b2 = flujos["flujo"].sum()

    if not comparar_float(total_continuan_desde_b1, total_continuan_hacia_b2):
        raise ErrorValidacion(
            "Error global: la suma de flujos de continuidad no coincide."
        )


def validar_matriz_costos(data):
    salas = data["salas"]
    costos = data["costos"]

    ids_salas = list(salas["sala_id"])
    set_salas = set(ids_salas)

    # No debe haber pares repetidos.
    duplicados = costos[costos.duplicated(subset=["sala_origen", "sala_destino"])]

    if not duplicados.empty:
        pares = duplicados[["sala_origen", "sala_destino"]].values.tolist()
        raise ErrorValidacion(
            f"costos_sala_sala.csv tiene pares origen-destino duplicados: {pares}"
        )

    pares_esperados = {(r, s) for r in set_salas for s in set_salas}
    pares_obtenidos = set(zip(costos["sala_origen"], costos["sala_destino"]))

    faltantes = pares_esperados - pares_obtenidos
    sobrantes = pares_obtenidos - pares_esperados

    if faltantes:
        raise ErrorValidacion(
            f"La matriz de costos está incompleta. Faltan pares: {sorted(faltantes)}"
        )

    if sobrantes:
        raise ErrorValidacion(
            f"La matriz de costos tiene pares sobrantes o inválidos: {sorted(sobrantes)}"
        )

    n = len(ids_salas)
    esperado = n * n

    if len(costos) != esperado:
        raise ErrorValidacion(
            f"La matriz de costos debe tener {esperado} filas, pero tiene {len(costos)}."
        )

    # En este modelo asumimos que permanecer en la misma sala cuesta 0.
    costos_diag = costos[costos["sala_origen"] == costos["sala_destino"]]

    for _, fila in costos_diag.iterrows():
        if not comparar_float(fila["costo"], 0):
            raise ErrorValidacion(
                f"El costo diagonal c({fila['sala_origen']},{fila['sala_destino']}) "
                f"debe ser 0, pero es {fila['costo']}."
            )


def advertencias_factibilidad_basica(data):
    """
    Estas advertencias NO bloquean la validación.

    Sirven para detectar casos que probablemente serán INFEASIBLE en Gurobi.
    Por eso no se levantan como error, porque algunos tests están diseñados
    intencionalmente para ser infactibles.
    """
    cursos_b1 = data["cursos_b1"]
    cursos_b2 = data["cursos_b2"]
    salas = data["salas"]

    advertencias = []

    max_cap = salas["capacidad"].max()
    n_salas = len(salas)

    for _, fila in cursos_b1.iterrows():
        if fila["tamano"] > max_cap:
            advertencias.append(
                f"Curso B1 {fila['curso_id']} tiene tamano {fila['tamano']} "
                f"mayor que la capacidad máxima disponible {max_cap}."
            )

    for _, fila in cursos_b2.iterrows():
        if fila["tamano"] > max_cap:
            advertencias.append(
                f"Curso B2 {fila['curso_id']} tiene tamano {fila['tamano']} "
                f"mayor que la capacidad máxima disponible {max_cap}."
            )

    if len(cursos_b1) > n_salas:
        advertencias.append(
            f"Hay {len(cursos_b1)} cursos en B1 y solo {n_salas} salas."
        )

    if len(cursos_b2) > n_salas:
        advertencias.append(
            f"Hay {len(cursos_b2)} cursos en B2 y solo {n_salas} salas."
        )

    return advertencias


# ============================================================
# Función principal de validación de una instancia
# ============================================================


def validar_instancia_modelo_4(carpeta: Path):
    validar_archivos_basicos(carpeta)

    data = cargar_instancia(carpeta)

    validar_columnas_y_tipos(data)
    validar_ids(data)
    validar_referencias(data)
    validar_conservacion_estudiantes(data)
    validar_matriz_costos(data)

    advertencias = advertencias_factibilidad_basica(data)

    return advertencias


# ============================================================
# Validación masiva de todas las carpetas
# ============================================================


def validar_todas_las_instancias(base_dir: Path = BASE_DIR):
    if not base_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta base: {base_dir}")

    carpetas = sorted([p for p in base_dir.iterdir() if p.is_dir()])

    if not carpetas:
        print(f"No hay carpetas de instancias en: {base_dir}")
        return

    print(f"Validando instancias en: {base_dir}\n")

    total = 0
    ok = 0
    errores = 0
    esperados_error = 0

    for carpeta in carpetas:
        total += 1
        metadata = leer_metadata(carpeta)
        status_esperado = metadata.get("status_esperado")

        try:
            advertencias = validar_instancia_modelo_4(carpeta)

            if status_esperado == "ERROR_VALIDACION":
                errores += 1
                print(f"[ERROR] {carpeta.name}")
                print(
                    "        La instancia fue válida, pero se esperaba ERROR_VALIDACION."
                )
            else:
                ok += 1
                print(f"[OK] {carpeta.name}")

                for adv in advertencias:
                    print(f"     [ADVERTENCIA] {adv}")

        except ErrorValidacion as e:
            if status_esperado == "ERROR_VALIDACION":
                esperados_error += 1
                print(f"[OK] {carpeta.name}")
                print(f"     Error de validación esperado: {e}")
            else:
                errores += 1
                print(f"[ERROR] {carpeta.name}")
                print(f"        {e}")

    print("\nResumen")
    print(f"Total de instancias revisadas: {total}")
    print(f"Instancias válidas: {ok}")
    print(f"Errores de validación esperados: {esperados_error}")
    print(f"Errores no esperados: {errores}")


# ============================================================
# Ejecución directa
# ============================================================

if __name__ == "__main__":
    validar_todas_las_instancias()
