import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Sliders,
  Bell,
  Clock,
  Type,
  Filter,
  Shield,
  Zap,
  ChevronRight,
  Check,
  X,
  Trash2,
  Plus,
} from 'lucide-react';
import { usePreferences, useUpdatePreferences } from '../hooks/useUser';

const TOPICS = [
  { id: 'AI', label: 'AI', color: 'bg-violet-500' },
  { id: 'Technology', label: 'Technology', color: 'bg-cyan-500' },
  { id: 'Business', label: 'Business', color: 'bg-amber-500' },
  { id: 'Science', label: 'Science', color: 'bg-emerald-500' },
  { id: 'Crypto', label: 'Crypto', color: 'bg-orange-500' },
  { id: 'Health', label: 'Health', color: 'bg-rose-500' },
  { id: 'Politics', label: 'Politics', color: 'bg-slate-500' },
  { id: 'Entertainment', label: 'Entertainment', color: 'bg-fuchsia-500' },
];

const SOURCES = [
  { id: 'TechCrunch', name: 'TechCrunch', icon: 'TC' },
  { id: 'Hacker News', name: 'Hacker News', icon: 'HN' },
  { id: 'The Verge', name: 'The Verge', icon: 'TV' },
  { id: 'Bloomberg', name: 'Bloomberg', icon: 'BB' },
  { id: 'WSJ', name: 'Wall Street Journal', icon: 'WSJ' },
  { id: 'Science Daily', name: 'Science Daily', icon: 'SD' },
];

const SUMMARY_LENGTHS = [
  { id: 'short', label: 'Quick', desc: 'Brief overview', time: '~30s' },
  { id: 'medium', label: 'Standard', desc: 'Balanced detail', time: '~2m' },
  { id: 'long', label: 'Deep Dive', desc: 'Full analysis', time: '~5m' },
];

const FRESHNESS_OPTIONS = [
  { id: 'breaking', label: 'Breaking News', desc: 'Latest updates, prioritize speed' },
  { id: 'daily', label: 'Daily Digest', desc: 'Balanced mix of recency and quality' },
  { id: 'weekly', label: 'Weekly Roundup', desc: 'Curated best content, less frequent' },
];

