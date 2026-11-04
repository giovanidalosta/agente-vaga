"""Schema e validação dos campos de entrada de uma vaga."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

SENIORIDADES: tuple[str, ...] = ("Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Liderança")
MODELOS_TRABALHO: tuple[str, ...] = ("Presencial", "Híbrido", "Remoto")
TIPOS_CONTRATACAO: tuple[str, ...] = ("CLT", "PJ", "Estágio")


@dataclass
class Vaga:
    cargo: str
    senioridade: str
    modelo_trabalho: str
    local: str
    tipo_contratacao: str
    responsabilidades: list[str]
    requisitos: list[str]
    diferenciais: list[str] = field(default_factory=list)
    beneficios: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    faixa_salarial: str = ""


def _chave(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.casefold().strip()


def _texto(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _lista(valor) -> list[str]:
    if isinstance(valor, str):
        valor = [valor]
    if not isinstance(valor, (list, tuple)):
        return []
    return [item.strip() for item in valor if isinstance(item, str) and item.strip()]


def _enum(nome: str, valor, opcoes: tuple[str, ...], erros: list[str]) -> str:
    texto = _texto(valor)
    if not texto:
        erros.append(f"{nome} é obrigatório")
        return ""
    for opcao in opcoes:
        if _chave(opcao) == _chave(texto):
            return opcao
    erros.append(f"{nome} inválida: '{texto}'. Use: {', '.join(opcoes)}"
                 if nome == "senioridade" else
                 f"{nome} inválido: '{texto}'. Use: {', '.join(opcoes)}")
    return ""


def validar_entrada(dados: dict) -> tuple[Vaga | None, list[str]]:
    """Valida e normaliza os campos da vaga. Devolve (Vaga, []) ou (None, erros)."""
    erros: list[str] = []

    cargo = _texto(dados.get("cargo"))
    if not cargo:
        erros.append("cargo é obrigatório")
    senioridade = _enum("senioridade", dados.get("senioridade"), SENIORIDADES, erros)
    modelo = _enum("modelo_trabalho", dados.get("modelo_trabalho"), MODELOS_TRABALHO, erros)
    local = _texto(dados.get("local"))
    if modelo and modelo != "Remoto" and not local:
        erros.append("local é obrigatório quando o modelo de trabalho não é Remoto")
    contratacao = _enum("tipo_contratacao", dados.get("tipo_contratacao"), TIPOS_CONTRATACAO, erros)

    responsabilidades = _lista(dados.get("responsabilidades"))
    if not responsabilidades:
        erros.append("responsabilidades precisa de ao menos 1 item")
    requisitos = _lista(dados.get("requisitos"))
    if not requisitos:
        erros.append("requisitos precisa de ao menos 1 item")

    if erros:
        return None, erros
    return Vaga(
        cargo=cargo,
        senioridade=senioridade,
        modelo_trabalho=modelo,
        local=local,
        tipo_contratacao=contratacao,
        responsabilidades=responsabilidades,
        requisitos=requisitos,
        diferenciais=_lista(dados.get("diferenciais")),
        beneficios=_lista(dados.get("beneficios")),
        soft_skills=_lista(dados.get("soft_skills")),
        faixa_salarial=_texto(dados.get("faixa_salarial")),
    ), []
