import tetris
import random

def inicializar(n):
    individuos = [] * n

    for i in individuos:
        i.append([random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)], 0)

    return individuos

def evaluar(individuos):
    for i in individuos:
        i[1] = tetris.jugar(i[0], random.randint())
        print(i)


def main():
    n = 100
    individuos = inicializar(n)
    evaluar(individuos)