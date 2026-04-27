# ==========================================================
# IQ DIGITS - SOLVER BASE (ORTOOLS + NUMPY)
# Autor: Base académica para taller UTA
# Modelo CSP:
# - Cada dígito 0..9 es una pieza rígida
# - Puede rotarse 0,90,180,270
# - Se ubica en tablero de aristas
# - No se superponen
# - Se dejan solo 2 aristas libres
# ==========================================================

from ortools.sat.python import cp_model as cp
import numpy as np

# ----------------------------------------------------------
# TABLERO
# ----------------------------------------------------------
# horizontales: 5 x 5
# verticales:   4 x 6

H_FILAS = 5
H_COLS  = 5

V_FILAS = 4
V_COLS  = 6

TOTAL_ARISTAS = 25 + 24   # 49


# ----------------------------------------------------------
# PIEZAS (modelo LCD)
# cada arista = ('h'/'v', fila_rel, col_rel)
# ----------------------------------------------------------

PIEZAS = {
0: [('h',0,0),('h',1,0),('v',0,0),('v',0,1)],
1: [('v',0,0),('v',1,0)],
2: [('h',0,0),('h',1,0),('h',2,0),('v',0,1),('v',1,0)],
3: [('h',0,0),('h',1,0),('h',2,0),('v',0,1),('v',1,1)],
4: [('h',1,0),('v',0,0),('v',0,1),('v',1,1)],
5: [('h',0,0),('h',1,0),('h',2,0),('v',0,0),('v',1,1)],
6: [('h',0,0),('h',1,0),('h',2,0),('v',0,0),('v',1,0),('v',1,1)],
7: [('h',0,0),('v',0,1),('v',1,1)],
8: [('h',0,0),('h',1,0),('h',2,0),('v',0,0),('v',0,1),('v',1,0),('v',1,1)],
9: [('h',0,0),('h',1,0),('h',2,0),('v',0,0),('v',0,1),('v',1,1)],
}


# ----------------------------------------------------------
# ROTACION
# ----------------------------------------------------------

def rotar_segmento(seg):
    tipo, r, c = seg

    # rotación 90° alrededor del origen
    if tipo == 'h':
        return ('v', c, -r)
    else:
        return ('h', c, -r)


def normalizar(pieza):
    """
    Ajusta coordenadas mínimas a (0,0)
    """
    filas = [x[1] for x in pieza]
    cols  = [x[2] for x in pieza]

    minf = min(filas)
    minc = min(cols)

    return [(t, f-minf, c-minc) for (t,f,c) in pieza]


def rotar_pieza(pieza, veces):
    p = pieza[:]

    for _ in range(veces):
        p = [rotar_segmento(x) for x in p]

    return normalizar(p)


# ----------------------------------------------------------
# VERIFICAR SI CABE EN TABLERO
# ----------------------------------------------------------

def entra_en_tablero(pieza, fila0, col0):

    for tipo, f, c in pieza:

        F = fila0 + f
        C = col0 + c

        if tipo == 'h':
            if not (0 <= F < H_FILAS and 0 <= C < H_COLS):
                return False
        else:
            if not (0 <= F < V_FILAS and 0 <= C < V_COLS):
                return False

    return True


# ----------------------------------------------------------
# GENERAR TODAS LAS UBICACIONES POSIBLES
# ----------------------------------------------------------

def generar_opciones():

    opciones = {}

    for d in range(10):

        opciones[d] = []

        for rot in range(4):

            pieza_rot = rotar_pieza(PIEZAS[d], rot)

            for i in range(6):
                for j in range(6):

                    if entra_en_tablero(pieza_rot, i, j):
                        opciones[d].append((rot, i, j, pieza_rot))

    return opciones


# ----------------------------------------------------------
# SOLVER
# ----------------------------------------------------------

def aristas_absolutas(opcion):
    _, fi, co, pieza = opcion
    return [(tipo, fi + f, co + c) for (tipo, f, c) in pieza]


def construir_tablero(seleccion):
    H_tab = np.zeros((H_FILAS, H_COLS), dtype=int)
    V_tab = np.zeros((V_FILAS, V_COLS), dtype=int)

    for _, opcion in seleccion:
        for tipo, F, C in aristas_absolutas(opcion):
            if tipo == 'h':
                H_tab[F][C] = 1
            else:
                V_tab[F][C] = 1

    return H_tab, V_tab


def construir_tablero_dueno(seleccion):
    H_dueno = np.full((H_FILAS, H_COLS), '.', dtype='<U1')
    V_dueno = np.full((V_FILAS, V_COLS), '.', dtype='<U1')

    for d, opcion in seleccion:
        for tipo, F, C in aristas_absolutas(opcion):
            if tipo == 'h':
                if H_dueno[F][C] == '.':
                    H_dueno[F][C] = str(d)
                else:
                    H_dueno[F][C] = 'X'
            else:
                if V_dueno[F][C] == '.':
                    V_dueno[F][C] = str(d)
                else:
                    V_dueno[F][C] = 'X'

    return H_dueno, V_dueno


def imprimir_tablero_visual(H_dueno, V_dueno):
    for i in range(H_FILAS):
        fila_h = "o"
        for j in range(H_COLS):
            fila_h += f"-{H_dueno[i][j]}-o"
        print(fila_h)

        if i < V_FILAS:
            fila_v = " " + "   ".join(V_dueno[i][j] for j in range(V_COLS))
            print(fila_v)

    print("o")
    print()


