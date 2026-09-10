export type OnboardingStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped'

// --- Fino ---

export interface FinoMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface AuthUser {
  id: string
  email: string
  name: string
  picture_url: string | null
  created_at: string
  onboarding_status: OnboardingStatus
  is_demo: boolean
  test_mode_enabled: boolean
}

// --- Onboarding quiz ---

export interface QuestionOption {
  value: string
  label: string
}

export interface OnboardingQuestion {
  id: string
  prompt: string
  help_text: string | null
  type: 'single_choice' | 'multi_choice' | 'knowledge_check'
  max_selections: number | null
  options: QuestionOption[]
  skippable: boolean
}

export type RiskBand = 'conservative' | 'moderate' | 'aggressive'
export type LiteracyLevel = 'beginner' | 'intermediate' | 'advanced'
export type LifeStage = 'student' | 'early_career' | 'family' | 'pre_retirement'
export type IncomeStability = 'stable' | 'variable' | 'irregular'
export type InvestmentExperience = 'none' | 'some' | 'experienced'

export interface QuizGoal {
  type: string
  target_amount: number | null
  target_date: string | null
  priority: number
}

export interface OnboardingProfile {
  status: OnboardingStatus
  current_step: number
  total_steps: number
  answers: Record<string, string | string[] | null>
  risk_band: RiskBand | null
  literacy_level: LiteracyLevel | null
  life_stage: LifeStage | null
  income_stability: IncomeStability | null
  investment_experience: InvestmentExperience | null
  goals: QuizGoal[]
  completed_at: string | null
}

export interface Category {
  id: string
  name: string
  is_system: boolean
}

export interface Transaction {
  id: string
  date: string
  description: string
  amount_minor: number
  category_id: string | null
  category_name: string | null
  category_confirmed: boolean
  source: string
}

export interface Budget {
  id: string
  category_id: string
  category_name: string | null
  monthly_limit_minor: number
  period: string
}

export interface BudgetAdherence {
  category: string
  limit_minor: number
  spent_minor: number
  pct_used: number
  is_over: boolean
}

export interface Goal {
  id: string
  name: string
  target_amount_minor: number
  target_date: string
  saved_amount_minor: number
  progress_pct: number
  projected_completion_date: string | null
}

export interface CategoryTrend {
  category: string
  latest_month: string
  latest_spend_minor: number
  rolling_avg_minor: number
  pct_change: number | null
  direction: 'rising' | 'falling' | 'stable'
}

export interface TransactionAnomaly {
  date: string
  category: string
  amount_minor: number
  z_score: number
}

export interface CategoryMonthAnomaly {
  month: string
  category: string
  spend_minor: number
  z_score: number
}

export interface SavingsRate {
  month: string
  income_minor: number
  spend_minor: number
  net_minor: number
  savings_rate_pct: number
}

export interface CategoryForecastPiece {
  predicted_minor: number
  low_minor: number
  high_minor: number
  model_used: string
}

export interface Forecast {
  id: string
  generated_at: string
  horizon_month: string
  predicted_total_minor: number
  confidence_low_minor: number
  confidence_high_minor: number
  per_category_breakdown: Record<string, CategoryForecastPiece>
  model_used: string
  is_low_confidence: boolean
  mae: number | null
  mape: number | null
  benchmark_model: string | null
  benchmark_mae: number | null
  benchmark_mape: number | null
}

export interface RecommendationItem {
  title: string
  rationale: string
  projected_impact: string
  category: string
  priority: 'high' | 'medium' | 'low'
}

export interface Recommendations {
  cached: boolean
  summary: string
  insights: string[]
  recommendations: RecommendationItem[]
  risks: string[]
}

// --- Dashboard summary ---

export interface SpendToDate {
  current_month: string
  days_elapsed: number
  spend_to_date_minor: number
  prior_month: string
  prior_spend_to_same_day_minor: number
  pct_change: number | null
}

export interface DailyBurnPoint {
  day: number
  cumulative_spend_minor: number
}

export interface RemainingBudget {
  total_limit_minor: number
  total_spent_minor: number
  remaining_minor: number
  pct_used: number
  is_over: boolean
}

export interface CategorySlice {
  category: string
  spend_minor: number
  pct_of_total: number
}

// --- Forecast horizon ---

export interface ForecastMonthPoint {
  month: string
  predicted_minor: number
  low_minor: number
  high_minor: number
}

export interface CategoryDriver {
  category: string
  current_month_minor: number
  predicted_next_month_minor: number
  delta_minor: number
}

export interface ForecastAccuracy {
  month: string
  predicted_minor: number
  actual_minor: number
  error_minor: number
  error_pct: number | null
}

export interface HorizonForecastResponse {
  months: ForecastMonthPoint[]
  model_used: string
  is_low_confidence: boolean
  history_months: number
  category_drivers: CategoryDriver[]
  accuracy: ForecastAccuracy | null
}

