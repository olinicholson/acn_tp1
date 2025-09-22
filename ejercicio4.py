# multiples simulaciones Monte Carlo para distintos valores de lambda 
from main import simulate_planes, Plane
import numpy as np
from tqdm import tqdm

# funcion que realiza multiples simulaciones Monte Carlo para distintos valores de lambda
def arrivos_congest(lambdas_prob, total_minutes):
    resultados = {}
    
    print(f"\n Iniciando simulaciones para {len(lambdas_prob)} valores de λ...")
    
    for lambda_prob in tqdm(lambdas_prob, desc="Simulando λ valores"):
        print(f"\n Simulando λ = {lambda_prob} aviones/minuto...")
        
        # Ejecutar simulación
        planes, _ = simulate_planes(lambda_prob, total_minutes)
        
        # Separar por estado final
        aterrizados = [p for p in planes if p.status == 'landed']
        desviados = [p for p in planes if p.status == 'montevideo']
        total_planes = len(planes)
        
        # Contar aviones congestionados (simplificado)
        congestionados = 0
        for plane in aterrizados:
            if hasattr(plane, 'positions') and len(plane.positions) > 1:
                # Verificar si en algún momento voló más lento que su velocidad máxima
                for i in range(len(plane.positions) - 1):
                    t1, d1 = plane.positions[i]
                    t2, d2 = plane.positions[i + 1]
                    if t2 > t1:  # Asegurar que el tiempo avanzó
                        speed_actual = abs(d1 - d2) / ((t2 - t1) / 60)  # nudos
                        plane.dist = d1  # Temporal para get_max_speed
                        max_speed = plane.get_max_speed()
                        if speed_actual < max_speed * 0.95:  # 5% de tolerancia
                            congestionados += 1
                            break
        
        # Calcular retrasos vs tiempo teórico sin congestión
        tiempo_teorico = 50/(400/60) + 35/(275/60) + 10/(225/60) + 5/(135/60)  # Velocidades promedio
        retrasos = []
        for p in aterrizados:
            if p.landed_time is not None:
                tiempo_real = p.landed_time - p.appear_time
                retraso = tiempo_real - tiempo_teorico
                retrasos.append(retraso)
        
        # Estadísticas
        prob_desvio = len(desviados) / total_planes if total_planes > 0 else 0
        prob_congestion = congestionados / total_planes if total_planes > 0 else 0
        retraso_promedio = np.mean(retrasos) if retrasos else 0
        error_retraso = np.std(retrasos) / np.sqrt(len(retrasos)) if len(retrasos) > 1 else 0
        
        resultados[lambda_prob] = {
            'total_aviones': total_planes,
            'aterrizados': len(aterrizados),
            'desviados': len(desviados),
            'prob_desvio': prob_desvio,
            'prob_congestion': prob_congestion,
            'retraso_promedio': retraso_promedio,
            'error_retraso': error_retraso,
            'retrasos_raw': retrasos
        }
        
        print(f"   Probabilidad de desvío: {prob_desvio:.4f} ({prob_desvio*100:.2f}%)")
        print(f"   Probabilidad de congestión: {prob_congestion:.4f} ({prob_congestion*100:.2f}%)")
        print(f"   Retraso promedio: {retraso_promedio:.2f} ± {error_retraso:.2f} min")

    # Generar gráfico simple y tabla de resumen
    crear_grafico_desvios(resultados, lambdas_prob)
    mostrar_tabla_resumen(resultados, lambdas_prob)
    
    return resultados

# funcion que crea un grafico simple mostrando como aumentan los desvios
def crear_grafico_desvios(resultados, lambdas_prob):
    """
    Crea un gráfico simple mostrando cómo aumentan los desvíos exponencialmente.
    """
    import matplotlib.pyplot as plt
    
    # Preparar datos
    lambdas = list(lambdas_prob)
    prob_desvios = [resultados[l]['prob_desvio'] * 100 for l in lambdas]  # Convertir a porcentaje
    
    # Crear gráfico simple y claro
    plt.figure(figsize=(12, 8))
    
    # Gráfico de línea con puntos grandes
    plt.plot(lambdas, prob_desvios, 'ro-', linewidth=4, markersize=15, 
             markerfacecolor='red', markeredgecolor='darkred', markeredgewidth=2)
    
    # Etiquetas y título
    plt.xlabel('Tasa de Arribo λ (aviones por minuto)', fontsize=14, fontweight='bold')
    plt.ylabel('Desvíos a Montevideo (%)', fontsize=14, fontweight='bold')
    plt.title('📈 CRECIMIENTO EXPONENCIAL DE DESVÍOS vs TASA DE ARRIBO', fontsize=16, fontweight='bold')
    
    # Agregar valores en cada punto
    for x, y in zip(lambdas, prob_desvios):
        plt.annotate(f'{y:.1f}%', (x, y), textcoords="offset points", 
                    xytext=(0,20), ha='center', fontsize=14, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8))
    
    # Mejorar la visualización
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max(prob_desvios) * 1.3 if prob_desvios else 1)
    
    
    plt.tight_layout()
    plt.show()

# funcion que muestra una tabla de resumen de los datos obtenidos en las simulaciones
def mostrar_tabla_resumen(resultados, lambdas_prob):
    """
    Muestra una tabla de resumen clara y simple.
    """
    print("\n" + "="*80)
    print("TABLA DE RESUMEN - IMPACTO DE λ EN DESVÍOS")
    print("="*80)
    print("| λ (aviones/min) | Total Aviones | Aterrizados | Desvíos | % Desvíos | Retraso (min) |")
    print("|-----------------|----------------|-------------|---------|-----------|---------------|")

    for lambda_val in lambdas_prob:
        r = resultados[lambda_val]
        print(f"| {lambda_val:>13.2f} | {r['total_aviones']:>11} | {r['aterrizados']:>9} | {r['desviados']:>7} | {r['prob_desvio']*100:>7.1f}% | {r['retraso_promedio']:>11.1f} |")
    
    print("="*80)
    
    # Análisis de crecimiento
    print("\n ANÁLISIS DE CRECIMIENTO:")
    print("-"*50)
    
    desvios_porcentajes = [resultados[l]['prob_desvio']*100 for l in lambdas_prob]
    
    for i in range(1, len(lambdas_prob)):
        lambda_prev = lambdas_prob[i-1]
        lambda_curr = lambdas_prob[i]
        desvio_prev = desvios_porcentajes[i-1]
        desvio_curr = desvios_porcentajes[i]
        
        if desvio_prev > 0:
            multiplicador = desvio_curr / desvio_prev
            print(f" De λ={lambda_prev} a λ={lambda_curr}: {desvio_prev:.1f}% → {desvio_curr:.1f}% (×{multiplicador:.1f})")
        else:
            print(f" De λ={lambda_prev} a λ={lambda_curr}: {desvio_prev:.1f}% → {desvio_curr:.1f}%")

    print("="*80)


if __name__ == "__main__":
    # parámetros de simulación
    lambdas_prob = [0.02, 0.1, 0.2, 0.5, 1.0]  
    total_minutes = 1080  # duración de la simulación en minutos 
    
    print(" ANÁLISIS DE CONGESTIÓN AEROPORTUARIA")
    print("=" * 60)
    print("Analizando el crecimiento exponencial de desvíos según λ")
    print(f"Valores de λ a evaluar: {lambdas_prob}")
    print(f"Duración de cada simulación: {total_minutes} minutos ({total_minutes/60} horas)")
    print("=" * 60)
    
    # ejecutar simulaciones y generar gráfico simple + tabla
    resultados = arrivos_congest(lambdas_prob, total_minutes)
    
    
