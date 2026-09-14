export type RunSummary = {
  id: number; source_id: number; schema: string; table: string;
  overall_score: number; completeness_score: number | null;
  uniqueness_score: number | null; validity_score: number | null; created_at: string
}
export const metrics = {
  overall_score: 'Overall', completeness_score: 'Completeness',
  uniqueness_score: 'Uniqueness', validity_score: 'Validity'
} as const
export type Metric = keyof typeof metrics
export function delta(latest: number | null | undefined, previous: number | null | undefined): number | null {
  if (latest == null || previous == null) return null
  const change = Number((latest - previous).toFixed(2))
  return change === 0 ? 0 : change
}
export function formatScore(score: number | null | undefined): string { return score == null ? 'N/A' : score.toFixed(2) }
export function formatDelta(change: number | null): string { return change === null ? 'N/A' : `${change > 0 ? '+' : ''}${change.toFixed(2)}` }
export function changeLabel(change: number | null): string { return change === null ? 'Not comparable' : change > 0 ? 'Increase' : change < 0 ? 'Decrease' : 'Unchanged' }
export function comparison(runs: RunSummary[], metric: Metric) {
  const latest = runs[0]?.[metric] ?? null
  const previous = runs[1]?.[metric] ?? null
  return {latest, previous, change: delta(latest, previous)}
}
export function chronological(runs: RunSummary[]) { return [...runs].reverse() }
export function localTimestamp(timestamp: string) { return new Date(timestamp).toLocaleString('en-US') }
