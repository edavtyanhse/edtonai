import { describe, expect, it, beforeEach, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Analysis from "@/pages/Analysis";
import { api } from "@/lib/api";
import { ANALYSIS_STORAGE_KEY, GENERATION_STORAGE_KEY } from "@/lib/session";
import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api", () => ({
  api: {
    getAnalysis: vi.fn(),
    generate: vi.fn(),
    listAnalyses: vi.fn(),
    listGenerations: vi.fn(),
    getDocument: vi.fn(),
    analyze: vi.fn(),
    parseFile: vi.fn(),
  },
}));

describe("Analysis page", () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem(
      ANALYSIS_STORAGE_KEY,
      JSON.stringify({
        analysisId: "analysis-1",
        resumeId: "resume-1",
        vacancyId: "vacancy-1",
        createdAt: new Date().toISOString(),
      }),
    );
    sessionStorage.setItem(GENERATION_STORAGE_KEY, JSON.stringify({ foo: "bar" }));

    vi.mocked(api.getAnalysis).mockResolvedValue({
      analysis: {
        id: "analysis-1",
        resume_id: "resume-1",
        vacancy_id: "vacancy-1",
        role: "Python Developer",
        match_score: 78.4,
        matched_skills: ["Python"],
        missing_skills: ["FastAPI"],
        tips: "# Совпадающие навыки\n- Python",
        created_at: new Date().toISOString(),
      },
      resume: {
        id: "resume-1",
        title: "Senior Engineer",
        content: "Experienced engineer",
        skills: ["Python"],
        created_at: new Date().toISOString(),
      },
      vacancy: {
        id: "vacancy-1",
        title: "Backend role",
        description: "Need backend",
        keywords: ["FastAPI"],
        created_at: new Date().toISOString(),
      },
      documents: [],
    });
    vi.mocked(api.generate).mockResolvedValue({
      analysis_id: "analysis-1",
      resume_id: "resume-1",
      vacancy_id: "vacancy-1",
      resume_document_id: "doc-resume",
      cover_letter_document_id: "doc-cover",
      improved_resume: "Improved",
      cover_letter: "Letter",
      ats_score: 82,
    });
  });

  it("loads analysis details from the API using the saved session", async () => {
    renderWithProviders(<Analysis />, { route: "/analysis" });

    await screen.findByText(/Python Developer/);
    expect(api.getAnalysis).toHaveBeenCalledWith("analysis-1");

    await waitFor(() => {
      expect(sessionStorage.getItem(GENERATION_STORAGE_KEY)).toBeNull();
    });

    expect(screen.getByText(/Совпадающие навыки/)).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
  });
});
