"""
Ejercicio 6 - Cierre Sorpresivo por Tormenta
Simulación del cierre del aeropuerto AEP por 30 minutos sin previo aviso
"""

from main import Plane, MIN_SEPARATION_MIN, REJOIN_GAP_MIN, BUFFER_MIN, knots_to_nm_per_min, eta_minutes, simulate_planes
import numpy as np
import random
import matplotlib.pyplot as plt
from tqdm import tqdm

class PlaneTormenta(Plane):
    def __init__(self, id, appear_time):
        super().__init__(id, appear_time)
        self.tiempo_espera_cierre = 0
        self.afectado_por_tormenta = False
        
def simulate_storm_closure(lambda_prob=0.2, total_minutes=1080, storm_start=540, storm_duration=30):
    """
    Simulación con cierre sorpresivo del aeropuerto
    
    Args:
        lambda_prob: Probabilidad de aparición de aviones por minuto
        total_minutes: Duración total de la simulación (18 horas = 1080 min)
        storm_start: Minuto en que empieza la tormenta (540 = 15:00, 9h después de las 6:00)
        storm_duration: Duración del cierre en minutos (30 min)
    """
    planes = []
    queue = []
    rejoining = []
    next_id = 1
    landed_count = 0
    montevideo_count = 0
    storm_end = storm_start + storm_duration
    
    # Estadísticas específicas de la tormenta
    planes_afectados = 0
    tiempo_espera_total = 0
    max_cola_durante_cierre = 0
    
    print(f"🌩️ Simulando tormenta: cierre de {storm_start//60 + 6}:{storm_start%60:02d} a {storm_end//60 + 6}:{storm_end%60:02d}")
    
    for t in tqdm(range(total_minutes), desc="⏱️  Simulando"):
        # 1. Aparición de aviones (continúa durante la tormenta)
        if random.random() < lambda_prob:
            plane = PlaneTormenta(next_id, t)
            planes.append(plane)
            queue.append(plane)
            next_id += 1
        
        # 2. ¿Está el aeropuerto cerrado por tormenta?
        aeropuerto_cerrado = storm_start <= t < storm_end
        
        if aeropuerto_cerrado:
            # Durante el cierre: los aviones solo pueden esperar o desviarse
            max_cola_durante_cierre = max(max_cola_durante_cierre, len(queue))
            
            # Procesar cola: aviones esperan hasta que se queden sin combustible
            to_remove = []
            for plane in queue[:]:
                if plane.status == 'approaching':
                    plane.tiempo_espera_cierre += 1
                    plane.afectado_por_tormenta = True
                    planes_afectados += 1
                    tiempo_espera_total += 1
                    
                    # Si un avión espera más de 60 minutos, se desvía (combustible)
                    if plane.tiempo_espera_cierre > 60:
                        plane.status = 'montevideo'
                        plane.montevideo_time = t
                        to_remove.append(plane)
                        montevideo_count += 1
                    # Si está muy cerca (< 10nm) y lleva esperando mucho, también se desvía
                    elif plane.dist < 10 and plane.tiempo_espera_cierre > 30:
                        plane.status = 'montevideo'
                        plane.montevideo_time = t
                        to_remove.append(plane)
                        montevideo_count += 1
            
            for plane in to_remove:
                if plane in queue:
                    queue.remove(plane)
        
        else:
            # Aeropuerto abierto: lógica normal con rejoin
            to_remove = []
            for i, plane in enumerate(queue[:]):
                if plane.status == 'approaching':
                    if i > 0:
                        prev = queue[i-1]
                        prev_time_to_land = t + eta_minutes(prev.dist, prev.speed) if prev.status != 'landed' else prev.landed_time
                        curr_time_to_land = t + eta_minutes(plane.dist, plane.speed)
                        nueva_speed = max(plane.get_min_speed(), prev.speed - 20)
                        curr_time_to_land_nueva = t + eta_minutes(plane.dist, nueva_speed)
                        
                        if (curr_time_to_land - prev_time_to_land) < MIN_SEPARATION_MIN:
                            required_speed = prev.speed - 20
                            if required_speed < plane.get_min_speed() or (curr_time_to_land_nueva - prev_time_to_land) < BUFFER_MIN:
                                plane.status = 'rejoin'
                                plane.rejoin_start_time = t
                                plane.rejoin_dist = plane.dist
                                rejoining.append(plane)
                                to_remove.append(plane)
                                continue
                            else:
                                plane.speed = nueva_speed
                        else:
                            plane.speed = plane.get_max_speed()
                    else:
                        plane.speed = plane.get_max_speed()
            
            for plane in to_remove:
                if plane in queue:
                    queue.remove(plane)
            
            # Procesar rejoining
            for plane in rejoining[:]:
                plane.dist += knots_to_nm_per_min(200)
                
                if plane.dist > 100.0:
                    plane.status = 'montevideo'
                    plane.montevideo_time = t
                    rejoining.remove(plane)
                    montevideo_count += 1
                    continue
                
                for j in range(1, len(queue)):
                    prev2 = queue[j-1]
                    curr2 = queue[j]
                    prev2_time = t + eta_minutes(prev2.dist, prev2.speed) if prev2.status != 'landed' else prev2.landed_time
                    curr2_time = t + eta_minutes(curr2.dist, curr2.speed) if curr2.status != 'landed' else curr2.landed_time
                    
                    if (curr2_time - prev2_time) >= REJOIN_GAP_MIN:
                        plane.status = 'approaching'
                        plane.dist = plane.rejoin_dist
                        queue.insert(j, plane)
                        rejoining.remove(plane)
                        break
            
            # Actualizar posiciones y aterrizajes (solo si aeropuerto abierto)
            to_remove_landed = []
            for plane in queue[:]:
                if plane.status == 'approaching':
                    plane.update_position(1)
                    
                    if plane.dist <= 0:
                        plane.status = 'landed'
                        plane.landed_time = t
                        to_remove_landed.append(plane)
                        landed_count += 1
                    elif plane.status == 'landed':
                        to_remove_landed.append(plane)
                        landed_count += 1
            
            for plane in to_remove_landed:
                if plane in queue:
                    queue.remove(plane)
    
    return (planes, landed_count, montevideo_count, planes_afectados, 
            tiempo_espera_total, max_cola_durante_cierre)

