from vaga.modelo import secoes_do_modelo


def test_extrai_secoes_nivel_2_em_ordem():
    texto = "# Título\n## Sobre a Ikatec\ntexto\n###  Sub\n##   Requisitos  \n## Benefícios\n"
    assert secoes_do_modelo(texto) == ["Sobre a Ikatec", "Requisitos", "Benefícios"]


def test_ignora_titulos_em_bloco_de_codigo():
    texto = "## A\n```\n## Não conta\n```\n## B\n"
    assert secoes_do_modelo(texto) == ["A", "B"]


def test_modelo_sem_secoes():
    assert secoes_do_modelo("só texto") == []
