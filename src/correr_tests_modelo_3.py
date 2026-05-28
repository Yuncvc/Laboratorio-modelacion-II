from pathlib import Path
import json
import time

from modelo_3_gurobi import resolver_modelo_3


def leer_metadata(carpeta_test):
    ruta_metadata = carpeta_test / "metadata.json"
    with open(ruta_metadata, "r", encoding="utf-8") as archivo:
        metadata = json.load(archivo)
    return metadata


def comparar_resultado(nombre_test, metadata, resultado):
    """
    Compara el resultado obtenido con el resultado esperado.
    Retorna True si el test pasa.
    """

    esperado_status = metadata["expected_status"]
    obtenido_status = resultado["status"]

    print(f"Status esperado:  {esperado_status}")
    print(f"Status obtenido:  {obtenido_status}")

    if obtenido_status != esperado_status:
        print("Resultado: ERROR")
        print("Motivo: el status no coincide.")
        return False

    if esperado_status == "INFEASIBLE":
        print("Resultado: OK")
        return True

    esperado_obj = metadata["expected_obj"]
    obtenido_obj = resultado["objetivo"]

    print(f"Objetivo esperado: {esperado_obj}")
    print(f"Objetivo obtenido: {obtenido_obj}")

    tolerancia = 1e-6

    if abs(obtenido_obj - esperado_obj) > tolerancia:
        print("Resultado: ERROR")
        print("Motivo: el valor objetivo no coincide.")
        return False

    print("Resultado: OK")
    return True


def clasificar_test(nombre_test):
    """
    Retorna el grupo al que pertenece el test según su número.
    """
    numero = int(nombre_test.split("_T")[1].split("_")[0])
    if numero <= 5:
        return "pequeño"
    elif numero <= 9:
        return "mediano"
    else:
        return "grande"


def correr_tests_modelo_3():
    """
    Corre todos los tests guardados en data/modelo3 y reporta tiempos de ejecución.
    """

    carpeta_base = Path("data/modelo3")

    if not carpeta_base.exists():
        print("ERROR: no existe la carpeta data/modelo3")
        print("Primero ejecuta:")
        print("  python src/generar_data_modelo_3.py")
        return

    carpetas_tests = sorted(c for c in carpeta_base.iterdir() if c.is_dir())

    if not carpetas_tests:
        print("ERROR: no se encontraron carpetas de tests.")
        return

    print("=" * 70)
    print("CORRIENDO TESTS DEL MODELO 3")
    print("=" * 70)

    tests_ok     = 0
    tests_error  = 0
    registros    = []

    tiempo_inicio_total = time.time()

    for carpeta_test in carpetas_tests:

        nombre_test = carpeta_test.name
        grupo       = clasificar_test(nombre_test)

        print()
        print("-" * 70)
        print(f"Test: {nombre_test}  [{grupo}]")
        print("-" * 70)

        try:
            metadata = leer_metadata(carpeta_test)

            tiempo_inicio = time.time()
            resultado     = resolver_modelo_3(carpeta_test, mostrar_output=False)
            tiempo_fin    = time.time()

            tiempo_seg = tiempo_fin - tiempo_inicio

            paso = comparar_resultado(nombre_test, metadata, resultado)

            print(f"Tiempo de ejecución: {tiempo_seg:.3f} s")

            registros.append({
                "test":    nombre_test,
                "grupo":   grupo,
                "tiempo":  tiempo_seg,
                "resultado": "OK" if paso else "ERROR",
            })

            if paso:
                tests_ok += 1
            else:
                tests_error += 1

        except Exception as error:
            tiempo_fin = time.time()
            tiempo_seg = tiempo_fin - tiempo_inicio

            print("Resultado: ERROR")
            print("Motivo: ocurrió un error al correr el test.")
            print(error)
            print(f"Tiempo de ejecución: {tiempo_seg:.3f} s")

            registros.append({
                "test":    nombre_test,
                "grupo":   grupo,
                "tiempo":  tiempo_seg,
                "resultado": "ERROR",
            })

            tests_error += 1

    tiempo_total = time.time() - tiempo_inicio_total

    # --------------------------------------------------
    # Resumen final
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Tests OK:        {tests_ok}")
    print(f"Tests con error: {tests_error}")
    print(f"Total tests:     {tests_ok + tests_error}")
    print(f"Tiempo total:    {tiempo_total:.3f} s")

    # --------------------------------------------------
    # Tabla de tiempos por test
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("TIEMPOS DE EJECUCIÓN POR TEST")
    print("=" * 70)
    print(f"{'Test':<45} {'Grupo':<10} {'Tiempo (s)':<12} {'Resultado'}")
    print("-" * 70)

    for r in registros:
        print(f"{r['test']:<45} {r['grupo']:<10} {r['tiempo']:<12.3f} {r['resultado']}")

    # --------------------------------------------------
    # Resumen por grupo
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("TIEMPOS PROMEDIO POR GRUPO")
    print("=" * 70)

    for grupo in ["pequeño", "mediano", "grande"]:
        tests_grupo = [r for r in registros if r["grupo"] == grupo]
        if not tests_grupo:
            continue
        tiempos     = [r["tiempo"] for r in tests_grupo]
        promedio    = sum(tiempos) / len(tiempos)
        minimo      = min(tiempos)
        maximo      = max(tiempos)
        print(f"{grupo.capitalize():<10}  n={len(tests_grupo)}  "
              f"promedio={promedio:.3f}s  min={minimo:.3f}s  max={maximo:.3f}s")

    if tests_error == 0:
        print()
        print("Todos los tests del Modelo 3 pasaron correctamente.")
    else:
        print()
        print("Hay tests con error. Revisa los mensajes anteriores.")


if __name__ == "__main__":
    correr_tests_modelo_3()
