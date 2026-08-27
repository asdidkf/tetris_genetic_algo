"""
Motor de Tetris simplificado, pensado para usarse como base de un
algoritmo genetico (o cualquier otra IA de busqueda).

Ideas clave del diseno:
- La logica del juego (TetrisGame) NO depende de graficos, por lo que
  se pueden simular miles de partidas por segundo.
- El metodo `get_possible_placements()` devuelve todas las jugadas
  finales posibles (columna + rotacion) para la pieza actual, junto
  con el tablero resultante. Esto es justo lo que necesita un GA:
  en vez de mover la pieza tecla por tecla, se evalua cada posible
  "aterrizaje" con una funcion heuristica y se elige el mejor segun
  los pesos del individuo (cromosoma).
- `board_features()` calcula las metricas clasicas usadas en papers
  de Tetris con GA: altura agregada, lineas completadas, huecos y
  "bumpiness" (irregularidad del perfil superior).
- Incluye un modo de visualizacion opcional con pygame, solo para
  poder ver jugar a tu mejor individuo. Para entrenar el GA no hace
  falta usar pygame en absoluto (es mucho mas rapido sin graficos).

Uso rapido (partida aleatoria, sin graficos):

    game = TetrisGame()
    while not game.game_over:
        placements = game.get_possible_placements()
        move = random.choice(placements)
        game.apply_placement(move)
    print("Score:", game.score, "Lineas:", game.lines_cleared)

Uso con un individuo del GA (vector de 4 pesos):

    def elegir_mejor_jugada(game, pesos):
        mejor = None
        mejor_valor = -math.inf
        for move in game.get_possible_placements():
            f = move["features"]
            valor = (pesos[0] * f["aggregate_height"] +
                     pesos[1] * f["lines_cleared"] +
                     pesos[2] * f["holes"] +
                     pesos[3] * f["bumpiness"])
            if valor > mejor_valor:
                mejor_valor = valor
                mejor = move
        return mejor
"""

import copy
import random

# ---------------------------------------------------------------------------
# Definicion de piezas (tetrominos) y sus rotaciones.
# Cada pieza es una lista de rotaciones; cada rotacion es una lista de
# coordenadas (fila, columna) relativas a una caja de 4x4.
# ---------------------------------------------------------------------------

