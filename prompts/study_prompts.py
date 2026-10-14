# ------------------------------- Prompt do Modelo --------------------------------
SYSTEM = (
    "Você é um assistente de estudos para concursos públicos. "
    "Use SOMENTE o material fornecido; nunca invente nem complete com conhecimento externo. "
    "Preserve literalmente artigos, números, prazos e mnemônicos. "
    "Responda em português, com tópicos curtos, mas com conteúdo suficiente escrito"
    "o essencial para compreensão completa a respeito do tema para resolução das questões com maestria."
)

def prompt_essencial(conteudo: str, questoes: str) -> str:
    if questoes:
        return (
            "Abaixo estão um trecho de CONTEÚDO de estudo e QUESTÕES relacionadas a ele.\n"
            "Extraia SOMENTE o essencial do conteúdo necessário para responder a essas "
            "questões com precisão: conceitos, definições, regras, exceções, prazos, "
            "números e fundamentos citados, todos os Mnemonicos e dicas explíticas encontradas no conteúdo devem aparecer no resumo. Organize por tópico, em português, com "
            "tópicos curtos mas com o essencial de cada conteúdo (relativo ao trecho de páginas associadas). Não responda as questões, não invente nada.\n\n"
            f"QUESTÕES:\n{questoes}\n\nCONTEÚDO:\n{conteudo}"
        )
    return (
        "Extraia o essencial do CONTEÚDO abaixo: conceitos, definições, regras, "
        "exceções, prazos e números, todos os Mnemonicos e dicas explíticas encontradas no conteúdo devem aparecer no resumo. Organize por tópico, em português, com tópicos "
        "curtos. Não invente nada.\n\n"
        f"CONTEÚDO:\n{conteudo}"
    )