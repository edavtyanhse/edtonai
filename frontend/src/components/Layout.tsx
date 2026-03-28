import { NavLink, Outlet } from 'react-router-dom'
import { History, GitCompare } from 'lucide-react'
import LanguageSwitcher from './LanguageSwitcher'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-900 text-white">
      <header className="bg-slate-900/80 backdrop-blur-lg border-b border-slate-800 px-6 py-3 sticky top-0 z-50">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/20">
              <span className="text-white font-bold">E</span>
            </div>
            <span className="font-bold text-xl text-white">EdtonAI</span>
          </div>

          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <nav className="flex gap-1">
              <NavLink
                to="/history"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
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
                      ? 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <GitCompare className="w-4 h-4" />
                Compare
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
