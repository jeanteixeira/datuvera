"use client"
import {useEffect,useRef,useState} from 'react'
import {Badge,Button,Card,DataTable,EmptyState,ErrorState,LoadingState,MetricCard,SectionHeader,ruleLabel} from '../ui'
import {QualityMetrics} from '../datasets/ProfilePanels'
import QualityTrendChart from './QualityTrendChart'
import {comparison,formatScore,formatDelta,changeLabel,localTimestamp,metrics,type Metric,type RunSummary} from './history'
import type {Quality} from '../datasets/types'

type Run = RunSummary & {checks?:Quality['checks']}
export default function RecentQualityRuns({sourceId,schema,table,revision}:{sourceId:string;schema:string;table:string;revision:number}){
 const [runs,setRuns]=useState<Run[]>([])
 const [state,setState]=useState('loading')
 const [selected,setSelected]=useState<Run|null>(null)
 const [detailState,setDetailState]=useState('idle')
 const [retry,setRetry]=useState(0)
 const [limit,setLimit]=useState(20)
 const [metric,setMetric]=useState<Metric>('overall_score')
 const detailRequest=useRef<AbortController|null>(null)
 const historyRequest=useRef<AbortController|null>(null)
 const stats=comparison(runs,metric)
 const root=`/api/v1/sources/${sourceId}/quality-runs`
 useEffect(()=>{
  detailRequest.current?.abort();const controller=new AbortController();historyRequest.current=controller;setState('loading');setSelected(null);setDetailState('idle')
  fetch(`${root}?${new URLSearchParams({schema,table,limit:String(limit),offset:'0'})}`,{signal:controller.signal})
   .then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{if(!controller.signal.aborted){setRuns(data);setState('success')}})
   .catch(()=>{if(!controller.signal.aborted)setState('error')})
  return()=>{controller.abort();detailRequest.current?.abort()}
 },[sourceId,schema,table,revision,retry,limit])
 async function select(id:number){detailRequest.current?.abort();const controller=new AbortController();detailRequest.current=controller;setSelected(null);setDetailState('loading');try{const r=await fetch(`${root}/${id}`,{signal:controller.signal});if(!r.ok)throw Error();const snapshot=await r.json();if(!controller.signal.aborted){setSelected(snapshot);setDetailState('success')}}catch{if(!controller.signal.aborted)setDetailState('error')}}
 return <Card><SectionHeader title="Quality History" description="Immutable quality runs, latest versus previous scores and historical evolution." action={<label className="field">Period<select value={limit} onChange={event=>{historyRequest.current?.abort();detailRequest.current?.abort();setState('loading');setRuns([]);setSelected(null);setLimit(Number(event.target.value))}}>{[10,20,50].map(n=><option key={n} value={n}>Last {n} runs</option>)}</select></label>}/>
 {state==='loading'&&<LoadingState>Loading quality history...</LoadingState>}{state==='error'&&<ErrorState retry={()=>setRetry(n=>n+1)}>We couldn’t load quality history.</ErrorState>}
 {state==='success'&&runs.length>0&&<>
 <div className="metrics-grid four"><MetricCard label={`Latest ${metrics[metric]} Score`} value={formatScore(stats.latest)} detail={`Run #${runs[0].id}`}/><MetricCard label="Previous Score" value={formatScore(stats.previous)} detail={runs[1]?`Run #${runs[1].id}`:'No previous run'}/><MetricCard label="Change" value={formatDelta(stats.change)} detail={`${changeLabel(stats.change)} · score points`}/><MetricCard label="Runs shown" value={runs.length} detail={`Up to ${limit} most recent runs`}/></div>
 <DataTable label="Dimension comparison"><thead><tr><th>Dimension</th><th>Latest</th><th>Previous</th><th>Change · points</th></tr></thead><tbody>{(['completeness_score','uniqueness_score','validity_score'] as const).map(key=>{const c=comparison(runs,key);return <tr key={key}><td>{metrics[key]}</td><td>{formatScore(c.latest)}</td><td>{formatScore(c.previous)}</td><td>{formatDelta(c.change)} <span className="muted text-xs">· {changeLabel(c.change)}</span></td></tr>})}</tbody></DataTable>
 <div className="mt-6"><label className="field max-w-xs">Metric<select value={metric} onChange={event=>setMetric(event.target.value as Metric)}>{Object.entries(metrics).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label></div>
 {runs.length===1?<EmptyState title="One quality run available" description="Run quality checks again to start comparing results."/>:<div className="mt-5"><QualityTrendChart runs={runs} metric={metric}/></div>}
 <div className="mt-6"><SectionHeader title="Run history" description="Newest execution first. Open a snapshot to inspect the checks from that run."/></div>
 </>}
 {state==='success'&&(runs.length?<DataTable label="Run history"><thead><tr><th>Executed At</th><th>Score</th><th>Completeness</th><th>Uniqueness</th><th>Validity</th><th>Action</th></tr></thead><tbody>{runs.map(run=><tr key={run.id}><td>{localTimestamp(run.created_at)}<p className="muted text-xs">Run #{run.id}</p></td><td className="cell-title">{run.overall_score.toFixed(2)}</td><td>{run.completeness_score?.toFixed(2)??'N/A'}</td><td>{run.uniqueness_score?.toFixed(2)??'N/A'}</td><td>{run.validity_score?.toFixed(2)??'N/A'}</td><td><Button variant="secondary" disabled={detailState==='loading'} aria-label={`View quality run ${run.id}`} onClick={()=>select(run.id)}>View snapshot</Button></td></tr>)}</tbody></DataTable>:<EmptyState title="No quality history yet." description="Run quality checks to start building a trend."/>)}
 {detailState==='loading'&&<LoadingState>Loading snapshot...</LoadingState>}{detailState==='error'&&<ErrorState>We couldn’t load this quality run. Select it again to retry.</ErrorState>}
 {selected&&<div className="inline-panel"><SectionHeader title={`Historical Snapshot · Run #${selected.id}`} description={localTimestamp(selected.created_at)} action={<Button variant="secondary" onClick={()=>setSelected(null)}>Close</Button>}/><QualityMetrics quality={{score:selected.overall_score,dimensions:{completeness:selected.completeness_score,uniqueness:selected.uniqueness_score,validity:selected.validity_score},checks:selected.checks||[],summary:{checks:0,passed:0,warnings:0,failed:0}}}/><DataTable label="Historical quality checks"><thead><tr><th>Check</th><th>Column</th><th>Score</th><th>Affected</th><th>Status</th></tr></thead><tbody>{selected.checks?.map((c,i)=><tr key={i}><td>{ruleLabel(c.rule)}{c.message&&<p className="muted text-xs">{c.message}</p>}</td><td className="cell-mono">{c.columns?.join(', ')||c.column||'—'}</td><td>{c.score.toFixed(2)}</td><td>{c.failed_count} · {c.failed_percentage.toFixed(2)}%</td><td><Badge tone={c.status}>{c.status}</Badge></td></tr>)}</tbody></DataTable></div>}
 </Card>
}
