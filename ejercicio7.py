import numpy as np
import sys
import os
import random
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import APPROACH_RANGES, eta_minutes, knots_to_nm_per_min, print_summary, minutos_a_hora

# Parámetros de combustible para Boeing 737 (aprox)
FUEL_CAPACITY_KG = 20_800  # kg (unos 25,000 litros)
FUEL_BURN_KG_PER_HOUR = 2_700  # kg/hora en crucero
FUEL_BURN_KG_PER_MIN = FUEL_BURN_KG_PER_HOUR / 60
# Distancia a Montevideo desde el holding (aprox)
DIST_TO_MVD = 120  # mn
SPEED_TO_MVD = 450  # nudos (crucero)

class PlaneWithFuel:
    def __init__(self, id, appear_time):
        self.id = id
        self.appear_time = appear_time
        self.dist = 100.0
        v_min, v_max = 300, 500  # rango inicial
        self.status = 'approaching'
        self.speed = random.uniform(v_min, v_max)
        self.positions = [(appear_time, self.dist)]
        self.waiting = False
        self.wait_time = 0
        self.landed_time = None
        self.montevideo_time = None
        # Inicializar combustible entre 50% y 90% de la capacidad
        self.fuel = random.uniform(0.5, 0.9) * FUEL_CAPACITY_KG
        self.in_holding = False

    def get_range(self):
        for r_min, r_max, v_min, v_max in APPROACH_RANGES:
            if r_min < self.dist <= r_max:
                return v_min, v_max
        return None, None

    def update_position(self, dt, speed=None):
        if speed is None:
            speed = self.speed
        # Consumo de combustible
        self.fuel -= FUEL_BURN_KG_PER_MIN * dt
        self.dist = max(0, self.dist - knots_to_nm_per_min(speed) * dt)
        self.positions.append((self.positions[-1][0] + dt, self.dist))
        if self.dist == 0 and self.status != 'landed':
            self.status = 'landed'
            self.landed_time = self.positions[-1][0]

    def can_reach_montevideo(self):
        # ¿Alcanza el combustible para ir a Montevideo?
        time_to_mvd = DIST_TO_MVD / knots_to_nm_per_min(SPEED_TO_MVD)
        fuel_needed = time_to_mvd * FUEL_BURN_KG_PER_MIN
        return self.fuel >= fuel_needed
    
