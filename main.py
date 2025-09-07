

# Simulación Monte Carlo de varios aviones aproximándose y aterrizando

# Simulación Monte Carlo mejorada con animación horizontal en tiempo real
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import random

MN_TO_KM = 1.852
KNOT_TO_KMH = 1.852

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
		speed_mn_min = speed * KNOT_TO_KMH / 60 / MN_TO_KM
		self.dist = max(0, self.dist - speed_mn_min * dt)
		self.positions.append((self.positions[-1][0] + dt, self.dist))
		if self.dist == 0 and self.status != 'landed':
			self.status = 'landed'
			self.landed_time = self.positions[-1][0]

def simulate_planes(lambda_prob=0.2, total_minutes=1080):
	planes = []
	queue = []
	next_id = 1
	landing_times = []
	for t in range(total_minutes):
		# Aparición de nuevos aviones
		if random.random() < lambda_prob:
			plane = Plane(next_id, t)
			# Chequeo de separación temporal con el anterior en la cola
			if queue:
				prev_plane = queue[-1]
				# Si la diferencia de aparición es menor a 4 minutos
				if (plane.appear_time - prev_plane.appear_time) < MIN_SEPARATION_MIN:
					# El avión ajusta velocidad a 20 nudos menos que el de adelante
					plane.speed = max(plane.get_min_speed(), prev_plane.speed - 20)
			planes.append(plane)
			queue.append(plane)
			next_id += 1
		# Actualización de posiciones y gestión de cola
		# Procesar aviones en estado 'approaching'
		for i, plane in enumerate(queue[:]):
			if plane.status == 'approaching':
				# Separación con el avión anterior
				if i > 0:
					prev = queue[i-1]
					# Calcular tiempo estimado de aterrizaje del anterior en la cola
					if prev.status == 'landed':
						prev_time_to_land = prev.landed_time
					else:
						prev_time_to_land = t + prev.dist / (prev.speed * KNOT_TO_KMH / 60 / MN_TO_KM)
					# Calcular tiempo estimado de aterrizaje del actual
					curr_time_to_land = t + plane.dist / (plane.speed * KNOT_TO_KMH / 60 / MN_TO_KM)
					# Si la separación estimada es menor a la mínima
					if (curr_time_to_land - prev_time_to_land) < MIN_SEPARATION_MIN:
						# El avión ajusta velocidad a 20 nudos menos que el de adelante
						nueva_speed = max(plane.get_min_speed(), prev.speed - 20)
						if nueva_speed < plane.get_min_speed():
							# No puede mantener separación, sale de la fila y busca gap de 10 min
							plane.status = 'rejoin'
							plane.montevideo_time = None
							plane.rejoin_start_time = t
							plane.rejoin_dist = plane.dist
							continue
						else:
							plane.speed = nueva_speed
							# Mantiene velocidad reducida hasta lograr 5 min de separación
							curr_time_to_land_nueva = t + plane.dist / (nueva_speed * KNOT_TO_KMH / 60 / MN_TO_KM)
							if (curr_time_to_land_nueva - prev_time_to_land) < (MIN_SEPARATION_MIN + 1):
								# Si ya está en velocidad mínima y sigue sin lograr separación, sale de la fila
								if plane.speed == plane.get_min_speed():
									plane.status = 'rejoin'
									plane.montevideo_time = None
									plane.rejoin_start_time = t
									plane.rejoin_dist = plane.dist
									continue
								# Sigue con velocidad reducida
								pass
							else:
								# Logró buffer, vuelve a velocidad máxima
								plane.speed = plane.get_max_speed()
					else:
						plane.speed = plane.get_max_speed()
				else:
					plane.speed = plane.get_max_speed()
		# Procesar aviones en estado 'rejoin' aparte
		for plane in queue[:]:
			if plane.status == 'rejoin':
				# Vuela hacia atrás a 200 nudos
				plane.dist += 200 * KNOT_TO_KMH / 60 / MN_TO_KM
				plane.positions.append((plane.positions[-1][0] + 1, plane.dist))
				# Si sale de las 100mn, se va a Montevideo y se elimina de la cola
				if plane.dist > 100.0:
					plane.status = 'montevideo'
					plane.montevideo_time = t
					if plane in queue:
						queue.remove(plane)
					continue
				# Buscar gap de 10 minutos en la cola
				gap_found = False
				for j in range(len(queue)):
					if j == 0:
						continue
					prev2 = queue[j-1]
					curr2 = queue[j]
					if prev2.status == 'landed':
						prev2_time = prev2.landed_time
					else:
						prev2_time = t + prev2.dist / (prev2.speed * KNOT_TO_KMH / 60 / MN_TO_KM)
					if curr2.status == 'landed':
						curr2_time = curr2.landed_time
					else:
						curr2_time = t + curr2.dist / (curr2.speed * KNOT_TO_KMH / 60 / MN_TO_KM)
					if (curr2_time - prev2_time) >= REJOIN_GAP_MIN:
						# Puede reingresar
						plane.status = 'approaching'
						plane.dist = plane.rejoin_dist
						plane.positions.append((plane.positions[-1][0], plane.dist))
						gap_found = True
						break
		# Actualizar posición de los aviones en estado 'approaching'
		for plane in queue:
			if plane.status == 'approaching':
				plane.update_position(1)
				if plane.status == 'landed':
					landing_times.append(plane.landed_time)
	return planes, total_minutes

