import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { useOAuthCallback } from '../hooks/useUser';

export function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const oauthCallback = useOAuthCallback();

  const code = searchParams.get('code');
  const provider = searchParams.get('provider') || 'google';
  const error = searchParams.get('error');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Completing authentication...');

  useEffect(() => {
    if (error) {
      setStatus('error');
      setMessage('Authentication was cancelled or failed.');
      return;
    }

    if (!code) {
      setStatus('error');
      setMessage('No authorization code received.');
      return;
    }

    oauthCallback.mutate(
      { code, provider },
      {
        onSuccess: () => {
          setStatus('success');
          setMessage('Authentication successful! Redirecting...');
          setTimeout(() => navigate('/'), 1500);
        },
        onError: (err: unknown) => {
          setStatus('error');
          const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
          setMessage(detail || 'Authentication failed. Please try again.');
        },
      }
    );
  }, [code, provider, error, oauthCallback, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center max-w-md"
      >
        {status === 'loading' && (
          <>
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
            <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {message}
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              Please wait while we connect your account.
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <CheckCircle className="w-12 h-12 text-emerald-600 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {message}
            </h1>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="w-12 h-12 text-rose-600 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Authentication Failed
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mb-6">
              {message}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              Back to Login
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
}
