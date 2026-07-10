'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { updateProfile } from '@/lib/api'
import toast from 'react-hot-toast'

export default function OnboardingPage() {
  const router = useRouter()
  const { user, profile, loading, refreshProfile } = useAuth()
  
  const [name, setName] = useState('')
  const [upiId, setUpiId] = useState('')
  const [gstNumber, setGstNumber] = useState('')
  const [bankDetails, setBankDetails] = useState('')
  const [saving, setSaving] = useState(false)

  // Route protection: redirect to login if not authenticated, or to dashboard if already onboarded
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push('/auth/login')
      } else if (profile?.onboarded) {
        router.push('/dashboard')
      }
    }
  }, [user, profile, loading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      toast.error('FULL NAME IS REQUIRED')
      return
    }

    if (!upiId.trim() || !upiId.includes('@')) {
      toast.error('VALID UPI ID IS REQUIRED (E.G. NAME@OKBANK)')
      return
    }

    setSaving(true)
    try {
      await updateProfile({
        name: name.trim(),
        upi_id: upiId.trim().toLowerCase(),
        gst_number: gstNumber.trim() ? gstNumber.trim().toUpperCase() : undefined,
        bank_details: bankDetails.trim() || undefined
      })

      toast.success('PROFILE SAVED SUCCESSFULLY')
      await refreshProfile()
      router.push('/dashboard')
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO SAVE PROFILE')
    } finally {
      setSaving(false)
    }
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center font-mono text-[11px] uppercase tracking-widest text-text-secondary">
        LOADING...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-surface border border-border-hairline p-8">
        
        {/* Branding Header */}
        <div className="text-center mb-8">
          <span className="font-inter font-semibold text-[16px] tracking-[-0.04em] uppercase text-text-primary">
            GIG.AI
          </span>
          <p className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mt-1">
             freelancers command centre
          </p>
        </div>

        <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary mb-2 uppercase text-center">
          Onboarding
        </h1>
        <p className="font-inter text-[11px] text-text-secondary text-center mb-6 uppercase tracking-wider">
          Complete profile to initialize agent services & invoicing
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Full Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={saving}
              placeholder="E.G. VERTIKA SINGH"
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              UPI ID * (Indian Payment gateway destination)
            </label>
            <input
              type="text"
              value={upiId}
              onChange={(e) => setUpiId(e.target.value)}
              disabled={saving}
              placeholder="E.G. VERTIKASINGH@OKAXIS"
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              GSTIN (Optional)
            </label>
            <input
              type="text"
              value={gstNumber}
              onChange={(e) => setGstNumber(e.target.value)}
              disabled={saving}
              maxLength={15}
              placeholder="E.G. 07AAAAA1111A1Z1"
              className="w-full font-mono text-[13px]"
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Bank Details (Optional)
            </label>
            <textarea
              value={bankDetails}
              onChange={(e) => setBankDetails(e.target.value)}
              disabled={saving}
              rows={3}
              placeholder="BANK: HDFC BANK&#10;A/C NO: 501002342342&#10;IFSC CODE: HDFC0000012"
              className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none resize-none"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="w-full bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase py-3 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
            >
              {saving ? 'SAVING...' : 'COMPLETE ONBOARDING'}
            </button>
          </div>
        </form>

      </div>
    </div>
  )
}
