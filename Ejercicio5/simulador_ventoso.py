# simulador interactivo del arribo de aviones a AEP en un dia de viento
import pygame
import sys
import random
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Plane, knots_to_nm_per_min, eta_minutes, MIN_SEPARATION_MIN, BUFFER_MIN, REJOIN_GAP_MIN
from tqdm import tqdm
import math
import os

# clase PlaneVentoso con lógica de interrupción
class PlaneVentoso(Plane):
    def __init__(self, id, appear_time):
        super().__init__(id, appear_time)
        self.interrupciones = 0
        self.en_interrupcion = False  # Para marcarlo en amarillo
        
    def intentar_aterrizaje(self):
        """10% probabilidad de interrupción"""
        if random.random() < 0.1:  # 1/10 chance
            self.interrupciones += 1
            return False  # Interrupción
        return True  # Aterrizaje exitoso

pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulación de Tráfico Aéreo - DÍA VENTOSO - ACN TP1")

# Colors
WHITE = (255, 255, 255)
BLUE = (135, 206, 235)  # Sky blue
GREEN = (34, 139, 34)   # Forest green
DARK_GREEN = (0, 100, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)  # Para aviones con interrupción
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Fonts
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 32)
font_large = pygame.font.Font(None, 48)

# Cargar imagen del avión
try:
    # Obtener el directorio donde está este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_dir, "descarga.jpeg")
    
    plane_image = pygame.image.load(image_path)
    # Redimensionar la imagen a un tamaño intermedio que funcione bien
    plane_image = pygame.transform.scale(plane_image, (40, 25))
    # Hacer el fondo transparente (opcional)
    plane_image = plane_image.convert_alpha()
    USE_IMAGE = True
    print("✈️ Imagen del avión cargada correctamente")
except Exception as e:
    USE_IMAGE = False
    print(f"⚠️ No se pudo cargar la imagen del avión: {e}")
    print("Usando gráficos vectoriales como respaldo")

# Airport layout
AIRPORT_X = WIDTH - 150
AIRPORT_Y = HEIGHT // 2
RUNWAY_LENGTH = 120
RUNWAY_WIDTH = 20

