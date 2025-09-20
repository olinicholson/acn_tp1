"""
Ejercicio 5 - Día Ventoso SIMPLIFICADO
Interrupciones de aterrizaje (1/10) + lógica de rejoin de main.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Plane, MIN_SEPARATION_MIN, REJOIN_GAP_MIN, BUFFER_MIN, knots_to_nm_per_min, eta_minutes, simulate_planes
import numpy as np
import random
import matplotlib.pyplot as plt

class PlaneVentoso(Plane):
    def __init__(self, id, appear_time):
        super().__init__(id, appear_time)
        self.interrupciones = 0
        self.en_interrupcion = False
        
    def intentar_aterrizaje(self):
        """10% probabilidad de interrupción"""
        if random.random() < 0.1:
            self.interrupciones += 1
            return False
        return True

def simulate_windy_day(lambda_prob=0.2, total_minutes=1080):
    """Simulación día ventoso usando lógica de main.py + interrupciones"""
    planes = []
    queue = []
    rejoining = []
    next_id = 1
    landed_count = 0
    montevideo_count = 0
    interrupciones_count = 0
    
    for t in range(total_minutes):
        # 1. Aparición
        if random.random() < lambda_prob:
            plane = PlaneVentoso(next_id, t)
            planes.append(plane)
            queue.append(plane)
            next_id += 1
        
        # 2. Procesar approaching (lógica exacta de main.py)
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
                            # Debe bajar por debajo del mínimo O no logra buffer, va a rejoin
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
                    # Primer avión, no tiene anterior
                    plane.speed = plane.get_max_speed()
        
        # Remover aviones marcados fuera del bucle principal
        for plane in to_remove:
            if plane in queue:
                queue.remove(plane)
        
        # 3. Procesar rejoining (lógica exacta de main.py)
        for plane in rejoining[:]:
            # Vuela hacia atrás a 200 nudos
            plane.dist += knots_to_nm_per_min(200)
            
            # Si sale de las 100mn sin encontrar gap, se va a Montevideo
            if plane.dist > 100.0:
                plane.status = 'montevideo'
                plane.montevideo_time = t
                rejoining.remove(plane)
                montevideo_count += 1
                continue
            
            # Buscar gap de 10 minutos en la cola
            for j in range(1, len(queue)):
                prev2 = queue[j-1]
                curr2 = queue[j]
                prev2_time = t + eta_minutes(prev2.dist, prev2.speed) if prev2.status != 'landed' else prev2.landed_time
                curr2_time = t + eta_minutes(curr2.dist, curr2.speed) if curr2.status != 'landed' else curr2.landed_time
                
                if (curr2_time - prev2_time) >= REJOIN_GAP_MIN:
                    # Encontró gap, puede reingresar
                    plane.status = 'approaching'
                    plane.dist = plane.rejoin_dist
                    queue.insert(j, plane)
                    rejoining.remove(plane)
                    break
        
        # 4. Actualizar posiciones y aterrizajes
        to_remove_landed = []
        for plane in queue[:]:
            if plane.status == 'approaching':
                plane.update_position(1)
                
                # Aterrizaje con interrupciones (SOLO para día ventoso)
                if plane.dist <= 0:
                    if plane.intentar_aterrizaje():
                        plane.status = 'landed'
                        plane.landed_time = t
                        to_remove_landed.append(plane)
                        landed_count += 1
                    else:
                        # Interrupción -> rejoin
                        plane.status = 'rejoin'
                        plane.rejoin_start_time = t
                        plane.rejoin_dist = 20.0
                        plane.dist = 20.0
                        plane.en_interrupcion = True
                        rejoining.append(plane)
                        to_remove_landed.append(plane)
                        interrupciones_count += 1
                
                elif plane.status == 'landed':
                    to_remove_landed.append(plane)
                    landed_count += 1
        
        for plane in to_remove_landed:
            if plane in queue:
                queue.remove(plane)
    
    return planes, landed_count, montevideo_count, interrupciones_count

def grafico_comparacion(lambdas_test=[0.1, 0.15, 0.2, 0.25, 0.3]):
    """Gráfico de líneas comparando normal vs ventoso"""
    print("📊 Generando gráfico...")
    
    normal_desvios = []
    ventoso_desvios = []
    
    for lam in lambdas_test:
        print(f"λ={lam}...")
        
        # Normal
        planes_normal, _ = simulate_planes(lam, 1080)
        normal_pct = len([p for p in planes_normal if p.status == 'montevideo']) / len(planes_normal) * 100
        normal_desvios.append(normal_pct)
        
        # Ventoso
        planes_ventoso, _, montevideo_count, _ = simulate_windy_day(lam, 1080)
        ventoso_pct = montevideo_count / len(planes_ventoso) * 100
        ventoso_desvios.append(ventoso_pct)
    
    # Gráfico de líneas simple
    plt.figure(figsize=(10, 6))
    plt.plot(lambdas_test, normal_desvios, 'bo-', linewidth=2, markersize=8, label='Normal')
    plt.plot(lambdas_test, ventoso_desvios, 'rs-', linewidth=2, markersize=8, label='Ventoso')
    plt.xlabel('Lambda (aviones/min)', fontsize=12)
    plt.ylabel('Desvíos (%)', fontsize=12)
    plt.title('Impacto del Día Ventoso', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    return normal_desvios, ventoso_desvios

def grafico_comparacion_montecarlo(lambdas_test=[0.1, 0.15, 0.2, 0.25, 0.3], N=100):
    """Gráfico de líneas comparando normal vs ventoso, con Monte Carlo y barras de error."""
    print("\nMonte Carlo Día Ventoso vs Normal")
    import matplotlib.pyplot as plt
    from tqdm import tqdm
    normal_desvios = []
    normal_err = []
    ventoso_desvios = []
    ventoso_err = []
    for lam in tqdm(lambdas_test, desc="Lambda Monte Carlo"):
        desvios_normal = []
        desvios_ventoso = []
        for _ in range(N):
            # Normal
            planes_normal, _ = simulate_planes(lam, 1080)
            if len(planes_normal) > 0:
                normal_pct = len([p for p in planes_normal if p.status == 'montevideo']) / len(planes_normal) * 100
                desvios_normal.append(normal_pct)
            # Ventoso
            planes_ventoso, _, montevideo_count, _ = simulate_windy_day(lam, 1080)
            if len(planes_ventoso) > 0:
                ventoso_pct = montevideo_count / len(planes_ventoso) * 100
                desvios_ventoso.append(ventoso_pct)
        # Promedio y error estándar
        normal_desvios.append(np.mean(desvios_normal))
        normal_err.append(np.std(desvios_normal) / np.sqrt(N))
        ventoso_desvios.append(np.mean(desvios_ventoso))
        ventoso_err.append(np.std(desvios_ventoso) / np.sqrt(N))
    # Gráfico de líneas con barras de error
    plt.figure(figsize=(10, 6))
    plt.errorbar(lambdas_test, normal_desvios, yerr=normal_err, fmt='bo-', linewidth=2, markersize=8, label='Normal', capsize=5)
    plt.errorbar(lambdas_test, ventoso_desvios, yerr=ventoso_err, fmt='rs-', linewidth=2, markersize=8, label='Ventoso', capsize=5)
    plt.xlabel('Lambda (aviones/min)', fontsize=12)
    plt.ylabel('Desvíos (%)', fontsize=12)
    plt.title('Impacto del Día Ventoso (Monte Carlo)', fontsize=14, fontweight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    # Mostrar errores de estimación
    print("\nResultados Monte Carlo:")
    for i, lam in enumerate(lambdas_test):
        print(f"λ={lam:.2f} | Normal: {normal_desvios[i]:.2f}% ± {normal_err[i]:.2f} | Ventoso: {ventoso_desvios[i]:.2f}% ± {ventoso_err[i]:.2f}")
    return normal_desvios, normal_err, ventoso_desvios, ventoso_err

# Para ejecutar desde main:
if __name__ == "__main__":
    print("🌪️ DÍA VENTOSO SIMPLIFICADO")
    print("="*30)
    
    # Comparación rápida
    for lam in [0.1, 0.2, 0.3]:
        _, _, mont_ventoso, _ = simulate_windy_day(lam, 1080)
        planes_normal, _ = simulate_planes(lam, 1080)
        mont_normal = len([p for p in planes_normal if p.status == 'montevideo'])
        print(f"λ={lam}: Normal {mont_normal}, Ventoso {mont_ventoso}")
    
    # Gráfico Monte Carlo
    grafico_comparacion_montecarlo()