import matplotlib
def animate_planes_real_time(planes, total_minutes):
	fig, ax = plt.subplots(figsize=(14,8))
	ax.set_xlim(100, 0)
	ax.set_ylim(0, total_minutes)
	ax.set_xlabel('Distancia a pista (mn)')
	ax.set_ylabel('Minuto de simulación')
	ax.set_title('Simulación Monte Carlo: Aproximación de aviones en tiempo real')

	landed_planes = [p for p in planes if p.status == 'landed']
	montevideo_planes = [p for p in planes if p.status == 'montevideo']
	cmap = plt.get_cmap('tab20', max(1, len(landed_planes)))

	scatters = []
	for idx, plane in enumerate(landed_planes):
		scatters.append(ax.scatter([], [], color=cmap(idx), s=40, label=f'Avión {plane.id}'))
	for plane in montevideo_planes:
		scatters.append(ax.scatter([], [], color='gray', s=40, label=f'Montevideo {plane.id}'))

	import numpy as np
	def update(frame):
		for idx, plane in enumerate(landed_planes):
			pos = [p for p in plane.positions if p[0] == frame]
			if pos:
				scatters[idx].set_offsets([[pos[0][1], frame]])
			else:
				scatters[idx].set_offsets(np.empty((0, 2)))
		for j, plane in enumerate(montevideo_planes):
			idx2 = len(landed_planes) + j
			pos = [p for p in plane.positions if p[0] == frame]
			if pos:
				scatters[idx2].set_offsets([[pos[0][1], frame]])
			else:
				scatters[idx2].set_offsets(np.empty((0, 2)))
		ax.set_title(f"Simulación Monte Carlo: Minuto {frame}")
		return scatters

	ani = animation.FuncAnimation(fig, update, frames=range(0, total_minutes, 10), interval=5, blit=True)
	ax.legend(loc='upper right')
	plt.tight_layout()
	plt.show()

def plot_landing_times_bar(planes):
	# Solo aviones aterrizados
	landed = [p for p in planes if p.status == 'landed']
	horas = [(6 + int(p.landed_time // 60)) for p in landed]
	plt.figure(figsize=(12,6))
	plt.hist(horas, bins=range(6,25), color='skyblue', edgecolor='black', align='left')
	plt.xlabel('Hora de aterrizaje')
	plt.ylabel('Cantidad de aterrizajes')
	plt.title('Distribución de aterrizajes por hora (6am a 12am)')
	plt.xticks(range(6,25))
	plt.tight_layout()
	plt.show()

def print_summary(planes):
	landed = [p for p in planes if p.status == 'landed']
	montevideo = [p for p in planes if p.status == 'montevideo']
	en_aproximacion = [p for p in planes if p.status == 'approaching']
	print(f"Total de aviones simulados: {len(planes)}")
	print(f"Aterrizados: {len(landed)}")
	print(f"Se fueron a Montevideo: {len(montevideo)}")
	print(f"En aproximación al final: {len(en_aproximacion)}")
	if landed:
		tiempos = [p.landed_time - p.appear_time for p in landed]
		print(f"Tiempo promedio de aproximación y aterrizaje: {np.mean(tiempos):.2f} minutos")


def minutos_a_hora(minuto):
	hora = 6 + minuto // 60
	minutos = minuto % 60
	return f"{hora:02d}:{minutos:02d}"

if __name__ == "__main__":
	# Simulación Monte Carlo completa: todos los aviones, aparición aleatoria, velocidad por rango, separación mínima
	print("Simulación Monte Carlo de todos los aviones entre 6am y 12am:")
	lambda_prob = 0.15
	total_minutes = 1080
	print(f"Lambda de aparición: {lambda_prob} aviones/minuto")
	planes, _ = simulate_planes(lambda_prob, total_minutes)
	#animate_planes_real_time(planes, total_minutes)
	plot_landing_times_bar(planes)
	print_summary(planes)
