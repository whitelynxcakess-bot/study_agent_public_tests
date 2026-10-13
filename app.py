import argparse
from pathlib import Path

from services.pdf_reader import (
    extrair_paginas,
    separar_conteudo_e_questoes,
)
from services.question_parser import separar_questoes
from services.block_builder import montar_blocos
from services.question_matcher import atribuir_questoes
from services.summarizer import resumir_bloco
from services.output_manager import (
    listar_blocos,
    escolher_blocos,
    salvar,
)
from config import PAGINAS_POR_BLOCO_PADRAO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?")
    parser.add_argument("--paginas-por-bloco", type=int)
    args = parser.parse_args()

    entrada = args.pdf or input("Caminho do PDF: ")
    caminho = Path(entrada.strip().strip('"').strip("'"))

    if not caminho.is_file() or caminho.suffix.lower() != ".pdf":
        raise FileNotFoundError(
            f"PDF não encontrado: {caminho.resolve()}"
        )

    tamanho = args.paginas_por_bloco

    if tamanho is None:
        resposta = input(
            f"Páginas de conteúdo por bloco "
            f"[{PAGINAS_POR_BLOCO_PADRAO}]: "
        ).strip()

        tamanho = (
            int(resposta)
            if resposta.isdigit() and int(resposta) > 0
            else PAGINAS_POR_BLOCO_PADRAO
        )

    # 1. Extrair o texto
    paginas = extrair_paginas(caminho)

    if not any(paginas):
        raise ValueError(
            "Nenhum texto extraído. O PDF pode precisar de OCR."
        )

    # 2. Separar conteúdo e páginas de questões
    pags_conteudo, pags_questao = (
        separar_conteudo_e_questoes(paginas)
    )

    if not pags_conteudo:
        raise ValueError("Nenhuma página de conteúdo identificada.")

    # 3. Construir os blocos de conteúdo
    blocos = montar_blocos(pags_conteudo, tamanho)

    # 4. Separar as questões e associá-las aos blocos
    questoes = separar_questoes(pags_questao)
    sem_bloco = atribuir_questoes(blocos, questoes)

    print(
        f"\n{len(paginas)} páginas | "
        f"{len(pags_conteudo)} páginas de conteúdo | "
        f"{len(questoes)} questões identificadas"
    )
    print(
        f"Questões associadas: {len(questoes) - len(sem_bloco)}"
    )
    print(f"Questões sem associação: {len(sem_bloco)}")

    # 5. Escolher blocos e gerar resumos
    while True:
        listar_blocos(blocos)
        escolha = escolher_blocos(blocos)

        if escolha is None:
            break

        for indice in escolha:
            bloco = blocos[indice - 1]

            print(
                f"\nResumindo bloco {indice} "
                f"(páginas {bloco['ini']}-{bloco['fim']})..."
            )

            try:
                resumo = resumir_bloco(bloco)
            except Exception as erro:
                print(f"Falhou: {erro}")
                continue

            print("\n" + resumo + "\n")
            destino = salvar(bloco, caminho.stem, resumo)
            print(f"Salvo em: {destino.resolve()}")


if __name__ == "__main__":
    main()
