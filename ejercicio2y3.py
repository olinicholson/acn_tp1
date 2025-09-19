import random

from main import Plane, simulate_planes, print_summary, minutos_a_hora
def cinco_aviones_1hora(lambda_prob, total_minutes):
    # Lista para almacenar los tiempos de aparición de los aviones
    planes = []
    random.seed(42)  # Fijar semilla para reproducibilidad

    # Simular minuto a minuto
    for t in range(total_minutes):
        if random.random() < lambda_prob:
            planes.append(t)

    # Dividir en intervalos de 60 minutos y contar aviones
    interval_minutes = 60
    total_intervals = total_minutes // interval_minutes
    count_target = 0
    for i in range(total_intervals):
        start = i * interval_minutes
        end = start + interval_minutes
        planes_in_interval = [p for p in planes if start <= p < end]
        if len(planes_in_interval) == 5:  # Contar intervalos con exactamente 5 aviones
            count_target += 1

    # Calcular probabilidad
    probability = count_target / total_intervals
    return probability


# Simulación Monte Carlo básica - solo estadísticas
print("Simulación Monte Carlo de aproximación de aeronaves")

# Calcular lambda para un arribo por hora 
lambda_prob = 1 / 60
# Duración de la simulación en minutos
total_minutes = 1080

print(f"Parámetros de simulación:")
print(f"  Lambda de aparición: {lambda_prob:.4f} aviones/minuto")
print(f"  Duración: {total_minutes} minutos ({total_minutes/60:.1f} horas)")
print(f"  Horario: 6:00am a {minutos_a_hora(total_minutes)}")
print()

# Ejecutar simulación
planes, _ = simulate_planes(lambda_prob, total_minutes)

# Mostrar resumen
print_summary(planes)
print()
     
# Simulación Monte Carlo básica - solo estadísticas
print("Simulación Monte Carlo de aproximación de aeronaves")

# Calcular lambda para un arribo por hora 
lambda_prob = 1 / 60
# Duración de la simulación en minutos
total_minutes = 100000 * 60  # Simular 100,000 horas para este ejercicio

print(f"Parámetros de simulación:")
print(f"  Lambda de aparición: {lambda_prob:.4f} aviones/minuto")
print(f"  Duración: {total_minutes} minutos ({total_minutes/60:.1f} horas)")
print()

# Ejecutar simulación para el ejercicio 3
prob_5_planes = cinco_aviones_1hora(lambda_prob, total_minutes)
print(f"Probabilidad estimada de que lleguen 5 aviones en una hora: {prob_5_planes:.6f}")
