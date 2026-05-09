import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, ArrowLeft, CheckCircle } from 'lucide-react';
import { api } from '../lib/api';
import { events } from '../lib/events';

export function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      events.emit('toast', {
        type: 'error',
        title: 'Invalid Link',
        message: 'This password reset link is invalid or has expired.',
        duration: 5000,
      });
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword.length < 8) {
      events.emit('toast', {
        type: 'error',
        title: 'Invalid Password',
        message: 'Password must be at least 8 characters long.',
        duration: 3000,
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      events.emit('toast', {
        type: 'error',
        title: 'Passwords Do Not Match',
        message: 'Please ensure both passwords match.',
        duration: 3000,
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: newPassword });
      setIsSuccess(true);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to reset password. Please try again.';
      events.emit('toast', {
        type: 'error',
        title: 'Reset Failed',
        message,
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
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
            Password Reset
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            Your password has been reset successfully. You can now log in with your new password.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Go to Login
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
            Reset Password
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            Enter your new password below.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              New Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min. 8 characters"
                required
                minLength={8}
                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                required
                minLength={8}
                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !token}
            className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <p className="text-center mt-6 text-sm text-slate-500 dark:text-slate-400">
          <Link to="/login" className="text-blue-600 dark:text-blue-400 font-medium hover:underline inline-flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" />
            Back to Login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
