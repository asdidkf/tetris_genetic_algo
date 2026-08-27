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
        #print(i)

    individuos.sort(key = lambda x:x[1])
    return(seleccionar(individuos))

def seleccionar(individuos):
    for _ in range(len(individuos)-10):
        individuos.pop(0)

    for i in individuos:
        #print(i)
        i[1] = 0
        
    return(reproduccion(individuos))
    

    #for i in range(len(individuos)):
        #print(individuos[i])  

def reproduccion(individuos):
    for _ in range(90):
        random = random.rantint(1,40)
        match random:
            case 1:
                individuos.append([random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3], 0])
            case 2:
                individuos.append([individuos[random.randint(0,9)][0][0], 
                                   random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3], 0])
            case 3:
                individuos.append([individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][3], 0])
            case 4:
                individuos.append([individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   random.uniform(-1,1), 0])
            case _:
                individuos.append([individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3], 0])

    return individuos


def main():
    n = 100
    individuos = inicializar(n)

    iter = 5
    for i in range(iter):
        evaluar(individuos)
        print(individuos)
    

main()