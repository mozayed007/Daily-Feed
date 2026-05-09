import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Square,
  Plus,
  Trash2,
  Clock,
  Calendar,
  Settings,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  X,
} from 'lucide-react';
import {
  useSchedulerJobs,
  useSchedulerStatus,
  useStartScheduler,
  useStopScheduler,
  useCreateJob,
  useDeleteJob,
  useToggleJob,
  useTriggerJob,
  ScheduledJob,
} from '../hooks/useScheduler';
import { CardSkeleton } from '../components/Skeleton';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { EmptyState } from '../components/EmptyState';
import { ConfirmDialog } from '../components/ConfirmDialog';

export function Scheduler() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: jobs, isLoading, isError, refetch } = useSchedulerJobs();
  const { data: statusData } = useSchedulerStatus();
  const schedulerRunning = statusData?.running ?? false;
  const startScheduler = useStartScheduler();
  const stopScheduler = useStopScheduler();
  const createJob = useCreateJob();
  const deleteJob = useDeleteJob();
  const toggleJob = useToggleJob();
  const triggerJob = useTriggerJob();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const handleStart = () => {
    startScheduler.mutate();
  };

  const handleStop = () => {
    stopScheduler.mutate();
  };

  const handleDelete = () => {
    if (confirmDelete) {
      deleteJob.mutate(confirmDelete);
      setConfirmDelete(null);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Scheduler
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Manage automated jobs and scheduled tasks
        </p>
      </motion.div>

      {/* Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div
              className={`w-10 sm:w-12 h-10 sm:h-12 rounded-xl flex items-center justify-center ${
                schedulerRunning
                  ? 'bg-emerald-100 dark:bg-emerald-900/30'
                  : 'bg-slate-100 dark:bg-slate-700'
              }`}
            >
              {schedulerRunning ? (
                <RefreshCw className="w-5 sm:w-6 h-5 sm:h-6 text-emerald-600 dark:text-emerald-400 animate-spin" />
              ) : (
                <Settings className="w-5 sm:w-6 h-5 sm:h-6 text-slate-500 dark:text-slate-400" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Scheduler Status
              </h2>
              <p
                className={`text-sm font-medium ${
                  schedulerRunning
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-500 dark:text-slate-400'
                }`}
              >
                {schedulerRunning ? 'Running' : 'Stopped'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 sm:self-auto self-end">
            {schedulerRunning ? (
              <button
                onClick={handleStop}
                disabled={stopScheduler.isPending}
                className="inline-flex items-center gap-2 px-4 py-2.5 min-h-[44px] bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400 rounded-xl font-medium hover:bg-rose-200 dark:hover:bg-rose-900/50 transition-colors disabled:opacity-50 w-full sm:w-auto justify-center"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={startScheduler.isPending}
                className="inline-flex items-center gap-2 px-4 py-2.5 min-h-[44px] bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-xl font-medium hover:bg-emerald-200 dark:hover:bg-emerald-900/50 transition-colors disabled:opacity-50 w-full sm:w-auto justify-center"
              >
                <Play className="w-4 h-4" />
                Start
              </button>
            )}
          </div>
        </div>
      </motion.div>

      {/* Jobs Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">
          Scheduled Jobs
        </h2>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 min-h-[44px] bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors w-full sm:w-auto justify-center"
        >
          <Plus className="w-4 h-4" />
          Add Job
        </button>
      </div>

      {/* Jobs List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : isError ? (
        <ErrorDisplay
          message="Failed to load scheduler jobs. Please try again."
          onRetry={() => refetch()}
        />
      ) : !jobs || jobs.length === 0 ? (
        <EmptyState
          icon={Clock}
          title="No scheduled jobs"
          description="Create your first scheduled job to automate fetching and digest generation."
          action={{
            label: 'Add Job',
            onClick: () => setIsModalOpen(true),
          }}
        />
      ) : (
        <div className="space-y-4">
          {jobs.map((job, index) => (
            <JobCard
              key={job.id}
              job={job}
              index={index}
              onToggle={(enabled) =>
                toggleJob.mutate({ jobId: job.id, enabled })
              }
              onDelete={() => setConfirmDelete(job.id)}
              onTrigger={() => triggerJob.mutate(job.id)}
              isToggling={toggleJob.isPending}
              isDeleting={deleteJob.isPending}
              isTriggering={triggerJob.isPending}
            />
          ))}
        </div>
      )}

      {/* Add Job Modal */}
      <AddJobModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={(jobData) => {
          createJob.mutate(jobData, {
            onSuccess: () => setIsModalOpen(false),
          });
        }}
        isSubmitting={createJob.isPending}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!confirmDelete}
        title="Delete Scheduled Job"
        message="Are you sure you want to delete this scheduled job? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  );
}

interface JobCardProps {
  job: ScheduledJob;
  index: number;
  onToggle: (enabled: boolean) => void;
  onDelete: () => void;
  onTrigger: () => void;
  isToggling: boolean;
  isDeleting: boolean;
  isTriggering: boolean;
}

