
# En este archivo ejecutamos simulaciones Monte Carlo para distintos valores de lambda
from main import simulate_planes
import numpy as np
from tqdm import tqdm

def montecarlo_desvios(lambdas_prob, total_minutes, n_mc=30):
    """
    Realiza simulaciones Monte Carlo para cada lambda, reportando media y desvío estándar de probabilidad de desvío y congestión.
    """
    resultados = {}
    print(f"\nIniciando simulaciones Monte Carlo para {len(lambdas_prob)} valores de λ, {n_mc} repeticiones cada uno...")
    for lambda_prob in tqdm(lambdas_prob, desc="Simulando λ valores"):
        prob_desvios = []
        prob_congestiones = []
        for _ in range(n_mc):
            planes, _ = simulate_planes(lambda_prob, total_minutes)
            total_planes = len(planes)
            desviados = [p for p in planes if p.status == 'montevideo']
            aterrizados = [p for p in planes if p.status == 'landed']
            # Congestión: al menos un tramo volado más lento que su velocidad máxima (como antes)
            congestionados = 0
            for plane in aterrizados:
                if hasattr(plane, 'positions') and len(plane.positions) > 1:
                    for i in range(len(plane.positions) - 1):
                        t1, d1 = plane.positions[i]
                        t2, d2 = plane.positions[i + 1]
                        if t2 > t1:
                            speed_actual = abs(d1 - d2) / ((t2 - t1) / 60)
                            plane.dist = d1
                            max_speed = plane.get_max_speed()
                            if speed_actual < max_speed * 0.95:
                                congestionados += 1
                                break
            prob_desvio = len(desviados) / total_planes if total_planes > 0 else 0
            prob_congestion = congestionados / total_planes if total_planes > 0 else 0
            prob_desvios.append(prob_desvio)
            prob_congestiones.append(prob_congestion)
        prob_desvio_mean = np.mean(prob_desvios)
        prob_desvio_std = np.std(prob_desvios, ddof=1)
        prob_congestion_mean = np.mean(prob_congestiones)
        prob_congestion_std = np.std(prob_congestiones, ddof=1)
        resultados[lambda_prob] = {
            'prob_desvio': prob_desvio_mean,
            'prob_desvio_std': prob_desvio_std,
            'prob_congestion': prob_congestion_mean,
            'prob_congestion_std': prob_congestion_std
        }
        print(f"   λ={lambda_prob:.2f}: Prob. desvío = {prob_desvio_mean*100:.2f}% ± {prob_desvio_std*100:.2f}% | Prob. congestión = {prob_congestion_mean*100:.2f}% ± {prob_congestion_std*100:.2f}%")
    return resultados

def graficar_desvios_mc(resultados, lambdas_prob):
    import matplotlib.pyplot as plt
    lambdas = list(lambdas_prob)
    prob_desvios = [resultados[l]['prob_desvio'] * 100 for l in lambdas]
    prob_desvios_std = [resultados[l]['prob_desvio_std'] * 100 for l in lambdas]
    plt.figure(figsize=(12, 8))
    plt.errorbar(lambdas, prob_desvios, yerr=prob_desvios_std, fmt='ro-', linewidth=4, markersize=15, 
                 markerfacecolor='red', markeredgecolor='darkred', markeredgewidth=2, capsize=8, label='Prob. desvío')
    plt.xlabel('Tasa de Arribo λ (aviones por minuto)', fontsize=14, fontweight='bold')
    plt.ylabel('Desvíos a Montevideo (%)', fontsize=14, fontweight='bold')
    plt.title('📈 CRECIMIENTO EXPONENCIAL DE DESVÍOS vs TASA DE ARRIBO (Monte Carlo)', fontsize=16, fontweight='bold')
    for x, y, err in zip(lambdas, prob_desvios, prob_desvios_std):
        plt.annotate(f'{y:.1f}%\n±{err:.1f}', (x, y), textcoords="offset points", 
                    xytext=(0,20), ha='center', fontsize=14, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8))
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max([a+b for a,b in zip(prob_desvios, prob_desvios_std)]) * 1.3 if prob_desvios else 1)
    plt.tight_layout()
    plt.show()

def graficar_congestion_mc(resultados, lambdas_prob):
    import matplotlib.pyplot as plt
    lambdas = list(lambdas_prob)
    prob_congestion = [resultados[l]['prob_congestion'] * 100 for l in lambdas]
    prob_congestion_std = [resultados[l]['prob_congestion_std'] * 100 for l in lambdas]
    plt.figure(figsize=(12, 8))
    plt.errorbar(lambdas, prob_congestion, yerr=prob_congestion_std, fmt='bo-', linewidth=4, markersize=15,
                 markerfacecolor='blue', markeredgecolor='darkblue', markeredgewidth=2, capsize=8, label='Prob. congestión')
    plt.xlabel('Tasa de Arribo λ (aviones por minuto)', fontsize=14, fontweight='bold')
    plt.ylabel('Probabilidad de Congestión (%)', fontsize=14, fontweight='bold')
    plt.title('📉 PROBABILIDAD DE CONGESTIÓN vs TASA DE ARRIBO (Monte Carlo)', fontsize=16, fontweight='bold')
    for x, y, err in zip(lambdas, prob_congestion, prob_congestion_std):
        plt.annotate(f'{y:.1f}%\n±{err:.1f}', (x, y), textcoords="offset points", 
                    xytext=(0,20), ha='center', fontsize=14, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8))
    plt.grid(True, alpha=0.3)
    plt.ylim(0, max([a+b for a,b in zip(prob_congestion, prob_congestion_std)]) * 1.3 if prob_congestion else 1)
    plt.tight_layout()
    plt.show()

def tabla_resumen_mc(resultados, lambdas_prob):
    print("\n" + "="*80)
    print("TABLA DE RESUMEN - PROBABILIDAD DE DESVÍO Y CONGESTIÓN (Monte Carlo)")
    print("="*80)
    print("| λ (aviones/min) | % Desvíos ± std | % Congestión ± std |")
    print("|-----------------|------------------|---------------------|")
    for lambda_val in lambdas_prob:
        r = resultados[lambda_val]
        print(f"| {lambda_val:>13.2f} | {r['prob_desvio']*100:>7.1f}% ± {r['prob_desvio_std']*100:>5.1f} | "
              f"{r['prob_congestion']*100:>7.1f}% ± {r['prob_congestion_std']*100:>5.1f} |")
    print("="*80)

if __name__ == "__main__":
    # parámetros de simulación a probar 
    lambdas_prob = [0.02, 0.1, 0.2, 0.5, 1.0]  
    total_minutes = 1080  # duración de la simulación en minutos 
    n_mc = 30  # cantidad de repeticiones Monte Carlo
    print(" ANÁLISIS DE DESVÍOS Y CONGESTIÓN (Monte Carlo)")
    print("=" * 60)
    print("Analizando el crecimiento  de desvíos y congestión según λ")
    print(f"Valores de λ a evaluar: {lambdas_prob}")
    print(f"Duración de cada simulación: {total_minutes} minutos ({total_minutes/60} horas)")
    print(f"Repeticiones Monte Carlo: {n_mc}")
    print("=" * 60)
    resultados = montecarlo_desvios(lambdas_prob, total_minutes, n_mc=n_mc)
    graficar_desvios_mc(resultados, lambdas_prob)
    graficar_congestion_mc(resultados, lambdas_prob)
    tabla_resumen_mc(resultados, lambdas_prob)
