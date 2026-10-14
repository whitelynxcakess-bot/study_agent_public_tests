import numpy as np
from ollama import Client
from config import HOST

MODEL_EMBEDDING = "bge-m3:latest"

client = Client(host=HOST, trust_env=False)

def gerar_embedding(texto: str):
    """
    Compatível com Ollama mais novo e mais antigo.
    """

    try:
        resp = client.embed(
            model=MODEL_EMBEDDING,
            input=texto
        )

        return np.array(resp["embeddings"][0])

    except AttributeError:
        resp = client.embeddings(
            model=MODEL_EMBEDDING,
            prompt=texto
        )

        return np.array(resp["embedding"])


def similaridade(v1, v2):
    norma1 = np.linalg.norm(v1)
    norma2 = np.linalg.norm(v2)

    if norma1 == 0 or norma2 == 0:
        return 0

    return float(
        np.dot(v1, v2) / (norma1 * norma2)
    )


def atribuir_questoes(blocos: list[dict], questoes: list[str]):

    if not questoes:
        return []

    if len(blocos) == 1:
        blocos[0]["questoes"] = list(questoes)
        return []

    sem_bloco = []

    print("Gerando embeddings dos blocos...")

    embeddings_blocos = []

    for bloco in blocos:
        emb = gerar_embedding(bloco["texto"])
        embeddings_blocos.append(emb)

    print("Associando questões...")

    for questao in questoes:

        emb_q = gerar_embedding(questao)

        scores = [
            similaridade(emb_q, emb_bloco)
            for emb_bloco in embeddings_blocos
        ]

        melhor_idx = int(np.argmax(scores))
        melhor_score = scores[melhor_idx]

        # ajuste conforme seus testes
        LIMIAR = 0.45

        if melhor_score < LIMIAR:
            sem_bloco.append(questao)
            continue

        blocos[melhor_idx]["questoes"].append(questao)

    return sem_bloco