"""
Visualiza en tiempo real una partida de Tetris jugada por el agente
(los pesos entrenados por el algoritmo genetico de agent.py).

Requiere pygame:
    pip install pygame

Uso:
    python visualizar.py
        -> usa los pesos guardados en mejor_pesos.txt (generado por
           agent.py + visualization.guardar_mejor) si existe, si no
           usa unos pesos de ejemplo razonables.

    python visualizar.py -0.51 0.76 -0.36 -0.18
        -> usa esos 4 pesos directamente [altura, lineas, huecos, bumpiness]

    python visualizar.py --seed 42 --fps 12
        -> semilla fija y velocidad de caida (pasos por segundo)

Controles durante la partida:
    ESPACIO   pausar / reanudar
    FLECHA ARRIBA / ABAJO   subir / bajar velocidad
    R         reiniciar la partida (misma semilla)
    ESC / cerrar ventana   salir
"""

import argparse
import sys

import pygame

import tetris

CELDA = 30
MARGEN = 20
PANEL_ANCHO = 220

ANCHO_VENTANA = tetris.ANCHO * CELDA + MARGEN * 2 + PANEL_ANCHO
ALTO_VENTANA = tetris.ALTO * CELDA + MARGEN * 2

COLOR_FONDO = (18, 18, 24)
COLOR_GRILLA = (45, 45, 55)
COLOR_TEXTO = (230, 230, 230)
COLOR_BLOQUE_FIJO = (90, 90, 220)

COLORES_PIEZA = {
    "I": (60, 200, 220),
    "O": (230, 210, 60),
    "T": (170, 80, 220),
    "S": (80, 210, 100),
    "Z": (220, 70, 70),
    "J": (70, 100, 220),
    "L": (230, 150, 60),
}


def cargar_pesos(archivo="mejor_pesos.txt"):
    """Lee el mejor individuo guardado por agent.py, si existe."""
    try:
        with open(archivo) as f:
            f.readline()  # fitness:<n>
            pesos = [float(p) for p in f.readline().strip().split(",")]
            if len(pesos) == 4:
                return pesos
    except (FileNotFoundError, ValueError, IndexError):
        pass
    # pesos de respaldo por si no hay archivo entrenado todavia
    return [-0.51, 0.76, -0.36, -0.18]


def celda_a_pixel(fila, col):
    x = MARGEN + col * CELDA
    y = MARGEN + fila * CELDA
    return x, y


def dibujar_tablero(screen, tablero, celdas_pieza=None, color_pieza=None):
    for f in range(tetris.ALTO):
        for c in range(tetris.ANCHO):
            x, y = celda_a_pixel(f, c)
            rect = pygame.Rect(x, y, CELDA - 1, CELDA - 1)
            if tablero[f][c]:
                pygame.draw.rect(screen, COLOR_BLOQUE_FIJO, rect)
            else:
                pygame.draw.rect(screen, COLOR_GRILLA, rect, 1)

    if celdas_pieza:
        for f, c in celdas_pieza:
            if f < 0:
                continue
            x, y = celda_a_pixel(f, c)
            rect = pygame.Rect(x, y, CELDA - 1, CELDA - 1)
            pygame.draw.rect(screen, color_pieza, rect)


def dibujar_panel(screen, fuente, fuente_chica, pesos, piezas, lineas, fps_pasos, pausado):
    x0 = MARGEN * 2 + tetris.ANCHO * CELDA
    y = MARGEN

    def linea(texto, salto=28, chica=False):
        nonlocal y
        f = fuente_chica if chica else fuente
        surf = f.render(texto, True, COLOR_TEXTO)
        screen.blit(surf, (x0, y))
        y += salto

    linea("Agente genetico", 36)
    linea(f"Piezas: {piezas}")
    linea(f"Lineas: {lineas}", 40)

    linea("Pesos:", 24, chica=True)
    nombres = ["altura", "lineas", "huecos", "bumpiness"]
    for nombre, p in zip(nombres, pesos):
        linea(f"  {nombre}: {round(p, 3)}", 22, chica=True)

    y += 16
    linea(f"Velocidad: {fps_pasos} pasos/s", 24, chica=True)
    if pausado:
        linea("(PAUSADO)", 24, chica=True)

    y += 16
    linea("ESPACIO pausa", 20, chica=True)
    linea("UP/DOWN velocidad", 20, chica=True)
    linea("R reinicia, ESC sale", 20, chica=True)


