"use client"
import {useEffect,useState} from 'react'
import SourceList,{useSources} from './SourceList'
import {PageHeader,Card,Badge,ActionLink} from '../ui'
export default function ExploreSources({kind}:{kind:'datasets'|'quality'|'ai'}){
 const {sources,state,load}=useSources()
 const text={datasets:['Datasets','Select a data source to explore schemas and tables.','Discovery on demand','Datasets are discovered from each source. Open a connection to choose a schema and dataset.'],quality:['Quality','Quality is evaluated per dataset.','Explainable quality','Select a dataset to configure rules and run quality checks. Results are generated on demand; each quality run is saved as an immutable snapshot.'],ai:['AI Insights','AI Insights are generated per dataset.','Optional analysis','Use AI to interpret profiling and quality results. Suggestions remain recommendations and never change your configured rules.']}[kind]
 const [ai,setAi]=useState<boolean|null>(null)
 const [failed,setFailed]=useState(false)
 useEffect(()=>{if(kind==='ai')fetch('/api/v1/ai/status').then(r=>{if(!r.ok)throw Error();return r.json()}).then(s=>setAi(s.enabled)).catch(()=>setFailed(true))},[kind])
 return <><PageHeader eyebrow="Dataset exploration" title={text[0]} description={text[1]}/><div className="stack"><Card><Badge tone="info">{text[2]}</Badge><p className="muted mt-3">{text[3]}</p>{kind==='ai'&&<p className="mt-3 text-sm">{failed?'We couldn’t check AI availability.':ai===null?'Checking AI availability...':ai?'AI is configured. Open a dataset to generate insights.':'AI Insights are optional and currently not configured. Profiling and deterministic quality checks remain fully available.'}</p>}<div className="mt-4"><ActionLink secondary href="/sources">Explore Data Sources</ActionLink></div></Card><SourceList sources={sources} state={state} retry={load} title="Choose a data source"/></div></>
}
