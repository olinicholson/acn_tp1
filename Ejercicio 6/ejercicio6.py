from main import Plane, MIN_SEPARATION_MIN, REJOIN_GAP_MIN, BUFFER_MIN, knots_to_nm_per_min, eta_minutes, simulate_planes
import random

class PlaneTormenta(Plane):
    def __init__(self, id, appear_time):
        super().__init__(id, appear_time)
        self.tiempo_espera_cierre = 0
        self.afectado_por_tormenta = False

def simulate_storm_closure(lambda_prob=0.2, total_minutes=1080, storm_start=None, storm_duration=30):
    """
    Simula un día con cierre sorpresivo del aeropuerto por tormenta.
    Si storm_start no se pasa, se elige un inicio aleatorio.
    """
    # Si no se especifica, elegir inicio random para la tormenta
    if storm_start is None:
        storm_start = random.randint(0, total_minutes - storm_duration)

    storm_end = storm_start + storm_duration

    planes = []
    queue = []
    rejoining = []
    next_id = 1
    landed_count = 0
    montevideo_count = 0

    planes_afectados = 0
    tiempo_espera_total = 0
    max_cola_durante_cierre = 0

    for t in range(total_minutes):
        # Aparición de aviones
        if random.random() < lambda_prob:
            plane = PlaneTormenta(next_id, t)
            planes.append(plane)
            queue.append(plane)
            next_id += 1

        aeropuerto_cerrado = storm_start <= t < storm_end

        if aeropuerto_cerrado:
            max_cola_durante_cierre = max(max_cola_durante_cierre, len(queue))
            to_remove = []
            for plane in queue[:]:
                if plane.status == 'approaching':
                    plane.update_position(1)
                    if plane.dist <= 10:
                        if aeropuerto_cerrado:
                            plane.status = 'montevideo'
                            plane.montevideo_time = t
                            to_remove.append(plane)
                            montevideo_count += 1
                            planes_afectados += 1
                        else:
                            plane.dist = 0
                            plane.status = 'landed'
                            plane.landed_time = t
                            landed_count += 1
                            to_remove.append(plane)
            for plane in to_remove:
                if plane in queue:
                    queue.remove(plane)
        else:
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
        tiempo_espera_total, max_cola_durante_cierre, storm_start, storm_end)
