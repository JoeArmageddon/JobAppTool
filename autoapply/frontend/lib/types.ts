// Mirrors backend Pydantic schemas

export interface ResumeSuggestion {
  category: string;
  issue: string;
  fix: string;
}

export interface Resume {
  id: string;
  user_id: string;
  raw_text?: string;
  structured_json?: Record<string, unknown>;
  ats_score?: number;
  impact_score?: number;
  completeness_score?: number;
  overall_score?: number;
  suggestions_json?: ResumeSuggestion[];
  file_url?: string;
  original_filename?: string;
  created_at: string;
  updated_at: string;
}

export interface HuntProfile {
  id: string;
  user_id: string;
  target_titles: string[];
  industries: string[];
  locations: string[];
  remote_preference: "remote" | "hybrid" | "onsite";
  seniority_level?: string;
  salary_floor?: number;
  company_size_pref?: string;
  blacklisted_companies: string[];
  job_sources: string[];
  is_active: boolean;
  daily_apply_limit: number;
  auto_apply: boolean;
  created_at: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location?: string;
  description_raw?: string;
  description_parsed_json?: Record<string, unknown>;
  source?: string;
  source_url?: string;
  salary_min?: number;
  salary_max?: number;
  posted_at?: string;
  scraped_at: string;
  match_score?: number;
  match_reasons_json?: Record<string, unknown>;
  status: string;
}

export interface Application {
  id: string;
  user_id: string;
  job_id: string;
  resume_id?: string;
  tailored_resume_text?: string;
  tailored_resume_pdf_url?: string;
  cover_letter_text?: string;
  status: ApplicationStatus;
  applied_at?: string;
  response_at?: string;
  notes?: string;
  screenshot_url?: string;
  created_at: string;
  job?: Job;
}

export type ApplicationStatus =
  | "queued"
  | "applying"
  | "applied"
  | "viewed"
  | "interview"
  | "rejected"
  | "offer";

export interface ApiError {
  error: string;
  code: string;
}
