from pathlib import Path
import json

from modelo_2_gurobi import resolver_modelo_2


def leer_metadata(carpeta_test):
    """
    Lee el archivo metadata.json de un test.
    """

    ruta_metadata = carpeta_test / "metadata.json"

    with open(ruta_metadata, "r", encoding="utf-8") as archivo:
        metadata = json.load(archivo)

    return metadata


def comparar_resultado(nombre_test, metadata, resultado):
    """
    Compara el resultado obtenido con el resultado esperado.

    Retorna True si el test pasa.
    Retorna False si el test falla.
    """

    esperado_status = metadata["expected_status"]
    obtenido_status = resultado["status"]

    print(f"Status esperado:  {esperado_status}")
    print(f"Status obtenido:  {obtenido_status}")

    # Primero revisamos el status
    if obtenido_status != esperado_status:
        print("Resultado: ERROR")
        print("Motivo: el status no coincide.")
        return False

    # Si el test esperaba INFEASIBLE, no revisamos objetivo
    if esperado_status == "INFEASIBLE":
        print("Resultado: OK")
        return True

    # Si el test esperaba OPTIMAL, revisamos el objetivo
    esperado_obj = metadata["expected_obj"]
    obtenido_obj = resultado["objetivo"]

    print(f"Objetivo esperado: {esperado_obj}")
    print(f"Objetivo obtenido: {obtenido_obj}")

    # Usamos tolerancia porque Gurobi a veces entrega números como 59.999999999
    tolerancia = 1e-6

    if abs(obtenido_obj - esperado_obj) > tolerancia:
        print("Resultado: ERROR")
        print("Motivo: el valor objetivo no coincide.")
        return False

    print("Resultado: OK")
    return True


def correr_tests_modelo_2():
    """
    Corre todos los tests guardados en data/modelo2.
    """

    carpeta_base = Path("data/modelo2")

    if not carpeta_base.exists():
        print("ERROR: no existe la carpeta data/modelo2")
        print("Primero ejecuta:")
        print("python src/generar_data_modelo2.py")
        return

    carpetas_tests = []

    for carpeta in carpeta_base.iterdir():
        if carpeta.is_dir():
            carpetas_tests.append(carpeta)

    carpetas_tests = sorted(carpetas_tests)

    if len(carpetas_tests) == 0:
        print("ERROR: no se encontraron carpetas de tests.")
        return

    print("=" * 70)
    print("CORRIENDO TESTS DEL MODELO 2")
    print("=" * 70)

    tests_ok = 0
    tests_error = 0

    for carpeta_test in carpetas_tests:

        nombre_test = carpeta_test.name

        print()
        print("-" * 70)
        print(f"Test: {nombre_test}")
        print("-" * 70)

        try:
            metadata = leer_metadata(carpeta_test)

            resultado = resolver_modelo_2(
                carpeta_test,
                mostrar_output=False
            )

            paso = comparar_resultado(
                nombre_test,
                metadata,
                resultado
            )

            if paso:
                tests_ok += 1
            else:
                tests_error += 1

        except Exception as error:
            print("Resultado: ERROR")
            print("Motivo: ocurrió un error al correr el test.")
            print(error)
            tests_error += 1

    print()
    print("=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    print(f"Tests OK:      {tests_ok}")
    print(f"Tests con error: {tests_error}")
    print(f"Total tests:   {tests_ok + tests_error}")

    if tests_error == 0:
        print()
        print("Todos los tests del Modelo 2 pasaron correctamente.")
    else:
        print()
        print("Hay tests con error. Revisa los mensajes anteriores.")


if __name__ == "__main__":
    correr_tests_modelo_2()