---
name: vaga
description: Gera descrições de vaga no padrão da Ikatec a partir de campos estruturados (cargo, senioridade, modelo de trabalho, local, contratação, responsabilidades, requisitos, diferenciais, soft skills, benefícios, faixa salarial). Use quando pedirem para criar, escrever ou revisar uma descrição/anúncio de vaga.
---

# Descrição de vaga (Ikatec)

Você escreve descrições de vaga prontas para publicar na Sólides (https://ikatec.vagas.solides.com.br/), no modelo e no tom de voz da Ikatec. Todos os comandos rodam a partir da raiz do projeto.

O resultado tem duas partes:
- **Ficha para a Sólides:** local, modelo de trabalho, contratação, senioridade, jornada e benefícios. Na Sólides esses dados vão em campos próprios do formulário, não no texto.
- **Descrição:** o corpo do anúncio, que segue `referencias/modelo-vaga.md`.

## Outros pedidos

- **Revisar uma vaga publicada** ("/vaga revisar <link ou id da Sólides>"): rode `python -X utf8 -m vaga.solides revisar "<link ou id>"`. Mostre a vaga e o resultado da validação. Se houver problemas, proponha o texto corrigido no formato do passo 7, sem salvar nada a menos que o usuário peça. Código de saída 2 significa que a vaga não está aberta ou que a Sólides não respondeu: mostre a mensagem.
- **Atualizar as referências** ("/vaga atualizar exemplos"): rode `python -X utf8 -m vaga.solides sincronizar`. O comando baixa as vagas abertas, regrava os exemplos `solides-*.md` e o catálogo `referencias/beneficios.md`. Mostre o resumo que ele imprimir. As vagas que saíram do ar são movidas para `referencias/historico/`.
- **Importar vagas antigas** ("/vaga importar <links ou ids>"): rode `python -X utf8 -m vaga.solides importar <ids ou links> --desde AAAA-MM-DD`. As vagas, inclusive as encerradas, vão para `referencias/historico/` e alimentam as sugestões do passo 1b. Os IDs aparecem nos links do painel da Sólides (`/selective-process/<id>`).

Nos outros casos, siga os passos abaixo para criar uma vaga.

## 0. Atualizar as referências (sempre, antes de tudo)

Antes de coletar os campos, rode, sem comentar com o usuário:

```bash
python -X utf8 -m vaga.solides sincronizar
```

O comando traz as vagas abertas agora na Sólides para os exemplos, atualiza o catálogo de benefícios e move para o histórico as vagas que saíram do ar. Assim, as sugestões do passo 1b partem sempre da vaga mais recente.

- **Código 0:** siga em frente sem mencionar nada.
- **Código 1 ou 2** (Sólides fora do ar, sem internet ou nenhuma vaga válida): o comando não apaga nada. Siga com as referências que já estão salvas e avise numa linha: "Não consegui atualizar com a Sólides agora; usei as vagas salvas até a última atualização."
- Rode **uma vez por conversa**: se já rodou nesta conversa, não repita.

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

Use o que o usuário já informou, inclusive na mensagem que chamou `/vaga`.

**Se faltar algum obrigatório, ofereça o formulário:**
- **No app do Claude** (quando a ferramenta `show_widget` existir): carregue `read_me` com o módulo `elicitation`, leia `.claude/skills/vaga/referencias/formulario.html` e passe o conteúdo, sem alterar, como `widget_code` do `show_widget`. Antes do formulário, escreva só uma linha: "Preencha os campos abaixo e clique em Gerar vaga." Não repita os campos em texto.
  - A resposta chega na mensagem seguinte, numa linha como `Detalhes da vaga — Cargo: … · Senioridade: … · Responsabilidades: … / …`. Textos longos aparecem depois de `--- Full content ---`.
  - Nos campos de lista (responsabilidades, requisitos, diferenciais, soft skills, benefícios), cada linha, ou cada trecho separado por ` / `, é um item.
  - `Observacoes` pode trazer horário, faixa salarial e área: distribua o que houver em `horario`, `faixa_salarial` e `area`.
  - Se aparecer "Skipped the form", peça os dados em texto, como no item abaixo.
- **No terminal ou sem `show_widget`**: mande de uma vez só um bloco para o usuário copiar e preencher, só com os campos que faltam, na ordem da tabela e com as opções dos campos de lista fechada, por exemplo `Senioridade (Estágio, Júnior, Pleno, Sênior, Especialista, Liderança):`. Diga numa linha que os opcionais podem ser informados.

Se o usuário já trouxe todos os obrigatórios, não mostre o formulário.

### 1b. Sugerir responsabilidades, requisitos e soft skills

Se, depois do passo anterior, **responsabilidades, requisitos ou soft skills** continuarem vazios e você já souber o cargo, rode:

```bash
python -X utf8 -m vaga.base sugerir --cargo "<cargo>" --senioridade "<senioridade>"
```

O comando busca nas vagas da Ikatec (`referencias/historico/` e `referencias/exemplos/`) a **vaga mais recente do mesmo cargo**, que é a fonte principal porque cada vaga nova é aberta com as informações mais atualizadas. Ele prefere o mesmo nível; seções obrigatórias que faltarem vêm da vaga anterior do mesmo cargo, e Diferenciais vem só da vaga principal.

- **Código 0 (`"encontrado": true`):** sugira só as seções que o recrutador **não** informou. Nunca troque o que ele escreveu.
  - **No app:** leia `referencias/formulario-sugestoes.html`, remova os grupos das seções que já foram informadas ou que não vieram na sugestão, e troque:
    - `{{RESPONSABILIDADES}}`, `{{REQUISITOS}}`, `{{DIFERENCIAIS}}` e `{{SOFT_SKILLS}}` pelos itens, um por linha, com `&`, `<` e `>` escapados;
    - `{{ORIGEM_…}}` por "Da vaga <título> (<mês/ano>)", acrescentando ", nível <senioridade>" quando `nivel_diferente` for true.
    Mostre com `show_widget` (o `read_me` de `elicitation` já foi carregado no passo 1; se não foi, carregue). Se vier "Skipped the form" ("Usar como está"), use as sugestões sem mudanças.
  - **No terminal:** mostre as seções sugeridas como listas, com a origem de cada uma, e pergunte numa linha se pode usar assim ou o que mudar.
  - Se `nivel_diferente` for true, avise que a vaga de referência é de outro nível e que vale ajustar o nível de exigência.
- **Código 1 (`"encontrado": false`):** não há vaga parecida. Mostre os `parecidos`, se houver, e pergunte se é um desses cargos. Senão, sugira itens com base no seu conhecimento, marcados como **sugestão genérica**, para o recrutador revisar.

As sugestões são o ponto de partida. No passo 4 você pode reescrever e detalhar os itens no tom dos exemplos, sem acrescentar fatos novos.

O recrutador costuma mandar poucos tópicos. Você pode desenvolver e detalhar o que ele informou, no nível de detalhe dos exemplos, sem acrescentar fatos novos (ver passo 4).

## 2. Validar a entrada

Escreva os dados em `vagas/.entrada.json`, com as chaves exatamente como na tabela e as listas como arrays JSON. Depois rode:

```bash
python -X utf8 -c "import json,sys; from dataclasses import asdict; from vaga.schema import validar_entrada; v,e=validar_entrada(json.load(open(sys.argv[1],encoding='utf-8'))); print(json.dumps(asdict(v) if v else {'erros':e}, ensure_ascii=False, indent=2))" vagas/.entrada.json
```

- Se aparecer `erros`, mostre-os ao usuário em linguagem simples, peça as correções e volte ao passo 1.
- Se não, use **os valores normalizados que o comando imprimiu** (ex.: "junior" vira "Júnior") daqui em diante. `jornada`, `horario` e `area` não passam pelo validador; use-os como vieram. Apague `vagas/.entrada.json`.

## 3. Ler o padrão da empresa

Leia `.claude/skills/vaga/referencias/modelo-vaga.md`, `.claude/skills/vaga/referencias/beneficios.md` e todos os arquivos em `.claude/skills/vaga/referencias/exemplos/`. Os arquivos `solides-*.md` são as vagas abertas na Sólides, sincronizadas automaticamente.

**Benefícios:** se o recrutador não informou `beneficios`, sugira o pacote do tipo de contratação que está em `beneficios.md`, com os itens oferecidos em pelo menos metade das vagas daquele tipo. Use os nomes exatamente como aparecem lá, que são os nomes do formulário da Sólides. Na ficha, marque a linha como `- Benefícios (sugeridos, confirme): …`. Se o tipo de contratação não aparecer em `beneficios.md`, omita a linha.

- Use **exatamente** os títulos `## ` do modelo, na mesma ordem e com a mesma grafia, sem o marcador "(opcional)".
- Imite o tom, o tamanho e a formatação dos exemplos: 1 a 3 parágrafos de introdução, listas de tópicos e a frase de fechamento.

Se o modelo não existir, pare e peça ao usuário o modelo de vaga da Ikatec.

## 4. Escrever

**Título** (linha `# `), no estilo da Sólides: `<Cargo> <sigla da senioridade> [<MODELO>]`. Exemplo: `Analista de Suporte Técnico JR [PRESENCIAL]`. As siglas são: Estágio → ESTÁGIO, Júnior → JR, Pleno → PL, Sênior → SR; Especialista e Liderança vão por extenso. As tags são `[PRESENCIAL]`, `[HÍBRIDO]` ou `[REMOTO]`.

**Ficha para a Sólides**, logo abaixo do título, separada da descrição por `---`. Siga o formato dos exemplos:
```
**Ficha para a Sólides**
- Local: <local ou "Remoto">
- Modelo de trabalho: <modelo_trabalho>
- Contratação: <tipo_contratacao>
- Senioridade: <senioridade>
- Jornada: <jornada>
- Faixa salarial: <faixa_salarial>
- Benefícios: <itens separados por "; ">
```
Omita as linhas de Jornada, Faixa salarial e Benefícios quando o campo não foi informado. Não copie a linha "> Vaga publicada" dos exemplos; ela existe só nas referências.

**Descrição:**
- A introdução preenche as lacunas do modelo: "A Ikatec está em busca de um(a) <Cargo>. Se você <perfil da pessoa, a partir dos requisitos e soft skills>, queremos te conhecer!". Na introdução, use a forma inclusiva do cargo (ex.: "Desenvolvedor(a) Backend", "Assessor(a) Executivo(a)"). Pode haver um segundo parágrafo sobre o papel ou a área, como nos exemplos.
- Seções na ordem do modelo. Itens com a primeira letra maiúscula e terminados em `;`, com `.` no último item.
- **Diferenciais** é opcional: se não for informado, omita a seção inteira.
- **Soft Skills** é obrigatória: se não for informada, sugira de 4 a 6 coerentes com o cargo e as responsabilidades. No passo 7, avise que foram sugeridas.
- Se houver `horario`, inclua a linha "Horário de trabalho: …" antes do fechamento.
- Termine com a frase de fechamento do modelo.

**Regras:**
- Não invente benefícios, faixa salarial, requisitos, responsabilidades, ferramentas, horários nem nomes de times. Benefícios só podem vir do recrutador ou do catálogo `beneficios.md` (marcados como sugeridos). Você pode reescrever e detalhar o que foi informado.
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
2. o título e a ficha para a Sólides;
3. a **descrição pronta para colar** no campo "Descrição" da Sólides, num bloco de código: tudo o que vem depois do `---`, com os títulos sem `## `, os itens com `• ` em vez de `- ` e as linhas em branco mantidas. O título e a ficha ficam fora do bloco, porque vão em campos próprios da Sólides;
4. se for o caso, o aviso de que as soft skills e/ou os benefícios foram sugeridos e devem ser revisados.

Ofereça ajustes, como tom, tamanho ou ênfase em algum ponto. A cada ajuste, salve e repita o passo 6.
