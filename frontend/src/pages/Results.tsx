import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, CheckCircle2, FileText, Mail, Download, Copy, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  loadGenerationSession,
  loadAnalysisSession,
  type GenerationSession,
} from "@/lib/session";

const Results = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [session, setSession] = useState<GenerationSession | null>(null);

  useEffect(() => {
    const generation = loadGenerationSession();
    if (!generation) {
      const hasAnalysis = loadAnalysisSession();
      toast({
        title: "Нет сгенерированных документов",
        description: hasAnalysis
          ? "Сначала сгенерируйте документы на предыдущем шаге"
          : "Загрузите резюме и вакансию заново",
        variant: "destructive",
      });
      navigate(hasAnalysis ? "/analysis" : "/upload", { replace: true });
      return;
    }
    setSession(generation);
  }, [navigate, toast]);

  const resumeDocumentQuery = useQuery({
    queryKey: ["document", session?.resumeDocumentId],
    queryFn: async () => {
      if (!session?.resumeDocumentId) {
        throw new Error("Нет идентификатора резюме");
      }
      return api.getDocument(session.resumeDocumentId);
    },
    enabled: !!session?.resumeDocumentId,
  });

  const coverDocumentQuery = useQuery({
    queryKey: ["document", session?.coverLetterDocumentId],
    queryFn: async () => {
      if (!session?.coverLetterDocumentId) {
        throw new Error("Нет идентификатора письма");
      }
      return api.getDocument(session.coverLetterDocumentId);
    },
    enabled: !!session?.coverLetterDocumentId,
  });

  const analysisQuery = useQuery({
    queryKey: ["analysis", session?.analysisId],
    queryFn: async () => {
      if (!session?.analysisId) {
        throw new Error("Нет анализа для генерации");
      }
      return api.getAnalysis(session.analysisId);
    },
    enabled: !!session?.analysisId,
    staleTime: 30_000,
  });

  const isLoading =
    !session || resumeDocumentQuery.isLoading || coverDocumentQuery.isLoading || analysisQuery.isLoading;

  const resumeText = resumeDocumentQuery.data?.content ?? "";
  const coverText = coverDocumentQuery.data?.content ?? "";
  const resumeHasError = resumeText.trim().toLowerCase().startsWith("[ai error");
  const coverHasError = coverText.trim().toLowerCase().startsWith("[ai error");
  const atsScore = resumeDocumentQuery.data?.ats_score ?? session?.atsScore ?? 0;
  const roleLabel = useMemo(() => analysisQuery.data?.analysis.role || "ваша цель", [analysisQuery.data?.analysis.role]);

  const handleDownload = (kind: "resume" | "cover") => {
    const content = kind === "resume" ? resumeText : coverText;
    const fileName = kind === "resume" ? "resume-edton.txt" : "cover-letter-edton.txt";
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "Скачивание началось",
      description: kind === "resume" ? "Резюме сохранено на устройство" : "Письмо сохранено на устройство",
    });
  };

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Скопировано",
      description: `${label} отправлено в буфер обмена`,
    });
  };

  if (!session) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <Sparkles className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Загружаем сгенерированные документы...</p>
        </div>
      </div>
    );
  }

  if (resumeDocumentQuery.isError || coverDocumentQuery.isError) {
    const message =
      resumeDocumentQuery.error instanceof Error
        ? resumeDocumentQuery.error.message
        : coverDocumentQuery.error instanceof Error
          ? coverDocumentQuery.error.message
          : "Не удалось загрузить документы";
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Alert variant="destructive" className="max-w-xl">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Ошибка загрузки</AlertTitle>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (isLoading || !resumeDocumentQuery.data || !coverDocumentQuery.data) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center">
          <Sparkles className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Получаем сгенерированные документы...</p>
        </div>
      </div>
    );
  }

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
              <div className="w-10 h-10 rounded-full bg-success flex items-center justify-center text-success-foreground">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Загрузка</span>
            </div>
            <div className="flex-1 h-0.5 bg-primary mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-success flex items-center justify-center text-success-foreground">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Анализ</span>
            </div>
            <div className="flex-1 h-0.5 bg-primary mx-4" />
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full gradient-hero flex items-center justify-center text-primary-foreground font-semibold">
                3
              </div>
              <span className="text-sm font-medium">Генерация</span>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto space-y-8">
          <div className="text-center space-y-2 animate-fade-in">
            <div className="flex items-center justify-center gap-2 mb-4">
              <CheckCircle2 className="w-8 h-8 text-success" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold">Документы готовы!</h1>
            <p className="text-muted-foreground text-lg">
              Резюме и сопроводительное письмо адаптированы под {roleLabel}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Resume Card */}
            <Card className="p-6 shadow-soft hover:shadow-card transition-all animate-slide-up flex flex-col gap-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg gradient-hero flex items-center justify-center flex-shrink-0">
                  <FileText className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-1">Адаптированное резюме</h3>
                  <p className="text-sm text-muted-foreground">
                    Используйте это резюме для подачи отклика — ATS-оценка {Math.round(atsScore)}%
                  </p>
                </div>
              </div>
              {resumeHasError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Не удалось сгенерировать новое резюме</AlertTitle>
                  <AlertDescription>{resumeText}</AlertDescription>
                </Alert>
              )}
              <Textarea readOnly value={resumeText} className="min-h-[220px] resize-none bg-muted/50" />
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopy(resumeText, "Резюме")}>
                  <Copy className="w-4 h-4 mr-2" />Скопировать
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleDownload("resume")}>
                  <Download className="w-4 h-4 mr-2" />Скачать
                </Button>
              </div>
            </Card>

            {/* Cover Letter Card */}
            <Card className="p-6 shadow-soft hover:shadow-card transition-all animate-slide-up flex flex-col gap-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
                  <Mail className="w-6 h-6 text-accent-foreground" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-1">Сопроводительное письмо</h3>
                  <p className="text-sm text-muted-foreground">
                    Персонализированное письмо для быстрого копирования и отправки
                  </p>
                </div>
              </div>
              {coverHasError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Не удалось сгенерировать письмо</AlertTitle>
                  <AlertDescription>{coverText}</AlertDescription>
                </Alert>
              )}
              <Textarea readOnly value={coverText} className="min-h-[220px] resize-none bg-muted/50" />
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopy(coverText, "Письмо")}>
                  <Copy className="w-4 h-4 mr-2" />Скопировать
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleDownload("cover")}>
                  <Download className="w-4 h-4 mr-2" />Скачать
                </Button>
              </div>
            </Card>
          </div>

          {/* AI Summary */}
          <Card className="p-6 shadow-soft bg-primary/5 border-primary/20 animate-slide-up">
            <div className="flex gap-4">
              <Sparkles className="w-6 h-6 text-primary flex-shrink-0" />
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">Результаты анализа AI</h3>
                <p className="text-sm text-muted-foreground">
                  Итоговая ATS-оценка: <span className="font-semibold text-primary">{Math.round(atsScore)}%</span>. Проверьте, что ключевые достижения и навыки отражают ваш реальный опыт перед отправкой рекрутеру.
                </p>
              </div>
            </div>
          </Card>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/upload')}
            >
              Создать новый отклик
            </Button>
            <Button
              size="lg"
              className="gradient-hero shadow-card"
              onClick={() => navigate('/')}
            >
              Вернуться на главную
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;

