import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronRight, 
  ChevronLeft, 
  Sparkles, 
  Newspaper, 
  Clock, 
  Check,
  TrendingUp,
  Zap,
  BookOpen,
  ArrowRight
} from 'lucide-react';
import { useOnboarding } from '../hooks/useUser';

const TOPICS = [
  { id: 'AI', label: 'AI', icon: '🤖', color: 'from-violet-500 to-purple-600' },
  { id: 'Technology', label: 'Technology', icon: '💻', color: 'from-cyan-500 to-blue-600' },
  { id: 'Business', label: 'Business', icon: '💼', color: 'from-amber-500 to-orange-600' },
  { id: 'Science', label: 'Science', icon: '🔬', color: 'from-emerald-500 to-green-600' },
  { id: 'Crypto', label: 'Crypto', icon: '₿', color: 'from-orange-500 to-red-600' },
  { id: 'Health', label: 'Health', icon: '❤️', color: 'from-rose-500 to-pink-600' },
  { id: 'Politics', label: 'Politics', icon: '🏛️', color: 'from-slate-500 to-slate-600' },
  { id: 'Entertainment', label: 'Entertainment', icon: '🎬', color: 'from-fuchsia-500 to-purple-600' },
];

const SOURCES = [
  { id: 'TechCrunch', name: 'TechCrunch', category: 'Tech' },
  { id: 'Hacker News', name: 'Hacker News', category: 'Tech' },
  { id: 'The Verge', name: 'The Verge', category: 'Tech' },
  { id: 'Bloomberg', name: 'Bloomberg', category: 'Business' },
  { id: 'WSJ', name: 'Wall Street Journal', category: 'Business' },
  { id: 'Science Daily', name: 'Science Daily', category: 'Science' },
];

const SUMMARY_LENGTHS = [
  { id: 'short', label: 'Quick', desc: '1-2 sentences', time: '~30 sec read' },
  { id: 'medium', label: 'Standard', desc: '1-2 paragraphs', time: '~2 min read' },
  { id: 'long', label: 'Detailed', desc: 'Full analysis', time: '~5 min read' },
];

