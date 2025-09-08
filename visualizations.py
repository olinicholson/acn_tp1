"""
Módulo de visualizaciones para la simulación Monte Carlo de aproximación de aeronaves.
Contiene todas las funciones de gráficos y animaciones.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
from main import simulate_planes, knots_to_nm_per_min, eta_minutes

def animate_planes_real_time(planes, total_minutes):
    """
    Crea una animación en tiempo real de la simulación de aeronaves.
    
    Args:
        planes: Lista de objetos Plane de la simulación
        total_minutes: Duración total de la simulación en minutos
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(100, 0)
    ax.set_ylim(0, total_minutes)
    ax.set_xlabel('Distancia a pista (mn)', fontsize=12)
    ax.set_ylabel('Minuto de simulación', fontsize=12)
    ax.set_title('Simulación Monte Carlo: Aproximación de aeronaves en tiempo real', fontsize=14)
    
    # Agregar líneas de referencia
    ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5, label='50mn')
    ax.axvline(x=15, color='gray', linestyle='--', alpha=0.5, label='15mn')
    ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5, label='5mn')

    landed_planes = [p for p in planes if p.status == 'landed']
    montevideo_planes = [p for p in planes if p.status == 'montevideo']
    cmap = plt.get_cmap('tab20', max(1, len(landed_planes)))

    scatters = []
    for idx, plane in enumerate(landed_planes):
        scatters.append(ax.scatter([], [], color=cmap(idx), s=40, label=f'Avión {plane.id}'))
    for plane in montevideo_planes:
        scatters.append(ax.scatter([], [], color='red', s=40, marker='x', label=f'Montevideo {plane.id}'))

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

    ani = animation.FuncAnimation(fig, update, frames=range(0, total_minutes, 10), 
                                interval=100, blit=True, repeat=True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
    plt.tight_layout()
    plt.show()
    return ani

def plot_landing_times_bar(planes):
    """
    Crea un histograma de los horarios de aterrizaje.
    
    Args:
        planes: Lista de objetos Plane de la simulación
    """
    landed = [p for p in planes if p.status == 'landed']
    if not landed:
        print("No hay aviones aterrizados para graficar")
        return
    
    horas = [(6 + int(p.landed_time // 60)) for p in landed]
    
    plt.figure(figsize=(12, 6))
    n, bins, patches = plt.hist(horas, bins=range(6, 25), color='skyblue', 
                               edgecolor='black', align='left', alpha=0.7)
    
    # Colorear las barras según la cantidad
    colors = cm.viridis(n / max(n))
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
    
    plt.xlabel('Hora de aterrizaje', fontsize=12)
    plt.ylabel('Cantidad de aterrizajes', fontsize=12)
    plt.title('Distribución de aterrizajes por hora (6am a 12am)', fontsize=14)
    plt.xticks(range(6, 25))
    plt.grid(True, alpha=0.3)
    
    # Agregar valores en las barras
    for i, v in enumerate(n):
        if v > 0:
            plt.text(i + 6, v + 0.1, str(int(v)), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()

def plot_speed_distribution(planes):
    """
    Gráfica la distribución de velocidades durante la simulación.
    
    Args:
        planes: Lista de objetos Plane de la simulación
    """
    all_speeds = []
    all_distances = []
    
    for plane in planes:
        if plane.status in ['landed', 'montevideo']:
            # Reconstruir velocidades basándose en las posiciones
            for i in range(len(plane.positions) - 1):
                t1, d1 = plane.positions[i]
                t2, d2 = plane.positions[i + 1]
                if t2 > t1:  # Evitar división por cero
                    speed = abs(d1 - d2) / ((t2 - t1) / 60)  # nudos
                    all_speeds.append(speed)
                    all_distances.append(d1)
    
    if not all_speeds:
        print("No hay datos de velocidad para graficar")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Histograma de velocidades
    ax1.hist(all_speeds, bins=30, color='lightcoral', edgecolor='black', alpha=0.7)
    ax1.set_xlabel('Velocidad (nudos)', fontsize=12)
    ax1.set_ylabel('Frecuencia', fontsize=12)
    ax1.set_title('Distribución de velocidades', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # Scatter plot velocidad vs distancia
    scatter = ax2.scatter(all_distances, all_speeds, alpha=0.6, c=all_distances, 
                         cmap='viridis', s=20)
    ax2.set_xlabel('Distancia a pista (mn)', fontsize=12)
    ax2.set_ylabel('Velocidad (nudos)', fontsize=12)
    ax2.set_title('Velocidad vs Distancia', fontsize=14)
    ax2.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax2, label='Distancia (mn)')
    
    plt.tight_layout()
    plt.show()

def plot_delay_analysis(planes):
    """
    Analiza y grafica los atrasos de las aeronaves.
    
    Args:
        planes: Lista de objetos Plane de la simulación
    """
    landed = [p for p in planes if p.status == 'landed']
    if not landed:
        print("No hay aviones aterrizados para analizar atrasos")
        return
    
    def baseline_time_from_100nm():
        """Tiempo teórico mínimo desde 100mn sin congestión"""
        t = 50/(300/60) + 35/(250/60) + 10/(200/60) + 5/(150/60)
        return t
    
    baseline = baseline_time_from_100nm()
    delays = [(p.landed_time - p.appear_time) - baseline for p in landed]
    appear_times = [p.appear_time for p in landed]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Atrasos en el tiempo
    ax1.scatter(appear_times, delays, alpha=0.6, color='orange', s=30)
    ax1.set_xlabel('Minuto de aparición', fontsize=12)
    ax1.set_ylabel('Atraso (minutos)', fontsize=12)
    ax1.set_title('Atraso vs Tiempo de aparición', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Sin atraso')
    ax1.legend()
    
    # Histograma de atrasos
    ax2.hist(delays, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
    ax2.set_xlabel('Atraso (minutos)', fontsize=12)
    ax2.set_ylabel('Frecuencia', fontsize=12)
    ax2.set_title('Distribución de atrasos', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=np.mean(delays), color='red', linestyle='--', 
                label=f'Promedio: {np.mean(delays):.1f} min')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()

def plot_system_efficiency(planes):
    """
    Gráfica métricas de eficiencia del sistema.
    
    Args:
        planes: Lista de objetos Plane de la simulación
    """
    landed = len([p for p in planes if p.status == 'landed'])
    montevideo = len([p for p in planes if p.status == 'montevideo'])
    in_flight = len([p for p in planes if p.status == 'approaching'])
    
    # Gráfico de torta
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    labels = ['Aterrizados', 'Montevideo', 'En vuelo']
    sizes = [landed, montevideo, in_flight]
    colors = ['lightgreen', 'lightcoral', 'lightyellow']
    explode = (0.1, 0, 0)  # explode the first slice
    
    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.set_title('Distribución de resultados de vuelos', fontsize=14)
    
    # Eficiencia por hora
    landed_planes = [p for p in planes if p.status == 'landed']
    if landed_planes:
        hours = range(6, 24)
        landings_per_hour = []
        
        for hour in hours:
            count = len([p for p in landed_planes 
                        if hour <= (6 + p.landed_time // 60) < hour + 1])
            landings_per_hour.append(count)
        
        ax2.bar(hours, landings_per_hour, color='steelblue', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Hora del día', fontsize=12)
        ax2.set_ylabel('Aterrizajes por hora', fontsize=12)
        ax2.set_title('Capacidad del sistema por hora', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(hours)
    
    plt.tight_layout()
    plt.show()

def plot_comparative_analysis(lambda_values=[0.1, 0.15, 0.2, 0.25]):
    """
    Compara resultados para diferentes valores de lambda.
    
    Args:
        lambda_values: Lista de valores de lambda a comparar
    """
    results = []
    
    print("Ejecutando simulaciones comparativas...")
    for lambda_val in lambda_values:
        print(f"Simulando con λ = {lambda_val}")
        planes, _ = simulate_planes(lambda_val, 1080)
        landed = len([p for p in planes if p.status == 'landed'])
        montevideo = len([p for p in planes if p.status == 'montevideo'])
        total = len(planes)
        efficiency = (landed / total * 100) if total > 0 else 0
        
        results.append({
            'lambda': lambda_val,
            'total': total,
            'landed': landed,
            'montevideo': montevideo,
            'efficiency': efficiency
        })
    
    # Gráficos comparativos
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    lambdas = [r['lambda'] for r in results]
    totals = [r['total'] for r in results]
    landed_counts = [r['landed'] for r in results]
    montevideo_counts = [r['montevideo'] for r in results]
    efficiencies = [r['efficiency'] for r in results]
    
    # Total de aviones vs lambda
    ax1.plot(lambdas, totals, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Lambda (probabilidad/minuto)', fontsize=12)
    ax1.set_ylabel('Total de aviones', fontsize=12)
    ax1.set_title('Aviones generados vs Lambda', fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # Aterrizados vs Montevideo
    width = 0.35
    x = np.arange(len(lambdas))
    ax2.bar(x - width/2, landed_counts, width, label='Aterrizados', color='lightgreen')
    ax2.bar(x + width/2, montevideo_counts, width, label='Montevideo', color='lightcoral')
    ax2.set_xlabel('Lambda', fontsize=12)
    ax2.set_ylabel('Cantidad de aviones', fontsize=12)
    ax2.set_title('Aterrizados vs Desvíos', fontsize=14)
    ax2.set_xticks(x)
    ax2.set_xticklabels(lambdas)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Eficiencia del sistema
    ax3.plot(lambdas, efficiencies, 'ro-', linewidth=2, markersize=8)
    ax3.set_xlabel('Lambda (probabilidad/minuto)', fontsize=12)
    ax3.set_ylabel('Eficiencia (%)', fontsize=12)
    ax3.set_title('Eficiencia del sistema vs Lambda', fontsize=14)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)
    
    # Tasa de desvíos
    diversion_rates = [(r['montevideo'] / r['total'] * 100) if r['total'] > 0 else 0 for r in results]
    ax4.plot(lambdas, diversion_rates, 'mo-', linewidth=2, markersize=8)
    ax4.set_xlabel('Lambda (probabilidad/minuto)', fontsize=12)
    ax4.set_ylabel('Tasa de desvíos (%)', fontsize=12)
    ax4.set_title('Desvíos a Montevideo vs Lambda', fontsize=14)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return results

def run_complete_analysis(lambda_prob=0.15, total_minutes=1080, show_animation=False):
    """
    Ejecuta un análisis completo con todas las visualizaciones.
    
    Args:
        lambda_prob: Probabilidad de aparición de aeronaves
        total_minutes: Duración de la simulación
        show_animation: Si mostrar la animación (puede ser lenta)
    """
    print(f"Ejecutando simulación completa con λ = {lambda_prob}")
    print(f"Duración: {total_minutes} minutos ({total_minutes/60:.1f} horas)")
    print("-" * 60)
    
    # Ejecutar simulación
    planes, _ = simulate_planes(lambda_prob, total_minutes)
    
    # Estadísticas básicas
    landed = [p for p in planes if p.status == 'landed']
    montevideo = [p for p in planes if p.status == 'montevideo']
    en_aproximacion = [p for p in planes if p.status == 'approaching' and p.dist > 0]
    
    print(f"Total de aviones simulados: {len(planes)}")
    print(f"Aterrizados: {len(landed)} ({len(landed)/len(planes)*100:.1f}%)")
    print(f"Se fueron a Montevideo: {len(montevideo)} ({len(montevideo)/len(planes)*100:.1f}%)")
    print(f"En aproximación al final: {len(en_aproximacion)}")
    print("-" * 60)
    
    # Generar todos los gráficos
    print("Generando visualizaciones...")
    
    print("1. Histograma de aterrizajes por hora")
    plot_landing_times_bar(planes)
    
    print("2. Distribución de velocidades")
    plot_speed_distribution(planes)
    
    print("3. Análisis de atrasos")
    plot_delay_analysis(planes)
    
    print("4. Eficiencia del sistema")
    plot_system_efficiency(planes)
    
    if show_animation:
        print("5. Animación en tiempo real (esto puede tomar un momento)")
        animate_planes_real_time(planes, total_minutes)
    
    print("\n¿Desea ejecutar análisis comparativo? (puede tomar varios minutos)")
    response = input("y/N: ").lower()
    if response == 'y':
        print("6. Análisis comparativo")
        plot_comparative_analysis()
    
    print("\nAnálisis completo terminado!")

if __name__ == "__main__":
    print("=== MÓDULO DE VISUALIZACIONES ===")
    print("1. Análisis completo con gráficos estándar")
    print("2. Análisis completo con animación")
    print("3. Solo análisis comparativo")
    print("4. Personalizado")
    
    choice = input("\nSeleccione una opción (1-4): ")
    
    if choice == "1":
        run_complete_analysis()
    elif choice == "2":
        run_complete_analysis(show_animation=True)
    elif choice == "3":
        plot_comparative_analysis()
    elif choice == "4":
        lambda_val = float(input("Ingrese valor de lambda (ej: 0.15): "))
        duration = int(input("Ingrese duración en minutos (ej: 1080): "))
        animation = input("¿Mostrar animación? (y/N): ").lower() == 'y'
        run_complete_analysis(lambda_val, duration, animation)
    else:
        print("Opción no válida. Ejecutando análisis estándar...")
        run_complete_analysis()
