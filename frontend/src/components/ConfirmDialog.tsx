import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning';
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={onCancel}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: 'spring', duration: 0.3 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white dark:bg-slate-800 rounded-2xl p-6 w-full max-w-sm shadow-2xl border border-slate-200 dark:border-slate-700"
          >
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                  variant === 'danger'
                    ? 'bg-rose-100 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400'
                    : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
                }`}
              >
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">{title}</h2>
            </div>

            <p className="text-slate-600 dark:text-slate-300 mb-6 text-sm leading-relaxed">
              {message}
            </p>

            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={onCancel}
                className="px-4 py-2.5 text-slate-600 dark:text-slate-400 font-medium hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors"
              >
                {cancelLabel}
              </button>
              <button
                onClick={onConfirm}
                className={`px-4 py-2.5 rounded-xl font-medium text-white transition-colors ${
                  variant === 'danger'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : 'bg-amber-600 hover:bg-amber-700'
                }`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
