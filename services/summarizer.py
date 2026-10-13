from config import MAX_CHARS_CONTEUDO, MAX_CHARS_QUESTOES
from services.llm_client import chamar_modelo
from prompts.study_prompts import SYSTEM, prompt_essencial

def agrupar(trechos: list[str], limite: int) -> list[str]:
    """Junta trechos inteiros em grupos de até `limite` caracteres, sem cortar nenhum."""
    grupos, atual, tam = [], [], 0
    for t in trechos:
        if atual and tam + len(t) > limite:
            grupos.append("\n\n".join(atual))
            atual, tam = [], 0
        atual.append(t)
        tam += len(t)
    if atual:
        grupos.append("\n\n".join(atual))
    return grupos


def resumir_bloco(bloco: dict) -> str:
    grupos_c = agrupar(bloco["trechos"], MAX_CHARS_CONTEUDO)
    grupos_q = agrupar(bloco["questoes"], MAX_CHARS_QUESTOES) or [""]

    total = len(grupos_c) * len(grupos_q)
    if total > 1:
        print(f"  Material grande: {total} chamadas ao modelo + consolidação.")

    parciais = []
    for gq in grupos_q:
        for gc in grupos_c:
            if total > 1:
                print(f"  Resumindo parte {len(parciais) + 1}/{total}...")
            parciais.append(chamar_modelo(SYSTEM, prompt_essencial(gc, gq)))

    if len(parciais) == 1:
        return parciais[0]

    print("  Consolidando partes...")
    return chamar_modelo(
        SYSTEM,
        "Junte os resumos parciais abaixo em um único resumo do essencial, "
        "removendo repetições e mantendo a organização por tópico. Não invente nada.\n\n"
        + "\n\n---\n\n".join(parciais),
    )
