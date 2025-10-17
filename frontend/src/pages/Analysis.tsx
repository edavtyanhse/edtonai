import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, CheckCircle2, AlertCircle, Lightbulb, ArrowRight } from "lucide-react";

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

const normalizeTips = (tips: string): string[] => {
  return tips
    .split(/\r?\n/)
    .map((line) => line.replace(/^[-*\d\.\)\s]+/, "").trim())
    .filter(Boolean);
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

  const matchPercentage = analysis?.response.match_score ?? 0;
  const totalSkills =
    (analysis?.response.matched_skills.length ?? 0) +
    (analysis?.response.missing_skills.length ?? 0);
  const skillCoverage = totalSkills
    ? Math.round((100 * (analysis?.response.matched_skills.length ?? 0)) / totalSkills)
    : Math.round(matchPercentage);
  const experienceScore = Math.round((matchPercentage + skillCoverage) / 2);

  const matchingSkills = useMemo(() => {
    const skills = analysis?.response.matched_skills ?? [];
    return skills.map((skill, index) => ({
      name: skill,
      level: index < 3 ? "high" : "medium",
    }));
  }, [analysis?.response.matched_skills]);

  const missingSkills = useMemo(() => {
    const skills = analysis?.response.missing_skills ?? [];
    return skills.map((skill, index) => ({
      name: skill,
      importance: index < 2 ? "high" : "medium",
    }));
  }, [analysis?.response.missing_skills]);

  const recommendations = useMemo(() => {
    const tips = analysis?.response.tips ?? "";
    return normalizeTips(tips);
  }, [analysis?.response.tips]);

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
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Ключевые навыки</span>
                    <span className="font-medium">{skillCoverage}%</span>
                  </div>
                  <Progress value={skillCoverage} className="h-2" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Опыт и требования</span>
                    <span className="font-medium">{experienceScore}%</span>
                  </div>
                  <Progress value={experienceScore} className="h-2" />
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
                <div className="grid gap-3">
                  {matchingSkills.length === 0 ? (
                    <div className="p-4 rounded-lg bg-muted/40 text-sm text-muted-foreground">
                      Мы не нашли совпадающих навыков. Попробуйте дополнить резюме ключевыми словами из вакансии.
                    </div>
                  ) : (
                    matchingSkills.map((skill) => (
                      <div key={skill.name} className="flex items-center justify-between p-4 rounded-lg bg-success/5 border border-success/20">
                        <span className="font-medium capitalize">{skill.name}</span>
                        <Badge
                          variant={skill.level === "high" ? "default" : "secondary"}
                          className="bg-success text-success-foreground"
                        >
                          {skill.level === "high" ? "Отлично" : "Хорошо"}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>

              <TabsContent value="missing" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Эти навыки требуются для вакансии, но не указаны в вашем резюме
                </p>
                <div className="grid gap-3">
                  {missingSkills.length === 0 ? (
                    <div className="p-4 rounded-lg bg-success/10 text-sm text-success">
                      Отлично! Все ключевые навыки уже упомянуты в резюме.
                    </div>
                  ) : (
                    missingSkills.map((skill) => (
                      <div key={skill.name} className="flex items-center justify-between p-4 rounded-lg bg-warning/5 border border-warning/20">
                        <span className="font-medium capitalize">{skill.name}</span>
                        <Badge
                          variant={skill.importance === "high" ? "destructive" : "secondary"}
                          className="bg-warning text-warning-foreground"
                        >
                          {skill.importance === "high" ? "Важно" : "Желательно"}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>

              <TabsContent value="recommendations" className="p-6 space-y-4">
                <p className="text-muted-foreground mb-4">
                  Рекомендации AI для улучшения вашего отклика
                </p>
                <div className="grid gap-3">
                  {recommendations.length === 0 ? (
                    <div className="p-4 rounded-lg bg-muted/40 text-sm text-muted-foreground">
                      Советы от модели пока недоступны. Попробуйте повторить анализ позже.
                    </div>
                  ) : (
                    recommendations.map((rec, index) => (
                      <div key={`${index}-${rec}`} className="flex gap-3 p-4 rounded-lg bg-primary/5 border border-primary/20">
                        <Lightbulb className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </div>
                    ))
                  )}
                </div>
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

