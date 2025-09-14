
import numpy as np
import random
from tqdm import tqdm

def knots_to_nm_per_min(knots: float) -> float:
	return knots / 60.0

def eta_minutes(dist_nm: float, speed_knots: float) -> float:
	return dist_nm / knots_to_nm_per_min(speed_knots)

APPROACH_RANGES = [
	(100, float('inf'), 300, 500),
	(50, 100, 250, 300),
	(15, 50, 200, 250),
	(5, 15, 150, 200),
	(0, 5, 120, 150)
]
MIN_SEPARATION_MIN = 4
BUFFER_MIN = 5
REJOIN_GAP_MIN = 10

class Plane:
	def __init__(self, id, appear_time):
		self.id = id
		self.appear_time = appear_time
		self.dist = 100.0  # mn
		self.status = 'approaching'  # 'approaching', 'montevideo', 'landed'
		self.speed = self.get_max_speed()
		self.positions = [(appear_time, self.dist)]
		self.waiting = False
		self.wait_time = 0
		self.landed_time = None
		self.montevideo_time = None

	def get_range(self):
		for r_min, r_max, v_min, v_max in APPROACH_RANGES:
			if r_min < self.dist <= r_max:
				return v_min, v_max
		return 120, 150

	def get_max_speed(self):
		v_min, v_max = self.get_range()
		return v_max

	def get_min_speed(self):
		v_min, v_max = self.get_range()
		return v_min

	def update_position(self, dt, speed=None):
		if speed is None:
			speed = self.speed
		self.dist = max(0, self.dist - knots_to_nm_per_min(speed) * dt)
		self.positions.append((self.positions[-1][0] + dt, self.dist))
		if self.dist == 0 and self.status != 'landed':
			self.status = 'landed'
			self.landed_time = self.positions[-1][0]

def simulate_planes(lambda_prob=0.2, total_minutes=1080):
	planes = []
	queue = []
	rejoining = []
	next_id = 1
	random.seed(42)
	np.random.seed(42)
	
	# Usar tqdm para mostrar progreso de la simulación
	for t in tqdm(range(total_minutes), desc="⏱️  Simulando", unit="min", disable=(total_minutes < 100)):
		# Aparición de nuevos aviones
		if random.random() < lambda_prob:
			plane = Plane(next_id, t)
			# Chequeo de separación temporal con el anterior en la cola
			if queue:
				prev_plane = queue[-1]
				if (plane.appear_time - prev_plane.appear_time) < MIN_SEPARATION_MIN:
					plane.speed = max(plane.get_min_speed(), prev_plane.speed - 20)
			planes.append(plane)
			queue.append(plane)
			next_id += 1
		# Procesar aviones en estado 'approaching'
		for i, plane in enumerate(queue[:]):
			if plane.status == 'approaching':
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
		
		# Procesar aviones en rejoining (buscan gap o van a Montevideo)
		for plane in rejoining[:]:
			# Vuela hacia atrás a 200 nudos
			plane.dist += knots_to_nm_per_min(200)
			plane.positions.append((plane.positions[-1][0] + 1, plane.dist))
			
			# Si sale de las 100mn sin encontrar gap, se va a Montevideo
			if plane.dist > 100.0:
				plane.status = 'montevideo'
				plane.montevideo_time = t
				rejoining.remove(plane)
				continue
			
			# Buscar gap de 10 minutos en la cola
			gap_found = False
			for j in range(1, len(queue)):
				prev2 = queue[j-1]
				curr2 = queue[j]
				prev2_time = t + eta_minutes(prev2.dist, prev2.speed) if prev2.status != 'landed' else prev2.landed_time
				curr2_time = t + eta_minutes(curr2.dist, curr2.speed) if curr2.status != 'landed' else curr2.landed_time
				
				if (curr2_time - prev2_time) >= REJOIN_GAP_MIN:
					# Encontró gap, puede reingresar
					plane.status = 'approaching'
					plane.dist = plane.rejoin_dist
					plane.positions.append((plane.positions[-1][0], plane.dist))
					queue.insert(j, plane)
					rejoining.remove(plane)
					gap_found = True
					break
		to_remove_landed = []
		for plane in queue[:]:
			if plane.status == 'approaching':
				plane.update_position(1)
				if plane.status == 'landed':
					to_remove_landed.append(plane)
		for plane in to_remove_landed:
			if plane in queue:
				queue.remove(plane)
		# Actualizar posición de los aviones en estado 'approaching'
		for plane in queue[:]:
			if plane.status == 'approaching':
				plane.update_position(1)
				if plane.status == 'landed':
					queue.remove(plane)
	return planes, total_minutes

def print_summary(planes):
	"""
	Imprime un resumen estadístico de la simulación.
	
	Args:
		planes: Lista de objetos Plane de la simulación
	"""
	landed = [p for p in planes if p.status == 'landed']
	montevideo = [p for p in planes if p.status == 'montevideo']
	en_aproximacion = [p for p in planes if p.status == 'approaching' and p.dist > 0]
	
	print(f"Total de aviones simulados: {len(planes)}")
	print(f"Aterrizados: {len(landed)} ({len(landed)/len(planes)*100:.1f}%)")
	print(f"Se fueron a Montevideo: {len(montevideo)} ({len(montevideo)/len(planes)*100:.1f}%)")
	print(f"En aproximación al final (en vuelo): {len(en_aproximacion)}")
	
	if landed:
		tiempos = [p.landed_time - p.appear_time for p in landed]
		print(f"Tiempo promedio de aproximación y aterrizaje: {np.mean(tiempos):.2f} minutos")
		
		# Métricas de atraso
		def baseline_time_from_100nm():
			t = 50/(300/60) + 35/(250/60) + 10/(200/60) + 5/(150/60)
			return t
		
		delays = [(p.landed_time - p.appear_time) - baseline_time_from_100nm() for p in landed]
		print(f"Atraso promedio respecto al mínimo teórico: {np.mean(delays):.2f} minutos")
		print(f"Desvío estándar del atraso: {np.std(delays):.2f} minutos")

def minutos_a_hora(minuto):
	"""
	Convierte minutos de simulación a formato hora:minuto.
	
	Args:
		minuto: Minuto de la simulación (0 = 6:00am)
	
	Returns:
		str: Hora en formato "HH:MM"
	"""
	hora = 6 + minuto // 60
	minutos = minuto % 60
	return f"{hora:02d}:{minutos:02d}"

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
	
	# Ejecutar simulación
	planes, _ = simulate_planes(lambda_prob, total_minutes)
	
	# Mostrar resumen
	print_summary(planes)
	print()
	print("Para visualizaciones detalladas, ejecute:")
	print("  python visualizations.py")
