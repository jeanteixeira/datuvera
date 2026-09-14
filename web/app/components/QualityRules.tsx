"use client"
import { useEffect, useState } from 'react'
import {Badge,Button,Card,DataTable,EmptyState,ErrorState,LoadingState,SectionHeader,ruleLabel} from '../../components/ui'

type Rule = { id: number; column: string; rule: string; parameters: { value?: number; values?: (string | number | boolean)[] }; is_enabled: boolean }
type Column = { name: string; data_type: string }

export default function QualityRules({ sourceId, schema, table, columns, onChanged }: {
  sourceId: string; schema: string; table: string; columns: Column[]; onChanged: () => void
}) {
  const root = `/api/v1/sources/${sourceId}/quality-rules`
  const [rules, setRules] = useState<Rule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const [column, setColumn] = useState(columns[0]?.name || '')
  const [type, setType] = useState('not_null')
  const [value, setValue] = useState('')

  async function load() {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${root}?${new URLSearchParams({ schema, table })}`)
      if (!res.ok) throw new Error('Could not load quality rules.')
      setRules(await res.json())
    } catch { setError('Could not load quality rules. Please retry.'); }
    finally { setLoading(false) }
  }
  useEffect(() => { setError(''); setShowForm(false); load() }, [sourceId, schema, table])

  const dtype = columns.find(c => c.name === column)?.data_type.toLowerCase() || ''
  const numeric = /int|numeric|decimal|real|double|float/.test(dtype)
  const textual = /char|text/.test(dtype)
  const compatible = ['not_null', 'unique', ...(textual ? ['email_format'] : []),
    ...(textual || numeric || /bool/.test(dtype) ? ['allowed_values'] : []), ...(numeric ? ['min_value', 'max_value'] : [])]

  async function mutate(method: string, id?: number, body?: object) {
    setBusy(true); setError('')
    try {
      const res = await fetch(id === undefined ? root : `${root}/${id}`, {
        method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body)
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Invalid rule configuration. Check the column and parameters.')
      }
      setShowForm(false); setEditing(null)
      await load(); onChanged()
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not save quality rule.') }
    finally { setBusy(false) }
  }

  function parameters() {
    if (type === 'min_value' || type === 'max_value') {
      if (!value.trim() || !Number.isFinite(Number(value))) throw new Error('Enter a finite numeric bound.')
      return { value: Number(value) }
    }
    if (type === 'allowed_values') {
      const values = value.split(',').map(v => v.trim()).filter(Boolean)
      if (!values.length) throw new Error('Enter at least one allowed value.')
      if (numeric) {
        if (values.some(v => !Number.isFinite(Number(v)))) throw new Error('Enter numeric allowed values.')
        return { values: values.map(Number) }
      }
      if (/bool/.test(dtype)) {
        if (values.some(v => v !== 'true' && v !== 'false')) throw new Error('Use true or false for boolean values.')
        return { values: values.map(v => v === 'true') }
      }
      return { values }
    }
    return {}
  }

  const descriptions:Record<string,string> = {not_null:'Checks whether values are missing.',unique:'Checks whether non-null values are unique.',email_format:'Checks whether non-null values resemble an email address.',allowed_values:'Checks whether non-null values belong to a defined list.',min_value:'Checks whether non-null values meet a minimum numeric bound.',max_value:'Checks whether non-null values stay within a maximum numeric bound.'}
  function add(){setEditing(null);setColumn(columns[0]?.name||'');setType('not_null');setValue('');setShowForm(true);setError('')}
  return (
    <Card>
      <SectionHeader title="Quality Rules" description="Configured rules run alongside automatic completeness and database constraint checks." action={<Button disabled={busy} onClick={add}>+ Add Rule</Button>}/>
      {loading && <LoadingState>Loading rules...</LoadingState>}
      {error && <ErrorState retry={load}>{error}</ErrorState>}
      {!loading && rules.length === 0 && !showForm && <EmptyState title="No configured rules" description="Automatic metadata rules will still be evaluated. Add column rules to validate your data requirements." action={<Button variant="secondary" onClick={add}>Add Rule</Button>}/>}
      {!!rules.length && <DataTable label="Configured quality rules"><thead><tr><th>Column</th><th>Rule</th><th>Parameters</th><th>Status</th><th>Actions</th></tr></thead><tbody>
        {rules.map(rule => <tr key={rule.id}>
          <td className="cell-mono cell-title">{rule.column}</td><td>{ruleLabel(rule.rule)}</td>
          <td className="muted max-w-xs break-words">{rule.parameters.values?.map(String).join(', ') ?? rule.parameters.value ?? '—'}</td>
          <td><Badge tone={rule.is_enabled?'enabled':'disabled'}>{rule.is_enabled?'Enabled':'Disabled'}</Badge></td>
          <td><div className="flex items-center gap-1">
            {(rule.rule==='allowed_values'||rule.rule==='min_value'||rule.rule==='max_value')&&<Button variant="secondary" disabled={busy} aria-label={`Edit parameters for ${rule.column} ${ruleLabel(rule.rule)}`} onClick={()=>{setColumn(rule.column);setType(rule.rule);setValue(rule.parameters.values?.map(String).join(', ')??String(rule.parameters.value??''));setEditing(rule.id);setShowForm(true);setError('')}}>Edit</Button>}
            <Button variant="secondary" disabled={busy} aria-label={`${rule.is_enabled?'Disable':'Enable'} ${rule.column} ${ruleLabel(rule.rule)}`} onClick={()=>mutate('PATCH',rule.id,{is_enabled:!rule.is_enabled})}>{rule.is_enabled?'Disable':'Enable'}</Button>
            <Button variant="danger" disabled={busy} aria-label={`Delete ${rule.column} ${ruleLabel(rule.rule)}`} onClick={()=>mutate('DELETE',rule.id)}>Delete</Button>
          </div></td></tr>)}
      </tbody></DataTable>}
      {showForm && <form className="inline-panel" onSubmit={event=>{event.preventDefault();try{const params=parameters();mutate(editing===null?'POST':'PATCH',editing??undefined,editing===null?{schema,table,column,rule:type,parameters:params}:{parameters:params})}catch(err){setError(err instanceof Error?err.message:'Invalid parameters')}}}>
        <SectionHeader title={editing===null?'Add quality rule':'Edit rule parameters'} description="Define a deterministic check for a dataset column."/>
        <div className="form-grid">
          <label className="field">Column<select value={column} disabled={editing!==null||busy} onChange={event=>{setColumn(event.target.value);setType('not_null');setValue('')}}>{columns.map(c=><option key={c.name} value={c.name}>{c.name}</option>)}</select></label>
          <label className="field">Rule Type<select value={type} disabled={editing!==null||busy} onChange={event=>{setType(event.target.value);setValue('')}}>{(editing===null?compatible:[type]).map(rule=><option key={rule} value={rule}>{ruleLabel(rule)}</option>)}</select></label>
          {type==='allowed_values'&&<label className="field">Allowed values (comma separated)<input disabled={busy} required value={value} placeholder={numeric?'0, 10, 20':/bool/.test(dtype)?'true, false':'AL, PE, BA'} onChange={event=>setValue(event.target.value)}/></label>}
          {(type==='min_value'||type==='max_value')&&<label className="field">Value<input disabled={busy} type="number" step="any" required value={value} onChange={event=>setValue(event.target.value)}/></label>}
        </div><p className="muted text-xs mt-4">{descriptions[type]}</p>
        <div className="mt-5 flex gap-2"><Button disabled={busy||!column}>{busy?'Saving rule...':'Save Rule'}</Button><Button type="button" variant="secondary" disabled={busy} onClick={()=>{setShowForm(false);setEditing(null)}}>Cancel</Button></div>
      </form>}
      <p className="muted text-xs mt-4">AI suggestions are separate. Disabled rules remain saved and are excluded from configured checks.</p>
    </Card>
  )
}
