import { getUserId } from "./auth";

const API_URL = import.meta.env.VITE_API_URL as string;

export type AnalyzeReq = {
  resume_text: string;
  vacancy_text: string;
  role?: string;
};

export type AnalyzeRes = {
  analysis_id: string;
  resume_id: string;
  vacancy_id: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  tips: string;
  role?: string | null;
  created_at: string;
};

export type GenerateReq = {
  analysis_id?: string;
  resume_text?: string;
  vacancy_text?: string;
  target_role?: string;
};

export type GenerateRes = {
  analysis_id: string;
  resume_id: string;
  vacancy_id: string;
  resume_document_id: string;
  cover_letter_document_id: string;
  improved_resume: string;
  cover_letter: string;
  ats_score: number;
};

export type ResumeRecord = {
  id: string;
  title: string | null;
  content: string;
  skills: string[];
  created_at: string;
};

export type VacancyRecord = {
  id: string;
  title: string | null;
  description: string;
  keywords: string[];
  created_at: string;
};

export type DocumentRecord = {
  id: string;
  analysis_id: string;
  kind: "resume" | "cover_letter";
  content: string;
  ats_score: number | null;
  created_at: string;
};

export type AnalysisRecord = {
  id: string;
  resume_id: string;
  vacancy_id: string;
  role: string | null;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  tips: string | null;
  created_at: string;
};

export type AnalysisDetail = {
  analysis: AnalysisRecord;
  resume: ResumeRecord;
  vacancy: VacancyRecord;
  documents: DocumentRecord[];
};

export type AnalysisSummary = {
  id: string;
  resume_id: string;
  vacancy_id: string;
  role: string | null;
  match_score: number;
  created_at: string;
  resume_title: string | null;
  vacancy_title: string | null;
};

export type GenerationSummary = {
  analysis_id: string;
  resume_document_id: string | null;
  cover_letter_document_id: string | null;
  ats_score: number | null;
  created_at: string;
};

export type ParsedContactInfo = {
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  links: string[];
};

export type ParsedExperience = {
  company?: string | null;
  role?: string | null;
  period?: string | null;
  responsibilities: string[];
  achievements: string[];
};

export type ParsedEducation = {
  institution?: string | null;
  degree?: string | null;
  period?: string | null;
  details: string[];
};

export type ParsedResumeStructured = {
  contacts: ParsedContactInfo | null;
  experience: ParsedExperience[];
  education: ParsedEducation[];
  skills: string[];
};

export type ParsedResumeResponse = {
  raw_text: string;
  structured: ParsedResumeStructured | null;
  ocr_error: string | null;
};

async function request<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": getUserId(),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText} ${text}`.trim());
  }

  return response.json() as Promise<T>;
}

async function getRequest<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "GET",
    headers: {
      "X-User-Id": getUserId(),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText} ${text}`.trim());
  }

  return response.json() as Promise<T>;
}

export const api = {
  analyze: (payload: AnalyzeReq) => request<AnalyzeRes>("/api/analyze", payload),
  generate: (payload: GenerateReq) => request<GenerateRes>("/api/generate", payload),
  getAnalysis: (analysisId: string) =>
    getRequest<AnalysisDetail>(`/api/analyses/${analysisId}`),
  listAnalyses: () => getRequest<AnalysisSummary[]>("/api/analyses"),
  getDocument: (documentId: string) =>
    getRequest<DocumentRecord>(`/api/documents/${documentId}`),
  listGenerations: () => getRequest<GenerationSummary[]>("/api/generations"),
  parseFile: async (file: File): Promise<ParsedResumeResponse> => {
    const fd = new FormData();
    fd.append("file", file);

    const response = await fetch(`${API_URL}/api/parse`, {
      method: "POST",
      headers: {
        "X-User-Id": getUserId(),
      },
      body: fd,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status} ${response.statusText} ${text}`.trim());
    }

    return response.json();
  },
};
