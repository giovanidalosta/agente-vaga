from vaga.modelo import secoes_do_modelo


def test_extrai_secoes_nivel_2_em_ordem():
    texto = "# Título\n## Sobre a Ikatec\ntexto\n###  Sub\n##   Requisitos  \n## Benefícios\n"
    assert secoes_do_modelo(texto) == ["Sobre a Ikatec", "Requisitos", "Benefícios"]


def test_ignora_titulos_em_bloco_de_codigo():
    texto = "## A\n```\n## Não conta\n```\n## B\n"
    assert secoes_do_modelo(texto) == ["A", "B"]


def test_modelo_sem_secoes():
    assert secoes_do_modelo("só texto") == []


from vaga.modelo import secoes_opcionais_do_modelo


def test_secao_opcional_tem_marcador_removido():
    texto = "## Requisitos\n## Diferenciais (opcional)\n## Soft Skills\n"
    assert secoes_do_modelo(texto) == ["Requisitos", "Diferenciais", "Soft Skills"]
    assert secoes_opcionais_do_modelo(texto) == {"Diferenciais"}
