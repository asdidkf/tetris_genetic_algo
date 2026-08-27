"""
Modulo separado para llevar el registro y mostrar en consola la
evolucion de un algoritmo genetico generacion a generacion.

Uso en tu agent.py (solo 1 linea nueva, ya no hace falta graficar al final):

    import visualizacion

    def evaluar(individuos, generacion):
        for i in individuos:
            i[1] = tetris.jugar(i[0], 10000, random.randint(1,1000))

        individuos.sort(key=lambda x: x[1])

        visualizacion.registrar(generacion, individuos)   # <-- nueva linea

        return seleccionar(individuos)
"""


def registrar(generacion, individuos, top=5):
    """Imprime en consola el resumen de esta generacion: maximo,
    promedio, minimo de lineas completadas, y los `top` mejores
    individuos con sus pesos. Llamalo despues de evaluar y ordenar a
    los individuos de forma ascendente (individuos[-1] = mejor)."""
    fitnesses = [i[1] for i in individuos]

    maximo = max(fitnesses)
    minimo = min(fitnesses)
    promedio = sum(fitnesses) / len(fitnesses)

    print(f"\n=== Generacion {generacion} ===")
    print(f"Maximo:   {maximo}")
    print(f"Promedio: {promedio:.2f}")
    print(f"Minimo:   {minimo}")

    print(f"Top {top} individuos:")
    # individuos esta ordenado ascendente, asi que los mejores estan al final
    mejores = individuos[-top:][::-1]
    for lugar, (pesos, fitness) in enumerate(mejores, start=1):
        pesos_fmt = [round(p, 3) for p in pesos]
        print(f"  {lugar}. lineas={fitness}  pesos={pesos_fmt}")