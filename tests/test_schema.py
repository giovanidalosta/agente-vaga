from vaga.schema import validar_entrada

BASE = dict(cargo="Desenvolvedor Backend", senioridade="Pleno", modelo_trabalho="Híbrido",
            local="Florianópolis/SC", tipo_contratacao="CLT",
            responsabilidades=["Desenvolver APIs"], requisitos=["Python"])


def test_entrada_valida():
    vaga, erros = validar_entrada(BASE)
    assert erros == [] and vaga.cargo == "Desenvolvedor Backend" and vaga.beneficios == []


def test_enum_sem_acento_e_caixa_normaliza():
    vaga, erros = validar_entrada({**BASE, "senioridade": "SENIOR", "modelo_trabalho": "hibrido"})
    assert erros == [] and vaga.senioridade == "Sênior" and vaga.modelo_trabalho == "Híbrido"


def test_enum_invalido():
    _, erros = validar_entrada({**BASE, "senioridade": "Master"})
    assert erros == ["senioridade inválida: 'Master'. Use: Estágio, Júnior, Pleno, Sênior, Especialista, Liderança"]


def test_campos_obrigatorios_ausentes():
    _, erros = validar_entrada({})
    assert "cargo é obrigatório" in erros and "requisitos precisa de ao menos 1 item" in erros


def test_remoto_dispensa_local():
    vaga, erros = validar_entrada({**BASE, "modelo_trabalho": "Remoto", "local": ""})
    assert erros == []


def test_presencial_exige_local():
    _, erros = validar_entrada({**BASE, "modelo_trabalho": "Presencial", "local": "  "})
    assert erros == ["local é obrigatório quando o modelo de trabalho não é Remoto"]


def test_itens_vazios_de_lista_sao_descartados():
    _, erros = validar_entrada({**BASE, "requisitos": ["", "  "]})
    assert erros == ["requisitos precisa de ao menos 1 item"]
