"use client"
import { useEffect, useState } from 'react'

export default function Home() {
  const [status, setStatus] = useState('unknown')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl p-8 bg-white rounded shadow">
        <h1 className="text-3xl font-semibold">Datuvera</h1>
        <p className="mt-4 text-gray-700">Know your data. Trust your data.</p>
        <p className="mt-2 text-gray-600">
          Open-source data profiling and quality platform for modern data stacks, enhanced with AI.
        </p>

        <div className="mt-6">
          <span className="text-sm text-gray-500">API status:</span>
          <div className="mt-2 font-mono">{status}</div>
        </div>
      </div>
    </main>
  )
}
