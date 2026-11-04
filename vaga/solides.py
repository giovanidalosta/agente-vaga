"""Integração de leitura com a página de carreiras da Ikatec na Sólides.

A Sólides expõe as vagas publicadas numa API pública (a mesma usada pelo site
ikatec.vagas.solides.com.br). Ela não é documentada e pode mudar sem aviso.
"""
from __future__ import annotations

import json
import re
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from typing import Callable

from vaga.schema import SENIORIDADES, _chave

URL_VAGAS = "https://apigw.solides.com.br/jobs/v3/companies/{empresa}/vacancies?take=25&page={pagina}"  # API limita take a 25
URL_VAGA = "https://apigw.solides.com.br/jobs/v3/vacancies/{id}"  # devolve também vagas encerradas


class ErroSolides(Exception):
    """Falha ao consultar a API da Sólides (rede ou resposta em formato inesperado)."""


def _buscar_json(url: str) -> dict:
    pedido = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "agente-vaga"})
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)


def baixar_vagas(empresa: str = "ikatec", buscar: Callable[[str], dict] = _buscar_json) -> list[dict]:
    """Todas as vagas publicadas da empresa na Sólides, percorrendo as páginas."""
    vagas: list[dict] = []
    pagina, total = 1, 1
    while pagina <= total:
        url = URL_VAGAS.format(empresa=empresa, pagina=pagina)
        try:
            dados = buscar(url)
        except (OSError, ValueError) as e:  # URLError/HTTPError/timeout são OSError; JSON inválido é ValueError
            raise ErroSolides(f"não foi possível acessar a Sólides ({url}): {e}") from None
        if not isinstance(dados, dict) or not isinstance(dados.get("data"), list):
            raise ErroSolides(f"resposta inesperada da Sólides ({url}): {str(dados)[:200]}")
        vagas += dados["data"]
        total = int(dados.get("totalPages") or 1)
        pagina += 1
    return vagas


def pacote_beneficios(vagas: list[dict]) -> dict[str, tuple[int, list[tuple[str, int]]]]:
    """Por tipo de contratação: (nº de vagas, [(benefício, nº de vagas que o oferecem)]), mais frequentes primeiro."""
    contagem: dict[str, Counter] = {}
    vagas_por_tipo: Counter = Counter()
    for v in vagas:
        beneficios = set(_nomes(v.get("benefits")))
        for tipo in _nomes(v.get("recruitmentContractType")):
            vagas_por_tipo[tipo] += 1
            contagem.setdefault(tipo, Counter()).update(beneficios)
    return {
        tipo: (vagas_por_tipo[tipo], sorted(contagem[tipo].items(), key=lambda kv: (-kv[1], kv[0])))
        for tipo in sorted(contagem)
    }


def beneficios_markdown(pacotes: dict[str, tuple[int, list[tuple[str, int]]]], data: str) -> str:
    linhas = [
        "# Benefícios publicados na Sólides",
        "",
        f"> Gerado por `python -m vaga.solides sincronizar` em {data}, a partir das vagas abertas. Não edite à mão.",
        "> A skill sugere o pacote do tipo de contratação; o recrutador confirma ou ajusta.",
    ]
    for tipo, (n, itens) in pacotes.items():
        linhas += ["", f"## {tipo} ({n} {'vaga' if n == 1 else 'vagas'})", ""]
        linhas += [f"- {nome} — {qtd} de {n} {'vaga' if n == 1 else 'vagas'}" for nome, qtd in itens]
    return "\n".join(linhas) + "\n"

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
        f"> Vaga publicada: https://{slug}.vagas.solides.com.br/vaga/{v['id']}" + (f" · criada em {v['createdAt'][:10]}" if v.get('createdAt') else ""),
        "**Ficha para a Sólides**\n" + "\n".join(l for l in ficha if l),
        "---",
        html_para_markdown(v.get("description") or ""),
    ]
    return "\n\n".join(partes) + "\n"


# --- CLI ------------------------------------------------------------------------
#   python -m vaga.solides sincronizar [--empresa ikatec] [--destino DIR]
#   python -m vaga.solides revisar <id ou link da vaga> [--empresa ikatec] [--destino DIR]

DESTINO_PADRAO = ".claude/skills/vaga/referencias"


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _chave(texto)).strip("-")


def _validar_exemplo(texto: str, modelo: str) -> list[str]:
    from vaga.modelo import secoes_do_modelo, secoes_opcionais_do_modelo
    from vaga.validador import validar_descricao

    return validar_descricao(texto, secoes_do_modelo(modelo), opcionais=secoes_opcionais_do_modelo(modelo))


def _sincronizar(vagas: list[dict], destino, modelo: str, empresa: str) -> int:
    from datetime import date
    from pathlib import Path

    exemplos_dir = Path(destino) / "exemplos"
    novos: dict[str, str] = {}
    for v in vagas:
        texto = vaga_para_exemplo(v, slug=empresa)
        erros = _validar_exemplo(texto, modelo)
        if erros:
            print(f"ignorada: vaga {v['id']} ({v['title'].strip()}) — {'; '.join(erros[:3])}")
            continue
        novos[f"solides-{v['id']}-{_slug(v['title'])}.md"] = texto

    if not novos:
        print("nenhuma vaga publicada passou no validador; exemplos e benefícios não foram alterados.")
        return 1

    exemplos_dir.mkdir(parents=True, exist_ok=True)
    historico_dir = Path(destino) / "historico"
    for antigo in exemplos_dir.glob("solides-*.md"):
        if antigo.name not in novos:
            historico_dir.mkdir(parents=True, exist_ok=True)
            antigo.replace(historico_dir / antigo.name)
            print(f"arquivado: {antigo.name} → historico/ (vaga não está mais aberta)")
    for nome, texto in novos.items():
        (exemplos_dir / nome).write_text(texto, encoding="utf-8")
    (Path(destino) / "beneficios.md").write_text(
        beneficios_markdown(pacote_beneficios(vagas), data=date.today().isoformat()), encoding="utf-8")
    print(f"{len(novos)} exemplos atualizados em {exemplos_dir}; benefícios em {Path(destino) / 'beneficios.md'}")
    return 0


