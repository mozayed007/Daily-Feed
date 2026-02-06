import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Newspaper, 
  Clock, 
  Check,
  TrendingUp,
  Zap,
  BookOpen,
  ArrowRight,
  ChevronDown
} from 'lucide-react';
import { useOnboarding } from '../hooks/useUser';
import { useToast } from '../components/Toast';
import { api } from '../lib/api';

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

const SUMMARY_LENGTHS = [
  { id: 'short', label: 'Quick', desc: '1-2 sentences', time: '~30 sec read' },
  { id: 'medium', label: 'Standard', desc: '1-2 paragraphs', time: '~2 min read' },
  { id: 'long', label: 'Detailed', desc: 'Full analysis', time: '~5 min read' },
];

export function Onboarding() {
  const navigate = useNavigate();
  const onboarding = useOnboarding();
  const { addToast } = useToast();
  
  const [sources, setSources] = useState<{ id: string, name: string, category: string }[]>([]);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const response = await api.get('/sources');
        const formattedSources = response.data.map((s: any) => ({
          id: s.name, // Use name as ID to match existing logic
          name: s.name,
          category: s.category
        }));
        setSources(formattedSources);
      } catch (error) {
        console.error('Failed to fetch sources:', error);
        // Fallback to defaults if fetch fails
        setSources([
          { id: 'TechCrunch', name: 'TechCrunch', category: 'Tech' },
          { id: 'Hacker News', name: 'Hacker News', category: 'Tech' },
          { id: 'The Verge', name: 'The Verge', category: 'Tech' },
        ]);
      }
    };
    fetchSources();
  }, []);

  const [formData, setFormData] = useState({
    name: '',
    interests: [] as string[],
    sources: [] as string[],
    summaryLength: 'medium',
    deliveryTime: '08:00',
    dailyLimit: 10,
  });

  // Scroll to section handling
  const sectionRefs = {
    welcome: useRef<HTMLDivElement>(null),
    interests: useRef<HTMLDivElement>(null),
    sources: useRef<HTMLDivElement>(null),
    preferences: useRef<HTMLDivElement>(null),
  };

  const scrollToSection = (key: keyof typeof sectionRefs) => {
    sectionRefs[key].current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleSubmit = async () => {
    if (!formData.name) {
      addToast({ type: 'error', title: 'Name required', message: 'Please tell us what to call you.' });
      scrollToSection('welcome');
      return;
    }
    if (formData.interests.length < 3) {
      addToast({ type: 'error', title: 'More interests needed', message: 'Please select at least 3 topics.' });
      scrollToSection('interests');
      return;
    }
    
    try {
      await onboarding.mutateAsync({
        name: formData.name,
        interests: formData.interests,
        preferred_sources: formData.sources,
        summary_length: formData.summaryLength as any,
        delivery_time: formData.deliveryTime,
        daily_limit: formData.dailyLimit,
      });
      navigate('/');
    } catch (error) {
      addToast({ type: 'error', title: 'Setup failed', message: 'Something went wrong. Please try again.' });
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative transition-colors selection:bg-primary/30 selection:text-primary">
      {/* Background patterns */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-border/40 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 premium-gradient rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
              <Newspaper className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">Daily Feed</span>
          </div>
          <div className="text-sm font-medium text-muted-foreground">
            Setup
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-3xl mx-auto px-6 py-12 space-y-24 pb-32">
        
        {/* Welcome Section */}
        <section ref={sectionRefs.welcome} className="scroll-mt-24 space-y-8 text-center">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
              <Sparkles className="w-3 h-3" />
              <span>AI-Powered Intelligence</span>
            </div>
            
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-foreground">
              Design Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Perfect Feed</span>
            </h1>
            
            <p className="text-lg text-muted-foreground max-w-lg mx-auto leading-relaxed">
              We'll curate a personalized news experience just for you. Let's get everything set up in one go.
            </p>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="glass-card p-8 rounded-[2rem] max-w-md mx-auto bg-card/50 backdrop-blur-md border border-border"
          >
            <label className="block text-sm font-medium text-muted-foreground mb-3">
              First, what should we call you?
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter your name"
              className="w-full px-6 py-4 rounded-xl border border-input bg-background text-lg text-center text-foreground focus:border-primary focus:ring-4 focus:ring-primary/10 outline-none transition-all placeholder:text-muted-foreground/50"
              autoFocus
            />
          </motion.div>

          <div className="flex justify-center animate-bounce opacity-50">
            <ChevronDown className="w-6 h-6" />
          </div>
        </section>

        {/* Interests Section */}
        <section ref={sectionRefs.interests} className="scroll-mt-24 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">What interests you?</h2>
            <p className="text-muted-foreground">Select at least 3 topics to train your AI editor.</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
                  className={`relative p-6 rounded-2xl border-2 text-left transition-all duration-300 ${
                    selected
                      ? `border-transparent bg-gradient-to-br ${topic.color} text-white shadow-xl shadow-${topic.id.toLowerCase()}-500/20`
                      : 'border-border hover:border-primary/30 bg-card hover:bg-accent/50 text-foreground'
                  }`}
                >
                  <span className="text-3xl mb-3 block">{topic.icon}</span>
                  <span className="font-bold">{topic.label}</span>
                  {selected && (
                    <div className="absolute top-3 right-3 w-6 h-6 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 text-white" />
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </section>

        {/* Sources Section */}
        <section ref={sectionRefs.sources} className="scroll-mt-24 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Trusted Sources</h2>
            <p className="text-muted-foreground">Choose specific publishers or let us find the best ones.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {sources.map((source) => {
              const selected = formData.sources.includes(source.id);
              return (
                <motion.button
                  key={source.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => {
                    const newSources = selected
                      ? formData.sources.filter(id => id !== source.id)
                      : [...formData.sources, source.id];
                    setFormData({ ...formData, sources: newSources });
                  }}
                  className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                    selected
                      ? 'border-primary bg-primary/5 shadow-lg shadow-primary/5'
                      : 'border-border hover:border-primary/30 bg-card hover:bg-accent/50 text-foreground'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${
                    selected ? 'bg-primary text-white' : 'bg-secondary text-muted-foreground'
                  }`}>
                    {source.name[0]}
                  </div>
                  <div className="text-left">
                    <div className={`font-medium ${selected ? 'text-primary' : 'text-foreground'}`}>
                      {source.name}
                    </div>
                    <div className="text-xs text-muted-foreground">{source.category}</div>
                  </div>
                  {selected && (
                    <div className="ml-auto text-primary">
                      <Check className="w-5 h-5" />
                    </div>
                  )}
                </motion.button>
              );
            })}
          </div>
        </section>

        {/* Preferences Section */}
        <section ref={sectionRefs.preferences} className="scroll-mt-24 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Fine-tune Experience</h2>
            <p className="text-muted-foreground">How and when do you want your updates?</p>
          </div>

          <div className="glass-card rounded-3xl p-8 space-y-8 border border-border bg-card/50 backdrop-blur-md">
            {/* Summary Length */}
            <div className="space-y-4">
              <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Summary Detail</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {SUMMARY_LENGTHS.map((length) => (
                  <button
                    key={length.id}
                    onClick={() => setFormData({ ...formData, summaryLength: length.id })}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      formData.summaryLength === length.id
                        ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                        : 'border-border hover:border-primary/30 bg-background/50 text-foreground'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <p className={`font-semibold ${formData.summaryLength === length.id ? 'text-primary' : ''}`}>
                        {length.label}
                      </p>
                      {formData.summaryLength === length.id && <Check className="w-4 h-4 text-primary" />}
                    </div>
                    <p className="text-xs text-muted-foreground">{length.desc}</p>
                    <p className="text-xs text-muted-foreground/70 mt-1">{length.time}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 pt-4">
              {/* Delivery Time */}
              <div className="space-y-4">
                <label className="flex items-center gap-2 text-sm font-medium text-muted-foreground uppercase tracking-wider">
                  <Clock className="w-4 h-4" />
                  Delivery Time
                </label>
                <div className="relative">
                  <input
                    type="time"
                    value={formData.deliveryTime}
                    onChange={(e) => setFormData({ ...formData, deliveryTime: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border border-input bg-background text-lg text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                  />
                </div>
              </div>

              {/* Daily Limit */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Daily Limit
                  </label>
                  <span className="px-3 py-1 rounded-full bg-primary/10 text-primary font-bold text-sm">
                    {formData.dailyLimit} articles
                  </span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="20"
                  value={formData.dailyLimit}
                  onChange={(e) => setFormData({ ...formData, dailyLimit: parseInt(e.target.value) })}
                  className="w-full accent-primary h-2 bg-muted rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Minimum (3)</span>
                  <span>Maximum (20)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

      </main>

      {/* Floating Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/95 to-transparent z-40 pointer-events-none">
        <div className="max-w-md mx-auto pointer-events-auto">
          <button
            onClick={handleSubmit}
            disabled={onboarding.isPending}
            className="w-full group relative flex items-center justify-center gap-3 px-8 py-4 rounded-2xl font-bold text-lg text-white premium-gradient shadow-2xl shadow-primary/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {onboarding.isPending ? (
              'Setting up your feed...'
            ) : (
              <>
                Complete Setup
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </>
            )}
            <div className="absolute inset-0 rounded-2xl bg-white/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </div>
      </div>
    </div>
  );
}