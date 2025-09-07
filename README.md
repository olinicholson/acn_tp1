# Simulación Monte Carlo de Aproximación y Aterrizaje de Aviones en AEP

Este proyecto simula el proceso de aproximación y aterrizaje de aviones en el Aeropuerto Jorge Newbery (AEP) entre las 6am y la medianoche, considerando congestión y restricciones operativas.

## Lógica del modelo

- **Aparición de aviones:** Cada minuto, con probabilidad `lambda_prob`, aparece un avión a 100 millas náuticas (mn) de la pista.
- **Velocidad:** Cada avión avanza según la velocidad máxima permitida en su rango de distancia:
  - >100 mn: 500-300 nudos
  - 100-50 mn: 300-250 nudos
  - 50-15 mn: 250-200 nudos
  - 15-5 mn: 200-150 nudos
  - 5-0 mn: 150-120 nudos
- **Separación mínima:** No puede haber aterrizajes separados por menos de 4 minutos. Si un avión se acerca demasiado al anterior, reduce su velocidad a 20 nudos menos que el avión de adelante (sin bajar del mínimo permitido).
- **Montevideo:** Si aún así no puede mantener la separación, el avión sale de la fila y se va a Montevideo.

## Estructura del código

- `Plane`: Clase que representa cada avión, con atributos de posición, velocidad, estado y métodos para actualizar su posición y velocidad según el rango.
- `simulate_planes`: Función principal que simula la aparición y movimiento de todos los aviones, gestionando la cola y las reglas de separación y Montevideo.
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
