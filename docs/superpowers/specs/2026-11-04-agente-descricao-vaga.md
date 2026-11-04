# Agente de Descrição de Vaga — Especificação

**Data:** 2026-11-04

## Objetivo

Um recrutador da Ikatec digita `/vaga` no Claude Code, informa os dados da vaga em campos estruturados e recebe uma descrição de vaga pronta para publicar. O texto segue o modelo e o tom de voz da empresa.

## Decisões

- **Interface:** uma skill do Claude Code (projeto: `.claude/skills/vaga/`). Não há app web nem API.
- **Linguagem dos utilitários:** Python 3.11+, testes com pytest.
- **Entrada:** campos estruturados (abaixo). O Claude pergunta pelos obrigatórios que faltarem.
- **Padrão da empresa:** o recrutador fornece o modelo (`modelo-vaga.md`) e exemplos de vagas reais. As seções `## ` do modelo definem a estrutura obrigatória da saída.

## Campos de entrada

| Campo | Obrigatório | Valores |
|---|---|---|
| cargo | sim | texto |
| senioridade | sim | Estágio, Júnior, Pleno, Sênior, Especialista, Liderança |
| modelo_trabalho | sim | Presencial, Híbrido, Remoto |
| local | sim, exceto quando Remoto | texto (cidade/UF) |
| tipo_contratacao | sim | CLT, PJ, Estágio |
| responsabilidades | sim, ≥1 | lista de textos |
| requisitos | sim, ≥1 | lista de textos |
| diferenciais | não | lista de textos |
| beneficios | não | lista de textos |
| faixa_salarial | não | texto livre (ex.: "R$ 6.000 – R$ 8.000") |

## Saída

Arquivo Markdown em `vagas/AAAA-MM-DD-<slug-do-cargo>.md` que:
1. contém todas as seções `## ` do modelo, na mesma ordem;
2. menciona o cargo, a senioridade, o modelo de trabalho e o tipo de contratação;
3. não contém placeholders sem preenchimento (`[...]`, `{...}`, `TODO`, `XXX`);
4. não contém termos discriminatórios (gênero, idade, aparência, estado civil, religião). Ver a Lei 9.029/95.

Antes de mostrar o resultado, a skill roda o validador e corrige o texto até ele passar.
