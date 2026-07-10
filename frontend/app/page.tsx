'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'

export default function RootPage() {
  const router = useRouter()
  const { user, profile, loading } = useAuth()

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push('/auth/login')
      } else if (profile && !profile.onboarded) {
        router.push('/onboarding')
      } else {
        router.push('/dashboard')
      }
    }
  }, [user, profile, loading, router])

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center font-mono text-[11px] uppercase tracking-widest text-text-secondary">
      LOADING...
    </div>
  )
}
