def montar_blocos(paginas_conteudo: list[tuple[int, str]], tamanho: int) -> list[dict]:
    blocos = []
    for i in range(0, len(paginas_conteudo), tamanho):
        fatia = paginas_conteudo[i:i + tamanho]
        blocos.append({
            "id": len(blocos) + 1,
            "ini": fatia[0][0],
            "fim": fatia[-1][0],
            "n_paginas": len(fatia),
            "trechos": [f"[Página {n}]\n{t}" for n, t in fatia],
            "texto": "\n".join(t for _, t in fatia),
            "questoes": [],
        })
    return blocos