export function Onboarding() {
  const navigate = useNavigate();
  const onboarding = useOnboarding();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    interests: [] as string[],
    sources: [] as string[],
    summaryLength: 'medium',
    deliveryTime: '08:00',
    dailyLimit: 10,
  });

  const steps = [
    { title: 'Welcome', description: 'Get started with your personalized news' },
    { title: 'Your Interests', description: 'Select topics you care about' },
    { title: 'Sources', description: 'Choose your preferred publishers' },
    { title: 'Preferences', description: 'Customize your experience' },
  ];

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleSubmit = async () => {
    await onboarding.mutateAsync({
      name: formData.name,
      interests: formData.interests,
      preferred_sources: formData.sources,
      summary_length: formData.summaryLength as any,
      delivery_time: formData.deliveryTime,
      daily_limit: formData.dailyLimit,
    });
    navigate('/');
  };

  const canProceed = () => {
    switch (step) {
      case 0: return formData.name.length > 0;
      case 1: return formData.interests.length > 0;
      case 2: return formData.sources.length > 0;
      default: return true;
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex items-center justify-center p-4 transition-colors">
      {/* Dynamic Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/20 rounded-full blur-[120px] animate-pulse delay-700" />
      
      <div className="w-full max-w-2xl relative z-10">
        {/* Progress Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 premium-gradient rounded-2xl flex items-center justify-center shadow-2xl shadow-primary/20 border border-white/20">
                <Newspaper className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-extrabold tracking-tight text-foreground">Daily Feed</h1>
                <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest">Intelligence Layer</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-1.5 rounded-full transition-all duration-500 ${
                    i === step ? 'w-10 bg-primary' : i < step ? 'w-2 bg-primary/50' : 'w-2 bg-muted'
                  }`}
                />
              ))}
            </div>
          </div>
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center space-y-2"
          >
            <h2 className="text-2xl font-bold tracking-tight text-foreground">{steps[step].title}</h2>
            <p className="text-muted-foreground">{steps[step].description}</p>
          </motion.div>
        </div>

        {/* Card */}
        <motion.div
          key={step}
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="glass-card rounded-[2.5rem] overflow-hidden border-white/10"
        >
          <div className="p-8">
            <AnimatePresence mode="wait">
              {step === 0 && (
                <motion.div
                  key="welcome"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  <div className="text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/50 dark:to-purple-900/50 rounded-3xl flex items-center justify-center mx-auto">
                      <Sparkles className="w-10 h-10 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
                      Welcome to Daily Feed
                    </h3>
                    <p className="text-slate-600 dark:text-slate-300 max-w-md mx-auto">
                      Get personalized news digests powered by AI. 
                      We'll learn what you like and deliver the perfect content.
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { icon: Zap, label: 'AI-Powered', desc: 'Smart curation' },
                      { icon: BookOpen, label: 'Learn', desc: 'Adapts to you' },
                      { icon: TrendingUp, label: 'Track', desc: 'See progress' },
                    ].map((feature) => (
                      <div key={feature.label} className="text-center p-4 rounded-xl bg-slate-50 dark:bg-slate-700/50">
                        <feature.icon className="w-6 h-6 text-blue-600 dark:text-blue-400 mx-auto mb-2" />
                        <p className="font-medium text-slate-900 dark:text-white">{feature.label}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">{feature.desc}</p>
                      </div>
                    ))}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 transition-colors">
                      What should we call you?
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Enter your name"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all"
                    />
                  </div>
                </motion.div>
              )}

              {step === 1 && (
                <motion.div
                  key="interests"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-4"
                >
                  <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-4">
                    Select at least 3 topics you're interested in
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {TOPICS.map((topic) => {
                      const selected = formData.interests.includes(topic.id);
                      return (
                        <motion.button
                          key={topic.id}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => {
                            setFormData({
                              ...formData,
                              interests: selected
                                ? formData.interests.filter((i) => i !== topic.id)
                                : [...formData.interests, topic.id],
                            });
                          }}
                          className={`relative p-4 rounded-xl border-2 transition-all ${
                            selected
                              ? `border-transparent bg-gradient-to-br ${topic.color} text-white shadow-lg shadow-${topic.id.toLowerCase()}-500/20`
                              : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                          }`}
                        >
                          <span className="text-2xl mb-2 block">{topic.icon}</span>
                          <span className="font-medium text-sm">{topic.label}</span>
                          {selected && (
                            <motion.div
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              className="absolute top-2 right-2 w-5 h-5 bg-white dark:bg-slate-200 rounded-full flex items-center justify-center"
                            >
                              <Check className="w-3 h-3 text-slate-900" />
                            </motion.div>
                          )}
                        </motion.button>
                      );
                    })}
                  </div>
                  <p className="text-center text-sm text-slate-500 dark:text-slate-400 transition-colors">
                     Selected: {formData.interests.length} topics
                   </p>
                </motion.div>
              )}

              {step === 2 && (
                <motion.div
                  key="sources"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-3"
                >
                  <p className="text-sm text-slate-500 dark:text-slate-400 text-center mb-4 transition-colors">
                    Choose your preferred news sources
                  </p>
                  {SOURCES.map((source) => {
                    const selected = formData.sources.includes(source.id);
                    return (
                      <motion.button
                        key={source.id}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => {
                          setFormData({
                            ...formData,
                            sources: selected
                              ? formData.sources.filter((s) => s !== source.id)
                              : [...formData.sources, source.id],
                          });
                        }}
                        className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all ${
                          selected
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                            : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            selected ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                          }`}>
                            <Newspaper className="w-5 h-5" />
                          </div>
                          <div className="text-left">
                            <p className="font-medium text-slate-900 dark:text-white transition-colors">{source.name}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 transition-colors">{source.category}</p>
                          </div>
                        </div>
                        {selected && <Check className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
                      </motion.button>
                    );
                  })}
                </motion.div>
              )}

              {step === 3 && (
                <motion.div
                  key="preferences"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="space-y-6"
                >
                  {/* Summary Length */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 transition-colors">
                      Summary Length
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {SUMMARY_LENGTHS.map((length) => (
                        <button
                          key={length.id}
                          onClick={() => setFormData({ ...formData, summaryLength: length.id })}
                          className={`p-4 rounded-xl border-2 text-center transition-all ${
                            formData.summaryLength === length.id
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                              : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800'
                          }`}
                        >
                          <p className="font-medium text-slate-900 dark:text-white transition-colors">{length.label}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 transition-colors">{length.desc}</p>
                          <p className="text-xs text-slate-400 dark:text-slate-500 transition-colors">{length.time}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Delivery Time */}
                  <div>
                    <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 transition-colors">
                      <Clock className="w-4 h-4" />
                      Daily Delivery Time
                    </label>
                    <input
                      type="time"
                      value={formData.deliveryTime}
                      onChange={(e) => setFormData({ ...formData, deliveryTime: e.target.value })}
                      className="px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-800 outline-none transition-all"
                    />
                  </div>

                  {/* Daily Limit */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 transition-colors">
                      Articles per Digest: {formData.dailyLimit}
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="20"
                      value={formData.dailyLimit}
                      onChange={(e) => setFormData({ ...formData, dailyLimit: parseInt(e.target.value) })}
                      className="w-full accent-blue-600"
                    />
                    <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1 transition-colors">
                      <span>3</span>
                      <span>20</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Footer */}
          <div className="px-8 py-6 bg-secondary/30 backdrop-blur-md border-t border-border/50 flex items-center justify-between transition-colors">
            <button
              onClick={handleBack}
              disabled={step === 0}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold transition-all ${
                step === 0
                  ? 'text-muted-foreground/30 cursor-not-allowed'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`flex items-center gap-2 px-8 py-3 rounded-2xl font-bold transition-all ${
                canProceed()
                  ? 'premium-gradient text-white shadow-xl shadow-primary/20 hover:scale-105 active:scale-95'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              }`}
            >
              {step === steps.length - 1 ? (
                onboarding.isPending ? (
                  'Configuring...'
                ) : (
                  <>
                    Initialize Engine
                    <Sparkles className="w-4 h-4" />
                  </>
                )
              ) : (
                <>
                  Proceed
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
