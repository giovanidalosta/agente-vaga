import json

import pytest

from vaga.base import carregar_vagas, main, normalizar_cargo, sugerir


def vaga_md(id_, titulo, criada, senioridade=None, secoes=None):
    ficha = ["**Ficha para a Sólides**", "- Local: Bauru - SP"]
    if senioridade:
        ficha.append(f"- Senioridade: {senioridade}")
    corpo = []
    for nome, itens in (secoes or {}).items():
        corpo += [f"## {nome}", ""] + [f"- {i}" for i in itens] + [""]
    return "\n".join([
        f"# {titulo}", "",
        f"> Vaga publicada: https://ikatec.vagas.solides.com.br/vaga/{id_} · criada em {criada}", "",
        *ficha, "", "---", "", "Intro.", "", *corpo,
    ])


@pytest.fixture
def base(tmp_path):
    pasta = tmp_path / "historico"
    pasta.mkdir()
    arquivos = {
        "1": ("Analista de Suporte Técnico JR [PRESENCIAL]", "2025-03-01", "Júnior",
              {"Responsabilidades": ["Atender chamados antigos."], "Requisitos": ["Windows."],
               "Soft Skills": ["Empatia antiga."]}),
        "2": ("Analista de Suporte Técnico - JR [PRESENCIAL]", "2026-06-10", "Júnior",
              {"Responsabilidades": ["Atender chamados novos."], "Requisitos": ["Windows e Linux."]}),
        "3": ("Analista de Suporte Técnico - Pleno [PRESENCIAL]", "2026-09-01", "Pleno",
              {"Responsabilidades": ["Resolver casos complexos."], "Requisitos": ["Redes."]}),
        "4": ("Executivo de Vendas [PRESENCIAL]", "2026-01-15", None,
              {"Responsabilidades": ["Prospectar."], "Requisitos": ["CRM."]}),
    }
    for id_, (titulo, data, sen, secoes) in arquivos.items():
        (pasta / f"solides-{id_}.md").write_text(vaga_md(id_, titulo, data, sen, secoes), encoding="utf-8")
    return [pasta]


def test_normalizar_cargo_remove_tags_e_senioridade():
    assert normalizar_cargo("Analista de Suporte Técnico - JR [PRESENCIAL]") == "analista de suporte tecnico"
    assert normalizar_cargo("Analista Customer Success  - JR [PRESENCIAL]") == "analista customer success"
    assert normalizar_cargo("Quality Assurance (QA) - PL") == "quality assurance qa"
    assert normalizar_cargo("Estágio em Suporte Técnico [PRESENCIAL]") == "estagio em suporte tecnico"


def test_carregar_vagas_le_cabecalho_ficha_e_secoes(base):
    vagas = {v.id: v for v in carregar_vagas(base)}
    v = vagas["2"]
    assert v.criada == "2026-06-10" and v.senioridade == "Júnior"
    assert v.secoes["Responsabilidades"] == ["Atender chamados novos."]


def test_senioridade_pelo_titulo_quando_nao_ha_ficha(tmp_path):
    pasta = tmp_path / "h"
    pasta.mkdir()
    (pasta / "a.md").write_text(vaga_md("9", "Quality Assurance (QA) - PL", "2026-01-01"), encoding="utf-8")
    assert carregar_vagas([pasta])[0].senioridade == "Pleno"


def test_mesmo_cargo_e_nivel_usa_a_vaga_mais_recente(base):
    s = sugerir("Analista de Suporte Técnico", "Júnior", carregar_vagas(base))
    assert s["encontrado"] is True
    resp = s["secoes"]["Responsabilidades"]
    assert resp["itens"] == ["Atender chamados novos."]
    assert resp["origem"] == {"id": "2", "criada": "2026-06-10", "titulo": "Analista de Suporte Técnico - JR [PRESENCIAL]",
                              "link": "https://ikatec.vagas.solides.com.br/vaga/2", "senioridade": "Júnior"}


def test_secao_que_falta_vem_da_vaga_anterior_do_mesmo_cargo(base):
    s = sugerir("Analista de Suporte Técnico", "Júnior", carregar_vagas(base))
    assert s["secoes"]["Soft Skills"]["itens"] == ["Empatia antiga."]
    assert s["secoes"]["Soft Skills"]["origem"]["id"] == "1"


def test_sem_o_mesmo_nivel_usa_o_mais_recente_de_outro_nivel(base):
    s = sugerir("Analista de Suporte Técnico", "Sênior", carregar_vagas(base))
    assert s["secoes"]["Responsabilidades"]["origem"]["id"] == "3"
    assert s["nivel_diferente"] is True


def test_busca_tolerante_a_nome_parcial(base):
    s = sugerir("analista de suporte", "Pleno", carregar_vagas(base))
    assert s["encontrado"] and s["secoes"]["Requisitos"]["itens"] == ["Redes."]


def test_cargo_desconhecido_devolve_parecidos(base):
    s = sugerir("Desenvolvedor Backend", "Pleno", carregar_vagas(base))
    assert s["encontrado"] is False and isinstance(s["parecidos"], list)


def test_outras_vagas_do_cargo_listadas_da_mais_recente_para_a_mais_antiga(base):
    s = sugerir("Analista de Suporte Técnico", "Júnior", carregar_vagas(base))
    assert [o["id"] for o in s["outras_vagas"]] == ["3", "1"]


def test_cli_sugerir_imprime_json(base, capsys):
    assert main(["sugerir", "--cargo", "Executivo de Vendas", "--senioridade", "Pleno", "--pastas", str(base[0])]) == 0
    dados = json.loads(capsys.readouterr().out)
    assert dados["secoes"]["Responsabilidades"]["itens"] == ["Prospectar."]


def test_cli_cargo_nao_encontrado_sai_com_1(base, capsys):
    assert main(["sugerir", "--cargo", "Astronauta", "--pastas", str(base[0])]) == 1


def test_diferenciais_nao_sao_completados_por_vaga_anterior(tmp_path):
    pasta = tmp_path / "h"
    pasta.mkdir()
    (pasta / "a.md").write_text(vaga_md("1", "Analista X JR", "2025-01-01", "Júnior",
                                        {"Responsabilidades": ["A."], "Diferenciais": ["Antigo."]}), encoding="utf-8")
    (pasta / "b.md").write_text(vaga_md("2", "Analista X JR", "2026-01-01", "Júnior",
                                        {"Responsabilidades": ["B."]}), encoding="utf-8")
    s = sugerir("Analista X", "Júnior", carregar_vagas([pasta]))
    assert "Diferenciais" not in s["secoes"]
