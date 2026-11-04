from vaga.validar import main


def escrever(tmp_path, nome, texto):
    p = tmp_path / nome
    p.write_text(texto, encoding="utf-8")
    return str(p)


def test_valido(tmp_path, capsys):
    m = escrever(tmp_path, "m.md", "## A\n## B\n")
    d = escrever(tmp_path, "d.md", "## A\nPleno\n## B\n")
    assert main([d, "--modelo", m, "--exigir", "Pleno"]) == 0
    assert capsys.readouterr().out.strip() == "OK"


def test_invalido(tmp_path, capsys):
    m = escrever(tmp_path, "m.md", "## A\n## B\n")
    d = escrever(tmp_path, "d.md", "## A\n")
    assert main([d, "--modelo", m]) == 1
    assert "seção ausente: 'B'" in capsys.readouterr().out


def test_arquivo_inexistente(tmp_path, capsys):
    m = escrever(tmp_path, "m.md", "## A\n")
    assert main([str(tmp_path / "nao.md"), "--modelo", m]) == 2
    assert "arquivo não encontrado" in capsys.readouterr().err


def test_modelo_sem_secoes(tmp_path, capsys):
    m = escrever(tmp_path, "m.md", "sem títulos")
    d = escrever(tmp_path, "d.md", "## A\n")
    assert main([d, "--modelo", m]) == 2
    assert "modelo não possui seções '## '" in capsys.readouterr().err


def escrever_bom(tmp_path, nome, texto):
    p = tmp_path / nome
    p.write_text(texto, encoding="utf-8-sig")
    return str(p)


def test_bom_no_modelo_e_na_descricao(tmp_path, capsys):
    m = escrever_bom(tmp_path, "m.md", "## Sobre\n## Requisitos\n")
    sem_sobre = escrever(tmp_path, "d1.md", "## Requisitos\n")
    assert main([sem_sobre, "--modelo", m]) == 1
    assert "seção ausente: 'Sobre'" in capsys.readouterr().out
    d = escrever_bom(tmp_path, "d2.md", "## Sobre\n## Requisitos\n")
    assert main([d, "--modelo", m]) == 0


def test_placeholder_em_titulo_do_modelo(tmp_path, capsys):
    m = escrever(tmp_path, "m.md", "## Sobre a vaga de [Cargo]\n## Requisitos\n")
    d = escrever(tmp_path, "d.md", "## Requisitos\n")
    assert main([d, "--modelo", m]) == 2
    assert "modelo tem placeholder no título: 'Sobre a vaga de [Cargo]'" in capsys.readouterr().err
