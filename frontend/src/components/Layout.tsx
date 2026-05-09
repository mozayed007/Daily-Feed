import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  BarChart3, 
  Settings, 
  History, 
  Newspaper,
  Sparkles,
  Clock,
  Menu,
  X,
  LogOut,
  User,
  TrendingUp,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeToggleSimple } from './ThemeToggle';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout } = useAuth();
  
  const navItems = [
    { path: '/', icon: Home, label: 'Feed' },
    { path: '/trends', icon: TrendingUp, label: 'Trends' },
    { path: '/stats', icon: BarChart3, label: 'Stats' },
    { path: '/history', icon: History, label: 'History' },
    { path: '/scheduler', icon: Clock, label: 'Scheduler' },
    { path: '/preferences', icon: Settings, label: 'Settings' },
    { path: '/profile', icon: User, label: 'Profile' },
  ];

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 transition-colors">
      {/* Mobile Header */}
      <header className="lg:hidden sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-700/60 transition-colors">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Newspaper className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-slate-900 dark:text-white">Daily Feed</span>
            </div>
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Open menu"
            >
              <Menu className="w-6 h-6 text-slate-600 dark:text-slate-300" />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 bg-black/50 z-50"
              onClick={closeMenu}
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="lg:hidden fixed top-0 right-0 bottom-0 w-72 bg-white dark:bg-slate-900 z-50 shadow-xl"
            >
              <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                <span className="font-semibold text-slate-900 dark:text-white">Menu</span>
                <button
                  onClick={closeMenu}
                  className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  aria-label="Close menu"
                >
                  <X className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                </button>
              </div>
              <nav className="p-4 space-y-2">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={closeMenu}
                    className={({ isActive }) =>
                      `flex items-center gap-3 min-h-[44px] px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                      }`
                    }
                  >
                    <item.icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </nav>
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200 dark:border-slate-700 space-y-2">
                <ThemeToggleSimple />
                <button
                  onClick={() => {
                    logout();
                    closeMenu();
                  }}
                  className="w-full flex items-center gap-3 min-h-[44px] px-4 py-3 rounded-xl text-sm font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-900/30 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Sign out</span>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop Header */}
      <header className="hidden lg:block sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-700/60 transition-colors">
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
            <nav className="flex items-center gap-4">
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
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-rose-50 dark:hover:bg-rose-900/30 hover:text-rose-600 dark:hover:text-rose-400 transition-all duration-200"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden xl:inline">Logout</span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 pb-24 lg:pb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 px-2 py-2 safe-area-pb transition-colors z-40">
        <div className="flex items-center justify-around">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-2 py-2 min-w-[64px] min-h-[44px] rounded-lg transition-colors ${
                  isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-blue-600' : ''}`} />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  );
}
