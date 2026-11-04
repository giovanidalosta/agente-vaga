# Agente de Descrição de Vaga — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a skill `/vaga`, que gera descrições de vaga no padrão da Ikatec a partir de campos estruturados e confere o resultado com um validador em Python.

**Architecture:** O pacote Python `vaga/` tem três partes: o schema de entrada (`schema.py`), a leitura do modelo da empresa (`modelo.py`) e o validador da saída (`validador.py`), que roda pela linha de comando com `python -m vaga.validar`. A skill (`SKILL.md`) conduz a conversa: coleta e valida os campos, lê o modelo e os exemplos, escreve a descrição, roda o validador e corrige o texto até ele passar.

**Tech Stack:** Python 3.11+, pytest, Claude Code Skills.

**Spec:** `docs/superpowers/specs/2026-11-04-agente-descricao-vaga.md`

## Global Constraints

- Python ≥ 3.11, somente biblioteca padrão em runtime (pytest só para testes).
- Nomes de código, mensagens de erro e textos ao usuário em português.
- Valores fixos: senioridade ∈ {Estágio, Júnior, Pleno, Sênior, Especialista, Liderança}; modelo_trabalho ∈ {Presencial, Híbrido, Remoto}; tipo_contratacao ∈ {CLT, PJ, Estágio}.
- Modelo da empresa em `.claude/skills/vaga/referencias/modelo-vaga.md`; exemplos em `.claude/skills/vaga/referencias/exemplos/*.md`.
- Saída salva em `vagas/AAAA-MM-DD-<slug>.md`.
- Validador: exit code 0 = válido, 1 = inválido (erros no stdout, um por linha), 2 = erro de uso/arquivo.

## Review Focus

1. **Acentos e caixa nos enums.** "senior", "SÊNIOR" e "hibrido" devem ser aceitos e normalizados ("Sênior", "Híbrido"). Recrutador digita sem acento. → teste em Task 1.
2. **Remoto sem local.** `local` vazio com `Remoto` é válido; vazio com `Presencial`/`Híbrido` é erro. → teste em Task 1.
3. **Termo discriminatório disfarçado.** "boa aparência", "sexo masculino", "idade entre 25 e 35", "até 30 anos" e "solteiro(a)" precisam ser pegos sem diferenciar maiúsculas de minúsculas. Já "aparência do produto" e "experiência de 3 anos" não podem ser falsos positivos. → teste em Task 3.
4. **Modelo com títulos com espaços extras ou subseções `###`.** Só os títulos `## ` contam, com espaços aparados. Os `###` são ignorados. → teste em Task 2.
5. **Arquivo de saída inexistente ou modelo ausente.** O CLI sai com código 2 e mensagem clara, sem traceback. → teste em Task 4.

---

## File Structure

```
pyproject.toml                         # projeto + config pytest
vaga/__init__.py
vaga/schema.py                         # Vaga (dataclass) + validar_entrada
vaga/modelo.py                         # secoes_do_modelo
vaga/validador.py                      # validar_descricao
vaga/validar.py                        # CLI: python -m vaga.validar
tests/test_schema.py
tests/test_modelo.py
tests/test_validador.py
tests/test_cli.py
.claude/skills/vaga/SKILL.md
.claude/skills/vaga/referencias/modelo-vaga.md      # fornecido pela Ikatec
.claude/skills/vaga/referencias/exemplos/*.md        # fornecidos pela Ikatec
vagas/.gitkeep
```

---

### Task 1: Schema de entrada

**Files:**
- Create: `pyproject.toml`, `vaga/__init__.py`, `vaga/schema.py`
- Test: `tests/test_schema.py`

**Interfaces:**
- Produces:
  - `SENIORIDADES: tuple[str, ...]`, `MODELOS_TRABALHO: tuple[str, ...]`, `TIPOS_CONTRATACAO: tuple[str, ...]` (valores canônicos com acento).
  - `@dataclass class Vaga: cargo: str; senioridade: str; modelo_trabalho: str; local: str; tipo_contratacao: str; responsabilidades: list[str]; requisitos: list[str]; diferenciais: list[str] = []; beneficios: list[str] = []; faixa_salarial: str = ""` (listas com `field(default_factory=list)`).
  - `validar_entrada(dados: dict) -> tuple[Vaga | None, list[str]]`: devolve `(Vaga normalizada, [])` ou `(None, [erros])`.

- [ ] **Step 0: Setup**

