import json
from pathlib import Path

import pytest

from vaga.modelo import secoes_do_modelo, secoes_opcionais_do_modelo
from vaga.solides import html_para_markdown, vaga_para_exemplo
from vaga.validador import validar_descricao

FIXTURE = Path(__file__).parent / "fixtures" / "solides_vagas.json"
MODELO = Path(__file__).parent.parent / ".claude" / "skills" / "vaga" / "referencias" / "modelo-vaga.md"


def vagas_reais():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["data"]


# --- html_para_markdown -------------------------------------------------------

def test_lista_ul_li_com_titulo_em_paragrafo():
    html = "<p>Intro.</p><p><strong>Responsabilidades</strong></p><ul><li>Fazer A;</li><li>Fazer B.</li></ul>"
    assert html_para_markdown(html) == "Intro.\n\n## Responsabilidades\n\n- Fazer A;\n- Fazer B."


def test_bullets_com_br():
    html = "<div><strong>Requisitos</strong><br />• Python;<br />• SQL.<br /><br />Se você gosta de desafios, venha!</div>"
    assert html_para_markdown(html) == "## Requisitos\n\n- Python;\n- SQL.\n\nSe você gosta de desafios, venha!"


def test_titulo_dentro_do_li_e_alias_hard_skills():
    html = "<ul><li>Último item.<br /><br /><strong>Hard Skills<br /><br /></strong></li><li>CRM;</li></ul>"
    assert html_para_markdown(html) == "- Último item.\n\n## Requisitos\n\n- CRM;"


def test_titulo_com_dois_pontos_e_acento_diferente():
    assert html_para_markdown("<p><b>soft skills:</b></p><ul><li>Empatia.</li></ul>") == "## Soft Skills\n\n- Empatia."


def test_entidades_e_espacos():
    assert html_para_markdown("<p>R&amp;D&nbsp; e   mais</p>") == "R&D e mais"


# --- vaga_para_exemplo ----------------------------------------------------------

def test_exemplo_tem_titulo_link_ficha_e_corpo():
    v = vagas_reais()[0]
    texto = vaga_para_exemplo(v)
    assert texto.startswith("# Analista de Suporte Técnico JR\n")
    assert "> Vaga publicada: https://ikatec.vagas.solides.com.br/vaga/945675" in texto
    assert "- Local: Bauru - SP" in texto
    assert "- Modelo de trabalho: Presencial" in texto
    assert "- Contratação: CLT" in texto
    assert "- Senioridade: Júnior" in texto
    assert "- Jornada: Integral" in texto
    assert "- Benefícios: Clube de descontos; " in texto
    assert "\n---\n" in texto and "## Responsabilidades" in texto


def test_senioridade_ausente_omite_linha():
    v = vagas_reais()[2]  # Assessor(a): sem senioridade na Sólides
    assert "Senioridade:" not in vaga_para_exemplo(v)


@pytest.mark.parametrize("v", [v for v in vagas_reais() if len(v["description"]) > 500], ids=lambda v: str(v["id"]))
def test_vagas_reais_convertidas_passam_no_validador(v):
    modelo = MODELO.read_text(encoding="utf-8")
    erros = validar_descricao(vaga_para_exemplo(v), secoes_do_modelo(modelo), opcionais=secoes_opcionais_do_modelo(modelo))
    assert erros == []


# --- baixar_vagas ---------------------------------------------------------------

from vaga.solides import ErroSolides, baixar_vagas, beneficios_markdown, pacote_beneficios


def test_baixar_vagas_percorre_todas_as_paginas():
    urls = []

    def falsa(url):
        urls.append(url)
        pagina = int(url.split("page=")[1])
        return {"totalPages": 2, "currentPage": pagina, "count": 3,
                "data": [{"id": pagina * 10}] if pagina == 2 else [{"id": 1}, {"id": 2}]}

    vagas = baixar_vagas("ikatec", buscar=falsa)
    assert [v["id"] for v in vagas] == [1, 2, 20]
    assert urls[0] == "https://apigw.solides.com.br/jobs/v3/companies/ikatec/vacancies?take=25&page=1"
    assert len(urls) == 2


def test_resposta_inesperada_vira_erro_claro():
    with pytest.raises(ErroSolides, match="resposta inesperada da Sólides"):
        baixar_vagas("ikatec", buscar=lambda url: {"code": "BadRequestException"})


def test_falha_de_rede_vira_erro_claro():
    def falha(url):
        raise OSError("timed out")

    with pytest.raises(ErroSolides, match="não foi possível acessar a Sólides"):
        baixar_vagas("ikatec", buscar=falha)


# --- benefícios -----------------------------------------------------------------

