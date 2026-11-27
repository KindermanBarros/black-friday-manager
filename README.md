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
