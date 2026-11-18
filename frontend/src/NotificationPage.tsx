import {useState} from 'react';
import {Bell,CheckCheck,MessageSquare} from 'lucide-react';
import {date,human,post} from './api';
import {Empty,ErrorBox,Loading,PageTitle,useData} from './components';
import type {Notice} from './types';

export function Notifications(){const {data,error,loading,reload}=useData<Notice[]>('/notifications');const [actionError,setActionError]=useState(''),[busy,setBusy]=useState(false);async function read(id?:number){setBusy(true);setActionError('');try{await post(id?`/notifications/${id}/read`:'/notifications/read-all');await reload();}catch(e){setActionError((e as Error).message);}finally{setBusy(false);}}
 return <><PageTitle eyebrow="STAY CONNECTED" title="Notification center" description="Updates from your account, orders, payments and deliveries." actions={<button disabled={busy||!data?.some(n=>!n.read)} className="btn outline" onClick={()=>read()}><CheckCheck size={16}/>Mark all as read</button>}/><ErrorBox message={error||actionError}/>{loading?<Loading/>:!data?.length?<Empty>Your notifications will appear here as you use TFPMDS.</Empty>:<div className="stack">{data.map(n=><article className={`panel notice ${n.read?'read':'unread'}`} key={n.id}><div className="notice-icon"><Bell size={18}/></div><div><div className="row between"><strong>{human(n.kind)}</strong><small>{date(n.created_at)}</small></div><p>{n.message}</p><div className="row wrap"><span className="sms-caption"><MessageSquare size={12}/>SMS simulated · {n.sms_reference}</span>{!n.read&&<button disabled={busy} className="btn small ghost" onClick={()=>read(n.id)}>Mark as read</button>}</div></div></article>)}</div>}</>
}
