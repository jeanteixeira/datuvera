"use client"
import { useEffect,useState } from 'react'
import SourceList,{useSources} from '../components/sources/SourceList'
import { ActionLink, Badge, Card, MetricCard, PageHeader, SectionHeader } from '../components/ui'
export default function Overview(){
 const {sources,state,load}=useSources()
 const [rules,setRules]=useState<number|null>(null)
 const [rulesFailed,setRulesFailed]=useState(false)
 useEffect(()=>{let active=true;setRules(null);setRulesFailed(false);if(state==='success')Promise.all(sources.map(async s=>{const r=await fetch(`/api/v1/sources/${s.id}/quality-rules`);if(!r.ok)throw Error();return (await r.json()).length})).then(counts=>{if(active)setRules(counts.reduce((a,b)=>a+b,0))}).catch(()=>{if(active)setRulesFailed(true)});return()=>{active=false}},[sources,state])
 return <><PageHeader eyebrow="Workspace" title="Overview" description="Monitor your connected data sources and explore data quality." action={<ActionLink href="/sources/add">+ Add Data Source</ActionLink>}/>
 <div className="metrics-grid"><MetricCard label="Data Sources" value={state==='success'?sources.length:'—'} detail={state==='loading'?'Loading sources…':state==='error'?'Count unavailable':'Connected to your workspace'}/><MetricCard label="Supported Connector" value="PostgreSQL" detail="Schemas, tables and column statistics"/><MetricCard label="Configured Rules" value={rules??'—'} detail={rulesFailed?'Count unavailable':rules===null?'Loading configured rules…':'Persisted rules, including disabled rules'}/></div>
 <div className="stack"><SourceList sources={sources} state={state} retry={load}/><div className="split-grid"><Card><SectionHeader title="Getting started" description="From connection to an explainable quality result."/><ol className="steps">{['Connect a data source','Explore schemas and tables','Profile your dataset','Configure quality rules','Run quality checks','Generate optional AI insights'].map(s=><li key={s}>{s}</li>)}</ol></Card><Card><Badge tone="info">Deterministic by design</Badge><h2 className="mt-4">Understand the checks behind the score.</h2><p className="muted mt-3">Profiling and quality checks run independently of AI. Explore each dataset, inspect affected rows and configure the rules that matter.</p><p className="muted text-sm mt-4">Quality and AI results are generated per dataset. Run history is not stored.</p></Card></div></div></>
}
