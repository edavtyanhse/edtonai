import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Upload as UploadIcon, FileText, Sparkles, ArrowRight, Link2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import {
  api,
  type AnalyzeReq,
  type ParsedResumeStructured,
  type ParsedExperience,
  type ParsedEducation,
  type ParsedContactInfo,
} from "@/lib/api";
import { saveAnalysisSession } from "@/lib/session";

const normaliseContacts = (contacts: ParsedContactInfo | null | undefined): ParsedContactInfo => ({
  full_name: contacts?.full_name ?? "",
  email: contacts?.email ?? "",
  phone: contacts?.phone ?? "",
  location: contacts?.location ?? "",
  links: Array.isArray(contacts?.links)
    ? contacts!.links.filter((link) => link && link.trim().length > 0).map((link) => link.trim())
    : [],
});

const normaliseExperience = (exp: ParsedExperience | undefined): ParsedExperience => ({
  company: exp?.company ?? "",
  role: exp?.role ?? "",
  period: exp?.period ?? "",
  responsibilities: Array.isArray(exp?.responsibilities)
    ? exp!.responsibilities.filter((item) => item && item.trim().length > 0).map((item) => item.trim())
    : [],
  achievements: Array.isArray(exp?.achievements)
    ? exp!.achievements.filter((item) => item && item.trim().length > 0).map((item) => item.trim())
    : [],
});

const normaliseEducation = (edu: ParsedEducation | undefined): ParsedEducation => ({
  institution: edu?.institution ?? "",
  degree: edu?.degree ?? "",
  period: edu?.period ?? "",
  details: Array.isArray(edu?.details)
    ? edu!.details.filter((item) => item && item.trim().length > 0).map((item) => item.trim())
    : [],
});

const normaliseStructured = (
  structured: ParsedResumeStructured | null,
): ParsedResumeStructured | null => {
  if (!structured) {
    return null;
  }

  return {
    contacts: normaliseContacts(structured.contacts),
    experience: Array.isArray(structured.experience)
      ? structured.experience.map((entry) => normaliseExperience(entry))
      : [],
    education: Array.isArray(structured.education)
      ? structured.education.map((entry) => normaliseEducation(entry))
      : [],
    skills: Array.isArray(structured.skills)
      ? structured.skills.filter((skill) => skill && skill.trim().length > 0).map((skill) => skill.trim())
      : [],
  };
};

const composeResumeText = (structured: ParsedResumeStructured | null, fallback: string): string => {
  if (!structured) {
    return fallback;
  }

  const sections: string[] = [];

  if (structured.contacts) {
    const contactLines: string[] = [];
    if (structured.contacts.full_name) contactLines.push(structured.contacts.full_name);
    if (structured.contacts.email) contactLines.push(`Email: ${structured.contacts.email}`);
    if (structured.contacts.phone) contactLines.push(`Телефон: ${structured.contacts.phone}`);
    if (structured.contacts.location) contactLines.push(`Локация: ${structured.contacts.location}`);
    if (structured.contacts.links?.length) {
      contactLines.push(`Ссылки: ${structured.contacts.links.join(", ")}`);
    }
    if (contactLines.length) {
      sections.push(contactLines.join("\n"));
    }
  }

  if (structured.experience.length) {
    const experienceText = structured.experience
      .map((item) => {
        const lines: string[] = [];
        const headerParts = [item.role, item.company, item.period].filter((part) => part && part.trim());
        if (headerParts.length) {
          lines.push(headerParts.join(" — "));
        }
        if (item.responsibilities.length) {
          lines.push("Обязанности:");
          lines.push(...item.responsibilities.map((resp) => `- ${resp}`));
        }
        if (item.achievements.length) {
          lines.push("Достижения:");
          lines.push(...item.achievements.map((ach) => `- ${ach}`));
        }
        return lines.join("\n");
      })
      .filter((block) => block.trim().length > 0)
      .join("\n\n");

    if (experienceText.trim().length > 0) {
      sections.push("Опыт работы:\n" + experienceText);
    }
  }

  if (structured.education.length) {
    const educationText = structured.education
      .map((item) => {
        const lines: string[] = [];
        const headerParts = [item.degree, item.institution, item.period].filter((part) => part && part.trim());
        if (headerParts.length) {
          lines.push(headerParts.join(" — "));
        }
        if (item.details.length) {
          lines.push(...item.details.map((detail) => `- ${detail}`));
        }
        return lines.join("\n");
      })
      .filter((block) => block.trim().length > 0)
      .join("\n\n");

    if (educationText.trim().length > 0) {
      sections.push("Образование:\n" + educationText);
    }
  }

  if (structured.skills.length) {
    sections.push(`Навыки: ${structured.skills.join(", ")}`);
  }

  const result = sections.join("\n\n").trim();
  return result.length > 0 ? result : fallback;
};

