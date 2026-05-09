import { useState } from "react";
import { motion } from "framer-motion";
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
  Area,
  AreaChart,
} from "recharts";
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
} from "lucide-react";
import { useUserStats } from "../hooks/useUser";
import { StatsCardSkeleton, ChartSkeleton } from "../components/Skeleton";
import { ErrorDisplay } from "../components/ErrorDisplay";

const COLORS = {
  ai: "#8b5cf6",
  tech: "#06b6d4",
  business: "#f59e0b",
  science: "#10b981",
  crypto: "#f97316",
  other: "#64748b",
};

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const TOPIC_COLORS: Record<string, string> = {
  AI: COLORS.ai,
  Technology: COLORS.tech,
  Business: COLORS.business,
  Science: COLORS.science,
  Crypto: COLORS.crypto,
  Health: "#f43f5e",
  Politics: "#475569",
  Entertainment: "#a855f7",
  Other: COLORS.other,
};

const SOURCE_COLORS = ["#3b82f6", "#f97316", "#8b5cf6", "#10b981", "#64748b", "#f59e0b", "#ef4444", "#06b6d4"];

export function Stats() {
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d">("7d");
  const days = timeRange === "7d" ? 7 : timeRange === "30d" ? 30 : 90;
  const { data: stats, isLoading, isError, refetch } = useUserStats(days);

  // Derive chart data from real stats
  const activityData = stats?.last_7_days_activity?.map((count, index) => {
    const today = new Date();
    const dayIndex = (today.getDay() + 1 + index) % 7; // Map to last 7 days ending with today
    return {
      day: DAY_LABELS[dayIndex],
      articles: count,
    };
  }) || DAY_LABELS.map((day) => ({ day, articles: 0 }));

  const topicsData = stats?.favorite_topics?.map((t) => ({
    name: t.topic,
    value: t.count,
    color: TOPIC_COLORS[t.topic] || TOPIC_COLORS.Other,
  })) || [];

  const sourcesData = stats?.favorite_sources?.map((s, index) => ({
    name: s.source,
    articles: s.count,
    color: SOURCE_COLORS[index % SOURCE_COLORS.length],
  })) || [];

  // Engagement trend derived from activity data (mocked weekly aggregation)
  const engagementData = activityData.reduce(
    (acc, curr, index) => {
      const weekIndex = Math.floor(index / 7);
      if (!acc[weekIndex]) {
        acc[weekIndex] = { week: `W${weekIndex + 1}`, opens: 0, clicks: 0 };
      }
      acc[weekIndex].opens += curr.articles;
      acc[weekIndex].clicks += Math.round(curr.articles * 0.6); // Estimate clicks as 60% of opens
      return acc;
    },
    [] as { week: string; opens: number; clicks: number }[]
  );

  // Fallback to single week if not enough data
  const finalEngagementData =
    engagementData.length > 0
      ? engagementData
      : [{ week: "This Week", opens: stats?.total_articles_read || 0, clicks: Math.round((stats?.total_articles_read || 0) * 0.6) }];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4].map((i) => (
            <StatsCardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <ErrorDisplay
        message="We couldn't load analytics right now. Please try again in a moment."
        onRetry={() => refetch()}
      />
    );
  }

  const statCards = [
    {
      icon: BookOpen,
      label: "Articles Read",
      value: stats?.total_articles_read || 0,
      change: "+12%",
      color: "blue",
    },
    {
      icon: Bookmark,
      label: "Saved Articles",
      value: stats?.total_articles_saved || 0,
      change: "+8%",
      color: "amber",
    },
    {
      icon: Clock,
      label: "Avg Read Time",
      value: `${Math.round((stats?.average_reading_time || 0) / 60)}m`,
      change: "+5%",
      color: "emerald",
    },
    {
      icon: Eye,
      label: "Open Rate",
      value: `${stats?.digest_open_rate || 0}%`,
      change: "+15%",
      color: "purple",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white transition-colors">
            Your Reading Analytics
          </h1>
          <p className="text-slate-500 dark:text-slate-400 transition-colors">
            Track your news consumption habits
          </p>
        </div>
        <div className="w-full sm:w-auto relative">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="w-full sm:w-40 appearance-none bg-white border border-slate-200 rounded-xl px-4 py-2.5 pr-10 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {statCards.map((card, index) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between">
              <div
                className={`p-2.5 rounded-xl bg-${card.color}-50 dark:bg-${card.color}-900/30`}
              >
                <card.icon
                  className={`w-5 h-5 text-${card.color}-600 dark:text-${card.color}-400`}
                />
              </div>
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-1 rounded-full">
                {card.change}
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white mt-3 transition-colors">
              {card.value}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
              {card.label}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Activity Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3 mb-4 sm:mb-6">
            <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">
                Daily Activity
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
                Articles read per day
              </p>
            </div>
          </div>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                  vertical={false}
                />
                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Bar dataKey="articles" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Topics Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3 mb-4 sm:mb-6">
            <div className="p-2 bg-purple-50 dark:bg-purple-900/30 rounded-lg">
              <Zap className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">
                Topic Distribution
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
                What you read most
              </p>
            </div>
          </div>
          <div className="h-56 sm:h-64 flex items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={topicsData.length > 0 ? topicsData : [{ name: "No Data", value: 1, color: COLORS.other }]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {(topicsData.length > 0 ? topicsData : [{ name: "No Data", value: 1, color: COLORS.other }]).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--tooltip-bg, #fff)",
                    border: "1px solid var(--tooltip-border, #e2e8f0)",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex flex-col gap-2 min-w-[120px]">
              {topicsData.length > 0 ? (
                topicsData.map((topic) => (
                  <div key={topic.name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: topic.color }}
                    />
                    <span className="text-sm text-slate-600 dark:text-slate-300">
                      {topic.name}
                    </span>
                    <span className="text-sm font-medium text-slate-900 dark:text-white ml-auto">
                      {topic.value}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">No topic data yet</p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Engagement Trend */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3 mb-4 sm:mb-6">
            <div className="p-2 bg-emerald-50 dark:bg-emerald-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">
                Engagement Trend
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
                Opens vs Clicks over time
              </p>
            </div>
          </div>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={finalEngagementData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                  vertical={false}
                />
                <XAxis
                  dataKey="week"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--tooltip-bg, #fff)",
                    border: "1px solid var(--tooltip-border, #e2e8f0)",
                    borderRadius: "8px",
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
              <span className="text-sm text-slate-600 dark:text-slate-300">
                Opens
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="text-sm text-slate-600 dark:text-slate-300">
                Clicks
              </span>
            </div>
          </div>
        </motion.div>

        {/* Top Sources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
        >
          <div className="flex items-center gap-3 mb-4 sm:mb-6">
            <div className="p-2 bg-amber-50 dark:bg-amber-900/30 rounded-lg">
              <Target className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-white transition-colors">
                Top Sources
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
                Your most-read publishers
              </p>
            </div>
          </div>
          <div className="space-y-4">
            {sourcesData.length > 0 ? (
              sourcesData.map((source, index) => (
                <div key={source.name} className="flex items-center gap-4">
                  <span className="text-sm font-medium text-slate-400 dark:text-slate-500 w-6">
                    #{index + 1}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-slate-900 dark:text-white">
                        {source.name}
                      </span>
                      <span className="text-sm text-slate-500 dark:text-slate-400">
                        {source.articles} articles
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min((source.articles / (sourcesData[0]?.articles || 1)) * 100, 100)}%` }}
                        transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: source.color }}
                      />
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500 text-center py-4">No source data yet</p>
            )}
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
          {stats?.total_articles_read ? (
            <>
              You've read <span className="font-semibold text-white">{stats.total_articles_read} articles</span> this week with an average read time of <span className="font-semibold text-white">{Math.round((stats?.average_reading_time || 0) / 60)}m</span>.
              {stats.favorite_topics?.[0] && (
                <> Your top topic is <span className="font-semibold text-white">{stats.favorite_topics[0].topic}</span>.</>
              )}
            </>
          ) : (
            "Start reading articles to see your personalized insights here!"
          )}
        </p>
      </motion.div>
    </div>
  );
}
