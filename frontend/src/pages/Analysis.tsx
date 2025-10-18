import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, CheckCircle2, AlertCircle, Lightbulb, ArrowRight } from "lucide-react";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  clearGenerationSession,
  loadAnalysisSession,
  saveGenerationSession,
  type AnalysisSession,
} from "@/lib/session";

type ParsedTips = {
  matchScore?: number;
  matchSummary?: string;
  matchedSkills: string[];
  missingSkills: string[];
  recommendations: { title: string; details?: string }[];
};

const parseAnalysisMarkdown = (tips: string): ParsedTips => {
  const result: ParsedTips = {
    matchedSkills: [],
    missingSkills: [],
    recommendations: [],
  };

  if (!tips || tips.trim().toLowerCase().startsWith("ai error")) {
    return result;
  }

  const matches = [...tips.matchAll(/^#\s+(.+)$/gm)];
  if (matches.length === 0) {
    return result;
  }

  const getSectionBody = (startIndex: number, nextIndex?: number) => {
    const bodyStart = matches[startIndex].index! + matches[startIndex][0].length;
    const bodyEnd = nextIndex !== undefined ? matches[nextIndex].index! : tips.length;
    return tips.slice(bodyStart, bodyEnd).trim();
  };

  matches.forEach((match, index) => {
    const heading = match[1].trim().toLowerCase();
    const body = getSectionBody(index, index + 1 < matches.length ? index + 1 : undefined);

    if (!body) {
      return;
    }

    if (heading.startsWith("матч")) {
      const lines = body.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      if (lines.length > 0) {
        const scoreMatch = lines[0].match(/(\d+(?:[\.,]\d+)?)\s*%/);
        if (scoreMatch) {
          result.matchScore = Number(scoreMatch[1].replace(",", "."));
        }
        result.matchSummary = lines[0].replace(/^(\d+(?:[\.,]\d+)?)\s*%\s*[—\-–]\s*/u, "").trim();
      }
    } else if (heading.includes("совпадающ")) {
      const skills = body
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => /^[-*]/.test(line))
        .map((line) => line.replace(/^[-*]\s*/, "").trim())
        .filter(Boolean);
      result.matchedSkills = skills;
    } else if (heading.includes("недостающ")) {
      const skills = body
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => /^[-*]/.test(line))
        .map((line) => line.replace(/^[-*]\s*/, "").trim())
        .filter(Boolean);
      result.missingSkills = skills;
    } else if (heading.includes("рекомендац")) {
      const lines = body.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      let current: { title: string; details?: string } | null = null;

      lines.forEach((line) => {
        if (/^[-*]\s*/.test(line)) {
          const content = line.replace(/^[-*]\s*/, "").trim();
          if (/^детали[:：]/i.test(content)) {
            if (current) {
              current.details = content.replace(/^детали[:：]\s*/i, "").trim();
            }
          } else {
            current = { title: content };
            result.recommendations.push(current);
          }
        }
      });
    }
  });

  return result;
};

