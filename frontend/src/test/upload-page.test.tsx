import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Upload from "@/pages/Upload";
import { api } from "@/lib/api";
import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api", () => ({
  api: {
    analyze: vi.fn(),
    parseFile: vi.fn(),
    generate: vi.fn(),
    getAnalysis: vi.fn(),
    listAnalyses: vi.fn(),
    getDocument: vi.fn(),
    listGenerations: vi.fn(),
  },
}));

describe("Upload page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders structured resume sections when OCR data is returned", async () => {
    vi.mocked(api.parseFile).mockResolvedValue({
      raw_text: "John Doe\nEngineer",
      structured: {
        contacts: {
          full_name: "John Doe",
          email: "john@example.com",
          phone: "+1 555-0100",
          location: "Remote",
          links: ["https://example.com"],
        },
        experience: [
          {
            company: "Acme",
            role: "Engineer",
            period: "2020-2022",
            responsibilities: ["Built APIs"],
            achievements: ["Reduced latency"],
          },
        ],
        education: [
          {
            institution: "MIT",
            degree: "BSc",
            period: "2014-2018",
            details: ["Honors"],
          },
        ],
        skills: ["Python", "FastAPI"],
      },
      ocr_error: null,
    });

    renderWithProviders(<Upload />);

    const input = screen.getByLabelText("Загрузить резюме");
    const file = new File(["resume"], "resume.pdf", { type: "application/pdf" });
    await fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(api.parseFile).toHaveBeenCalled();
    });

    expect(screen.getByText("Контакты")).toBeInTheDocument();
    expect(screen.getByLabelText("ФИО")).toHaveValue("John Doe");
    expect(screen.getByText("Опыт работы")).toBeInTheDocument();
    expect(screen.getByLabelText("Степень / специальность")).toHaveValue("BSc");
    expect(screen.getByLabelText("Перечислите навыки через запятую")).toHaveValue("Python, FastAPI");
  });
});
