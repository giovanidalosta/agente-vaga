"""Base de vagas da Ikatec para sugerir responsabilidades, requisitos e soft skills.

Hierarquia: para o mesmo cargo, a vaga mais recente é a fonte principal, porque cada vaga
nova é aberta com as informações mais atualizadas do cargo. Prefere-se o mesmo nível de
senioridade; seções que faltarem são completadas pela vaga seguinte na mesma ordem.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from vaga.schema import SENIORIDADES, _chave

PASTAS_PADRAO = (".claude/skills/vaga/referencias/historico", ".claude/skills/vaga/referencias/exemplos")
SECOES_SUGERIDAS = ("Responsabilidades", "Requisitos", "Diferenciais", "Soft Skills")
SECOES_COMPLETAVEIS = {"Responsabilidades", "Requisitos", "Soft Skills"}  # obrigatórias no modelo
LIMIAR = 0.8  # similaridade mínima entre o cargo pedido e o título da vaga

_TOKENS_NIVEL = {"jr", "junior", "pl", "pleno", "sr", "senior", "nivel", "i", "ii", "iii"}
_NIVEL_TITULO = [
    (re.compile(r"\b(jr|junior)\b"), "Júnior"),
    (re.compile(r"\b(pl|pleno)\b"), "Pleno"),
    (re.compile(r"\b(sr|senior)\b"), "Sênior"),
    (re.compile(r"\bestagi"), "Estágio"),
    (re.compile(r"\bespecialista\b"), "Especialista"),
]


@dataclass
class VagaRef:
    id: str
    titulo: str
    criada: str
    link: str
    senioridade: str | None
    secoes: dict[str, list[str]] = field(default_factory=dict)

    def origem(self) -> dict:
        return {"id": self.id, "criada": self.criada, "titulo": self.titulo,
                "link": self.link, "senioridade": self.senioridade}


def normalizar_cargo(titulo: str) -> str:
    """'Analista de Suporte Técnico - JR [PRESENCIAL]' → 'analista de suporte tecnico'."""
    texto = re.sub(r"\[[^\]]*\]", " ", _chave(titulo))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return " ".join(t for t in texto.split() if t not in _TOKENS_NIVEL)


def _senioridade(texto: str | None) -> str | None:
    if not texto:
        return None
    for opcao in SENIORIDADES:
        if _chave(opcao) == _chave(texto):
            return opcao
    return None


def _senioridade_do_titulo(titulo: str) -> str | None:
    chave = re.sub(r"\[[^\]]*\]", " ", _chave(titulo))
    for padrao, nivel in _NIVEL_TITULO:
        if padrao.search(chave):
            return nivel
    return None


def _ler(arquivo: Path) -> VagaRef | None:
    texto = arquivo.read_text(encoding="utf-8-sig")
    titulo = next((l[2:].strip() for l in texto.splitlines() if l.startswith("# ")), "")
    cab = re.search(r"^> Vaga publicada: (\S+?/vaga/(\d+))(?: · criada em (\d{4}-\d{2}-\d{2}))?", texto, re.M)
    if not titulo or not cab:
        return None
    ficha = re.search(r"^- Senioridade: (.+)$", texto, re.M)
    senioridade = _senioridade(ficha.group(1).split(" / ")[0]) if ficha else None

    secoes: dict[str, list[str]] = {}
    atual = None
    for linha in texto.split("\n---\n", 1)[-1].splitlines():
        if linha.startswith("## "):
            atual = linha[3:].strip()
        elif atual and linha.startswith("- "):
            secoes.setdefault(atual, []).append(linha[2:].strip())
    return VagaRef(id=cab.group(2), titulo=titulo, criada=cab.group(3) or "", link=cab.group(1),
                   senioridade=senioridade or _senioridade_do_titulo(titulo), secoes=secoes)


def carregar_vagas(pastas) -> list[VagaRef]:
    """Lê os arquivos de vaga (formato dos exemplos) das pastas; a mesma vaga em duas pastas conta uma vez."""
    vagas: dict[str, VagaRef] = {}
    for pasta in pastas:
        for arquivo in sorted(Path(pasta).glob("*.md")):
            if (v := _ler(arquivo)) and v.id not in vagas:
                vagas[v.id] = v
    return list(vagas.values())


def _similaridade(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if ta and tb and (ta <= tb or tb <= ta):
        return 0.9 + 0.1 * SequenceMatcher(None, a, b).ratio()
    return SequenceMatcher(None, a, b).ratio()


def sugerir(cargo: str, senioridade: str | None, vagas: list[VagaRef]) -> dict:
    alvo = normalizar_cargo(cargo)
    nivel = _senioridade(senioridade)
    pontuadas = sorted(((_similaridade(alvo, normalizar_cargo(v.titulo)), v) for v in vagas),
                       key=lambda p: p[0], reverse=True)
    if not pontuadas or pontuadas[0][0] < LIMIAR:
        vistos: list[str] = []
        for _, v in pontuadas:
            if v.titulo not in vistos:
                vistos.append(v.titulo)
        return {"encontrado": False, "cargo": cargo, "parecidos": vistos[:3]}

    melhor = pontuadas[0][0]
    grupo = sorted((v for s, v in pontuadas if s >= melhor - 0.02), key=lambda v: v.criada, reverse=True)
    mesmo_nivel = [v for v in grupo if nivel and v.senioridade == nivel]
    ordem = mesmo_nivel + [v for v in grupo if v not in mesmo_nivel]

    principal = ordem[0]
    secoes = {}
    for nome in SECOES_SUGERIDAS:
        # Seções opcionais vêm só da vaga principal: se a mais recente tirou os diferenciais, foi de propósito.
        candidatas = ordem if nome in SECOES_COMPLETAVEIS else [principal]
        fonte = next((v for v in candidatas if v.secoes.get(nome)), None)
        if fonte:
            secoes[nome] = {"itens": fonte.secoes[nome], "origem": fonte.origem()}
    return {
        "encontrado": True,
        "cargo": cargo,
        "nivel_diferente": bool(nivel) and not mesmo_nivel,
        "secoes": secoes,
        "outras_vagas": [v.origem() for v in grupo if v is not principal],
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys

    from vaga.validar import _utf8

    _utf8(sys.stdout)
    parser = argparse.ArgumentParser(prog="python -m vaga.base", description="Sugestões a partir das vagas da Ikatec.")
    sub = parser.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("sugerir", help="responsabilidades, requisitos e soft skills da vaga mais recente do cargo")
    p.add_argument("--cargo", required=True)
    p.add_argument("--senioridade")
    p.add_argument("--pastas", nargs="+", default=list(PASTAS_PADRAO))
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0

    resultado = sugerir(args.cargo, args.senioridade, carregar_vagas(args.pastas))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0 if resultado["encontrado"] else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