const Analysis = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [analysis, setAnalysis] = useState<AnalysisSession | null>(null);

  useEffect(() => {
    const session = loadAnalysisSession();
    if (!session) {
      toast({
        title: "Нет данных для анализа",
        description: "Загрузите резюме и вакансию заново",
        variant: "destructive",
      });
      navigate("/upload", { replace: true });
      return;
    }
    clearGenerationSession();
    setAnalysis(session);
  }, [navigate, toast]);

  const parsedTips = useMemo(
    () => parseAnalysisMarkdown(analysis?.response.tips ?? ""),
    [analysis?.response.tips],
  );
  const aiTipsError = (analysis?.response.tips ?? "").trim().toLowerCase().startsWith("ai error");
  const rawMatchScore = parsedTips.matchScore ?? analysis?.response.match_score ?? 0;
  const matchPercentage = Math.round(rawMatchScore);
  const matchSummary = parsedTips.matchSummary;

  const matchingSkills = useMemo(() => {
    const skills = new Set<string>();
    (analysis?.response.matched_skills ?? []).forEach((skill) => skills.add(skill));
    parsedTips.matchedSkills.forEach((skill) => skills.add(skill));
    return Array.from(skills).sort((a, b) => a.localeCompare(b, "ru"));
  }, [analysis?.response.matched_skills, parsedTips]);

  const missingSkills = useMemo(() => {
    const skills = new Set<string>();
    (analysis?.response.missing_skills ?? []).forEach((skill) => skills.add(skill));
    parsedTips.missingSkills.forEach((skill) => skills.add(skill));
    return Array.from(skills).sort((a, b) => a.localeCompare(b, "ru"));
  }, [analysis?.response.missing_skills, parsedTips]);

  const totalSkills = matchingSkills.length + missingSkills.length;
  const skillCoverage = totalSkills
    ? Math.round((100 * matchingSkills.length) / totalSkills)
    : Math.round(matchPercentage);
  const readinessScore = Math.round((rawMatchScore + skillCoverage) / 2);
  const recommendations = parsedTips.recommendations;

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!analysis) {
        throw new Error("Нет данных для генерации");
      }

      return api.generate({
        resume_text: analysis.request.resume_text,
        vacancy_text: analysis.request.vacancy_text,
        target_role: analysis.request.role,
      });
    },
    onSuccess: (data) => {
      if (!analysis) {
        return;
      }
      saveGenerationSession({
        request: {
          resume_text: analysis.request.resume_text,
          vacancy_text: analysis.request.vacancy_text,
          target_role: analysis.request.role,
        },
        response: data,
      });
      toast({
        title: "Генерация завершена",
        description: "Резюме и сопроводительное письмо готовы",
      });
      navigate("/results");
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Не удалось создать документы";
      toast({
        title: "Ошибка генерации",
        description: message,
        variant: "destructive",
      });
    },
  });

  if (!analysis) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <Sparkles className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Подготавливаем данные для анализа...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-8 h-8 rounded-lg gradient-hero flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">EdTon.ai</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        {/* Progress Steps */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex items-center justify-between">
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-success flex items-center justify-center text-success-foreground">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Загрузка</span>
            </div>
            <div className="flex-1 h-0.5 bg-primary mx-4" />
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                2
              </div>
              <span className="text-sm font-medium">Анализ</span>
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

        {/* Analysis Results */}
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="text-center space-y-2 animate-fade-in">
            <h1 className="text-3xl md:text-4xl font-bold">Результат анализа</h1>
            <p className="text-muted-foreground text-lg">
              Ваше резюме проанализировано для выбранной вакансии
            </p>
          </div>

          {aiTipsError && (
            <Alert variant="destructive" className="animate-fade-in">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Не удалось получить советы от модели</AlertTitle>
              <AlertDescription>{analysis?.response.tips}</AlertDescription>
            </Alert>
          )}

          {/* Match Score */}
          <Card className="p-8 shadow-card animate-slide-up">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <div className="relative w-40 h-40">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="hsl(var(--secondary))"
                    strokeWidth="12"
                  />
                  <circle
                    cx="80"
                    cy="80"
                    r="70"
                    fill="none"
                    stroke="hsl(var(--primary))"
                    strokeWidth="12"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - matchPercentage / 100)}`}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-4xl font-bold text-primary">{matchPercentage}%</span>
                  <span className="text-sm text-muted-foreground">совпадение</span>
                </div>
              </div>
              <div className="flex-1 space-y-4">
                <h2 className="text-2xl font-semibold">
                  {matchPercentage >= 70 ? "Хорошее соответствие!" : "Есть, что улучшить"}
                </h2>
                <p className="text-muted-foreground">
                  Мы сопоставили навыки из резюме с требованиями вакансии и подготовили рекомендации для повышения релевантности.
                </p>
                {matchSummary && (
                  <p className="text-sm text-muted-foreground border-l-2 border-primary/40 pl-3">
                    {matchSummary}
                  </p>
                )}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Ключевые навыки</span>
                    <span className="font-medium">{skillCoverage}%</span>
                  </div>
                  <Progress value={skillCoverage} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Готовность профиля</span>
                    <span className="font-medium">{readinessScore}%</span>
                  </div>
                  <Progress value={readinessScore} className="h-2" />
                </div>
              </div>
            </div>
          </Card>

          {/* Details Tabs */}
          <Card className="shadow-soft animate-slide-up">
            <Tabs defaultValue="matching" className="w-full">
              <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0">
                <TabsTrigger
                  value="matching"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Совпадающие навыки
                </TabsTrigger>
                <TabsTrigger
                  value="missing"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Недостающие навыки
                </TabsTrigger>
                <TabsTrigger
                  value="recommendations"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Рекомендации AI
                </TabsTrigger>
              </TabsList>

              <TabsContent value="matching" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Эти навыки из вашего резюме соответствуют требованиям вакансии
                </p>
                {matchingSkills.length === 0 ? (
                  <div className="p-4 rounded-lg bg-muted/40 text-sm text-muted-foreground">
                    Мы не нашли совпадающих навыков. Попробуйте дополнить резюме ключевыми словами из вакансии.
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {matchingSkills.map((skill) => (
                      <Badge
                        key={skill}
                        variant="secondary"
                        className="border border-success/30 bg-success/10 text-success-foreground"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="missing" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Эти навыки требуются для вакансии, но не указаны в вашем резюме
                </p>
                {missingSkills.length === 0 ? (
                  <div className="p-4 rounded-lg bg-success/10 text-sm text-success">
                    Отлично! Все ключевые навыки уже упомянуты в резюме.
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {missingSkills.map((skill) => (
                      <Badge
                        key={skill}
                        variant="outline"
                        className="border-warning/40 bg-warning/10 text-warning-foreground"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="recommendations" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Рекомендации AI для улучшения вашего отклика
                </p>
                {recommendations.length === 0 || aiTipsError ? (
                  <div className="p-4 rounded-lg bg-muted/40 text-sm text-muted-foreground">
                    Советы от модели пока недоступны. Попробуйте повторить анализ позже.
                  </div>
                ) : (
                  <Accordion type="multiple" className="w-full">
                    {recommendations.map((rec, index) => (
                      <AccordionItem value={`rec-${index}`} key={`rec-${index}`}>
                        <AccordionTrigger className="text-left text-base">
                          <div className="flex items-center gap-2">
                            <Lightbulb className="w-4 h-4 text-primary" />
                            <span>{rec.title}</span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          <p className="text-sm text-muted-foreground">
                            {rec.details || "Уточните детали самостоятельно и добавьте в резюме релевантные факты."}
                          </p>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                )}
              </TabsContent>
            </Tabs>
          </Card>

          {/* Action Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              className="gradient-hero text-lg shadow-card min-w-[250px]"
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <>
                  <Sparkles className="mr-2 h-5 w-5 animate-spin" />
                  Генерируем документы...
                </>
              ) : (
                <>
                  Сгенерировать документы
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

export default Analysis;

