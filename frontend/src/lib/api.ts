const API_URL = import.meta.env.VITE_API_URL as string;

export type AnalyzeReq = {
  resume_text: string;
  vacancy_text: string;
  role?: string;
};

export type AnalyzeRes = {
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  tips: string;
};

export type GenerateReq = {
  resume_text: string;
  vacancy_text: string;
  target_role?: string;
};

export type GenerateRes = {
  improved_resume: string;
  cover_letter: string;
  ats_score: number;
};

async function request<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
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
  parseFile: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);

    const response = await fetch(`${API_URL}/api/parse`, {
      method: "POST",
      body: fd,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`${response.status} ${response.statusText} ${text}`.trim());
    }

    return response.text();
  },
};
