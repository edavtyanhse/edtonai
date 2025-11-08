import { describe, expect, it, beforeEach, vi } from "vitest";
import { screen } from "@testing-library/react";

import Results from "@/pages/Results";
import { api } from "@/lib/api";
import { GENERATION_STORAGE_KEY } from "@/lib/session";
import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api", () => ({
  api: {
    getAnalysis: vi.fn(),
    getDocument: vi.fn(),
    listAnalyses: vi.fn(),
    listGenerations: vi.fn(),
    analyze: vi.fn(),
    generate: vi.fn(),
    parseFile: vi.fn(),
  },
}));

describe("Results page", () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem(
      GENERATION_STORAGE_KEY,
      JSON.stringify({
        analysisId: "analysis-1",
        resumeDocumentId: "doc-resume",
        coverLetterDocumentId: "doc-cover",
        atsScore: 90,
      }),
    );

    vi.mocked(api.getDocument).mockImplementation(async (id: string) => {
      if (id === "doc-resume") {
        return {
          id,
          analysis_id: "analysis-1",
          kind: "resume",
          content: "Improved resume body",
          ats_score: 91,
          created_at: new Date().toISOString(),
        };
      }
      return {
        id,
        analysis_id: "analysis-1",
        kind: "cover_letter",
        content: "Cover letter body",
        ats_score: 91,
        created_at: new Date().toISOString(),
      };
    });

    vi.mocked(api.getAnalysis).mockResolvedValue({
      analysis: {
        id: "analysis-1",
        resume_id: "resume-1",
        vacancy_id: "vacancy-1",
        role: "Backend Engineer",
        match_score: 80,
        matched_skills: [],
        missing_skills: [],
        tips: "",
        created_at: new Date().toISOString(),
      },
      resume: {
        id: "resume-1",
        title: null,
        content: "",
        skills: [],
        created_at: new Date().toISOString(),
      },
      vacancy: {
        id: "vacancy-1",
        title: null,
        description: "",
        keywords: [],
        created_at: new Date().toISOString(),
      },
      documents: [],
    });
  });

  it("fetches documents on load and shows the saved contents", async () => {
    renderWithProviders(<Results />, { route: "/results" });

    await screen.findByDisplayValue(/Improved resume body/);
    expect(api.getDocument).toHaveBeenCalledWith("doc-resume");
    expect(api.getDocument).toHaveBeenCalledWith("doc-cover");
    expect(screen.getByText(/Backend Engineer/)).toBeInTheDocument();
  });
});
