import re
import unicodedata

RE_INICIO_QUESTAO = re.compile(
    r"(?im)^[ \t]*(?:quest[ãa]o[ \t]*\d+|q[ \t]*\d{3,}|\d{1,3}[\)\.\-–][ \t]+\S)"
)

RE_NUMERO_QUESTAO = re.compile(
    r"(?imx)^[ \t]*(?:"
    r"quest[ãa]o[ \t]*(\d+)"
    r"|q[ \t]*(\d{3,})"
    r"|(\d{1,3})[)\.\-–][ \t]+\S"
    r")" 
)

def identificar_numero_questao(texto: str) -> str:
    """Extrai o número original, quando reconhecível."""

    match = RE_NUMERO_QUESTAO.search(texto)

    if not match:
        return "sem número detectado"

    return next(
        grupo for grupo in match.groups()
        if grupo is not None
    )

def separar_questoes(
    paginas_questao: list[tuple[int, str]]
) -> list[str]:
    """Separa questões, preservando o número original e a página do PDF."""

    unidades = []

    for n, texto in paginas_questao:
        pos = [
            m.start()
            for m in RE_INICIO_QUESTAO.finditer(texto)
        ]

        # Sem marcador detectável: preserva a página como uma unidade.
        if not pos:
            numero = identificar_numero_questao(texto)
            unidades.append(
                f"[Questão {numero} | pág. {n}]\n{texto}"
            )
            continue

        # Inclui eventual texto anterior ao primeiro marcador
        # para não perder conteúdo extraído da página.
        cabeca = texto[:pos[0]].strip()
        pos.append(len(texto))

        for i, (a, b) in enumerate(zip(pos, pos[1:])):
            trecho = texto[a:b].strip()

            if i == 0 and cabeca:
                trecho = cabeca + "\n" + trecho

            numero = identificar_numero_questao(trecho)

            unidades.append(
                f"[Questão {numero} | pág. {n}]\n{trecho}"
            )

    return unidades

def rotulo_questao(questao: str) -> str:
    """Recupera o identificador salvo no início da questão."""

    match = re.match(r"^\[Questão ([^\]|]+)", questao)

    if match:
        return match.group(1).strip()

    return "sem número detectado"


STOPWORDS = {
    "para", "como", "mais", "mas", "com", "sem", "uma", "uns", "umas", "que",
    "por", "dos", "das", "nos", "nas", "pela", "pelo", "pelas", "pelos", "ser",
    "sao", "foi", "era", "tem", "tambem", "quando", "onde", "qual", "quais",
    "seu", "sua", "seus", "suas", "este", "esta", "estes", "estas", "esse",
    "essa", "esses", "essas", "isso", "isto", "aquele", "aquela", "ainda",
    "assim", "entre", "sobre", "apos", "ate", "cada", "todo", "toda", "todos",
    "todas", "outro", "outra", "pode", "podem", "deve", "devem", "nao", "sim",
    # ruído típico de enunciados
    "questao", "gabarito", "banca", "orgao", "ano", "julgue", "assinale",
    "alternativa", "alternativas", "opcao", "certo", "errado", "correta",
    "correto", "incorreta", "incorreto", "afirmativa", "afirmativas", "item",
    "itens", "pagina", "texto", "seguir", "abaixo", "acima",
}

def termos(texto: str) -> set[str]:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z]{4,}", t) if w not in STOPWORDS}