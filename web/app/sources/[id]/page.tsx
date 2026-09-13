"use client"
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

export default function SourceDetail() {
  const params = useParams()
  const id = params?.id
  const [src, setSrc] = useState<any>(null)
  const [schemas, setSchemas] = useState<string[]>([])
  const [tables, setTables] = useState<any[]>([])
  const [selectedSchema, setSelectedSchema] = useState('public')

  useEffect(() => {
    fetch(`/api/v1/sources/${id}`).then(r=>r.json()).then(setSrc)
    fetch(`/api/v1/sources/${id}/schemas`).then(r=>r.json()).then(setSchemas)
  }, [id])

  useEffect(() => {
    if (selectedSchema) fetch(`/api/v1/sources/${id}/schemas/${selectedSchema}/tables`).then(r=>r.json()).then(setTables)
  }, [selectedSchema, id])

  if (!src) return <div className="p-6">Loading...</div>

  return (
    <main className="p-6">
      <div className="max-w-3xl mx-auto bg-white p-6 rounded shadow">
        <h2 className="text-lg font-semibold">{src.name}</h2>
        <div className="text-sm text-gray-600">{src.type} — {src.host}:{src.port} / {src.database}</div>

        <div className="mt-4">
          <h3 className="font-medium">Schemas</h3>
          <div className="mt-2 flex space-x-2">
            {schemas.map(s => (
              <button key={s} onClick={()=>setSelectedSchema(s)} className={`px-2 py-1 border ${selectedSchema===s? 'bg-gray-200':''}`}>{s}</button>
            ))}
          </div>
        </div>

        <div className="mt-4">
          <h3 className="font-medium">Tables</h3>
          <ul className="mt-2">
            {tables.map(t => (
              <li key={t.name} className="py-1 flex items-center justify-between">
                <span>{t.name}</span>
                <a href={`/sources/${id}/datasets/${selectedSchema}/${t.name}`} className="text-sm text-blue-600">Run Profile</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}
