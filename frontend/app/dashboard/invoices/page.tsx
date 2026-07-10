'use client'

import React, { useState, useEffect } from 'react'
import { listInvoices, markInvoicePaid, triggerFollowup, getInvoicePdf } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { FileText, Check, AlertTriangle, Send, X, Clipboard } from 'lucide-react'
import toast from 'react-hot-toast'

interface Invoice {
  id: string
  invoice_number: string
  client_name: string
  client_email: string
  amount_inr: number
  gst_amount: number
  total_inr: number
  payment_status: 'sent' | 'paid' | 'overdue'
  due_date: string | null
  created_at: string
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  
  // Followup Draft Modal State
  const [followupModalOpen, setFollowupModalOpen] = useState(false)
  const [followupSubject, setFollowupSubject] = useState('')
  const [followupBody, setFollowupBody] = useState('')
  const [targetInvoiceNo, setTargetInvoiceNo] = useState('')

  const fetchInvoices = async () => {
    setLoading(true)
    try {
      const data = await listInvoices()
      setInvoices(data)
    } catch (err: any) {
      toast.error('FAILED TO FETCH INVOICES: ' + err.message?.toUpperCase())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInvoices()
  }, [])

  const handleMarkPaid = async (id: string) => {
    if (!confirm('MARK THIS INVOICE AS PAID?')) return
    try {
      await markInvoicePaid(id)
      toast.success('INVOICE SET TO PAID')
      fetchInvoices()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO MARK PAID')
    }
  }

  const handleTriggerFollowup = async (invoice: Invoice) => {
    const loadingToast = toast.loading('RUNNING REMINDER WRITER AGENT...')
    try {
      const data = await triggerFollowup(invoice.id)
      toast.dismiss(loadingToast)
      toast.success('REMINDER DRAFT COMPILED')
      
      setTargetInvoiceNo(invoice.invoice_number)
      setFollowupSubject(data.subject || 'Payment Reminder')
      setFollowupBody(data.body || '')
      setFollowupModalOpen(true)
    } catch (err: any) {
      toast.dismiss(loadingToast)
      toast.error(err.message?.toUpperCase() || 'AGENT RUN FAILED')
    }
  }

  const handleDownloadPdf = async (invoiceId: string) => {
    const loadingToast = toast.loading('SIGNING EXPORT PDF LINK...')
    try {
      const data = await getInvoicePdf(invoiceId)
      toast.dismiss(loadingToast)
      if (data.pdf_url) {
        window.open(data.pdf_url, '_blank')
      } else {
        toast.error('PDF URL NOT RETRIEVED')
      }
    } catch (err: any) {
      toast.dismiss(loadingToast)
      toast.error(err.message?.toUpperCase() || 'FAILED TO LOAD PDF')
    }
  }

  const handleCopyToClipboard = () => {
    const copyText = `Subject: ${followupSubject}\n\n${followupBody}`
    navigator.clipboard.writeText(copyText)
    toast.success('COPIED DRAFT TO CLIPBOARD')
  }

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#1A3A1A] text-[#22C55E] uppercase">PAID</span>
      case 'overdue':
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#3A0A0A] text-[#EF4444] uppercase">OVERDUE</span>
      case 'sent':
      default:
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#3A2A0A] text-[#F59E0B] uppercase">SENT</span>
    }
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="border-bottom border-border-hairline pb-4">
        <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
          FINANCIAL DIRECTORY
        </span>
        <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
          Settlement Invoices
        </h1>
      </div>

      {/* Main Table Area */}
      {loading ? (
        <div className="font-mono text-[11px] text-text-secondary uppercase">
          LOADING INVOICES...
        </div>
      ) : invoices.length > 0 ? (
        <div className="bg-surface border border-border-hairline overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface border-bottom border-border-hairline">
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Invoice No</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Client</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Gross Total</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Due Date</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Status</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-bottom border-border-hairline hover:bg-surface-raised transition-colors">
                  <td className="px-6 py-4 font-mono text-[13px] font-medium text-text-primary">
                    {inv.invoice_number}
                  </td>
                  <td className="px-6 py-4 font-inter text-[13px] text-text-secondary">
                    {inv.client_name}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-primary">
                    {formatCurrency(inv.total_inr)}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-secondary">
                    {formatDate(inv.due_date)}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(inv.payment_status)}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleDownloadPdf(inv.id)}
                      className="text-text-secondary hover:text-text-primary p-1.5 transition-colors cursor-pointer inline-flex items-center space-x-1 font-inter text-[11px] font-semibold uppercase tracking-wider bg-surface border border-border-strong px-2 py-1"
                      title="Download PDF"
                    >
                      <FileText size={12} />
                      <span className="hidden sm:inline">PDF</span>
                    </button>
                    {inv.payment_status !== 'paid' && (
                      <>
                        <button
                          onClick={() => handleMarkPaid(inv.id)}
                          className="bg-accent text-accent-inverse font-inter text-[11px] font-semibold uppercase px-2.5 py-1 transition-colors cursor-pointer border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong"
                        >
                          <Check size={12} className="inline mr-1" />
                          <span>PAID</span>
                        </button>
                        <button
                          onClick={() => handleTriggerFollowup(inv)}
                          className="bg-surface text-warning border border-border-strong font-inter text-[11px] font-semibold uppercase px-2.5 py-1 hover:border-border-active transition-colors cursor-pointer"
                          title="Generate Reminder Draft"
                        >
                          <Send size={11} className="inline mr-1" />
                          <span>FOLLOW UP</span>
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-16 bg-surface border border-border-hairline">
          <h3 className="font-inter text-[14px] text-text-primary uppercase">
            No Invoices Found
          </h3>
          <p className="font-inter text-[12px] text-text-secondary mt-1">
            INVOICES WILL GENERATE AUTOMATICALLY UPON MARKING MILESTONES COMPLETE.
          </p>
        </div>
      )}

      {/* Followup Reminder Draft Modal */}
      {followupModalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-border-strong w-full max-w-lg p-6 relative">
            <button
              onClick={() => setFollowupModalOpen(false)}
              className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>

            <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase border-bottom border-border-hairline pb-2 mb-4">
              Reminders Draft Compiler
            </h2>

            <div className="space-y-4">
              <div className="bg-[#0A0A0A] p-3 border border-border-hairline">
                <div className="text-[10px] text-text-secondary uppercase font-mono">Invoice Targeted</div>
                <div className="text-[13px] text-text-primary font-mono font-medium mt-1">{targetInvoiceNo}</div>
              </div>

              <div className="space-y-1">
                <div className="text-[11px] uppercase font-inter font-medium text-text-muted">
                  AGENT OUTPUT
                </div>
                <div className="bg-[#0A0A0A] border-l-2 border-white p-4 font-mono text-[12px] leading-relaxed text-text-primary whitespace-pre-wrap select-text max-h-[300px] overflow-y-auto">
                  <div className="font-bold text-[#FFFFFF] border-bottom border-[#1A1A1A] pb-2 mb-2">
                    Subject: {followupSubject}
                  </div>
                  {followupBody}
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setFollowupModalOpen(false)}
                  className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
                >
                  CLOSE
                </button>
                <button
                  type="button"
                  onClick={handleCopyToClipboard}
                  className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer flex items-center space-x-1"
                >
                  <Clipboard size={12} />
                  <span>COPY DRAFT</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
