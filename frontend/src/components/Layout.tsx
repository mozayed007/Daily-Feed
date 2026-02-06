import { NavLink } from 'react-router-dom';
import { 
  Home, 
  BarChart3, 
  Settings, 
  History, 
  Newspaper,
  Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';
import { ThemeToggleSimple } from './ThemeToggle';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const navItems = [
    { path: '/', icon: Home, label: 'Feed' },
    { path: '/stats', icon: BarChart3, label: 'Stats' },
    { path: '/history', icon: History, label: 'History' },
    { path: '/preferences', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-background relative selection:bg-primary/30 selection:text-primary transition-colors">
      {/* Background patterns */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] premium-gradient rounded-full blur-[150px] opacity-[0.08]" />
        <div className="absolute bottom-[20%] left-[10%] w-[40%] h-[40%] bg-primary rounded-full blur-[180px] opacity-[0.05]" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40 transition-colors">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Newspaper className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-300 bg-clip-text text-transparent transition-colors">
                  Daily Feed
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-amber-500" />
                  AI-Powered
                </p>
              </div>
            </div>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-4">
              <ThemeToggleSimple />
              <div className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 shadow-sm'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <item.icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : ''}`} />
                      <span>{item.label}</span>
                    </>
                  )}
                </NavLink>
              ))}
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 px-4 py-2 safe-area-pb transition-colors">
        <div className="flex items-center justify-around">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-3 py-2 rounded-lg transition-colors ${
                  isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : ''}`} />
                  <span className="text-xs font-medium">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
