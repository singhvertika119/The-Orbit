import { supabase } from './supabase'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  }
}

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const headers = await getAuthHeaders()
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Request failed with status ${response.status}`)
  }

  return response.json()
}

// Brief Parsing & Scoping
export const parseBrief = (briefText: string) => 
  apiRequest('/api/v1/brief/parse', {
    method: 'POST',
    body: JSON.stringify({ brief_text: briefText })
  })

export const scopeBrief = (briefSummary: string, deliverables: string[], projectType: string) => 
  apiRequest('/api/v1/brief/scope', {
    method: 'POST',
    body: JSON.stringify({ brief_summary: briefSummary, deliverables, project_type: projectType })
  })

export const draftProposal = (params: {
  project_title: string
  client_name: string
  scope_breakdown: string[]
  timeline_days: number
  price_inr: number
  deliverables: string[]
}) => 
  apiRequest('/api/v1/brief/proposal', {
    method: 'POST',
    body: JSON.stringify(params)
  })

// Profile Update (Onboarding flow)
export const updateProfile = (profileData: {
  name?: string
  upi_id?: string
  gst_number?: string
  bank_details?: string
}) => 
  apiRequest('/api/v1/auth/profile', {
    method: 'PATCH',
    body: JSON.stringify(profileData)
  })

// Clients CRUD
export const listClients = () => apiRequest('/api/v1/clients')
export const getClient = (id: string) => apiRequest(`/api/v1/clients/${id}`)
export const createClient = (client: { name: string; email: string; phone?: string; notes?: string }) => 
  apiRequest('/api/v1/clients', { method: 'POST', body: JSON.stringify(client) })
export const updateClient = (id: string, client: Partial<{ name: string; email: string; phone: string; notes: string }>) => 
  apiRequest(`/api/v1/clients/${id}`, { method: 'PATCH', body: JSON.stringify(client) })
export const deleteClient = (id: string) => apiRequest(`/api/v1/clients/${id}`, { method: 'DELETE' })

// Projects CRUD
export const listProjects = () => apiRequest('/api/v1/projects')
export const getProject = (id: string) => apiRequest(`/api/v1/projects/${id}`)
export const createProject = (project: {
  title: string
  description?: string
  client_id?: string
  value_inr: number
  deadline: string
  scope: any
}) => apiRequest('/api/v1/projects', { method: 'POST', body: JSON.stringify(project) })
export const updateProject = (id: string, project: any) => 
  apiRequest(`/api/v1/projects/${id}`, { method: 'PATCH', body: JSON.stringify(project) })
export const deleteProject = (id: string) => apiRequest(`/api/v1/projects/${id}`, { method: 'DELETE' })

// Milestones Routing
export const listMilestones = (projectId: string) => apiRequest(`/api/v1/milestones?project_id=${projectId}`)
export const createMilestone = (milestone: {
  project_id: string
  title: string
  description?: string
  amount_inr: number
  due_date: string
}) => apiRequest('/api/v1/milestones', { method: 'POST', body: JSON.stringify(milestone) })
export const updateMilestone = (id: string, milestone: any) => 
  apiRequest(`/api/v1/milestones/${id}`, { method: 'PATCH', body: JSON.stringify(milestone) })
export const deleteMilestone = (id: string) => apiRequest(`/api/v1/milestones/${id}`, { method: 'DELETE' })
export const completeMilestone = (id: string) => apiRequest(`/api/v1/milestones/${id}/complete`, { method: 'PATCH' })

// Invoices CRUD
export const listInvoices = () => apiRequest('/api/v1/invoices')
export const getInvoice = (id: string) => apiRequest(`/api/v1/invoices/${id}`)
export const markInvoicePaid = (id: string) => apiRequest(`/api/v1/invoices/${id}/paid`, { method: 'PATCH' })
export const triggerFollowup = (id: string) => apiRequest(`/api/v1/invoices/${id}/followup`, { method: 'POST' })
export const getInvoicePdf = (id: string) => apiRequest(`/api/v1/invoices/${id}/pdf`)

// Digest Routing
export const getDigestToday = (refresh = false) => apiRequest(`/api/v1/digest/today?refresh=${refresh}`)
