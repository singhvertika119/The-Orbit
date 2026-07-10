'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'

export default function SignupPage() {
  const router = useRouter()
  const { user, profile, loading } = useAuth()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && user) {
      if (profile && !profile.onboarded) {
        router.push('/onboarding')
      } else {
        router.push('/')
      }
    }
  }, [user, profile, loading, router])

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      toast.error('EMAIL AND PASSWORD REQUIRED')
      return
    }

    if (password.length < 6) {
      toast.error('PASSWORD MUST BE AT LEAST 6 CHARACTERS')
      return
    }

    setAuthLoading(true)
    try {
      const { error, data } = await supabase.auth.signUp({
        email,
        password
      })

      if (error) {
        toast.error(error.message.toUpperCase())
      } else {
        // Check if user is auto-confirmed or needs email confirmation
        if (data.session) {
          toast.success('REGISTRATION SUCCESSFUL')
          router.push('/onboarding')
        } else {
          toast.success('VERIFICATION EMAIL SENT. PLEASE CHECK YOUR INBOX.')
          router.push('/auth/login')
        }
      }
    } catch (err: any) {
      toast.error('UNEXPECTED ERROR OCCURRED')
    } finally {
      setAuthLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center font-mono text-[11px] uppercase tracking-widest text-text-secondary">
        LOADING...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-surface border border-border-hairline p-8">
        
        {/* Logo */}
        <div className="text-center mb-8">
          <span className="font-inter font-semibold text-[16px] tracking-[-0.04em] uppercase text-text-primary">
            GIG.AI
          </span>
          <p className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mt-1">
            Freelance Command Centre
          </p>
        </div>

        <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary text-center mb-6 uppercase">
          Register Account
        </h1>

        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={authLoading}
              placeholder="YOUR.EMAIL@DOMAIN.COM"
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Password (6+ characters)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={authLoading}
              placeholder="••••••••••••"
              className="w-full"
              required
            />
          </div>

          <button
            type="submit"
            disabled={authLoading}
            className="w-full bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase py-3 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
          >
            {authLoading ? 'LOADING...' : 'REGISTER ACCOUNT'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link 
            href="/auth/login" 
            className="font-inter text-[11px] tracking-[0.06em] uppercase text-text-secondary hover:text-text-primary transition-colors"
          >
            Already registered? Access Account
          </Link>
        </div>

      </div>
    </div>
  )
}
