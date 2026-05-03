# IQ Digits Solver: Versión Orientada a Objetos (CP-SAT)

Este proyecto universitario de **Inteligencia Artificial** resuelve el rompecabezas _IQ Digits_ de SmartGames empleando **Programación por Restricciones** con la librería `OR-Tools` de Google. Nuestra implementación destaca por un diseño robusto basado en objetos y un motor de búsqueda optimizado para manejar múltiples restricciones simultáneas.

---

## 1. Reglas y Componentes del Juego

### El Tablero (Grilla Unificada 9×11)

El tablero se modela como una estructura de aristas horizontales y verticales:

- **Aristas Totales**: 49 (25 horizontales y 24 verticales).
- **Celdas**: 20 unidades de 1×1, cada una rodeada por 4 aristas.
- **Sistema de Coordenadas**: Se utiliza una matriz de 9 filas × 11 columnas donde las posiciones `(par, impar)` son aristas horizontales y las `(impar, par)` son aristas verticales.

### Los Dígitos (0–9)

Cada dígito tiene una geometría única inspirada en un display LCD:

| Dígito      |  0  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  |
| :---------- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **Aristas** |  4  |  2  |  5  |  5  |  4  |  5  |  6  |  3  |  7  |  6  |

> **Nota**: La ocupación total es de 47 aristas, dejando siempre **2 aristas vacías** en cualquier solución válida.

---

## 2. Pistas por Celda (Etiquetas de Grupo)

El programa soporta el **Modo Restricción**, donde el usuario ingresa pistas para celdas específicas siguiendo el formato de etiquetas:

- **Etiqueta 0**: La arista debe permanecer **vacía**.
- **Etiquetas 1–4**: Identifican grupos de pertenencia.
  - Aristas con la **misma etiqueta** deben ser cubiertas por el **mismo dígito**.
  - Aristas con **etiquetas distintas** deben ser cubiertas por **dígitos distintos**.
- **Suma**: El valor total de la pista es la suma de los valores de los dígitos únicos que forman los grupos de la celda.

---

## 3. Especificación del Modelo CSP

### Variables de Decisión

- **Variables Booleanas ($V$)**: Representan si el dígito $d$ se coloca en una rotación $r$ y posición $(f, c)$ determinada.
- **Variables Enteras de Grupo ($G$)**: Representan el valor numérico (0–9) del dígito asignado a una etiqueta específica dentro de una celda con pista.

### Restricciones Principales

1.  **Unicidad**: Cada dígito del 0 al 9 se utiliza exactamente una vez en el tablero.
2.  **No Solapamiento**: Una arista no puede ser compartida por dos o más dígitos.
3.  **Consistencia de Grupo**: Todas las aristas marcadas con la misma etiqueta en una celda se vinculan a la misma variable entera de dígito.
4.  **Dígitos Distintos**: Aplicación de la restricción global `AddAllDifferent` sobre las etiquetas de una misma celda.
5.  **Suma de Pista**: La suma de las variables de grupo debe igualar el objetivo definido por el usuario.

---

## 4. Diferenciación y Optimizaciones

A diferencia de otras implementaciones, nuestro solver incluye las siguientes mejoras técnicas:

- **Arquitectura OOP**: Encapsulamiento de la lógica en la clase `IQDigitsSolver`, facilitando la gestión del estado del modelo y la escalabilidad del código.
- **Procesamiento con NumPy**: Uso de `np.rot90` y `np.where` para generar dinámicamente las transformaciones de las piezas, reduciendo errores manuales en la definición de coordenadas.
- **Variables Ponderadas para Sumas**: En lugar de múltiples booleanos por grupo, se utiliza una **suma ponderada** ($ \sum d \cdot V $) para asignar valores a las variables de grupo, optimizando el tiempo de resolución del motor CP-SAT.
- **Interfaz de Referencia**: Visualización previa de mapas de coordenadas (Esquinas vs. Celdas) para minimizar errores humanos en la entrada de datos.

---

## 5. Requisitos y Uso

### Requisitos

- Python 3.8+
- Librerías: `ortools`, `numpy`

### Ejecución

1.  Instalar dependencias: `pip install ortools numpy`.
2.  Ejecutar el script: `python main.py`.
3.  Seguir las instrucciones en pantalla para ingresar **Piezas Fijas** (Modo Puzle) y **Pistas de Celda** (Modo Restricción).

---

## 6. Estructura del Código

| Componente                 | Descripción                                                    |
| :------------------------- | :------------------------------------------------------------- |
| `IQDigitsSolver`           | Clase principal que contiene el modelo CSP y el solver.        |
| `_preparar_colocaciones()` | Generador dinámico de rotaciones y posiciones para las piezas. |
| `_indice_arista()`         | Función de mapeo de coordenadas 9×11 a índices lineales.       |
| `resolver()`               | Orquestador de restricciones y ejecución de búsqueda.          |
| `mostrar_referencias()`    | Generador de mapas ASCII para asistencia al usuario.           |

---

_Proyecto realizado para la asignatura de Inteligencia Artificial - Taller de Resolución de Problemas mediante CSP._
