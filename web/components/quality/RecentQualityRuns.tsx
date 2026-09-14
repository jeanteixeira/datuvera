"use client"
import {useEffect,useRef,useState} from 'react'
import {Badge,Button,Card,DataTable,EmptyState,ErrorState,LoadingState,SectionHeader,ruleLabel} from '../ui'
import {QualityMetrics} from '../datasets/ProfilePanels'
import type {Quality} from '../datasets/types'

type Run = {id:number;source_id:number;schema:string;table:string;overall_score:number;completeness_score:number|null;uniqueness_score:number|null;validity_score:number|null;created_at:string;checks?:Quality['checks']}
export default function RecentQualityRuns({sourceId,schema,table,revision}:{sourceId:string;schema:string;table:string;revision:number}){
 const [runs,setRuns]=useState<Run[]>([])
 const [state,setState]=useState('loading')
 const [selected,setSelected]=useState<Run|null>(null)
 const [detailState,setDetailState]=useState('idle')
 const [retry,setRetry]=useState(0)
 const detailRequest=useRef<AbortController|null>(null)
 const root=`/api/v1/sources/${sourceId}/quality-runs`
 useEffect(()=>{
  detailRequest.current?.abort();const controller=new AbortController();setState('loading');setSelected(null);setDetailState('idle')
  fetch(`${root}?${new URLSearchParams({schema,table,limit:'5',offset:'0'})}`,{signal:controller.signal})
   .then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{setRuns(data);setState('success')})
   .catch(()=>{if(!controller.signal.aborted)setState('error')})
  return()=>{controller.abort();detailRequest.current?.abort()}
 },[sourceId,schema,table,revision,retry])
 async function select(id:number){detailRequest.current?.abort();const controller=new AbortController();detailRequest.current=controller;setSelected(null);setDetailState('loading');try{const r=await fetch(`${root}/${id}`,{signal:controller.signal});if(!r.ok)throw Error();setSelected(await r.json());setDetailState('success')}catch{if(!controller.signal.aborted)setDetailState('error')}}
 return <Card><SectionHeader title="Recent Quality Runs" description="The five most recent persisted snapshots. History remains unchanged when rules or data change."/>
 {state==='loading'&&<LoadingState>Loading quality runs...</LoadingState>}{state==='error'&&<ErrorState retry={()=>setRetry(n=>n+1)}>We couldn’t load quality run history.</ErrorState>}
 {state==='success'&&(runs.length?<DataTable label="Recent quality runs"><thead><tr><th>Executed At</th><th>Score</th><th>Completeness</th><th>Uniqueness</th><th>Validity</th><th>Action</th></tr></thead><tbody>{runs.map(run=><tr key={run.id}><td>{new Date(run.created_at).toLocaleString('en-US')}<p className="muted text-xs">Run #{run.id}</p></td><td className="cell-title">{run.overall_score.toFixed(2)}</td><td>{run.completeness_score?.toFixed(2)??'N/A'}</td><td>{run.uniqueness_score?.toFixed(2)??'N/A'}</td><td>{run.validity_score?.toFixed(2)??'N/A'}</td><td><Button variant="secondary" disabled={detailState==='loading'} aria-label={`View quality run ${run.id}`} onClick={()=>select(run.id)}>View snapshot</Button></td></tr>)}</tbody></DataTable>:<EmptyState title="No quality runs yet" description="Run quality checks to start building dataset history."/>)}
 {detailState==='loading'&&<LoadingState>Loading snapshot...</LoadingState>}{detailState==='error'&&<ErrorState>We couldn’t load this quality run. Select it again to retry.</ErrorState>}
 {selected&&<div className="inline-panel"><SectionHeader title={`Historical Snapshot · Run #${selected.id}`} description={new Date(selected.created_at).toLocaleString('en-US')} action={<Button variant="secondary" onClick={()=>setSelected(null)}>Close</Button>}/><QualityMetrics quality={{score:selected.overall_score,dimensions:{completeness:selected.completeness_score,uniqueness:selected.uniqueness_score,validity:selected.validity_score},checks:selected.checks||[],summary:{checks:0,passed:0,warnings:0,failed:0}}}/><DataTable label="Historical quality checks"><thead><tr><th>Check</th><th>Column</th><th>Score</th><th>Affected</th><th>Status</th></tr></thead><tbody>{selected.checks?.map((c,i)=><tr key={i}><td>{ruleLabel(c.rule)}{c.message&&<p className="muted text-xs">{c.message}</p>}</td><td className="cell-mono">{c.columns?.join(', ')||c.column||'—'}</td><td>{c.score.toFixed(2)}</td><td>{c.failed_count} · {c.failed_percentage.toFixed(2)}%</td><td><Badge tone={c.status}>{c.status}</Badge></td></tr>)}</tbody></DataTable></div>}
 </Card>
}
