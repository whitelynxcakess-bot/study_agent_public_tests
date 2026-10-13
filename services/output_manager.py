from pathlib import Path
from services.question_parser import rotulo_questao
from config import PASTA_SAIDA

def listar_blocos(blocos: list[dict]) -> None:
    print("\nBLOCOS DE CONTEÚDO")

    for b in blocos:
        numeros = [
            rotulo_questao(q)
            for q in b["questoes"]
        ]

        print(
            f"  [{b['id']:>2}] págs {b['ini']}-{b['fim']} | "
            f"{b['n_paginas']} pág. de conteúdo | "
            f"{len(b['questoes'])} questões ligadas"
        )

        print(
            "      Questões: "
            + (", ".join(numeros) if numeros else "nenhuma")
        )

def escolher_blocos(blocos: list[dict]) -> list[int] | None:
    total = len(blocos)
    while True:
        r = input(
            "\nQual(is) bloco(s)? (ex: 2 | 1,3 | 2-4 | todos | "
            "q 2 = ver questões do bloco 2 | sair): "
        ).strip().lower()

        if r in ("sair", "s"):
            return None
        if r in ("todos", "t"):
            return list(range(1, total + 1))
        if r.startswith("q "):
            try:
                b = blocos[int(r[2:]) - 1]
                print("\n" + ("\n\n".join(b["questoes"]) or "(nenhuma questão ligada a este bloco)"))
            except (ValueError, IndexError):
                print("Bloco inválido.")
            continue
        try:
            ids = set()
            for parte in r.split(","):
                parte = parte.strip()
                if "-" in parte:
                    a, b = map(int, parte.split("-"))
                    ids.update(range(a, b + 1))
                else:
                    ids.add(int(parte))
            validos = sorted(i for i in ids if 1 <= i <= total)
            if validos:
                return validos
        except ValueError:
            pass
        print("Entrada inválida.")

def salvar(bloco: dict, nome_pdf: str, texto: str) -> Path:
    PASTA_SAIDA.mkdir(exist_ok=True)
    destino = PASTA_SAIDA / f"{nome_pdf}_bloco{bloco['id']:02d}_pags{bloco['ini']}-{bloco['fim']}.txt"
    destino.write_text(texto, encoding="utf-8")
    return destino