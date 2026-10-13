import math
from collections import Counter
from services.question_parser import termos

def atribuir_questoes(blocos: list[dict], questoes: list[str]) -> list[str]:
    """Liga cada questão ao bloco com maior afinidade de vocabulário (ponderado
    por raridade do termo entre os blocos). Devolve as questões sem bloco."""
    if not questoes:
        return []
    if len(blocos) == 1:
        blocos[0]["questoes"] = list(questoes)
        return []

    n = len(blocos)
    vocab = [termos(b["texto"]) for b in blocos]
    df = Counter(t for v in vocab for t in v)
    idf = {t: math.log(n / c) for t, c in df.items()}

    sem_bloco = []
    for q in questoes:
        tq = termos(q)
        pontos = [sum(idf[t] for t in tq if t in v) for v in vocab]
        melhor = max(range(n), key=lambda i: pontos[i])
        if pontos[melhor] <= 0:
            sem_bloco.append(q)
        else:
            blocos[melhor]["questoes"].append(q)
    return sem_bloco