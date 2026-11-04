---
name: vaga
description: Gera descrições de vaga no padrão da Ikatec a partir de campos estruturados (cargo, senioridade, modelo de trabalho, local, contratação, responsabilidades, requisitos, diferenciais, benefícios, faixa salarial). Use quando pedirem para criar, escrever ou revisar uma descrição/anúncio de vaga.
---

# Descrição de vaga (Ikatec)

Você escreve descrições de vaga prontas para publicar, no modelo e no tom de voz da Ikatec. Todos os comandos rodam a partir da raiz do projeto.

## 1. Coletar os campos

| Campo | Obrigatório | Valores |
|---|---|---|
| cargo | sim | texto |
| senioridade | sim | Estágio, Júnior, Pleno, Sênior, Especialista, Liderança |
| modelo_trabalho | sim | Presencial, Híbrido, Remoto |
| local | sim, exceto Remoto | cidade/UF |
| tipo_contratacao | sim | CLT, PJ, Estágio |
| responsabilidades | sim (≥1) | lista |
| requisitos | sim (≥1) | lista |
| diferenciais | não | lista |
| beneficios | não | lista |
| faixa_salarial | não | texto |

Use o que o usuário já informou (inclusive na mensagem que chamou `/vaga`). Pergunte **de uma vez só** por todos os obrigatórios que faltarem, mostrando as opções válidas dos campos de lista fechada. Não pergunte pelos opcionais um a um; mencione numa linha que eles podem ser informados.

## 2. Validar a entrada

Escreva os dados em `vagas/.entrada.json`, com as chaves exatamente como na tabela e as listas como arrays JSON. Depois rode:

```bash
python -X utf8 -c "import json,sys; from dataclasses import asdict; from vaga.schema import validar_entrada; v,e=validar_entrada(json.load(open(sys.argv[1],encoding='utf-8'))); print(json.dumps(asdict(v) if v else {'erros':e}, ensure_ascii=False, indent=2))" vagas/.entrada.json
```

- Se aparecer `erros`, mostre-os ao usuário em linguagem simples, peça as correções e volte ao passo 1.
- Se não, use **os valores normalizados que o comando imprimiu** (ex.: "senior" vira "Sênior") daqui em diante. Apague `vagas/.entrada.json`.

## 3. Ler o padrão da empresa

Leia `.claude/skills/vaga/referencias/modelo-vaga.md` e todos os arquivos em `.claude/skills/vaga/referencias/exemplos/`.

- A descrição usa **exatamente** os títulos `## ` do modelo, na mesma ordem e com a mesma grafia.
- O tom, o tamanho e a formatação imitam os exemplos.

Se o modelo não existir, pare e peça ao usuário o modelo de vaga da Ikatec.

## 4. Escrever

- Não invente benefícios, faixa salarial, requisitos nem responsabilidades que não foram informados. Você pode reescrever o que foi informado com mais clareza.
- Nunca remova uma seção do modelo (o validador exige todas). Se faltarem dados para uma seção, use o texto institucional que o modelo traz para ela.
- Inclua no texto, escritos exatamente assim ao menos uma vez, o cargo, a senioridade, o modelo de trabalho e o tipo de contratação, além do local quando não for Remoto. O lugar natural é o título ou um resumo no topo, por exemplo: `Desenvolvedor Backend · Pleno · Híbrido (Florianópolis/SC) · CLT`. O cargo escrito literalmente no título não impede linguagem inclusiva no restante do texto.
- Use linguagem inclusiva, como nos exemplos. Nunca peça gênero, idade, aparência, estado civil, filhos ou religião (Lei 9.029/95).
- Não deixe placeholders: nada de `[...]`, `{...}`, `TODO` ou `XXX`.

## 5. Salvar

Salve em `vagas/AAAA-MM-DD-<slug>.md`, com a data de hoje. O slug é o cargo em minúsculas, sem acentos e com hífens no lugar dos espaços (ex.: `2026-11-04-desenvolvedor-backend.md`). Se o arquivo já existir, acrescente `-2`, `-3` e assim por diante.

## 6. Validar a descrição

```bash
python -X utf8 -m vaga.validar vagas/<arquivo>.md --modelo .claude/skills/vaga/referencias/modelo-vaga.md --exigir "<cargo>" --exigir "<senioridade>" --exigir "<modelo_trabalho>" --exigir "<tipo_contratacao>"
```

Quando o modelo de trabalho não for Remoto, acrescente `--exigir "<local>"`. Se algum valor tiver `"`, `$` ou crase, coloque-o entre aspas simples em vez de duplas.

- Código de saída 0 (`OK`): siga para o passo 7.
- Código 1: corrija o texto conforme cada erro listado, salve e rode de novo, até 3 tentativas. Se ainda falhar, mostre os erros restantes ao usuário junto com a descrição.
- Código 2: problema de arquivo ou modelo. Mostre a mensagem ao usuário.

## 7. Entregar

Mostre a descrição final completa e o caminho do arquivo salvo. Ofereça ajustes, como tom, tamanho ou ênfase em algum ponto; a cada ajuste, repita o passo 6.
