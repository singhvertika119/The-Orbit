'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { updateProfile } from '@/lib/api'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const { user, profile, loading, refreshProfile } = useAuth()
  
  const [name, setName] = useState('')
  const [upiId, setUpiId] = useState('')
  const [gstNumber, setGstNumber] = useState('')
  const [bankDetails, setBankDetails] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (profile) {
      setName(profile.name || '')
      setUpiId(profile.upi_id || '')
      setGstNumber(profile.gst_number || '')
      setBankDetails(profile.bank_details || '')
    }
  }, [profile])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      toast.error('NAME IS REQUIRED')
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

      toast.success('SETTINGS UPDATED')
      await refreshProfile()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO UPDATE SETTINGS')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="font-mono text-[11px] text-text-secondary uppercase">
        LOADING SETTINGS...
      </div>
    )
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="border-bottom border-border-hairline pb-4">
        <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
          WORKSPACE PARAMETERS
        </span>
        <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
          Freelancer Settings
        </h1>
      </div>

      <div className="max-w-xl bg-surface border border-border-hairline p-6">
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={saving}
              placeholder="VERTIKA SINGH"
              className="w-full"
              required
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              UPI ID (Payments recipient address)
            </label>
            <input
              type="text"
              value={upiId}
              onChange={(e) => setUpiId(e.target.value)}
              disabled={saving}
              placeholder="YOURNAME@OKBANK"
              className="w-full font-mono text-[13px]"
              required
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              GSTIN (Tax registration number)
            </label>
            <input
              type="text"
              value={gstNumber}
              onChange={(e) => setGstNumber(e.target.value)}
              disabled={saving}
              maxLength={15}
              placeholder="07AAAAA1111A1Z1"
              className="w-full font-mono text-[13px]"
            />
          </div>

          <div>
            <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
              Settlement Bank Details
            </label>
            <textarea
              value={bankDetails}
              onChange={(e) => setBankDetails(e.target.value)}
              disabled={saving}
              rows={4}
              placeholder="BANK NAME: HDFC BANK&#10;ACCOUNT NUMBER: 5010001234567&#10;IFSC CODE: HDFC0000001"
              className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none resize-none"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
            >
              {saving ? 'SAVING...' : 'SAVE SETTINGS'}
            </button>
          </div>
        </form>
      </div>

    </div>
  )
}