def verificar_consistencia(seleccion, H_tab, V_tab):
    ok = True

    digitos = [d for d, _ in seleccion]
    if len(seleccion) != 10 or len(set(digitos)) != 10:
        print("[FALLA] No hay exactamente una opcion por cada digito 0..9")
        ok = False
    else:
        print("[OK] Cada digito se uso exactamente una vez")

    usadas = set()
    choque = False
    for _, opcion in seleccion:
        for arista in aristas_absolutas(opcion):
            if arista in usadas:
                choque = True
            usadas.add(arista)

    if choque:
        print("[FALLA] Hay superposicion de aristas")
        ok = False
    else:
        print("[OK] No hay superposicion de aristas")

    aristas_usadas = len(usadas)
    libres = TOTAL_ARISTAS - aristas_usadas

    if aristas_usadas == TOTAL_ARISTAS - 2:
        print(f"[OK] Aristas usadas = {aristas_usadas}, libres = {libres}")
    else:
        print(f"[FALLA] Aristas usadas = {aristas_usadas}, se esperaban {TOTAL_ARISTAS - 2}")
        ok = False

    suma_tablero = int(np.sum(H_tab) + np.sum(V_tab))
    if suma_tablero == aristas_usadas:
        print("[OK] Conteo del tablero consistente con seleccion")
    else:
        print("[FALLA] Conteo del tablero inconsistente con seleccion")
        ok = False

    return ok


def resolver_base():

    model = cp.CpModel()

    opciones = generar_opciones()

    # variable booleana por opción elegida
    usar = {}

    for d in range(10):
        for k in range(len(opciones[d])):
            usar[(d,k)] = model.NewBoolVar(f"pieza_{d}_{k}")

    # ------------------------------------------------------
    # Cada pieza se usa exactamente una vez
    # ------------------------------------------------------

    for d in range(10):
        model.AddExactlyOne(
            usar[(d,k)] for k in range(len(opciones[d]))
        )

    # ------------------------------------------------------
    # Cobertura de aristas por opciones
    # ------------------------------------------------------

    cobertura_h = {(i, j): [] for i in range(H_FILAS) for j in range(H_COLS)}
    cobertura_v = {(i, j): [] for i in range(V_FILAS) for j in range(V_COLS)}

    for d in range(10):
        for k, opcion in enumerate(opciones[d]):
            b = usar[(d, k)]
            for tipo, F, C in aristas_absolutas(opcion):
                if tipo == 'h':
                    cobertura_h[(F, C)].append(b)
                else:
                    cobertura_v[(F, C)].append(b)

    # ------------------------------------------------------
    # No superposición:
    # una arista no puede ser activada por 2 piezas distintas
    # ------------------------------------------------------

    for i in range(H_FILAS):
        for j in range(H_COLS):
            model.Add(sum(cobertura_h[(i, j)]) <= 1)

    for i in range(V_FILAS):
        for j in range(V_COLS):
            model.Add(sum(cobertura_v[(i, j)]) <= 1)

    # ------------------------------------------------------
    # Variables de ocupacion de aristas
    # ------------------------------------------------------

    H = np.array([
        [model.NewBoolVar(f"h({i},{j})") for j in range(H_COLS)]
        for i in range(H_FILAS)
    ])

    V = np.array([
        [model.NewBoolVar(f"v({i},{j})") for j in range(V_COLS)]
        for i in range(V_FILAS)
    ])

    for i in range(H_FILAS):
        for j in range(H_COLS):
            model.Add(sum(cobertura_h[(i, j)]) == H[i][j])

    for i in range(V_FILAS):
        for j in range(V_COLS):
            model.Add(sum(cobertura_v[(i, j)]) == V[i][j])

    # ------------------------------------------------------
    # Solo 2 aristas libres
    # ------------------------------------------------------

    model.Add(
        sum(H.flatten()) + sum(V.flatten()) == TOTAL_ARISTAS - 2
    )

    # ------------------------------------------------------
    # Resolver
    # ------------------------------------------------------

    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 20
    solver.parameters.num_search_workers = 1

    status = solver.Solve(model)

    if status in (cp.OPTIMAL, cp.FEASIBLE):

        print("SOLUCION ENCONTRADA\n")

        seleccion = []
        for d in range(10):
            for k in range(len(opciones[d])):
                if solver.Value(usar[(d, k)]):
                    opcion = opciones[d][k]
                    rot, fi, co, _ = opcion
                    seleccion.append((d, opcion))
                    print(f"Pieza {d}: fila={fi}, col={co}, rot={rot*90}")

        H_tab, V_tab = construir_tablero(seleccion)
        H_dueno, V_dueno = construir_tablero_dueno(seleccion)
        aristas_usadas = int(np.sum(H_tab) + np.sum(V_tab))

        print(f"\nAristas usadas: {aristas_usadas}")
        print(f"Aristas libres: {TOTAL_ARISTAS - aristas_usadas}\n")

        imprimir_tablero_visual(H_dueno, V_dueno)

        print("Chequeo automatico:")
        consistente = verificar_consistencia(seleccion, H_tab, V_tab)
        if consistente:
            print("Resultado del chequeo: OK")
        else:
            print("Resultado del chequeo: FALLA")

    else:
        print("No se encontro solucion.")

    print()
    print('NumConflicts: {}'.format(solver.NumConflicts()))
    print('NumBranches:  {}'.format(solver.NumBranches()))
    print('WallTime:     {}'.format(solver.WallTime()))


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------

resolver_base()