// --- Financial health score ---

export interface HealthPillar {
  key: string
  label: string
  score: number | null
  weight: number
  value_label: string
  note: string
}

export interface HealthLever {
  pillar_key: string
  pillar_label: string
  current_score: number
  estimated_point_gain: number
  note: string
}

export interface HealthTrendPoint {
  month: string
  score: number
}

export interface HealthScoreResponse {
  score: number | null
  band: string | null
  is_provisional: boolean
  pillars: HealthPillar[]
  top_levers: HealthLever[]
  trend: HealthTrendPoint[]
}

// --- AI advisor (/api/advice) ---

export interface AdviceEvidence {
  metric: string
  value: string
  period: string
}

export interface AdviceInsight {
  title: string
  detail: string
  evidence: AdviceEvidence
  severity: 'info' | 'watch' | 'urgent'
}

export type RecommendationStatus = 'pending' | 'dismissed' | 'done'
export type AdviceHorizon = 'this_month' | 'next_3_months' | 'long_term'

export interface AdviceRecommendation {
  id: string
  action: string
  why: string
  impact_inr_per_month: number
  effort: 'low' | 'medium' | 'high'
  category: 'budget' | 'save' | 'invest' | 'debt'
  horizon: AdviceHorizon
  linked_goal: string | null
  goal_impact: string | null
  status: RecommendationStatus
}

export interface AdviceResponse {
  advice_id: string
  generated_at: string
  cached: boolean
  is_fallback: boolean
  headline: string
  health_score: number
  insights: AdviceInsight[]
  recommendations: AdviceRecommendation[]
  questions_to_consider: string[]
}

export interface AdviceHistoryItem {
  advice_id: string
  generated_at: string
  headline: string
  health_score: number
  is_fallback: boolean
}

export interface DashboardSummary {
  as_of: string
  spend_to_date: SpendToDate
  daily_burn: DailyBurnPoint[]
  projected_month_end_spend_minor: number
  remaining_budget: RemainingBudget
  top_categories: CategorySlice[]
}

// --- CSV import ---

export interface ColumnMapping {
  date: string | null
  description: string | null
  amount: string | null
  debit: string | null
  credit: string | null
}

export interface CategoryGuess {
  category: string | null
  confidence: number | null
}

export interface UploadPreviewResponse {
  columns: string[]
  suggested_mapping: ColumnMapping
  sample_rows: Record<string, string>[]
  category_guesses: CategoryGuess[]
  total_rows: number
  upload_token: string
}

export interface UploadCommitResponse {
  inserted: number
  duplicates_skipped: number
  unparseable_skipped: number
}

// --- Market indices ---

export interface IntradayPoint {
  timestamp: number
  value: number
}

export interface IndexData {
  name: string
  symbol: string
  current: number
  change: number
  change_pct: number
  previous_close: number
  points: IntradayPoint[]
  timestamp: number
  is_open: boolean
  is_stale: boolean
}

export interface MarketIndicesResponse {
  indices: IndexData[]
  source: string
  delayed_minutes: number
}

// --- Screenshot transaction extraction ---

export interface ExtractionConfidence {
  amount: number
  merchant: number
  category: number
}

export interface TransactionExtraction {
  is_transaction: boolean
  amount: number | null
  currency: string | null
  direction: 'debit' | 'credit' | null
  merchant: string | null
  datetime: string | null
  reference: string | null
  category: string | null
  confidence: ExtractionConfidence
  unreadable_fields: string[]
  notes: string | null
}

// --- Market education ---

export interface EducationLesson {
  id: string
  title: string
  description: string
  youtube_id: string
  source: string
}

export interface EducationModule {
  id: string
  title: string
  level: string
  description: string
  lessons: EducationLesson[]
}

export interface EducationProgress {
  completed_lesson_ids: string[]
  total_lesson_count: number
}

// --- Mutual funds ---

export interface CuratedSchemeSummary {
  scheme_code: number
  scheme_name: string
  category: string
  category_label: string
  latest_nav: number
  change_pct_30d: number | null
  is_stale: boolean
}

export interface CuratedListResponse {
  schemes: CuratedSchemeSummary[]
  source: string
}

export interface NavPoint {
  date: string
  nav: number
}

export interface SchemeDetail {
  scheme_code: number
  scheme_name: string
  fund_house: string
  scheme_category: string
  latest_nav: number
  latest_date: string
  change_pct_30d: number | null
  history: NavPoint[]
  is_stale: boolean
}

export interface FinoBuddyResponse {
  matched_categories: string[]
  schemes: CuratedSchemeSummary[]
}

// --- Finance news ---

export interface NewsArticle {
  uuid: string
  title: string
  description: string
  url: string
  image_url: string | null
  source: string
  published_at: string
}

export interface NewsResponse {
  articles: NewsArticle[]
  is_available: boolean
  is_stale: boolean
  source: string
}
