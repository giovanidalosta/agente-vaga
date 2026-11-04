---
name: vaga
description: Gera descrições de vaga no padrão da Ikatec a partir de campos estruturados (cargo, senioridade, modelo de trabalho, local, contratação, responsabilidades, requisitos, diferenciais, soft skills, benefícios, faixa salarial). Use quando pedirem para criar, escrever ou revisar uma descrição/anúncio de vaga.
---

# Descrição de vaga (Ikatec)

Você escreve descrições de vaga prontas para publicar na Sólides (https://ikatec.vagas.solides.com.br/), no modelo e no tom de voz da Ikatec. Todos os comandos rodam a partir da raiz do projeto.

O resultado tem duas partes:
- **Ficha para a Sólides:** local, modelo de trabalho, contratação, senioridade, jornada e benefícios. Na Sólides esses dados vão em campos próprios do formulário, não no texto.
- **Descrição:** o corpo do anúncio, que segue `referencias/modelo-vaga.md`.

## 1. Coletar os campos

| Campo | Obrigatório | Valores |
|---|---|---|
| cargo | sim | texto (ex.: "Analista de Suporte Técnico") |
| senioridade | sim | Estágio, Júnior, Pleno, Sênior, Especialista, Liderança |
| modelo_trabalho | sim | Presencial, Híbrido, Remoto |
| local | sim, exceto Remoto | cidade - UF (ex.: "Bauru - SP") |
| tipo_contratacao | sim | CLT, PJ, Estágio |
| responsabilidades | sim (≥1) | lista |
| requisitos | sim (≥1) | lista |
| diferenciais | não | lista |
| soft_skills | não | lista |
| beneficios | não | lista |
| faixa_salarial | não | texto |
| jornada | não | texto (ex.: "Integral") |
| horario | não | texto (ex.: "das 10h às 20h") |
| area | não | texto, contexto para a introdução (ex.: "time de Marketing") |

Use o que o usuário já informou, inclusive na mensagem que chamou `/vaga`. Pergunte **de uma vez só** por todos os obrigatórios que faltarem, mostrando as opções válidas dos campos de lista fechada. Não pergunte pelos opcionais um a um; diga numa linha que eles podem ser informados.

O recrutador costuma mandar poucos tópicos. Você pode desenvolver e detalhar o que ele informou, no nível de detalhe dos exemplos, sem acrescentar fatos novos (ver passo 4).

## 2. Validar a entrada

Escreva os dados em `vagas/.entrada.json`, com as chaves exatamente como na tabela e as listas como arrays JSON. Depois rode:

```bash
python -X utf8 -c "import json,sys; from dataclasses import asdict; from vaga.schema import validar_entrada; v,e=validar_entrada(json.load(open(sys.argv[1],encoding='utf-8'))); print(json.dumps(asdict(v) if v else {'erros':e}, ensure_ascii=False, indent=2))" vagas/.entrada.json
```

- Se aparecer `erros`, mostre-os ao usuário em linguagem simples, peça as correções e volte ao passo 1.
- Se não, use **os valores normalizados que o comando imprimiu** (ex.: "junior" vira "Júnior") daqui em diante. `jornada`, `horario` e `area` não passam pelo validador; use-os como vieram. Apague `vagas/.entrada.json`.

## 3. Ler o padrão da empresa

Leia `.claude/skills/vaga/referencias/modelo-vaga.md` e todos os arquivos em `.claude/skills/vaga/referencias/exemplos/`.

- Use **exatamente** os títulos `## ` do modelo, na mesma ordem e com a mesma grafia, sem o marcador "(opcional)".
- Imite o tom, o tamanho e a formatação dos exemplos: 1 a 3 parágrafos de introdução, listas de tópicos e a frase de fechamento.

Se o modelo não existir, pare e peça ao usuário o modelo de vaga da Ikatec.

## 4. Escrever

**Título** (linha `# `), no estilo da Sólides: `<Cargo> <sigla da senioridade> [<MODELO>]`. Exemplo: `Analista de Suporte Técnico JR [PRESENCIAL]`. As siglas são: Estágio → ESTÁGIO, Júnior → JR, Pleno → PL, Sênior → SR; Especialista e Liderança vão por extenso.

**Ficha para a Sólides**, logo abaixo do título, separada da descrição por `---`. Siga o formato dos exemplos:
```
**Ficha para a Sólides**
- Local: <local ou "Remoto">
- Modelo de trabalho: <modelo_trabalho>
- Contratação: <tipo_contratacao>
- Senioridade: <senioridade>
- Jornada: <jornada, se informada>
- Faixa salarial: <faixa_salarial ou "Não informado">
- Benefícios: <itens separados por "; ", se informados>
```

**Descrição:**
- A introdução preenche as lacunas do modelo: "A Ikatec está em busca de um(a) <Cargo>. Se você <perfil da pessoa, a partir dos requisitos e soft skills>, queremos te conhecer!". Pode ter um segundo parágrafo sobre o papel ou a área, como nos exemplos.
- Seções na ordem do modelo. Itens com a primeira letra maiúscula e terminados em `;`, com `.` no último item.
- **Diferenciais** é opcional: se não for informado, omita a seção inteira.
- **Soft Skills** é obrigatória: se não for informada, sugira de 4 a 6 coerentes com o cargo e as responsabilidades. No passo 7, avise que foram sugeridas.
- Se houver `horario`, inclua a linha "Horário de trabalho: …" antes do fechamento.
- Termine com a frase de fechamento do modelo.

**Regras:**
- Não invente benefícios, faixa salarial, requisitos, responsabilidades, ferramentas, horários nem nomes de times. Você pode reescrever e detalhar o que foi informado.
- Use linguagem inclusiva, como nos exemplos ("um(a)", "pessoa"). O cargo escrito literalmente no título não impede linguagem inclusiva no restante do texto.
- Nunca peça gênero, idade, aparência, estado civil, filhos ou religião (Lei 9.029/95).
- Não deixe placeholders: nada de `[...]` (exceto a tag do modelo no título, como `[PRESENCIAL]`), `{...}`, `_____`, `TODO` ou `XXX`.

## 5. Salvar

Salve em `vagas/AAAA-MM-DD-<slug>.md`, com a data de hoje. O slug é o cargo em minúsculas, sem acentos e com hífens no lugar dos espaços (ex.: `2026-11-04-analista-de-suporte-tecnico.md`). Se o arquivo já existir, acrescente `-2`, `-3` e assim por diante.

## 6. Validar a descrição

```bash
python -X utf8 -m vaga.validar vagas/<arquivo>.md --modelo .claude/skills/vaga/referencias/modelo-vaga.md --exigir "<cargo>" --exigir "<senioridade>" --exigir "<modelo_trabalho>" --exigir "<tipo_contratacao>"
```

Quando o modelo de trabalho não for Remoto, acrescente `--exigir "<local>"`. Se algum valor tiver `"`, `$` ou crase, coloque-o entre aspas simples em vez de duplas.

- Código de saída 0 (`OK`): siga para o passo 7.
- Código 1: corrija o texto conforme cada erro listado, salve e rode de novo, até 3 tentativas. Se ainda falhar, mostre os erros restantes ao usuário junto com a descrição.
- Código 2: problema de arquivo ou modelo. Mostre a mensagem ao usuário.

## 7. Entregar

Mostre ao usuário:
1. o caminho do arquivo salvo;
2. a ficha para a Sólides;
3. a **descrição pronta para colar** na Sólides, num bloco de código: títulos sem `## ` e itens com `• ` em vez de `- `, como nas vagas publicadas;
4. se for o caso, o aviso de que as soft skills foram sugeridas e devem ser revisadas.

Ofereça ajustes, como tom, tamanho ou ênfase em algum ponto. A cada ajuste, salve e repita o passo 6.
