import tetris
import random

def inicializar(n):
    individuos = []

    for i in range(n):
        individuos.append([[random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)], 0])
        
    return individuos

def evaluar(individuos):
    for i in individuos:
        i[1] = tetris.jugar(i[0], 10000, random.randint(1,1000))
        print(i)

    individuos.sort(key = lambda x:x[1])

def main():
    n = 100
    individuos = inicializar(n)
    evaluar(individuos)
    

main()