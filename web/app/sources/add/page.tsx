"use client"
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AddSource() {
  const [form, setForm] = useState({ name: '', host: '', port: '5432', database: '', username: '', password: '' })
  const [message, setMessage] = useState('')
  const router = useRouter()

  const test = async () => {
    setMessage('Testing...')
    const res = await fetch('/api/v1/sources/test', { method: 'POST', body: JSON.stringify({ ...form, type: 'postgresql', port: parseInt(form.port) }), headers: { 'Content-Type': 'application/json' } })
    const data = await res.json()
    if (res.ok) setMessage('Connection successful')
    else setMessage('Connection failed: ' + JSON.stringify(data))
  }

  const save = async () => {
    const res = await fetch('/api/v1/sources', { method: 'POST', body: JSON.stringify({ ...form, type: 'postgresql', port: parseInt(form.port) }), headers: { 'Content-Type': 'application/json' } })
    if (res.ok) router.push('/sources')
    else setMessage('Save failed')
  }

  return (
    <main className="p-6">
      <div className="max-w-md mx-auto bg-white p-6 rounded shadow">
        <h2 className="text-lg font-semibold">Add Data Source</h2>
        <p className="mt-2 text-sm">Connect PostgreSQL, or try the included demo with intentional quality issues.</p>
        <button type="button" onClick={() => {
          setForm({ name: 'Datuvera Demo', host: 'datuvera-demo-db', port: '5432', database: 'demo', username: 'demo', password: 'demo' })
          setMessage('Demo settings loaded. Test Connection, then Save Source.')
        }} className="mt-3 px-3 py-2 border rounded">Use demo database</button>
        <p className="mt-2 text-sm text-gray-600">Demo: datuvera-demo-db:5432 · database demo · username demo · password demo</p>
        <div className="mt-4 space-y-2">
          <input aria-label="Name" placeholder="Name" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full p-2 border" />
          <input aria-label="Host" placeholder="Host" value={form.host} onChange={(e) => setForm({...form, host: e.target.value})} className="w-full p-2 border" />
          <input aria-label="Port" placeholder="Port" value={form.port} onChange={(e) => setForm({...form, port: e.target.value})} className="w-full p-2 border" />
          <input aria-label="Database" placeholder="Database" value={form.database} onChange={(e) => setForm({...form, database: e.target.value})} className="w-full p-2 border" />
          <input aria-label="Username" placeholder="Username" value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} className="w-full p-2 border" />
          <input aria-label="Password" placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full p-2 border" />
        </div>
        <div className="mt-4 flex space-x-2">
          <button onClick={test} className="px-3 py-2 bg-gray-200 rounded">Test Connection</button>
          <button onClick={save} className="px-3 py-2 bg-blue-600 text-white rounded">Save Source</button>
        </div>
        {message && <div className="mt-3 font-mono text-sm">{message}</div>}
      </div>
    </main>
  )
}