def _revisar(vagas: list[dict], ref: str, modelo: str, empresa: str) -> int:
    import sys

    id_vaga = re.search(r"(\d+)\s*/?\s*$", ref.split("?")[0])
    v = next((v for v in vagas if id_vaga and str(v["id"]) == id_vaga.group(1)), None)
    if v is None:
        print(f"erro: vaga {ref} não está aberta na Sólides de '{empresa}'.", file=sys.stderr)
        return 2
    texto = vaga_para_exemplo(v, slug=empresa)
    erros = _validar_exemplo(texto, modelo)
    print(texto)
    print("Validação: OK" if not erros else "Validação: problemas encontrados\n" + "\n".join(f"- {e}" for e in erros))
    return 1 if erros else 0


def _id_da_ref(ref: str) -> str | None:
    m = re.search(r"(\d+)\s*/?\s*$", ref.split("?")[0])
    return m.group(1) if m else None


def _importar(refs: list[str], destino, modelo: str, empresa: str, buscar: Callable[[str], dict]) -> int:
    """Baixa vagas (inclusive encerradas) pelo id e grava as válidas em historico/."""
    from pathlib import Path

    historico_dir = Path(destino) / "historico"
    importadas: set[str] = set()
    for ref in refs:
        id_vaga = _id_da_ref(ref)
        if not id_vaga or id_vaga in importadas:
            if not id_vaga:
                print(f"{ref}: não parece um id ou link de vaga da Sólides")
            continue
        try:
            v = buscar(URL_VAGA.format(id=id_vaga))
        except (OSError, ValueError) as e:
            print(f"{id_vaga}: não foi possível acessar a Sólides ({e})")
            continue
        if not isinstance(v, dict) or "id" not in v:
            print(f"{id_vaga}: não encontrada na Sólides")
            continue
        if (v.get("slug") or "").lower() != empresa.lower():
            print(f"{id_vaga}: ignorada — a vaga não é da empresa '{empresa}'")
            continue
        texto = vaga_para_exemplo(v, slug=empresa)
        if erros := _validar_exemplo(texto, modelo):
            print(f"{id_vaga}: ignorada ({v['title'].strip()}) — {'; '.join(erros[:3])}")
            continue
        historico_dir.mkdir(parents=True, exist_ok=True)
        (historico_dir / f"solides-{v['id']}-{_slug(v['title'])}.md").write_text(texto, encoding="utf-8")
        importadas.add(id_vaga)
        print(f"{id_vaga}: importada ({v['title'].strip()}, {v.get('currentState') or 'status desconhecido'})")
    n = len(importadas)
    print(f"{n} {'vaga importada' if n == 1 else 'vagas importadas'} para {historico_dir}")
    return 0 if n else 1


def main(argv: list[str] | None = None, buscar: Callable[[str], dict] = _buscar_json) -> int:
    import argparse
    import sys
    from pathlib import Path

    from vaga.validar import _utf8

    _utf8(sys.stdout)
    _utf8(sys.stderr)
    parser = argparse.ArgumentParser(prog="python -m vaga.solides", description="Integração com a página de vagas da Sólides.")
    sub = parser.add_subparsers(dest="comando", required=True)
    for nome, ajuda in (("sincronizar", "atualiza os exemplos e o catálogo de benefícios a partir das vagas publicadas"),
                        ("revisar", "baixa uma vaga publicada e roda o validador nela"),
                        ("importar", "baixa vagas pelo id (inclusive encerradas) e grava no histórico")):
        p = sub.add_parser(nome, help=ajuda)
        if nome == "revisar":
            p.add_argument("vaga", help="id ou link da vaga na Sólides")
        if nome == "importar":
            p.add_argument("vagas", nargs="+", help="ids ou links das vagas na Sólides")
        p.add_argument("--empresa", default="ikatec", help="slug da empresa na Sólides (padrão: ikatec)")
        p.add_argument("--destino", default=DESTINO_PADRAO, help="pasta de referências da skill")
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0

    try:
        modelo = (Path(args.destino) / "modelo-vaga.md").read_text(encoding="utf-8-sig")
    except OSError as e:
        print(f"erro: modelo de vaga não encontrado em {args.destino}: {e}", file=sys.stderr)
        return 2
    if args.comando == "importar":
        return _importar(args.vagas, args.destino, modelo, args.empresa, buscar)
    try:
        vagas = baixar_vagas(args.empresa, buscar=buscar)
    except ErroSolides as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2

    if args.comando == "sincronizar":
        return _sincronizar(vagas, args.destino, modelo, args.empresa)
    return _revisar(vagas, args.vaga, modelo, args.empresa)


if __name__ == "__main__":
    import sys

    sys.exit(main())
