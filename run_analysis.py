"""
Launcher para ejecutar diferentes tipos de análisis y visualizaciones
de la simulación Monte Carlo de aproximación de aeronaves.
"""

import sys
import os

# Asegurar que podemos importar desde el directorio actual
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visualizations import (
    run_complete_analysis,
    plot_comparative_analysis,
    animate_planes_real_time,
    plot_landing_times_bar,
    plot_speed_distribution,
    plot_delay_analysis,
    plot_system_efficiency
)
from main import simulate_planes

def menu_principal():
    """Muestra el menú principal de opciones."""
    print("=" * 60)
    print("    SIMULACIÓN MONTE CARLO - APROXIMACIÓN DE AERONAVES")
    print("=" * 60)
    print()
    print("Opciones disponibles:")
    print()
    print("1. 📊 Análisis completo (todos los gráficos)")
    print("2. 🎬 Análisis completo con animación")
    print("3. 📈 Solo análisis comparativo (múltiples λ)")
    print("4. 🔧 Simulación personalizada")
    print("5. 📋 Gráficos individuales")
    print("6. ⚡ Simulación rápida (solo estadísticas)")
    print("0. 🚪 Salir")
    print()

def menu_graficos_individuales():
    """Submenú para gráficos individuales."""
    print("\n" + "=" * 40)
    print("    GRÁFICOS INDIVIDUALES")
    print("=" * 40)
    print()
    print("1. Histograma de aterrizajes por hora")
    print("2. Distribución de velocidades")
    print("3. Análisis de atrasos")
    print("4. Eficiencia del sistema")
    print("5. Animación en tiempo real")
    print("0. Volver al menú principal")
    print()

def obtener_parametros_personalizados():
    """Obtiene parámetros personalizados del usuario."""
    print("\nConfiguración personalizada:")
    
    try:
        lambda_val = float(input("Lambda (probabilidad/minuto) [0.15]: ") or "0.15")
        if lambda_val <= 0 or lambda_val > 1:
            print("⚠️  Valor de lambda fuera de rango. Usando 0.15")
            lambda_val = 0.15
    except ValueError:
        print("⚠️  Valor inválido. Usando lambda = 0.15")
        lambda_val = 0.15
    
    try:
        duration = int(input("Duración en minutos [1080]: ") or "1080")
        if duration <= 0:
            print("⚠️  Duración inválida. Usando 1080 minutos")
            duration = 1080
    except ValueError:
        print("⚠️  Valor inválido. Usando duración = 1080 minutos")
        duration = 1080
    
    return lambda_val, duration

def ejecutar_simulacion_rapida():
    """Ejecuta una simulación básica solo con estadísticas."""
    from main import print_summary, minutos_a_hora
    
    lambda_val, duration = obtener_parametros_personalizados()
    
    print(f"\n🚀 Ejecutando simulación rápida...")
    print(f"   λ = {lambda_val}, duración = {duration} min")
    
    planes, _ = simulate_planes(lambda_val, duration)
    
    print(f"\n📊 Resultados:")
    print_summary(planes)

def main():
    """Función principal del launcher."""
    while True:
        menu_principal()
        
        try:
            opcion = input("Seleccione una opción (0-6): ").strip()
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        
        if opcion == "0":
            print("👋 ¡Hasta luego!")
            break
        
        elif opcion == "1":
            print("\n📊 Iniciando análisis completo...")
            try:
                run_complete_analysis()
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif opcion == "2":
            print("\n🎬 Iniciando análisis completo con animación...")
            try:
                run_complete_analysis(show_animation=True)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif opcion == "3":
            print("\n📈 Iniciando análisis comparativo...")
            try:
                plot_comparative_analysis()
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif opcion == "4":
            try:
                lambda_val, duration = obtener_parametros_personalizados()
                animation = input("¿Incluir animación? (y/N): ").lower() == 'y'
                
                print(f"\n🔧 Iniciando simulación personalizada...")
                run_complete_analysis(lambda_val, duration, animation)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif opcion == "5":
            # Submenú de gráficos individuales
            while True:
                menu_graficos_individuales()
                
                try:
                    sub_opcion = input("Seleccione un gráfico (0-5): ").strip()
                except KeyboardInterrupt:
                    break
                
                if sub_opcion == "0":
                    break
                
                # Primero necesitamos datos de simulación
                try:
                    lambda_val, duration = obtener_parametros_personalizados()
                    print(f"\n🔄 Ejecutando simulación...")
                    planes, _ = simulate_planes(lambda_val, duration)
                    
                    if sub_opcion == "1":
                        plot_landing_times_bar(planes)
                    elif sub_opcion == "2":
                        plot_speed_distribution(planes)
                    elif sub_opcion == "3":
                        plot_delay_analysis(planes)
                    elif sub_opcion == "4":
                        plot_system_efficiency(planes)
                    elif sub_opcion == "5":
                        animate_planes_real_time(planes, duration)
                    else:
                        print("❌ Opción no válida")
                        continue
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif opcion == "6":
            try:
                ejecutar_simulacion_rapida()
            except Exception as e:
                print(f"❌ Error: {e}")
        
        else:
            print("❌ Opción no válida. Intente nuevamente.")
        
        # Pausa antes de mostrar el menú nuevamente
        if opcion != "0":
            input("\n⏸️  Presione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Por favor, verifique que todas las dependencias estén instaladas.")
