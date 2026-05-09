import { motion } from 'framer-motion';
import { Home, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="text-center max-w-md"
      >
        <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Search className="w-10 h-10 text-blue-600 dark:text-blue-400" />
        </div>

        <h1 className="text-6xl font-bold text-slate-900 dark:text-white mb-2">
          404
        </h1>
        <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-4">
          Page Not Found
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8">
          The page you are looking for does not exist or has been moved.
        </p>

        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          <Home className="w-5 h-5" />
          Go Home
        </Link>
      </motion.div>
    </div>
  );
}
