"""
Resumidor de PDF de estudos por blocos.

Fluxo:
  1. Você informa o caminho do PDF (argumento ou digitando).
  2. O script extrai o texto página a página e separa o que é CONTEÚDO
     do que é QUESTÃO (heurística por padrões: alternativas a)/b)/c),
     "Gabarito", "Banca:", "Julgue", Certo/Errado etc.).
  3. O PDF é dividido em blocos de X páginas. Cada bloco guarda o seu
     conteúdo e as suas questões.
  4. Você escolhe qual(is) bloco(s) quer. O modelo local (Ollama) gera o
     essencial do conteúdo necessário para responder às questões daquele bloco.

Uso:
    python resumir_pdf_blocos.py caminho/do/arquivo.pdf
    python resumir_pdf_blocos.py caminho/do/arquivo.pdf --paginas-por-bloco 8
"""

import argparse
import re
from pathlib import Path

from ollama import Client
from pypdf import PdfReader

# ----------------------------- Configuração -----------------------------
MODELO = "qwen3.5:2b"
HOST = "http://127.0.0.1:11434"
PAGINAS_POR_BLOCO_PADRAO = 10
NUM_CTX = 16384
NUM_PREDICT = 1500
MAX_CHARS_CONTEUDO = 12000   # acima disso o bloco é resumido em partes
MAX_CHARS_QUESTOES = 6000    # limite de questões enviadas ao modelo
PASTA_SAIDA = Path("./resumos")

client = Client(host=HOST, trust_env=False)

# ------------------- Detecção de conteúdo x questão --------------------
RE_ALTERNATIVA = re.compile(r"^\s*\(?[A-Ea-e][\)\.\-]\s*\S", re.MULTILINE)
RE_MARCADORES = re.compile(
    r"(?i)\b(gabarito|quest[ãa]o\s*\d*|banca\s*:|[óo]rg[ãa]o\s*:|"
    r"ano\s*:\s*\d{4}|julgue|assinale a (alternativa|op[çc][ãa]o)|"
    r"\(\s*\)\s*certo|\(\s*\)\s*errado|certo\s*\(\s*\)|errado\s*\(\s*\))"
)


def eh_pagina_de_questao(texto: str) -> bool:
    alternativas = len(RE_ALTERNATIVA.findall(texto))
    marcadores = len(RE_MARCADORES.findall(texto))
    return (
        alternativas >= 3
        or marcadores >= 3
        or (alternativas >= 2 and marcadores >= 1)
    )


# ------------------------------ PDF e blocos ---------------------------
def extrair_paginas(caminho: Path) -> list[str]:
    reader = PdfReader(caminho)
    return [(p.extract_text() or "").strip() for p in reader.pages]


def montar_blocos(paginas: list[str], tamanho: int) -> list[dict]:
    blocos = []
    for i in range(0, len(paginas), tamanho):
        ini, fim = i + 1, min(i + tamanho, len(paginas))
        conteudo, questoes = [], []
        pags_conteudo, pags_questoes = [], []
        for n in range(ini, fim + 1):
            texto = paginas[n - 1]
            if not texto:
                continue
            trecho = f"[Página {n}]\n{texto}"
            if eh_pagina_de_questao(texto):
                questoes.append(trecho)
                pags_questoes.append(n)
            else:
                conteudo.append(trecho)
                pags_conteudo.append(n)
        blocos.append({
            "id": len(blocos) + 1,
            "ini": ini,
            "fim": fim,
            "conteudo": "\n\n".join(conteudo),
            "questoes": "\n\n".join(questoes),
            "pags_conteudo": pags_conteudo,
            "pags_questoes": pags_questoes,
        })
    return blocos


