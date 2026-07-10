'use client'

import React, { useState, useEffect } from 'react'
import { parseBrief, scopeBrief, draftProposal, createProject, listClients } from '@/lib/api'
import { Cpu, Send, CheckSquare, Shield, DollarSign, FileText, Clipboard, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatCurrency } from '@/lib/utils'

interface ParsedBrief {
  brief_summary: string
  deliverables: string[]
  project_type: 'development' | 'design' | 'marketing' | 'consulting' | 'other'
}

interface ScopedBrief {
  scope_breakdown: string[]
  estimated_price_inr: number
  estimated_timeline_days: number
  risk_indicators: string[]
}

interface Proposal {
  subject: string
  body: string
}

export default function BriefParserPage() {
  const [step, setStep] = useState(1) // 1: input, 2: parsed, 3: scoped, 4: proposal
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<any[]>([])

  // Step 1: Input Raw Text
  const [rawText, setRawText] = useState('')

  // Step 2: Parsed Result State
  const [parsed, setParsed] = useState<ParsedBrief | null>(null)
  const [selectedDeliverables, setSelectedDeliverables] = useState<string[]>([])
  const [projectType, setProjectType] = useState<string>('development')

  // Step 3: Scope Results State
  const [scoped, setScoped] = useState<ScopedBrief | null>(null)
  
  // Custom project params before proposal draft
  const [projectTitle, setProjectTitle] = useState('')
  const [clientName, setClientName] = useState('')
  const [customPrice, setCustomPrice] = useState('')
  const [customTimeline, setCustomTimeline] = useState('')

  // Step 4: Final Proposal State
  const [proposal, setProposal] = useState<Proposal | null>(null)

  useEffect(() => {
    listClients().then(setClients).catch(console.error)
  }, [])

  // Step 1 -> Step 2
  const handleParse = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rawText.trim()) {
      toast.error('BRIEF TEXT REQUIRED')
      return
    }

    setLoading(true)
    try {
      const data = await parseBrief(rawText.trim())
      setParsed(data)
      setSelectedDeliverables(data.deliverables || [])
      setProjectType(data.project_type || 'development')
      setStep(2)
      toast.success('CLIENT BRIEF PARSED SUCCESSFULLY')
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'PARSING BRIEF FAILED')
    } finally {
      setLoading(false)
    }
  }

  // Step 2 -> Step 3
  const handleScope = async () => {
    if (selectedDeliverables.length === 0) {
      toast.error('SELECT AT LEAST ONE DELIVERABLE FOR SCOPING')
      return
    }

    setLoading(true)
    try {
      const data = await scopeBrief(
        parsed?.brief_summary || '',
        selectedDeliverables,
        projectType
      )
      setScoped(data)
      setCustomPrice(String(data.estimated_price_inr || ''))
      setCustomTimeline(String(data.estimated_timeline_days || ''))
      setStep(3)
      toast.success('SCOPE & ESTIMATES CALCULATED')
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'SCOPING SUMMARY FAILED')
    } finally {
      setLoading(false)
    }
  }

  // Step 3 -> Step 4
  const handleProposal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectTitle.trim() || !clientName.trim() || !customPrice.trim() || !customTimeline.trim()) {
      toast.error('ALL PROPOSAL TARGET PARAMETERS ARE REQUIRED')
      return
    }

    setLoading(true)
    try {
      const data = await draftProposal({
        project_title: projectTitle.trim(),
        client_name: clientName.trim(),
        scope_breakdown: scoped?.scope_breakdown || [],
        timeline_days: parseInt(customTimeline),
        price_inr: parseFloat(customPrice),
        deliverables: selectedDeliverables
      })
      setProposal(data)
      setStep(4)
      toast.success('CLIENT PROPOSAL DRAFTED')
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'PROPOSAL GENERATION FAILED')
    } finally {
      setLoading(false)
    }
  }

  // Auto-instantiate project inside DB from parsed data
  const handleInstantiateProject = async () => {
    // Attempt to map client name to registered clients or create a placeholder client
    let targetClientId = ''
    const matchedClient = clients.find(c => c.name.toLowerCase() === clientName.toLowerCase())
    
    if (matchedClient) {
      targetClientId = matchedClient.id
    } else {
      toast.error('CLIENT MUST BE REGISTERED IN DIRECTORY FIRST. GO TO CLIENTS TAB.')
      return
    }

    const loadingToast = toast.loading('INSTANTIATING CONTRACT PROJECT...')
    try {
      await createProject({
        title: projectTitle.trim(),
        client_id: targetClientId,
        value_inr: parseFloat(customPrice),
        deadline: new Date(Date.now() + parseInt(customTimeline) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        scope: {
          scope_breakdown: scoped?.scope_breakdown || []
        }
      })
      toast.dismiss(loadingToast)
      toast.success('PROJECT CREATED SUCCESSFULLY')
    } catch (err: any) {
      toast.dismiss(loadingToast)
      toast.error(err.message?.toUpperCase() || 'FAILED TO INSTANTIATE PROJECT')
    }
  }

  const handleCopyToClipboard = () => {
    if (!proposal) return
    const text = `Subject: ${proposal.subject}\n\n${proposal.body}`
    navigator.clipboard.writeText(text)
    toast.success('PROPOSAL COPIED')
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="border-bottom border-border-hairline pb-4 flex items-center justify-between">
        <div>
          <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
            AI AGENT LAYER
          </span>
          <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
            Brief Parsing Workspace
          </h1>
        </div>
        
        {/* Progress indicators */}
        <div className="flex items-center space-x-2 font-mono text-[11px] text-text-secondary uppercase">
          <span className={step === 1 ? 'text-white' : ''}>01_INPUT</span>
          <span>&gt;</span>
          <span className={step === 2 ? 'text-white' : ''}>02_PARSE</span>
          <span>&gt;</span>
          <span className={step === 3 ? 'text-white' : ''}>03_SCOPE</span>
          <span>&gt;</span>
          <span className={step === 4 ? 'text-white' : ''}>04_PROPOSAL</span>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-border-strong w-full max-w-sm p-6 text-center space-y-4">
            <Cpu className="animate-spin text-white mx-auto" size={32} />
            <h3 className="font-inter text-[13px] text-text-primary uppercase tracking-wider font-semibold">
              RUNNING AGENT LAYER SERVICES
            </h3>
            <p className="font-mono text-[11px] text-text-secondary uppercase animate-pulse">
              Please wait while Groq computes tokens...
            </p>
          </div>
        </div>
      )}

      {/* Step 1: Input text box */}
      {step === 1 && (
        <div className="bg-surface border border-border-hairline p-6 space-y-4">
          <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary">
            Submit Raw Requirements Brief
          </h2>
          <p className="font-inter text-[12px] text-text-secondary uppercase leading-relaxed">
            Paste raw text requirements, chat summaries, client emails, or bullet points. 
            The Brief Parser agent will extract key milestones, timeline scope, and target constraints.
          </p>

          <form onSubmit={handleParse} className="space-y-4">
            <textarea
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              rows={8}
              placeholder="PASTE CLIENT CHAT LOG OR SPEC DOCUMENT DETAILS HERE..."
              className="w-full bg-[#0A0A0A] border border-[#1A1A1A] text-white p-4 font-mono text-[13px] rounded-none focus:border-white focus:outline-none"
              required
            />
            <button
              type="submit"
              className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-5 py-2.5 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors flex items-center space-x-2 cursor-pointer"
            >
              <span>RUN BRIEF-PARSER AGENT</span>
              <ArrowRight size={14} />
            </button>
          </form>
        </div>
      )}

      {/* Step 2: Parsed Result View */}
      {step === 2 && parsed && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 bg-surface border border-border-hairline p-6 space-y-4">
            <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary border-bottom border-border-hairline pb-2 mb-4">
              Agent Brief Summary
            </h2>
            
            <div className="space-y-1">
              <div className="text-[11px] uppercase font-inter font-medium text-text-muted">
                AGENT OUTPUT
              </div>
              <div className="bg-[#0A0A0A] border-l-2 border-white p-4 font-mono text-[12px] leading-relaxed text-text-primary select-text">
                {parsed.brief_summary}
              </div>
            </div>

            <div>
              <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                Project Category
              </label>
              <select
                value={projectType}
                onChange={(e) => setProjectType(e.target.value)}
                className="bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none"
              >
                <option value="development">DEVELOPMENT</option>
                <option value="design">DESIGN</option>
                <option value="marketing">MARKETING</option>
                <option value="consulting">CONSULTING</option>
              </select>
            </div>
          </div>

          {/* Deliverables selection checklist */}
          <div className="lg:col-span-5 bg-surface border border-border-hairline p-6 flex flex-col justify-between">
            <div className="space-y-4">
              <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary border-bottom border-border-hairline pb-2 mb-4">
                Verify Deliverables Checklist
              </h2>
              <div className="space-y-2">
                {parsed.deliverables.map((item, idx) => {
                  const checked = selectedDeliverables.includes(item)
                  return (
                    <label key={idx} className="flex items-start space-x-3 p-2 bg-[#0A0A0A] border border-border-hairline select-none cursor-pointer">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => {
                          if (checked) {
                            setSelectedDeliverables(selectedDeliverables.filter(d => d !== item))
                          } else {
                            setSelectedDeliverables([...selectedDeliverables, item])
                          }
                        }}
                        className="mt-0.5 rounded-none accent-white cursor-pointer"
                      />
                      <span className="font-inter text-[12px] text-text-primary">{item}</span>
                    </label>
                  )
                })}
              </div>
            </div>

            <div className="pt-4 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
              >
                BACK
              </button>
              <button
                onClick={handleScope}
                className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
              >
                RUN SCOPE-ADVISOR
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Scope Results & Configuration */}
      {step === 3 && scoped && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 bg-surface border border-border-hairline p-6 space-y-4">
            <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary border-bottom border-border-hairline pb-2 mb-4">
              Scope Advisor Suggestion
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#0A0A0A] p-4 border border-border-hairline">
                <span className="font-inter text-[11px] uppercase tracking-wider text-text-secondary">AI Suggested Price</span>
                <div className="font-mono text-[18px] text-success mt-1">{formatCurrency(scoped.estimated_price_inr)}</div>
              </div>
              <div className="bg-[#0A0A0A] p-4 border border-border-hairline">
                <span className="font-inter text-[11px] uppercase tracking-wider text-text-secondary">Timeline Estimated</span>
                <div className="font-mono text-[18px] text-text-primary mt-1">{scoped.estimated_timeline_days} DAYS</div>
              </div>
            </div>

            <div className="space-y-1">
              <div className="text-[11px] uppercase font-inter font-medium text-text-muted">
                AGENT TASKS BREAKDOWN
              </div>
              <div className="bg-[#0A0A0A] border-l-2 border-white p-4 font-mono text-[12px] leading-relaxed text-text-primary select-text">
                <ul className="list-disc pl-4 space-y-1">
                  {scoped.scope_breakdown.map((task, i) => (
                    <li key={i}>{task}</li>
                  ))}
                </ul>
              </div>
            </div>

            {scoped.risk_indicators.length > 0 && (
              <div className="bg-surface-raised border border-danger/20 p-4">
                <div className="flex items-center space-x-2 text-danger font-inter text-[11px] font-semibold uppercase tracking-wider mb-2">
                  <Shield size={14} />
                  <span>Risk Flags Identified</span>
                </div>
                <ul className="list-disc pl-4 font-inter text-[12px] text-text-secondary space-y-1">
                  {scoped.risk_indicators.map((risk, i) => (
                    <li key={i}>{risk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Form to edit before drawing proposal */}
          <div className="lg:col-span-4 bg-surface border border-border-hairline p-6 flex flex-col justify-between">
            <form onSubmit={handleProposal} className="space-y-4">
              <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary border-bottom border-border-hairline pb-2 mb-4">
                Configure Proposal
              </h2>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Project Title *
                </label>
                <input
                  type="text"
                  value={projectTitle}
                  onChange={(e) => setProjectTitle(e.target.value)}
                  placeholder="E.G. WEB PORTAL REDESIGN"
                  className="w-full"
                  required
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Client Name *
                </label>
                <input
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="E.G. CLIENT CO"
                  className="w-full"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                    Value (INR) *
                  </label>
                  <input
                    type="number"
                    value={customPrice}
                    onChange={(e) => setCustomPrice(e.target.value)}
                    className="w-full font-mono text-[13px]"
                    required
                  />
                </div>
                <div>
                  <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                    Timeline (Days) *
                  </label>
                  <input
                    type="number"
                    value={customTimeline}
                    onChange={(e) => setCustomTimeline(e.target.value)}
                    className="w-full font-mono text-[13px]"
                    required
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
                >
                  BACK
                </button>
                <button
                  type="submit"
                  className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
                >
                  DRAFT PROPOSAL
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Step 4: Final Proposal Copy screen */}
      {step === 4 && proposal && (
        <div className="bg-surface border border-border-hairline p-6 space-y-4">
          <div className="flex items-center justify-between border-bottom border-border-hairline pb-2">
            <h2 className="font-inter font-medium text-[14px] uppercase text-text-primary">
              Drafted Client Proposal
            </h2>
            <button
              onClick={handleCopyToClipboard}
              className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-3 py-1.5 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors flex items-center space-x-1 cursor-pointer"
            >
              <Clipboard size={12} />
              <span>COPY DRAFT</span>
            </button>
          </div>

          <div className="space-y-1">
            <div className="text-[11px] uppercase font-inter font-medium text-text-muted">
              AGENT PROPOSAL OUTPUT
            </div>
            <div className="bg-[#0A0A0A] border-l-2 border-white p-4 font-mono text-[12px] leading-relaxed text-text-primary select-text max-h-[400px] overflow-y-auto">
              <div className="font-bold text-[#FFFFFF] border-bottom border-[#1A1A1A] pb-2 mb-2">
                Subject: {proposal.subject}
              </div>
              {proposal.body}
            </div>
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(3)}
              className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
            >
              BACK
            </button>
            <div className="space-x-3">
              <button
                onClick={handleInstantiateProject}
                className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
              >
                CREATE PROJECT IN GIG.AI
              </button>
              <button
                onClick={() => setStep(1)}
                className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
              >
                PARSE NEW BRIEF
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
