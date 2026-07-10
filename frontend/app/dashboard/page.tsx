'use client'

import React, { useState, useEffect } from 'react'
import { getDigestToday, listInvoices, listProjects } from '@/lib/api'
import { RefreshCw, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'

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
      console.error('Error fetching stats:', err)
    } finally {
      setLoadingMetrics(false)
    }
  }

  useEffect(() => {
    fetchDigest()
    fetchMetrics()
  }, [])

  // Stat currency formatter: no decimals for zero state, use toLocaleString('en-IN') for real values
  const formatStatCurrency = (value: number) => {
    if (value === 0) return '₹0'
    return '₹' + Math.round(value).toLocaleString('en-IN')
  }

  return (
    <div className="space-y-6">
      
      {/* Header Panel */}
      <div className="border-bottom border-border-hairline pb-4">
        <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase">
          Today Dashboard
        </h1>
      </div>

      {/* Grid of Brutalist Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Metric 1 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Active Projects
          </span>
          <div className={`font-mono text-[24px] mt-1 ${
            metrics.activeProjects > 0 ? 'text-text-primary' : 'text-[#444444]'
          }`}>
            {loadingMetrics ? '—' : metrics.activeProjects}
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Unpaid Receivables
          </span>
          <div className={`font-mono text-[24px] mt-1 ${
            metrics.unpaidAmount > 0 ? 'text-danger' : 'text-[#444444]'
          }`}>
            {loadingMetrics ? '—' : formatStatCurrency(metrics.unpaidAmount)}
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-surface border border-border-hairline p-4">
          <span className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary">
            Total Revenue Settled
          </span>
          <div className={`font-mono text-[24px] mt-1 ${
            metrics.paidAmount > 0 ? 'text-success' : 'text-[#444444]'
          }`}>
            {loadingMetrics ? '—' : formatStatCurrency(metrics.paidAmount)}
          </div>
        </div>

      </div>

      {/* Split layout: Actions + Digest */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left column: Actions (5 cols) */}
        <div className="lg:col-span-5 flex flex-col">
          <div className="bg-surface border border-border-hairline p-6 min-h-[200px] flex flex-col justify-between flex-1">
            <div className="space-y-4 flex flex-col flex-1">
              <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase border-bottom border-border-hairline pb-2 mb-4 shrink-0">
                Action Items Today
              </h2>
              
              {loadingMetrics ? (
                <div className="font-mono text-[11px] text-text-secondary uppercase">
                  LOADING ACTIONS...
                </div>
              ) : metrics.dueToday.length > 0 ? (
                <ul className="space-y-3 overflow-y-auto">
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
                <div className="flex-1 flex flex-col items-center justify-center py-6 text-center">
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
        </div>

        {/* Right column: Morning Digest (7 cols) */}
        <div className="lg:col-span-7">
          <div className="bg-surface border border-border-hairline p-6 space-y-4">
            <div className="flex items-center justify-between border-bottom border-border-hairline pb-2">
              <div className="flex items-center space-x-2">
                <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase">
                  Morning Digest
                </h2>
                {digest && !loadingDigest && (
                  <span className="font-mono text-[9px] uppercase tracking-wider text-[#333333] font-semibold">
                    {cached ? '· CACHED' : '· LIVE RUN'}
                  </span>
                )}
              </div>
              <button
                onClick={() => {
                  fetchDigest(true)
                  fetchMetrics()
                }}
                disabled={loadingDigest}
                className="text-text-secondary hover:text-text-primary font-inter text-[11px] font-semibold uppercase tracking-wider flex items-center space-x-1.5 transition-colors cursor-pointer"
              >
                <RefreshCw size={11} className={loadingDigest ? 'animate-spin' : ''} />
                <span>{loadingDigest ? 'LOADING...' : 'REFRESH'}</span>
              </button>
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
                <div className="text-[11px] uppercase font-inter font-medium text-text-muted">
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