# ------------------------------- Modelo --------------------------------
def chamar_modelo(system: str, user: str) -> str:
    resposta = client.chat(
        model=MODELO,
        think=False,
        options={"num_ctx": NUM_CTX, "num_predict": NUM_PREDICT, "temperature": 0.2},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    texto = (resposta.message.content or "").strip()
    if not texto:
        raise RuntimeError(
            f"Resposta vazia do modelo (done_reason={resposta.done_reason}, "
            f"prompt_eval_count={resposta.prompt_eval_count})."
        )
    return texto


SYSTEM = (
    "Você é um assistente de estudos para concursos. Resuma de forma fiel ao "
    "material fornecido, sem inventar informações e sem usar conhecimento externo."
)


def dividir_texto(texto: str, limite: int) -> list[str]:
    """Divide em partes de até `limite` caracteres, quebrando em separadores de página."""
    partes, atual = [], ""
    for trecho in texto.split("\n\n[Página "):
        trecho = trecho if trecho.startswith("[Página ") else "[Página " + trecho
        if atual and len(atual) + len(trecho) > limite:
            partes.append(atual)
            atual = ""
        atual += ("\n\n" if atual else "") + trecho
    if atual:
        partes.append(atual)
    return partes


def prompt_essencial(conteudo: str, questoes: str) -> str:
    if questoes:
        return (
            "Abaixo estão o CONTEÚDO de estudo e as QUESTÕES que aparecem junto a ele.\n"
            "Extraia SOMENTE o essencial do conteúdo necessário para responder a essas "
            "questões com precisão: conceitos, definições, regras, exceções, prazos, "
            "números e fundamentos citados. Organize por tópico, em português, com "
            "tópicos curtos. Não responda as questões, não invente nada.\n\n"
            f"QUESTÕES:\n{questoes}\n\nCONTEÚDO:\n{conteudo}"
        )
    return (
        "Extraia o essencial do CONTEÚDO abaixo: conceitos, definições, regras, "
        "exceções, prazos e números. Organize por tópico, em português, com tópicos "
        "curtos. Não invente nada.\n\n"
        f"CONTEÚDO:\n{conteudo}"
    )


def resumir_bloco(bloco: dict) -> str:
    conteudo = bloco["conteudo"]
    questoes = bloco["questoes"]

    if not conteudo:
        return "Este bloco não tem páginas de conteúdo (apenas questões ou páginas sem texto)."

    if len(questoes) > MAX_CHARS_QUESTOES:
        print(f"  Aviso: questões do bloco truncadas em {MAX_CHARS_QUESTOES} caracteres.")
        questoes = questoes[:MAX_CHARS_QUESTOES]

    partes = dividir_texto(conteudo, MAX_CHARS_CONTEUDO)
    if len(partes) == 1:
        return chamar_modelo(SYSTEM, prompt_essencial(partes[0], questoes))

    parciais = []
    for i, parte in enumerate(partes, 1):
        print(f"  Resumindo parte {i}/{len(partes)}...")
        parciais.append(chamar_modelo(SYSTEM, prompt_essencial(parte, questoes)))

    print("  Consolidando partes...")
    return chamar_modelo(
        SYSTEM,
        "Junte os resumos parciais abaixo em um único resumo do essencial, "
        "removendo repetições e mantendo a organização por tópico. Não invente nada.\n\n"
        + "\n\n---\n\n".join(parciais),
    )


# ------------------------------- Interface -----------------------------
def listar_blocos(blocos: list[dict]) -> None:
    print("\nBLOCOS DISPONÍVEIS")
    for b in blocos:
        print(
            f"  [{b['id']:>2}] págs {b['ini']}-{b['fim']} | "
            f"{len(b['pags_conteudo'])} de conteúdo, "
            f"{len(b['pags_questoes'])} de questões"
        )


def escolher_blocos(total: int) -> list[int] | None:
    while True:
        r = input("\nQual(is) bloco(s)? (ex: 2 | 1,3 | 2-4 | todos | sair): ").strip().lower()
        if r in ("sair", "s", "q"):
            return None
        if r in ("todos", "t"):
            return list(range(1, total + 1))
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", nargs="?", help="caminho do PDF")
    ap.add_argument("--paginas-por-bloco", type=int, default=None)
    args = ap.parse_args()

    entrada = args.pdf or input("Caminho do PDF: ")
    caminho = Path(entrada.strip().strip('"').strip("'"))
    if not (caminho.is_file() and caminho.suffix.lower() == ".pdf"):
        raise FileNotFoundError(f"PDF não encontrado: {caminho.resolve()}")

    tamanho = args.paginas_por_bloco
    if tamanho is None:
        r = input(f"Páginas por bloco [{PAGINAS_POR_BLOCO_PADRAO}]: ").strip()
        tamanho = int(r) if r.isdigit() and int(r) > 0 else PAGINAS_POR_BLOCO_PADRAO

    print(f"PDF: {caminho.resolve()}")
    paginas = extrair_paginas(caminho)
    if not any(paginas):
        raise ValueError("Nenhum texto extraído. O PDF pode ser digitalizado (precisa de OCR).")

    blocos = montar_blocos(paginas, tamanho)
    todas_q = [n for b in blocos for n in b["pags_questoes"]]
    print(f"{len(paginas)} páginas | páginas classificadas como questões: {todas_q or 'nenhuma'}")

    while True:
        listar_blocos(blocos)
        escolha = escolher_blocos(len(blocos))
        if escolha is None:
            break
        for i in escolha:
            bloco = blocos[i - 1]
            print(f"\nBloco {i} (págs {bloco['ini']}-{bloco['fim']})...")
            try:
                resumo = resumir_bloco(bloco)
            except Exception as e:
                print(f"  Falhou: {e}")
                continue
            print("\n" + resumo + "\n")
            print(f"Salvo em: {salvar(bloco, caminho.stem, resumo).resolve()}")


if __name__ == "__main__":
    main()