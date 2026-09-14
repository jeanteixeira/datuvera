"use client"
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Badge, Card, DataTable, EmptyState, LoadingState, ErrorState, ActionLink, SectionHeader } from '../ui'
export type Source = { id:number; name:string; type:string; host:string; port:number; database:string }
export function useSources() {
  const [sources,setSources]=useState<Source[]>([])
  const [state,setState]=useState<'loading'|'success'|'error'>('loading')
  async function load(){setState('loading');try{const r=await fetch('/api/v1/sources');if(!r.ok)throw Error();setSources(await r.json());setState('success')}catch{setState('error')}}
  useEffect(()=>{load()},[])
  return {sources,state,load}
}
export default function SourceList({ sources, state, retry, title = 'Connected sources' }: { sources:Source[]; state:string; retry:()=>void; title?:string }) {
  return <Card><SectionHeader title={title} description="Open a source to explore schemas and datasets." />
    {state==='loading' && <LoadingState>Loading sources...</LoadingState>}
    {state==='error' && <ErrorState retry={retry}>We couldn’t load your data sources.</ErrorState>}
    {state==='success' && !sources.length && <EmptyState title="No data sources connected" description="Connect PostgreSQL to start profiling and validating your data." action={<ActionLink href="/sources/add">Add Data Source</ActionLink>}/>}
    {state==='success' && !!sources.length && <DataTable label="Data sources"><thead><tr><th>Name</th><th>Connector</th><th>Host</th><th>Database</th><th><span className="sr-only">Action</span></th></tr></thead><tbody>{sources.map(s=><tr key={s.id}><td className="cell-title"><Link href={`/sources/${s.id}`}>{s.name}</Link></td><td><Badge>PostgreSQL</Badge></td><td className="cell-mono">{s.host}:{s.port}</td><td className="cell-mono">{s.database}</td><td><Link className="text-link" href={`/sources/${s.id}`}>Open Source <span aria-hidden="true">→</span></Link></td></tr>)}</tbody></DataTable>}
  </Card>
}
