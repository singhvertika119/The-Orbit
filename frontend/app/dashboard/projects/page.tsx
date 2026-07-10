'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { listProjects, createProject, deleteProject, listClients } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Plus, Edit2, Trash2, X, Eye } from 'lucide-react'
import toast from 'react-hot-toast'

interface Project {
  id: string
  title: string
  description: string | null
  client_id: string | null
  value_inr: number
  deadline: string | null
  status: 'active' | 'scoping' | 'complete' | 'cancelled'
  client_name?: string
}

interface Client {
  id: string
  name: string
}

export default function ProjectsPage() {
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  
  // Modal State
  const [modalOpen, setModalOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [clientId, setClientId] = useState('')
  const [valueInr, setValueInr] = useState('')
  const [deadline, setDeadline] = useState('')
  const [saving, setSaving] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [projectsData, clientsData] = await Promise.all([
        listProjects(),
        listClients()
      ])

      // Map client names for display
      const mapped = projectsData.map((p: any) => {
        const client = clientsData.find((c: any) => c.id === p.client_id)
        return {
          ...p,
          client_name: client ? client.name : '—'
        }
      })

      setProjects(mapped)
      setClients(clientsData)
    } catch (err: any) {
      toast.error('FAILED TO FETCH PROJECTS: ' + err.message?.toUpperCase())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const openAddModal = () => {
    if (clients.length === 0) {
      toast.error('ADD A CLIENT FIRST BEFORE CREATING A PROJECT')
      return
    }
    setTitle('')
    setDescription('')
    setClientId(clients[0].id)
    setValueInr('')
    setDeadline('')
    setModalOpen(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !valueInr.trim() || !deadline.trim() || !clientId) {
      toast.error('TITLE, VALUE, DEADLINE, AND CLIENT REQUIRED')
      return
    }

    setSaving(true)
    try {
      await createProject({
        title: title.trim(),
        description: description.trim() || undefined,
        client_id: clientId,
        value_inr: parseFloat(valueInr),
        deadline: deadline,
        scope: { scope_breakdown: [] } // Empty scope default
      })

      toast.success('PROJECT CREATED')
      setModalOpen(false)
      fetchData()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO CREATE PROJECT')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent row click navigation trigger
    if (!confirm('ARE YOU SURE YOU WANT TO DELETE THIS PROJECT?')) return
    try {
      await deleteProject(id)
      toast.success('PROJECT DELETED')
      fetchData()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO DELETE PROJECT')
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'ACTIVE':
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-white text-black uppercase">ACTIVE</span>
      case 'SCOPING':
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#1A1A1A] text-[#666666] uppercase">SCOPING</span>
      case 'COMPLETE':
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#1A3A1A] text-[#22C55E] uppercase">COMPLETE</span>
      default:
        return <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider bg-[#1A1A1A] text-[#333333] uppercase">{status}</span>
    }
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between border-bottom border-border-hairline pb-4">
        <div>
          <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
            PROJECT PORTFOLIO
          </span>
          <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
            Contract Projects
          </h1>
        </div>
        <button
          onClick={openAddModal}
          className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors flex items-center space-x-1 cursor-pointer"
        >
          <Plus size={14} />
          <span>CREATE PROJECT</span>
        </button>
      </div>

      {/* Main Table Area */}
      {loading ? (
        <div className="font-mono text-[11px] text-text-secondary uppercase">
          LOADING PROJECT LIST...
        </div>
      ) : projects.length > 0 ? (
        <div className="bg-surface border border-border-hairline overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface border-bottom border-border-hairline">
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Project Title</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Client</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Value</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Deadline</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Status</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr 
                  key={project.id} 
                  onClick={() => router.push(`/projects/${project.id}`)}
                  className="border-bottom border-border-hairline hover:bg-surface-raised transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4 font-inter text-[13px] font-medium text-text-primary">
                    {project.title}
                  </td>
                  <td className="px-6 py-4 font-inter text-[13px] text-text-secondary">
                    {project.client_name}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-primary">
                    {formatCurrency(project.value_inr)}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-secondary">
                    {formatDate(project.deadline)}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(project.status)}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        router.push(`/projects/${project.id}`)
                      }}
                      className="text-text-secondary hover:text-text-primary p-1 transition-colors cursor-pointer"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={(e) => handleDelete(project.id, e)}
                      className="text-danger hover:text-red-400 p-1 transition-colors cursor-pointer"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-16 bg-surface border border-border-hairline">
          <h3 className="font-inter text-[14px] text-text-primary uppercase">
            No Projects Active
          </h3>
          <p className="font-inter text-[12px] text-text-secondary mt-1 mb-4">
            YOU HAVE NOT REGISTERED ANY ACTIVE PROJECT OR CONTRACT YET.
          </p>
          <button
            onClick={openAddModal}
            className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:bg-canvas hover:text-text-primary hover:border-border-strong border border-transparent transition-colors cursor-pointer"
          >
            CREATE PROJECT NOW
          </button>
        </div>
      )}

      {/* Project Creation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-surface border border-border-strong w-full max-w-md p-6 relative">
            <button
              onClick={() => setModalOpen(false)}
              className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
            >
              <X size={18} />
            </button>

            <h2 className="font-inter font-medium text-[14px] tracking-[-0.02em] text-text-primary uppercase border-bottom border-border-hairline pb-2 mb-4">
              CREATE CONTRACT PROJECT
            </h2>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Project Title *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={saving}
                  placeholder="E.G. GIG.AI FRONTEND INTEGRATION"
                  className="w-full"
                  required
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={saving}
                  rows={2}
                  placeholder="E.G. NEXT.JS INTERFACE DEVELOPMENT AND STYLES..."
                  className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none resize-none"
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Assign Client *
                </label>
                <select
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  disabled={saving}
                  className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none"
                  required
                >
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                    Value (INR) *
                  </label>
                  <input
                    type="number"
                    value={valueInr}
                    onChange={(e) => setValueInr(e.target.value)}
                    disabled={saving}
                    placeholder="E.G. 150000"
                    className="w-full font-mono text-[13px]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                    Deadline Date *
                  </label>
                  <input
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    disabled={saving}
                    className="w-full font-mono text-[13px]"
                    required
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="bg-surface text-text-primary border border-border-strong font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:border-border-active transition-colors cursor-pointer"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors cursor-pointer"
                >
                  {saving ? 'CREATING...' : 'CREATE PROJECT'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}
