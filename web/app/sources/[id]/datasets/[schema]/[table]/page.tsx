"use client"
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'

export default function DatasetProfilePage() {
  const params = useParams()
  const router = useRouter()
  const { id, schema, table } = params || {}
  const [state, setState] = useState<'idle'|'running'|'success'|'error'>('idle')
  const [qualityState, setQualityState] = useState<'idle'|'running'|'success'|'error'>('idle')
  const [quality, setQuality] = useState<any>(null)
  const [profile, setProfile] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!id || !schema || !table) return
    runProfile()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, schema, table])

  async function runProfile() {
    setState('running')
    setErrorMsg(null)
    try {
      const res = await fetch(`/api/v1/sources/${id}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ schema, table })
      })
      if (!res.ok) {
        const txt = await res.text()
        setErrorMsg(txt || 'Failed to profile')
        setState('error')
        return
      }
      const data = await res.json()
      setProfile(data)
      setState('success')
    } catch (e:any) {
      setErrorMsg(e?.message || String(e))
      setState('error')
    }
  }

  async function runQuality() {
    setQualityState('running')
    try {
      const res = await fetch(`/api/v1/sources/${id}/quality`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ schema, table })
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      setQuality(data)
      setQualityState('success')
    } catch (e:any) {
      setQualityState('error')
    }
  }

  if (state === 'running') return <div className="p-6">Profiling dataset...</div>
  if (state === 'error') return (
    <div className="p-6">
      <div className="text-red-600">Error profiling dataset.</div>
      <div className="mt-2 text-sm text-gray-700">{errorMsg}</div>
      <div className="mt-4"><button onClick={runProfile} className="px-3 py-1 bg-blue-600 text-white rounded">Run again</button></div>
    </div>
  )

  if (!profile) return <div className="p-6">No profile yet.</div>

  const ds = profile.dataset
  const cols = profile.columns || []

  return (
    <main className="p-6">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold">{ds.table}</h2>
        <div className="text-sm text-gray-600">{ds.schema}.{ds.table} — PostgreSQL</div>
        <div className="mt-3">
          <span className="mr-4">{ds.row_count} rows</span>
          <span className="mr-4">{ds.column_count} columns</span>
          <span className="mr-4">{ds.estimated_size_bytes ? Math.round(ds.estimated_size_bytes/1024) + ' KB' : '—'}</span>
          <div className="text-sm text-gray-500 mt-2">Profile generated at: {ds.generated_at}</div>
        </div>

        <div className="mt-6">
          <table className="w-full table-auto border-collapse">
            <thead>
              <tr className="text-left border-b"><th className="py-2">Column</th><th>Type</th><th>Nulls</th><th>Distinct</th><th>Min</th><th>Max</th><th>Extras</th></tr>
            </thead>
            <tbody>
              {cols.map((c:any)=> (
                <tr key={c.name} className="border-b">
                  <td className="py-2">{c.name}</td>
                  <td>{c.data_type}</td>
                  <td>{c.null_percentage}%</td>
                  <td>{c.distinct_percentage}%</td>
                  <td>{c.min ?? '—'}</td>
                  <td>{c.max ?? '—'}</td>
                  <td>
                    <details>
                      <summary className="text-sm text-blue-600">View metrics</summary>
                      <div className="mt-2 text-sm text-gray-700">
                        {c.min_length !== undefined && <div>Min length: {c.min_length}</div>}
                        {c.max_length !== undefined && <div>Max length: {c.max_length}</div>}
                        {c.avg_length !== undefined && <div>Avg length: {c.avg_length}</div>}
                        {c.mean !== undefined && <div>Mean: {c.mean}</div>}
                        {c.true_count !== undefined && <div>True: {c.true_count} / False: {c.false_count}</div>}
                        {c.top_values && c.top_values.length>0 && (
                          <div className="mt-2">
                            <div className="font-medium">Top values</div>
                            <ul className="list-disc list-inside text-sm">
                              {c.top_values.map((t:any,i:number)=> <li key={i}>{String(t.value)} ({t.count})</li>)}
                            </ul>
                          </div>
                        )}
                      </div>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4">
            <button onClick={runProfile} className="px-3 py-1 bg-blue-600 text-white rounded">Run again</button>
             <button onClick={runQuality} className="ml-2 px-3 py-1 bg-green-600 text-white rounded">Run Quality Checks</button>
            <button onClick={()=>router.back()} className="ml-2 px-3 py-1 border rounded">Back</button>
          </div>
        </div>

          <div className="mt-6">
            <h3 className="font-medium">Data Quality</h3>
            {qualityState === 'idle' && <div className="text-sm text-gray-600">Run quality checks to evaluate dataset.</div>}
            {qualityState === 'running' && <div>Running quality checks...</div>}
            {qualityState === 'error' && <div className="text-red-600">Failed to run quality checks.</div>}
            {qualityState === 'success' && quality && (
              <div className="mt-2">
                <div className="text-2xl font-semibold">{quality.score} / 100</div>
                <div className="mt-2 grid grid-cols-3 gap-4">
                  <div className="p-3 border rounded"><div className="font-medium">Completeness</div><div className="text-lg">{quality.dimensions.completeness ?? 'N/A'}</div></div>
                  <div className="p-3 border rounded"><div className="font-medium">Uniqueness</div><div className="text-lg">{quality.dimensions.uniqueness ?? 'N/A'}</div></div>
                  <div className="p-3 border rounded"><div className="font-medium">Validity</div><div className="text-lg">{quality.dimensions.validity ?? 'N/A'}</div></div>
                </div>
                <div className="mt-4">
                  <h4 className="font-medium">Checks</h4>
                  <ul className="mt-2">
                    {quality.checks.map((c:any,i:number)=>(
                      <li key={i} className="py-2 border-b">
                        <div>{c.status === 'passed' ? '✓' : c.status === 'warning' ? '⚠' : '✕'} {c.columns?.join(', ') || c.column} — {c.rule}</div>
                        <div className="text-sm">Status: {c.status} · Score: {c.score.toFixed(2)}/100</div>
                        {c.status !== 'passed' && (
                          <div className="mt-1 text-sm">
                            <div>{c.failed_count} affected rows · {c.failed_percentage.toFixed(2)}% of rows affected</div>
                            {c.message && <div>{c.message}</div>}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
      </div>
    </main>
  )
}
