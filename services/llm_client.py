
from ollama import Client
from config import HOST, MODELO, NUM_CTX, NUM_PREDICT

client = Client(host=HOST, trust_env=False)


def chamar_modelo(system: str, user: str) -> str:
    resposta = client.chat(
        model=MODELO,
        think=False,
        options={
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "temperature": 0.2,
        },
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    texto = (resposta.message.content or "").strip()

    if not texto:
        raise RuntimeError("O modelo retornou uma resposta vazia.")

    return texto
