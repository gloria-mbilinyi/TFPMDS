import {useEffect,useState,type ReactNode} from 'react';
import {AlertCircle,ArrowRight,Check,MapPin,Package,RefreshCw,Sprout} from 'lucide-react';
import {Link} from 'react-router-dom';
import {api,money,human} from './api';
import type {Produce} from './types';

export function useData<T>(path:string) {
  const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
  async function reload(){setLoading(true);setError('');try{setData(await api<T>(path));}catch(e){setError((e as Error).message);}finally{setLoading(false);}}
  useEffect(()=>{let current=true;setLoading(true);setError('');api<T>(path).then(d=>{if(current)setData(d)}).catch(e=>{if(current)setError(e.message)}).finally(()=>{if(current)setLoading(false)});return()=>{current=false}},[path]);
  return {data,error,loading,reload};
}
export function ErrorBox({message}:{message:string}) {return message ? <div role="alert" className="error"><AlertCircle size={18}/>{message}</div> : null}
export function Loading(){return <div role="status" className="empty"><RefreshCw className="spin" size={24}/> Loading your workspace…</div>}
export function Empty({children}:{children:ReactNode}){return <div className="empty"><Package size={30}/>{children}</div>}
export function Badge({status}:{status:string}){return <span className={`badge ${['approved','successful','completed','delivered','active','paid'].includes(status)?'good':['rejected','failed','cancelled','delivery_failed','returned'].includes(status)?'bad':'neutral'}`}><i/>{human(status)}</span>}
export function PageTitle({eyebrow,title,description,actions}:{eyebrow?:string;title:string;description?:string;actions?:ReactNode}){return <div className="page-title"><div>{eyebrow&&<p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description&&<p className="muted">{description}</p>}</div>{actions&&<div className="actions">{actions}</div>}</div>}
export function Metric({label,value,note,icon}:{label:string;value:ReactNode;note:string;icon:ReactNode}){return <div className="metric"><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><strong>{value}</strong><small>{note}</small></div>}
export function CropArt({crop,large=false}:{crop:string;large?:boolean}) {
  const palette:Record<string,string>={Rice:'#c8ae6d',Maize:'#dbb947',Beans:'#944f48',Potatoes:'#c99c74',Tomatoes:'#d55e49',Avocado:'#416e38',Sunflower:'#cbb341'};
  const color=palette[crop]||'#7b9c62';
  return <div className={`crop-art crop-${crop.toLowerCase()} ${large?'large':''}`}><svg viewBox="0 0 360 180" aria-label={`${crop} illustration`} role="img"><ellipse cx="180" cy="161" rx="106" ry="12" fill="#133e2412"/>{[0,1,2].map(i=><g key={i} transform={`translate(${80+i*75} ${35+(i%2)*16}) rotate(${i*14-14} 35 55)`}>{['Rice','Maize','Sunflower'].includes(crop)?<><path d="M40 119V30M40 65Q8 42 15 29M40 86Q65 67 70 37" fill="none" stroke="#69804d" strokeWidth="5"/>{[0,1,2,3,4].map(j=><ellipse key={j} cx={j%2?29:48} cy={26+j*12} rx="9" ry="15" transform={`rotate(${j%2?-45:45} ${j%2?29:48} ${26+j*12})`} fill={color}/>)}</>:<><ellipse cx="40" cy="75" rx={crop==='Beans'?28:38} ry={crop==='Avocado'?54:37} fill={color}/><ellipse cx="29" cy="63" rx="9" ry="15" fill="#ffffff28"/><path d="M40 39q-22-27-29-9 24 16 29 9 22-32 30-14-17 20-30 14" fill="#547347"/>{crop==='Avocado'&&<><ellipse cx="40" cy="80" rx="25" ry="35" fill="#c4ce80"/><circle cx="40" cy="90" r="15" fill="#906744"/></>}</>}</g>)}</svg><span className="art-label"><Sprout size={12}/> Tanzania grown</span></div>
}
export function ProduceCard({produce}:{produce:Produce}){return <article className="produce-card"><Link to={`/marketplace/${produce.id}`} className="art-link"><CropArt crop={produce.crop}/><span className="card-category">{produce.crop}</span></Link><div className="produce-body"><div className="row between"><span className="location"><MapPin size={13}/>{produce.region}</span><span className="stock"><i/>In stock</span></div><Link to={`/marketplace/${produce.id}`} className="produce-name">{produce.name}</Link><p className="farmer-name">{produce.farmer_name}</p><div className="price-row"><div><strong>TZS {money(produce.price_tzs)}</strong><span> / kg</span></div><span>{money(produce.available_kg)} kg available</span></div><Link to={`/marketplace/${produce.id}`} className="card-action">View produce <ArrowRight size={16}/></Link></div></article>}
export function Success({children}:{children:ReactNode}){return <div role="status" className="success"><Check size={18}/>{children}</div>}