TETROMINOS = {
    "I": [
        [(1, 0), (1, 1), (1, 2), (1, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
    ],
    "O": [
        [(0, 1), (0, 2), (1, 1), (1, 2)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 2), (1, 1), (1, 2), (2, 1)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

PIECE_COLORS = {
    "I": (0, 255, 255),
    "O": (255, 255, 0),
    "T": (160, 0, 240),
    "S": (0, 255, 0),
    "Z": (255, 0, 0),
    "J": (0, 0, 255),
    "L": (255, 165, 0),
}

BOARD_WIDTH = 10
BOARD_HEIGHT = 20


class TetrisGame:
    """Motor de Tetris sin graficos, listo para IA."""

    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT, seed=None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)

        # board[fila][columna] = None (vacio) o letra de la pieza
        self.board = [[None] * self.width for _ in range(self.height)]

        self.score = 0
        self.lines_cleared = 0
        self.pieces_placed = 0
        self.game_over = False

        self.bag = []  # "bolsa" de las 7 piezas, estilo Tetris moderno
        self.current_piece = self._next_piece()
        self.next_piece = self._next_piece()

    # -----------------------------------------------------------------
    # Generacion de piezas
    # -----------------------------------------------------------------
    def _next_piece(self):
        if not self.bag:
            self.bag = list(TETROMINOS.keys())
            self.rng.shuffle(self.bag)
        return self.bag.pop()

    # -----------------------------------------------------------------
    # Colocacion de piezas
    # -----------------------------------------------------------------
    def _cells_for(self, piece, rotation, col_offset):
        """Devuelve las celdas (fila, col) de una pieza en una rotacion
        dada, desplazada horizontalmente por col_offset."""
        return [(r, c + col_offset) for r, c in TETROMINOS[piece][rotation]]

    def _fits(self, cells, board=None):
        board = self.board if board is None else board
        for r, c in cells:
            if c < 0 or c >= self.width:
                return False
            if r >= self.height:
                return False
            if r >= 0 and board[r][c] is not None:
                return False
        return True

    def get_possible_placements(self):
        """Genera todas las jugadas finales posibles para la pieza
        actual: cada combinacion de rotacion y columna, ya caida hasta
        el fondo. Devuelve una lista de dicts con:
            - rotation, col_offset
            - board resultante (copia)
            - features (metricas del tablero resultante)
            - lines_cleared_by_move
        Esto es lo que un algoritmo genetico evalua para decidir la
        mejor jugada, en vez de simular tecla por tecla.
        """
        piece = self.current_piece
        placements = []

        for rotation in range(len(TETROMINOS[piece])):
            shape = TETROMINOS[piece][rotation]
            min_c = min(c for _, c in shape)
            max_c = max(c for _, c in shape)

            for col_offset in range(-min_c, self.width - max_c):
                cells = self._cells_for(piece, rotation, col_offset)

                # Si no cabe ni en la fila inicial, se descarta.
                if not self._fits(cells):
                    continue

                # Dejar caer la pieza hasta que ya no quepa un paso mas.
                drop = 0
                while self._fits([(r + drop + 1, c) for r, c in cells]):
                    drop += 1
                final_cells = [(r + drop, c) for r, c in cells]

                # Construir el tablero resultante.
                new_board = copy.deepcopy(self.board)
                for r, c in final_cells:
                    if r < 0:
                        # La pieza no entro completa: jugada invalida (game over)
                        continue
                    new_board[r][c] = piece

                new_board, cleared = self._clear_lines(new_board)
                features = self._board_features(new_board, cleared)

                placements.append({
                    "piece": piece,
                    "rotation": rotation,
                    "col_offset": col_offset,
                    "cells": final_cells,
                    "board": new_board,
                    "lines_cleared_by_move": cleared,
                    "features": features,
                })

        return placements

    def apply_placement(self, placement):
        """Aplica una jugada (obtenida de get_possible_placements) al
        estado real del juego y avanza a la siguiente pieza."""
        self.board = placement["board"]
        cleared = placement["lines_cleared_by_move"]
        self.lines_cleared += cleared
        self.score += self._score_for_lines(cleared)
        self.pieces_placed += 1

        self.current_piece = self.next_piece
        self.next_piece = self._next_piece()

        # Si la pieza nueva no cabe de entrada, se acabo la partida.
        shape = TETROMINOS[self.current_piece][0]
        if not self._fits(shape):
            self.game_over = True

    @staticmethod
    def _score_for_lines(cleared):
        # Puntuacion estilo NES clasico (aprox.)
        return {0: 0, 1: 40, 2: 100, 3: 300, 4: 1200}.get(cleared, 0)

    # -----------------------------------------------------------------
    # Metricas del tablero (para la funcion de fitness del GA)
    # -----------------------------------------------------------------
    def _clear_lines(self, board):
        new_rows = [row for row in board if any(cell is None for cell in row)]
        cleared = len(board) - len(new_rows)
        while len(new_rows) < len(board):
            new_rows.insert(0, [None] * self.width)
        return new_rows, cleared

    def _column_heights(self, board):
        heights = []
        for c in range(self.width):
            h = 0
            for r in range(self.height):
                if board[r][c] is not None:
                    h = self.height - r
                    break
            heights.append(h)
        return heights

    def _board_features(self, board, cleared):
        heights = self._column_heights(board)
        aggregate_height = sum(heights)
        bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))

        holes = 0
        for c in range(self.width):
            block_found = False
            for r in range(self.height):
                if board[r][c] is not None:
                    block_found = True
                elif block_found:
                    holes += 1

        return {
            "aggregate_height": aggregate_height,
            "lines_cleared": cleared,
            "holes": holes,
            "bumpiness": bumpiness,
            "max_height": max(heights) if heights else 0,
        }

    def board_features(self):
        """Features del tablero actual (sin aplicar ninguna jugada)."""
        return self._board_features(self.board, 0)

    # -----------------------------------------------------------------
    # Utilidad: representacion en texto (para debug rapido en consola)
    # -----------------------------------------------------------------
    def render_text(self):
        lines = []
        for row in self.board:
            lines.append("".join("#" if cell else "." for cell in row))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Ejemplo de agente controlado por un GA: cada individuo es un vector de
# pesos que pondera las features de cada jugada posible.
# ---------------------------------------------------------------------------

def elegir_mejor_jugada(game: TetrisGame, pesos: dict):
    """pesos es un dict tipo:
        {"aggregate_height": -0.5, "lines_cleared": 1.0,
         "holes": -0.8, "bumpiness": -0.3}
    Cuanto mas negativo el peso de una feature "mala" (huecos, altura),
    mas penaliza esa jugada. El GA evoluciona estos numeros.
    """
    placements = game.get_possible_placements()
    if not placements:
        return None

    def valor(p):
        f = p["features"]
        return sum(pesos.get(k, 0) * v for k, v in f.items())

    return max(placements, key=valor)


def jugar_partida(pesos: dict, max_piezas=500, seed=None):
    """Juega una partida completa usando los pesos dados y devuelve
    metricas utiles como fitness para el GA."""
    game = TetrisGame(seed=seed)
    while not game.game_over and game.pieces_placed < max_piezas:
        jugada = elegir_mejor_jugada(game, pesos)
        if jugada is None:
            break
        game.apply_placement(jugada)
    return {
        "score": game.score,
        "lines_cleared": game.lines_cleared,
        "pieces_placed": game.pieces_placed,
    }


# ---------------------------------------------------------------------------
# Visualizacion opcional con pygame (solo para ver jugar, no para entrenar)
# ---------------------------------------------------------------------------

def visualizar_con_pygame(pesos: dict, fps=8, cell_size=30):
    """Muestra en una ventana como juega un individuo con los pesos
    dados. Requiere `pip install pygame`. No es necesario para
    entrenar el algoritmo genetico: solo sirve para ver el resultado."""
    import pygame

    pygame.init()
    game = TetrisGame()
    screen = pygame.display.set_mode((game.width * cell_size, game.height * cell_size))
    pygame.display.set_caption("Tetris GA")
    clock = pygame.time.Clock()

    running = True
    while running and not game.game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        jugada = elegir_mejor_jugada(game, pesos)
        if jugada is None:
            break
        game.apply_placement(jugada)

        screen.fill((20, 20, 20))
        for r in range(game.height):
            for c in range(game.width):
                cell = game.board[r][c]
                if cell:
                    color = PIECE_COLORS[cell]
                    rect = (c * cell_size, r * cell_size, cell_size - 1, cell_size - 1)
                    pygame.draw.rect(screen, color, rect)
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    print("Score final:", game.score, "| Lineas:", game.lines_cleared)


if __name__ == "__main__":
    # Demo rapida sin graficos: pesos "a mano" razonables (parecidos a
    # los que suele converger un GA bien entrenado).
    pesos_demo = {
        "aggregate_height": -0.51,
        "lines_cleared": 0.76,
        "holes": -0.36,
        "bumpiness": -0.18,
    }
    resultado = jugar_partida(pesos_demo, max_piezas=200, seed=42)
    print("Resultado de partida de ejemplo:", resultado)