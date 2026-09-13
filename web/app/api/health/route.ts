import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const res = await fetch(process.env.API_URL ? `${process.env.API_URL}/health` : 'http://localhost:8000/health')
    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    return NextResponse.json({ status: 'unreachable' }, { status: 503 })
  }
}
