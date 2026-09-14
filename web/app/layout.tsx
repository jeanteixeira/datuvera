import type { ReactNode } from 'react'
import AppShell from '../components/layout/AppShell'
import './globals.css'
export const metadata = { title: 'Datuvera — Data Quality', description: 'Know your data. Trust your data.' }
export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body><AppShell>{children}</AppShell></body></html>
}
