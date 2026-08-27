"""
Tetris minimo para entrenar un agente con algoritmo genetico.

Idea: en vez de mover la pieza tecla por tecla, para cada pieza se
generan TODAS las jugadas finales posibles (columna + rotacion, ya
caida). El agente (los "pesos" del GA) elige la jugada cuyo tablero
resultante tenga el mejor puntaje segun 4 metricas clasicas:

    altura acumulada, lineas completadas, huecos, bumpiness

El cromosoma del GA es justamente ese vector de 4 pesos.
"""

import copy
import random

PIEZAS = {
    "I": [[(1, 0), (1, 1), (1, 2), (1, 3)], [(0, 2), (1, 2), (2, 2), (3, 2)]],
    "O": [[(0, 1), (0, 2), (1, 1), (1, 2)]],
    "T": [[(0, 1), (1, 0), (1, 1), (1, 2)], [(0, 1), (1, 1), (1, 2), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 1)], [(0, 1), (1, 0), (1, 1), (2, 1)]],
    "S": [[(0, 1), (0, 2), (1, 0), (1, 1)], [(0, 1), (1, 1), (1, 2), (2, 2)]],
    "Z": [[(0, 0), (0, 1), (1, 1), (1, 2)], [(0, 2), (1, 1), (1, 2), (2, 1)]],
    "J": [[(0, 0), (1, 0), (1, 1), (1, 2)], [(0, 1), (0, 2), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)], [(0, 1), (1, 1), (2, 0), (2, 1)]],
    "L": [[(0, 2), (1, 0), (1, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (1, 2), (2, 0)], [(0, 0), (0, 1), (1, 1), (2, 1)]],
}

ANCHO, ALTO = 10, 20


class Tetris:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.tablero = [[False] * ANCHO for _ in range(ALTO)]
        self.lineas = 0
        self.piezas_colocadas = 0
        self.game_over = False
        self.pieza_actual = self.rng.choice(list(PIEZAS.keys()))

    def _cabe(self, celdas, tablero):
        for f, c in celdas:
            if c < 0 or c >= ANCHO or f >= ALTO:
                return False
            if f >= 0 and tablero[f][c]:
                return False
        return True

    def jugadas_posibles(self):
        """Devuelve cada jugada final posible: (rotacion, columna,
        tablero resultante, features del tablero resultante)."""
        jugadas = []
        for rot, forma in enumerate(PIEZAS[self.pieza_actual]):
            min_c = min(c for _, c in forma)
            max_c = max(c for _, c in forma)
            for desplaz in range(-min_c, ANCHO - max_c):
                celdas = [(f, c + desplaz) for f, c in forma]
                if not self._cabe(celdas, self.tablero):
                    continue
                # caer hasta el fondo
                caida = 0
                while self._cabe([(f + caida + 1, c) for f, c in celdas], self.tablero):
                    caida += 1
                celdas_final = [(f + caida, c) for f, c in celdas]

                nuevo = copy.deepcopy(self.tablero)
                for f, c in celdas_final:
                    if f < 0:
                        continue
                    nuevo[f][c] = True
                nuevo, lineas_limpiadas = self._limpiar_lineas(nuevo)

                jugadas.append({
                    "rotacion": rot,
                    "desplaz": desplaz,
                    "tablero": nuevo,
                    "lineas": lineas_limpiadas,
                    # features en orden fijo: [altura, lineas, huecos, bumpiness]
                    "features": self._features(nuevo, lineas_limpiadas),
                })
        return jugadas

    def aplicar(self, jugada):
        self.tablero = jugada["tablero"]
        self.lineas += jugada["lineas"]
        self.piezas_colocadas += 1
        self.pieza_actual = self.rng.choice(list(PIEZAS.keys()))
        if not self._cabe(PIEZAS[self.pieza_actual][0], self.tablero):
            self.game_over = True

    def _limpiar_lineas(self, tablero):
        filas_libres = [f for f in tablero if not all(f)]
        limpiadas = ALTO - len(filas_libres)
        return [[False] * ANCHO for _ in range(limpiadas)] + filas_libres, limpiadas

    def _features(self, tablero, lineas):
        alturas = []
        for c in range(ANCHO):
            h = 0
            for f in range(ALTO):
                if tablero[f][c]:
                    h = ALTO - f
                    break
            alturas.append(h)

        huecos = 0
        for c in range(ANCHO):
            bloque = False
            for f in range(ALTO):
                if tablero[f][c]:
                    bloque = True
                elif bloque:
                    huecos += 1

        bumpiness = sum(abs(alturas[i] - alturas[i + 1]) for i in range(ANCHO - 1))

        # Orden fijo: [altura, lineas, huecos, bumpiness]
        return [sum(alturas), lineas, huecos, bumpiness]


def elegir_jugada(juego, pesos):
    """pesos: lista de 4 numeros en orden [altura, lineas, huecos, bumpiness]."""
    jugadas = juego.jugadas_posibles()
    if not jugadas:
        return None
    return max(jugadas, key=lambda j: sum(p * f for p, f in zip(pesos, j["features"])))


def jugar(pesos, max_piezas=300, seed=None):
    """Juega una partida completa con estos pesos (lista de 4 numeros)
    y devuelve el fitness (numero de lineas completadas)."""
    juego = Tetris(seed=seed)
    while not juego.game_over and juego.piezas_colocadas < max_piezas:
        jugada = elegir_jugada(juego, pesos)
        if jugada is None:
            break
        juego.aplicar(jugada)
    return juego.lineas


if __name__ == "__main__":
    # [altura, lineas, huecos, bumpiness]
    pesos = [-0.51, 0.76, -0.36, -0.18]
    print("Lineas completadas:", jugar(pesos, seed=42))