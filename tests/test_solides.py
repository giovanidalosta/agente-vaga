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