export function Preferences() {
  const { data: preferences, isLoading } = usePreferences();
  const updatePreferences = useUpdatePreferences();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [newBlockedTopic, setNewBlockedTopic] = useState('');

  const handleInterestChange = (topicId: string, value: number) => {
    const newInterests = {
      ...preferences?.topic_interests,
      [topicId]: value / 100,
    };
    updatePreferences.mutate({ topic_interests: newInterests });
  };

  const handleToggleSource = (sourceId: string) => {
    const currentSources = preferences?.source_preferences || {};
    const newValue = currentSources[sourceId] === 1.0 ? 0.5 : 1.0;
    updatePreferences.mutate({
      source_preferences: { ...currentSources, [sourceId]: newValue },
    });
  };

  const handleAddBlockedTopic = () => {
    if (newBlockedTopic && !preferences?.exclude_topics?.includes(newBlockedTopic)) {
      updatePreferences.mutate({
        exclude_topics: [...(preferences?.exclude_topics || []), newBlockedTopic],
      });
      setNewBlockedTopic('');
    }
  };

  const handleRemoveBlockedTopic = (topic: string) => {
    updatePreferences.mutate({
      exclude_topics: preferences?.exclude_topics?.filter((t) => t !== topic) || [],
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  const sections = [
    {
      id: 'interests',
      icon: Zap,
      title: 'Topic Interests',
      description: 'Adjust how much you want to see from each topic',
      color: 'violet',
    },
    {
      id: 'sources',
      icon: Sliders,
      title: 'News Sources',
      description: 'Prioritize your preferred publishers',
      color: 'blue',
    },
    {
      id: 'content',
      icon: Type,
      title: 'Content Preferences',
      description: 'Summary length and delivery settings',
      color: 'emerald',
    },
    {
      id: 'filters',
      icon: Filter,
      title: 'Content Filters',
      description: 'Block topics and sources you don\'t want to see',
      color: 'rose',
    },
    {
      id: 'notifications',
      icon: Bell,
      title: 'Notifications',
      description: 'Delivery time and frequency',
      color: 'amber',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white transition-colors">Preferences</h1>
          <p className="text-slate-500 dark:text-slate-400 transition-colors">Customize your Daily Feed experience</p>
        </div>
        {updatePreferences.isPending && (
          <span className="text-sm text-blue-600 flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            Saving...
          </span>
        )}
      </div>

      {/* Settings Sections */}
      <div className="space-y-4">
        {sections.map((section, index) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden transition-colors"
          >
            <button
              onClick={() => setActiveSection(activeSection === section.id ? null : section.id)}
              className="w-full flex items-center justify-between p-6 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl bg-${section.color}-50 dark:bg-${section.color}-900/30`}>
                  <section.icon className={`w-5 h-5 text-${section.color}-600 dark:text-${section.color}-400`} />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">{section.title}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">{section.description}</p>
                </div>
              </div>
              <ChevronRight
                className={`w-5 h-5 text-slate-400 transition-transform ${
                  activeSection === section.id ? 'rotate-90' : ''
                }`}
              />
            </button>

            {/* Expandable Content */}
            {activeSection === section.id && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="border-t border-slate-100"
              >
                <div className="p-6">
                  {section.id === 'interests' && (
                    <div className="space-y-4">
                      {TOPICS.map((topic) => {
                        const value = Math.round((preferences?.topic_interests?.[topic.id] || 0.5) * 100);
                        return (
                          <div key={topic.id} className="flex items-center gap-4">
                            <span className="w-24 text-sm font-medium text-slate-700">
                              {topic.label}
                            </span>
                            <div className="flex-1 flex items-center gap-3">
                              <input
                                type="range"
                                min="0"
                                max="100"
                                value={value}
                                onChange={(e) => handleInterestChange(topic.id, parseInt(e.target.value))}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                              />
                              <span className="w-12 text-sm font-medium text-slate-600 text-right">
                                {value}%
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {section.id === 'sources' && (
                    <div className="grid grid-cols-2 gap-3">
                      {SOURCES.map((source) => {
                        const isPreferred = preferences?.source_preferences?.[source.id] === 1.0;
                        return (
                          <button
                            key={source.id}
                            onClick={() => handleToggleSource(source.id)}
                            className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-all ${
                              isPreferred
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-slate-200 hover:border-slate-300'
                            }`}
                          >
                            <div
                              className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${
                                isPreferred ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {source.icon}
                            </div>
                            <span className="font-medium text-slate-900">{source.name}</span>
                            {isPreferred && <Check className="w-4 h-4 text-blue-600 ml-auto" />}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {section.id === 'content' && (
                    <div className="space-y-6">
                      {/* Summary Length */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Summary Length
                        </label>
                        <div className="grid grid-cols-3 gap-3">
                          {SUMMARY_LENGTHS.map((length) => (
                            <button
                              key={length.id}
                              onClick={() => updatePreferences.mutate({ summary_length: length.id })}
                              className={`p-4 rounded-xl border-2 text-center transition-all ${
                                preferences?.summary_length === length.id
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-slate-200 hover:border-slate-300'
                              }`}
                            >
                              <p className="font-medium text-slate-900">{length.label}</p>
                              <p className="text-xs text-slate-500 mt-1">{length.desc}</p>
                              <p className="text-xs text-slate-400 mt-0.5">{length.time}</p>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Freshness */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Content Freshness
                        </label>
                        <div className="space-y-2">
                          {FRESHNESS_OPTIONS.map((option) => (
                            <button
                              key={option.id}
                              onClick={() => updatePreferences.mutate({ freshness_preference: option.id })}
                              className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all ${
                                preferences?.freshness_preference === option.id
                                  ? 'border-blue-500 bg-blue-50'
                                  : 'border-slate-200 hover:border-slate-300'
                              }`}
                            >
                              <div className="text-left">
                                <p className="font-medium text-slate-900">{option.label}</p>
                                <p className="text-sm text-slate-500">{option.desc}</p>
                              </div>
                              {preferences?.freshness_preference === option.id && (
                                <Check className="w-5 h-5 text-blue-600" />
                              )}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Daily Limit */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Articles per Digest: {preferences?.daily_article_limit}
                        </label>
                        <input
                          type="range"
                          min="3"
                          max="20"
                          value={preferences?.daily_article_limit || 10}
                          onChange={(e) =>
                            updatePreferences.mutate({ daily_article_limit: parseInt(e.target.value) })
                          }
                          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-slate-500 mt-1">
                          <span>3</span>
                          <span>20</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {section.id === 'filters' && (
                    <div className="space-y-6">
                      {/* Blocked Topics */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Blocked Topics
                        </label>
                        <div className="flex gap-2 mb-3">
                          <input
                            type="text"
                            value={newBlockedTopic}
                            onChange={(e) => setNewBlockedTopic(e.target.value)}
                            placeholder="Add topic to block..."
                            className="flex-1 px-4 py-2 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                            onKeyDown={(e) => e.key === 'Enter' && handleAddBlockedTopic()}
                          />
                          <button
                            onClick={handleAddBlockedTopic}
                            className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                          >
                            <Plus className="w-5 h-5" />
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {preferences?.exclude_topics?.map((topic) => (
                            <span
                              key={topic}
                              className="inline-flex items-center gap-1 px-3 py-1 bg-rose-100 text-rose-700 rounded-full text-sm"
                            >
                              {topic}
                              <button
                                onClick={() => handleRemoveBlockedTopic(topic)}
                                className="hover:bg-rose-200 rounded-full p-0.5"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </span>
                          ))}
                          {(!preferences?.exclude_topics || preferences.exclude_topics.length === 0) && (
                            <p className="text-sm text-slate-400">No blocked topics</p>
                          )}
                        </div>
                      </div>

                      {/* Auto-adjust */}
                      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                        <div>
                          <p className="font-medium text-slate-900">Auto-adjust Interests</p>
                          <p className="text-sm text-slate-500">
                            Let AI learn from your reading habits
                          </p>
                        </div>
                        <button
                          onClick={() =>
                            updatePreferences.mutate({ auto_adjust_interests: !preferences?.auto_adjust_interests })
                          }
                          className={`relative w-14 h-7 rounded-full transition-colors ${
                            preferences?.auto_adjust_interests ? 'bg-blue-600' : 'bg-slate-300'
                          }`}
                        >
                          <div
                            className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                              preferences?.auto_adjust_interests ? 'translate-x-7' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                  )}

                  {section.id === 'notifications' && (
                    <div className="space-y-6">
                      {/* Delivery Time */}
                      <div>
                        <label className="flex items-center gap-2 text-sm font-medium text-slate-700 mb-3">
                          <Clock className="w-4 h-4" />
                          Daily Delivery Time
                        </label>
                        <input
                          type="time"
                          value={preferences?.delivery_time || '08:00'}
                          onChange={(e) =>
                            updatePreferences.mutate({ delivery_time: e.target.value })
                          }
                          className="px-4 py-2 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                        />
                      </div>

                      {/* Timezone */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                          Timezone
                        </label>
                        <select
                          value={preferences?.timezone || 'UTC'}
                          onChange={(e) => updatePreferences.mutate({ timezone: e.target.value })}
                          className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
                        >
                          <option value="UTC">UTC</option>
                          <option value="America/New_York">Eastern Time</option>
                          <option value="America/Chicago">Central Time</option>
                          <option value="America/Denver">Mountain Time</option>
                          <option value="America/Los_Angeles">Pacific Time</option>
                          <option value="Europe/London">London</option>
                          <option value="Europe/Paris">Paris</option>
                          <option value="Asia/Tokyo">Tokyo</option>
                        </select>
                      </div>

                      {/* Reading Time */}
                      <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                        <div>
                          <p className="font-medium text-slate-900">Show Reading Time</p>
                          <p className="text-sm text-slate-500">
                            Display estimated read duration on articles
                          </p>
                        </div>
                        <button
                          onClick={() =>
                            updatePreferences.mutate({
                              include_reading_time: !preferences?.include_reading_time,
                            })
                          }
                          className={`relative w-14 h-7 rounded-full transition-colors ${
                            preferences?.include_reading_time ? 'bg-blue-600' : 'bg-slate-300'
                          }`}
                        >
                          <div
                            className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${
                              preferences?.include_reading_time ? 'translate-x-7' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Reset Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-rose-50 rounded-2xl p-6 border border-rose-100"
      >
        <div className="flex items-start gap-4">
          <div className="p-3 bg-rose-100 rounded-xl">
            <Trash2 className="w-5 h-5 text-rose-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-rose-900">Reset Preferences</h3>
            <p className="text-sm text-rose-700 mt-1">
              This will reset all your preferences to default values. Your reading history will be preserved.
            </p>
          </div>
          <button className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors text-sm font-medium">
            Reset
          </button>
        </div>
      </motion.div>
    </div>
  );
}
