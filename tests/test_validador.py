import pytest
from vaga.validador import validar_descricao

SECOES = ["Sobre a Ikatec", "Responsabilidades", "Requisitos"]
OK = "## Sobre a Ikatec\nx\n## Responsabilidades\n- APIs\n## Requisitos\n- Python, 3 anos de experiência\n"


def test_descricao_valida():
    assert validar_descricao(OK, SECOES, ["Requisitos"]) == []


def test_secao_ausente():
    assert validar_descricao("## Sobre a Ikatec\n## Requisitos\n", SECOES) == ["seção ausente: 'Responsabilidades'"]


def test_secoes_fora_de_ordem():
    texto = "## Requisitos\n## Sobre a Ikatec\n## Responsabilidades\n"
    assert validar_descricao(texto, SECOES) == ["seções fora da ordem do modelo"]


def test_termo_obrigatorio_ausente():
    assert validar_descricao(OK, SECOES, ["Sênior"]) == ["termo obrigatório ausente: 'Sênior'"]


@pytest.mark.parametrize("trecho", ["[nome da empresa]", "{salario}", "TODO", "XXX"])
def test_placeholder(trecho):
    erros = validar_descricao(OK + trecho, SECOES)
    assert any(e.startswith("placeholder não preenchido") for e in erros)


def test_link_markdown_nao_e_placeholder():
    assert validar_descricao(OK + "[site](https://ikatec.com.br)", SECOES) == []


@pytest.mark.parametrize("trecho", ["Boa aparência", "sexo masculino", "idade entre 25 e 35",
                                    "até 30 anos", "Solteiro(a)", "apenas mulheres"])
def test_termo_discriminatorio(trecho):
    erros = validar_descricao(OK + trecho, SECOES)
    assert any(e.startswith("termo discriminatório") for e in erros)


@pytest.mark.parametrize("trecho", ["aparência do produto", "3 anos de experiência", "mais de 10 anos de mercado"])
def test_sem_falso_positivo(trecho):
    assert validar_descricao(OK + trecho, SECOES) == []


def test_declaracao_de_diversidade_nao_e_discriminatoria():
    texto = OK + "Valorizamos a diversidade: contratamos sem distinção de gênero, idade ou religião.\n"
    assert validar_descricao(texto, SECOES) == []


def test_exigencia_religiosa_e_discriminatoria():
    erros = validar_descricao(OK + "Preferencialmente evangélico.\n", SECOES)
    assert any(e.startswith("termo discriminatório") for e in erros)


def test_todo_minusculo_em_portugues_nao_e_placeholder():
    assert validar_descricao(OK + "Atuação em todo o ciclo do produto.\n", SECOES) == []


@pytest.mark.parametrize("linha", [
    "Não fazemos distinção de gênero, idade ou religião.",
    "Não discriminamos por religião.",
    "Venha como você é, seja qual for sua religião, gênero ou idade.",
    "Plano de saúde extensivo a dependentes até 21 anos.",
    "Auxílio educação para filhos até 14 anos.",
])
def test_frases_legitimas_nao_sao_discriminatorias(linha):
    assert validar_descricao(OK + linha + "\n", SECOES) == []


@pytest.mark.parametrize("linha", [
    "Sexo: masculino", "Idade: entre 25 e 35 anos", "Faixa etária de 20 a 30",
    "Limite de idade 35", "Casado(a)", "Estado civil: casado", "Preferencialmente homens",
    "Somos uma empresa cristã e buscamos pessoas cristãs",
])
def test_variacoes_discriminatorias(linha):
    erros = validar_descricao(OK + linha + "\n", SECOES)
    assert any(e.startswith("termo discriminatório") for e in erros)
