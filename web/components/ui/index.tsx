import type { ReactNode, ButtonHTMLAttributes } from 'react'
import Link from 'next/link'

export function Button({ variant = 'primary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }) {
  return <button className={`button button-${variant} ${className}`} {...props} />
}
export function ActionLink({ href, children, secondary = false }: { href: string; children: ReactNode; secondary?: boolean }) {
  return <Link className={`button button-${secondary ? 'secondary' : 'primary'}`} href={href}>{children}</Link>
}
export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{children}</section>
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: string }) {
  const semantic: Record<string, string> = { passed: 'success', low: 'success', enabled: 'success', warning: 'warning', medium: 'warning', failed: 'danger', high: 'danger', error: 'danger', disabled: 'neutral', info: 'info', success: 'success', danger: 'danger', neutral: 'neutral' }
  return <span className={`badge badge-${semantic[tone] || 'neutral'}`}>{children}</span>
}
export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <header className="page-header"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="muted mt-2">{description}</p>}</div>{action && <div className="header-actions">{action}</div>}</header>
}
export function SectionHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <div className="section-header"><div><h2>{title}</h2>{description && <p className="muted text-sm mt-1">{description}</p>}</div>{action}</div>
}
export function MetricCard({ label, value, detail }: { label: string; value: ReactNode; detail?: string }) {
  return <Card><p className="metric-label">{label}</p><p className="metric-value">{value}</p>{detail && <p className="muted text-sm mt-2">{detail}</p>}</Card>
}
export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-mark" aria-hidden="true">—</div><h3>{title}</h3><p className="muted">{description}</p>{action && <div className="mt-5">{action}</div>}</div>
}
export function LoadingState({ children }: { children: ReactNode }) {
  return <div className="state-message" role="status"><span className="spinner" aria-hidden="true" />{children}</div>
}
export function ErrorState({ children, retry }: { children: ReactNode; retry?: () => void }) {
  return <div className="error-state" role="alert"><p>{children}</p>{retry && <Button variant="secondary" onClick={retry}>Try again</Button>}</div>
}
export function DataTable({ children, label }: { children: ReactNode; label: string }) {
  return <div className="table-scroll" role="region" aria-label={label} tabIndex={0}><table>{children}</table></div>
}
export function ruleLabel(rule: string) { return ({not_null:'Not null',unique:'Unique',email_format:'Email format',allowed_values:'Allowed values',min_value:'Min value',max_value:'Max value'} as Record<string,string>)[rule] || rule }
