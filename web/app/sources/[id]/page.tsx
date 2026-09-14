"use client"
import {useEffect,useRef,useState} from 'react'
import {useParams} from 'next/navigation'
import Link from 'next/link'
import type {Source} from '../../../components/sources/SourceList'
import {Badge,Button,Card,DataTable,EmptyState,ErrorState,LoadingState,PageHeader,SectionHeader} from '../../../components/ui'
export default function SourceDetail(){
 const id=String(useParams()?.id||'')
 const [src,setSrc]=useState<Source|null>(null)
 const [schemas,setSchemas]=useState<string[]>([])
 const [tables,setTables]=useState<{name:string}[]>([])
 const [selectedSchema,setSelectedSchema]=useState('')
 const [state,setState]=useState('loading')
 const [tableState,setTableState]=useState('idle')
 const [testState,setTestState]=useState('idle')
 const [tableRetry,setTableRetry]=useState(0)
 const request=useRef<AbortController|null>(null)
 async function load(){request.current?.abort();const controller=new AbortController();request.current=controller;setState('loading');try{const a=await fetch(`/api/v1/sources/${id}`,{signal:controller.signal});if(!a.ok)throw Error();setSrc(await a.json());const b=await fetch(`/api/v1/sources/${id}/schemas`,{signal:controller.signal});if(!b.ok)throw Error();const data=await b.json();setSchemas(data);setSelectedSchema(data.includes('public')?'public':data[0]||'');setState('success')}catch{if(!controller.signal.aborted)setState('error')}}
 useEffect(()=>{setSrc(null);setSchemas([]);setTables([]);setSelectedSchema('');setTestState('idle');load();return()=>request.current?.abort()},[id])
 useEffect(()=>{let active=true;if(!selectedSchema)return;setTableState('loading');fetch(`/api/v1/sources/${id}/schemas/${encodeURIComponent(selectedSchema)}/tables`).then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{if(active){setTables(data);setTableState('success')}}).catch(()=>{if(active)setTableState('error')});return()=>{active=false}},[id,selectedSchema,tableRetry])
 async function test(){setTestState('testing');try{const r=await fetch(`/api/v1/sources/${id}/test`,{method:'POST'});if(!r.ok)throw Error();setTestState('success')}catch{setTestState('error')}}
 return <><nav className="breadcrumb" aria-label="Breadcrumb"><Link href="/sources">Data Sources</Link><span>/</span><span>{src?.name||'Source'}</span></nav><PageHeader eyebrow="Source explorer" title={src?.name||'Data Source'} description={src?`${src.host}:${src.port}/${src.database}`:undefined} action={src&&<Button variant="secondary" onClick={test} disabled={testState==='testing'}>{testState==='testing'?'Testing...':'Test Connection'}</Button>}/>
 {src&&<div className="mb-6"><Badge>PostgreSQL</Badge></div>}{state==='loading'&&<LoadingState>Loading source and schemas...</LoadingState>}{state==='error'&&<ErrorState retry={load}>We couldn’t load this data source or its schemas.</ErrorState>}{testState==='success'&&<p className="mb-5" role="status"><Badge tone="success">Connection successful · tested now</Badge></p>}{testState==='error'&&<ErrorState retry={test}>Connection failed. Check the database availability and connection details.</ErrorState>}
 {state==='success'&&<div className="stack"><Card><SectionHeader title="Schemas" description="Select a schema to explore its tables."/>{!schemas.length?<EmptyState title="No schemas available" description="This source has no accessible schemas."/>:<div className="schema-list">{schemas.map(s=><Button variant="secondary" key={s} aria-pressed={selectedSchema===s} onClick={()=>setSelectedSchema(s)}>{s}</Button>)}</div>}</Card>{selectedSchema&&<Card><SectionHeader title="Tables" description={`${selectedSchema} schema`}/>{tableState==='loading'&&<LoadingState>Loading datasets...</LoadingState>}{tableState==='error'&&<ErrorState retry={()=>setTableRetry(n=>n+1)}>We couldn’t load tables for this schema.</ErrorState>}{tableState==='success'&&(tables.length?<DataTable label="Tables"><thead><tr><th>Table</th><th>Schema</th><th>Action</th></tr></thead><tbody>{tables.map(t=><tr key={t.name}><td className="cell-title cell-mono">{t.name}</td><td><Badge>{selectedSchema}</Badge></td><td><Link className="text-link" href={`/sources/${id}/datasets/${encodeURIComponent(selectedSchema)}/${encodeURIComponent(t.name)}`}>Explore <span aria-hidden="true">→</span></Link></td></tr>)}</tbody></DataTable>:<EmptyState title="No tables in this schema" description="Choose another schema to continue exploring."/>)}</Card>}</div>}</>
}
