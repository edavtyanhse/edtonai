import { NavLink, Outlet } from 'react-router-dom'
import { CreditCard, History, GitCompare } from 'lucide-react'
import LanguageSwitcher from './LanguageSwitcher'
import ThemeSwitcher from './ThemeSwitcher'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-app-bg text-app-text">
      <header className="bg-app-surface/80 backdrop-blur-lg border-b border-app-border px-6 py-3 sticky top-0 z-50">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
              <span className="text-white font-bold">E</span>
            </div>
            <span className="font-bold text-xl text-app-text">EdtonAI</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <ThemeSwitcher />
              <LanguageSwitcher />
            </div>
            <nav className="flex gap-1">
              <NavLink
                to="/history"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-app-accent-soft/60 text-app-accent border border-app-accent/20'
                      : 'text-app-text-muted hover:text-app-text hover:bg-app-surface-muted'
                  }`
                }
              >
                <History className="w-4 h-4" />
                History
              </NavLink>

              <NavLink
                to="/compare"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-app-accent-soft/60 text-app-accent border border-app-accent/20'
                      : 'text-app-text-muted hover:text-app-text hover:bg-app-surface-muted'
                  }`
                }
              >
                <GitCompare className="w-4 h-4" />
                Compare
              </NavLink>

              <NavLink
                to="/billing"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-app-accent-soft/60 text-app-accent border border-app-accent/20'
                      : 'text-app-text-muted hover:text-app-text hover:bg-app-surface-muted'
                  }`
                }
              >
                <CreditCard className="w-4 h-4" />
                Подписка
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