function JobCard({
  job,
  index,
  onToggle,
  onDelete,
  onTrigger,
  isToggling,
  isDeleting,
  isTriggering,
}: JobCardProps) {
  const statusColors = {
    pending: 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300',
    running: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    completed: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    failed: 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400',
  };

  const formatInterval = (seconds?: number) => {
    if (!seconds) return null;
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700"
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 sm:gap-4">
            <div
              className={`w-10 sm:w-12 h-10 sm:h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                job.enabled
                  ? 'bg-blue-100 dark:bg-blue-900/30'
                  : 'bg-slate-100 dark:bg-slate-700'
              }`}
            >
              {job.status === 'running' ? (
                <RefreshCw className="w-5 sm:w-6 h-5 sm:h-6 text-blue-600 dark:text-blue-400 animate-spin" />
              ) : job.status === 'completed' ? (
                <CheckCircle className="w-5 sm:w-6 h-5 sm:h-6 text-emerald-600 dark:text-emerald-400" />
              ) : job.status === 'failed' ? (
                <AlertCircle className="w-5 sm:w-6 h-5 sm:h-6 text-rose-600 dark:text-rose-400" />
              ) : (
                <Clock className="w-5 sm:w-6 h-5 sm:h-6 text-slate-500 dark:text-slate-400" />
              )}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 sm:gap-3 mb-1 flex-wrap">
                <h3 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-white truncate">
                  {job.name}
                </h3>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${statusColors[job.status]}`}
                >
                  {job.status}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                {job.cron ? (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 sm:w-4 h-3 sm:h-4" />
                    {job.cron}
                  </span>
                ) : job.interval_seconds ? (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 sm:w-4 h-3 sm:h-4" />
                    Every {formatInterval(job.interval_seconds)}
                  </span>
                ) : null}
                <span className="flex items-center gap-1">
                  <RefreshCw className="w-3 sm:w-4 h-3 sm:h-4" />
                  {job.run_count} runs
                </span>
                {job.error_count > 0 && (
                  <span className="flex items-center gap-1 text-rose-500">
                    <AlertCircle className="w-3 sm:w-4 h-3 sm:h-4" />
                    {job.error_count} errors
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
            <button
              onClick={onTrigger}
              disabled={isTriggering}
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
              title="Run now"
            >
              <Play className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            </button>
            <button
              onClick={() => onToggle(!job.enabled)}
              disabled={isToggling}
              className={`p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg transition-colors disabled:opacity-50 ${
                job.enabled
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/50'
                  : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
              title={job.enabled ? 'Disable' : 'Enable'}
            >
              {job.enabled ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Square className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={onDelete}
              disabled={isDeleting}
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-rose-100 dark:hover:bg-rose-900/30 text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-lg transition-colors disabled:opacity-50"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Schedule Details */}
        <div className="pt-3 sm:pt-4 border-t border-slate-100 dark:border-slate-700 grid grid-cols-2 gap-3 sm:gap-4">
          <div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
              Next Run
            </p>
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              {formatDateTime(job.next_run)}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
              Last Run
            </p>
            <p className="text-sm font-medium text-slate-900 dark:text-white">
              {formatDateTime(job.last_run)}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

interface AddJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (job: {
    name: string;
    type: 'cron' | 'interval';
    cron?: string;
    interval?: number;
    enabled?: boolean;
  }) => void;
  isSubmitting: boolean;
}

function AddJobModal({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}: AddJobModalProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState<'cron' | 'interval'>('cron');
  const [cron, setCron] = useState('');
  const [interval, setInterval] = useState('');
  const [enabled, setEnabled] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      type,
      cron: type === 'cron' ? cron : undefined,
      interval: type === 'interval' ? parseInt(interval, 10) : undefined,
      enabled,
    });
  };

  const resetForm = () => {
    setName('');
    setType('cron');
    setCron('');
    setInterval('');
    setEnabled(true);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50"
            onClick={handleClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-4 sm:p-6 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
                  Add Scheduled Job
                </h2>
                <button
                  onClick={handleClose}
                  className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Job Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Daily Digest"
                    required
                    className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Schedule Type
                  </label>
                  <div className="flex gap-2 sm:gap-3">
                    <button
                      type="button"
                      onClick={() => setType('cron')}
                      className={`flex-1 px-3 sm:px-4 py-2.5 rounded-xl border transition-colors ${
                        type === 'cron'
                          ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-600 dark:text-blue-400'
                          : 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      <Calendar className="w-5 h-5 mx-auto mb-1" />
                      <span className="text-sm font-medium">Cron</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setType('interval')}
                      className={`flex-1 px-3 sm:px-4 py-2.5 rounded-xl border transition-colors ${
                        type === 'interval'
                          ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-600 dark:text-blue-400'
                          : 'bg-slate-50 dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      <Clock className="w-5 h-5 mx-auto mb-1" />
                      <span className="text-sm font-medium">Interval</span>
                    </button>
                  </div>
                </div>

                {type === 'cron' ? (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Cron Expression
                    </label>
                    <input
                      type="text"
                      value={cron}
                      onChange={(e) => setCron(e.target.value)}
                      placeholder="0 8 * * *"
                      required
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
                    />
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      e.g., "0 8 * * *" for daily at 8am
                    </p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={interval}
                      onChange={(e) => setInterval(e.target.value)}
                      placeholder="3600"
                      required
                      min="1"
                      className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      e.g., "3600" for every hour
                    </p>
                  </div>
                )}

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setEnabled(!enabled)}
                    className={`w-10 h-6 rounded-full transition-colors flex-shrink-0 ${
                      enabled
                        ? 'bg-blue-600'
                        : 'bg-slate-300 dark:bg-slate-600'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 bg-white rounded-full shadow transform transition-transform ${
                        enabled ? 'translate-x-5' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Enable job immediately
                  </span>
                </div>

                <div className="flex gap-3 pt-2 sm:pt-4">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex-1 px-4 py-2.5 min-h-[44px] border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-400 rounded-xl font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-4 py-2.5 min-h-[44px] bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 active:bg-blue-800 transition-colors disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <RefreshCw className="w-5 h-5 mx-auto animate-spin" />
                    ) : (
                      'Create Job'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
