/// <reference types="vite/client" />
// Production reads public GitHub directly; development retains local Vite feeds.
export function feedUrl(name:string):string {
  if(!/^(?:collector-(?:00|30)|pc-collector-(?:00|30)|phone-collector-00)\.json$/.test(name)) throw new Error('Invalid feed');
  return import.meta.env.DEV ? '/data/'+name : 'https://raw.githubusercontent.com/KindermanBarros/black-friday-manager/main/data/'+name;
}
