const BASE = import.meta.env.VITE_API_URL || '';
export const token = () => sessionStorage.getItem('tfpmds-token');
export class ApiError extends Error {constructor(public status:number, message:string){super(message)}}
export async function api<T>(path:string, options:RequestInit = {}):Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set('Content-Type','application/json');
  if (token()) headers.set('Authorization',`Bearer ${token()}`);
  let response:Response;
  try { response = await fetch(BASE + '/api' + path, {...options,headers}); }
  catch { throw new Error('Cannot reach TFPMDS. Check that the API is running on port 8000.'); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail=data.detail;
    const message=Array.isArray(detail) ? detail.map((d:{loc:string[];msg:string})=>`${d.loc.slice(1).join('.')}: ${d.msg}`).join('; ') : typeof detail==='object' ? detail.message : detail;
    throw new ApiError(response.status,message || 'Something went wrong. Please try again.');
  }
  return data as T;
}
export const post = <T,>(path:string,body:unknown={},key?:string) => api<T>(path,{method:'POST',body:JSON.stringify(body),headers:key ? {'Idempotency-Key':key} : {}});
export const patch = <T,>(path:string,body:unknown) => api<T>(path,{method:'PATCH',body:JSON.stringify(body)});
export const money = (value:number) => new Intl.NumberFormat('en-TZ',{maximumFractionDigits:0}).format(value);
export const human = (value:string) => value.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
export const date = (value:string) => new Date(value.endsWith('Z') || value.includes('+') || value.length===10 ? value : value+'Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});
