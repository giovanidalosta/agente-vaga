"""Validação da descrição de vaga gerada."""
from __future__ import annotations

import re

from vaga.modelo import secoes_do_modelo

# Tags usadas nos títulos das vagas da Ikatec, ex.: "Analista JR [PRESENCIAL]".
_TAGS_TITULO = r"PRESENCIAL|H[IÍ]BRIDO|REMOTO|HOME OFFICE|BANCO DE TALENTOS"

PLACEHOLDERS: list[re.Pattern] = [
    # colchete que não é link Markdown nem tag de título
    re.compile(r"\[(?!(?:" + _TAGS_TITULO + r")\])[^\]\n]{1,60}\](?!\()", re.IGNORECASE),
    re.compile(r"_{3,}"),  # lacuna do modelo ("um(a) __________")
    re.compile(r"\{[^}\n]{1,60}\}"),
    re.compile(r"\bTODO\b"),  # case-sensitive: "todo" é palavra comum em português
    re.compile(r"\bXXX\b"),
]


def _ci(padrao: str) -> re.Pattern:
    return re.compile(padrao, re.IGNORECASE)


# Sempre discriminatórios, em qualquer contexto.
TERMOS_PROIBIDOS: list[re.Pattern] = [
    _ci(p)
    for p in (
        r"boa apar[êe]ncia",
        r"\bsexo\s*:?\s*(masculino|feminino)\b",
        r"\b(apenas|somente|preferencialmente) (homens|mulheres)\b",
        r"\bidade\s*:?\s*(entre|m[áa]xima|m[íi]nima|at[ée]|de \d)",
        r"\bfaixa et[áa]ria\b",
        r"\blimite de idade\b",
        r"\bsolteir[oa]s?(\(a\))?",
        r"\bcasad[oa]s?\b",
        r"\bsem filhos\b",
    )
]

# Discriminatórios, exceto em declarações de diversidade
# ("não fazemos distinção de religião ou estado civil" é legítimo).
CONTEXTO_DIVERSIDADE = _ci(
    r"diversidade|distin[çc][ãa]o|discrimin|seja qual for|independente(mente)?|inclus|respeit|qualquer"
)
TERMOS_FORA_DE_DIVERSIDADE: list[re.Pattern] = [
    _ci(r"\b(religi[ãa]o|crist[ãa](o|os|s)?|evang[ée]lic[oa]s?|cat[óo]lic[oa]s?)\b"),
    _ci(r"\bestado civil\b"),
]

# "até NN anos" é limite de idade, exceto quando fala de dependentes/filhos ou da empresa.
LIMITE_ANOS = _ci(r"\bat[ée] \d{2} anos\b")
CONTEXTO_NAO_CANDIDATO = _ci(r"dependente|filh|empresa|mercado|hist[óo]ria|experi[êe]ncia")


def _verificar_secoes(descricao: str, secoes: list[str], opcionais: set[str]) -> list[str]:
    presentes = secoes_do_modelo(descricao)
    ausentes = [s for s in secoes if s not in presentes and s not in opcionais]
    if ausentes:
        return [f"seção ausente: '{s}'" for s in ausentes]
    # remove repetições mantendo a primeira ocorrência
    ordem = list(dict.fromkeys(s for s in presentes if s in secoes))
    esperada = [s for s in secoes if s in ordem]
    return [] if ordem == esperada else ["seções fora da ordem do modelo"]


def _termos_discriminatorios(descricao: str) -> list[str]:
    achados: list[str] = []
    for linha in descricao.splitlines():
        padroes = list(TERMOS_PROIBIDOS)
        if not CONTEXTO_DIVERSIDADE.search(linha):
            padroes += TERMOS_FORA_DE_DIVERSIDADE
        if not CONTEXTO_NAO_CANDIDATO.search(linha):
            padroes.append(LIMITE_ANOS)
        achados += [m.group(0) for padrao in padroes for m in padrao.finditer(linha)]
    return [f"termo discriminatório: '{t}'" for t in achados]


def validar_descricao(descricao: str, secoes: list[str], termos_obrigatorios: list[str] = [],
                      opcionais: set[str] = frozenset()) -> list[str]:
    """Lista de erros da descrição (vazia se válida). Seções em `opcionais` podem faltar."""
    erros = _verificar_secoes(descricao, secoes, set(opcionais))
    texto_min = descricao.casefold()
    erros += [f"termo obrigatório ausente: '{t}'" for t in termos_obrigatorios if t.casefold() not in texto_min]
    erros += [f"placeholder não preenchido: '{m.group(0)}'"
              for padrao in PLACEHOLDERS for m in padrao.finditer(descricao)]
    erros += _termos_discriminatorios(descricao)
    return erros