class VisualSimulationVentoso:
    def __init__(self):
        self.current_time = 0
        self.time_speed = 0.2  # Velocidad muy lenta para ver la simulación paso a paso
        self.planes = []
        self.queue = []
        self.rejoining = []  # Lista de aviones en rejoin (del main.py)
        self.all_planes = []  # Mantener registro de todos los aviones
        self.simulation_running = False
        self.paused = False
        
        # Parámetros de simulación (igual que main.py)
        self.lambda_prob = 0.2
        self.total_minutes = 1080  # 18 horas (6am a 24hs)
        self.next_id = 1
        
        # Para tracking de estadísticas
        self.landed_count = 0
        self.montevideo_count = 0
        self.total_spawned = 0
        self.interrupciones_count = 0
        
        # Configurar semillas para reproducibilidad
        random.seed(42)
        np.random.seed(42)
        
    def start_simulation(self):
        """Inicia una nueva simulación"""
        self.planes = []
        self.queue = []
        self.all_planes = []
        self.current_time = 0
        self.landed_count = 0
        self.montevideo_count = 0
        self.total_spawned = 0
        self.interrupciones_count = 0
        self.next_id = 1
        self.simulation_running = True
        self.paused = False
        
        # Resetear semillas
        random.seed(42)
        np.random.seed(42)
        
    def update_simulation(self, dt):
        """Actualiza la simulación combinando lógica de main.py + día ventoso"""
        if not self.simulation_running or self.paused:
            return
            
        # Avanzar tiempo (simulación por minutos) - controlar velocidad
        old_time = int(self.current_time)
        self.current_time += dt * self.time_speed
        t = int(self.current_time)
        
        # Solo ejecutar lógica cuando cambia el minuto
        if t == old_time:
            return
            
        if t >= self.total_minutes:
            self.simulation_running = False
            return
        
        # === LÓGICA COMBINADA: main.py + día ventoso ===
        
        # 1. Aparición de nuevos aviones
        if random.random() < self.lambda_prob:
            plane = PlaneVentoso(self.next_id, t)
            # Chequeo de separación temporal con el anterior en la cola
            if self.queue:
                prev_plane = self.queue[-1]
                if (plane.appear_time - prev_plane.appear_time) < MIN_SEPARATION_MIN:
                    plane.speed = max(plane.get_min_speed(), prev_plane.speed - 20)
            
            self.all_planes.append(plane)
            self.queue.append(plane)
            self.next_id += 1
            self.total_spawned += 1
            
        # 2. Procesar aviones en estado 'approaching' (LÓGICA DE main.py)
        to_remove = []
        for i, plane in enumerate(self.queue[:]):
            if plane.status == 'approaching':
                if i > 0:
                    prev = self.queue[i-1]
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
                            self.rejoining.append(plane)
                            to_remove.append(plane)
                            continue
                        else:
                            plane.speed = nueva_speed
                    else:
                        plane.speed = plane.get_max_speed()
                else:
                    # Primer avión, no tiene anterior
                    plane.speed = plane.get_max_speed()
        
        # Remover aviones marcados para rejoin
        for plane in to_remove:
            if plane in self.queue:
                self.queue.remove(plane)
        
        # 3. Procesar aviones en rejoining (LÓGICA DE main.py)
        for plane in self.rejoining[:]:
            # Vuela hacia atrás a 200 nudos
            plane.dist += knots_to_nm_per_min(200)
            plane.positions.append((plane.positions[-1][0] + 1, plane.dist))
            
            # Si sale de las 100nm sin encontrar gap, se va a Montevideo
            if plane.dist > 100.0:
                plane.status = 'montevideo'
                plane.montevideo_time = t
                self.rejoining.remove(plane)
                self.montevideo_count += 1
                continue
            
            # Buscar gap de 10 minutos en la cola
            gap_found = False
            for j in range(1, len(self.queue)):
                prev2 = self.queue[j-1]
                curr2 = self.queue[j]
                prev2_time = t + eta_minutes(prev2.dist, prev2.speed) if prev2.status != 'landed' else prev2.landed_time
                curr2_time = t + eta_minutes(curr2.dist, curr2.speed) if curr2.status != 'landed' else curr2.landed_time
                
                if (curr2_time - prev2_time) >= REJOIN_GAP_MIN:
                    # Encontró gap, puede reingresar
                    plane.status = 'approaching'
                    plane.dist = plane.rejoin_dist
                    plane.positions.append((plane.positions[-1][0], plane.dist))
                    self.queue.insert(j, plane)
                    self.rejoining.remove(plane)
                    gap_found = True
                    break
        
        # 4. Actualizar posición y aterrizajes (LÓGICA COMBINADA)
        to_remove_landed = []
        for plane in self.queue[:]:
            if plane.status == 'approaching':
                plane.update_position(1)
                
                # Cuando llega a la pista (dist <= 0)
                if plane.dist <= 0:
                    # DÍA VENTOSO: Probabilidad de interrupción (1/10)
                    if plane.intentar_aterrizaje():  # 90% éxito
                        # ATERRIZAJE EXITOSO
                        plane.status = 'landed'
                        plane.landed_time = t
                        plane.en_interrupcion = False
                        to_remove_landed.append(plane)
                        self.landed_count += 1
                    else:  # 10% interrupción
                        # INTERRUPCIÓN - va a rejoin (como main.py)
                        plane.status = 'rejoin'
                        plane.rejoin_start_time = t
                        plane.rejoin_dist = 20.0  # Empieza el rejoin desde 20nm
                        plane.dist = 20.0
                        plane.en_interrupcion = True  # Marcarlo amarillo
                        plane.speed = plane.get_min_speed() * 0.5  # Velocidad reducida
                        self.rejoining.append(plane)
                        to_remove_landed.append(plane)
                        self.interrupciones_count += 1
                        
                        # CONGESTIÓN ADICIONAL (del día ventoso)
                        for other in self.queue:
                            if other != plane and other.status == 'approaching':
                                # Reducir velocidad a otros aviones
                                other.speed = max(other.get_min_speed() * 0.6, 80)
        
        for plane in to_remove_landed:
            if plane in self.queue:
                self.queue.remove(plane)
        
        # Actualizar lista de aviones visibles (approaching + rejoining)
        self.planes = [p for p in self.queue if p.status == 'approaching'] + self.rejoining
            
    def draw_plane(self, plane, x, y, color=WHITE):
        """Dibuja un avión usando la imagen real o gráficos vectoriales"""
        
        if USE_IMAGE:
            # Usar la imagen real del avión sin fondo
            clean_image = plane_image.copy()
            
            # Hacer el fondo transparente eliminando colores similares al amarillo/blanco
            # Convertir a RGBA para transparencia
            clean_image = clean_image.convert_alpha()
            
            # Eliminar el fondo - hacer transparentes los píxeles amarillos/blancos
            for x_pixel in range(clean_image.get_width()):
                for y_pixel in range(clean_image.get_height()):
                    pixel = clean_image.get_at((x_pixel, y_pixel))
                    # Si el pixel es muy claro (amarillo/blanco/gris claro), hacerlo transparente
                    if pixel[0] > 200 and pixel[1] > 200 and pixel[2] > 180:  # RGB valores altos
                        clean_image.set_at((x_pixel, y_pixel), (0, 0, 0, 0))  # Transparente
            
            # Si el avión tiene interrupción, agregar un borde amarillo
            if hasattr(plane, 'en_interrupcion') and plane.en_interrupcion:
                # Crear un rectángulo amarillo de fondo
                yellow_rect = pygame.Surface((clean_image.get_width() + 4, clean_image.get_height() + 4))
                yellow_rect.fill(YELLOW)
                yellow_rect.set_alpha(150)  # Semi-transparente
                
                # Centrar el rectángulo amarillo
                yellow_rect_pos = (x - (clean_image.get_width() + 4)//2, y - (clean_image.get_height() + 4)//2)
                screen.blit(yellow_rect, yellow_rect_pos)
            
            # Centrar la imagen en la posición
            image_rect = clean_image.get_rect(center=(x, y))
            screen.blit(clean_image, image_rect)
            
        else:
            # Usar gráficos vectoriales como respaldo
            # Colores más realistas
            fuselage_color = (220, 220, 220) if color == WHITE else color  # Gris claro para fuselaje
            wing_color = (180, 180, 180)  # Gris más oscuro para alas
            
            # Si tiene interrupción, dibujar fondo amarillo
            if hasattr(plane, 'en_interrupcion') and plane.en_interrupcion:
                pygame.draw.ellipse(screen, YELLOW, (x-18, y-10, 36, 20))
            
            # Fuselaje principal (cuerpo alargado del avión)
            pygame.draw.ellipse(screen, fuselage_color, (x-12, y-2, 24, 4))
            
            # Cabina (parte delantera más ancha)
            pygame.draw.ellipse(screen, fuselage_color, (x+8, y-3, 8, 6))
            
            # Alas principales (más realistas)
            # Ala izquierda
            pygame.draw.polygon(screen, wing_color, [
                (x-4, y-8),
                (x+6, y-2),
                (x+6, y+2),
                (x-4, y+8)
            ])
            
            # Motores en las alas
            pygame.draw.ellipse(screen, (100, 100, 100), (x-2, y-6, 6, 3))
            pygame.draw.ellipse(screen, (100, 100, 100), (x-2, y+3, 6, 3))
            
            # Cola vertical
            pygame.draw.polygon(screen, wing_color, [
                (x-12, y),
                (x-8, y-5),
                (x-8, y+5)
            ])
            
            # Cola horizontal
            pygame.draw.polygon(screen, wing_color, [
                (x-10, y-3),
                (x-6, y),
                (x-10, y+3)
            ])
            
            # Ventanas de la cabina
            pygame.draw.circle(screen, (50, 50, 150), (x+14, y-1), 1)
            pygame.draw.circle(screen, (50, 50, 150), (x+14, y+1), 1)
        
        # ID del avión (siempre visible)
        text = font_small.render(f"{plane.id}", True, BLACK)
        screen.blit(text, (x - 10, y + 12))
        
    def draw_airport(self):
        """Dibuja el aeropuerto y la pista"""
        # Pista de aterrizaje
        runway_rect = pygame.Rect(AIRPORT_X - RUNWAY_LENGTH, AIRPORT_Y - RUNWAY_WIDTH//2, 
                                RUNWAY_LENGTH, RUNWAY_WIDTH)
        pygame.draw.rect(screen, GRAY, runway_rect)
        
        # Marcas de la pista
        for i in range(0, RUNWAY_LENGTH, 20):
            x = AIRPORT_X - RUNWAY_LENGTH + i
            pygame.draw.rect(screen, WHITE, (x, AIRPORT_Y - 2, 10, 4))
            
        # Torre de control
        tower_rect = pygame.Rect(AIRPORT_X - 30, AIRPORT_Y - 60, 20, 40)
        pygame.draw.rect(screen, DARK_GREEN, tower_rect)
        
        # Etiqueta del aeropuerto
        text = font_medium.render("AEROPUERTO", True, BLACK)
        screen.blit(text, (AIRPORT_X - 90, AIRPORT_Y + 40))
        
        # Línea de 100nm
        line_x = 50
        pygame.draw.line(screen, RED, (line_x, 50), (line_x, HEIGHT - 50), 2)
        text_100nm = font_small.render("100nm", True, RED)
        screen.blit(text_100nm, (line_x - 20, 30))
        
    def draw_planes(self):
        """Dibuja todos los aviones en sus posiciones actuales"""
        # Aviones en approaching
        approaching_planes = [p for p in self.planes if p.status == 'approaching']
        for i, plane in enumerate(approaching_planes):
            # Convertir distancia (0-100nm) a posición en pantalla
            # 100nm = línea roja, 0nm = aeropuerto
            x = int((100 - plane.dist) / 100 * (AIRPORT_X - 100)) + 50
            
            # Distribuir verticalmente los aviones para evitar superposición
            y_base = AIRPORT_Y - 200
            y_offset = (i % 8) * 40
            y = y_base + y_offset
            
            # Color según estado (amarillo para interrupciones)
            if hasattr(plane, 'en_interrupcion') and plane.en_interrupcion:
                color = YELLOW
            else:
                # Color según velocidad (sin amarillo molesto)
                speed_ratio = plane.speed / 500
                if speed_ratio > 0.8:
                    color = GREEN
                elif speed_ratio > 0.6:
                    color = WHITE  # Blanco en lugar de amarillo
                else:
                    color = ORANGE
                
            self.draw_plane(plane, x, y, color)
            
            # Mostrar información del avión
            info_lines = [
                f"#{plane.id} V:{plane.speed:.0f}kt D:{plane.dist:.1f}nm",
            ]
            if hasattr(plane, 'interrupciones') and plane.interrupciones > 0:
                info_lines.append(f"Interrupciones:{plane.interrupciones}")
            
            for j, line in enumerate(info_lines):
                text = font_small.render(line, True, color)
                screen.blit(text, (x + 25, y + j * 12))
        
        # Aviones en rejoin (volando hacia atrás)
        for i, plane in enumerate(self.rejoining):
            # Convertir distancia (puede ser > 100nm) a posición en pantalla
            x = int((100 - plane.dist) / 100 * (AIRPORT_X - 100)) + 50
            # Si está más allá de 100nm, dibujarlo a la izquierda
            if plane.dist > 100:
                x = 50 - int((plane.dist - 100) / 50 * 100)  # Extender hacia la izquierda
            
            # Distribuir verticalmente (parte inferior)
            y_base = AIRPORT_Y + 50
            y_offset = (i % 6) * 35
            y = y_base + y_offset
            
            # Color MAGENTA para rejoin, YELLOW si está interrumpido
            color = YELLOW if (hasattr(plane, 'en_interrupcion') and plane.en_interrupcion) else PURPLE
                
            self.draw_plane(plane, x, y, color)
            
            # Mostrar información específica de rejoin
            info_lines = [
                f"REJOIN #{plane.id} D:{plane.dist:.1f}nm",
            ]
            if hasattr(plane, 'interrupciones') and plane.interrupciones > 0:
                info_lines.append(f"Int:{plane.interrupciones}")
            
            for j, line in enumerate(info_lines):
                text = font_small.render(line, True, color)
                screen.blit(text, (x + 25, y + j * 12))
                
    def draw_info_panel(self):
        """Dibuja el panel de información y estadísticas"""
        panel_x = 20
        panel_y = 20
        
        # Fondo del panel
        panel_rect = pygame.Rect(panel_x - 10, panel_y - 10, 320, 260)
        pygame.draw.rect(screen, WHITE, panel_rect)
        pygame.draw.rect(screen, BLACK, panel_rect, 2)
        
        # Título
        title = font_medium.render("DÍA VENTOSO - ACN TP1", True, BLACK)
        screen.blit(title, (panel_x, panel_y))
        
        # Tiempo actual
        current_hour = 6 + int(self.current_time // 60)
        current_min = int(self.current_time % 60)
        time_text = font_medium.render(f"Hora: {current_hour:02d}:{current_min:02d}", 
                                     True, BLACK)
        screen.blit(time_text, (panel_x, panel_y + 30))
        
        # Duración total
        duration_text = font_small.render(f"Duración: 6:00 - 24:00 ({self.total_minutes//60}h)", 
                                        True, BLACK)
        screen.blit(duration_text, (panel_x, panel_y + 55))
        
        # Estadísticas
        approaching_count = len([p for p in self.planes if p.status == 'approaching'])
        interrumpidos = len([p for p in self.planes if hasattr(p, 'en_interrupcion') and p.en_interrupcion])
        
        stats = [
            f"Aviones aproximando: {approaching_count}",
            f"Con interrupciones: {interrumpidos}",
            f"En cola total: {len(self.queue)}",
            f"Aterrizados: {self.landed_count}",
            f"A Montevideo: {self.montevideo_count}",
            f"Total interrupciones: {self.interrupciones_count}",
            f"Total generados: {self.total_spawned}",
            f"Lambda: {self.lambda_prob} aviones/min"
        ]
        
        for i, stat in enumerate(stats):
            text = font_small.render(stat, True, BLACK)
            screen.blit(text, (panel_x, panel_y + 80 + i * 18))
            
        # Estado de la simulación
        if not self.simulation_running:
            status = "TERMINADA" if self.current_time >= self.total_minutes else "DETENIDA"
        elif self.paused:
            status = "PAUSADA"
        else:
            status = "EJECUTANDO"
            
        status_text = font_small.render(f"Estado: {status}", True, 
                                      RED if not self.simulation_running else 
                                      YELLOW if self.paused else GREEN)
        screen.blit(status_text, (panel_x, panel_y + 230))
        
    def draw_controls(self):
        """Dibuja los controles disponibles"""
        controls_y = HEIGHT - 160
        controls = [
            "CONTROLES - DÍA VENTOSO:",
            "ESPACIO - Iniciar/Pausar",
            "R - Reiniciar simulación", 
            "↑/+ - Aumentar velocidad",
            "↓/- - Reducir velocidad",
            "L - Cambiar lambda",
            "ESC - Salir",
            "🌪️ AMARILLO = INTERRUPCIÓN 1/10"
        ]
        
        for i, control in enumerate(controls):
            color = YELLOW if i == 0 or i == 7 else WHITE if i == 7 else GRAY
            text = font_small.render(control, True, color)
            screen.blit(text, (20, controls_y + i * 18))

# Inicializar simulación
sim = VisualSimulationVentoso()
clock = pygame.time.Clock()

# Game loop principal
running = True
while running:
    dt = clock.tick(60) / 1000.0  # Delta time en segundos
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                if not sim.simulation_running:
                    sim.start_simulation()
                else:
                    sim.paused = not sim.paused
            elif event.key == pygame.K_r:
                sim.start_simulation()
            elif event.key == pygame.K_UP or event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                sim.time_speed = min(20, sim.time_speed + 1)
            elif event.key == pygame.K_DOWN or event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                sim.time_speed = max(0.1, sim.time_speed - 1)
            elif event.key == pygame.K_l:
                # Cambiar lambda entre 0.1, 0.15, 0.2, 0.25
                lambdas = [0.1, 0.15, 0.2, 0.25]
                current_idx = lambdas.index(sim.lambda_prob) if sim.lambda_prob in lambdas else 0
                sim.lambda_prob = lambdas[(current_idx + 1) % len(lambdas)]
    
    # Actualizar simulación
    sim.update_simulation(dt)
    
    # Dibujar todo
    screen.fill(BLUE)
    
    sim.draw_airport()
    sim.draw_planes()
    sim.draw_info_panel()
    sim.draw_controls()
    
    # Mostrar velocidad de simulación
    speed_text = font_small.render(f"Velocidad: {sim.time_speed:.1f}x", True, WHITE)
    screen.blit(speed_text, (WIDTH - 150, 20))
    
    # Mostrar progreso
    progress = (sim.current_time / sim.total_minutes) * 100
    progress_text = font_small.render(f"Progreso: {progress:.1f}%", True, WHITE)
    screen.blit(progress_text, (WIDTH - 150, 45))
    
    pygame.display.flip()

pygame.quit()
sys.exit()
