# Black Friday Manager

React + TypeScript + Vite + Tailwind CSS + Recharts + Lucide.

## Desenvolvimento

```sh
npm install
npm run dev
npm run build
```

## Vercel
Importe o repositório e utilize Vite, npm run build, dist. O build copia os arquivos de dados para dist/data. Cada commit dispara uma publicação quando a integração Git está ativa.

## Coletores
Leia AGENTS.md. Os arquivos data/collector-00.json e data/collector-30.json permanecem na raiz para preservar o contrato das automações. Cada execução adiciona um snapshot com ofertas verificadas. Não inclua segredos nem informações pessoais. A interface recarrega os dados a cada minuto; novos dados chegam após a publicação da Vercel.

## Coletores gratuitos (GitHub Actions)

O workflow `.github/workflows/collect.yml` executa os cinco feeds nos slots originais em runners públicos padrão, sem credenciais comerciais. A pesquisa usa links históricos, buscas internas e dados estruturados dos varejistas; o SmartTracker (MIT) fornece seletores complementares. O workflow também pode ser disparado manualmente em Actions → Free price collectors → Run workflow. Execuções automáticas encerram após 28/11/2026 (Manaus); disparos manuais continuam disponíveis. A publicação usa GITHUB_TOKEN de escopo limitado e retry com SHA, inclusive em falhas de pesquisa. Resultados e bloqueios aparecem no resumo da execução. Nenhum cupom não confirmado é aplicado. A verificação conservadora pode retornar zero ofertas por bloqueios ou falta de dados estruturados; não há garantia de cobertura. Não copie scrapers sem licença.

Em produção, os três dashboards consultam os JSON públicos diretamente do GitHub; a Vercel ignora builds sem mudanças de frontend. Em desenvolvimento, continuam lendo /data local. O cache do GitHub pode atrasar a atualização em alguns minutos. Desative as automações antigas quando o novo workflow estiver validado para evitar duplicação de coletas.
