import re
from pypdf import PdfReader
from pathlib import Path

RE_ALTERNATIVA = re.compile(r"^\s*\(?[A-Ea-e][\)\.\-]\s*\S", re.MULTILINE)
RE_MARCADORES = re.compile(
    r"(?i)\b(gabarito|quest[ãa]o\s*\d*|banca\s*:|[óo]rg[ãa]o\s*:|"
    r"ano\s*:\s*\d{4}|julgue|assinale a (alternativa|op[çc][ãa]o)|"
    r"\(\s*\)\s*certo|\(\s*\)\s*errado|certo\s*\(\s*\)|errado\s*\(\s*\))"
)

# ------------------------------ Leitura do PDF -------------------------
def extrair_paginas(caminho: Path) -> list[str]:
    reader = PdfReader(caminho)
    return [(p.extract_text() or "").strip() for p in reader.pages]

def eh_pagina_de_questao(texto: str) -> bool:
    alternativas = len(RE_ALTERNATIVA.findall(texto))
    marcadores = len(RE_MARCADORES.findall(texto))
    return (
        alternativas >= 3
        or marcadores >= 3
        or (alternativas >= 2 and marcadores >= 1)
    )

def separar_conteudo_e_questoes(paginas: list[str]):
    #criar tupla numerando a página e seu conteúdo
    paginas_validas = [
        (n, texto)
        for n, texto in enumerate(paginas, 1)
        if texto
    ]

    #seleciona todas as tuplas de paginas_validas que na função eh_pagina_de_questao() apresentam FALSE
    conteudo = [
        (n, texto)
        for n, texto in paginas_validas
        if not eh_pagina_de_questao(texto)
    ]

    #seleciona todas as tuplas de paginas_validas que na função eh_pagina_de_questao() apresentam TRUE
    questoes = [
        (n, texto)
        for n, texto in paginas_validas
        if eh_pagina_de_questao(texto)
    ]

    return conteudo, questoes