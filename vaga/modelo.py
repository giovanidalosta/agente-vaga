"""Leitura do modelo de vaga da empresa."""
from __future__ import annotations

import re

# Seções marcadas como "## Nome (opcional)" no modelo podem faltar na descrição.
_MARCADOR_OPCIONAL = re.compile(r"\s*\(opcional\)\s*$", re.IGNORECASE)


def _titulos(texto: str) -> list[str]:
    titulos: list[str] = []
    em_codigo = False
    for linha in texto.lstrip("﻿").splitlines():
        if linha.lstrip().startswith("```"):
            em_codigo = not em_codigo
            continue
        if not em_codigo and linha.startswith("## "):
            titulo = linha[3:].strip()
            if titulo:
                titulos.append(titulo)
    return titulos


def secoes_do_modelo(texto: str) -> list[str]:
    """Títulos de nível 2 (`## `) na ordem em que aparecem, sem o marcador "(opcional)"."""
    return [_MARCADOR_OPCIONAL.sub("", t) for t in _titulos(texto)]


def secoes_opcionais_do_modelo(texto: str) -> set[str]:
    """Nomes das seções marcadas com "(opcional)" no modelo."""
    return {_MARCADOR_OPCIONAL.sub("", t) for t in _titulos(texto) if _MARCADOR_OPCIONAL.search(t)}
