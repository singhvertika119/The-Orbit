'use client'

import React, { useState, useEffect } from 'react'
import { getDigestToday, listInvoices, listProjects } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { RefreshCw, Play, ArrowRight, Calendar, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

interface DigestData {
  digest_text: string
  cached: boolean
  metrics?: {
    active_projects_count: number
    milestones_due_today_count: number
    overdue_invoices_count: number
    total_unpaid_amount: number
    total_paid_amount: number
    due_today_titles: string[]
  }
}

export default function TodayDashboard() {
  const [digest, setDigest] = useState<string>('')
  const [cached, setCached] = useState<boolean>(true)
  const [metrics, setMetrics] = useState<any>({
    activeProjects: 0,
    dueToday: [] as string[],
    unpaidAmount: 0,
    paidAmount: 0
  })
  
  const [loadingDigest, setLoadingDigest] = useState<boolean>(true)
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(true)

  const fetchDigest = async (forceRefresh = false) => {
    setLoadingDigest(true)
    try {
      const data = await getDigestToday(forceRefresh)
      setDigest(data.digest_text || 'No daily operations summary available. Click refresh to write one.')
      setCached(data.cached ?? true)
      if (forceRefresh) {
        toast.success('DAILY BRIEFING REGENERATED')
      }
    } catch (err: any) {
      toast.error('FAILED TO GENERATE DAILY BRIEFING: ' + err.message?.toUpperCase())
    } finally {
      setLoadingDigest(false)
    }
  }

  const fetchMetrics = async () => {
    setLoadingMetrics(true)
    try {
      const [projects, invoices] = await Promise.all([
        listProjects(),
        listInvoices()
      ])

      const active = projects.filter((p: any) => p.status === 'active').length
      
      // Calculate unpaid, paid totals
      let unpaidTotal = 0
      let paidTotal = 0
      invoices.forEach((inv: any) => {
        const val = parseFloat(inv.total_inr || 0)
        if (inv.payment_status === 'paid') {
          paidTotal += val
        } else {
          unpaidTotal += val
        }
      })

      // Fetch pending milestones due today from projects
      const todayStr = new Date().toISOString().split('T')[0]
      const dueTodayTitles: string[] = []
      projects.forEach((proj: any) => {
        if (proj.milestones && Array.isArray(proj.milestones)) {
          proj.milestones.forEach((m: any) => {
            if (m.status === 'pending' && m.due_date === todayStr) {
              dueTodayTitles.push(`${proj.title} : ${m.title}`)
            }
          })
        }
      })

      setMetrics({
        activeProjects: active,
        dueToday: dueTodayTitles,
        unpaidAmount: unpaidTotal,
        paidAmount: paidTotal
      })
    } catch (err) {
      console.error('Error fetching dashboard stats:', err)
    } finally {
      setLoadingMetrics(false)
    }
  }

  useEffect(() => {
    fetchDigest()
    fetchMetrics()
  }, [])

  return (
    <div className="space-y-6">
      
      {/* Header Panel */}
      <div className="flex items-center justify-between border-bottom border-border-hairline pb-4">
        <div>
          <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
            COMMAND CONTROL
          </span>
          <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
            Today Dashboard
          </h1>
        </div>
        <button
          onClick={() => {
            fetchDigest(true)
            fetchMetrics()
          }}
          disabled={loadingDigest}
          className="bg-surface hover:bg-surface-raised border border-border-strong text-text-primary px-3 py-1.5 font-inter text-[11px] font-semibold uppercase tracking-wider flex items-center space-x-1.5 transition-colors cursor-pointer"
        >
          <RefreshCw size={12} className={loadingDigest ? 'animate-spin' : ''} />
          <span>{loadingDigest ? 'LOADING...' : 'REFRESH CONTEXT'}</span>
        </button>
      </div>

      {/* Grid of Brutalist Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Metric 1 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Active Projects
          </span>
          <div className="font-mono text-[24px] text-text-primary mt-2">
            {loadingMetrics ? '---' : String(metrics.activeProjects).padStart(2, '0')}
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Unpaid Receivables
          </span>
          <div className="font-mono text-[24px] text-danger mt-2">
            {loadingMetrics ? '---' : formatCurrency(metrics.unpaidAmount)}
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Total Revenue Settled
          </span>
          <div className="font-mono text-[24px] text-success mt-2">
            {loadingMetrics ? '---' : formatCurrency(metrics.paidAmount)}
          </div>
        </div>

      </div>

      {/* Split layout: Actions + Digest */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left column: Actions (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-surface border border-border-hairline p-6">
            <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase border-bottom border-border-hairline pb-2 mb-4">
              Action Items Today
            </h2>
            
            {loadingMetrics ? (
              <div className="font-mono text-[11px] text-text-secondary uppercase">
                LOADING ACTIONS...
              </div>
            ) : metrics.dueToday.length > 0 ? (
              <ul className="space-y-3">
                {metrics.dueToday.map((item: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-3 p-3 bg-surface-raised border border-border-strong">
                    <Calendar size={14} className="text-warning mt-0.5 shrink-0" />
                    <div>
                      <span className="font-mono text-[11px] text-warning uppercase block">
                        DUE TODAY
                      </span>
                      <span className="font-inter text-[13px] text-text-primary mt-1 block">
                        {item}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-8">
                <h3 className="font-inter text-[14px] text-text-primary uppercase">
                  All Clear
                </h3>
                <p className="font-inter text-[12px] text-text-secondary mt-1">
                  NO GIG MILESTONES ARE DUE TODAY.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right column: Operations Digest (7 cols) */}
        <div className="lg:col-span-7">
          <div className="bg-surface border border-border-hairline p-6 space-y-4">
            <div className="flex items-center justify-between border-bottom border-border-hairline pb-2">
              <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase">
                Operations Coach Briefing
              </h2>
              {digest && !loadingDigest && (
                <span className="font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 bg-surface-raised text-text-secondary">
                  {cached ? 'CACHED' : 'LIVE RUN'}
                </span>
              )}
            </div>

            {loadingDigest ? (
              <div className="space-y-4">
                <span className="font-mono text-[11px] text-text-secondary uppercase animate-pulse">
                  PROCESSING CONTEXT & ASSEMBLING DAILY DIGEST...
                </span>
                {/* Skeleton Block */}
                <div className="space-y-2">
                  <div className="h-4 bg-[#111111] border border-border-hairline animate-pulse" />
                  <div className="h-4 bg-[#111111] border border-border-hairline w-5/6 animate-pulse" />
                  <div className="h-4 bg-[#111111] border border-border-hairline w-4/6 animate-pulse" />
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-[11px] uppercase font-inter font-medium text-text-secondary">
                  AGENT OUTPUT
                </div>
                <div className="bg-[#0A0A0A] border-l-2 border-white p-4 font-mono text-[12px] leading-relaxed text-text-primary whitespace-pre-wrap select-text">
                  {digest}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  )
}