def simulate_planes_holding(lambda_prob=0.2, total_minutes=1080):
    HOLD_INNER_NM = 10
    HOLD_OUTER_NM = 15
    HOLD_SPEED = 230  # velocidad típica en holding bajo FL140

    planes = []
    queue = []
    holding = []
    next_id = 1

    
    for t in range(total_minutes):
        # Aparición de nuevos aviones
        if random.random() < lambda_prob:
            plane = PlaneWithFuel(next_id, t)
            planes.append(plane)
            queue.append(plane)
            next_id += 1

        # Procesar aviones en estado 'approaching'
        to_remove = []
        for i, plane in enumerate(queue[:] ):
            if plane.status == 'approaching':
                if i > 0:
                    prev = queue[i-1]
                    prev_time_to_land = t + eta_minutes(prev.dist, prev.speed) if prev.status != 'landed' else prev.landed_time
                    curr_time_to_land = t + eta_minutes(plane.dist, plane.speed)

                    nueva_speed = max(plane.get_range()[0], prev.speed - 20)
                    curr_time_to_land_nueva = t + eta_minutes(plane.dist, nueva_speed)

                    if (curr_time_to_land - prev_time_to_land) < 4:
                        required_speed = prev.speed - 20
                        if required_speed < plane.get_range()[0] or (curr_time_to_land_nueva - prev_time_to_land) < 5:
                            plane.status = 'holding'
                            plane.holding_start_time = t
                            holding.append(plane)
                            to_remove.append(plane)
                            continue
                        else:
                            plane.speed = nueva_speed
                    else:
                        plane.speed = plane.get_range()[1]
                else:
                    plane.speed = plane.get_range()[1]
        for plane in to_remove:
            if plane in queue:
                queue.remove(plane)

        # Procesar aviones en holding
        for plane in holding[:]:
            # Mantenerse en patrón de espera entre 10 y 15 NM
            if plane.dist > HOLD_OUTER_NM:
                plane.dist = HOLD_OUTER_NM
            elif plane.dist < HOLD_INNER_NM:
                    plane.dist = HOLD_INNER_NM
            else:
                # Oscila entre inner y outer como si fueran las piernas del racetrack
                sentido = random.choice([-1, 1])
                nueva_dist = plane.dist + sentido * (HOLD_OUTER_NM - HOLD_INNER_NM)
                plane.dist = nueva_dist

            plane.speed = HOLD_SPEED
            plane.update_position(1, plane.speed)

            # Si no puede llegar a Montevideo, se desvía
            if not plane.can_reach_montevideo():
                plane.status = 'montevideo'
                plane.montevideo_time = t
                holding.remove(plane)
                continue

            # Buscar gap en la cola
            gap_found = False
            for j in range(1, len(queue)):
                prev2 = queue[j-1]
                curr2 = queue[j]
                prev2_time = t + eta_minutes(prev2.dist, prev2.speed) if prev2.status != 'landed' else prev2.landed_time
                curr2_time = t + eta_minutes(curr2.dist, curr2.speed) if curr2.status != 'landed' else curr2.landed_time
                if (curr2_time - prev2_time) >= 10:
                    plane.status = 'approaching'
                    plane.dist = HOLD_INNER_NM
                    plane.positions.append((plane.positions[-1][0], plane.dist))
                    queue.insert(j, plane)
                    holding.remove(plane)
                    gap_found = True
                    break

        # Actualizar posición de los aviones en estado 'approaching'
        to_remove_landed = []
        for plane in queue[:]:
            if plane.status == 'approaching':
                plane.update_position(1)
                if plane.status == 'landed':
                    to_remove_landed.append(plane)
        for plane in to_remove_landed:
            if plane in queue:
                queue.remove(plane)

    # Resumen estadístico
    landed = [p for p in planes if p.status == 'landed']
    montevideo = [p for p in planes if p.status == 'montevideo']
    total = len(landed) + len(montevideo)

    return planes, total_minutes

simulate_planes_holding.use_tqdm = True
if __name__ == "__main__":
    print("Simulación con política de holding y combustible (Ejercicio 7)")
    lambda_prob = 0.2
    total_minutes = 1080
    N = 1000  # cantidad de simulaciones Monte Carlo
    desvios = []
    aterrizajes = []
    totales = []

    for i in tqdm(range(N), desc="Monte Carlo", unit="sim"):
        planes, _ = simulate_planes_holding(lambda_prob, total_minutes)
        landed = [p for p in planes if p.status == 'landed']
        montevideo = [p for p in planes if p.status == 'montevideo']
        total = len(landed) + len(montevideo)
        if total > 0:
            desvios.append(len(montevideo) / total)
            aterrizajes.append(len(landed) / total)
            totales.append(total)
    # Restaurar tqdm si se desea para simulaciones interactivas
    print(f"\nMonte Carlo ({N} caminos, lambda={lambda_prob}):")
    print(f"Promedio porcentaje desvíos: {100 * np.mean(desvios):.1f}%")
    print(f"Promedio porcentaje aterrizajes: {100 * np.mean(aterrizajes):.1f}%")
    print(f"Promedio total de aviones: {np.mean(totales):.1f}")
    # Calcular error estándar del porcentaje de desvíos
    desvios_arr = np.array(desvios)
    error_std = np.std(desvios_arr) / np.sqrt(N)
    print(f"Error estándar del porcentaje de desvíos: {100 * error_std:.2f}%")