`git init`. Crie o `pyproject.toml` com `[project] name="agente-descricao-vaga"`, `requires-python=">=3.11"`, `[project.optional-dependencies] dev=["pytest>=8"]` e `[tool.pytest.ini_options] testpaths=["tests"]`. Depois rode `python -m venv .venv` e `pip install -e .[dev]`. Adicione `.venv/` e `__pycache__/` ao `.gitignore`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_schema.py -v`
Expected: FAIL com `ModuleNotFoundError: vaga.schema`

- [ ] **Step 3: Implement `validar_entrada(dados: dict) -> tuple[Vaga | None, list[str]]` in `vaga/schema.py`**

Para normalizar os enums, compare com `unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().casefold().strip()` dos dois lados e devolva o valor canônico. Remova espaços das pontas dos textos e tire os itens vazios das listas. Junte todos os erros antes de retornar.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_schema.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add .gitignore pyproject.toml vaga tests/test_schema.py
git commit -m "feat: schema de entrada da vaga com normalização de enums"
```

---

### Task 2: Leitura do modelo da empresa

**Files:**
- Create: `vaga/modelo.py`
- Test: `tests/test_modelo.py`

**Interfaces:**
- Produces: `secoes_do_modelo(texto: str) -> list[str]`: títulos de nível 2 (linhas que começam com `## `) na ordem em que aparecem e sem espaços nas pontas. Ignora `#`, `###` e linhas dentro de blocos de código cercados por ```.

- [ ] **Step 1: Write the failing tests**

```python
from vaga.modelo import secoes_do_modelo

def test_extrai_secoes_nivel_2_em_ordem():
    texto = "# Título\n## Sobre a Ikatec\ntexto\n###  Sub\n##   Requisitos  \n## Benefícios\n"
    assert secoes_do_modelo(texto) == ["Sobre a Ikatec", "Requisitos", "Benefícios"]

def test_ignora_titulos_em_bloco_de_codigo():
    texto = "## A\n```\n## Não conta\n```\n## B\n"
    assert secoes_do_modelo(texto) == ["A", "B"]

def test_modelo_sem_secoes():
    assert secoes_do_modelo("só texto") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modelo.py -v`
Expected: FAIL com `ModuleNotFoundError: vaga.modelo`

- [ ] **Step 3: Implement `secoes_do_modelo` in `vaga/modelo.py`**

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modelo.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add vaga/modelo.py tests/test_modelo.py
git commit -m "feat: extração das seções do modelo de vaga"
```

---

### Task 3: Validador da descrição gerada

**Files:**
- Create: `vaga/validador.py`
- Test: `tests/test_validador.py`

**Interfaces:**
- Consumes: `secoes_do_modelo(texto) -> list[str]` (Task 2).
- Produces: `validar_descricao(descricao: str, secoes: list[str], termos_obrigatorios: list[str] = []) -> list[str]` devolve uma lista de erros (vazia se a descrição for válida). `TERMOS_PROIBIDOS: list[re.Pattern]`.

Regras, todas aplicadas e acumuladas:
1. Seção ausente → `"seção ausente: '<nome>'"`. Seções presentes fora da ordem do modelo → `"seções fora da ordem do modelo"`.
2. Cada termo em `termos_obrigatorios` que não aparece no texto (sem diferenciar maiúsculas de minúsculas) → `"termo obrigatório ausente: '<termo>'"`.
3. Placeholder → `"placeholder não preenchido: '<trecho>'"` para os padrões `\[[^\]\n]{1,60}\](?!\()` (colchete que não é link Markdown), `\{[^}\n]{1,60}\}`, `\bTODO\b` e `\bXXX\b`.
4. Termo discriminatório → `"termo discriminatório: '<trecho>'"`. Os padrões abaixo são aplicados com `re.IGNORECASE`:
   - `boa apar[êe]ncia`
   - `\bsexo (masculino|feminino)\b`
   - `\b(apenas|somente) (homens|mulheres)\b`
   - `\bidade (entre|m[áa]xima|m[íi]nima|at[ée])\b`
   - `\bat[ée] \d{2} anos\b`
   - `\bsolteir[oa](\(a\))?\b`
   - `\bsem filhos\b`
   - `\b(religi[ãa]o|crist[ãa]o|evang[ée]lic[oa])\b`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validador.py -v`
Expected: FAIL com `ModuleNotFoundError: vaga.validador`

- [ ] **Step 3: Implement `validar_descricao` in `vaga/validador.py`**

Extraia as seções da descrição com `secoes_do_modelo` e compare com as do modelo. A ordem só é checada quando nenhuma seção está faltando: filtre as seções da descrição pelas que existem no modelo e compare a lista resultante com `secoes`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validador.py -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add vaga/validador.py tests/test_validador.py
git commit -m "feat: validador de descrição (seções, placeholders, termos discriminatórios)"
```

---

### Task 4: CLI do validador

**Files:**
- Create: `vaga/validar.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `secoes_do_modelo` (Task 2), `validar_descricao` (Task 3).
- Produces: `main(argv: list[str] | None = None) -> int`. Uso: `python -m vaga.validar <descricao.md> --modelo <modelo-vaga.md> [--exigir TERMO ...]`. Imprime `OK` ou um erro por linha. Retorna 0, 1 ou 2 (ver Global Constraints). Termina com `if __name__ == "__main__": sys.exit(main())`. Lê os arquivos em UTF-8.

- [ ] **Step 1: Write the failing tests**

```python
from vaga.validar import main

