import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import simulate_planes, print_summary, minutos_a_hora
from tqdm import tqdm as tqdm_ext

if __name__ == "__main__":
    # Simulación Monte Carlo básica - solo estadísticas
    print("Simulación Monte Carlo de aproximación de aeronaves")
    print("=" * 60)
    
    lambda_prob = 0.15
    total_minutes = 1080
    
    print(f"Parámetros de simulación:")
    print(f"  Lambda de aparición: {lambda_prob} aviones/minuto")
    print(f"  Duración: {total_minutes} minutos ({total_minutes/60:.1f} horas)")
    print(f"  Horario: 6:00am a {minutos_a_hora(total_minutes)}")
    print()
    
    # Ejecutar simulación única
    planes, _ = simulate_planes(lambda_prob, total_minutes)
    print_summary(planes)
    print()
    print("Para visualizaciones detalladas, ejecute:")
    print("  python visualizations.py")

    # --- Monte Carlo: múltiples caminos y promedios ---
    N = 1000  # cantidad de simulaciones
    lambda_prob_mc = 0.2
    desvios = []
    aterrizajes = []
    totales = []  # Lista para almacenar el total de aviones por simulación
    aterrizajes_totales = []  # Lista para almacenar el total de aviones aterrizados por simulación
    simulate_planes.use_tqdm = False
    for i in tqdm_ext(range(N), desc="Monte Carlo", unit="sim"):
        planes_mc, _ = simulate_planes(lambda_prob=lambda_prob_mc, total_minutes=total_minutes)
        landed = len([p for p in planes_mc if p.status == 'landed'])
        montevideo = len([p for p in planes_mc if p.status == 'montevideo'])
        total = landed + montevideo
        if total > 0:
            desvios.append(montevideo / total)
            aterrizajes.append(landed / total)
            totales.append(total)  # Agregar el total de aviones de esta simulación
            aterrizajes_totales.append(landed)  # Agregar el total de aviones aterrizados de esta simulación
    simulate_planes.use_tqdm = True
    print(f"\nMonte Carlo ({N} caminos, lambda={lambda_prob_mc}):")
    print(f"Promedio porcentaje desvíos: {100 * sum(desvios)/len(desvios):.1f}%")
    print(f"Promedio porcentaje aterrizajes: {100 * sum(aterrizajes)/len(aterrizajes):.1f}%")
    print(f"Promedio total de aviones: {sum(totales)/len(totales):.1f}")  # Mostrar el promedio total de aviones
    print(f"Promedio total de aviones aterrizados: {sum(aterrizajes_totales)/len(aterrizajes_totales):.1f}")  # Mostrar el promedio total de aviones aterrizados
    
    # Calcular error estándar del porcentaje de desvíos
    desvios_arr = np.array(desvios)
    error_std = np.std(desvios_arr) / np.sqrt(N)
    print(f"Error estándar del porcentaje de desvíos: {100 * error_std:.2f}%")