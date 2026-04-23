import gurobipy as gp
from gurobipy import GRB

# 1. Datos Sintéticos (Para probar la lógica)
cursos = ["Calculo", "Fisica", "Programacion"]
salas = ["Sala_A", "Sala_B", "Sala_C"]

alumnos = {"Calculo": 80, "Fisica": 30, "Programacion": 45}
capacidad = {"Sala_A": 50, "Sala_B": 100, "Sala_C": 60}

# 2. Crear el objeto Modelo
model = gp.Model("Asignacion_Salas_Basico")

# 3. Variables de Decisión
# x[i, j] = 1 si el curso i va a la sala j
x = model.addVars(cursos, salas, vtype=GRB.BINARY, name="asignacion")

# 4. Función Objetivo
# En el Modelo 1, a veces solo buscamos "factibilidad" (que quepan).
# Pero podemos poner que no haga nada (0) o minimizar el uso de salas.
model.setObjective(0, GRB.MINIMIZE)

# 5. Restricciones (Aquí está la magia)

# R1: Cada curso debe tener exactamente UNA sala
model.addConstrs((x.sum(i, "*") == 1 for i in cursos), name="R1_Asignacion")

# R2: Cada sala puede tener máximo UN curso
model.addConstrs((x.sum("*", j) <= 1 for j in salas), name="R2_Ocupacion")

# R3: Capacidad (El curso debe caber en la sala)
for i in cursos:
    for j in salas:
        # Si x[i,j] es 1, alumnos[i] debe ser <= capacidad[j]
        model.addConstr(alumnos[i] * x[i, j] <= capacidad[j], name=f"R3_Cap_{i}_{j}")

# 6. Resolver
model.optimize()

# 7. Mostrar resultados
if model.status == GRB.OPTIMAL:
    for v in model.getVars():
        if v.x > 0.5:  # Si la variable es 1
            print(f"Resultado: {v.varName} = {v.x}")
else:
    print("No se encontró solución factible.")