def test_pacote_de_beneficios_por_contratacao():
    vagas = [
        {"recruitmentContractType": [{"name": "CLT"}], "benefits": [{"name": "PLR"}, {"name": "Wellhub"}]},
        {"recruitmentContractType": [{"name": "CLT"}], "benefits": [{"name": "PLR"}]},
        {"recruitmentContractType": [{"name": "PJ"}, {"name": "CLT"}], "benefits": [{"name": "Gympass"}]},
    ]
    pacotes = pacote_beneficios(vagas)
    assert pacotes["CLT"] == (3, [("PLR", 2), ("Gympass", 1), ("Wellhub", 1)])
    assert pacotes["PJ"] == (1, [("Gympass", 1)])


def test_beneficios_markdown():
    texto = beneficios_markdown({"CLT": (2, [("PLR", 2), ("Wellhub", 1)])}, data="2026-11-04")
    assert texto.startswith("# Benefícios publicados na Sólides\n")
    assert "2026-11-04" in texto
    assert "## CLT (2 vagas)\n\n- PLR — 2 de 2 vagas\n- Wellhub — 1 de 2 vagas\n" in texto


def test_pacote_real_clt_tem_plano_de_saude():
    _, itens = pacote_beneficios(vagas_reais())["CLT"]
    assert any("Plano de saúde" in nome for nome, _ in itens)


# --- CLI: sincronizar / revisar ---------------------------------------------------

from vaga.solides import main


def api_fixture(url):
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def preparar_destino(tmp_path):
    destino = tmp_path / "referencias"
    (destino / "exemplos").mkdir(parents=True)
    (destino / "modelo-vaga.md").write_text(MODELO.read_text(encoding="utf-8"), encoding="utf-8")
    (destino / "exemplos" / "manual-antigo.md").write_text("antigo", encoding="utf-8")
    (destino / "exemplos" / "solides-1-vaga-fechada.md").write_text("fechada", encoding="utf-8")
    return destino


def test_sincronizar_grava_exemplos_validos_e_beneficios(tmp_path, capsys):
    destino = preparar_destino(tmp_path)
    assert main(["sincronizar", "--destino", str(destino)], buscar=api_fixture) == 0
    nomes = sorted(p.name for p in (destino / "exemplos").iterdir())
    assert "solides-945675-analista-de-suporte-tecnico-jr.md" in nomes
    assert len([n for n in nomes if n.startswith("solides-")]) == 4  # banco de talentos fica de fora
    assert "solides-1-vaga-fechada.md" not in nomes  # vaga que saiu do ar é removida
    assert "manual-antigo.md" in nomes  # exemplos escritos à mão são preservados
    assert (destino / "beneficios.md").read_text(encoding="utf-8").startswith("# Benefícios publicados na Sólides")
    saida = capsys.readouterr().out
    assert "4 exemplos atualizados" in saida and "398916" in saida


def test_sincronizar_sem_vagas_validas_nao_apaga_nada(tmp_path, capsys):
    destino = preparar_destino(tmp_path)
    vazia = lambda url: {"totalPages": 1, "currentPage": 1, "count": 0, "data": []}
    assert main(["sincronizar", "--destino", str(destino)], buscar=vazia) == 1
    assert (destino / "exemplos" / "solides-1-vaga-fechada.md").exists()
    assert not (destino / "beneficios.md").exists()


def test_sincronizar_sem_rede(tmp_path, capsys):
    def falha(url):
        raise OSError("sem rede")

    assert main(["sincronizar", "--destino", str(preparar_destino(tmp_path))], buscar=falha) == 2
    assert "não foi possível acessar a Sólides" in capsys.readouterr().err


@pytest.mark.parametrize("ref", ["945675", "https://ikatec.vagas.solides.com.br/vaga/945675"])
def test_revisar_vaga_publicada(ref, tmp_path, capsys):
    destino = preparar_destino(tmp_path)
    assert main(["revisar", ref, "--destino", str(destino)], buscar=api_fixture) == 0
    saida = capsys.readouterr().out
    assert "# Analista de Suporte Técnico JR" in saida and saida.rstrip().endswith("Validação: OK")


def test_revisar_aponta_problemas(tmp_path, capsys):
    dados = json.loads(FIXTURE.read_text(encoding="utf-8"))
    dados["data"][0]["description"] += "<p>Requisito: boa aparência.</p>"
    assert main(["revisar", "945675", "--destino", str(preparar_destino(tmp_path))], buscar=lambda url: dados) == 1
    assert "termo discriminatório: 'boa aparência'" in capsys.readouterr().out


def test_revisar_vaga_inexistente(tmp_path, capsys):
    assert main(["revisar", "123", "--destino", str(preparar_destino(tmp_path))], buscar=api_fixture) == 2
    assert "vaga 123 não está aberta na Sólides" in capsys.readouterr().err