def analizar_impacto_tormenta(lambdas_test=[0.1, 0.15, 0.2, 0.25, 0.3]):
    """Analiza el impacto de la tormenta vs día normal"""
    print("🌩️ ANÁLISIS DE IMPACTO DE TORMENTA")
    print("="*50)
    
    resultados_normales = []
    resultados_tormenta = []
    
    for lam in lambdas_test:
        print(f"\n📊 Analizando λ={lam} aviones/min...")
        
        # Simulación normal
        planes_normal, _ = simulate_planes(lam, 1080)
        normal_montevideo = len([p for p in planes_normal if p.status == 'montevideo'])
        normal_total = len(planes_normal)
        normal_pct = (normal_montevideo / normal_total * 100) if normal_total > 0 else 0
        
        # Simulación con tormenta
        (planes_tormenta, landed_tormenta, montevideo_tormenta, 
         afectados, tiempo_espera, max_cola) = simulate_storm_closure(lam, 1080)
        
        tormenta_total = len(planes_tormenta)
        tormenta_pct = (montevideo_tormenta / tormenta_total * 100) if tormenta_total > 0 else 0
        
        resultados_normales.append(normal_pct)
        resultados_tormenta.append(tormenta_pct)
        
        print(f"  Normal:   {normal_montevideo:3d}/{normal_total:3d} = {normal_pct:5.1f}% desvíos")
        print(f"  Tormenta: {montevideo_tormenta:3d}/{tormenta_total:3d} = {tormenta_pct:5.1f}% desvíos")
        print(f"  Impacto:  +{tormenta_pct - normal_pct:5.1f}% puntos porcentuales")
        print(f"  Afectados por cierre: {afectados} aviones")
        print(f"  Tiempo espera total: {tiempo_espera} minutos-avión")
        print(f"  Cola máxima durante cierre: {max_cola} aviones")
    
    return resultados_normales, resultados_tormenta

