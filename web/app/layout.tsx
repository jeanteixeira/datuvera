import Link from 'next/link'
import type { ReactNode } from 'react'
import './globals.css'

export const metadata = { title: 'Datuvera', description: 'Know your data. Trust your data.' }

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <nav aria-label="Main navigation" className="border-b bg-white px-6 py-4 flex gap-6 items-center">
          <Link href="/" className="font-semibold">Datuvera</Link>
          <Link href="/">Home</Link>
          <Link href="/sources">Sources</Link>
        </nav>
        {children}
      </body>
    </html>
  )
}
