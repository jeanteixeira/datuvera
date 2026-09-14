"use client"
import {useState} from 'react'
import {useRouter} from 'next/navigation'
import {ActionLink,Badge,Button,Card,ErrorState,LoadingState,PageHeader,SectionHeader} from '../../../components/ui'
export default function AddSource(){
 const [form,setForm]=useState({name:'',host:'',port:'5432',database:'',username:'',password:''})
 const [status,setStatus]=useState<'idle'|'testing'|'tested'|'saving'|'error'>('idle')
 const [message,setMessage]=useState('')
 const [useDemo,setUseDemo]=useState(false)
 const [savedId,setSavedId]=useState<number|null>(null)
 const router=useRouter()
 const busy=status==='testing'||status==='saving'
 const payload=()=>({...form,type:'postgresql',port:Number(form.port)})
 async function test(){if(busy)return;setStatus('testing');setMessage('');try{const r=await fetch('/api/v1/sources/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});if(!r.ok)throw Error();setStatus('tested');setMessage('Connection successful')}catch{setStatus('error');setMessage('Connection failed. Check the connection details and try again.')}}
 async function save(){if(busy)return;setStatus('saving');setMessage('');try{let id=savedId;if(id===null){const r=await fetch('/api/v1/sources',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});if(!r.ok)throw Error('We couldn’t save this data source. Check the connection details and try again.');id=(await r.json()).id;setSavedId(id)}
 if(useDemo&&form.host==='datuvera-demo-db'&&form.database==='demo'){
 const root=`/api/v1/sources/${id}/quality-rules`,r=await fetch(root+'?schema=public&table=customers');if(!r.ok)throw Error('Source saved. Demo rules could not be configured. Save again to retry.');const existing=await r.json();
 for(const rule of [{column:'email',rule:'email_format',parameters:{}},{column:'state',rule:'allowed_values',parameters:{values:['AL','PE','BA','SP','RJ']}}]){if(existing.some((x:any)=>x.column===rule.column&&x.rule===rule.rule))continue;const r=await fetch(root,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:'public',table:'customers',...rule})});if(!r.ok)throw Error('Source saved. Demo rules could not be configured. Save again to retry.')}
 }
 router.push(`/sources/${id}`)
 }catch(e){setStatus('error');setMessage(e instanceof Error?e.message:'We couldn’t save this source. Try again.')}}
 return <><PageHeader eyebrow="Connections" title="Add Data Source" description="Connect a PostgreSQL database to start exploring your data." action={<ActionLink secondary href="/sources">Cancel</ActionLink>}/><div className="max-w-3xl"><div className="demo-panel"><div><h3>Explore with the demo</h3><p className="muted text-sm mt-1">Use the built-in PostgreSQL demo to explore Datuvera quickly.</p><p className="muted text-xs mt-2">Includes customers, orders and products, plus two editable quality rules.</p></div><Button variant="secondary" disabled={busy||savedId!==null} onClick={()=>{setUseDemo(true);setForm({name:'Datuvera Demo',host:'datuvera-demo-db',port:'5432',database:'demo',username:'demo',password:'demo'});setStatus('idle');setMessage('Demo settings loaded. Save to explore the dataset.')}}>Use demo database</Button></div>
 <Card><SectionHeader title="Connection Details" description="Credentials are used to connect to your database."/><form onSubmit={e=>{e.preventDefault();save()}}><div className="form-grid"><label className="field">Name<input required value={form.name} disabled={busy||savedId!==null} placeholder="e.g. Analytics warehouse" onChange={e=>{setForm({...form,name:e.target.value});setStatus('idle');setMessage('')}}/></label><label className="field">Type<select disabled aria-label="Type"><option>PostgreSQL</option></select></label>{(['host','port','database','username','password'] as const).map(key=><label className="field" key={key}><span>{key[0].toUpperCase()+key.slice(1)}</span><input required={key!=='password'} type={key==='password'?'password':key==='port'?'number':'text'} min={key==='port'?1:undefined} max={key==='port'?65535:undefined} autoComplete={key==='password'?'new-password':key==='username'?'username':'off'} disabled={busy||savedId!==null} value={form[key]} placeholder={key==='host'?'db.example.com':undefined} onChange={e=>{setForm({...form,[key]:e.target.value});setStatus('idle');setMessage('')}}/></label>)}</div>
 {status==='error'&&<ErrorState>{message}</ErrorState>}{status==='tested'&&<p role="status" className="mt-5"><Badge tone="success">Connection successful</Badge></p>}{status==='idle'&&message&&<p role="status" className="muted text-sm mt-5">{message}</p>}{busy&&<LoadingState>{status==='testing'?'Testing connection...':'Saving source...'}</LoadingState>}
 <div className="form-actions"><Button type="button" variant="secondary" disabled={busy} onClick={test}>Test Connection</Button><Button disabled={busy}>{status==='saving'?'Saving...':'Save Source'}</Button></div></form></Card></div></>
}
