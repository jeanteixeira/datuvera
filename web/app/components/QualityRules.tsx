"use client"
import { useEffect, useState } from 'react'

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
    setLoading(true)
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

  return (
    <section className="mt-6 border-t pt-4" aria-label="Quality Rules">
      <h2 className="font-medium">Quality Rules</h2>
      <p className="text-sm text-gray-600">Configured rules run alongside automatic completeness and database constraint checks. AI suggestions are separate.</p>
      {loading && <p role="status">Loading rules...</p>}
      {error && <p className="mt-2 text-red-600" role="alert">{error} <button onClick={load}>Reload</button></p>}
      {!loading && rules.length === 0 && <p className="mt-2 text-sm">No configured rules yet.</p>}
      <ul>
        {rules.map(rule => (
          <li key={rule.id} className="mt-2 p-3 border rounded">
            <div>{rule.column} · {rule.rule} · {rule.is_enabled ? 'Enabled' : 'Disabled'}</div>
            {rule.parameters.value !== undefined && <p>Value: {rule.parameters.value}</p>}
            {rule.parameters.values && <p>Allowed values: {rule.parameters.values.map(String).join(', ')}</p>}
            <button disabled={busy} onClick={() => mutate('PATCH', rule.id, { is_enabled: !rule.is_enabled })} className="mt-2 mr-3 underline">{rule.is_enabled ? 'Disable' : 'Enable'}</button>
            {(rule.rule === 'allowed_values' || rule.rule === 'min_value' || rule.rule === 'max_value') && (
              <button disabled={busy} className="mr-3 underline" onClick={() => {
                setColumn(rule.column); setType(rule.rule); setValue(rule.parameters.values?.map(String).join(', ') ?? String(rule.parameters.value ?? ''))
                setEditing(rule.id); setShowForm(true); setError('')
              }}>Edit Parameters</button>
            )}
            <button disabled={busy} onClick={() => mutate('DELETE', rule.id)} className="underline">Delete</button>
          </li>
        ))}
      </ul>
      <button disabled={busy} className="mt-3 px-3 py-1 border rounded" onClick={() => {
        setEditing(null); setColumn(columns[0]?.name || ''); setType('not_null'); setValue(''); setShowForm(true); setError('')
      }}>Add Rule</button>
      {showForm && (
        <form className="mt-3 flex flex-col gap-2" onSubmit={event => {
          event.preventDefault()
          try {
            const params = parameters()
            mutate(editing === null ? 'POST' : 'PATCH', editing ?? undefined,
              editing === null ? { schema, table, column, rule: type, parameters: params } : { parameters: params })
          } catch (err) { setError(err instanceof Error ? err.message : 'Invalid parameters') }
        }}>
          <label>Column <select value={column} disabled={editing !== null || busy} onChange={event => { setColumn(event.target.value); setType('not_null'); setValue('') }} className="border rounded p-1">
            {columns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select></label>
          <label>Rule Type <select value={type} disabled={editing !== null || busy} onChange={event => { setType(event.target.value); setValue('') }} className="border rounded p-1">
            {(editing === null ? compatible : [type]).map(rule => <option key={rule} value={rule}>{rule}</option>)}
          </select></label>
          {type === 'allowed_values' && <label>Allowed values (comma separated) <input required value={value} onChange={event => setValue(event.target.value)} className="border rounded p-1" /></label>}
          {(type === 'min_value' || type === 'max_value') && <label>Value <input type="number" step="any" required value={value} onChange={event => setValue(event.target.value)} className="border rounded p-1" /></label>}
          <div><button disabled={busy || !column} className="px-3 py-1 bg-blue-600 text-white rounded">{busy ? 'Saving...' : 'Save Rule'}</button>
          <button type="button" disabled={busy} onClick={() => { setShowForm(false); setEditing(null) }} className="ml-3 underline">Cancel</button></div>
        </form>
      )}
    </section>
  )
}