def animar_caida(screen, reloj, fuente, fuente_chica, juego, jugada, pesos, fps_pasos, estado):
    """Anima la pieza actual cayendo desde arriba hasta su posicion
    final (la calculada por jugada), celda por celda."""
    pieza = juego.pieza_actual
    forma = tetris.PIEZAS[pieza][jugada["rotacion"]]
    desplaz = jugada["desplaz"]
    celdas = [(f, c + desplaz) for f, c in forma]

    caida = 0
    while juego._cabe([(f + caida + 1, c) for f, c in celdas], juego.tablero):
        caida += 1

    color = COLORES_PIEZA[pieza]

    for paso in range(caida + 1):
        for evento in pygame.event.get():
            manejar_evento(evento, estado)
        while estado["pausado"]:
            for evento in pygame.event.get():
                manejar_evento(evento, estado)
            reloj.tick(30)

        celdas_paso = [(f + paso, c) for f, c in celdas]
        screen.fill(COLOR_FONDO)
        dibujar_tablero(screen, juego.tablero, celdas_paso, color)
        dibujar_panel(screen, fuente, fuente_chica, pesos, juego.piezas_colocadas,
                      juego.lineas, estado["fps_pasos"], estado["pausado"])
        pygame.display.flip()
        reloj.tick(max(1, estado["fps_pasos"]))


def manejar_evento(evento, estado):
    if evento.type == pygame.QUIT:
        estado["salir"] = True
    elif evento.type == pygame.KEYDOWN:
        if evento.key == pygame.K_ESCAPE:
            estado["salir"] = True
        elif evento.key == pygame.K_SPACE:
            estado["pausado"] = not estado["pausado"]
        elif evento.key == pygame.K_UP:
            estado["fps_pasos"] = min(60, estado["fps_pasos"] + 2)
        elif evento.key == pygame.K_DOWN:
            estado["fps_pasos"] = max(1, estado["fps_pasos"] - 2)
        elif evento.key == pygame.K_r:
            estado["reiniciar"] = True


def jugar_partida(screen, reloj, fuente, fuente_chica, pesos, max_piezas, seed, estado):
    juego = tetris.Tetris(seed=seed)

    while not juego.game_over and juego.piezas_colocadas < max_piezas:
        for evento in pygame.event.get():
            manejar_evento(evento, estado)
        if estado["salir"] or estado["reiniciar"]:
            return

        jugada = tetris.elegir_jugada(juego, pesos)
        if jugada is None:
            break

        animar_caida(screen, reloj, fuente, fuente_chica, juego, jugada, pesos,
                     estado["fps_pasos"], estado)
        if estado["salir"] or estado["reiniciar"]:
            return

        juego.aplicar(jugada)

        screen.fill(COLOR_FONDO)
        dibujar_tablero(screen, juego.tablero)
        dibujar_panel(screen, fuente, fuente_chica, pesos, juego.piezas_colocadas,
                      juego.lineas, estado["fps_pasos"], estado["pausado"])
        pygame.display.flip()

    # pantalla final
    fin = pygame.time.get_ticks() + 5000
    while pygame.time.get_ticks() < fin and not estado["salir"] and not estado["reiniciar"]:
        for evento in pygame.event.get():
            manejar_evento(evento, estado)
        screen.fill(COLOR_FONDO)
        dibujar_tablero(screen, juego.tablero)
        dibujar_panel(screen, fuente, fuente_chica, pesos, juego.piezas_colocadas,
                      juego.lineas, estado["fps_pasos"], estado["pausado"])
        texto = fuente.render("GAME OVER - R reinicia", True, (240, 90, 90))
        screen.blit(texto, (MARGEN, ALTO_VENTANA - 40))
        pygame.display.flip()
        reloj.tick(30)


def main():
    parser = argparse.ArgumentParser(description="Visualiza una partida jugada por el agente.")
    parser.add_argument("pesos", nargs="*", type=float,
                         help="4 pesos [altura, lineas, huecos, bumpiness]. "
                              "Si se omiten, se usa mejor_pesos.txt")
    parser.add_argument("--seed", type=int, default=None, help="semilla del juego")
    parser.add_argument("--max-piezas", type=int, default=500, help="tope de piezas por partida")
    parser.add_argument("--fps", type=int, default=15, help="pasos de caida por segundo")
    args = parser.parse_args()

    if len(args.pesos) == 4:
        pesos = args.pesos
    elif len(args.pesos) == 0:
        pesos = cargar_pesos()
    else:
        print("Error: dame 0 o 4 pesos.", file=sys.stderr)
        sys.exit(1)

    pygame.init()
    pygame.display.set_caption("Tetris GA - mejor partida")
    screen = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont("consolas", 20)
    fuente_chica = pygame.font.SysFont("consolas", 16)

    estado = {"salir": False, "pausado": False, "reiniciar": False, "fps_pasos": args.fps}
    seed = args.seed

    while not estado["salir"]:
        estado["reiniciar"] = False
        jugar_partida(screen, reloj, fuente, fuente_chica, pesos, args.max_piezas, seed, estado)

    pygame.quit()


if __name__ == "__main__":
    main()
