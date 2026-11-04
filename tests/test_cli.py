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
