# Roadmap — Integrações do `/vaga`

**Data:** 2026-11-04 · **Status:** Fase 1 implementada (branch `feat/fase1-solides`); Fases 2–4 propostas

Objetivo: tirar trabalho manual do recrutador, de modo que a vaga já nasça consistente com (1) o que a Ikatec publica na Sólides e (2) o Mapa de Carreira oficial.

## O que já sabemos

### Página de carreiras (Sólides)
- A página `ikatec.vagas.solides.com.br` carrega as vagas de uma **API pública, sem login**:
  - `GET https://apigw.solides.com.br/jobs/v3/companies/ikatec/vacancies?take=12&page=1`
- Cada vaga vem com `title`, `description` (HTML), `seniority`, `recruitmentContractType`, `jobType` (presencial/…), `homeOffice`, `city`/`state`, `benefits`, `shift`, `education`, `occupationAreas`, `salary` e `createdAt`.
- Ressalva: a API **não é documentada**. É a mesma que o site usa e pode mudar sem aviso, então toda integração precisa de um plano B (os exemplos salvos no repositório continuam valendo).
- **Publicar** vagas exige acesso autenticado ao painel da Sólides. Não sabemos se a Sólides oferece uma API de escrita para clientes; isso precisa ser confirmado com a Sólides.

### Mapa de Carreira (Loop)
- O arquivo é `Mapa de Carreira - IKATEC.loop`, num workspace do Loop.
- O conector do Microsoft 365 **não consegue ler arquivos do Loop** (403): o Loop guarda os dados num contêiner próprio, fora do SharePoint comum.
- Pelo trecho que a busca mostrou, o mapa descreve cargos e níveis. Ainda não vimos a estrutura completa (trilhas, competências por nível, faixas).

## Fases

Cada fase entrega algo usável sozinha. A ordem vai do menor risco e de quem não depende de ninguém até o que depende de terceiros.

### Fase 1 — Sólides como fonte de referência ✅ implementada
1. **`python -m vaga.solides sincronizar`**: baixa as vagas publicadas, converte o HTML para o formato dos exemplos (ficha + descrição) e atualiza `referencias/exemplos/`. Com isso, o tom de voz acompanha o que o RH publica.
2. **Catálogo de benefícios por modelo de contratação**: extrai das vagas publicadas o pacote padrão (CLT presencial, PJ…). A skill **sugere** o pacote e o recrutador confirma, sem precisar digitar a lista toda vez.
3. **Vocabulário da Sólides na ficha**: senioridade, contratação, jornada e área escritas como aparecem no formulário (ex.: "Junior", "Integral", "Tecnologia"), para facilitar o preenchimento.
4. **`/vaga revisar <id ou link da Sólides>`**: baixa uma vaga já publicada, roda o validador (termos discriminatórios, estrutura, placeholders) e sugere melhorias.

Entrega: exemplos e benefícios sempre atualizados e revisão das vagas que já estão no ar. Tudo testável com respostas da API salvas nos testes.

**Como ficou:**
- `python -X utf8 -m vaga.solides sincronizar`: regrava `referencias/exemplos/solides-*.md` (só vagas que passam no validador; remove as que saíram do ar e preserva os exemplos escritos à mão) e `referencias/beneficios.md`.
- `python -X utf8 -m vaga.solides revisar <link ou id>`: mostra a vaga publicada já convertida, com o resultado do validador.
- Na skill: "/vaga revisar <link>", "/vaga atualizar exemplos" e sugestão de benefícios a partir do catálogo, marcada como "sugeridos, confirme".
- Vocabulário: os benefícios usam os nomes exatos da Sólides; a senioridade da Sólides ("Junior", "Senior") é convertida para a da skill ("Júnior", "Sênior").
- Limite descoberto: a API aceita no máximo `take=25` por página. O download percorre todas as páginas.

### Fase 1.5 — Sugestões de responsabilidades, requisitos e soft skills ✅ parte Sólides implementada

Ideia: com o cargo e a senioridade em mãos, a skill **propõe** responsabilidades, requisitos e soft skills a partir de uma base de cargos da Ikatec. O recrutador revisa, edita e confirma.

**Fontes, em ordem de prioridade:**
1. **Descrições de cargo do Loop** (fonte oficial): mesmo bloqueio do Mapa de Carreira. O conector não lê o Loop, então é preciso exportar o conteúdo. Pode ser feito junto com a Fase 2.
2. **Vagas da Sólides:**
   - **abertas:** já sincronizadas na Fase 1;
   - **encerradas:** a API devolve vagas encerradas por ID (`GET /jobs/v3/vacancies/{id}`, com status "concluido" ou "cancelado"), mas **não lista** quais são da Ikatec. Os IDs ou links precisam vir do painel da Sólides. Novo comando: `python -m vaga.solides importar <ids…>`. Não fazemos varredura de IDs, porque traria dados de outras empresas;
   - **daqui para a frente:** em vez de apagar a vaga que sai do ar, o `sincronizar` passa a guardá-la em `referencias/historico/`, e o histórico cresce sozinho.
