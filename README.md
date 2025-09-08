# Simulación Monte Carlo de Aproximación de Aeronaves

## Descripción

Este proyecto implementa una simulación Monte Carlo completa del sistema de aproximación de aeronaves a un aeropuerto, modelando condiciones realistas de congestión, separación temporal y gestión de tráfico aéreo.

## Características Principales

### 🛩️ Modelo de Aeronaves
- **Aparición aleatoria**: Basada en distribución de probabilidad configurable (λ)
- **Rangos de velocidad por distancia**: Velocidades realistas según la distancia a pista
- **Estado dinámico**: Aproximación, rejoin, Montevideo o aterrizaje

### ⏱️ Sistema de Separación
- **Separación mínima**: 4 minutos entre aeronaves consecutivas
- **Buffer objetivo**: 5 minutos para operaciones seguras
- **Reducción de velocidad**: 20 nudos menos que la aeronave anterior cuando hay conflicto

### 🔄 Gestión de Congestión
- **Rejoin automático**: Vuelo hacia atrás a 200 nudos para buscar gaps
- **Detección de gaps**: Búsqueda de espacios de 10+ minutos en la secuencia
- **Desvío a Montevideo**: Cuando no se puede mantener separación dentro de 100mn

### 📊 Análisis y Visualización
- **Animación en tiempo real**: Seguimiento visual de todas las aeronaves
- **Estadísticas detalladas**: Aterrizajes, desvíos, tiempos promedio
- **Distribución horaria**: Análisis de aterrizajes por hora del día

## Rangos de Velocidad por Distancia

| Distancia (mn) | Velocidad Mínima (kt) | Velocidad Máxima (kt) |
|----------------|----------------------|----------------------|
| >100           | 300                  | 500                  |
| 50-100         | 250                  | 300                  |
| 15-50          | 200                  | 250                  |
| 5-15           | 150                  | 200                  |
| 0-5            | 120                  | 150                  |

## Estructura del Código

### Clase `Plane`
```python
class Plane:
    def __init__(self, id, appear_time)
    def get_range()          # Obtiene rango de velocidad según distancia
    def get_max_speed()      # Velocidad máxima permitida
    def get_min_speed()      # Velocidad mínima permitida
    def update_position()    # Actualiza posición según velocidad y tiempo
```

### Función Principal `simulate_planes()`
- **Aparición de aeronaves**: Proceso estocástico con probabilidad λ
- **Gestión de cola**: Mantenimiento de secuencia ordenada
- **Lógica de separación**: Verificación y ajuste continuo de velocidades
- **Procesamiento de rejoin**: Gestión de aeronaves en busca de gaps
- **Actualización de posiciones**: Avance temporal de la simulación

### Funciones de Visualización
- `animate_planes_real_time()`: Animación interactiva de la simulación
- `plot_landing_times_bar()`: Histograma de aterrizajes por hora
- `print_summary()`: Estadísticas completas de la simulación

## Parámetros de Configuración

```python
MIN_SEPARATION_MIN = 4     # Separación mínima (minutos)
BUFFER_MIN = 5            # Buffer objetivo (minutos)
REJOIN_GAP_MIN = 10       # Gap mínimo para rejoin (minutos)
lambda_prob = 0.15        # Probabilidad de aparición por minuto
total_minutes = 1080      # Duración simulación (18 horas: 6am-12am)
```

## Lógica de Decisión de Rejoin

Una aeronave debe realizar rejoin cuando:
1. **Violación de velocidad mínima**: La velocidad requerida es menor al mínimo del rango, **O**
2. **Buffer insuficiente**: No puede lograr el buffer de 5 minutos incluso a velocidad mínima

## Métricas de Rendimiento

- **Tasa de aterrizajes exitosos**: Porcentaje de aeronaves que aterrizan
- **Desvíos a Montevideo**: Aeronaves que no pueden reintegrarse
- **Tiempo promedio de aproximación**: Desde aparición hasta aterrizaje
- **Atraso respecto al tiempo teórico**: Comparación con aproximación sin congestión
- **Distribución temporal**: Patrones de aterrizaje durante el día

## Uso del Programa

### Opción 1: Launcher Interactivo (Recomendado)
```bash
python run_analysis.py
```
Ofrece un menú completo con todas las opciones de análisis.

### Opción 2: Simulación Básica
```bash
python main.py
```
Ejecuta solo la simulación con estadísticas básicas.

### Opción 3: Módulo de Visualizaciones
```bash
python visualizations.py
```
Acceso directo al módulo de gráficos con menú de opciones.

### Configuración Programática
```python
from main import simulate_planes
from visualizations import run_complete_analysis

# Simulación personalizada
planes, _ = simulate_planes(lambda_prob=0.20, total_minutes=720)

# Análisis completo
run_complete_analysis(lambda_prob=0.15, total_minutes=1080, show_animation=True)
```

