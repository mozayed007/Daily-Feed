import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { events } from '../lib/events';

export function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setIsSubmitting(true);
    try {
      await api.post('/auth/forgot-password', { email });
      setIsSent(true);
    } catch {
      events.emit('toast', {
        type: 'error',
        title: 'Request Failed',
        message: 'Could not send reset instructions. Please try again.',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSent) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md text-center"
        >
          <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Check Your Email
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            If an account exists with <strong>{email}</strong>, we have sent password reset instructions.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium hover:underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Login
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Forgot Password?
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            Enter your email and we will send you reset instructions.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Sending...' : 'Send Reset Instructions'}
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-slate-500 dark:text-slate-400">
          Remember your password?{' '}
          <Link to="/login" className="text-blue-600 dark:text-blue-400 font-medium hover:underline">
            Log in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
