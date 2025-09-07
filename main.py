

# Simulación Monte Carlo de varios aviones aproximándose y aterrizando

# Simulación Monte Carlo mejorada con animación horizontal en tiempo real

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import random

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
	for t in range(total_minutes):
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
								if (curr_time_to_land_nueva - prev_time_to_land) < BUFFER_MIN:
									# No logra buffer, va a rejoin
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
	en_aproximacion = [p for p in planes if p.status == 'approaching' and p.dist > 0]
	print(f"Total de aviones simulados: {len(planes)}")
	print(f"Aterrizados: {len(landed)}")
	print(f"Se fueron a Montevideo: {len(montevideo)}")
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
	hora = 6 + minuto // 60
	minutos = minuto % 60
	return f"{hora:02d}:{minutos:02d}"

if __name__ == "__main__":
	# Simulación Monte Carlo completa: todos los aviones, aparición aleatoria, velocidad por rango, separación mínima
	print("Simulación Monte Carlo de todos los aviones entre 6am y 12am:")
	lambda_prob = 0.1
	total_minutes = 1080
	print(f"Lambda de aparición: {lambda_prob} aviones/minuto")
	planes, _ = simulate_planes(lambda_prob, total_minutes)
	#animate_planes_real_time(planes, total_minutes)
	plot_landing_times_bar(planes)
	print_summary(planes)
