/**
 * Daily Feed - TypeScript API Types
 * 
 * This file contains all TypeScript types needed for frontend development.
 * Copy these into your React/Vue/Angular project.
 */

// ============================================================================
// Core Models
// ============================================================================

export interface Article {
  id: number;
  title: string;
  url: string;
  content?: string;
  summary?: string;
  source: string;
  category?: string;
  sentiment?: string;
  reading_time: number;
  key_points: string[];
  published_at?: string;
  fetched_at: string;
  is_processed: boolean;
  critic_score?: number;
}

export interface Source {
  id: number;
  name: string;
  url: string;
  category?: string;
  enabled: boolean;
  last_fetch?: string;
  fetch_count: number;
  error_count: number;
  created_at: string;
}

export interface Digest {
  id: number;
  created_at: string;
  article_count: number;
  articles?: Article[];
  delivered: boolean;
}

// ============================================================================
// User & Personalization
// ============================================================================

export interface User {
  id: string;
  email: string;
  name: string;
  onboarding_completed: boolean;
  created_at: string;
}

export interface UserPreferences {
  topic_interests: Record<string, number>;  // { "AI": 0.9, "Tech": 0.7 }
  source_preferences: Record<string, number>;  // { "TechCrunch": 1.0 }
  summary_length: 'short' | 'medium' | 'long';
  daily_article_limit: number;
  delivery_time: string;  // "HH:MM" format
  timezone: string;
  exclude_topics: string[];
  exclude_sources: string[];
  language_preference: string;
  include_reading_time: boolean;
  freshness_preference: 'breaking' | 'daily' | 'weekly';
  auto_adjust_interests: boolean;
  diversity_boost: number;
}

export interface UserInteraction {
  id: string;
  article_id: number;
  delivered_at: string;
  opened_at?: string;
  read_duration_seconds: number;
  scroll_depth: number;
  rating?: -1 | 0 | 1;
  saved: boolean;
  shared: boolean;
  engagement_score: number;
}

export type UserPreferencesResponse = UserPreferences;
export type UserInteractionResponse = UserInteraction;

export interface PersonalizedDigest {
  id: string;
  created_at: string;
  articles: PersonalizedArticle[];
  personalization_score: number;
  diversity_score: number;
  status: 'pending' | 'sent' | 'opened';
  sent_at?: string;
}

export interface PersonalizedArticle extends Article {
  score: number;
  score_breakdown: {
    topic: number;
    source: number;
    freshness: number;
    quality: number;
    diversity: number;
    final: number;
  };
}

export interface UserStats {
  total_articles_read: number;
  total_articles_saved: number;
  average_reading_time: number;
  favorite_topics: Array<{ topic: string; count: number }>;
  favorite_sources: Array<{ source: string; count: number }>;
  digest_open_rate: number;
  last_7_days_activity: number[];
}

// ============================================================================
// API Request/Response Types
// ============================================================================

// Articles
export interface ArticleListResponse {
  articles: Article[];
  total: number;
  page: number;
  page_size: number;
}

export interface ArticleFilterParams {
  processed?: boolean;
  category?: string;
  source?: string;
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
}

// Sources
export interface CreateSourceRequest {
  name: string;
  url: string;
  category?: string;
  enabled?: boolean;
}

// User Onboarding
export interface OnboardingRequest {
  name: string;
  interests: string[];
  preferred_sources: string[];
  summary_length?: 'short' | 'medium' | 'long';
  delivery_time?: string;
  daily_limit?: number;
}

// Preferences
export interface UpdatePreferencesRequest {
  topic_interests?: Record<string, number>;
  source_preferences?: Record<string, number>;
  summary_length?: 'short' | 'medium' | 'long';
  daily_article_limit?: number;
  delivery_time?: string;
  timezone?: string;
  exclude_topics?: string[];
  exclude_sources?: string[];
  language_preference?: string;
  include_reading_time?: boolean;
  freshness_preference?: 'breaking' | 'daily' | 'weekly';
  auto_adjust_interests?: boolean;
  diversity_boost?: number;
}

// Feedback
export interface ArticleFeedbackRequest {
  articleId: number;
  feedback: 'like' | 'dislike' | 'save' | 'dismiss';
}

export interface RecordInteractionRequest {
  article_id: number;
  opened?: boolean;
  read_duration_seconds?: number;
  scroll_depth?: number;
  rating?: -1 | 0 | 1;
  saved?: boolean;
  shared?: boolean;
  dismissed?: boolean;
}

// Pipeline
export interface PipelineRequest {
  task_type: 'fetch' | 'process' | 'digest' | 'full' | 'memory_sync';
  params?: Record<string, any>;
}

export interface PipelineResponse {
  success: boolean;
  task_type: string;
  result: any;
}

// Scheduler
export interface ScheduledJob {
  id: string;
  name: string;
  enabled: boolean;
  cron?: string;
  interval?: number;
  next_run?: string;
  last_run?: string;
  run_count: number;
  error_count: number;
}

export interface CreateJobRequest {
  name: string;
  type: 'cron' | 'interval';
  cron?: string;
  interval?: number;
  enabled?: boolean;
}

// Memory
export interface MemoryStats {
  total_units: number;
  total_categories: number;
  category_distribution: Record<string, number>;
  total_entities: number;
  top_entities: Array<{ entity: string; count: number }>;
}

export interface UserInterests {
  topics: Array<{ topic: string; score: number }>;
  sources: Array<{ source: string; score: number }>;
  reading_patterns: {
    avg_reading_time: number;
    preferred_times: string[];
    category_distribution: Record<string, number>;
  };
}

// Config
export interface AppConfig {
  name: string;
  version: string;
  debug: boolean;
  host: string;
  port: number;
  environment: string;
  features: {
    agent_loop: boolean;
    memory: boolean;
    scheduler: boolean;
    personalization: boolean;
  };
}

// Stats
export interface AppStats {
  total_articles: number;
  processed_articles: number;
  pending_articles: number;
  total_sources: number;
  active_sources: number;
  total_digests: number;
  memory_units?: number;
}

// ============================================================================
// UI/Component Types
// ============================================================================

export interface ArticleCardProps {
  article: PersonalizedArticle | Article;
  showScore?: boolean;
  onLike?: (id: number) => void;
  onSave?: (id: number) => void;
  onDismiss?: (id: number) => void;
  onClick?: (article: Article) => void;
}

export interface DigestViewProps {
  digest: PersonalizedDigest;
  onArticleFeedback?: (articleId: number, feedback: string) => void;
}

export interface PreferencesFormProps {
  preferences: UserPreferences;
  onUpdate: (prefs: Partial<UserPreferences>) => void;
  availableTopics: string[];
  availableSources: string[];
}

export interface OnboardingStepProps {
  data: Partial<OnboardingRequest>;
  onUpdate: (data: Partial<OnboardingRequest>) => void;
  onNext: () => void;
  onBack?: () => void;
}

export interface StatsDashboardProps {
  stats: UserStats;
  timeRange?: '7d' | '30d' | '90d';
}

// ============================================================================
// API Error Types
// ============================================================================

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// ============================================================================
// WebSocket Types (Future)
// ============================================================================

export interface WebSocketMessage {
  type: 'article_new' | 'digest_ready' | 'job_complete' | 'error';
  payload: any;
  timestamp: string;
}
