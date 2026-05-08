# Laboratorio de Modelación II

Repositorio del proyecto desarrollado para el ramo **Laboratorio de Modelación II**.  
El objetivo general del proyecto es modelar e implementar un problema de optimización para la asignación de salas, considerando la movilidad de estudiantes entre bloques consecutivos de clases.

## Descripción general

El proyecto busca construir progresivamente distintos modelos de asignación de salas.  
Cada versión incorpora nuevas restricciones o elementos de realismo, partiendo desde una formulación simple hasta modelos más complejos.

La implementación se trabaja con **Python** y **Gurobi**, utilizando datos sintéticos para validar el correcto funcionamiento de cada modelo.

## Estructura del repositorio

```text
Laboratorio-modelacion-II/
│
├── modelo_prueba/
│   └── Primeras pruebas con Gurobi para entender su funcionamiento.
│
├── Modelo1/
│   └── Código correspondiente a la primera versión del modelo.
│       Incluye tres instancias sintéticas usadas para comprobar el funcionamiento del optimizador.
│
├── notebooks/
│   └── Notebooks exploratorios de cada modelo.
│       Se utilizan para documentar pruebas, revisar resultados y analizar la implementación.
│
├── data/
│   └── Datos sintéticos generados para probar los modelos.
│
└── src/
    └── Códigos auxiliares utilizados por los notebooks,
        como generación de datos, validación de instancias y resolución de modelos.
```

## Modelos desarrollados

### Modelo 1

Versión inicial del problema. Considera cursos y salas homogéneas, con costos binarios de movimiento entre salas.

### Modelo 2

Extiende el Modelo 1 incorporando tamaños de cursos variables y capacidades heterogéneas de salas.
