'use client'

import React, { useState, useEffect } from 'react'
import { listClients, createClient, updateClient, deleteClient } from '@/lib/api'
import { Plus, Edit2, Trash2, X } from 'lucide-react'
import toast from 'react-hot-toast'

interface Client {
  id: string
  name: string
  email: string
  phone: string | null
  notes: string | null
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)

  // Form states
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)

  const fetchClients = async () => {
    setLoading(true)
    try {
      const data = await listClients()
      setClients(data)
    } catch (err: any) {
      toast.error('FAILED TO FETCH CLIENTS: ' + err.message?.toUpperCase())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClients()
  }, [])

  const openAddModal = () => {
    setEditingClient(null)
    setName('')
    setEmail('')
    setPhone('')
    setNotes('')
    setModalOpen(true)
  }

  const openEditModal = (client: Client) => {
    setEditingClient(client)
    setName(client.name)
    setEmail(client.email)
    setPhone(client.phone || '')
    setNotes(client.notes || '')
    setModalOpen(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !email.trim()) {
      toast.error('NAME AND EMAIL REQUIRED')
      return
    }

    setSaving(true)
    try {
      if (editingClient) {
        // Edit existing client
        await updateClient(editingClient.id, {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          phone: phone.trim() || undefined,
          notes: notes.trim() || undefined
        })
        toast.success('CLIENT UPDATED')
      } else {
        // Create new client
        await createClient({
          name: name.trim(),
          email: email.trim().toLowerCase(),
          phone: phone.trim() || undefined,
          notes: notes.trim() || undefined
        })
        toast.success('CLIENT CREATED')
      }
      setModalOpen(false)
      fetchClients()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO SAVE CLIENT')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('ARE YOU SURE YOU WANT TO DELETE THIS CLIENT? THIS WILL FAIL IF THE CLIENT HAS PROJECTS.')) return
    try {
      await deleteClient(id)
      toast.success('CLIENT DELETED')
      fetchClients()
    } catch (err: any) {
      toast.error(err.message?.toUpperCase() || 'FAILED TO DELETE CLIENT')
    }
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between border-bottom border-border-hairline pb-4">
        <div>
          <span className="font-mono text-[11px] text-text-secondary tracking-widest uppercase">
            CLIENT DIRECTORY
          </span>
          <h1 className="font-inter font-medium text-[18px] tracking-[-0.02em] text-text-primary uppercase mt-1">
            Manage Clients
          </h1>
        </div>
        <button
          onClick={openAddModal}
          className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 border border-transparent hover:bg-canvas hover:text-text-primary hover:border-border-strong transition-colors flex items-center space-x-1 cursor-pointer"
        >
          <Plus size={14} />
          <span>ADD CLIENT</span>
        </button>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="font-mono text-[11px] text-text-secondary uppercase">
          LOADING CLIENT LIST...
        </div>
      ) : clients.length > 0 ? (
        <div className="bg-surface border border-border-hairline overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface border-bottom border-border-hairline">
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Name</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Email Address</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3">Phone</th>
                <th className="font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client) => (
                <tr key={client.id} className="border-bottom border-border-hairline hover:bg-surface-raised transition-colors">
                  <td className="px-6 py-4 font-inter text-[13px] font-medium text-text-primary">
                    {client.name}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-secondary">
                    {client.email}
                  </td>
                  <td className="px-6 py-4 font-mono text-[13px] text-text-secondary">
                    {client.phone || '—'}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => openEditModal(client)}
                      className="text-text-secondary hover:text-text-primary p-1 transition-colors cursor-pointer"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(client.id)}
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
            No Clients Logged
          </h3>
          <p className="font-inter text-[12px] text-text-secondary mt-1 mb-4">
            YOU HAVE NOT REGISTERED ANY CLIENT CONTEXT YET.
          </p>
          <button
            onClick={openAddModal}
            className="bg-accent text-accent-inverse font-inter font-semibold text-[11px] tracking-[0.06em] uppercase px-4 py-2 hover:bg-canvas hover:text-text-primary hover:border-border-strong border border-transparent transition-colors cursor-pointer"
          >
            ADD CLIENT NOW
          </button>
        </div>
      )}

      {/* Brutalist Modal Overlay */}
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
              {editingClient ? 'EDIT CLIENT DETAILS' : 'ADD NEW CLIENT'}
            </h2>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Client Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={saving}
                  placeholder="E.G. ACME INC"
                  className="w-full"
                  required
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={saving}
                  placeholder="CONTACT@CLIENT.COM"
                  className="w-full font-mono text-[13px]"
                  required
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Phone (Optional)
                </label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={saving}
                  placeholder="E.G. +91 98765 43210"
                  className="w-full font-mono text-[13px]"
                />
              </div>

              <div>
                <label className="block font-inter text-[11px] tracking-[0.08em] uppercase text-text-secondary mb-1">
                  Internal Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={saving}
                  rows={3}
                  placeholder="E.G. MET ON UPWORK, MONTHLY RETAINER BASIS..."
                  className="w-full bg-[#111111] border border-[#1A1A1A] text-white p-2 text-[13px] rounded-none focus:border-white focus:outline-none resize-none"
                />
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
                  {saving ? 'SAVING...' : 'SAVE CLIENT'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}
