"use client"
import {useEffect,useRef,useState} from 'react'
import {useParams} from 'next/navigation'
import Link from 'next/link'
import {Badge,Button,PageHeader} from '../../../../../../components/ui'
import {ProfileOverview,ColumnsPanel} from '../../../../../../components/datasets/ProfilePanels'
import QualityPanel from '../../../../../../components/quality/QualityPanel'
import InsightsPanel from '../../../../../../components/ai/InsightsPanel'
import type {Profile,Quality,Insights,RunState} from '../../../../../../components/datasets/types'
import type {Source} from '../../../../../../components/sources/SourceList'

export default function DatasetPage(){
 const params=useParams(),id=String(params?.id||''),schema=String(params?.schema||''),table=String(params?.table||'')
 const root=`/api/v1/sources/${id}`,key=`${id}/${schema}/${table}`
 const [tab,setTab]=useState('Overview')
 const [source,setSource]=useState<Source|null>(null)
 const [profile,setProfile]=useState<Profile|null>(null)
 const [quality,setQuality]=useState<Quality|null>(null)
 const [insights,setInsights]=useState<Insights|null>(null)
 const [profileState,setProfileState]=useState<RunState>('idle')
 const [qualityState,setQualityState]=useState<RunState>('idle')
 const [aiAvailable,setAiAvailable]=useState<boolean|null>(null)
 const [aiState,setAiState]=useState('idle')
 const [historyRevision,setHistoryRevision]=useState(0)
 const generation=useRef(0)
 useEffect(()=>{generation.current++;setTab('Overview');setProfile(null);setQuality(null);setInsights(null);setProfileState('idle');setQualityState('idle');setAiState('idle');setSource(null);let active=true;fetch(root).then(r=>{if(!r.ok)throw Error();return r.json()}).then(s=>{if(active)setSource(s)}).catch(()=>{});return()=>{active=false;generation.current++}},[key])
 useEffect(()=>{let active=true;fetch('/api/v1/ai/status').then(r=>{if(!r.ok)throw Error();return r.json()}).then(s=>{if(active)setAiAvailable(s.enabled)}).catch(()=>{if(active)setAiState('unavailable')});return()=>{active=false}},[])
 const busy=profileState==='running'||qualityState==='running'||aiState==='running'
 async function run(kind:'profile'|'quality'|'insights'){
 if(busy)return
 const current=generation.current
 if(kind==='profile')setProfileState('running');else if(kind==='quality')setQualityState('running');else{setAiState('running');setInsights(null)}
 try{const r=await fetch(`${root}/${kind}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema,table})});if(current!==generation.current)return;if(kind==='insights'&&r.status===503){setAiState('unavailable');return}if(!r.ok)throw Error();const data=await r.json();if(current!==generation.current)return;if(kind==='profile'){setProfile(data);setProfileState('success');setQuality(null);setQualityState('idle');setInsights(null);setAiState('idle')}else if(kind==='quality'){setHistoryRevision(n=>n+1);setQuality(data);setQualityState('success');setInsights(null);setAiState('idle')}else{setInsights(data);setAiState('success')}}catch{if(current!==generation.current)return;if(kind==='profile')setProfileState('error');else if(kind==='quality')setQualityState('error');else setAiState('error')}
 }
 function rulesChanged(){generation.current++;setQuality(null);setQualityState('idle');setInsights(null);setAiState('idle');if(profileState==='running')setProfileState('idle')}
 const tabs=['Overview','Columns','Quality','AI Insights']
 return <><nav className="breadcrumb" aria-label="Breadcrumb"><Link href="/sources">Data Sources</Link><span>/</span><Link href={`/sources/${id}`}>{source?.name||'Source'}</Link><span>/</span><span>{schema}</span><span>/</span><span>{table}</span></nav><PageHeader eyebrow="Dataset workspace" title={`${schema}.${table}`} description={`${source?.name||'Data Source'} / PostgreSQL`} action={<><Button variant="secondary" onClick={()=>run('profile')} disabled={busy}>{profileState==='running'?'Running profile...':'Run Profile'}</Button><Button onClick={()=>{setTab('Quality');run('quality')}} disabled={busy}>{qualityState==='running'?'Running quality...':'Run Quality Checks'}</Button></>}/><div className="mb-5 flex gap-2"><Badge>PostgreSQL</Badge><Badge>{schema}</Badge></div>
 <div className="tabs" role="tablist" aria-label="Dataset navigation">{tabs.map((t,i)=><button key={t} id={`tab-${i}`} role="tab" className="tab" aria-selected={tab===t} aria-controls={`panel-${i}`} tabIndex={tab===t?0:-1} onClick={()=>setTab(t)} onKeyDown={e=>{if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?3:(i+(e.key==='ArrowRight'?1:3))%4;setTab(tabs[next]);document.getElementById(`tab-${next}`)?.focus()}}}>{t}</button>)}</div>
 <div role="tabpanel" id={`panel-${tabs.indexOf(tab)}`} aria-labelledby={`tab-${tabs.indexOf(tab)}`} tabIndex={0}>
 {tab==='Overview'&&<ProfileOverview profile={profile} quality={quality} state={profileState} run={()=>run('profile')}/>}{tab==='Columns'&&<ColumnsPanel profile={profile} state={profileState} run={()=>run('profile')}/>}{tab==='Quality'&&<QualityPanel quality={quality} profile={profile} state={qualityState} run={()=>run('quality')} runProfile={()=>run('profile')} sourceId={id} schema={schema} table={table} onRulesChanged={rulesChanged} historyRevision={historyRevision}/>}{tab==='AI Insights'&&<InsightsPanel available={aiAvailable} state={aiState} insights={insights} run={()=>run('insights')}/>}
 </div></>
}
