import Link from 'next/link'

export default function Home() {
  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-4xl font-semibold">Datuvera</h1>
      <p className="mt-4 text-xl">Know your data. Trust your data.</p>
      <p className="mt-3 text-gray-600">Open-source data profiling and quality platform for modern data stacks.</p>
      <div className="mt-6 flex gap-4">
        <Link href="/sources" className="px-4 py-2 bg-blue-600 text-white rounded">Explore Sources</Link>
        <a href="http://localhost:8000/docs" className="px-4 py-2 border rounded">API Docs</a>
      </div>
      <section aria-label="How Datuvera works" className="mt-10 grid gap-6 sm:grid-cols-2">
        <div><h2 className="font-semibold">Connect</h2><p>Connect your PostgreSQL data source, or start with the included demo.</p></div>
        <div><h2 className="font-semibold">Profile</h2><p>Understand schema, nulls, cardinality and distributions.</p></div>
        <div><h2 className="font-semibold">Assess Quality</h2><p>Run deterministic checks and calculate explainable quality scores. No LLM required.</p></div>
        <div><h2 className="font-semibold">AI Insights</h2><p>Coming next. Planned assistance built on profiling and quality results.</p></div>
      </section>
    </main>
  )
}
