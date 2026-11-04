"""Integração de leitura com a página de carreiras da Ikatec na Sólides.

A Sólides expõe as vagas publicadas numa API pública (a mesma usada pelo site
ikatec.vagas.solides.com.br). Ela não é documentada e pode mudar sem aviso.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

from vaga.schema import SENIORIDADES, _chave

# --- HTML da descrição → Markdown no formato dos exemplos ---------------------

# Títulos usados nas vagas publicadas → seção canônica do modelo.
ALIASES_SECAO: dict[str, str] = {
    "responsabilidades": "Responsabilidades",
    "atividades": "Responsabilidades",
    "requisitos": "Requisitos",
    "hard skills": "Requisitos",
    "requisitos tecnicos": "Requisitos",
    "qualificacoes": "Requisitos",
    "diferenciais": "Diferenciais",
    "soft skills": "Soft Skills",
    "competencias comportamentais": "Soft Skills",
}

# Linhas que encerram uma lista e voltam a ser parágrafo.
_FECHAMENTO = re.compile(r"^(se você|se voce|se identificou|horário|horario|sendo|venha)\b", re.IGNORECASE)
_QUEBRAS = {"p", "div", "br", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}


class _Linhas(HTMLParser):
    """Quebra o HTML em linhas de texto, marcando as que começam um <li>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.linhas: list[tuple[str, bool]] = []
        self._atual: list[str] = []
        self._li = False

    def _fechar_linha(self) -> None:
        texto = re.sub(r"\s+", " ", "".join(self._atual)).strip()
        self._atual = []
        if texto:
            self.linhas.append((texto, self._li))
            self._li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self._fechar_linha()
            self._li = True
        elif tag in _QUEBRAS:
            self._fechar_linha()

    def handle_endtag(self, tag):
        if tag in _QUEBRAS or tag == "li":
            self._fechar_linha()

    def handle_data(self, data):
        self._atual.append(data)

    def close(self):
        super().close()
        self._fechar_linha()


def _secao(texto: str) -> str | None:
    return ALIASES_SECAO.get(_chave(texto.rstrip(":").strip()))


def html_para_markdown(html: str) -> str:
    """Converte a descrição HTML da Sólides para o Markdown dos exemplos (## seções, - itens)."""
    parser = _Linhas()
    parser.feed(html)
    parser.close()

    blocos: list[tuple[str, str]] = []  # (tipo, texto): tipo ∈ {"h", "li", "p"}
    em_secao = False
    for texto, li in parser.linhas:
        secao = _secao(texto)
        if secao:
            blocos.append(("h", secao))
            em_secao = True
            continue
        if texto.startswith("•"):
            li, texto = True, texto.lstrip("• ").strip()
        anterior = blocos[-1][0] if blocos else None
        if (not li and em_secao and anterior in ("h", "li") and texto.endswith((";", "."))
                and not _FECHAMENTO.match(texto)):
            li = True  # item de lista escrito como parágrafo
        if not li:
            em_secao = em_secao and not _FECHAMENTO.match(texto)
        blocos.append(("li" if li else "p", texto))

    saida: list[str] = []
    for i, (tipo, texto) in enumerate(blocos):
        if i > 0 and not (tipo == "li" and blocos[i - 1][0] == "li"):
            saida.append("")
        saida.append(f"## {texto}" if tipo == "h" else f"- {texto}" if tipo == "li" else texto)
    return "\n".join(saida)


# --- Vaga da API → arquivo de exemplo (ficha + descrição) -----------------------

_MODELOS = {"presencial": "Presencial", "hibrido": "Híbrido", "remoto": "Remoto", "home office": "Remoto"}


def _nomes(itens) -> list[str]:
    return [i["name"] for i in (itens or []) if i.get("name")]


def _senioridade(nome: str) -> str:
    for opcao in SENIORIDADES:
        if _chave(opcao) == _chave(nome):
            return opcao
    return nome


def modelo_trabalho(v: dict) -> str:
    tipo = _chave(v.get("jobType") or "").replace("_", " ")
    return _MODELOS.get(tipo, (v.get("jobType") or "").capitalize())


def vaga_para_exemplo(v: dict, slug: str = "ikatec") -> str:
    """Monta o arquivo de exemplo no formato da skill: título, link, ficha para a Sólides e descrição."""
    modelo = modelo_trabalho(v)
    cidade, uf = (v.get("city") or {}).get("name"), (v.get("state") or {}).get("code")
    local = "Remoto" if modelo == "Remoto" else " - ".join(p for p in (cidade, uf) if p)

    ficha = [f"- Local: {local}" if local else None,
             f"- Modelo de trabalho: {modelo}" if modelo else None]
    if contratos := _nomes(v.get("recruitmentContractType")):
        ficha.append(f"- Contratação: {' / '.join(contratos)}")
    if senioridades := _nomes(v.get("seniority")):
        ficha.append(f"- Senioridade: {' / '.join(_senioridade(s) for s in senioridades)}")
    if jornada := _nomes(v.get("shift")):
        ficha.append(f"- Jornada: {' / '.join(jornada)}")
    if beneficios := _nomes(v.get("benefits")):
        ficha.append(f"- Benefícios: {'; '.join(beneficios)}")

    partes = [
        f"# {v['title'].strip()}",
        f"> Vaga publicada: https://{slug}.vagas.solides.com.br/vaga/{v['id']}",
        "**Ficha para a Sólides**\n" + "\n".join(l for l in ficha if l),
        "---",
        html_para_markdown(v.get("description") or ""),
    ]
    return "\n\n".join(partes) + "\n"
