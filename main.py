# Simulación de llegada y aproximación de aviones a AEP, y otras funciones relevantes para esta simulacion.
import numpy as np
import random
from tqdm import tqdm

# funcion que convierte una velocidad en nudos a una  velocidad en millas náuticas por minuto. 
def knots_to_nm_per_min(knots: float) -> float:
	return knots / 60.0

# funcion que calcula el tiempo estimado de llegada en minutos, dado una distancia en millas náuticas y una velocidad en nudos.
def eta_minutes(dist_nm: float, speed_knots: float) -> float:
	return dist_nm / knots_to_nm_per_min(speed_knots)

# funcion que convierte minutos de simulacion a formato hora:minuto
def minutos_a_hora(minuto):
	"""
	Convierte minutos de simulación a formato hora:minuto.
	"""
	hora = 6 + minuto // 60
	minutos = minuto % 60
	return f"{hora:02d}:{minutos:02d}"

# rangos de la velocidad maxima permitida de acuerdo a la distancia a AEP
APPROACH_RANGES = [
	(100, float('inf'), 300, 500),
	(50, 100, 250, 300),
	(15, 50, 200, 250),
	(5, 15, 150, 200),
	(0, 5, 120, 150)
]
MIN_SEPARATION_MIN = 4 # tiempo minimo de separacion
BUFFER_MIN = 5 # buffer minimo de seguridad 
REJOIN_GAP_MIN = 10 # tiempo minimo de gap para reingresar

# clase Plane que representa un avion en la simulacion con : 
# - id: identificador unico del avion
# - appear_time: minuto de aparicion del avion en la simulacion
# - dist: distancia del avion a AEP en mn
# - status: estado del avion ('approaching', 'montevideo', 'landed', 'rejoin'), approaching por default
# - speed: velocidad actual del avion en nudos, maxima permtitida por default 
# - positions: lista de tuplas (tiempo, distancia) que registra la posicion del avion a lo largo del tiempo
# - waiting: booleano que indica si el avion esta esperando para reingresar
# - wait_time: tiempo total que el avion ha estado esperando para reingresar
# - landed_time: minuto en que el avion aterrizo (si es que aterrizo)
# - montevideo_time: minuto en que el avion se fue a Montevideo (si se tuvo que ir a Montevideo)
class Plane:
	def __init__(self, id, appear_time):
		self.id = id
		self.appear_time = appear_time
		# Distancia inicial fija a 100 mn
		self.dist = 100.0
		# Buscar el rango de velocidad permitido según la distancia (100 mn)
		v_min, v_max = None, None
		for r_min, r_max, vmin, vmax in APPROACH_RANGES:
			if r_min < self.dist <= r_max:
				v_min, v_max = vmin, vmax
				break
		if v_min is None or v_max is None:
			raise ValueError(f"No se encontró rango de velocidad para distancia {self.dist}")
		self.status = 'approaching'  # 'approaching', 'montevideo', 'landed'
		self.speed = random.uniform(v_min, v_max)
		self.positions = [(appear_time, self.dist)]
		self.waiting = False
		self.wait_time = 0
		self.landed_time = None
		self.montevideo_time = None

	# determina el rango de velocidad segun la distancia actual del avion a AEP
	def get_range(self):
		for r_min, r_max, v_min, v_max in APPROACH_RANGES:
			if r_min < self.dist <= r_max:
				return v_min, v_max
		return None, None

	# velocidad maxima del avion
	def get_max_speed(self):
		v_min, v_max = self.get_range()
		return v_max
	
	# velocidad minima del avion
	def get_min_speed(self):
		v_min, v_max = self.get_range()
		return v_min

	# actualiza la posicion del avion segun el tiempo transcurrido dt y la velocidad (si no se pasa, usa la velocidad actual)
	def update_position(self, dt, speed=None):
		if speed is None:
			speed = self.speed
		self.dist = max(0, self.dist - knots_to_nm_per_min(speed) * dt)
		self.positions.append((self.positions[-1][0] + dt, self.dist))
		if self.dist == 0 and self.status != 'landed':
			self.status = 'landed'
			self.landed_time = self.positions[-1][0]

# funcion que simula la llegada y aproximacion de aviones a AEP
def simulate_planes(lambda_prob=0.2, total_minutes=1080):
	planes = []
	queue = []
	rejoining = []
	next_id = 1
	
	# Usar tqdm para mostrar progreso de la simulación solo si no está deshabilitado globalmente
	use_tqdm = getattr(simulate_planes, "use_tqdm", False)
	iterator = range(total_minutes)
	if use_tqdm:
		iterator = tqdm(iterator, desc="⏱️  Simulando", unit="min", disable=(total_minutes < 100))
	for t in iterator:
		# Aparición de nuevos aviones
		if random.random() < lambda_prob:
			plane = Plane(next_id, t)
			# Chequeo de separación temporal con el anterior en la cola
			if queue:
				prev_plane = queue[-1]
				if (plane.appear_time - prev_plane.appear_time) < MIN_SEPARATION_MIN:  #si el tiempo entre aviones es menor al minimo de separacion
					plane.speed = max(plane.get_min_speed(), prev_plane.speed - 20) #ajusta la velocidad a 20 nudos menos
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
						# Chequeo: ¿la velocidad está dentro del rango permitido?
						vmin, vmax = plane.get_range()
						if plane.speed < vmin or plane.speed > vmax:
							print(f"[ADVERTENCIA] Avión {plane.id} en t={t} mn={plane.dist:.2f} velocidad={plane.speed:.2f} fuera de rango [{vmin}, {vmax}]")
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
			if plane.dist > 100:
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
			# Actualizar posición de los aviones en estado 'approaching'
			if plane.status == 'approaching':
				plane.update_position(1) # actualiza la posicion con dt=1 minuto
				if plane.status == 'landed':
					to_remove_landed.append(plane) # se marca como aterrizado y para eliminarse de "approaching"
		for plane in to_remove_landed:
			if plane in queue:
				queue.remove(plane) # se elimina de "approaching" a los aterrizados
	return planes, total_minutes

# funcion que imprime un resumen estadistico de la simulacion
def print_summary(planes):
	"""
	Imprime un resumen estadístico de la simulación.
	
	Args:
		planes: Lista de objetos Plane de la simulación
	"""
	landed = [p for p in planes if p.status == 'landed']
	montevideo = [p for p in planes if p.status == 'montevideo']
	en_aproximacion = [p for p in planes if p.status == 'approaching' and p.dist > 0]
	
