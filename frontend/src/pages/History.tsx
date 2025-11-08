import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Clock, RefreshCcw, Sparkles, FileText, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  clearGenerationSession,
  saveAnalysisSession,
  saveGenerationSession,
} from "@/lib/session";

const History = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const analysesQuery = useQuery({
    queryKey: ["history", "analyses"],
    queryFn: () => api.listAnalyses(),
    staleTime: 30_000,
  });

  const generationsQuery = useQuery({
    queryKey: ["history", "generations"],
    queryFn: () => api.listGenerations(),
    staleTime: 30_000,
  });

  const hasHistory = useMemo(() => {
    return (analysesQuery.data?.length ?? 0) > 0 || (generationsQuery.data?.length ?? 0) > 0;
  }, [analysesQuery.data, generationsQuery.data]);

  const handleOpenAnalysis = (analysis: Awaited<ReturnType<typeof api.listAnalyses>>[number]) => {
    clearGenerationSession();
    saveAnalysisSession({
      analysisId: analysis.id,
      resumeId: analysis.resume_id,
      vacancyId: analysis.vacancy_id,
      createdAt: analysis.created_at,
    });
    navigate("/analysis");
  };

  const handleOpenGeneration = (bundle: Awaited<ReturnType<typeof api.listGenerations>>[number]) => {
    if (!bundle.resume_document_id || !bundle.cover_letter_document_id) {
      toast({
        title: "Неполная генерация",
        description: "Для этой записи не найдены оба документа",
        variant: "destructive",
      });
      return;
    }

    const relatedAnalysis = analysesQuery.data?.find((item) => item.id === bundle.analysis_id);
    if (relatedAnalysis) {
      saveAnalysisSession({
        analysisId: relatedAnalysis.id,
        resumeId: relatedAnalysis.resume_id,
        vacancyId: relatedAnalysis.vacancy_id,
        createdAt: relatedAnalysis.created_at,
      });
    }

    saveGenerationSession({
      analysisId: bundle.analysis_id,
      resumeDocumentId: bundle.resume_document_id,
      coverLetterDocumentId: bundle.cover_letter_document_id,
      atsScore: bundle.ats_score ?? 0,
    });
    navigate("/results");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}> 
            <div className="w-8 h-8 rounded-lg gradient-hero flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">EdTon.ai</span>
          </div>
          <Button variant="outline" onClick={() => navigate('/upload')}>
            Новый анализ
          </Button>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12 space-y-8">
        <div className="flex items-center gap-3">
          <Clock className="w-6 h-6 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">История работы</h1>
            <p className="text-muted-foreground">
              Возвращайтесь к сохранённым анализам и сгенерированным документам в любое время
            </p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Анализы вакансий</h2>
                <p className="text-muted-foreground text-sm">
                  Последние анализы сопоставления резюме и вакансий
                </p>
              </div>
              <RefreshCcw
                className="w-5 h-5 text-muted-foreground cursor-pointer"
                onClick={() => analysesQuery.refetch()}
              />
            </div>

            {analysesQuery.isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <Skeleton key={index} className="h-16 w-full" />
                ))}
              </div>
            )}

            {!analysesQuery.isLoading && (analysesQuery.data?.length ?? 0) === 0 && (
              <p className="text-sm text-muted-foreground">Анализов пока нет.</p>
            )}

            <div className="space-y-3">
              {analysesQuery.data?.map((analysis) => (
                <div
                  key={analysis.id}
                  className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 hover:border-primary transition"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-semibold">{analysis.role ?? "Без роли"}</p>
                    <p className="text-xs text-muted-foreground">
                      Совпадение: {Math.round(analysis.match_score)}% • {new Date(analysis.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button size="sm" onClick={() => handleOpenAnalysis(analysis)}>
                    Открыть
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">Сгенерированные документы</h2>
                <p className="text-muted-foreground text-sm">Недавние резюме и сопроводительные письма</p>
              </div>
              <RefreshCcw
                className="w-5 h-5 text-muted-foreground cursor-pointer"
                onClick={() => generationsQuery.refetch()}
              />
            </div>

            {generationsQuery.isLoading && (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, index) => (
                  <Skeleton key={index} className="h-20 w-full" />
                ))}
              </div>
            )}

            {!generationsQuery.isLoading && (generationsQuery.data?.length ?? 0) === 0 && (
              <p className="text-sm text-muted-foreground">Документы пока не сгенерированы.</p>
            )}

            <div className="space-y-3">
              {generationsQuery.data?.map((generation) => (
                <div
                  key={generation.analysis_id}
                  className="rounded-lg border bg-card px-4 py-3 space-y-3 hover:border-primary transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-semibold">ATS: {Math.round(generation.ats_score ?? 0)}%</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(generation.created_at).toLocaleString()}
                      </p>
                    </div>
                    <Button size="sm" onClick={() => handleOpenGeneration(generation)}>
                      Открыть
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      {generation.resume_document_id ? "Резюме сохранено" : "Нет резюме"}
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      {generation.cover_letter_document_id ? "Письмо сохранено" : "Нет письма"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {!analysesQuery.isLoading && !generationsQuery.isLoading && !hasHistory && (
          <Card className="p-8 text-center space-y-3">
            <Sparkles className="w-8 h-8 mx-auto text-primary" />
            <h2 className="text-xl font-semibold">История пока пуста</h2>
            <p className="text-sm text-muted-foreground">
              Проведите анализ и сгенерируйте документы, чтобы сохранить результаты здесь.
            </p>
            <Button onClick={() => navigate('/upload')}>Начать анализ</Button>
          </Card>
        )}
      </div>
    </div>
  );
};

export default History;
