'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getProject, createMilestone, completeMilestone, getClient, deleteMilestone, getInvoicePdf } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Calendar, Plus, FileText, Check, Trash2, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'

interface Milestone {
  id: string
  title: string
  description: string | null
  amount_inr: number
  due_date: string | null
  status: 'pending' | 'complete'
  invoice_id: string | null
  completed_at: string | null
}

interface Project {
  id: string
  title: string
  description: string | null
  client_id: string
  value_inr: number
  deadline: string | null
  status: string
  milestones?: Milestone[]
}

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const [project, setProject] = useState<Project | null>(null)
  const [client, setClient] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Add Milestone Form state
  const [milestoneTitle, setMilestoneTitle] = useState('')
  const [milestoneDescription, setMilestoneDescription] = useState('')
  const [milestoneAmount, setMilestoneAmount] = useState('')
  const [milestoneDueDate, setMilestoneDueDate] = useState('')
  const [addingMilestone, setAddingMilestone] = useState(false)

  const fetchProjectDetails = async () => {
    try {
      const projData = await getProject(projectId)
      setProject(projData)

      if (projData.client_id) {
        const clientData = await getClient(projData.client_id)
        setClient(clientData)
      }
    } catch (err: any) {
      toast.error('FAILED TO FETCH PROJECT DETAILS: ' + err.message?.toUpperCase())
      router.push('/projects')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjectDetails()
  }, [projectId])

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!milestoneTitle.trim() || !milestoneAmount.trim() || !milestoneDueDate.trim()) {
      toast.error('MILESTONE TITLE, AMOUNT, AND DUE DATE REQUIRED')
      return
    }

    setAddingMilestone(true)
    try {
      await createMilestone({
        project_id: projectId,
        title: milestoneTitle.trim(),
        description: milestoneDescription.trim() || undefined,
        amount_inr: parseFloat(milestoneAmount),
        due_date: milestoneDueDate
      })

      toast.success('MILESTONE ADDED')
      setMilestoneTitle('')
      setMilestoneDescription('')
      setMilestoneAmount('')
      setMilestoneDueDate('')
      fetchProjectDetails()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO ADD MILESTONE')
    } finally {
      setAddingMilestone(false)
    }
  }

  const handleCompleteMilestone = async (milestoneId: string) => {
    const loadingToast = toast.loading('COMPLETING MILESTONE & COMPILING BILL IN BACKGROUND...')
    try {
      await completeMilestone(milestoneId)
      toast.dismiss(loadingToast)
      toast.success('MILESTONE COMPLETED! BILL SENT.')
      fetchProjectDetails()
    } catch (err: any) {
      toast.dismiss(loadingToast)
      toast.error(err.message?.toUpperCase() || 'FAILED TO COMPLETE MILESTONE')
    }
  }

  const handleDeleteMilestone = async (milestoneId: string) => {
    if (!confirm('DELETE THIS MILESTONE?')) return
    try {
      await deleteMilestone(milestoneId)
      toast.success('MILESTONE DELETED')
      fetchProjectDetails()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO DELETE MILESTONE')
    }
  }

  const handleDownloadInvoice = async (invoiceId: string) => {
    const loadingToast = toast.loading('GENERATING PDF signed URL...')
    try {
      const data = await getInvoicePdf(invoiceId)
      toast.dismiss(loadingToast)
      if (data.pdf_url) {
        window.open(data.pdf_url, '_blank')
      } else {
        toast.error('PDF URL NOT RETURNED')
      }
    } catch (err: any) {
      toast.dismiss(loadingToast)
      toast.error(err.message?.toUpperCase() || 'FAILED TO GENERATE PDF')
    }
  }

  if (loading || !project) {
    return (
      <div className="font-mono text-[11px] text-text-secondary uppercase">
        LOADING DETAILS...
      </div>
    )
  }

  const milestonesList = project.milestones || []

  return (
    <div className="space-y-6">
      
      {/* Navigation Back */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => router.push('/projects')}
          className="text-text-secondary hover:text-text-primary transition-colors flex items-center space-x-1.5 uppercase text-[11px] font-semibold tracking-wider cursor-pointer"
        >
          <ArrowLeft size={14} />
          <span>Back to Projects</span>
        </button>
      </div>

      {/* Grid: Overview + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Main Details block (8 cols) */}
        <div className="lg:col-span-8 bg-surface border border-border-hairline p-6 space-y-4">
          <div>
            <span className="font-mono text-[11px] text-text-secondary uppercase">
              PROJECT ID: {project.id.slice(0, 8)}
            </span>
            <h1 className="font-inter font-medium text-[20px] tracking-[-0.02em] text-text-primary uppercase mt-1">
              {project.title}
            </h1>
          </div>

          <p className="text-text-secondary text-[13px] leading-relaxed whitespace-pre-wrap">
            {project.description || 'No description provided for this contract.'}
          </p>

          <div className="border-t border-border-hairline pt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <span className="block font-inter text-[11px] uppercase tracking-wider text-text-secondary">Client Context</span>
              <span className="block font-inter text-[13px] text-text-primary font-medium mt-0.5">{client?.name || '—'}</span>
            </div>
            <div>
              <span className="block font-inter text-[11px] uppercase tracking-wider text-text-secondary">Valuation</span>
              <span className="block font-mono text-[13px] text-text-primary font-medium mt-0.5">{formatCurrency(project.value_inr)}</span>
            </div>
            <div>
              <span className="block font-inter text-[11px] uppercase tracking-wider text-text-secondary">Deadline</span>
              <span className="block font-mono text-[13px] text-text-primary font-medium mt-0.5">{formatDate(project.deadline)}</span>
            </div>
          </div>
        </div>

        {/* Sidebar Info (4 cols) */}
        <div className="lg:col-span-4 bg-surface border border-border-hairline p-6 flex flex-col justify-between">
          <div>
            <span className="font-inter text-[11px] uppercase tracking-wider text-text-secondary block">Project Progress</span>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between font-mono text-[13px]">
                <span className="text-text-secondary">Total Milestones</span>
                <span>{milestonesList.length}</span>
              </div>
              <div className="flex justify-between font-mono text-[13px]">
                <span className="text-text-secondary">Completed</span>
                <span className="text-success">
                  {milestonesList.filter((m) => m.status === 'complete').length}
                </span>
              </div>
            </div>
          </div>
          <div className="border-t border-border-hairline pt-4 mt-4">
            <span className="font-inter text-[11px] uppercase tracking-wider text-text-secondary block">Client Email</span>
            <span className="font-mono text-[13px] text-text-primary block mt-1 break-all">{client?.email || '—'}</span>
          </div>
        </div>

      </div>

      {/* Milestones list + Quick Add Form */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Milestones (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <h2 className="font-inter font-medium text-[14px] uppercase tracking-wide text-text-primary">
            Contract Milestones
          </h2>

          {milestonesList.length > 0 ? (
            <div className="space-y-3">
              {milestonesList.map((m) => (
                <div key={m.id} className="bg-surface border border-border-hairline p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-inter text-[13px] font-medium text-text-primary">{m.title}</h3>
                      {m.status === 'complete' ? (
                        <span className="px-2 py-0.5 text-[9px] font-mono font-semibold bg-[#1A3A1A] text-[#22C55E] uppercase">COMPLETE</span>
                      ) : (
                        <span className="px-2 py-0.5 text-[9px] font-mono font-semibold bg-[#3A2A0A] text-[#F59E0B] uppercase">PENDING</span>
                      )}
                    </div>
                    {m.description && <p className="text-[12px] text-text-secondary">{m.description}</p>}
                    
                    <div className="flex items-center space-x-4 pt-1 font-mono text-[11px] text-text-secondary">
                      <span>Valuation: {formatCurrency(m.amount_inr)}</span>
                      <span>Due: {formatDate(m.due_date)}</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 shrink-0">
                    {m.status === 'complete' ? (
                      m.invoice_id ? (
                        <button
                          onClick={() => handleDownloadInvoice(m.invoice_id!)}
                          className="bg-[#111111] text-text-primary border border-border-strong font-inter text-[11px] font-semibold uppercase px-3 py-1.5 hover:border-border-active transition-colors flex items-center space-x-1 cursor-pointer"
                        >
                          <FileText size={12} />
                          <span>GET INVOICE</span>
                        </button>
                      ) : (
                        <span className="font-mono text-[11px] text-text-secondary uppercase">NO INVOICE</span>
                      )
                    ) : (
                      <>
                        <button
                          onClick={() => handleCompleteMilestone(m.id)}
                          className="bg-accent text-accent-inverse font-inter text-[11px] font-semibold uppercase px-3 py-1.5 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors flex items-center space-x-1 cursor-pointer"
                        >
                          <Check size={12} />
                          <span>MARK COMPLETE</span>
                        </button>
                        <button
                          onClick={() => handleDeleteMilestone(m.id)}
                          className="text-text-secondary hover:text-danger p-1.5 transition-colors cursor-pointer"
                        >
                          <Trash2 size={13} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-surface border border-border-hairline p-8 text-center uppercase font-inter text-[11px] text-text-secondary">
              NO MILESTONES SCHEDULED FOR THIS CONTRACT.
            </div>
          )}
        </div>

        {/* Right Column: Quick Add (4 cols) */}
        <div className="lg:col-span-4 bg-surface border border-border-hairline p-6 h-fit">
          <h2 className="font-inter font-medium text-[14px] uppercase tracking-wide text-text-primary border-bottom border-border-hairline pb-2 mb-4">
            Add Milestone
          </h2>

          <form onSubmit={handleAddMilestone} className="space-y-4">
            <div>
              <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                Milestone Title *
              </label>
              <input
                type="text"
                value={milestoneTitle}
                onChange={(e) => setMilestoneTitle(e.target.value)}
                disabled={addingMilestone}
                placeholder="E.G. FIRST SPRINT DELIVERABLE"
                className="w-full"
                required
              />
            </div>

            <div>
              <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                Description (Optional)
              </label>
              <textarea
                value={milestoneDescription}
                onChange={(e) => setMilestoneDescription(e.target.value)}
                disabled={addingMilestone}
                rows={2}
                placeholder="E.G. DEVELOPMENT OF LOGIN AND INTEGRATING AUTH HOOKS..."
                className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none resize-none"
              />
            </div>

            <div>
              <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                Amount (INR) *
              </label>
              <input
                type="number"
                value={milestoneAmount}
                onChange={(e) => setMilestoneAmount(e.target.value)}
                disabled={addingMilestone}
                placeholder="E.G. 50000"
                className="w-full font-mono text-[13px]"
                required
              />
            </div>

            <div>
              <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                Due Date *
              </label>
              <input
                type="date"
                value={milestoneDueDate}
                onChange={(e) => setMilestoneDueDate(e.target.value)}
                disabled={addingMilestone}
                className="w-full font-mono text-[13px]"
                required
              />
            </div>

            <button
              type="submit"
              disabled={addingMilestone}
              className="w-full bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase py-2.5 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer flex items-center justify-center space-x-1"
            >
              <Plus size={12} />
              <span>{addingMilestone ? 'ADDING...' : 'ADD MILESTONE'}</span>
            </button>
          </form>
        </div>

      </div>

    </div>
  )
}
