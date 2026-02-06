import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import {
  BookOpen,
  Bookmark,
  TrendingUp,
  Clock,
  Calendar,
  Eye,
  Zap,
  Target,
  ChevronDown,
} from 'lucide-react';
import { useUserStats } from '../hooks/useUser';

const COLORS = {
  ai: '#8b5cf6',
  tech: '#06b6d4',
  business: '#f59e0b',
  science: '#10b981',
  crypto: '#f97316',
  other: '#64748b',
};

const ACTIVITY_DATA = [
  { day: 'Mon', articles: 5, time: 12 },
  { day: 'Tue', articles: 8, time: 18 },
  { day: 'Wed', articles: 3, time: 8 },
  { day: 'Thu', articles: 12, time: 28 },
  { day: 'Fri', articles: 7, time: 15 },
  { day: 'Sat', articles: 15, time: 35 },
  { day: 'Sun', articles: 10, time: 22 },
];

const TOPICS_DATA = [
  { name: 'AI', value: 35, color: COLORS.ai },
  { name: 'Technology', value: 25, color: COLORS.tech },
  { name: 'Business', value: 20, color: COLORS.business },
  { name: 'Science', value: 12, color: COLORS.science },
  { name: 'Other', value: 8, color: COLORS.other },
];

const SOURCES_DATA = [
  { name: 'TechCrunch', articles: 45, color: '#3b82f6' },
  { name: 'Hacker News', articles: 38, color: '#f97316' },
  { name: 'The Verge', articles: 32, color: '#8b5cf6' },
  { name: 'Bloomberg', articles: 28, color: '#10b981' },
  { name: 'WSJ', articles: 22, color: '#64748b' },
];

const ENGAGEMENT_DATA = [
  { week: 'W1', opens: 65, clicks: 42 },
  { week: 'W2', opens: 72, clicks: 48 },
  { week: 'W3', opens: 68, clicks: 45 },
  { week: 'W4', opens: 85, clicks: 62 },
];

export function Stats() {
  const { data: stats, isLoading } = useUserStats();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  const statCards = [
    {
      icon: BookOpen,
      label: 'Articles Read',
      value: stats?.total_articles_read || 0,
      change: '+12%',
      color: 'blue',
    },
    {
      icon: Bookmark,
      label: 'Saved Articles',
      value: stats?.total_articles_saved || 0,
      change: '+8%',
      color: 'amber',
    },
    {
      icon: Clock,
      label: 'Avg Read Time',
      value: `${Math.round((stats?.average_reading_time || 0) / 60)}m`,
      change: '+5%',
      color: 'emerald',
    },
    {
      icon: Eye,
      label: 'Open Rate',
      value: `${stats?.digest_open_rate || 0}%`,
      change: '+15%',
      color: 'purple',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white transition-colors">Your Reading Analytics</h1>
          <p className="text-slate-500 dark:text-slate-400 transition-colors">Track your news consumption habits</p>
        </div>
        <div className="relative">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="appearance-none bg-white border border-slate-200 rounded-xl px-4 py-2 pr-10 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, index) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between">
              <div className={`p-2.5 rounded-xl bg-${card.color}-50 dark:bg-${card.color}-900/30`}>
                <card.icon className={`w-5 h-5 text-${card.color}-600 dark:text-${card.color}-400`} />
              </div>
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-1 rounded-full">
                {card.change}
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white mt-3 transition-colors">{card.value}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">{card.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">Daily Activity</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">Articles read per day</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ACTIVITY_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Bar
                  dataKey="articles"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Topics Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-50 rounded-lg">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Topic Distribution</h3>
              <p className="text-sm text-slate-500">What you read most</p>
            </div>
          </div>
          <div className="h-64 flex items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={TOPICS_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {TOPICS_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex flex-col gap-2 min-w-[120px]">
              {TOPICS_DATA.map((topic) => (
                <div key={topic.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: topic.color }}
                  />
                  <span className="text-sm text-slate-600">{topic.name}</span>
                  <span className="text-sm font-medium text-slate-900 ml-auto">
                    {topic.value}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Engagement Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-emerald-50 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Engagement Trend</h3>
              <p className="text-sm text-slate-500">Opens vs Clicks over time</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={ENGAGEMENT_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="week"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="opens"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="clicks"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-violet-500" />
              <span className="text-sm text-slate-600">Opens</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="text-sm text-slate-600">Clicks</span>
            </div>
          </div>
        </motion.div>

        {/* Top Sources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-amber-50 rounded-lg">
              <Target className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Top Sources</h3>
              <p className="text-sm text-slate-500">Your most-read publishers</p>
            </div>
          </div>
          <div className="space-y-4">
            {SOURCES_DATA.map((source, index) => (
              <div key={source.name} className="flex items-center gap-4">
                <span className="text-sm font-medium text-slate-400 w-6">
                  #{index + 1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-slate-900">{source.name}</span>
                    <span className="text-sm text-slate-500">{source.articles} articles</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(source.articles / 50) * 100}%` }}
                      transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: source.color }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Insights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 text-white"
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <h3 className="font-semibold text-lg">Weekly Insight</h3>
        </div>
        <p className="text-blue-100">
          You're most active on <span className="font-semibold text-white">Saturday</span> with an average of{' '}
          <span className="font-semibold text-white">15 articles</span> read. Your engagement has increased by{' '}
          <span className="font-semibold text-white">23%</span> this week!
        </p>
      </motion.div>
    </div>
  );
}
