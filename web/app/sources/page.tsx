"use client"
import Link from 'next/link'
import { useEffect, useState } from 'react'

export default function SourcesPage() {
  const [sources, setSources] = useState([])

  useEffect(() => {
    fetch('/api/v1/sources')
      .then((r) => r.json())
      .then((d) => setSources(d))
      .catch(() => setSources([]))
  }, [])

  return (
    <main className="p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-semibold">Data Sources</h1>
          <Link href="/sources/add" className="text-sm text-blue-600">Add data source</Link>
        </div>

        <ul className="mt-4 space-y-3">
          {sources.map((s: any) => (
            <li key={s.id} className="p-4 bg-white rounded shadow">
              <Link href={`/sources/${s.id}`} className="block">
                <div className="font-medium">{s.name}</div>
                <div className="text-sm text-gray-500">{s.type} — {s.host}:{s.port}</div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </main>
  )
}
