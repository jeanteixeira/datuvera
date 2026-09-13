"use client"
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AddSource() {
  const [form, setForm] = useState({ name: '', host: '', port: '5432', database: '', username: '', password: '' })
  const [message, setMessage] = useState('')
  const router = useRouter()
  const [useDemo, setUseDemo] = useState(false)
  const [saving, setSaving] = useState(false)
  const [savedId, setSavedId] = useState<number | null>(null)

  const test = async () => {
    setMessage('Testing...')
    const res = await fetch('/api/v1/sources/test', { method: 'POST', body: JSON.stringify({ ...form, type: 'postgresql', port: parseInt(form.port) }), headers: { 'Content-Type': 'application/json' } })
    const data = await res.json()
    if (res.ok) setMessage('Connection successful')
    else setMessage('Connection failed: ' + JSON.stringify(data))
  }

  const save = async () => {
    if (saving) return
    setSaving(true)
    setMessage('Saving...')
    try {
      let id = savedId
      if (id === null) {
        const res = await fetch('/api/v1/sources', { method: 'POST', body: JSON.stringify({ ...form, type: 'postgresql', port: parseInt(form.port) }), headers: { 'Content-Type': 'application/json' } })
        if (!res.ok) throw new Error('Save failed')
        id = (await res.json()).id
        setSavedId(id)
      }
      if (useDemo && form.host === 'datuvera-demo-db' && form.database === 'demo') {
        const root = `/api/v1/sources/${id}/quality-rules`
        const existingRes = await fetch(`${root}?schema=public&table=customers`)
        if (!existingRes.ok) throw new Error('Source saved. Could not configure demo rules; click Save Source to retry.')
        const existing = await existingRes.json()
        for (const rule of [{ column: 'email', rule: 'email_format', parameters: {} },
          { column: 'state', rule: 'allowed_values', parameters: { values: ['AL','PE','BA','SP','RJ'] } }]) {
          if (existing.some((r:any) => r.column === rule.column && r.rule === rule.rule)) continue
          const res = await fetch(root, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ schema: 'public', table: 'customers', ...rule }) })
          if (!res.ok) throw new Error('Source saved. Could not configure demo rules; click Save Source to retry.')
        }
      }
      router.push('/sources')
    } catch (err) { setMessage(err instanceof Error ? err.message : 'Save failed') }
    finally { setSaving(false) }
  }

  return (
    <main className="p-6">
      <div className="max-w-md mx-auto bg-white p-6 rounded shadow">
        <h2 className="text-lg font-semibold">Add Data Source</h2>
        <p className="mt-2 text-sm">Connect PostgreSQL, or try the included demo with intentional quality issues.</p>
        <button type="button" disabled={saving || savedId !== null} onClick={() => {
          setUseDemo(true)
          setForm({ name: 'Datuvera Demo', host: 'datuvera-demo-db', port: '5432', database: 'demo', username: 'demo', password: 'demo' })
          setMessage('Demo settings loaded. Save Source also creates email and state quality rules.')
        }} className="mt-3 px-3 py-2 border rounded">Use demo database</button>
        <p className="mt-2 text-sm text-gray-600">Demo creates two editable quality rules for public.customers. Demo: datuvera-demo-db:5432 · database demo · username demo · password demo</p>
        <div className="mt-4 space-y-2">
          <input disabled={saving || savedId !== null} aria-label="Name" placeholder="Name" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full p-2 border" />
          <input disabled={saving || savedId !== null} aria-label="Host" placeholder="Host" value={form.host} onChange={(e) => setForm({...form, host: e.target.value})} className="w-full p-2 border" />
          <input disabled={saving || savedId !== null} aria-label="Port" placeholder="Port" value={form.port} onChange={(e) => setForm({...form, port: e.target.value})} className="w-full p-2 border" />
          <input disabled={saving || savedId !== null} aria-label="Database" placeholder="Database" value={form.database} onChange={(e) => setForm({...form, database: e.target.value})} className="w-full p-2 border" />
          <input disabled={saving || savedId !== null} aria-label="Username" placeholder="Username" value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} className="w-full p-2 border" />
          <input disabled={saving || savedId !== null} aria-label="Password" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full p-2 border" />
        </div>
        <div className="mt-4 flex space-x-2">
          <button onClick={test} className="px-3 py-2 bg-gray-200 rounded">Test Connection</button>
          <button disabled={saving} onClick={save} className="px-3 py-2 bg-blue-600 text-white rounded">Save Source</button>
        </div>
        {message && <div className="mt-3 font-mono text-sm">{message}</div>}
      </div>
    </main>
  )
}
