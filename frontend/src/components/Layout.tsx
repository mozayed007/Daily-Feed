import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  Home, 
  BarChart3, 
  Settings, 
  History, 
  Newspaper,
  Sparkles,
  Users,
  ChevronDown,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeToggleSimple } from './ThemeToggle';
import { useUser, useAllUsers, useSwitchUser } from '../hooks/useUser';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { data: currentUser } = useUser();
  const { data: allUsers } = useAllUsers();
  const switchUser = useSwitchUser();

  const navItems = [
    { path: '/', icon: Home, label: 'Feed' },
    { path: '/stats', icon: BarChart3, label: 'Stats' },
    { path: '/history', icon: History, label: 'History' },
    { path: '/preferences', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 transition-colors">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-700/60 transition-colors">
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
              
              {/* User Switcher */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-muted transition-colors text-sm font-medium"
                >
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <Users className="w-3.5 h-3.5" />
                  </div>
                  <span className="max-w-[100px] truncate">{currentUser?.name || 'User'}</span>
                  <ChevronDown className="w-3 h-3 text-muted-foreground" />
                </button>

                <AnimatePresence>
                  {showUserMenu && (
                    <>
                      <div 
                        className="fixed inset-0 z-40"
                        onClick={() => setShowUserMenu(false)}
                      />
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="absolute right-0 top-full mt-2 w-56 bg-card border border-border rounded-xl shadow-xl z-50 p-2"
                      >
                        <div className="text-xs font-medium text-muted-foreground px-2 py-1.5 mb-1 uppercase tracking-wider">
                          Switch Profile
                        </div>
                        <div className="space-y-1">
                          {allUsers?.map((user) => (
                            <button
                              key={user.id}
                              onClick={() => {
                                switchUser.mutate(user.id);
                                setShowUserMenu(false);
                              }}
                              className={`w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-sm transition-colors ${
                                currentUser?.id === user.id
                                  ? 'bg-primary/10 text-primary'
                                  : 'hover:bg-muted text-foreground'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                                  currentUser?.id === user.id ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'
                                }`}>
                                  {user.name[0]}
                                </div>
                                {user.name}
                              </div>
                              {currentUser?.id === user.id && (
                                <Check className="w-3.5 h-3.5" />
                              )}
                            </button>
                          ))}
                        </div>
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>
              </div>

              <div className="h-6 w-px bg-border mx-2" />

              <div className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-primary/10 text-primary shadow-sm'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <item.icon className={`w-4 h-4 ${isActive ? 'text-primary' : ''}`} />
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
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-background/80 backdrop-blur-lg border-t border-border px-4 py-2 safe-area-pb transition-colors z-50">
        <div className="flex items-center justify-around">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 p-2 rounded-lg transition-colors ${
                  isActive
                    ? 'text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </NavLink>
          ))}
          <div className="p-2">
            <ThemeToggleSimple />
          </div>
        </div>
      </nav>
    </div>
  );
}
