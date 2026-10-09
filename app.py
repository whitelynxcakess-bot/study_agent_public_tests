from ollama import Client

MODELO = "qwen3.5:2b"  # troque pelo nome que aparecer na lista

client = Client(host="http://127.0.0.1:11434", trust_env=False)

resposta = client.chat(
    model=MODELO,
    messages=[
        {"role": "user", "content": "Por que o céu é azul? Responda em 3 frases curtas e simples."}
    ],
)

print(resposta.message.content)