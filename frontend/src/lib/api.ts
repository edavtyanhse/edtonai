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

export type ParsedResume = {
  raw_text: string;
  summary?: string | null;
  contact: {
    full_name?: string | null;
    title?: string | null;
    email?: string | null;
    phone?: string | null;
    location?: string | null;
    links: string[];
  };
  experiences: {
    company?: string | null;
    position?: string | null;
    period?: string | null;
    responsibilities: string[];
    achievements: string[];
  }[];
  education: {
    institution?: string | null;
    degree?: string | null;
    period?: string | null;
    details: string[];
  }[];
  skills: string[];
  languages: string[];
  warnings: string[];
};

const defaultParsedResume: ParsedResume = {
  raw_text: "",
  summary: null,
  contact: {
    full_name: null,
    title: null,
    email: null,
    phone: null,
    location: null,
    links: [],
  },
  experiences: [],
  education: [],
  skills: [],
  languages: [],
  warnings: [],
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

    const json = (await response.json()) as Partial<ParsedResume> | null;
    return {
      ...defaultParsedResume,
      ...(json ?? {}),
      contact: {
        ...defaultParsedResume.contact,
        ...(json?.contact ?? {}),
        links: json?.contact?.links ?? [],
      },
      experiences: json?.experiences ?? [],
      education: json?.education ?? [],
      skills: json?.skills ?? [],
      languages: json?.languages ?? [],
      warnings: json?.warnings ?? [],
    } satisfies ParsedResume;
  },
};
