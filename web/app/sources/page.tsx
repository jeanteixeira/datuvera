"use client"
import SourceList,{useSources} from '../../components/sources/SourceList'
import {ActionLink,PageHeader} from '../../components/ui'
export default function SourcesPage(){const {sources,state,load}=useSources();return <><PageHeader eyebrow="Connections" title="Data Sources" description="Connect PostgreSQL and explore the data behind your quality checks." action={<ActionLink href="/sources/add">+ Add Data Source</ActionLink>}/><SourceList sources={sources} state={state} retry={load}/><p className="muted text-xs mt-4">Connections are tested on demand. Datuvera does not continuously monitor connection status.</p></>}