def escrever(tmp_path, nome, texto):
    p = tmp_path / nome; p.write_text(texto, encoding="utf-8"); return str(p)

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError: vaga.validar`

- [ ] **Step 3: Implement `main` in `vaga/validar.py` with `argparse`**

Use `--exigir` com `action="append"` e `default=[]`. Capture `FileNotFoundError` e imprima a mensagem no stderr.

- [ ] **Step 4: Run all tests**

Run: `pytest -v`
Expected: todos passam

- [ ] **Step 5: Commit**

```bash
git add vaga/validar.py tests/test_cli.py
git commit -m "feat: CLI python -m vaga.validar"
```

---

### Task 5: Skill `/vaga` e referências da Ikatec

**Files:**
- Create: `.claude/skills/vaga/SKILL.md`, `.claude/skills/vaga/referencias/modelo-vaga.md`, `.claude/skills/vaga/referencias/exemplos/` (1+ arquivos), `vagas/.gitkeep`

**Interfaces:**
- Consumes: os campos e enums de `vaga/schema.py` (Task 1) e o CLI `python -m vaga.validar` (Task 4).

- [ ] **Step 1: Receber o modelo e os exemplos da Ikatec**

Peça ao usuário o modelo de vaga e de 1 a 3 vagas reais já publicadas. Salve o modelo em `referencias/modelo-vaga.md`, com cada seção fixa como título `## `, e os exemplos em `referencias/exemplos/`. Confira o modelo: `python -c "from vaga.modelo import secoes_do_modelo; print(secoes_do_modelo(open('.claude/skills/vaga/referencias/modelo-vaga.md',encoding='utf-8').read()))"` deve listar as seções esperadas. Não avance sem esse material, porque a skill depende dele.

- [ ] **Step 2: Escrever `SKILL.md`**

Frontmatter:
```yaml
---
name: vaga
description: Gera descrições de vaga no padrão da Ikatec a partir de campos estruturados (cargo, senioridade, modelo de trabalho, local, contratação, responsabilidades, requisitos, diferenciais, benefícios, faixa salarial). Use quando pedirem para criar, escrever ou revisar uma descrição/anúncio de vaga.
---
```
O corpo descreve este fluxo, nesta ordem:
1. Coletar os campos da tabela da spec. Perguntar de uma vez só pelos obrigatórios que faltarem, mostrando as opções válidas dos enums.
2. Validar a entrada com `python -c` chamando `validar_entrada` e passando os dados em JSON. Se houver erros, mostrar ao usuário e voltar ao passo 1.
3. Ler `referencias/modelo-vaga.md` e todos os `referencias/exemplos/*.md`. O texto segue as seções do modelo na ordem e imita o tom dos exemplos.
4. Regras de escrita: não inventar benefícios, faixa salarial ou requisitos que não foram informados; nunca remover uma seção do modelo (o validador exige todas); se faltarem dados para uma seção, usar o texto institucional que o modelo traz para ela; usar linguagem inclusiva ("pessoa desenvolvedora" ou o cargo seguido de "(a/e)", conforme os exemplos); não usar termos discriminatórios.
5. Salvar em `vagas/AAAA-MM-DD-<slug>.md`. O slug é o cargo em minúsculas, sem acentos e com hífens.
6. Rodar `python -m vaga.validar <arquivo> --modelo .claude/skills/vaga/referencias/modelo-vaga.md --exigir "<cargo>" --exigir "<senioridade>" --exigir "<modelo_trabalho>" --exigir "<tipo_contratacao>"`. Se o código de saída for 1, corrigir o texto conforme os erros e rodar de novo, no máximo 3 vezes. Depois disso, mostrar os erros que restarem ao usuário.
7. Mostrar a descrição final e o caminho do arquivo.

- [ ] **Step 3: Teste de ponta a ponta**

Em uma sessão nova do Claude Code nesta pasta, rode `/vaga` e informe: Desenvolvedor Backend, pleno, hibrido, Florianópolis/SC, CLT, responsabilidades ["Desenvolver APIs REST", "Participar de code reviews"] e requisitos ["Python", "SQL"].
Expected: o arquivo `vagas/2026-..-desenvolvedor-backend.md` é criado; `python -m vaga.validar` nele imprime `OK`; o texto mostra "Pleno" e "Híbrido" normalizados e não tem benefícios inventados.
Depois rode de novo omitindo `local` com modelo Presencial. Expected: a skill pergunta pelo local antes de gerar o texto.

- [ ] **Step 4: Commit**

```bash
git add .claude vagas/.gitkeep
git commit -m "feat: skill /vaga com modelo e exemplos da Ikatec"
```
