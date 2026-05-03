import numpy as np
from ortools.sat.python import cp_model

class IQDigitsSolver:
    def __init__(self):
        #Inicializa el modelo de restricciones y los parámetros del tablero.
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.num_search_workers = 8 # Uso de paralelismo
        
        # Dimensiones de la grilla unificada (9x11)
        self.FILAS, self.COLS = 9, 11
        self.TOTAL_H, self.TOTAL_V = 25, 24
        self.TOTAL_ARISTAS = self.TOTAL_H + self.TOTAL_V

        # Definición de dígitos (1: ocupado, 0: vacío)
        self.DIGITOS_DICCIONARIO = {
            0: np.array([[0,1,0],[1,0,1],[0,1,0]]),                   
            1: np.array([[0,0,0],[0,0,1],[0,0,0],[0,0,1],[0,0,0]]),   
            2: np.array([[0,1,0],[0,0,1],[0,1,0],[1,0,0],[0,1,0]]),   
            3: np.array([[0,1,0],[0,0,1],[0,1,0],[0,0,1],[0,1,0]]),   
            4: np.array([[0,0,0],[1,0,1],[0,1,0],[0,0,1],[0,0,0]]),   
            5: np.array([[0,1,0],[1,0,0],[0,1,0],[0,0,1],[0,1,0]]),   
            6: np.array([[0,1,0],[1,0,0],[0,1,0],[1,0,1],[0,1,0]]),   
            7: np.array([[0,1,0],[0,0,1],[0,0,0],[0,0,1],[0,0,0]]),   
            8: np.array([[0,1,0],[1,0,1],[0,1,0],[1,0,1],[0,1,0]]),   
            9: np.array([[0,1,0],[1,0,1],[0,1,0],[0,0,1],[0,1,0]]),   
        }

    def _indice_arista(self, f, c):
        #Convierte coordenadas (f, c) de la grilla 9x11 a un índice lineal (0-48).
        if f % 2 == 0: # Arista Horizontal
            return (f // 2) * 5 + (c // 2)
        else:          # Arista Vertical
            return self.TOTAL_H + (f // 2) * 6 + (c // 2)

    def _preparar_colocaciones(self):
        #Genera todas las transformaciones y posiciones posibles para cada dígito.
        colocaciones = {d: [] for d in range(10)}
        for d in range(10):
            plantilla_base = self.DIGITOS_DICCIONARIO[d]
            for rot in range(4):
                # Rotación de la matriz usando NumPy
                p = np.rot90(plantilla_base, rot)
                h, w = p.shape
                # Desplazamiento por la grilla (pasos de 2 para mantener paridad)
                for f_off in range(0, self.FILAS - h + 1, 2):
                    for c_off in range(0, self.COLS - w + 1, 2):
                        aristas = []
                        f_coords, c_coords = np.where(p == 1)
                        for rf, rc in zip(f_coords, c_coords):
                            aristas.append(self._indice_arista(f_off + rf, c_off + rc))
                        
                        colocaciones[d].append({
                            'var': self.model.NewBoolVar(f'd{d}_r{rot}_f{f_off}_c{c_off}'),
                            'aristas': tuple(aristas),
                            'config': (rot, f_off, c_off)
                        })
        return colocaciones

    def mostrar_referencias(self):
        #Muestra guías visuales para facilitar la entrada de datos al usuario.
        print("\n[MAPA DE ESQUINAS] -> Para colocar piezas (Dígitos)")
        print("       c=0     c=1     c=2     c=3     c=4     c=5")
        for f in range(5):
            print(f"f={f}   " + "".join(f"({f},{c})---" for c in range(6))[:-3])
            if f < 4: print("       |       |       |       |       |       |")
        
        print("\n[MAPA DE CELDAS] -> Para pistas de SUMA")
        print("       c=0     c=1     c=2     c=3     c=4")
        for f in range(4):
            print(f"f={f}   " + "".join(f"[{f},{c}]   " for c in range(5)))
        print("-" * 55)

    def resolver(self, piezas_fijas, pistas_celda):
        #Construye el modelo CSP y busca la solución.
        colocaciones = self._preparar_colocaciones()
        cobertura_aristas = [[] for _ in range(self.TOTAL_ARISTAS)]
        
        # 1. Restricción: Cada dígito se usa exactamente una vez
        for d in range(10):
            self.model.AddExactlyOne(c['var'] for c in colocaciones[d])
            for c in colocaciones[d]:
                for a in c['aristas']:
                    cobertura_aristas[a].append((d, c['var']))

        # 2. Restricción: No solapamiento en aristas
        for a in range(self.TOTAL_ARISTAS):
            if cobertura_aristas[a]:
                self.model.Add(sum(var for d, var in cobertura_aristas[a]) <= 1)

        # 3. Modo Puzle: Piezas fijas
        for d, rot, f, c in piezas_fijas:
            for col in colocaciones[d]:
                if col['config'] == (rot, f, c):
                    self.model.Add(col['var'] == 1)

        # 4. Modo Restricción: Etiquetas de grupo y sumas
        for rf, rc, suma_obj, izq, der, arr, aba in pistas_celda:
            aristas_celda = [
                self.TOTAL_H + rf*6 + rc,     # Izquierda
                self.TOTAL_H + rf*6 + rc + 1, # Derecha
                rf*5 + rc,                    # Arriba
                (rf+1)*5 + rc                 # Abajo
            ]
            etiquetas = [izq, der, arr, aba]
            grupos = {}

            for arista, etiqueta in zip(aristas_celda, etiquetas):
                if etiqueta == 0:
                    self.model.Add(sum(var for d, var in cobertura_aristas[arista]) == 0)
                else:
                    self.model.Add(sum(var for d, var in cobertura_aristas[arista]) == 1)
                    grupos.setdefault(etiqueta, []).append(arista)

            # Variables de dígito por etiqueta
            digitos_grupos = []
            for e, lista_aristas in grupos.items():
                dg = self.model.NewIntVar(0, 9, f'dg_c{rf}{rc}_e{e}')
                for a in lista_aristas:
                    # El valor del grupo es el dígito que ocupa la arista
                    self.model.Add(dg == sum(d * var for d, var in cobertura_aristas[a]))
                digitos_grupos.append(dg)

            if len(digitos_grupos) > 1:
                self.model.AddAllDifferent(digitos_grupos) # Diferentes etiquetas = diferentes dígitos
            self.model.Add(sum(digitos_grupos) == suma_obj)

        # 5. Resolución
        status = self.solver.Solve(self.model)
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self._imprimir_solucion(colocaciones)
        else:
            print("\n[!] Sin solución. Verifique las restricciones.")

    def _imprimir_solucion(self, colocaciones):
        #Dibuja el tablero final en formato ASCII.
        res = np.full((self.FILAS, self.COLS), '·')
        res[::2, ::2] = '+'
        for d in range(10):
            for c in colocaciones[d]:
                if self.solver.Value(c['var']):
                    for a_idx in c['aristas']:
                        if a_idx < self.TOTAL_H: # Horizontal
                            f, col = (a_idx // 5) * 2, (a_idx % 5) * 2 + 1
                        else: # Vertical
                            idx = a_idx - self.TOTAL_H
                            f, col = (idx // 6) * 2 + 1, (idx % 6) * 2
                        res[f, col] = str(d)
        
        print("\n=== TABLERO RESUELTO ===")
        for fila in res:
            print(" ".join(fila))
        print("========================\n")

# --- Bloque Principal ---
def main():
    print("\n" + "="*55)
    print("                  IQ DIGITS SOLVER  ")
    print("="*55)

    app = IQDigitsSolver()
    app.mostrar_referencias()
    
    fijas, pistas = [], []
    
    print(">>> PIEZAS FIJAS (Dígito Rotación{0-3} Fila Columna) - Enter para saltar:")
    while (ent := input("> ")):
        try:
            d, r, f, c = map(int, ent.split())
            fijas.append((d, r, f*2, c*2))
        except: print("Formato inválido.")

    print("\n>>> PISTAS DE SUMA (Fila Col Suma Izq Der Arr Aba) - Enter para resolver:")
    while (ent := input("> ")):
        try:
            p = tuple(map(int, ent.split()))
            if len(p) == 7: pistas.append(p)
        except: print("Formato inválido.")

    app.resolver(fijas, pistas)

if __name__ == "__main__":
    main()