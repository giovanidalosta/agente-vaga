"""Leitura do modelo de vaga da empresa."""
from __future__ import annotations


def secoes_do_modelo(texto: str) -> list[str]:
    """Títulos de nível 2 (`## `) na ordem em que aparecem, ignorando blocos de código."""
    secoes: list[str] = []
    em_codigo = False
    for linha in texto.splitlines():
        if linha.lstrip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if not em_codigo and linha.startswith("## "):
            titulo = linha[3:].strip()
            if titulo:
                secoes.append(titulo)
    return secoes