## Dependencias

```python
import numpy as np           # Cálculos matemáticos
import matplotlib.pyplot as plt     # Visualización
import matplotlib.animation as animation  # Animaciones
import matplotlib.cm as cm   # Mapas de color
import random               # Generación aleatoria
```

## Instalación de Dependencias

```bash
pip install numpy matplotlib
```

## Interpretación de Resultados

### Salida de Ejemplo
```
Simulación Monte Carlo de todos los aviones entre 6am y 12am:
Lambda de aparición: 0.15 aviones/minuto
Total de aviones simulados: 162
Aterrizados: 145
Se fueron a Montevideo: 12
En aproximación al final (en vuelo): 5
Tiempo promedio de aproximación y aterrizaje: 45.23 minutos
Atraso promedio respecto al mínimo teórico: 25.67 minutos
Desvío estándar del atraso: 18.45 minutos
```

### Análisis
- **Eficiencia del sistema**: 89.5% de aterrizajes exitosos
- **Impacto de congestión**: 25.67 min de atraso promedio
- **Variabilidad**: Desviación estándar indica dispersión en tiempos

## Casos de Estudio

### Baja Congestión (λ = 0.10)
- Alto porcentaje de aterrizajes
- Pocos desvíos a Montevideo
- Atrasos mínimos

### Alta Congestión (λ = 0.25)
- Incremento significativo de desvíos
- Mayor variabilidad en tiempos
- Activación frecuente del sistema de rejoin

## Extensiones Posibles

1. **Múltiples pistas**: Modelado de operaciones paralelas
2. **Condiciones meteorológicas**: Impacto en velocidades y separación
3. **Diferentes tipos de aeronaves**: Características específicas por tipo
4. **Optimización de secuencias**: Algoritmos de reordenamiento
5. **Análisis de capacidad**: Determinación de límites del sistema

## Validación del Modelo

El modelo ha sido validado para:
- ✅ Respeto de separaciones mínimas
- ✅ Adherencia a rangos de velocidad
- ✅ Comportamiento correcto del sistema de rejoin
- ✅ Conservación del número de aeronaves
- ✅ Realismo operacional

## Autor

Desarrollado como parte del Trabajo Práctico 1 - ACN 2025

## Archivos del Proyecto

- **`main.py`**: Código principal de simulación (lógica core, sin visualizaciones)
- **`visualizations.py`**: Módulo completo de gráficos y análisis visual
- **`run_analysis.py`**: Launcher interactivo para ejecutar diferentes tipos de análisis
- **`README.md`**: Documentación completa del proyecto
- **`Trabajo práctico 1 ACN 2025.pdf`**: Especificaciones originales

## Uso de los Archivos

### Ejecución Básica (solo estadísticas)
```bash
python main.py
```

### Análisis Visual Completo
```bash
python visualizations.py
```

### Launcher Interactivo (Recomendado)
```bash
python run_analysis.py
```

El launcher ofrece un menú interactivo con opciones para:
- 📊 Análisis completo con todos los gráficos
- 🎬 Análisis con animación en tiempo real
- 📈 Análisis comparativo de múltiples valores λ
- 🔧 Configuración personalizada de parámetros
- 📋 Gráficos individuales específicos
- ⚡ Simulación rápida solo con estadísticas
- `animate_planes_real_time`: Visualiza la aproximación de todos los aviones en tiempo real, mostrando su posición minuto a minuto.
- `plot_landing_times_bar`: Muestra un gráfico de barras con la cantidad de aterrizajes por hora.
- `print_summary`: Imprime un resumen con el total de aviones simulados, aterrizados, Montevideo y los que quedan en aproximación al final.

## Resultados y visualización

- El gráfico animado muestra la aproximación de cada avión, con colores distintos y los que se van a Montevideo en gris.
- El gráfico de barras muestra la distribución de aterrizajes por hora.
- El resumen final indica cuántos aviones aterrizaron, cuántos se fueron a Montevideo y cuántos quedaron en aproximación al finalizar la simulación.

## Parámetros principales
- `lambda_prob`: Probabilidad de aparición de un avión por minuto (ajustar para calibrar la demanda).
- `total_minutes`: Duración de la simulación (por defecto, 1080 minutos = 18 horas).

## Ejecución
Instala las dependencias con:
```bash
pip install -r requirements.txt
```
Ejecuta la simulación con:
```bash
python main.py
```

## Personalización
Puedes modificar los parámetros, los rangos de velocidad, o agregar nuevas reglas en el archivo `main.py` para explorar diferentes escenarios de congestión y operación.
