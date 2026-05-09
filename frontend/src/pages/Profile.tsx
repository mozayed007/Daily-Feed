import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Calendar, Settings, BarChart3, ChevronRight, Lock, Eye, EyeOff } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUser, useUserStats, useChangePassword } from '../hooks/useUser';
import { StatsCardSkeleton } from '../components/Skeleton';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { events } from '../lib/events';

export function Profile() {
  const { data: user, isLoading: userLoading, isError: userError } = useUser();
  const { data: stats, isLoading: statsLoading, isError: statsError } = useUserStats();

  const isLoading = userLoading || statsLoading;
  const isError = userError || statsError;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (isError) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Profile
        </h1>
        <ErrorDisplay message="Failed to load profile data. Please try again." />
      </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Profile
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Manage your account and view your activity
        </p>
      </motion.div>

      {/* User Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700"
      >
        {isLoading ? (
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-700 animate-pulse" />
            <div className="space-y-2 flex-1">
              <div className="h-5 w-40 bg-slate-100 dark:bg-slate-700 rounded animate-pulse" />
              <div className="h-4 w-56 bg-slate-100 dark:bg-slate-700 rounded animate-pulse" />
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold shrink-0">
              {user?.name?.charAt(0).toUpperCase() || '?'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                {user?.name || 'User'}
              </h2>
              <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 text-sm mt-1">
                <Mail className="w-4 h-4" />
                {user?.email || 'No email'}
              </div>
              {user?.created_at && (
                <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500 text-xs mt-1">
                  <Calendar className="w-3 h-3" />
                  Joined {formatDate(user.created_at)}
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        {isLoading ? (
          <>
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
            <StatsCardSkeleton />
          </>
        ) : (
          <>
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {stats?.total_articles_read || 0}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Articles Read</p>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {stats?.total_articles_saved || 0}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Saved</p>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {stats?.average_reading_time
                  ? `${Math.round(stats.average_reading_time / 60)}m`
                  : '0m'}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Avg. Read Time</p>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {stats?.digest_open_rate ? `${Math.round(stats.digest_open_rate)}%` : '0%'}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Open Rate</p>
            </div>
          </>
        )}
      </motion.div>

      {/* Navigation Links */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-3"
      >
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Quick Links
        </h2>

        <Link
          to="/stats"
          className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">Statistics</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Detailed analytics and trends</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-slate-400" />
        </Link>

        <Link
          to="/preferences"
          className="flex items-center justify-between p-4 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-violet-100 dark:bg-violet-900/30 rounded-xl flex items-center justify-center">
              <Settings className="w-5 h-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <p className="font-medium text-slate-900 dark:text-white">Preferences</p>
              <p className="text-sm text-slate-500 dark:text-slate-400">Topics, sources, and delivery settings</p>
            </div>
          </div>
          <ChevronRight className="w-5 h-5 text-slate-400" />
        </Link>
      </motion.div>

      {/* Change Password */}
      <ChangePasswordSection />
    </div>
  );
}

function ChangePasswordSection() {
  const [showForm, setShowForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const changePassword = useChangePassword();

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

    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          events.emit('toast', {
            type: 'success',
            title: 'Password Updated',
            message: 'Your password has been changed successfully.',
            duration: 3000,
          });
          setShowForm(false);
          setCurrentPassword('');
          setNewPassword('');
          setConfirmPassword('');
        },
        onError: (error: any) => {
          events.emit('toast', {
            type: 'error',
            title: 'Update Failed',
            message: error?.response?.data?.detail || 'Failed to change password. Please try again.',
            duration: 5000,
          });
        },
      }
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700"
    >
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Security
      </h2>

      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors w-full text-left"
        >
          <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-xl flex items-center justify-center shrink-0">
            <Lock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <p className="font-medium text-slate-900 dark:text-white">Change Password</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">Update your account password</p>
          </div>
          <ChevronRight className="w-5 h-5 text-slate-400 ml-auto" />
        </button>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Current Password
            </label>
            <div className="relative">
              <input
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full pl-4 pr-10 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showCurrent ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              New Password
            </label>
            <div className="relative">
              <input
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                className="w-full pl-4 pr-10 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showNew ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={changePassword.isPending}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {changePassword.isPending ? 'Updating...' : 'Update Password'}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-6 py-2.5 text-slate-600 dark:text-slate-400 font-medium hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </motion.div>
  );
}