const blankExperience = (): ParsedExperience => ({
  company: "",
  role: "",
  period: "",
  responsibilities: [],
  achievements: [],
});

const blankEducation = (): ParsedEducation => ({
  institution: "",
  degree: "",
  period: "",
  details: [],
});

const Upload = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [isParsingFile, setIsParsingFile] = useState(false);
  const [structuredResume, setStructuredResume] = useState<ParsedResumeStructured | null>(null);
  const [ocrError, setOcrError] = useState<string | null>(null);

  const analyzeMutation = useMutation({
    mutationFn: (payload: AnalyzeReq) => api.analyze(payload),
    onSuccess: (data) => {
      saveAnalysisSession({
        analysisId: data.analysis_id,
        resumeId: data.resume_id,
        vacancyId: data.vacancy_id,
        createdAt: data.created_at,
      });
      toast({
        title: "Анализ завершён",
        description: "Мы нашли ключевые совпадения и рекомендации",
      });
      navigate("/analysis");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Не удалось выполнить анализ";
      toast({
        title: "Ошибка анализа",
        description: message,
        variant: "destructive",
      });
    },
  });

  const resumePayload = useMemo(
    () => composeResumeText(structuredResume, resumeText),
    [structuredResume, resumeText],
  );

  const resumeCharacters = useMemo(() => resumePayload.trim().length, [resumePayload]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || !event.target.files[0]) {
      return;
    }

    const file = event.target.files[0];
    setResumeFile(file);

    try {
      setIsParsingFile(true);
      const parsed = await api.parseFile(file);
      setResumeText(parsed.raw_text ?? "");
      const structured = normaliseStructured(parsed.structured);
      setStructuredResume(structured);
      setOcrError(parsed.ocr_error ?? null);

      toast({
        title: "Файл распознан",
        description: structured
          ? "Контакты, опыт и навыки заполнены автоматически"
          : "Текст извлечён, отредактируйте его вручную ниже",
      });
    } catch (error) {
      console.error("Failed to parse resume file", error);
      setStructuredResume(null);
      setOcrError(error instanceof Error ? error.message : "Ошибка распознавания");
      const message =
        error instanceof Error ? error.message : "Вставьте текст резюме вручную ниже";
      toast({
        title: "Не удалось распознать файл",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsParsingFile(false);
    }
  };

  const handleAnalyze = () => {
    if (!resumePayload.trim()) {
      toast({
        title: "Добавьте резюме",
        description: "Вставьте текст или загрузите файл с резюме",
        variant: "destructive",
      });
      return;
    }
    if (!jobDescription.trim()) {
      toast({
        title: "Добавьте вакансию",
        description: "Необходимо вставить текст вакансии",
        variant: "destructive",
      });
      return;
    }

    const payload: AnalyzeReq = {
      resume_text: resumePayload,
      vacancy_text: jobDescription,
      role: targetRole || undefined,
    };

    analyzeMutation.mutate(payload);
  };

  const handleContactsChange = (field: keyof ParsedContactInfo, value: string) => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const contacts = normaliseContacts(prev.contacts);
      return {
        ...prev,
        contacts: {
          ...contacts,
          [field]: value,
        },
      };
    });
  };

  const handleLinksChange = (value: string) => {
    const links = value
      .split("\n")
      .map((link) => link.trim())
      .filter((link) => link.length > 0);
    setStructuredResume((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        contacts: {
          ...normaliseContacts(prev.contacts),
          links,
        },
      };
    });
  };

  const handleExperienceChange = (
    index: number,
    field: keyof ParsedExperience,
    value: string,
  ) => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const nextExperience = prev.experience.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: value,
            }
          : item,
      );
      return { ...prev, experience: nextExperience };
    });
  };

  const handleExperienceListChange = (
    index: number,
    field: "responsibilities" | "achievements",
    value: string,
  ) => {
    const items = value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const nextExperience = prev.experience.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: items,
            }
          : item,
      );
      return { ...prev, experience: nextExperience };
    });
  };

  const handleEducationChange = (
    index: number,
    field: keyof ParsedEducation,
    value: string,
  ) => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const nextEducation = prev.education.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              [field]: value,
            }
          : item,
      );
      return { ...prev, education: nextEducation };
    });
  };

  const handleEducationDetailsChange = (index: number, value: string) => {
    const details = value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const nextEducation = prev.education.map((item, itemIndex) =>
        itemIndex === index
          ? {
              ...item,
              details,
            }
          : item,
      );
      return { ...prev, education: nextEducation };
    });
  };

  const handleSkillsChange = (value: string) => {
    const skills = value
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill.length > 0);
    setStructuredResume((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        skills,
      };
    });
  };

  const addExperience = () => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      return { ...prev, experience: [...prev.experience, blankExperience()] };
    });
  };

  const addEducation = () => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      return { ...prev, education: [...prev.education, blankEducation()] };
    });
  };

  const switchToTextMode = () => {
    setStructuredResume((prev) => {
      if (!prev) return prev;
      const composed = composeResumeText(prev, resumeText);
      setResumeText(composed);
      return null;
    });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}
            <div className="w-8 h-8 rounded-lg gradient-hero flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">EdTon.ai</span>
          </div>
          <Button variant="outline" onClick={() => navigate('/history')}>
            История
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        {/* Progress Steps */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                1
              </div>
              <span className="text-sm font-medium">Загрузка</span>
            </div>
            <div className="flex-1 h-0.5 bg-border mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground font-semibold">
                2
              </div>
              <span className="text-sm text-muted-foreground">Анализ</span>
            </div>
            <div className="flex-1 h-0.5 bg-border mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground font-semibold">
                3
              </div>
              <span className="text-sm text-muted-foreground">Генерация</span>
            </div>
          </div>
        </div>

        {/* Upload Section */}
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2 animate-fade-in">
            <h1 className="text-3xl md:text-4xl font-bold">Загрузите данные для анализа</h1>
            <p className="text-muted-foreground text-lg">
              Загрузите своё резюме и добавьте текст вакансии
            </p>
          </div>

          {/* Resume Upload */}
          <Card className="p-8 shadow-soft animate-slide-up">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold">Загрузите своё резюме</h2>
              </div>
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer">
                <input
                  type="file"
                  id="resume-upload"
                  className="hidden"
                  accept=".pdf,.docx,.doc,.txt"
                  aria-label="Загрузить резюме"
                  onChange={handleFileChange}
                />
                <label htmlFor="resume-upload" className="cursor-pointer space-y-4 block">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                    <UploadIcon className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-lg font-medium">
                      {resumeFile ? resumeFile.name : "Нажмите для загрузки"}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Поддерживаются форматы: PDF, DOCX (до 10MB)
                    </p>
                  </div>
                </label>
              </div>
              {resumeFile && (
                <div className="flex items-center gap-2 p-3 bg-success/10 rounded-lg animate-fade-in">
                  <FileText className="w-5 h-5 text-success" />
                  <span className="text-sm font-medium truncate">{resumeFile.name}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Job Description */}
          <Card className="p-8 shadow-soft animate-slide-up">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Link2 className="w-5 h-5 text-primary" />
                <h2 className="text-xl font-semibold">Добавьте вакансию</h2>
              </div>
              <div className="space-y-2">
                <Textarea
                  placeholder="Вставьте текст вакансии или ссылку на HH.ru..."
                  className="min-h-[200px] resize-none"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                />
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  <Sparkles className="w-4 h-4" />
                  Можно просто вставить ссылку на HH или текст вакансии
                </p>
              </div>
            </div>
          </Card>

          {/* Resume Text */}
          {structuredResume ? (
            <Card className="p-8 shadow-soft animate-slide-up">
              <div className="space-y-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" />
                    <div>
                      <h2 className="text-xl font-semibold">Проверьте распознанные данные</h2>
                      <p className="text-sm text-muted-foreground">
                        Структурированная информация из файла — отредактируйте при необходимости
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className="text-xs text-muted-foreground">Символов: {resumeCharacters}</p>
                    <Button variant="outline" size="sm" onClick={switchToTextMode}>
                      Редактировать как текст
                    </Button>
                  </div>
                </div>

                {ocrError && (
                  <Alert variant="destructive">
                    <AlertTitle>Не удалось извлечь структуру полностью</AlertTitle>
                    <AlertDescription>{ocrError}</AlertDescription>
                  </Alert>
                )}

                <section className="space-y-4">
                  <h3 className="text-lg font-semibold">Контакты</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="contact-fullname">ФИО</Label>
                      <Input
                        id="contact-fullname"
                        value={structuredResume.contacts?.full_name ?? ""}
                        onChange={(e) => handleContactsChange("full_name", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="contact-email">Email</Label>
                      <Input
                        id="contact-email"
                        value={structuredResume.contacts?.email ?? ""}
                        onChange={(e) => handleContactsChange("email", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="contact-phone">Телефон</Label>
                      <Input
                        id="contact-phone"
                        value={structuredResume.contacts?.phone ?? ""}
                        onChange={(e) => handleContactsChange("phone", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="contact-location">Локация</Label>
                      <Input
                        id="contact-location"
                        value={structuredResume.contacts?.location ?? ""}
                        onChange={(e) => handleContactsChange("location", e.target.value)}
                      />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="contact-links">Ссылки (по одной в строке)</Label>
                      <Textarea
                        id="contact-links"
                        className="min-h-[100px]"
                        value={(structuredResume.contacts?.links ?? []).join("\n")}
                        onChange={(e) => handleLinksChange(e.target.value)}
                      />
                    </div>
                  </div>
                </section>

                <section className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Опыт работы</h3>
                    <Button variant="outline" size="sm" onClick={addExperience}>
                      Добавить позицию
                    </Button>
                  </div>
                  {structuredResume.experience.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Не найдено опыта — добавьте позиции вручную
                    </p>
                  ) : (
                    <div className="space-y-6">
                      {structuredResume.experience.map((exp, index) => (
                        <Card key={`experience-${index}`} className="p-4 border-dashed">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <Label htmlFor={`exp-role-${index}`}>Должность</Label>
                              <Input
                                id={`exp-role-${index}`}
                                value={exp.role ?? ""}
                                onChange={(e) => handleExperienceChange(index, "role", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`exp-company-${index}`}>Компания</Label>
                              <Input
                                id={`exp-company-${index}`}
                                value={exp.company ?? ""}
                                onChange={(e) => handleExperienceChange(index, "company", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`exp-period-${index}`}>Период</Label>
                              <Input
                                id={`exp-period-${index}`}
                                value={exp.period ?? ""}
                                onChange={(e) => handleExperienceChange(index, "period", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2 md:col-span-3">
                              <Label htmlFor={`exp-resp-${index}`}>Обязанности (по строке)</Label>
                              <Textarea
                                id={`exp-resp-${index}`}
                                className="min-h-[120px]"
                                value={(exp.responsibilities ?? []).join("\n")}
                                onChange={(e) => handleExperienceListChange(index, "responsibilities", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2 md:col-span-3">
                              <Label htmlFor={`exp-ach-${index}`}>Достижения (по строке)</Label>
                              <Textarea
                                id={`exp-ach-${index}`}
                                className="min-h-[120px]"
                                value={(exp.achievements ?? []).join("\n")}
                                onChange={(e) => handleExperienceListChange(index, "achievements", e.target.value)}
                              />
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}
                </section>

                <section className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Образование</h3>
                    <Button variant="outline" size="sm" onClick={addEducation}>
                      Добавить образование
                    </Button>
                  </div>
                  {structuredResume.education.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      Не найдено записей об образовании — добавьте вручную
                    </p>
                  ) : (
                    <div className="space-y-6">
                      {structuredResume.education.map((edu, index) => (
                        <Card key={`education-${index}`} className="p-4 border-dashed">
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-2">
                              <Label htmlFor={`edu-degree-${index}`}>Степень / специальность</Label>
                              <Input
                                id={`edu-degree-${index}`}
                                value={edu.degree ?? ""}
                                onChange={(e) => handleEducationChange(index, "degree", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`edu-inst-${index}`}>Учреждение</Label>
                              <Input
                                id={`edu-inst-${index}`}
                                value={edu.institution ?? ""}
                                onChange={(e) => handleEducationChange(index, "institution", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`edu-period-${index}`}>Период</Label>
                              <Input
                                id={`edu-period-${index}`}
                                value={edu.period ?? ""}
                                onChange={(e) => handleEducationChange(index, "period", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2 md:col-span-3">
                              <Label htmlFor={`edu-details-${index}`}>Детали / курсы (по строке)</Label>
                              <Textarea
                                id={`edu-details-${index}`}
                                className="min-h-[100px]"
                                value={(edu.details ?? []).join("\n")}
                                onChange={(e) => handleEducationDetailsChange(index, e.target.value)}
                              />
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}
                </section>

                <section className="space-y-4">
                  <h3 className="text-lg font-semibold">Навыки</h3>
                  <div className="space-y-2">
                    <Label htmlFor="skills-input">Перечислите навыки через запятую</Label>
                    <Input
                      id="skills-input"
                      value={structuredResume.skills.join(", ")}
                      onChange={(e) => handleSkillsChange(e.target.value)}
                    />
                  </div>
                </section>

                <div className="space-y-2">
                  <Label htmlFor="target-role">Целевая роль (необязательно)</Label>
                  <Input
                    id="target-role"
                    placeholder="Например, Product Manager"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                  />
                </div>
              </div>
            </Card>
          ) : (
            <Card className="p-8 shadow-soft animate-slide-up">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <h2 className="text-xl font-semibold">Проверьте текст резюме</h2>
                </div>
                {ocrError && (
                  <Alert variant="destructive">
                    <AlertTitle>Не удалось распознать структуру</AlertTitle>
                    <AlertDescription>{ocrError}</AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Label htmlFor="resume-text">Текст резюме</Label>
                  <Textarea
                    id="resume-text"
                    placeholder="Вставьте сюда текст резюме или загрузите файл"
                    className="min-h-[220px] resize-y"
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">Символов: {resumeCharacters}</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="target-role">Целевая роль (необязательно)</Label>
                  <Input
                    id="target-role"
                    placeholder="Например, Product Manager"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                  />
                </div>
              </div>
            </Card>
          )}

          {/* Action Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              className="gradient-hero text-lg shadow-card min-w-[250px]"
              onClick={handleAnalyze}
              disabled={analyzeMutation.isPending || isParsingFile}
            >
              {analyzeMutation.isPending || isParsingFile ? (
                <>
                  <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                  {isParsingFile ? "Обрабатываю файл..." : "Анализирую..."}
                </>
              ) : (
                <>
                  Анализировать соответствие
                  <ArrowRight className="ml-2 h-5 w-5" />
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
