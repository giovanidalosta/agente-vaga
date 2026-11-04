"""Validação da descrição de vaga gerada."""
from __future__ import annotations

import re

from vaga.modelo import secoes_do_modelo

PLACEHOLDERS: list[re.Pattern] = [
    re.compile(r"\[[^\]\n]{1,60}\](?!\()"),  # colchete que não é link Markdown
    re.compile(r"\{[^}\n]{1,60}\}"),
    re.compile(r"\bTODO\b"),  # case-sensitive: "todo" é palavra comum em português
    re.compile(r"\bXXX\b"),
]

TERMOS_PROIBIDOS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"boa apar[êe]ncia",
        r"\bsexo (masculino|feminino)\b",
        r"\b(apenas|somente) (homens|mulheres)\b",
        r"\bidade (entre|m[áa]xima|m[íi]nima|at[ée])\b",
        r"\bat[ée] \d{2} anos\b",
        r"\bsolteir[oa](\(a\))?",
        r"\bsem filhos\b",
    )
]

# Termos religiosos só contam fora de declarações de diversidade
# ("contratamos sem distinção de religião" é legítimo).
TERMOS_RELIGIOSOS = re.compile(r"\b(religi[ãa]o|crist[ãa]o|evang[ée]lic[oa])\b", re.IGNORECASE)
CONTEXTO_DIVERSIDADE = re.compile(
    r"diversidade|sem distin[çc][ãa]o|sem discrimina[çc][ãa]o|independente(mente)?|inclus", re.IGNORECASE
)


def _verificar_secoes(descricao: str, secoes: list[str]) -> list[str]:
    presentes = secoes_do_modelo(descricao)
    ausentes = [s for s in secoes if s not in presentes]
    if ausentes:
        return [f"seção ausente: '{s}'" for s in ausentes]
    ordem = [s for s in presentes if s in secoes]
    # remove repetições mantendo a primeira ocorrência
    ordem = list(dict.fromkeys(ordem))
    return [] if ordem == secoes else ["seções fora da ordem do modelo"]


def _termos_discriminatorios(descricao: str) -> list[str]:
    erros = [f"termo discriminatório: '{m.group(0)}'"
             for padrao in TERMOS_PROIBIDOS for m in padrao.finditer(descricao)]
    for linha in descricao.splitlines():
        if CONTEXTO_DIVERSIDADE.search(linha):
            continue
        erros += [f"termo discriminatório: '{m.group(0)}'" for m in TERMOS_RELIGIOSOS.finditer(linha)]
    return erros


def validar_descricao(descricao: str, secoes: list[str], termos_obrigatorios: list[str] = []) -> list[str]:
    """Lista de erros da descrição (vazia se válida)."""
    erros = _verificar_secoes(descricao, secoes)
    texto_min = descricao.casefold()
    erros += [f"termo obrigatório ausente: '{t}'" for t in termos_obrigatorios if t.casefold() not in texto_min]
    erros += [f"placeholder não preenchido: '{m.group(0)}'"
              for padrao in PLACEHOLDERS for m in padrao.finditer(descricao)]
    erros += _termos_discriminatorios(descricao)
    return erros
