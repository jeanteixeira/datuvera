"use client"
import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'

const items = [['/','Overview','overview'],['/sources','Data Sources','sources'],['/datasets','Datasets','datasets'],['/quality','Quality','quality'],['/ai-insights','AI Insights','ai']] as const
function Icon({ name }: { name: string }) {
  const paths: Record<string,string> = { overview:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z', sources:'M4 6c0-4 16-4 16 0s-16 4-16 0v12c0 4 16 4 16 0V6 M4 12c0 4 16 4 16 0', datasets:'M3 4h18v16H3z M3 10h18 M9 4v16', quality:'M12 3l8 4v6c0 4-8 8-8 8s-8-4-8-8V7z M8 12l3 3 5-6', ai:'M4 18V6 M10 18v-8 M16 18V4 M22 18v-5' }
  return <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>
}
export default function AppShell({ children }: { children: ReactNode }) {
  const path = usePathname()
  const [open, setOpen] = useState(false)
  const context = path.startsWith('/sources/add') ? 'New connection' : path.includes('/datasets/') ? 'Dataset workspace' : items.find(([href]) => href !== '/' && path.startsWith(href))?.[1] || 'Overview'
  return <div className="app-shell">
    <a href="#main-content" className="skip-link">Skip to content</a>
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`} aria-label="Application sidebar">
      <Link href="/" className="brand" onClick={() => setOpen(false)}><span className="brand-mark" aria-hidden="true">D</span><span>Datuvera<small>DATA QUALITY PLATFORM</small></span></Link>
      <p className="nav-label">Workspace</p>
      <nav aria-label="Main navigation">{items.map(([href,label,icon]) => { const active=href==='/' ? path==='/' : path.startsWith(href); return <Link key={href} href={href} className={`nav-item ${active?'active':''}`} aria-current={active?'page':undefined} onClick={() => setOpen(false)}><Icon name={icon} />{label}</Link> })}</nav>
      <div className="sidebar-footer"><a className="nav-item" href="https://github.com/jeanteixeira/datuvera#readme">Documentation <span aria-hidden="true">↗</span></a><a className="nav-item" href="https://github.com/jeanteixeira/datuvera">GitHub <span aria-hidden="true">↗</span></a><p className="muted text-xs px-3 mt-4">Know your data. Trust your data.</p></div>
    </aside>
    <div className="app-body"><header className="topbar"><button className="menu-button button button-secondary" aria-expanded={open} aria-label="Toggle navigation" onClick={() => setOpen(!open)}>Menu</button><div className="topbar-context"><span className="muted">Workspace</span><span aria-hidden="true">/</span><span>{context}</span></div><a href="https://github.com/jeanteixeira/datuvera" className="topbar-link">Open source <span aria-hidden="true">↗</span></a></header><main id="main-content" className="page-content">{children}</main></div>
  </div>
}
