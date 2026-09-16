export function safeOsvUrl(value:string):string|null{ try{ const url=new URL(value); if(url.protocol!=='https:'||url.hostname.toLowerCase()!=='osv.dev') return null; return url.toString(); }catch{return null;} }
export function normalizeEnumLabel(value:string):string{ const part=value.includes('.')?(value.split('.').at(-1)??value):value; return part.replaceAll('_',' '); }
