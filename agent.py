import tetris
import random
import visualization

def inicializar(n):
    individuos = []

    for i in range(n):
        individuos.append([[random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)], 0])
        
    return individuos

def evaluar(individuos, generation):
    for i in individuos:
        i[1] = tetris.jugar(i[0], 1000, random.randint(1,1000))
        #print(i)

    individuos.sort(key = lambda x:x[1])

    visualization.registrar(generation, individuos)

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
        random_value = random.randint(1,40)
        match random_value:
            case 1:
                individuos.append([[random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3]], 0])
            case 2:
                individuos.append([[individuos[random.randint(0,9)][0][0], 
                                   random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3]], 0])
            case 3:
                individuos.append([[individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   random.uniform(-1,1), 
                                   individuos[random.randint(0,9)][0][3]], 0])
            case 4:
                individuos.append([[individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   random.uniform(-1,1)], 0])
            case _:
                individuos.append([[individuos[random.randint(0,9)][0][0], 
                                   individuos[random.randint(0,9)][0][1], 
                                   individuos[random.randint(0,9)][0][2], 
                                   individuos[random.randint(0,9)][0][3]], 0])

    return individuos


def main():
    n = 100
    individuos = inicializar(n)

    iteraciones = 10
    for gen in range(1, iteraciones + 1):
        individuos = evaluar(individuos, gen)

        
main()