3. **Conhecimento geral do Claude:** só como último recurso, sempre marcado como "sugestão genérica".

**Como funcionaria:**
- `referencias/cargos/`: base estruturada (cargo → nível → responsabilidades, requisitos, soft skills), montada a partir das fontes 1 e 2. Só entram vagas que passam no validador, para que texto antigo com termo discriminatório não seja reaproveitado.
- `python -m vaga.base sugerir --cargo "Analista de Suporte" --senioridade Pleno`: busca o cargo mais parecido (tolera variações como "Analista de Suporte Técnico" ou "Suporte N2"). Prefere o mesmo nível e, se não houver, um nível vizinho. Devolve os itens com a **origem** de cada um. É testável como o resto do código.
- Na skill, um fluxo em duas etapas:
  1. formulário curto: cargo, senioridade, modelo, local e contratação;
  2. segundo formulário com responsabilidades, requisitos e soft skills **já preenchidos** com as sugestões, para o recrutador editar. A origem aparece como "(descrição de cargo)", "(vaga de 03/2025)" ou "(sugestão genérica)".

**Como ficou (parte Sólides):**
- 93 vagas criadas em 2025–2026 importadas para `referencias/historico/`. Os IDs foram coletados do painel (aba "Concluída"), só leitura.
- O histórico usa um critério mais leve que o das vagas novas: barra termos discriminatórios e exige Responsabilidades ou Requisitos reconhecidos. Mais títulos de seção são reconhecidos ("[Atividades]", "Principais responsabilidades", "[Hard skills]"…).
- `python -m vaga.base sugerir --cargo … --senioridade …`: a vaga mais recente do mesmo cargo é a fonte principal, com preferência pelo mesmo nível. Seções obrigatórias que faltarem vêm da vaga anterior do mesmo cargo; Diferenciais, só da principal.
- Na skill: passo 1b, com um segundo formulário já preenchido pelas sugestões e a origem de cada seção.
- Pendente: descrições de cargo do Loop (depende da exportação).

**Decisões pendentes:**
- O RH consegue exportar as descrições de cargo do Loop (Word ou Markdown)?
- Alguém consegue tirar do painel da Sólides a lista de vagas encerradas (links ou IDs)?
- O fluxo em duas etapas, com sugestões pré-preenchidas, faz sentido para o recrutador?

### Fase 2 — Mapa de Carreira como fonte de conteúdo
**Pré-requisito:** exportar o mapa do Loop. Um dos caminhos:
- (a) **Exportar e versionar** *(recomendado para começar)*: copiar a página do Loop para um `.docx` ou Markdown, e eu converto para `referencias/mapa-de-carreira.yaml` (trilha → cargo → nível → responsabilidades, competências técnicas e comportamentais). É simples e testável, mas precisa ser exportado de novo quando o mapa mudar.
- (b) **Mover o mapa para uma lista do SharePoint ou um Excel**, que o conector consegue ler. Fica sempre atualizado, mas exige acesso ao Microsoft 365 em cada máquina que usar a skill.

Com o mapa estruturado:
1. **Pré-preenchimento**: "/vaga Analista de Suporte JR" já traz do mapa as responsabilidades, os requisitos e as soft skills daquele cargo e nível. O recrutador só ajusta, e a skill avisa o que veio do mapa.
2. **Nomenclatura oficial**: avisa quando o cargo ou o nível não existe no mapa (ex.: "Dev Back" → "Desenvolvedor Backend").
3. **Validação cruzada**: alerta quando um requisito pedido está acima do nível (ex.: exigir liderança técnica numa vaga JR).

Pontos de atenção: se o mapa tiver **faixas salariais**, decidir se elas podem aparecer na ficha. O mapa é interno, e expor um trecho dele numa vaga pública é uma decisão do RH.

### Fase 3 — Publicação na Sólides (depende da Sólides)
- **3a.** Confirmar com a Sólides se existe uma API de criação de vagas para clientes (token e permissões).
- **3b.** Se existir: `python -m vaga.solides publicar vagas/<arquivo>.md` cria a vaga **como rascunho**. Publicar fica com o recrutador.
- **3c.** Se não existir: preenchimento assistido no navegador, em que o Claude preenche o formulário da Sólides e o recrutador revisa e clica em publicar. Nunca publicar sem confirmação.

### Fase 4 — Extras (opcionais)
- Mostrar na descrição a trilha de crescimento do cargo, a partir do mapa ("próximos passos: Pleno → Sênior"), se o RH quiser usar isso como atrativo.
- Painel com as vagas abertas, a data de abertura e se cada uma passa no validador.

## Decisões pendentes
1. Começar pela Fase 1?
2. Mapa de Carreira: exportar e versionar (a) ou mover para uma lista ou Excel (b)?
3. O mapa tem faixas salariais? Elas podem aparecer nas vagas?
4. Quem pode falar com a Sólides sobre a API de publicação (Fase 3a)?
