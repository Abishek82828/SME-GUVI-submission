export interface ForecastItem {
  month: string;
  forecast_revenue: number;
  forecast_expense: number;
  forecast_operating_profit: number;
}

export interface Recommendation {
  title: string;
  why: string;
  actions: string[];
  impact_estimate: string;
}

export interface Risk {
  severity: string;
  type: string;
  signal: string;
  why: string;
}

export interface AssessmentResult {
  scores: {
    health_score: number;
    risk_score: number;
    credit_readiness_score: number;
    rating: string;
  };
  kpis: {
    total_revenue: number;
    total_expense: number;
    operating_margin: number;
    dso_days: number;
    dpo_days: number;
    emi_to_monthly_revenue: number;
    runway_months_proxy: number;
  };
  risks: Risk[];
  recommendations: Recommendation[];
  benchmarks: {
    available: boolean;
    industry?: string;
    benchmarks?: Record<string, any>;
    your?: Record<string, any>;
    gaps?: Record<string, any>;
  };
  forecast: {
    horizon_months: number;
    method: string;
    forecast: ForecastItem[];
  };
  breakdowns?: any;
}

export interface AssessmentResponse {
  id: string;
  company: string;
  industry: string;
  lang: string;
  created_at: string;
  result_json: AssessmentResult;
}

export interface HistoryItem {
  id: string;
  company: string;
  industry: string;
  created_at: string;
}