def grafico_comparacion_tormenta(lambdas_test=[0.1, 0.15, 0.2, 0.25, 0.3]):
    """Gráfico comparando normal vs tormenta"""
    print("\n📈 Generando gráfico de comparación...")
    
    normales, tormenta = analizar_impacto_tormenta(lambdas_test)
    
    plt.figure(figsize=(12, 8))
    
    # Gráfico principal
    plt.subplot(2, 1, 1)
    plt.plot(lambdas_test, normales, 'bo-', linewidth=2, markersize=8, label='Día Normal')
    plt.plot(lambdas_test, tormenta, 'rs-', linewidth=2, markersize=8, label='Con Tormenta (30min)')
    plt.xlabel('Lambda (aviones/min)', fontsize=12)
    plt.ylabel('Desvíos a Montevideo (%)', fontsize=12)
    plt.title('Impacto del Cierre por Tormenta en AEP', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Gráfico de diferencia
    plt.subplot(2, 1, 2)
    diferencias = [t - n for n, t in zip(normales, tormenta)]
    plt.bar(lambdas_test, diferencias, color='red', alpha=0.7, width=0.03)
    plt.xlabel('Lambda (aviones/min)', fontsize=12)
    plt.ylabel('Incremento en Desvíos (% puntos)', fontsize=12)
    plt.title('Incremento de Desvíos por Tormenta', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Anotar valores
    for i, (lam, diff) in enumerate(zip(lambdas_test, diferencias)):
        plt.annotate(f'+{diff:.1f}%', (lam, diff), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.show()
    
    return normales, tormenta

def simular_diferentes_momentos_tormenta():
    """Analiza el impacto según el momento del día en que ocurre la tormenta"""
    print("\n🕐 ANÁLISIS POR MOMENTO DEL DÍA")
    print("="*40)
    
    lambda_fijo = 0.2  # Tráfico medio
    
    # Diferentes momentos del día (en minutos desde las 6:00)
    momentos = {
        "Mañana (8:00)": 2 * 60,      # 120 min = 8:00
        "Mediodía (12:00)": 6 * 60,   # 360 min = 12:00  
        "Tarde (15:00)": 9 * 60,      # 540 min = 15:00
        "Noche (18:00)": 12 * 60,     # 720 min = 18:00
        "Madrugada (21:00)": 15 * 60  # 900 min = 21:00
    }
    
    resultados = {}
    
    for momento, inicio in momentos.items():
        print(f"\n⏰ Tormenta en {momento}:")
        
        (planes, landed, montevideo, afectados, 
         tiempo_espera, max_cola) = simulate_storm_closure(lambda_fijo, 1080, inicio, 30)
        
        total = len(planes)
        pct_montevideo = (montevideo / total * 100) if total > 0 else 0
        
        resultados[momento] = {
            'montevideo_pct': pct_montevideo,
            'afectados': afectados,
            'tiempo_espera': tiempo_espera,
            'max_cola': max_cola
        }
        
        print(f"  Desvíos: {montevideo}/{total} = {pct_montevideo:.1f}%")
        print(f"  Afectados: {afectados} aviones")
        print(f"  Tiempo espera total: {tiempo_espera} min-avión")
        print(f"  Cola máxima: {max_cola} aviones")
    
    return resultados

if __name__ == "__main__":
    print("🌩️ SIMULACIÓN DE CIERRE POR TORMENTA")
    print("="*50)
    print("Escenario: Cierre sorpresivo de AEP por 30 minutos")
    print("- Los pilotos NO tienen aviso previo")
    print("- Los aviones en vuelo deben esperar o desviarse")
    print("- Cierre típico: 15:00-15:30 (hora pico)")
    print()
    
    # Análisis principal
    normales, tormenta = grafico_comparacion_tormenta()
    
    # Análisis por momento del día
    resultados_momento = simular_diferentes_momentos_tormenta()
    
