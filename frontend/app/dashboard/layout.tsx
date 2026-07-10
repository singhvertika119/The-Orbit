'use client'

import React, { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  FileText, 
  Cpu, 
  Settings as SettingsIcon, 
  LogOut 
} from 'lucide-react'

const navItems = [
  { label: 'TODAY', path: '/dashboard', icon: LayoutDashboard },
  { label: 'CLIENTS', path: '/dashboard/clients', icon: Users },
  { label: 'PROJECTS', path: '/dashboard/projects', icon: Briefcase },
  { label: 'INVOICES', path: '/dashboard/invoices', icon: FileText },
  { label: 'BRIEF PARSER', path: '/dashboard/brief', icon: Cpu },
  { label: 'SETTINGS', path: '/dashboard/settings', icon: SettingsIcon }
]

export default function DashboardLayout({
  children
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, profile, loading, signOut } = useAuth()

  // Route protection
  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push('/auth/login')
      } else if (profile && !profile.onboarded) {
        router.push('/onboarding')
      }
    }
  }, [user, profile, loading, router])

  if (loading || !user || (profile && !profile.onboarded)) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center font-mono text-[11px] uppercase tracking-widest text-text-secondary">
        LOADING...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col font-inter text-[13px] text-text-primary antialiased">
      
      {/* Top Navbar */}
      <header className="h-[48px] bg-canvas border-bottom border-border-hairline flex items-center justify-between px-6 z-10">
        <div className="flex items-center space-x-2">
          <span className="font-inter font-semibold text-[14px] tracking-[0.1em] uppercase text-text-primary">
            GIG.AI
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <span className="font-mono text-[11px] text-text-secondary uppercase">
            {profile?.name || user.email}
          </span>
          <button 
            onClick={() => signOut()}
            className="text-text-secondary hover:text-text-primary transition-colors flex items-center space-x-1 uppercase text-[11px] tracking-wider font-semibold cursor-pointer"
          >
            <LogOut size={13} />
            <span>LOG OUT</span>
          </button>
        </div>
      </header>

      {/* Main Core Layout: Sidebar + Canvas */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Sidebar */}
        <aside className="w-[200px] bg-canvas border-right border-border-hairline flex flex-col justify-between shrink-0">
          <nav className="py-4 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.path || (item.path !== '/dashboard' && pathname.startsWith(item.path))
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  className={`flex items-center space-x-3 px-4 py-2 font-inter text-[13px] tracking-wide transition-colors ${
                    isActive 
                      ? 'text-text-primary bg-surface-raised border-left-2 border-white' 
                      : 'text-[#444444] hover:text-text-primary hover:bg-surface'
                  }`}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
          
          {/* Sidebar Footer */}
          <div className="p-4 border-top border-border-hairline">
            <span className="font-mono text-[11px] text-text-muted uppercase block">
              GIG.AI CORE V1.0
            </span>
          </div>
        </aside>

        {/* Dynamic Content Panel */}
        <main className="flex-1 overflow-y-auto bg-canvas p-6">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>

      </div>
    </div>
  )
}
