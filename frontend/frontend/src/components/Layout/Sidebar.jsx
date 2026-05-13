import React from 'react'
import { NavLink } from 'react-router-dom'
import { Upload, BookOpen, Home } from 'lucide-react'

const links = [
  { to: '/', icon: Home, label: 'Upload' },
  { to: '/library', icon: BookOpen, label: 'Library' },
]

export default function Sidebar() {
  return (
    <aside className="w-14 bg-surface-1 border-r border-border flex flex-col items-center py-4 gap-1 flex-shrink-0">
      {links.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          title={label}
          className={({ isActive }) =>
            `w-10 h-10 flex items-center justify-center rounded-md transition-colors ${
              isActive
                ? 'bg-accent/15 text-accent'
                : 'text-text-muted hover:text-text-primary hover:bg-surface-2'
            }`
          }
        >
          <Icon size={18} />
        </NavLink>
      ))}
    </aside>
  )
}
