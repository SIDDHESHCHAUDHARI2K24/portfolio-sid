import { useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  LayoutDashboardIcon,
  ClockIcon,
  FolderIcon,
  FileTextIcon,
  TagsIcon,
  CodeIcon,
  AwardIcon,
  FormInputIcon,
  PresentationIcon,
  LibraryIcon,
  PenLineIcon,
  GraduationCapIcon,
  FileBadgeIcon,
  BotIcon,
  ChevronLeftIcon,
  LogOutIcon,
  MenuIcon,
  XIcon,
  SettingsIcon,
  MailIcon,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboardIcon },
  { to: '/timeline', label: 'Timeline', icon: ClockIcon },
  { to: '/projects', label: 'Projects', icon: FolderIcon },
  { to: '/posts', label: 'Posts', icon: FileTextIcon },
  { to: '/thesis', label: 'Thesis', icon: GraduationCapIcon },
  { to: '/skills', label: 'Skills', icon: CodeIcon },
  { to: '/certs', label: 'Certifications', icon: AwardIcon },
  { to: '/collections', label: 'Collections', icon: LibraryIcon },
  { to: '/prose', label: 'Prose', icon: PenLineIcon },
  { to: '/resumes', label: 'Resumes', icon: FileBadgeIcon },
  { to: '/forms', label: 'Forms', icon: FormInputIcon },
  { to: '/contact', label: 'Contact', icon: MailIcon },
  { to: '/overview', label: 'Overview', icon: PresentationIcon },
  { to: '/tag-map', label: 'Tag Map', icon: TagsIcon },
  { to: '/crawlers', label: 'Crawlers', icon: BotIcon },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

export function AdminLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const logout = useMutation({
    mutationFn: () => apiFetch('/auth/logout', { method: 'POST' }),
    onSuccess: () => {
      navigate('/login')
    },
  })

  return (
    <div className="flex min-h-screen">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-border bg-card transition-transform lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          <Link to="/" className="text-lg font-semibold">
            Admin
          </Link>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setSidebarOpen(false)}>
            <XIcon className="size-5" />
          </Button>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {NAV_ITEMS.map((item) => {
            const isActive = item.to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.to)
            return (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                )}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-border p-2">
          <Button
            variant="ghost"
            className="w-full justify-start gap-2 text-sm text-muted-foreground hover:text-destructive"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOutIcon className="size-4" />
            {logout.isPending ? 'Logging out...' : 'Logout'}
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center gap-2 border-b border-border px-4 lg:px-6">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <MenuIcon className="size-5" />
          </Button>
          <ChevronLeftIcon className="size-4 text-muted-foreground lg:hidden" />
          <h2 className="text-sm font-medium text-muted-foreground">
            {NAV_ITEMS.find((item) => {
              if (item.to === '/') return location.pathname === '/'
              return location.pathname.startsWith(item.to)
            })?.label ?? 'Admin'}
          </h2>
        </header>

        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
